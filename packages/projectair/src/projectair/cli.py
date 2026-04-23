"""`air` CLI. Surfaces `trace`, `demo`, and `version` subcommands."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import typer

from airsdk import __version__ as airsdk_version
from airsdk._demo import write_sample_log, write_sample_registry
from airsdk.agdr import load_chain, verify_chain
from airsdk.article72 import generate_article72_report
from airsdk.detections import (
    IMPLEMENTED_AIR_DETECTORS,
    IMPLEMENTED_ASI_DETECTORS,
    UNIMPLEMENTED_DETECTORS,
    run_detectors,
)
from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.registry import AgentRegistry, load_registry
from airsdk.types import (
    AgDRRecord,
    ForensicReport,
    StepKind,
    VerificationStatus,
)

app = typer.Typer(
    name="air",
    help="Project AIR: forensic reconstruction and incident response for AI agents.",
    no_args_is_help=True,
    add_completion=False,
)

report_app = typer.Typer(
    name="report",
    help="Generate compliance reports from a Project AIR signed forensic chain.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(report_app, name="report")


def _count_conversations(records: list[AgDRRecord]) -> int:
    finishes = sum(1 for r in records if r.kind == StepKind.AGENT_FINISH)
    return max(finishes, 1)


def _severity_color(severity: str) -> str:
    return {
        "critical": typer.colors.RED,
        "high": typer.colors.YELLOW,
        "medium": typer.colors.CYAN,
    }.get(severity, typer.colors.WHITE)


def _print_detector_coverage() -> None:
    implemented = len(IMPLEMENTED_ASI_DETECTORS)
    roadmap = len(UNIMPLEMENTED_DETECTORS)
    typer.secho(
        f"OWASP Top 10 for Agentic Applications coverage ({implemented} implemented, {roadmap} on roadmap):",
        fg=typer.colors.BRIGHT_BLACK,
    )
    for code, name, status in IMPLEMENTED_ASI_DETECTORS:
        typer.secho(f"  {code} {name:<42} {status}", fg=typer.colors.BRIGHT_BLACK)
    for code, name in UNIMPLEMENTED_DETECTORS:
        typer.secho(f"  {code} {name:<42} not yet implemented", fg=typer.colors.BRIGHT_BLACK)
    typer.echo()
    typer.secho("Additional detectors (OWASP LLM Top 10 + AIR-native):", fg=typer.colors.BRIGHT_BLACK)
    for code, name, mapping in IMPLEMENTED_AIR_DETECTORS:
        typer.secho(f"  {code} {name:<32} {mapping}", fg=typer.colors.BRIGHT_BLACK)


def _run_trace_pipeline(
    log: Path,
    output: Path,
    output_format: str,
    registry: AgentRegistry | None = None,
) -> None:
    """Shared body for ``air trace`` and ``air demo``. Raises ``typer.Exit`` on failure."""
    typer.secho(f"[AIR v{airsdk_version}] Analyzing {log}...", fg=typer.colors.WHITE, bold=True)

    records = load_chain(log)
    conversations = _count_conversations(records)
    typer.secho(
        f"[AIR v{airsdk_version}] Loaded {len(records)} agent steps across {conversations} conversations.",
        fg=typer.colors.BRIGHT_BLACK,
    )
    if registry is not None:
        typer.secho(
            f"[Registry] {len(registry.agents)} agents declared; "
            f"Zero-Trust enforcement enabled for ASI03.",
            fg=typer.colors.BRIGHT_BLACK,
        )

    verification = verify_chain(records)
    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[VERIFICATION FAILED] {verification.status.value}: {verification.reason}",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        typer.secho(
            f"  Failed at step_id: {verification.failed_step_id}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    typer.secho(
        f"[Chain verified] {verification.records_verified} signatures valid.",
        fg=typer.colors.GREEN,
    )

    findings = run_detectors(records, registry=registry)
    typer.echo()
    if findings:
        for finding in findings:
            typer.secho(
                f"  {finding.detector_id} {finding.title} detected at step {finding.step_index}",
                fg=_severity_color(finding.severity),
            )
            typer.secho(f"    {finding.description}", fg=typer.colors.BRIGHT_BLACK)
    else:
        typer.secho("  No detector findings on this trace.", fg=typer.colors.GREEN)

    typer.echo()
    _print_detector_coverage()

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=conversations,
        verification=verification,
        findings=findings,
    )

    fmt = output_format.lower()
    try:
        if fmt == "json":
            written = export_json(report, output)
        elif fmt == "pdf":
            written = export_pdf(report, output)
        elif fmt == "siem":
            written = export_siem(report, output)
        else:
            typer.secho(
                f"Unknown --format '{output_format}'. Accepts: json, pdf, siem.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)
    except NotImplementedError as exc:
        typer.secho(f"[Export] {exc}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=3) from exc

    typer.echo()
    typer.secho(f"[Export] {written.resolve()}", fg=typer.colors.CYAN)


def _load_registry_or_exit(path: Path | None) -> AgentRegistry | None:
    """Helper: load a registry from disk, or emit a clean CLI error on failure."""
    if path is None:
        return None
    try:
        return load_registry(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"[Registry] Failed to load {path}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


@app.command()
def trace(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    output: Path = typer.Option(
        Path("forensic-report.json"),
        "--output", "-o",
        help="Where to write the forensic report.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Output format. json today; pdf and siem are reserved.",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help=(
            "Path to a YAML or JSON agent registry. Enables ASI03 Identity & "
            "Privilege Abuse and ASI10 Rogue Agents Zero-Trust enforcement. "
            "Without a registry, those detectors emit no findings."
        ),
        exists=True,
        readable=True,
    ),
) -> None:
    """Ingest an AgDR log, verify its signatures, and output a forensic timeline."""
    registry = _load_registry_or_exit(agent_registry)
    _run_trace_pipeline(log, output, output_format, registry=registry)


@app.command()
def demo(
    sample_path: Path = typer.Option(
        Path("air-demo.log"),
        "--sample-path", "-s",
        help="Where to write the generated sample AgDR log.",
    ),
    output: Path = typer.Option(
        Path("forensic-report.json"),
        "--output", "-o",
        help="Where to write the forensic report.",
    ),
    registry_path: Path = typer.Option(
        Path("air-demo-registry.yaml"),
        "--registry-path",
        help="Where to write the generated sample agent registry.",
    ),
) -> None:
    """Generate a signed sample trace and run trace against it. Zero setup required."""
    typer.secho(
        "[demo] Generating a fresh signed Intent Capsule chain "
        "(baked-in ASI01/02/03/04/05/06/07/08/09/10 + AIR-01/02/03/04 violations)...",
        fg=typer.colors.WHITE, bold=True,
    )
    signer = write_sample_log(sample_path)
    typer.secho(
        f"[demo] Wrote sample to {sample_path.resolve()} (signer pubkey: {signer.public_key_hex[:16]}...)",
        fg=typer.colors.BRIGHT_BLACK,
    )
    write_sample_registry(registry_path, signer.public_key_hex)
    typer.secho(
        f"[demo] Wrote sample registry to {registry_path.resolve()} "
        f"(ASI03 Zero-Trust enforcement active).",
        fg=typer.colors.BRIGHT_BLACK,
    )
    registry = load_registry(registry_path)
    typer.echo()
    _run_trace_pipeline(sample_path, output, "json", registry=registry)


@report_app.command("article72")
def report_article72(
    log: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSON-lines AgDR log."),
    system_id: str = typer.Option(
        ...,
        "--system-id",
        help="Unique identifier for the high-risk AI system under Article 11 Annex IV.",
    ),
    output: Path = typer.Option(
        Path("article72-report.md"),
        "--output", "-o",
        help="Where to write the generated Article 72 report (Markdown).",
    ),
    system_name: str = typer.Option(
        "[high-risk AI system name]",
        "--system-name",
        help="Human-readable name of the high-risk AI system.",
    ),
    operator: str = typer.Option(
        "[Provider / Operator entity]",
        "--operator",
        help="Legal entity operating the system (will appear in the attestation).",
    ),
    period: str = typer.Option(
        "[reporting period, e.g. 2026-Q3]",
        "--period",
        help="Reporting period label (free text).",
    ),
    agent_registry: Path | None = typer.Option(
        None,
        "--agent-registry",
        help="Optional agent registry to enable ASI03/ASI10 Zero-Trust enforcement during report generation.",
        exists=True,
        readable=True,
    ),
) -> None:
    """Generate an EU AI Act Article 72 post-market monitoring report from an AgDR log.

    The output is a populated Markdown template, not a filed compliance
    artefact. The provider must review, adapt, and have a qualified person
    sign the attestation before the report is legally usable.
    """
    registry = _load_registry_or_exit(agent_registry)

    typer.secho(
        f"[Article 72] Loading {log}...",
        fg=typer.colors.WHITE, bold=True,
    )
    records = load_chain(log)
    conversations = _count_conversations(records)
    verification = verify_chain(records)
    findings = run_detectors(records, registry=registry)

    report = ForensicReport(
        air_version=airsdk_version,
        report_id=str(uuid4()),
        source_log=str(log.resolve()),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=len(records),
        conversations=conversations,
        verification=verification,
        findings=findings,
    )
    markdown = generate_article72_report(
        report,
        records,
        system_id,
        system_name=system_name,
        operator_entity=operator,
        monitoring_period=period,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    if verification.status != VerificationStatus.OK:
        typer.secho(
            f"[WARNING] Chain verification did NOT pass: {verification.reason}. "
            "Review before relying on this report as evidence.",
            fg=typer.colors.YELLOW, err=True,
        )
    else:
        typer.secho(
            f"[Chain verified] {verification.records_verified} signatures valid.",
            fg=typer.colors.GREEN,
        )

    typer.secho(
        f"[Article 72] Wrote report to {output.resolve()} "
        f"({len(findings)} findings across {report.records} records).",
        fg=typer.colors.CYAN,
    )
    typer.secho(
        "[Reminder] This is an informational template. Have a qualified person "
        "sign the attestation and consult counsel before filing.",
        fg=typer.colors.BRIGHT_BLACK,
    )


@app.command()
def version() -> None:
    """Print the AIR version."""
    typer.echo(f"air / airsdk {airsdk_version}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
