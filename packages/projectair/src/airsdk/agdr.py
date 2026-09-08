"""AgDR signing, verification, and chain walking.

BLAKE3 for content hashing; Ed25519 or ML-DSA-65 (FIPS 204) for signatures.
See ``types`` module for the record shape and chain semantics.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import blake3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from airsdk._compat import UTC

try:
    # `X as X` marks these as explicit re-exports so downstream modules can
    # import them from airsdk.agdr under mypy --strict (no-implicit-reexport).
    from cryptography.hazmat.primitives.asymmetric.mldsa import (
        MLDSA65PrivateKey as MLDSA65PrivateKey,
    )
    from cryptography.hazmat.primitives.asymmetric.mldsa import (
        MLDSA65PublicKey as MLDSA65PublicKey,
    )
    _HAS_MLDSA = True
except ImportError:
    _HAS_MLDSA = False
    MLDSA65PrivateKey = None  # type: ignore[assignment,misc]
    MLDSA65PublicKey = None  # type: ignore[assignment,misc]

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
    SigningAlgorithm,
    StepKind,
    VerificationResult,
    VerificationStatus,
)

SigningKey = Ed25519PrivateKey | MLDSA65PrivateKey

_MLDSA_UNAVAILABLE = (
    "ML-DSA-65 (FIPS 204) post-quantum signing requires cryptography>=48 "
    "(OpenSSL 3.5). The installed cryptography is older. Ed25519 signing and "
    "verification are unaffected. To enable ML-DSA-65, run: "
    "pip install 'projectair[pqc]'"
)


def mldsa_available() -> bool:
    """``True`` when this install can sign and verify ML-DSA-65 records."""
    return _HAS_MLDSA


def _require_mldsa() -> None:
    """Raise a clear RuntimeError when ML-DSA-65 is requested but unavailable."""
    if not _HAS_MLDSA:
        raise RuntimeError(_MLDSA_UNAVAILABLE)


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


def _meta_hash(*, step_id: str, timestamp: str, kind: str, algorithm: str) -> str:
    """BLAKE3 over the record metadata bound into the signature (meta_signed=True).

    Binding step_id, timestamp, kind, and signature_algorithm closes the gap
    where those fields sat outside the signed material and could be altered
    without breaking ``verify_record``.
    """
    return _blake3_hex(
        _canonical_json(
            {
                "step_id": step_id,
                "timestamp": timestamp,
                "kind": kind,
                "signature_algorithm": algorithm,
            }
        )
    )


def _sig_material(prev_hash: str, content_hash: str, meta_hash: str | None) -> bytes:
    material = bytes.fromhex(prev_hash) + bytes.fromhex(content_hash)
    if meta_hash is not None:
        material += bytes.fromhex(meta_hash)
    return material


class Signer:
    """Holds a keypair and emits signed AgDRRecord instances in chain order.

    Usage:
        signer = Signer.from_env()   # or Signer.generate()
        rec = signer.sign(kind=StepKind.LLM_START, payload={"prompt": "..."})
        next_rec = signer.sign(kind=StepKind.LLM_END, payload={"response": "..."})

    ML-DSA-65 (FIPS 204, experimental):
        signer = Signer.generate(algorithm=SigningAlgorithm.ML_DSA_65)
    """

    def __init__(self, private_key: SigningKey, prev_hash: str = GENESIS_PREV_HASH) -> None:
        self._priv = private_key
        self._pub = private_key.public_key()
        self._prev_hash = prev_hash
        self._signer_key_hex = self._pub.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        if _HAS_MLDSA and isinstance(private_key, MLDSA65PrivateKey):
            self._algorithm = SigningAlgorithm.ML_DSA_65
        else:
            self._algorithm = SigningAlgorithm.ED25519

    @classmethod
    def generate(cls, algorithm: SigningAlgorithm = SigningAlgorithm.ED25519) -> Signer:
        if algorithm == SigningAlgorithm.ML_DSA_65:
            _require_mldsa()
            return cls(MLDSA65PrivateKey.generate())
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_env(
        cls,
        env_var: str = "AIRSDK_SIGNING_KEY",
        *,
        algorithm: SigningAlgorithm = SigningAlgorithm.ED25519,
    ) -> Signer:
        """Load a private key from a PEM or raw-hex env var.

        PEM keys are auto-detected (Ed25519 or ML-DSA-65). Hex seeds
        require the ``algorithm`` hint since both use 32-byte seeds.
        Falls back to ``generate(algorithm)`` when the env var is unset.
        """
        raw = os.environ.get(env_var)
        if raw is None:
            return cls.generate(algorithm)
        data = raw.strip()
        if data.startswith("-----BEGIN"):
            priv = load_pem_private_key(data.encode(), password=None)
            if isinstance(priv, Ed25519PrivateKey):
                return cls(priv)
            if _HAS_MLDSA and isinstance(priv, MLDSA65PrivateKey):
                return cls(priv)
            raise ValueError(f"{env_var} must hold an Ed25519 or ML-DSA-65 key, got {type(priv).__name__}")
        try:
            key_bytes = bytes.fromhex(data)
        except ValueError as exc:
            raise ValueError(f"{env_var} is neither PEM nor valid hex seed") from exc
        if len(key_bytes) != 32:
            raise ValueError(f"{env_var} hex seed must decode to 32 bytes, got {len(key_bytes)}")
        if algorithm == SigningAlgorithm.ML_DSA_65:
            _require_mldsa()
            return cls(MLDSA65PrivateKey.from_seed_bytes(key_bytes))
        return cls(Ed25519PrivateKey.from_private_bytes(key_bytes))

    @property
    def algorithm(self) -> SigningAlgorithm:
        return self._algorithm

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
        step_id = _uuid7()
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        meta_hash = _meta_hash(
            step_id=step_id,
            timestamp=timestamp,
            kind=kind.value,
            algorithm=self._algorithm.value,
        )
        sig_material = _sig_material(self._prev_hash, content_hash, meta_hash)
        signature_hex = self._priv.sign(sig_material).hex()

        record = AgDRRecord(
            step_id=step_id,
            timestamp=timestamp,
            kind=kind,
            payload=payload,
            prev_hash=self._prev_hash,
            content_hash=content_hash,
            signature=signature_hex,
            signer_key=self._signer_key_hex,
            signature_algorithm=self._algorithm,
            meta_signed=True,
        )
        self._prev_hash = content_hash
        return record


def verify_record(record: AgDRRecord) -> tuple[bool, str | None]:
    """Recompute content_hash and verify signature against the record's signer_key.

    Dispatches to Ed25519 or ML-DSA-65 based on ``record.signature_algorithm``.
    Records without the field (v0.4 and earlier) default to Ed25519.

    When ``record.meta_signed`` is True the signed material also covers the
    record metadata (step_id, timestamp, kind, signature_algorithm), so those
    fields cannot be altered without breaking verification. Legacy records
    (meta_signed False) verify over prev_hash + content_hash exactly as before.

    Returns (ok, reason). reason is None when ok is True.
    """
    payload_dict = record.payload.model_dump(exclude_none=True)
    expected_hash = _blake3_hex(_canonical_json(payload_dict))
    if expected_hash != record.content_hash:
        return False, f"content_hash mismatch: expected {expected_hash}, got {record.content_hash}"

    algo = record.signature_algorithm
    try:
        key_bytes = bytes.fromhex(record.signer_key)
        meta_hash = (
            _meta_hash(
                step_id=record.step_id,
                timestamp=record.timestamp,
                kind=record.kind.value,
                algorithm=str(record.signature_algorithm),
            )
            if record.meta_signed
            else None
        )
        sig_material = _sig_material(record.prev_hash, record.content_hash, meta_hash)
        sig_bytes = bytes.fromhex(record.signature)
        if algo == SigningAlgorithm.ML_DSA_65:
            if not _HAS_MLDSA:
                return False, _MLDSA_UNAVAILABLE
            MLDSA65PublicKey.from_public_bytes(key_bytes).verify(sig_bytes, sig_material)
        else:
            Ed25519PublicKey.from_public_bytes(key_bytes).verify(sig_bytes, sig_material)
    except InvalidSignature:
        return False, f"{algo} signature did not verify"
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


def filter_records_by_date_range(
    records: list[AgDRRecord],
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[AgDRRecord]:
    """Return records whose timestamp falls within [from_date, to_date] inclusive.

    Both bounds are optional; when both are None the input is returned unchanged.
    Records with unparseable timestamps are excluded when any bound is set.
    """
    if from_date is None and to_date is None:
        return records

    filtered: list[AgDRRecord] = []
    for record in records:
        ts = record.timestamp
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        try:
            record_dt = datetime.fromisoformat(normalized)
        except (ValueError, TypeError):
            continue
        record_date = record_dt.date()
        if from_date is not None and record_date < from_date:
            continue
        if to_date is not None and record_date > to_date:
            continue
        filtered.append(record)
    return filtered


def export_private_key_pem(signer: Signer) -> bytes:
    """PEM bytes of the signer's private key. Works for Ed25519 and ML-DSA-65."""
    return signer._priv.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
