"""The issuer's signing key and airsdk_pro's verification key must agree.

A license token is signed by ``vindicara.licensing.issuer`` and verified on the
customer's machine by ``airsdk_pro.license`` against a public key compiled into
that distribution. Nothing at mint time used to compare the two, so they drifted
apart from 2026-04-27 to 2026-09-08: the embedded constant named a key whose
private half existed nowhere, while the issuer signed with a different key. Every
token minted in that window was rejected on the customer side, and no test, log,
or webhook response showed it.

These tests are the guard. They mirror ``test_feature_registry`` in spirit: the
two sides of a contract that ship in different packages are asserted equal here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from vindicara.licensing.issuer import (
    EXPECTED_LICENSE_PUBLIC_KEY_HEX,
    LicenseIssuanceError,
    LicensePlan,
    issue_license_token,
)

_PRO_SRC = Path(__file__).resolve().parents[2] / "packages" / "projectair-pro" / "src"


def _embedded_public_key_hex() -> str:
    """Read the constant compiled into the projectair-pro distribution."""
    if str(_PRO_SRC) not in sys.path:
        sys.path.insert(0, str(_PRO_SRC))
    from airsdk_pro._keys import VENDOR_LICENSE_PUBLIC_KEY_HEX

    return VENDOR_LICENSE_PUBLIC_KEY_HEX


@pytest.mark.skipif(not _PRO_SRC.exists(), reason="projectair-pro not checked out")
def test_issuer_and_airsdk_pro_name_the_same_public_key() -> None:
    """The exact drift that shipped broken licenses for four months."""
    assert _embedded_public_key_hex() == EXPECTED_LICENSE_PUBLIC_KEY_HEX


def test_expected_public_key_is_a_valid_ed25519_public_key() -> None:
    raw = bytes.fromhex(EXPECTED_LICENSE_PUBLIC_KEY_HEX)
    assert len(raw) == 32


def _pem_for(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode()


def test_issuance_refuses_a_key_the_customer_cannot_verify() -> None:
    """A signing key whose public half is not the embedded one must fail closed.

    Minting is worse than refusing here: the customer has paid, the webhook
    reports success, and the break only surfaces later on their machine.
    """
    wrong = Ed25519PrivateKey.generate()
    plan = LicensePlan(tier="individual", duration_days=33, features=("anchor",))

    with pytest.raises(LicenseIssuanceError, match="does not match the public key"):
        issue_license_token(
            email="buyer@example.com", plan=plan, signing_key_pem=_pem_for(wrong)
        )


def test_the_error_names_both_keys_so_the_mismatch_is_diagnosable() -> None:
    wrong = Ed25519PrivateKey.generate()
    wrong_hex = (
        wrong.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    )
    plan = LicensePlan(tier="individual", duration_days=33, features=("anchor",))

    with pytest.raises(LicenseIssuanceError) as excinfo:
        issue_license_token(
            email="buyer@example.com", plan=plan, signing_key_pem=_pem_for(wrong)
        )

    message = str(excinfo.value)
    assert EXPECTED_LICENSE_PUBLIC_KEY_HEX in message
    assert wrong_hex in message
