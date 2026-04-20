"""`air` CLI. Surfaces `trace`, `demo`, and `version` subcommands."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import typer

from airsdk import __version__ as airsdk_version
from airsdk._demo import write_sample_log
from airsdk.agdr import load_chain, verify_chain
from airsdk.detections import UNIMPLEMENTED_DETECTORS, run_detectors
from airsdk.exports import export_json, export_pdf, export_siem
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
    typer.secho("Detector coverage:", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("  ASI01 Agent Goal Hijack          implemented", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("  ASI02 Tool Misuse                implemented", fg=typer.colors.BRIGHT_BLACK)
    typer.secho("  ASI03 Prompt Injection           implemented", fg=typer.colors.BRIGHT_BLACK)
    for code, name in UNIMPLEMENTED_DETECTORS:
        typer.secho(f"  {code} {name:<31} not yet implemented", fg=typer.colors.BRIGHT_BLACK)


def _run_trace_pipeline(log: Path, output: Path, output_format: str) -> None:
    """Shared body for ``air trace`` and ``air demo``. Raises ``typer.Exit`` on failure."""
    typer.secho(f"[AIR v{airsdk_version}] Analyzing {log}...", fg=typer.colors.WHITE, bold=True)

    records = load_chain(log)
    conversations = _count_conversations(records)
    typer.secho(
        f"[AIR v{airsdk_version}] Loaded {len(records)} agent steps across {conversations} conversations.",
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

    findings = run_detectors(records)
    typer.echo()
    if findings:
        for finding in findings:
            typer.secho(
                f"  {finding.asi_id} {finding.title} detected at step {finding.step_index}",
                fg=_severity_color(finding.severity),
            )
            typer.secho(f"    {finding.description}", fg=typer.colors.BRIGHT_BLACK)
    else:
        typer.secho("  No ASI01 or ASI02 findings on this trace.", fg=typer.colors.GREEN)

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
) -> None:
    """Ingest an AgDR log, verify its signatures, and output a forensic timeline."""
    _run_trace_pipeline(log, output, output_format)


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
) -> None:
    """Generate a signed sample trace and run trace against it. Zero setup required."""
    typer.secho(
        "[demo] Generating a fresh signed AgDR chain (13 steps, includes baked-in ASI01 + ASI02 violations)...",
        fg=typer.colors.WHITE, bold=True,
    )
    signer = write_sample_log(sample_path)
    typer.secho(
        f"[demo] Wrote sample to {sample_path.resolve()} (signer pubkey: {signer.public_key_hex[:16]}...)",
        fg=typer.colors.BRIGHT_BLACK,
    )
    typer.echo()
    _run_trace_pipeline(sample_path, output, "json")


@app.command()
def version() -> None:
    """Print the AIR version."""
    typer.echo(f"air / airsdk {airsdk_version}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
