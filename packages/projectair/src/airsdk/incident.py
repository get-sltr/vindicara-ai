"""Incident timeline: what executed, under whose authority, where evidence is missing.

``air trace`` tells you the chain verifies and which detectors fired.
``air explain`` tells you which records caused a step. Neither answers the
three questions an incident review actually asks, side by side, per step:

1. **What executed.** The step, in plain words.
2. **Under whose authority.** The delegation, approval, declared scope, or
   (when none of those exist) the bare fact that only the agent's own key
   vouches for it. See :mod:`airsdk._incident_authority`.
3. **Where the evidence is missing.** Whether the step is signed and
   externally anchored, signed only, sits at a gap the AIR-04 detector
   found, or lies past a verification failure and cannot be trusted.

:func:`assemble_incident` composes those from primitives that already
exist (chain verification, key custody, anchor ranges, the causal graph,
the detectors) into one :class:`IncidentTimeline`. It reads the chain; it
never writes to it, and it never says more than the records show: an
anchor record's presence is reported as "anchored", not as "anchor
verified", because verification of the anchor is ``air verify-public``.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from airsdk import __version__
from airsdk._compat import UTC, StrEnum
from airsdk._incident_authority import AUTHORITY_EVENT_KINDS, Authority, resolve_authority
from airsdk.agdr import verify_chain
from airsdk.causal import build_causal_graph, explain_finding, explain_step
from airsdk.key_custody import KeyCustodyResult, KeyCustodyStatus, verify_key_custody
from airsdk.types import AgDRRecord, Finding, StepKind, VerificationResult, VerificationStatus

#: Readiness label printed on every surface of this feature.
READINESS = "beta"

GAP_DETECTOR = "AIR-04"


class EvidenceStatus(StrEnum):
    ANCHORED = "anchored"  # signed, verified, and inside a range an external anchor covers
    SIGNED = "signed"  # signed and verified; no external anchor covers it
    GAP = "gap"  # signed, but evidence around it is missing (AIR-04)
    UNVERIFIED = "unverified"  # at or past a verification or custody failure; cannot be trusted


class TimelineEntry(BaseModel):
    """One row of the incident timeline."""

    model_config = ConfigDict(extra="forbid")

    ordinal: int
    step_id: str
    timestamp: str
    kind: str
    summary: str
    authority: Authority
    evidence: EvidenceStatus
    evidence_detail: str
    findings: list[str]  # detector ids that flagged this step
    target: bool = False  # the step or finding the timeline was asked about
    in_ancestry: bool = False  # in the causal ancestry of a target

    @property
    def is_authority_event(self) -> bool:
        return self.kind in {k.value for k in AUTHORITY_EVENT_KINDS}


class IncidentTimeline(BaseModel):
    """The full output of ``air incident``."""

    model_config = ConfigDict(extra="forbid")

    air_version: str
    readiness: str
    source_log: str
    generated_at: str
    focus: str | None  # "step 8" or "detector ASI02", None for the whole chain
    verification: VerificationResult
    custody: KeyCustodyResult
    anchors: int
    unanchored_records: int
    entries: list[TimelineEntry]
    gaps: list[str]  # every place the evidence is missing, in chain order
    findings: list[Finding]

    def focused(self) -> list[TimelineEntry]:
        """The rows an incident reviewer needs: targets, their causal ancestry,
        every authority event, every halted action, and every gap."""
        if self.focus is None:
            return list(self.entries)
        return [
            e for e in self.entries
            if e.target or e.in_ancestry or e.is_authority_event
            or e.evidence in {EvidenceStatus.GAP, EvidenceStatus.UNVERIFIED}
            or e.authority.kind.value == "halted"
        ]


def _summarize(record: AgDRRecord, graph_summary: str) -> str:
    p = record.payload
    if record.kind == StepKind.DELEGATION and p.delegation is not None:
        return f"session opened for agent {p.delegation.agent_id}: {p.delegation.scope.goal}"
    if record.kind == StepKind.HUMAN_APPROVAL and p.human_approval is not None:
        return f"human {p.human_approval.decision} for challenge {p.human_approval.challenge_id}"
    if record.kind == StepKind.KEY_TRANSITION and p.key_transition is not None:
        return f"signing key rotated ({p.key_transition.reason})"
    if record.kind == StepKind.AUDIT_REVIEW and p.audit_review is not None:
        return f"audit-trail review: {p.audit_review.outcome}"
    if record.kind == StepKind.GPU_ATTESTATION and p.attestation is not None:
        return f"GPU attestation ({p.attestation.gpu_arch})"
    if record.kind == StepKind.TOOL_START and p.blocked:
        return f"HALTED {graph_summary}"
    return graph_summary


def _anchor_coverage(records: list[AgDRRecord]) -> dict[int, str]:
    """Map each covered ordinal to a short description of the anchor covering it."""
    ordinal_of = {r.step_id: i for i, r in enumerate(records)}
    covered: dict[int, str] = {}
    for index, record in enumerate(records):
        if record.kind != StepKind.ANCHOR or not record.payload.anchored_step_range:
            continue
        rng = record.payload.anchored_step_range
        start = ordinal_of.get(rng.get("from_step_id", ""))
        end = ordinal_of.get(rng.get("to_step_id", ""))
        if start is None or end is None:
            continue
        services = []
        if record.payload.rekor is not None:
            services.append(f"Rekor {record.payload.rekor.log_index}")
        if record.payload.rfc3161 is not None:
            services.append("RFC 3161")
        label = f"anchor at step {index} ({', '.join(services) or 'no service recorded'})"
        for ordinal in range(start, end + 1):
            covered.setdefault(ordinal, label)
    return covered


def _evidence(
    index: int,
    record: AgDRRecord,
    *,
    verification: VerificationResult,
    custody: KeyCustodyResult,
    covered: dict[int, str],
    gap_findings: dict[str, list[Finding]],
) -> tuple[EvidenceStatus, str]:
    if verification.status != VerificationStatus.OK and index >= verification.records_verified:
        if index == verification.records_verified:
            return EvidenceStatus.UNVERIFIED, f"{verification.status.value}: {verification.reason}"
        return EvidenceStatus.UNVERIFIED, f"after {verification.status.value} at step {verification.records_verified}"
    if custody.status != KeyCustodyStatus.OK and index >= custody.records_verified:
        return EvidenceStatus.UNVERIFIED, f"{custody.status.value}: {custody.reason}"
    gaps = gap_findings.get(record.step_id, [])
    if gaps:
        return EvidenceStatus.GAP, "; ".join(f.description for f in gaps)
    if record.kind == StepKind.ANCHOR:
        return EvidenceStatus.SIGNED, "anchor record; verify with air verify-public"
    if index in covered:
        return EvidenceStatus.ANCHORED, covered[index]
    return EvidenceStatus.SIGNED, "signed by the agent key; no external anchor covers this step"


def assemble_incident(
    records: list[AgDRRecord],
    findings: list[Finding],
    *,
    source_log: str,
    step: int | None = None,
    detector: str | None = None,
) -> IncidentTimeline:
    """Build the timeline for ``records``.

    ``step`` (0-based ordinal) or ``detector`` (id such as ``ASI02``) focuses
    the timeline on a target and marks its causal ancestry; pass neither for
    the whole chain. ``findings`` is the output of ``run_detectors`` over the
    same records, so the timeline shows exactly what ``air trace`` showed.
    """
    if step is not None and detector is not None:
        raise ValueError("pass at most one of step= or detector=")
    verification = verify_chain(records)
    custody = verify_key_custody(records)
    covered = _anchor_coverage(records)
    graph = build_causal_graph(records)
    authorities = resolve_authority(records)

    by_step: dict[str, list[Finding]] = {}
    for finding in findings:
        by_step.setdefault(finding.step_id, []).append(finding)
    gap_findings = {sid: [f for f in fs if f.detector_id == GAP_DETECTOR] for sid, fs in by_step.items()}

    targets: set[int] = set()
    ancestry: set[int] = set()
    focus: str | None = None
    if step is not None:
        explanation = explain_step(graph, step)
        targets, focus = set(explanation.targets), f"step {step}"
        ancestry = {n.ordinal for n in explanation.nodes}
    elif detector is not None:
        explanation = explain_finding(graph, findings, detector)
        targets, focus = set(explanation.targets), f"detector {detector}"
        ancestry = {n.ordinal for n in explanation.nodes}

    entries: list[TimelineEntry] = []
    gaps: list[str] = []
    for index, record in enumerate(records):
        status, detail = _evidence(
            index, record, verification=verification, custody=custody, covered=covered, gap_findings=gap_findings,
        )
        if status in {EvidenceStatus.GAP, EvidenceStatus.UNVERIFIED}:
            gaps.append(f"step {index}: {detail}")
        entries.append(TimelineEntry(
            ordinal=index,
            step_id=record.step_id,
            timestamp=record.timestamp,
            kind=record.kind.value,
            summary=_summarize(record, graph.node(index).summary),
            authority=authorities[index],
            evidence=status,
            evidence_detail=detail,
            findings=sorted({f.detector_id for f in by_step.get(record.step_id, [])}),
            target=index in targets,
            in_ancestry=index in ancestry,
        ))

    anchors = sum(1 for r in records if r.kind == StepKind.ANCHOR)
    unanchored = sum(1 for e in entries if e.evidence == EvidenceStatus.SIGNED and e.kind != StepKind.ANCHOR.value)
    if anchors == 0 and records:
        gaps.append("no external anchor: timing rests on the agent's own clock and signing key (run air anchor)")
    elif unanchored:
        gaps.append(f"{unanchored} record(s) after the last anchor are signed but not yet externally witnessed")

    return IncidentTimeline(
        air_version=__version__,
        readiness=READINESS,
        source_log=source_log,
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        focus=focus,
        verification=verification,
        custody=custody,
        anchors=anchors,
        unanchored_records=unanchored,
        entries=entries,
        gaps=gaps,
        findings=findings,
    )
