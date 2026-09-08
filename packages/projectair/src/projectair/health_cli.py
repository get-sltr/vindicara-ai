"""``air health``: is the evidence complete, and is verification working?

Free, offline, read-only. Takes one chain file or a directory of them and
exits non-zero when any chain fails a check (or warns, with ``--strict``),
so it can run from cron or CI next to the agent it watches.
"""
from __future__ import annotations

from pathlib import Path

import typer

from airsdk import __version__ as airsdk_version
from airsdk.agdr import load_chain
from airsdk.health import READINESS, EvidenceHealth, HealthCheck, HealthLevel, assess_health
from airsdk.registry import AgentRegistry

CHAIN_SUFFIXES = frozenset({".jsonl", ".log"})

_LEVEL_COLOR = {
    HealthLevel.OK: typer.colors.GREEN,
    HealthLevel.WARN: typer.colors.YELLOW,
    HealthLevel.FAIL: typer.colors.RED,
}


def register(app: typer.Typer) -> None:
    """Attach the health command to ``app``."""
    app.command(name="health")(health_cmd)


def health_cmd(
    path: Path = typer.Argument(..., exists=True, help="Chain JSONL file, or a directory of chains (*.jsonl, *.log)."),
    as_json: bool = typer.Option(False, "--json", help="Print the assessment(s) as JSON."),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero on warnings as well as failures."),
    agent_registry: Path | None = typer.Option(
        None, "--agent-registry", exists=True, readable=True,
        help="Optional agent registry to enable the ASI03 / ASI10 Zero-Trust detectors.",
    ),
) -> None:
    """Check whether a chain's evidence is complete and verification is working (beta).

    Eight checks per chain: integrity, key custody, verification support,
    completeness (every call has its outcome), external anchoring, authority
    binding, detectors, and freshness. The level is the worst check. Exit 0
    when healthy, 1 when any chain fails (or warns, with --strict).
    """
    from projectair.cli import _load_registry_or_exit

    registry = _load_registry_or_exit(agent_registry)
    chains = _discover(path)
    if not chains:
        typer.secho(f"No chain files (*.jsonl, *.log) under {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    results = [_assess(chain, registry) for chain in chains]
    if as_json:
        typer.echo(_json(results, single=path.is_file()))
    elif len(results) == 1:
        _render_one(results[0])
    else:
        _render_many(results)
    worst = max((r.level for r in results), key=lambda lv: [HealthLevel.OK, HealthLevel.WARN, HealthLevel.FAIL].index(lv))
    if worst == HealthLevel.FAIL or (strict and worst == HealthLevel.WARN):
        raise typer.Exit(code=1)


def _json(results: list[EvidenceHealth], *, single: bool) -> str:
    if single:
        return results[0].model_dump_json(indent=2)
    return "[\n" + ",\n".join(r.model_dump_json(indent=2) for r in results) + "\n]"


def _discover(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in CHAIN_SUFFIXES)


def _assess(chain: Path, registry: AgentRegistry | None) -> EvidenceHealth:
    try:
        records = load_chain(chain)
    except ValueError as exc:
        reason = str(exc).splitlines()[0]
        broken = HealthCheck(key="integrity", title="Chain integrity", level=HealthLevel.FAIL, detail=f"cannot load: {reason}", metrics={})
        return EvidenceHealth(
            air_version=airsdk_version, readiness=READINESS, source_log=str(chain.resolve()), generated_at="",
            records=0, level=HealthLevel.FAIL, checks=[broken], findings_by_severity={},
        )
    return assess_health(records, source_log=str(chain.resolve()), registry=registry)


def _render_one(health: EvidenceHealth) -> None:
    typer.secho(f"[AIR v{airsdk_version}] Evidence health ({READINESS}): {health.source_log}", fg=typer.colors.WHITE, bold=True)
    typer.secho(f"  {health.level.value.upper()}", fg=_LEVEL_COLOR[health.level], bold=True, nl=False)
    typer.secho(f"  {health.records} record(s)", fg=typer.colors.WHITE)
    typer.echo("")
    for check in health.checks:
        _render_check(check)
    typer.echo("")
    _render_next_steps(health)


def _render_check(check: HealthCheck) -> None:
    typer.secho(f"  {check.level.value.upper():5}", fg=_LEVEL_COLOR[check.level], bold=True, nl=False)
    typer.secho(f"  {check.title:22}", fg=typer.colors.WHITE, bold=True, nl=False)
    typer.secho(check.detail, fg=typer.colors.WHITE)


def _render_next_steps(health: EvidenceHealth) -> None:
    hints = {
        "integrity": "air incident <chain>   (see which records are unverified)",
        "custody": "air incident <chain>   (see where the signing key changed)",
        "verifiable": "pip install 'projectair[pqc]'",
        "completeness": "air incident <chain> --finding AIR-04",
        "anchoring": "air anchor <chain>",
        "authority": "open the session with AIRRecorder.open_delegation(grant)",
    }
    lines = [f"    {hints[c.key]}" for c in health.checks if c.level != HealthLevel.OK and c.key in hints]
    if lines:
        typer.secho("  Next", fg=typer.colors.WHITE, bold=True)
        for line in lines:
            typer.secho(line, fg=typer.colors.WHITE)


def _render_many(results: list[EvidenceHealth]) -> None:
    typer.secho(f"[AIR v{airsdk_version}] Evidence health ({READINESS}): {len(results)} chain(s)", fg=typer.colors.WHITE, bold=True)
    typer.echo("")
    for health in results:
        typer.secho(f"  {health.level.value.upper():5}", fg=_LEVEL_COLOR[health.level], bold=True, nl=False)
        typer.secho(f"  {health.records:>6}  {health.source_log}", fg=typer.colors.WHITE)
        for check in health.checks:
            if check.level != HealthLevel.OK:
                typer.secho(f"           {check.level.value:5} {check.title}: {check.detail}", fg=_LEVEL_COLOR[check.level])
    counts = {lv: sum(1 for r in results if r.level == lv) for lv in HealthLevel}
    typer.echo("")
    typer.secho(
        f"  {counts[HealthLevel.OK]} ok, {counts[HealthLevel.WARN]} warn, {counts[HealthLevel.FAIL]} fail",
        fg=typer.colors.WHITE, bold=True,
    )
