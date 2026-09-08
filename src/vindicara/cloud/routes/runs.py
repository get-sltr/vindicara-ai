"""Runs routes: the console's list and detail views.

- ``GET /v1/runs``                 one query against the run store, newest first
- ``GET /v1/runs/{run_id}``        verification, findings, timeline, health (no bodies)
- ``GET /v1/runs/{run_id}/records`` the records, paged, bodies included

Bodies are paged on their own so a long run never pushes one response past
the gateway's limit; the timeline carries one-line summaries only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from airsdk.types import AgDRRecord  # noqa: TC002 (pydantic resolves the field type at runtime)
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict

from vindicara.cloud.roles import Capability, Role, require
from vindicara.cloud.run_store import RunStore, RunSummary
from vindicara.cloud.runs import RunDetail, assess_run, order_chain

if TYPE_CHECKING:
    from vindicara.cloud.capsule_store import CapsuleStore

router = APIRouter(tags=["runs"])


class RunRow(RunSummary):
    console_url: str


class RunsPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    count: int
    runs: list[RunRow]


class RunRecordsPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    count: int
    offset: int
    records: list[AgDRRecord]


def _scoped(request: Request, summary: RunSummary) -> bool:
    """Members and viewers see only runs their own key ingested (as with capsules)."""
    if request.state.role in (Role.MEMBER, Role.VIEWER):
        return bool(summary.api_key_id == str(request.state.api_key_id))
    return True


def _run_or_404(request: Request, run_id: str) -> RunSummary:
    store: RunStore = request.app.state.run_store
    summary = store.get(request.state.workspace_id, run_id)
    if summary is None or not _scoped(request, summary):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"run {run_id!r} not found in this workspace")
    return summary


def _records(request: Request, summary: RunSummary) -> list[AgDRRecord]:
    capsules: CapsuleStore = request.app.state.capsule_store
    return order_chain([c.record for c in capsules.for_run(summary.workspace_id, summary.run_id)])


@router.get("/v1/runs", response_model=RunsPage, summary="List runs in the calling key's workspace, newest first.")
async def list_runs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> RunsPage:
    require(request, Capability.READ_CAPSULES)
    store: RunStore = request.app.state.run_store
    workspace_id: str = request.state.workspace_id
    console = str(request.app.state.console_url).rstrip("/")
    page, total = store.list(workspace_id, limit=limit, offset=offset)
    rows = [RunRow(**s.model_dump(), console_url=f"{console}/runs/{s.run_id}") for s in page if _scoped(request, s)]
    return RunsPage(workspace_id=workspace_id, count=total, runs=rows)


@router.get("/v1/runs/{run_id}", response_model=RunDetail, summary="Verification, findings, timeline, and health for one run.")
async def get_run(request: Request, run_id: str) -> RunDetail:
    require(request, Capability.READ_CAPSULES)
    summary = _run_or_404(request, run_id)
    records = _records(request, summary)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"run {run_id!r} has no records")
    detail = assess_run(summary, records, console_url=str(request.app.state.console_url))
    store: RunStore = request.app.state.run_store
    store.assess(detail.summary)
    return detail


@router.get("/v1/runs/{run_id}/records", response_model=RunRecordsPage, summary="The signed records of one run, in chain order, paged.")
async def get_run_records(
    request: Request,
    run_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> RunRecordsPage:
    require(request, Capability.READ_CAPSULES)
    summary = _run_or_404(request, run_id)
    records = _records(request, summary)
    return RunRecordsPage(run_id=run_id, count=len(records), offset=offset, records=records[offset : offset + limit])
