"""Stripe webhook endpoint that auto-issues a Pro license on successful checkout.

Path: ``POST /webhooks/stripe``. Whitelisted in
:mod:`vindicara.api.middleware.auth` so Stripe (which can't carry our
API key) can hit it; authentication is the ``Stripe-Signature`` header
verified against the configured webhook signing secret.

Flow on ``checkout.session.completed``:
    1. Verify signature on the raw request body.
    2. Extract customer email + the line-item Price ID.
    3. Resolve the Price ID to a license plan (tier + duration + features).
    4. Mint an Ed25519-signed license token.
    5. Email the token + projectair-pro wheel link to the customer.
    6. Return 200.

Any failure between (3) and (5) returns a 5xx so Stripe retries the event,
preventing silent loss of a paid license. Signature failures and unknown
event types return 400 / 200 respectively (Stripe should not retry those).
"""
from __future__ import annotations

import stripe
import structlog
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from vindicara.config.settings import VindicaraSettings
from vindicara.licensing import (
    LicenseIssuanceError,
    issue_license_token,
    plan_for_price_id,
)
from vindicara.notifications import EmailDeliveryError, LicenseEmail, send_license_email

logger = structlog.get_logger(__name__)
router = APIRouter()

# Stripe events we act on. Anything else returns a fast 200 so Stripe stops
# retrying; we don't have to subscribe to events we don't handle, but the
# dashboard UI sometimes adds extras and a 200 is the cheapest acknowledgement.
_HANDLED_EVENTS = frozenset(
    {
        "checkout.session.completed",
        "invoice.paid",
    }
)


def _settings() -> VindicaraSettings:
    return VindicaraSettings()


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> Response:
    """Render the outcome as JSON.

    Success is ``{"status": ...}``; failure is ``{"error": ...}`` carrying the
    HTTPException detail. Stripe only cares about the status code, but a typed
    body makes the Stripe dashboard's delivery log readable when a fulfillment
    fails, which is the moment someone has paid and not received a license.
    """
    try:
        outcome = await _process(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(status_code=200, content={"status": outcome})


async def _process(request: Request) -> str:
    settings = _settings()

    if not settings.stripe_webhook_secret:
        logger.error("stripe.webhook.no_secret_configured")
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except ValueError:
        logger.warning("stripe.webhook.malformed_payload")
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    except stripe.SignatureVerificationError:
        logger.warning("stripe.webhook.bad_signature")
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    event_type = event["type"]
    event_id = event["id"]
    logger.info("stripe.webhook.received", event_type=event_type, event_id=event_id)

    if event_type not in _HANDLED_EVENTS:
        return "ignored"

    if event_type == "checkout.session.completed":
        return await _handle_checkout_completed(event, settings)
    return await _handle_invoice_paid(event, settings)


async def _handle_checkout_completed(
    event: stripe.Event, settings: VindicaraSettings
) -> str:
    session = event["data"]["object"]
    customer_email = (
        session.get("customer_details", {}).get("email")
        or session.get("customer_email")
        or ""
    )
    if not customer_email:
        logger.error(
            "stripe.webhook.missing_email", session_id=session.get("id"), event_id=event["id"]
        )
        raise HTTPException(status_code=500, detail="Session has no customer email")

    # Resolve Price ID. Checkout Sessions carry it under either
    # display_items / line_items depending on Stripe API version. The Sessions
    # API only includes line_items if explicitly expanded, so fetch them.
    session_id = session["id"]
    try:
        line_items = stripe.checkout.Session.list_line_items(
            session_id, api_key=settings.stripe_secret_key, limit=1
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "stripe.webhook.line_items_fetch_failed",
            session_id=session_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Could not fetch line items") from exc

    if not line_items.data:
        logger.error("stripe.webhook.empty_line_items", session_id=session_id)
        raise HTTPException(status_code=500, detail="Session has no line items")

    # LineItem.price is optional in the Stripe model. 5xx rather than skip, so
    # Stripe retries instead of silently dropping a paid session.
    price = line_items.data[0].price
    if price is None:
        logger.error("stripe.webhook.line_item_no_price", session_id=session_id)
        raise HTTPException(status_code=500, detail="Line item has no price")

    await _issue_and_email(customer_email, price.id, settings, source="checkout")
    return "fulfilled"


async def _handle_invoice_paid(
    event: stripe.Event, settings: VindicaraSettings
) -> str:
    invoice = event["data"]["object"]
    customer_email = invoice.get("customer_email") or ""
    if not customer_email:
        logger.warning(
            "stripe.webhook.invoice_no_email", invoice_id=invoice.get("id")
        )
        return "skipped"

    lines = invoice.get("lines", {}).get("data", [])
    if not lines:
        logger.warning(
            "stripe.webhook.invoice_no_lines", invoice_id=invoice.get("id")
        )
        return "skipped"

    price_id = lines[0].get("price", {}).get("id")
    if not price_id:
        logger.warning(
            "stripe.webhook.invoice_no_price", invoice_id=invoice.get("id")
        )
        return "skipped"

    # Skip the initial invoice from a new subscription. Stripe also emits
    # checkout.session.completed for that, and we already handled it there.
    if invoice.get("billing_reason") == "subscription_create":
        logger.info(
            "stripe.webhook.invoice_skipped_initial",
            invoice_id=invoice.get("id"),
        )
        return "skipped"

    await _issue_and_email(customer_email, price_id, settings, source="renewal")
    return "renewed"


async def _issue_and_email(
    email: str, price_id: str, settings: VindicaraSettings, *, source: str
) -> None:
    try:
        plan = plan_for_price_id(price_id)
    except LicenseIssuanceError as exc:
        logger.error(
            "stripe.webhook.unknown_price", price_id=price_id, source=source, error=str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        token = issue_license_token(
            email=email,
            plan=plan,
            signing_key_pem=settings.license_signing_key_pem,
        )
    except LicenseIssuanceError as exc:
        logger.error("stripe.webhook.signing_failed", email=email, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not settings.pro_wheel_signed_url:
        logger.error("stripe.webhook.no_wheel_url", email=email)
        raise HTTPException(status_code=500, detail="Wheel download URL not configured")

    payload = LicenseEmail(
        recipient=email,
        tier=plan.tier,
        expires_at=int(token["expires_at"]),  # type: ignore[arg-type]
        license_token=token,
        wheel_download_url=settings.pro_wheel_signed_url,
    )
    try:
        message_id = send_license_email(payload, resend_api_key=settings.resend_api_key)
    except EmailDeliveryError as exc:
        logger.error("stripe.webhook.email_failed", email=email, error=str(exc))
        raise HTTPException(status_code=500, detail="Email delivery failed") from exc

    logger.info(
        "stripe.webhook.license_delivered",
        email=email,
        tier=plan.tier,
        source=source,
        message_id=message_id,
    )
