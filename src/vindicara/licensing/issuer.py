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

# Single source of truth for feature strings (OSS base package). The same
# constants are imported by the airsdk_pro @requires_pro gates, so a granted
# feature here can never drift from the checked feature there. A contract test
# enforces it. Never type a bare feature string in this module.
from airsdk import features as F
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)

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


# Enterprise: everything in Team plus the boundary features the Team comment
# above reserves for Enterprise+ (SOC 2-AI attestation report, HL7 / FHIR
# clinical capture under a BAA).
_ENTERPRISE_FEATURES: tuple[str, ...] = (
    *_TEAM_FEATURES,
    F.REPORT_SOC2_AI,
    F.HL7_FHIR,
)

#: Free tier grants nothing: everything that runs locally is open source and ungated,
#: so the grant exists only to say "this workspace is on the free tier".
_FREE_FEATURES: tuple[str, ...] = ()

#: Lifetime of a console-issued grant. Short on purpose: the console is the
#: authority, and a workspace that downgrades or lapses simply stops renewing.
GRANT_DAYS = 30

#: Workspace tier -> the grant it earns. Keys are ``Workspace.tier`` values.
_TIER_TO_FEATURES: dict[str, tuple[str, ...]] = {
    "free": _FREE_FEATURES,
    "pro": _INDIVIDUAL_FEATURES,
    "team": _TEAM_FEATURES,
    "enterprise": _ENTERPRISE_FEATURES,
}


@dataclass(frozen=True)
class LicensePlan:
    """Resolved plan derived from a Stripe Price ID."""

    tier: str
    duration_days: int
    features: tuple[str, ...]


# Price ID → plan mapping. The Price IDs are not secret (the secret material is
# the signing key, not these), but they are also not discoverable from a Payment
# Link: the buy.stripe.com page ships only the plink_... id and the display
# amount. Read a Price ID off the price in the Stripe Dashboard.
_PRICE_TO_PLAN: dict[str, LicensePlan] = {
    # Current Pro AIR price: $30/mo from 2026-09-08 (docs/pro-tier-spec.md),
    # behind Payment Link plink_1UDKBQC4TNI7tWa0tOP8dFoq on the pricing page.
    "price_1UDKAkC4TNI7tWa0ZDYeUM29": LicensePlan(
        tier="individual", duration_days=33, features=_INDIVIDUAL_FEATURES
    ),
    # Retired 2026-09-08: the $25/mo Pro price (live 2026-09-07 to 2026-09-08).
    # Retired prices stay mapped because renewal invoices carry the Price ID the
    # subscriber originally bought at; removing one hard-fails their reissue.
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


def plan_for_tier(tier: str) -> LicensePlan:
    """Resolve a workspace tier to the console grant it earns; raise if unknown.

    This is the console-grant path: the workspace's ``tier`` in AIR Cloud is
    the authority for every tier, free included, and the grant is re-issued
    on request for ``GRANT_DAYS`` at a time.
    """
    features = _TIER_TO_FEATURES.get(tier)
    if features is None:
        raise LicenseIssuanceError(f"unknown workspace tier {tier!r}; refusing to issue a grant")
    return LicensePlan(tier=tier, duration_days=GRANT_DAYS, features=features)


def _canonical_signing_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


#: Public half of the license signing key, hex-encoded raw Ed25519.
#:
#: This MUST equal ``airsdk_pro._keys.VENDOR_LICENSE_PUBLIC_KEY_HEX``: the
#: issuer signs with the private half, the customer's ``airsdk_pro`` verifies
#: against that constant, and a token only validates when the two agree. The
#: two drifted apart undetected from 2026-04-27 to 2026-09-08 (the constant
#: named a key whose private half existed nowhere), so every token minted in
#: that window failed verification on the customer side with no signal here.
#: A cross-package test asserts the two constants are equal.
EXPECTED_LICENSE_PUBLIC_KEY_HEX = (
    "8627b4309db46b9fa42ac9c47c9a409819d1e62cfd4ab079609a78db2d587d23"
)


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
    # Fail closed on a signing key the customer's verifier cannot match. Minting
    # a token nobody can verify is worse than refusing: the customer has paid,
    # the webhook reports success, and the failure only surfaces later on their
    # machine as an invalid license.
    actual = key_obj.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    if actual != EXPECTED_LICENSE_PUBLIC_KEY_HEX:
        raise LicenseIssuanceError(
            "configured signing key does not match the public key embedded in "
            f"airsdk_pro (expected {EXPECTED_LICENSE_PUBLIC_KEY_HEX}, got {actual}); "
            "refusing to mint a token no customer can verify"
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
