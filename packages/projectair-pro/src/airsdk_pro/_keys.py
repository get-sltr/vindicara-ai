"""Vendor public key embedded in the projectair-pro distribution.

This is the Ed25519 public key whose corresponding private key Vindicara uses
to sign license tokens. Verification is local: a token is accepted only if its
signature validates against this public key. The private key never leaves
Vindicara's infrastructure.

Replacing this constant with a different public key invalidates every license
issued against the original. The constant is therefore versioned in code and
should never be edited except as part of a deliberate, advertised key rotation.
"""
from __future__ import annotations

# Ed25519 public key (raw, 32 bytes, hex-encoded).
#
# Corrected 2026-09-08. The original constant (e992bb1f..., "generated
# 2026-04-27") never had a private key anywhere: not in Secrets Manager in any
# region, not on disk. The issuer has always signed with the key in
# Vindicara_dashboard.license_signing_key_pem, whose public half is the value
# below, so every token ever minted failed verification here. Nothing was
# invalidated by this change; tokens that could not verify now can. The drift
# went unnoticed because no test compared the two sides, which
# vindicara.licensing.issuer now enforces at mint time.
VENDOR_LICENSE_PUBLIC_KEY_HEX: str = "8627b4309db46b9fa42ac9c47c9a409819d1e62cfd4ab079609a78db2d587d23"
