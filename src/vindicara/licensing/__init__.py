"""Server-side license issuance.

Issues Ed25519-signed license tokens whose verification side ships in
``packages/projectair-pro/src/airsdk_pro/license.py``. The two halves use
the same canonicalization and signature scheme; the public key is embedded
in the customer-installed ``airsdk_pro`` wheel.
"""
from vindicara.licensing.issuer import (
    LicenseIssuanceError,
    issue_license_token,
    plan_for_price_id,
    plan_for_tier,
)

__all__ = [
    "LicenseIssuanceError",
    "issue_license_token",
    "plan_for_price_id",
    "plan_for_tier",
]
