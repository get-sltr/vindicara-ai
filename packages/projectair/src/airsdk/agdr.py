"""AgDR signing, verification, and chain walking.

BLAKE3 for content hashing, Ed25519 for signatures. See ``types`` module for
the record shape and chain semantics.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import blake3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

from airsdk.types import (
    GENESIS_PREV_HASH,
    AgDRPayload,
    AgDRRecord,
    StepKind,
    VerificationResult,
    VerificationStatus,
)


def _canonical_json(obj: Any) -> bytes:
    """Stable JSON encoding: sorted keys, no extraneous whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _uuid7() -> str:
    """RFC 9562 UUIDv7: 48-bit Unix millisecond timestamp prefix, random tail.

    Preferred over UUIDv4 because AgDR chains benefit from timestamp-sortable IDs.
    """
    ms = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    # Layout: 48b ms | 4b ver(0111) | 12b rand_a | 2b var(10) | 62b rand_b
    value = (ms & ((1 << 48) - 1)) << 80
    value |= 0x7 << 76
    value |= (rand_a & 0xFFF) << 64
    value |= 0b10 << 62
    value |= rand_b & ((1 << 62) - 1)
    hex_ = f"{value:032x}"
    return f"{hex_[0:8]}-{hex_[8:12]}-{hex_[12:16]}-{hex_[16:20]}-{hex_[20:32]}"


def _blake3_hex(data: bytes) -> str:
    return blake3.blake3(data).hexdigest()


class Signer:
    """Holds a keypair and emits signed AgDRRecord instances in chain order.

    Usage:
        signer = Signer.from_env()   # or Signer.generate()
        rec = signer.sign(kind=StepKind.LLM_START, payload={"prompt": "..."})
        next_rec = signer.sign(kind=StepKind.LLM_END, payload={"response": "..."})
    """

    def __init__(self, private_key: Ed25519PrivateKey, prev_hash: str = GENESIS_PREV_HASH) -> None:
        self._priv = private_key
        self._pub = private_key.public_key()
        self._prev_hash = prev_hash
        self._signer_key_hex = self._pub.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()

    @classmethod
    def generate(cls) -> Signer:
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_env(cls, env_var: str = "AIRSDK_SIGNING_KEY") -> Signer:
        """Load an Ed25519 private key from a PEM or raw-hex env var.

        Falls back to ``generate()`` when the env var is unset. This lets local
        development work without setup while still supporting stable keys in CI
        and production.
        """
        raw = os.environ.get(env_var)
        if raw is None:
            return cls.generate()
        data = raw.strip()
        if data.startswith("-----BEGIN"):
            priv = load_pem_private_key(data.encode(), password=None)
            if not isinstance(priv, Ed25519PrivateKey):
                raise ValueError(f"{env_var} must hold an Ed25519 key, got {type(priv).__name__}")
            return cls(priv)
        try:
            key_bytes = bytes.fromhex(data)
        except ValueError as exc:
            raise ValueError(f"{env_var} is neither PEM nor hex-encoded Ed25519 seed") from exc
        if len(key_bytes) != 32:
            raise ValueError(f"{env_var} hex seed must decode to 32 bytes, got {len(key_bytes)}")
        return cls(Ed25519PrivateKey.from_private_bytes(key_bytes))

    @property
    def public_key_hex(self) -> str:
        return self._signer_key_hex

    @property
    def head_hash(self) -> str:
        return self._prev_hash

    def sign(self, kind: StepKind, payload: AgDRPayload | dict[str, Any]) -> AgDRRecord:
        if isinstance(payload, dict):
            payload = AgDRPayload.model_validate(payload)

        payload_dict = payload.model_dump(exclude_none=True)
        content_hash = _blake3_hex(_canonical_json(payload_dict))
        sig_material = bytes.fromhex(self._prev_hash) + bytes.fromhex(content_hash)
        signature_hex = self._priv.sign(sig_material).hex()

        record = AgDRRecord(
            step_id=_uuid7(),
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            kind=kind,
            payload=payload,
            prev_hash=self._prev_hash,
            content_hash=content_hash,
            signature=signature_hex,
            signer_key=self._signer_key_hex,
        )
        self._prev_hash = content_hash
        return record


def verify_record(record: AgDRRecord) -> tuple[bool, str | None]:
    """Recompute content_hash and verify Ed25519 signature against the record's signer_key.

    Returns (ok, reason). reason is None when ok is True.
    """
    payload_dict = record.payload.model_dump(exclude_none=True)
    expected_hash = _blake3_hex(_canonical_json(payload_dict))
    if expected_hash != record.content_hash:
        return False, f"content_hash mismatch: expected {expected_hash}, got {record.content_hash}"

    try:
        signer_key_bytes = bytes.fromhex(record.signer_key)
        pub = Ed25519PublicKey.from_public_bytes(signer_key_bytes)
        sig_material = bytes.fromhex(record.prev_hash) + bytes.fromhex(record.content_hash)
        pub.verify(bytes.fromhex(record.signature), sig_material)
    except InvalidSignature:
        return False, "Ed25519 signature did not verify"
    except ValueError as exc:
        return False, f"signer_key or signature not valid hex: {exc}"
    return True, None


def verify_chain(records: list[AgDRRecord]) -> VerificationResult:
    """Walk the chain forward. Every record must verify and link to its predecessor."""
    if not records:
        return VerificationResult(status=VerificationStatus.OK, records_verified=0)

    expected_prev = GENESIS_PREV_HASH
    for index, record in enumerate(records):
        if record.prev_hash != expected_prev:
            return VerificationResult(
                status=VerificationStatus.BROKEN_CHAIN,
                records_verified=index,
                failed_step_id=record.step_id,
                reason=(
                    f"chain break at index {index}: "
                    f"expected prev_hash {expected_prev}, got {record.prev_hash}"
                ),
            )
        ok, reason = verify_record(record)
        if not ok:
            return VerificationResult(
                status=VerificationStatus.TAMPERED,
                records_verified=index,
                failed_step_id=record.step_id,
                reason=reason,
            )
        expected_prev = record.content_hash

    return VerificationResult(status=VerificationStatus.OK, records_verified=len(records))


def load_chain(path: str | Path) -> list[AgDRRecord]:
    """Read a JSON-lines AgDR log and return typed records. Raises on malformed lines."""
    records: list[AgDRRecord] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(AgDRRecord.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(f"malformed AgDR record on line {line_number}: {exc}") from exc
    return records


def export_private_key_pem(signer: Signer) -> bytes:
    """PEM bytes of the signer's private key. Useful when persisting generated keys."""
    return signer._priv.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
