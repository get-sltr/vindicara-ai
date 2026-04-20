"""AgDR record types.

AgDR (AI Decision Record) is the canonical unit of forensic evidence Project AIR
writes for every agent step. Each record is content-hashed with BLAKE3 and signed
with Ed25519. The signature covers both the record's content_hash AND the previous
record's content_hash, producing a tamper-evident hash chain.

Session 1 shape (stable within session, may evolve with version field bump):

    {
      "step_id":      UUIDv7        one per step, monotonic timestamp prefix
      "timestamp":    ISO 8601 UTC  when the step happened
      "kind":         enum          llm_start | llm_end | tool_start | tool_end | agent_finish
      "payload":      object        kind-specific contents (prompt, response, tool name, args)
      "prev_hash":    hex string    content_hash of previous record, or "0"*64 for first
      "content_hash": hex string    BLAKE3 of canonical(payload) - computed by signer
      "signature":    hex string    Ed25519(prev_hash || content_hash) - computed by signer
      "signer_key":   hex string    Ed25519 public key, for offline verification
    }

Verification walks the chain forward: for each record, recompute content_hash from
payload, assert signature verifies (prev_hash || content_hash) against signer_key,
assert this record's prev_hash equals the last record's content_hash.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# 64 hex chars = 256 bits. BLAKE3 default output size and Ed25519 public key size.
GENESIS_PREV_HASH = "0" * 64

AGDR_VERSION = "0.1"


class StepKind(StrEnum):
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    AGENT_FINISH = "agent_finish"


class AgDRPayload(BaseModel):
    """Kind-specific payload. Structured but extensible via `extra`."""

    model_config = ConfigDict(extra="allow")

    prompt: str | None = None
    response: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_output: str | None = None
    user_intent: str | None = None
    final_output: str | None = None


class AgDRRecord(BaseModel):
    """One signed entry in the forensic chain."""

    model_config = ConfigDict(extra="forbid")

    version: str = AGDR_VERSION
    step_id: str
    timestamp: str
    kind: StepKind
    payload: AgDRPayload
    prev_hash: str = Field(min_length=64, max_length=64)
    content_hash: str = Field(min_length=64, max_length=64)
    signature: str
    signer_key: str


class Finding(BaseModel):
    """One detection surfaced by `air trace`."""

    model_config = ConfigDict(extra="forbid")

    asi_id: str
    title: str
    severity: str
    step_id: str
    step_index: int
    description: str


class VerificationStatus(StrEnum):
    OK = "ok"
    TAMPERED = "tampered"
    BROKEN_CHAIN = "broken_chain"


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: VerificationStatus
    records_verified: int
    failed_step_id: str | None = None
    reason: str | None = None


class ForensicReport(BaseModel):
    """The full output of `air trace`."""

    model_config = ConfigDict(extra="forbid")

    air_version: str
    report_id: str
    source_log: str
    generated_at: str
    records: int
    conversations: int
    verification: VerificationResult
    findings: list[Finding]
