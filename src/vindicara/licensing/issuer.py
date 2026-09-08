"""Issue Ed25519-signed Vindicara Pro license tokens.

The signing side mirrors ``packages/projectair-pro/tools/issue_license.py``;
this module exists so the FastAPI Lambda can call ``issue_license_token`` in
process and load the private key from a string (env var or Secrets Manager
fetch) rather than a filesystem path.

Every token produced here verifies with ``airsdk_pro.license.verify_token``
on the customer side because both halves use the same canonicalization
(sorted keys, no whitespace, UTF-8) and the same Ed25519 keypair.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Single source of truth for feature strings (OSS base package). The same
# constants are imported by the airsdk_pro @requires_pro gates, so a granted
# feature here can never drift from the checked feature there. A contract test
# enforces it. Never type a bare feature string in this module.
from airsdk import features as F

TOKEN_VERSION = 1

# Feature bundles per tier. Mirror these in the pricing-page copy when changes
# ship; the verifier on the customer side enforces them via has_feature().
# Pro AIR (individual). Locked bundle: see docs/pro-tier-spec.md.
# report-soc2-ai is Enterprise-only; Monitor/Protect, SIEM, multi-seat are Team+.
_INDIVIDUAL_FEATURES: tuple[str, ...] = (
    F.AIR_CLOUD_CLIENT,
    F.PREMIUM_DETECTORS,
    F.ANCHOR,            # BLAKE3 + Ed25519 + RFC 3161 + Sigstore Rekor
    F.AUDIT,             # APPM pillar 1
    F.PROVE,             # APPM pillar 2
    F.EVIDENCE_PACKS,    # exportable, third-party verifiable
    F.REPORT_NIST_AI_RMF,
    F.FLIGHTDECK_HOSTED,  # single-operator scope
)
# Team (locked spec). Everything in Pro plus the second half of APPM (Monitor +
# Protect), the collaboration/integration layer, and certified admissibility.
# Pro proves; Team proves, watches, and intervenes. report-soc2-ai, BAA/HIPAA,
# ML-DSA-65, Agent IAM (full L4), Vindicara-named attestation, and
# dedicated/on-prem/IR stay Enterprise+ — that boundary is the moat.
_TEAM_FEATURES: tuple[str, ...] = (
    *_INDIVIDUAL_FEATURES,
    F.MONITOR,            # APPM Monitor — continuous fleet-wide watch (L2)
    F.PROTECT,            # APPM Protect — real-time containment, fail-closed (L3)
    F.DUAL_CONTROL,       # FlightDeck dual-control on the Engage cascade
    F.COHORT_SCOPE,
    F.FLEET_SCOPE,
    F.SIEM_INTEGRATIONS,  # Datadog/Splunk/Sumo/Sentinel/Slack
    F.MULTI_SEAT,         # shared workspace, operators, roles
    F.INCIDENT_WORKFLOWS,  # routed alerts/notifications
    F.ADMISSIBILITY,      # certified legal-hold packs; customer signs FRE 902
    F.REPORT_FLEET_POSTURE,  # operational fleet/incident report (non-attestation)
)


@dataclass(frozen=True)
class LicensePlan:
    """Resolved plan derived from a Stripe Price ID."""

    tier: str
    duration_days: int
    features: tuple[str, ...]


# Price ID → plan mapping. The Price IDs are public (they appear in Stripe
# Checkout URLs); the secret material is the signing key, not these.
_PRICE_TO_PLAN: dict[str, LicensePlan] = {
    # Pro AIR price ID. Priced $25/mo from 2026-09-07 (docs/pro-tier-spec.md);
    # if a new Stripe price is created for the change, add its ID here too.
    "price_1TbIB2C4TNI7tWa0226pj2SS": LicensePlan(
        tier="individual", duration_days=33, features=_INDIVIDUAL_FEATURES
    ),
    # Legacy individual prices ($45/annual). Kept mapped so any still-live
    # checkout link issues the correct features; archive these in Stripe.
    "price_1TUFKqC4TNI7tWa0kzayypru": LicensePlan(
        tier="individual", duration_days=33, features=_INDIVIDUAL_FEATURES
    ),
    "price_1TUfRhC4TNI7tWa0v0joo1xG": LicensePlan(
        tier="individual", duration_days=395, features=_INDIVIDUAL_FEATURES
    ),
    "price_1TUfSDC4TNI7tWa0r7AmOjCh": LicensePlan(
        tier="team", duration_days=33, features=_TEAM_FEATURES
    ),
    "price_1TUfSrC4TNI7tWa0gdHeoFK9": LicensePlan(
        tier="team", duration_days=395, features=_TEAM_FEATURES
    ),
}


class LicenseIssuanceError(Exception):
    """Raised when a license cannot be issued (bad config, unknown price, etc.)."""


def plan_for_price_id(price_id: str) -> LicensePlan:
    """Resolve a Stripe Price ID to its license plan; raise if unknown.

    Webhook handlers should treat unknown Price IDs as a hard error rather
    than falling back to a default. An unrecognized Price could be a typo,
    a price the operator created but didn't intend to fulfill, or a probe.
    """
    plan = _PRICE_TO_PLAN.get(price_id)
    if plan is None:
        raise LicenseIssuanceError(
            f"unrecognized Stripe Price ID {price_id!r}; refusing to issue a license"
        )
    return plan


def _canonical_signing_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _load_signing_key(pem: str) -> Ed25519PrivateKey:
    if not pem:
        raise LicenseIssuanceError(
            "license signing key is not configured; set VINDICARA_LICENSE_SIGNING_KEY_PEM"
        )
    key_obj = load_pem_private_key(pem.encode("utf-8"), password=None)
    if not isinstance(key_obj, Ed25519PrivateKey):
        raise LicenseIssuanceError(
            f"configured signing key is not Ed25519 (got {type(key_obj).__name__})"
        )
    return key_obj


def issue_license_token(
    *,
    email: str,
    plan: LicensePlan,
    signing_key_pem: str,
    issued_at: int | None = None,
) -> dict[str, object]:
    """Mint a signed license token for ``email`` under ``plan``.

    Returns the token as a dict, ready to ``json.dumps`` and hand to a
    customer. The verifier on the customer side enforces that the JSON is
    a single object whose signature validates against the embedded vendor
    public key, so callers must not mutate the dict before serialization.
    """
    if not email or "@" not in email:
        raise LicenseIssuanceError(f"invalid customer email: {email!r}")
    issued = issued_at if issued_at is not None else int(time.time())
    expires = issued + plan.duration_days * 86_400
    payload: dict[str, object] = {
        "v": TOKEN_VERSION,
        "email": email,
        "tier": plan.tier,
        "issued_at": issued,
        "expires_at": expires,
        "features": sorted(plan.features),
    }
    private_key = _load_signing_key(signing_key_pem)
    signature = private_key.sign(_canonical_signing_bytes(payload)).hex()
    return {**payload, "signature": signature}
