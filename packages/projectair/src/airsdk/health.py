"""Evidence health: is the record complete, and is verification working?

A chain that verifies is not the same as a chain you can rely on. The
signatures can all check out while half the tool calls never got a
``tool_end``, the last anchor is three hours behind the tail, the signing
key rotated without a transition record, or the records were signed with
an algorithm this install cannot verify at all. Each of those is a fact
about the *evidence*, not about the agent, and until now the only way to
learn them was to read four different commands and do the arithmetic.

:func:`assess_health` runs eight checks over one chain and returns an
:class:`EvidenceHealth` whose level is the worst check. It is offline and
read-only: anchors are counted, not re-verified (that is
``air verify-public``). ``air health`` prints it and exits non-zero on a
failure, so it can sit in a cron job or a CI step next to the agent.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from airsdk import __version__
from airsdk._compat import UTC, StrEnum
from airsdk._incident_authority import AuthorityKind, resolve_authority
from airsdk.agdr import mldsa_available, verify_chain
from airsdk.detections import IMPLEMENTED_AIR_DETECTORS, IMPLEMENTED_ASI_DETECTORS, run_detectors
from airsdk.key_custody import KeyCustodyStatus, verify_key_custody
from airsdk.registry import AgentRegistry
from airsdk.types import AgDRRecord, Finding, SigningAlgorithm, StepKind, VerificationStatus

READINESS = "beta"

#: Anchoring cadence the default ``AnchoringPolicy`` promises (100 steps / 10 s).
#: The tail is flagged when it is a full cadence of steps behind, or six
#: cadences of wall clock, so an idle chain is not nagged about one record.
ANCHOR_TAIL_STEPS = 100
ANCHOR_TAIL_SECONDS = 60.0
#: A chain whose newest record is older than this is reported, not failed.
STALE_AFTER_SECONDS = 24 * 3600.0

_ZERO_TRUST_DETECTORS = frozenset({"ASI03", "ASI10"})
_CLOSING_KINDS = frozenset({StepKind.AGENT_FINISH, StepKind.ANCHOR, StepKind.AUDIT_REVIEW, StepKind.HUMAN_APPROVAL})


class HealthLevel(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


_RANK = {HealthLevel.OK: 0, HealthLevel.WARN: 1, HealthLevel.FAIL: 2}


class HealthCheck(BaseModel):
    """One named check, its level, a sentence a human can act on, and the numbers behind it."""

    model_config = ConfigDict(extra="forbid")

    key: str
    title: str
    level: HealthLevel
    detail: str
    metrics: dict[str, int | float | str] = Field(default_factory=dict)


class EvidenceHealth(BaseModel):
    """The full output of ``air health`` for one chain."""

    model_config = ConfigDict(extra="forbid")

    air_version: str
    readiness: str
    source_log: str
    generated_at: str
    records: int
    level: HealthLevel
    checks: list[HealthCheck]
    findings_by_severity: dict[str, int]

    def check(self, key: str) -> HealthCheck:
        return next(c for c in self.checks if c.key == key)


def _epoch(timestamp: str) -> float | None:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _check_integrity(records: list[AgDRRecord]) -> HealthCheck:
    result = verify_chain(records)
    if result.status == VerificationStatus.OK:
        return HealthCheck(key="integrity", title="Chain integrity", level=HealthLevel.OK,
                           detail=f"{result.records_verified} record(s) verify and link", metrics={"verified": result.records_verified})
    return HealthCheck(key="integrity", title="Chain integrity", level=HealthLevel.FAIL,
                       detail=f"{result.status.value} at record {result.records_verified}: {result.reason}",
                       metrics={"verified": result.records_verified, "status": result.status.value})


def _check_custody(records: list[AgDRRecord]) -> HealthCheck:
    result = verify_key_custody(records)
    keys = len({r.signer_key for r in records})
    metrics: dict[str, int | float | str] = {"signing_keys": keys, "rotations": result.rotations}
    if result.status == KeyCustodyStatus.OK:
        return HealthCheck(key="custody", title="Key custody", level=HealthLevel.OK,
                           detail=f"{keys} signing key(s), {result.rotations} authorized rotation(s)", metrics=metrics)
    return HealthCheck(key="custody", title="Key custody", level=HealthLevel.FAIL,
                       detail=f"{result.status.value} at record {result.records_verified}: {result.reason}", metrics=metrics)


def _check_algorithms(records: list[AgDRRecord]) -> HealthCheck:
    algorithms = sorted({r.signature_algorithm for r in records})
    metrics: dict[str, int | float | str] = {"algorithms": ", ".join(algorithms)}
    if SigningAlgorithm.ML_DSA_65.value in algorithms and not mldsa_available():
        return HealthCheck(key="verifiable", title="Verification support", level=HealthLevel.FAIL,
                           detail="chain carries ML-DSA-65 signatures this install cannot verify; pip install 'projectair[pqc]'",
                           metrics=metrics)
    return HealthCheck(key="verifiable", title="Verification support", level=HealthLevel.OK,
                       detail=f"every signature algorithm present ({', '.join(algorithms)}) is verifiable here", metrics=metrics)


def _check_completeness(records: list[AgDRRecord], findings: list[Finding]) -> HealthCheck:
    gaps = [f for f in findings if f.detector_id == "AIR-04"]
    unpaired_tool = sum(1 for f in gaps if "tool_start" in f.description)
    unpaired_llm = sum(1 for f in gaps if "llm_start" in f.description)
    silent = len(gaps) - unpaired_tool - unpaired_llm
    tool_calls = sum(1 for r in records if r.kind == StepKind.TOOL_START and not r.payload.blocked)
    llm_calls = sum(1 for r in records if r.kind == StepKind.LLM_START)
    last = records[-1].kind
    open_tail = last in {StepKind.TOOL_START, StepKind.LLM_START}
    metrics: dict[str, int | float | str] = {
        "tool_calls": tool_calls, "tool_calls_closed": tool_calls - unpaired_tool,
        "llm_calls": llm_calls, "llm_calls_closed": llm_calls - unpaired_llm,
        "silent_intervals": silent, "last_record": last.value,
    }
    problems = []
    if unpaired_tool:
        problems.append(f"{unpaired_tool} of {tool_calls} tool call(s) never recorded an outcome")
    if unpaired_llm:
        problems.append(f"{unpaired_llm} of {llm_calls} model call(s) never recorded a response")
    if silent:
        problems.append(f"{silent} silent interval(s) over five minutes")
    if open_tail:
        problems.append(f"chain ends on an open {last.value}: the session is still running or it crashed")
    if problems:
        return HealthCheck(key="completeness", title="Completeness", level=HealthLevel.WARN, detail="; ".join(problems), metrics=metrics)
    closed = "closed" if last in _CLOSING_KINDS else f"last record {last.value}"
    return HealthCheck(key="completeness", title="Completeness", level=HealthLevel.OK,
                       detail=f"every tool and model call has its outcome recorded; {closed}", metrics=metrics)


def _check_anchoring(records: list[AgDRRecord]) -> HealthCheck:
    anchors = [(i, r) for i, r in enumerate(records) if r.kind == StepKind.ANCHOR]
    if not anchors:
        return HealthCheck(key="anchoring", title="External anchoring", level=HealthLevel.WARN,
                           detail="no anchor record: timing rests on the agent's own clock and key (run air anchor)",
                           metrics={"anchors": 0, "unanchored_records": len(records)})
    last_index, last_anchor = anchors[-1]
    tail = [r for r in records[last_index + 1:] if r.kind != StepKind.ANCHOR]
    tail_seconds = 0.0
    if tail:
        start, end = _epoch(last_anchor.timestamp), _epoch(records[-1].timestamp)
        tail_seconds = max(0.0, end - start) if start is not None and end is not None else 0.0
    services = [s for s, present in (("RFC 3161", last_anchor.payload.rfc3161), ("Rekor", last_anchor.payload.rekor)) if present]
    metrics: dict[str, int | float | str] = {
        "anchors": len(anchors), "unanchored_records": len(tail), "tail_seconds": round(tail_seconds, 1),
        "services": ", ".join(services) or "none",
    }
    if len(tail) > ANCHOR_TAIL_STEPS or (tail and tail_seconds > ANCHOR_TAIL_SECONDS):
        return HealthCheck(key="anchoring", title="External anchoring", level=HealthLevel.WARN,
                           detail=f"{len(tail)} record(s) spanning {tail_seconds:.0f}s after the last anchor are not externally witnessed",
                           metrics=metrics)
    return HealthCheck(key="anchoring", title="External anchoring", level=HealthLevel.OK,
                       detail=f"{len(anchors)} anchor(s) ({', '.join(services) or 'no service recorded'}); {len(tail)} record(s) in the unanchored tail",
                       metrics=metrics)


def _check_authority(records: list[AgDRRecord]) -> HealthCheck:
    kinds = Counter(a.kind for a in resolve_authority(records))
    metrics: dict[str, int | float | str] = {k.value: n for k, n in kinds.items()}
    if kinds[AuthorityKind.EXPIRED]:
        return HealthCheck(key="authority", title="Authority binding", level=HealthLevel.WARN,
                           detail=f"{kinds[AuthorityKind.EXPIRED]} record(s) ran after the delegation expired", metrics=metrics)
    if kinds[AuthorityKind.DELEGATED] or kinds[AuthorityKind.APPROVED]:
        return HealthCheck(key="authority", title="Authority binding", level=HealthLevel.OK,
                           detail="session is bound to an identity-verified human", metrics=metrics)
    if kinds[AuthorityKind.DECLARED]:
        return HealthCheck(key="authority", title="Authority binding", level=HealthLevel.WARN,
                           detail="scope is declared but no human identity is bound to the session (open it with a DelegationGrant)",
                           metrics=metrics)
    return HealthCheck(key="authority", title="Authority binding", level=HealthLevel.WARN,
                       detail="no delegation, approval, or declared scope: only the agent signing key vouches for every step",
                       metrics=metrics)


def _check_detectors(findings: list[Finding], registry: AgentRegistry | None) -> HealthCheck:
    total = len(IMPLEMENTED_ASI_DETECTORS) + len(IMPLEMENTED_AIR_DETECTORS)
    active = total if registry is not None else total - len(_ZERO_TRUST_DETECTORS)
    severities = Counter(f.severity for f in findings)
    metrics: dict[str, int | float | str] = {"active": active, "total": total, "findings": len(findings)}
    note = "" if registry is not None else "; ASI03 / ASI10 need --agent-registry"
    return HealthCheck(key="detectors", title="Detectors", level=HealthLevel.OK,
                       detail=f"{active} of {total} detectors ran, {len(findings)} finding(s)"
                       + (f" ({', '.join(f'{n} {s}' for s, n in severities.most_common())})" if findings else "") + note,
                       metrics=metrics)


def _check_freshness(records: list[AgDRRecord], now: datetime) -> HealthCheck:
    newest = _epoch(records[-1].timestamp)
    if newest is None:
        return HealthCheck(key="freshness", title="Freshness", level=HealthLevel.WARN,
                           detail=f"last record timestamp {records[-1].timestamp!r} is not ISO 8601", metrics={})
    age = max(0.0, now.timestamp() - newest)
    metrics: dict[str, int | float | str] = {"age_seconds": round(age, 1), "last_timestamp": records[-1].timestamp}
    stale = " (older than 24h)" if age > STALE_AFTER_SECONDS else ""
    return HealthCheck(key="freshness", title="Freshness", level=HealthLevel.OK,
                       detail=f"newest record is {age / 60:.0f} min old{stale}", metrics=metrics)


def assess_health(
    records: list[AgDRRecord],
    *,
    source_log: str,
    registry: AgentRegistry | None = None,
    now: datetime | None = None,
) -> EvidenceHealth:
    """Run every check over ``records`` and return the aggregate."""
    now = now or datetime.now(UTC)
    generated = now.isoformat().replace("+00:00", "Z")
    if not records:
        empty = HealthCheck(key="integrity", title="Chain integrity", level=HealthLevel.FAIL, detail="chain is empty", metrics={})
        return EvidenceHealth(air_version=__version__, readiness=READINESS, source_log=source_log, generated_at=generated,
                              records=0, level=HealthLevel.FAIL, checks=[empty], findings_by_severity={})
    findings = run_detectors(records, registry=registry)
    checks = [
        _check_integrity(records),
        _check_custody(records),
        _check_algorithms(records),
        _check_completeness(records, findings),
        _check_anchoring(records),
        _check_authority(records),
        _check_detectors(findings, registry),
        _check_freshness(records, now),
    ]
    level = max((c.level for c in checks), key=lambda lv: _RANK[lv])
    return EvidenceHealth(
        air_version=__version__, readiness=READINESS, source_log=source_log, generated_at=generated,
        records=len(records), level=level, checks=checks,
        findings_by_severity=dict(Counter(f.severity for f in findings)),
    )
