"""``air incident``: what executed, under whose authority, where evidence is missing.

The terminal timeline is free, like ``air trace`` and ``air explain``.
Writing the Markdown incident pack (``--output``) requires a license, the
same split as ``air report security-review``: seeing is free, the
artifact you attach to a ticket is paid.
"""
from __future__ import annotations

from pathlib import Path

import typer

from airsdk import __version__ as airsdk_version
from airsdk.agdr import load_chain
from airsdk.detections import run_detectors
from airsdk.incident import READINESS, EvidenceStatus, IncidentTimeline, TimelineEntry, assemble_incident
from airsdk.types import AgDRRecord, VerificationStatus

_EVIDENCE_COLOR = {
    EvidenceStatus.ANCHORED: typer.colors.GREEN,
    EvidenceStatus.SIGNED: typer.colors.WHITE,
    EvidenceStatus.GAP: typer.colors.YELLOW,
    EvidenceStatus.UNVERIFIED: typer.colors.RED,
}


def register(app: typer.Typer) -> None:
    """Attach the incident command to ``app``."""
    app.command(name="incident")(incident_cmd)


def incident_cmd(
    chain: Path = typer.Argument(..., exists=True, dir_okay=False, help="Chain JSONL file."),
    step: str | None = typer.Option(None, "--step", help="Focus on a step: UUID or 0-based ordinal."),
    finding: str | None = typer.Option(None, "--finding", help="Focus on a detector id (e.g. ASI02, AIR-04)."),
    full: bool = typer.Option(False, "--full", help="Show every record, not only the focused rows."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write the Markdown incident pack here (licensed)."),
    as_json: bool = typer.Option(False, "--json", help="Print the timeline as JSON instead of a table."),
    agent_registry: Path | None = typer.Option(
        None, "--agent-registry", exists=True, readable=True,
        help="Optional agent registry to enable the ASI03 / ASI10 Zero-Trust detectors.",
    ),
) -> None:
    """Assemble an incident timeline from a signed chain (beta).

    One row per record: what executed, under whose authority (delegation,
    approval, declared scope, or only the agent key), and whether the
    evidence is anchored, signed, at a gap, or past a verification failure.
    Focus with --step or --finding to see the causal ancestry plus every
    authority event and gap; --full shows the whole chain.
    """
    from projectair.cli import _load_registry_or_exit, _require_license_or_exit

    if step is not None and finding is not None:
        typer.secho("Pass at most one of --step or --finding", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    records = load_chain(chain)
    registry = _load_registry_or_exit(agent_registry)
    findings = run_detectors(records, registry=registry)
    ordinal = _resolve_step(step, records) if step is not None else None
    timeline = assemble_incident(
        records, findings, source_log=str(chain.resolve()), step=ordinal, detector=finding,
    )
    if as_json:
        typer.echo(timeline.model_dump_json(indent=2))
    else:
        _render(timeline, chain, full=full)
    if output is None:
        return
    _require_license_or_exit("air incident --output (Markdown incident pack)")
    from airsdk._incident_render import render_incident_markdown

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_incident_markdown(timeline, full=full), encoding="utf-8")
    typer.secho(f"[air incident] Wrote incident pack to {output.resolve()}", fg=typer.colors.CYAN)


def _resolve_step(step_arg: str, records: list[AgDRRecord]) -> int:
    if step_arg.isdigit():
        ordinal = int(step_arg)
        if ordinal >= len(records):
            typer.secho(f"  Ordinal {ordinal} out of range (chain has {len(records)} records).", fg=typer.colors.RED)
            raise typer.Exit(code=2)
        return ordinal
    for index, record in enumerate(records):
        if record.step_id == step_arg:
            return index
    typer.secho(f"  Step id {step_arg!r} not found in chain.", fg=typer.colors.RED)
    raise typer.Exit(code=2)


def _clock(timestamp: str) -> str:
    return timestamp[11:19] if len(timestamp) >= 19 else timestamp


def _fit(text: str, width: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 3] + "..."


def _render(timeline: IncidentTimeline, chain: Path, *, full: bool) -> None:
    typer.secho(f"[AIR v{airsdk_version}] Incident timeline ({READINESS}): {chain}", fg=typer.colors.WHITE, bold=True)
    verification = timeline.verification.status.value
    v_color = typer.colors.GREEN if timeline.verification.status == VerificationStatus.OK else typer.colors.RED
    typer.secho(f"  focus: {timeline.focus or 'whole chain'}   ", fg=typer.colors.WHITE, nl=False)
    typer.secho(f"verification: {verification}   ", fg=v_color, nl=False)
    typer.secho(f"custody: {timeline.custody.status.value}   anchors: {timeline.anchors}", fg=typer.colors.WHITE)
    typer.echo("")
    typer.secho(
        f"    {'#':>3}  {'time':8}  {'step':14}  {'what executed':40}  {'authority':30}  evidence",
        fg=typer.colors.WHITE, bold=True,
    )
    entries = timeline.entries if full else timeline.focused()
    for entry in entries:
        _render_entry(entry)
    omitted = len(timeline.entries) - len(entries)
    if omitted:
        typer.secho(f"\n    {omitted} record(s) outside the focus not shown; pass --full to include them.", fg=typer.colors.WHITE)
    typer.echo("")
    typer.secho("  Where the evidence is missing", fg=typer.colors.WHITE, bold=True)
    for gap in timeline.gaps or ["none: every record verifies and is covered by an anchor"]:
        typer.secho(f"    - {gap}", fg=typer.colors.YELLOW if timeline.gaps else typer.colors.GREEN)
    typer.echo("")
    typer.secho(
        "  Legend:  * target   + causal ancestry   HALTED = policy stopped the action   "
        "agent-key = only the agent signing key vouches",
        fg=typer.colors.WHITE,
    )


def _render_entry(entry: TimelineEntry) -> None:
    marker = "*" if entry.target else "+" if entry.in_ancestry else " "
    color = typer.colors.YELLOW if entry.target else typer.colors.WHITE
    typer.secho(
        f"  {marker} {entry.ordinal:>3}  {_clock(entry.timestamp):8}  {entry.kind:14}  "
        f"{_fit(entry.summary, 40):40}  {_fit(entry.authority.label(), 30):30}  ",
        fg=color, nl=False,
    )
    typer.secho(entry.evidence.value, fg=_EVIDENCE_COLOR[entry.evidence], bold=entry.evidence != EvidenceStatus.SIGNED)
    if entry.findings:
        typer.secho(f"           findings: {', '.join(entry.findings)}", fg=typer.colors.WHITE)
    if entry.evidence in {EvidenceStatus.GAP, EvidenceStatus.UNVERIFIED}:
        typer.secho(f"           {_fit(entry.evidence_detail, 110)}", fg=_EVIDENCE_COLOR[entry.evidence])
