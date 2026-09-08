"""Markdown rendering for the incident timeline.

Kept apart from :mod:`airsdk.incident` so the assembler stays about
evidence and this file stays about presentation. The Markdown pack is
what gets attached to an incident ticket or handed to a reviewer; every
figure in it is recomputable from the chain named in the header.
"""
from __future__ import annotations

from airsdk.incident import EvidenceStatus, IncidentTimeline, TimelineEntry

SCOPE_NOTE = (
    "This timeline is assembled from the signed Intent Capsule chain named above and nothing else. "
    "\"anchored\" means an anchor record in the chain covers the step; the anchor itself is verified "
    "with `air verify-public`. \"agent-key\" means no delegation, approval, or declared scope is "
    "recorded for the step, so only the agent's own signing key vouches for it. A gap is a finding "
    "about the evidence, not proof of what happened in the interval."
)

VERIFY_STEPS = (
    "1. `pip install projectair` and run `air trace <chain>` to re-verify every signature and re-run the detectors.\n"
    "2. Run `air incident <chain>` with the same focus to reproduce this table.\n"
    "3. If anchors are present, run `air verify-public <chain>` to check them against public services."
)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _row(entry: TimelineEntry) -> str:
    marker = "**" if entry.target else ""
    flags = ", ".join(entry.findings) or ""
    return (
        f"| {marker}{entry.ordinal}{marker} | {entry.timestamp} | {entry.kind} | {_cell(entry.summary)} "
        f"| {_cell(entry.authority.label())} | {entry.evidence.value} | {_cell(flags)} |"
    )


def render_incident_markdown(timeline: IncidentTimeline, *, full: bool = False) -> str:
    """Render ``timeline`` as a Markdown incident pack."""
    entries = timeline.entries if full else timeline.focused()
    omitted = len(timeline.entries) - len(entries)
    counts = {status: sum(1 for e in timeline.entries if e.evidence == status) for status in EvidenceStatus}
    lines: list[str] = [
        f"# Incident timeline ({timeline.readiness})",
        "",
        f"- **Chain:** `{timeline.source_log}`",
        f"- **Generated:** {timeline.generated_at} by AIR v{timeline.air_version}",
        f"- **Focus:** {timeline.focus or 'whole chain'}",
        f"- **Chain verification:** {timeline.verification.status.value}"
        + (f" ({timeline.verification.reason})" if timeline.verification.reason else ""),
        f"- **Key custody:** {timeline.custody.status.value}, {timeline.custody.rotations} rotation(s)",
        f"- **Records:** {len(timeline.entries)} total; "
        + ", ".join(f"{counts[s]} {s.value}" for s in EvidenceStatus if counts[s]),
        f"- **Anchors:** {timeline.anchors}",
        "",
        "## Timeline",
        "",
        "| # | Time (UTC) | Step | What executed | Authority | Evidence | Findings |",
        "|---|---|---|---|---|---|---|",
    ]
    lines += [_row(e) for e in entries]
    if omitted:
        lines += ["", f"{omitted} record(s) outside the focus omitted; pass `--full` to include them."]
    lines += ["", "## Where the evidence is missing", ""]
    lines += [f"- {gap}" for gap in timeline.gaps] or ["- None: every record verifies and is covered by an anchor."]
    lines += ["", "## Authority", ""]
    lines += _authority_summary(timeline)
    lines += ["", "## Findings", ""]
    if timeline.findings:
        lines += ["| Detector | Severity | Step | Title |", "|---|---|---|---|"]
        lines += [f"| {f.detector_id} | {f.severity} | {f.step_index} | {_cell(f.title)} |" for f in timeline.findings]
    else:
        lines.append("No detector findings in this chain.")
    lines += ["", "## Scope", "", SCOPE_NOTE, "", "## Reproduce", "", VERIFY_STEPS, ""]
    return "\n".join(lines)


def _authority_summary(timeline: IncidentTimeline) -> list[str]:
    by_kind: dict[str, int] = {}
    subjects: dict[str, set[str]] = {}
    for entry in timeline.entries:
        kind = entry.authority.kind.value
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if entry.authority.subject:
            subjects.setdefault(kind, set()).add(entry.authority.subject)
    out = []
    for kind, count in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        who = ", ".join(sorted(subjects.get(kind, set())))
        out.append(f"- **{kind}:** {count} record(s)" + (f" ({who})" if who else ""))
    return out
