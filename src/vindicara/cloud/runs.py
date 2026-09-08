"""Run lineage and run detail, as pure functions over records.

Resolution order for the run a record belongs to:

1. The client said so. ``X-AIR-Run-Id`` carries the genesis step_id; the
   SDK and ``air push`` both know it, and it lives outside the signed record
   so ``content_hash`` is untouched.
2. Lineage inside the batch. A whole chain pushed in one request resolves by
   walking ``prev_hash`` to ``content_hash`` within the batch, in any order.
3. Otherwise the record is its own run. A 1.3.x client posting one record
   at a time with no header lands here; ``group_runs`` re-joins such rows
   in memory when a whole workspace is read.

Detail is assembled from the same primitives the CLI uses (``verify_chain``,
``run_detectors``, ``assemble_incident``, ``assess_health``), so what the
console shows is exactly what ``air trace`` and ``air incident`` would say.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from airsdk.agdr import verify_chain
from airsdk.detections import run_detectors
from airsdk.health import EvidenceHealth, assess_health
from airsdk.incident import IncidentTimeline, assemble_incident
from airsdk.types import GENESIS_PREV_HASH, AgDRRecord, Finding, VerificationResult
from pydantic import BaseModel, ConfigDict

from vindicara.cloud.run_store import RunSummary

if TYPE_CHECKING:
    from vindicara.cloud.capsule_store import StoredCapsule

_RUN_ID_RE = re.compile(r"^[0-9a-fA-F-]{8,64}$")
_SEVERITY_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}


def valid_run_id(value: str | None) -> str | None:
    """A client-supplied run id, or ``None`` when absent or malformed."""
    if value and _RUN_ID_RE.match(value):
        return value
    return None


def _sort_key(record: AgDRRecord) -> tuple[str, str]:
    return (record.timestamp, record.step_id)


def _parent_in(candidates: list[AgDRRecord], child: AgDRRecord) -> AgDRRecord | None:
    """The record ``child`` links to. ``content_hash`` covers the payload only, so
    two records with identical payloads share a hash; the parent is the latest
    candidate signed no later than the child (timestamps carry microseconds,
    step ids break ties), never the child itself."""
    others = [c for c in candidates if c.step_id != child.step_id]
    earlier = [c for c in others if _sort_key(c) <= _sort_key(child)]
    pool = earlier or others
    return max(pool, key=_sort_key) if pool else None


def resolve_run_ids(records: list[AgDRRecord], *, header_run_id: str | None) -> list[str]:
    """One run id per record, in input order."""
    if header_run_id is not None:
        return [header_run_id] * len(records)
    by_hash: dict[str, list[AgDRRecord]] = {}
    for record in records:
        by_hash.setdefault(record.content_hash, []).append(record)
    resolved: dict[str, str] = {}  # step_id -> run_id

    def resolve(record: AgDRRecord) -> str:
        chain: list[AgDRRecord] = []
        visited: set[str] = set()
        current: AgDRRecord | None = record
        while current is not None and current.step_id not in resolved and current.step_id not in visited:
            visited.add(current.step_id)
            chain.append(current)
            if current.prev_hash == GENESIS_PREV_HASH:
                current = None
                break
            current = _parent_in(by_hash.get(current.prev_hash, []), current)
        root = resolved[current.step_id] if current is not None and current.step_id in resolved else chain[-1].step_id
        for item in chain:
            resolved[item.step_id] = root
        return root

    return [resolve(r) for r in records]


def order_chain(records: list[AgDRRecord]) -> list[AgDRRecord]:
    """Genesis first, then each record whose prev_hash is the previous content_hash."""
    by_prev: dict[str, list[AgDRRecord]] = {}
    for record in records:
        by_prev.setdefault(record.prev_hash, []).append(record)
    ordered: list[AgDRRecord] = []
    seen: set[str] = set()
    roots = sorted(by_prev.get(GENESIS_PREV_HASH, []), key=_sort_key)
    cursor: AgDRRecord | None = roots[0] if roots else None
    while cursor is not None and cursor.step_id not in seen:
        ordered.append(cursor)
        seen.add(cursor.step_id)
        later = [c for c in by_prev.get(cursor.content_hash, []) if c.step_id not in seen]
        cursor = min(later, key=_sort_key) if later else None
    leftovers = sorted((r for r in records if r.step_id not in seen), key=_sort_key)
    return ordered + leftovers


def group_runs(capsules: list[StoredCapsule]) -> dict[str, list[AgDRRecord]]:
    """Group stored capsules by run, resolving rows that were stored without one."""
    resolved = resolve_run_ids([c.record for c in capsules], header_run_id=None)
    groups: dict[str, list[AgDRRecord]] = {}
    for capsule, fallback in zip(capsules, resolved, strict=True):
        groups.setdefault(capsule.run_id or fallback, []).append(capsule.record)
    return groups


def summarize_batch(workspace_id: str, run_id: str, records: list[AgDRRecord], *, api_key_id: str) -> RunSummary:
    """A partial summary of one ingest batch, ready to be merged into the run's row."""
    timestamps = [r.timestamp for r in records]
    intent = next((r.payload.user_intent for r in records if r.payload.user_intent), None)
    return RunSummary(
        run_id=run_id,
        workspace_id=workspace_id,
        api_key_id=api_key_id,
        first_at=min(timestamps),
        last_at=max(timestamps),
        records=len(records),
        kinds=dict(Counter(r.kind.value for r in records)),
        user_intent=intent,
        signer_key=records[0].signer_key,
    )


class RunDetail(BaseModel):
    """Everything the run page needs except record bodies (paged separately)."""

    model_config = ConfigDict(extra="forbid")

    summary: RunSummary
    verification: VerificationResult
    findings: list[Finding]
    timeline: IncidentTimeline
    health: EvidenceHealth
    console_url: str


def assess_run(summary: RunSummary, records: list[AgDRRecord], *, console_url: str) -> RunDetail:
    """Verify, detect, and assemble the timeline and health for one run."""
    ordered = order_chain(records)
    source = f"air-cloud:{summary.workspace_id}/{summary.run_id}"
    verification = verify_chain(ordered)
    findings = run_detectors(ordered)
    timeline = assemble_incident(ordered, findings, source_log=source)
    health = assess_health(ordered, source_log=source)
    worst = max((f.severity for f in findings), key=lambda s: _SEVERITY_RANK.get(s, -1), default=None)
    assessed = summary.model_copy(
        update={
            "verification": verification.status.value,
            "findings": len(findings),
            "max_severity": worst,
            "assessed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "records": len(ordered),
        }
    )
    return RunDetail(
        summary=assessed, verification=verification, findings=findings, timeline=timeline, health=health,
        console_url=f"{console_url.rstrip('/')}/runs/{summary.run_id}",
    )


__all__ = ["RunDetail", "assess_run", "group_runs", "order_chain", "resolve_run_ids", "summarize_batch", "valid_run_id"]
