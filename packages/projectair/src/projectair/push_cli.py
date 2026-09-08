"""``air push``: upload a signed chain file to AIR Cloud and print its run link."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from airsdk.cloud_config import run_url
from airsdk.types import GENESIS_PREV_HASH, AgDRRecord
from projectair.cloud_target import resolve_cloud_target

if TYPE_CHECKING:
    import httpx

RUN_ID_HEADER = "X-AIR-Run-Id"
CHUNK = 200


def _load_records(chain: Path) -> list[AgDRRecord]:
    records: list[AgDRRecord] = []
    for i, line in enumerate(chain.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            records.append(AgDRRecord.model_validate_json(stripped))
        except ValueError as exc:
            typer.secho(f"Invalid record at line {i}: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2) from exc
    if not records:
        typer.secho("Chain file is empty.", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=2)
    return records


def split_runs(records: list[AgDRRecord]) -> list[list[AgDRRecord]]:
    """Split a file into runs: every genesis record starts a new one."""
    runs: list[list[AgDRRecord]] = []
    for record in records:
        if record.prev_hash == GENESIS_PREV_HASH or not runs:
            runs.append([record])
        else:
            runs[-1].append(record)
    return runs


def _push(
    chain: Path = typer.Argument(..., exists=True, readable=True, help="Path to a JSONL chain file."),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="Workspace API key (else AIRSDK_CLOUD_API_KEY, else the key saved by air login)."),
    cloud_url: str | None = typer.Option(None, "--cloud-url", help="AIR Cloud endpoint (else AIRSDK_CLOUD_URL, else the URL saved by air login)."),
) -> None:
    """Push a signed forensic chain to AIR Cloud and print the run link."""
    import httpx

    target = resolve_cloud_target(api_key, cloud_url)
    if not target.api_key:
        typer.secho(
            "No workspace API key. Run `air login` (saves one), pass --api-key, or set AIRSDK_CLOUD_API_KEY.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=2)
    records = _load_records(chain)
    runs = split_runs(records)
    typer.secho(f"[AIR Cloud] Pushing {len(records)} record(s) in {len(runs)} run(s) to {target.url}", fg=typer.colors.WHITE, bold=True)

    pushed = 0
    with httpx.Client(base_url=target.url, headers={"X-API-Key": target.api_key}, timeout=30.0) as client:
        for run in runs:
            run_id = run[0].step_id
            for start in range(0, len(run), CHUNK):
                batch = run[start : start + CHUNK]
                pushed += _send_batch(client, batch, run_id, already=pushed)
            typer.secho(f"  run {run_id}: {len(run)} record(s)  {run_url(target.console_url, run_id)}", fg=typer.colors.WHITE)
    typer.secho(f"[AIR Cloud] Pushed {pushed}/{len(records)} records.", fg=typer.colors.GREEN, bold=True)


def _send_batch(client: httpx.Client, batch: list[AgDRRecord], run_id: str, *, already: int) -> int:
    """Send one batch as NDJSON; fall back to single posts on an older server. Returns records accepted."""
    body = "\n".join(r.model_dump_json(exclude_none=True) for r in batch)
    headers = {RUN_ID_HEADER: run_id, "Content-Type": "application/x-ndjson"}
    resp = client.post("/v1/capsules/bulk", content=body, headers=headers)
    if resp.status_code == 404:
        for offset, record in enumerate(batch):
            single = client.post("/v1/capsules", content=record.model_dump_json(exclude_none=True), headers={RUN_ID_HEADER: run_id, "Content-Type": "application/json"})
            _fail_unless_ok(single, already + offset + 1)
        return len(batch)
    _fail_unless_ok(resp, already + 1)
    return len(batch)


def _fail_unless_ok(resp: httpx.Response, position: int) -> None:
    if resp.status_code in (200, 201):
        return
    typer.secho(f"Failed at record {position}: HTTP {resp.status_code}: {resp.text[:200]}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def register(app: typer.Typer) -> None:
    app.command("push")(_push)
