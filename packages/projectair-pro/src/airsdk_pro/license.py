"""License token format, signing, verification, and on-disk storage.

A license token is a JSON object signed with the vendor's Ed25519 private key.
Verification happens entirely locally against the public key embedded in this
package, so license checks work air-gapped and never phone home.

Token shape::

    {
      "v": 1,
      "email": "kevin@example.com",
      "tier": "individual" | "team" | "enterprise",
      "issued_at": 1714200000,
      "expires_at": 1745736000,
      "features": ["air-cloud-client", "report-nist-ai-rmf", ...],
      "signature": "<hex Ed25519 signature over canonical JSON of fields above>"
    }

Storage path: ``~/.airsdk/license.json`` (mode 600). The file holds the raw
signed token plus a ``installed_at`` timestamp; verification re-reads the
signature on every check, so editing the file in place is detected.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from airsdk_pro._keys import VENDOR_LICENSE_PUBLIC_KEY_HEX

TOKEN_VERSION = 1
DEFAULT_LICENSE_PATH = Path.home() / ".airsdk" / "license.json"
FREE_TIER = "free"
#: ``individual`` is the pre-1.4.0 name for Pro; tokens already in the field carry it.
VALID_TIERS = frozenset({FREE_TIER, "pro", "individual", "team", "enterprise"})


class LicenseError(Exception):
    """Base for license problems. All subclasses are user-facing."""


class LicenseMissingError(LicenseError):
    """No license file is installed."""


class LicenseInvalidError(LicenseError):
    """The license file exists but failed signature or schema verification."""


class LicenseExpiredError(LicenseError):
    """The license is past its ``expires_at``."""


@dataclass(frozen=True)
class LicenseToken:
    """Verified, in-memory representation of a license."""

    email: str
    tier: str
    issued_at: int
    expires_at: int
    features: tuple[str, ...]

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    @property
    def is_paid(self) -> bool:
        """``True`` for any tier above free. A free grant proves the workspace
        exists on the console; it unlocks nothing."""
        return self.tier != FREE_TIER

    @property
    def days_remaining(self) -> int:
        return max(0, int((self.expires_at - time.time()) // 86_400))

    def has_feature(self, feature: str) -> bool:
        return feature in self.features


def _canonical_signing_bytes(payload: dict[str, Any]) -> bytes:
    """Bytes that the vendor private key signs over.

    Fields are sorted, no whitespace, UTF-8 encoded. Identical canonicalization
    to the OSS AgDR records so the same primitives back both signatures.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def verify_token(token: dict[str, Any]) -> LicenseToken:
    """Validate the token's signature and shape; return a frozen LicenseToken.

    Raises :class:`LicenseInvalidError` for any structural or cryptographic
    problem and :class:`LicenseExpiredError` if the token's ``expires_at`` is
    in the past.
    """
    if not isinstance(token, dict):
        raise LicenseInvalidError("license token is not a JSON object")
    if token.get("v") != TOKEN_VERSION:
        raise LicenseInvalidError(f"license token version {token.get('v')!r} is unsupported (expected {TOKEN_VERSION})")
    signature_hex = token.get("signature")
    if not isinstance(signature_hex, str):
        raise LicenseInvalidError("license token has no signature field")
    payload = {k: v for k, v in token.items() if k != "signature"}
    for required in ("email", "tier", "issued_at", "expires_at", "features"):
        if required not in payload:
            raise LicenseInvalidError(f"license token missing required field {required!r}")
    if payload["tier"] not in VALID_TIERS:
        raise LicenseInvalidError(f"license tier {payload['tier']!r} is not valid")
    if not isinstance(payload["features"], list) or not all(isinstance(f, str) for f in payload["features"]):
        raise LicenseInvalidError("license features must be a list of strings")

    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(VENDOR_LICENSE_PUBLIC_KEY_HEX))
    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError as exc:
        raise LicenseInvalidError(f"license signature is not valid hex: {exc}") from exc
    try:
        public_key.verify(signature, _canonical_signing_bytes(payload))
    except InvalidSignature as exc:
        raise LicenseInvalidError("license signature does not verify against vendor public key") from exc

    parsed = LicenseToken(
        email=str(payload["email"]),
        tier=str(payload["tier"]),
        issued_at=int(payload["issued_at"]),
        expires_at=int(payload["expires_at"]),
        features=tuple(payload["features"]),
    )
    if parsed.is_expired:
        raise LicenseExpiredError(
            f"license expired on {time.strftime('%Y-%m-%d', time.gmtime(parsed.expires_at))}; renew at https://vindicara.io/pricing"
        )
    return parsed


def install_license(token_text: str, *, path: Path | None = None) -> LicenseToken:
    """Verify ``token_text`` (raw JSON) and write it to ``path`` (default storage location).

    Creates the parent directory if needed and forces mode 0600 on the written
    file so the license is not world-readable.
    """
    try:
        token = json.loads(token_text)
    except json.JSONDecodeError as exc:
        raise LicenseInvalidError(f"license is not valid JSON: {exc}") from exc

    parsed = verify_token(token)
    target = path if path is not None else DEFAULT_LICENSE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    on_disk = {"installed_at": int(time.time()), "token": token}
    target.write_text(json.dumps(on_disk, indent=2), encoding="utf-8")
    os.chmod(target, 0o600)
    return parsed


def load_license(path: Path | None = None) -> LicenseToken:
    """Read and verify the installed license. Raises ``LicenseMissingError`` if none."""
    target = path if path is not None else DEFAULT_LICENSE_PATH
    if not target.exists():
        raise LicenseMissingError(
            f"no license at {target}. Buy a license at https://vindicara.io/pricing then run `air login --license <token>`."
        )
    try:
        on_disk = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LicenseInvalidError(f"license file at {target} is corrupt: {exc}") from exc
    if not isinstance(on_disk, dict) or "token" not in on_disk:
        raise LicenseInvalidError(f"license file at {target} is missing the 'token' field")
    return verify_token(on_disk["token"])


def current_license(path: Path | None = None) -> LicenseToken | None:
    """Return the active license, or ``None`` if missing / invalid / expired.

    Use this when you want a non-throwing check; use :func:`load_license` when
    a precise error is useful for the caller (e.g. CLI status commands).
    """
    try:
        return load_license(path)
    except LicenseError:
        return None


def is_pro_active(path: Path | None = None) -> bool:
    """``True`` when a valid, non-expired, paid-tier license is installed."""
    license_obj = current_license(path)
    return license_obj is not None and license_obj.is_paid


def has_feature(feature: str, path: Path | None = None) -> bool:
    """``True`` when a valid license is installed and grants ``feature``."""
    license_obj = current_license(path)
    return license_obj is not None and license_obj.has_feature(feature)
