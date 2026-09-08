"""Tests for POST /webhooks/stripe (Stripe auto-fulfillment)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app
from vindicara.cloud.workspace import InMemoryApiKeyStore, InMemoryWorkspaceStore

# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

_TEST_PRICE_ID = "price_1TUFKqC4TNI7tWa0kzayypru"  # pro monthly


def _generate_signing_key_pem() -> str:
    key = Ed25519PrivateKey.generate()
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()


_SIGNING_KEY_PEM = _generate_signing_key_pem()


def _checkout_event(email: str = "buyer@example.com") -> dict[str, object]:
    return {
        "id": "evt_test_checkout",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer_details": {"email": email},
            },
        },
    }


def _invoice_event(
    email: str = "buyer@example.com",
    billing_reason: str = "subscription_cycle",
) -> dict[str, object]:
    return {
        "id": "evt_test_invoice",
        "type": "invoice.paid",
        "data": {
            "object": {
                "customer_email": email,
                "billing_reason": billing_reason,
                "lines": {
                    "data": [
                        {"price": {"id": _TEST_PRICE_ID}},
                    ],
                },
            },
        },
    }


@pytest.fixture(autouse=True)
def _stripe_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject Stripe-related env vars for VindicaraSettings."""
    monkeypatch.setenv("VINDICARA_STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("VINDICARA_STRIPE_SECRET_KEY", "sk_test_xxx")
    monkeypatch.setenv("VINDICARA_LICENSE_SIGNING_KEY_PEM", _SIGNING_KEY_PEM)
    monkeypatch.setenv("VINDICARA_RESEND_API_KEY", "re_test_xxx")
    monkeypatch.setenv("VINDICARA_PRO_WHEEL_SIGNED_URL", "https://example.com/wheel.whl")


@pytest.fixture
def app_with_cloud():
    """App with AIR Cloud workspace/key stores attached."""
    app = create_app(dev_api_keys=["vnd_test"])
    app.state.cloud_workspaces = InMemoryWorkspaceStore()
    app.state.cloud_api_keys = InMemoryApiKeyStore()
    return app


@pytest.fixture
def app_without_cloud():
    """App without AIR Cloud stores (non-cloud deployment)."""
    return create_app(dev_api_keys=["vnd_test"])


def _mock_line_items() -> MagicMock:
    """Build a mock ListObject for Session.list_line_items."""
    price = SimpleNamespace(id=_TEST_PRICE_ID)
    item = SimpleNamespace(price=price)
    result = MagicMock()
    result.data = [item]
    return result


@pytest.mark.asyncio
async def test_bad_signature_returns_400(app_with_cloud: object) -> None:
    """Stripe-Signature verification failure produces 400."""
    with patch(
        "stripe.Webhook.construct_event",
        side_effect=__import__("stripe").SignatureVerificationError(
            "bad sig",
            "sig_header",
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "bad"},
            )
    assert resp.status_code == 400
    assert "signature" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_unknown_event_returns_200(app_with_cloud: object) -> None:
    """Unknown event types are acknowledged (200) so Stripe stops retrying."""
    with patch(
        "stripe.Webhook.construct_event",
        return_value={"id": "evt_test_unknown", "type": "customer.created", "data": {}},
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=1,v1=abc"},
            )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_checkout_fulfilled_mints_and_emails_license(app_with_cloud: object) -> None:
    """checkout.session.completed mints a license and emails it. No workspace.

    Fulfillment deliberately stops at the license token. Workspaces and owner
    keys are created by ``provision_identity`` from ``POST /v1/auth/exchange``,
    keyed on the verified Auth0 ``(issuer, sub)``. A webhook only has an email,
    so a workspace created here could never be linked to the buyer's identity:
    their later ``air login`` would mint a second workspace and strand the paid
    one. The empty-store assertion below is the regression guard for that.
    """
    event = _checkout_event()
    with (
        patch("stripe.Webhook.construct_event", return_value=event),
        patch(
            "stripe.checkout.Session.list_line_items",
            return_value=_mock_line_items(),
        ),
        patch("resend.Emails.send", return_value={"id": "msg_test"}) as mock_send,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=1,v1=abc"},
            )

    assert resp.status_code == 200
    assert resp.json()["status"] == "fulfilled"

    # The license email carries the signed token and the wheel link.
    mock_send.assert_called_once()
    call_params = mock_send.call_args[0][0]
    assert call_params["to"] == ["buyer@example.com"]
    assert "license" in call_params["text"].lower()

    # Fulfillment provisions no tenancy; auth exchange owns that.
    ws_store: InMemoryWorkspaceStore = app_with_cloud.state.cloud_workspaces  # type: ignore[union-attr]
    assert ws_store.list() == []


@pytest.mark.asyncio
async def test_checkout_without_cloud_stores(app_without_cloud: object) -> None:
    """checkout.session.completed still works without cloud stores (no workspace)."""
    event = _checkout_event()
    with (
        patch("stripe.Webhook.construct_event", return_value=event),
        patch(
            "stripe.checkout.Session.list_line_items",
            return_value=_mock_line_items(),
        ),
        patch("resend.Emails.send", return_value={"id": "msg_test"}) as mock_send,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_without_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=1,v1=abc"},
            )

    assert resp.status_code == 200
    assert resp.json()["status"] == "fulfilled"
    # Same email either way: fulfillment never depends on the cloud stores.
    call_params = mock_send.call_args[0][0]
    assert "air cloud login" not in call_params["text"].lower()


@pytest.mark.asyncio
async def test_missing_email_returns_500(app_with_cloud: object) -> None:
    """checkout.session.completed without email produces 500."""
    event = _checkout_event()
    # Remove the email
    event["data"]["object"]["customer_details"] = {}  # type: ignore[index]

    with (
        patch("stripe.Webhook.construct_event", return_value=event),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=1,v1=abc"},
            )

    assert resp.status_code == 500
    assert "email" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_unconfigured_webhook_secret_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing webhook secret returns 503 (service unavailable)."""
    monkeypatch.setenv("VINDICARA_STRIPE_WEBHOOK_SECRET", "")
    app = create_app(dev_api_keys=["vnd_test"])

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=abc"},
        )

    assert resp.status_code == 503
    assert "not configured" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_invoice_subscription_create_skipped(app_with_cloud: object) -> None:
    """invoice.paid with billing_reason=subscription_create is skipped."""
    event = _invoice_event(billing_reason="subscription_create")

    with patch("stripe.Webhook.construct_event", return_value=event):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=1,v1=abc"},
            )

    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"


@pytest.mark.asyncio
async def test_invoice_renewal_fulfilled(app_with_cloud: object) -> None:
    """invoice.paid renewal re-issues license and sends email."""
    event = _invoice_event(billing_reason="subscription_cycle")

    with (
        patch("stripe.Webhook.construct_event", return_value=event),
        patch("resend.Emails.send", return_value={"id": "msg_renew"}) as mock_send,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_cloud),  # type: ignore[arg-type]
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/webhooks/stripe",
                content=json.dumps(event).encode(),
                headers={"stripe-signature": "t=1,v1=abc"},
            )

    assert resp.status_code == 200
    assert resp.json()["status"] == "renewed"
    mock_send.assert_called_once()
