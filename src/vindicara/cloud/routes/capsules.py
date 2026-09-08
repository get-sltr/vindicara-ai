"""Capsule ingest + list routes for AIR Cloud.

Distinct from ``vindicara.api.routes.capsules`` (single-tenant engine
substrate); this is the multi-tenant hosted variant. Every route here
relies on ``AirCloudAuthMiddleware`` having already populated
``request.state.workspace_id``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from airsdk.agdr import verify_record
from airsdk.types import AgDRRecord
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, ValidationError

from vindicara.cloud.capsule_store import CapsuleStore, StoredCapsule
from vindicara.cloud.event_bus import CapsuleEvent, CapsuleEventBus
from vindicara.cloud.roles import Capability, Role, require
from vindicara.cloud.runs import resolve_run_ids, summarize_batch, valid_run_id

if TYPE_CHECKING:
    from vindicara.cloud.run_store import RunStore

router = APIRouter()

RUN_ID_HEADER = "X-AIR-Run-Id"
#: DynamoDB items cap at 400 KB; leave room for the row's own attributes.
MAX_RECORD_BYTES = 350_000


def _store_batch(request: Request, records: list[AgDRRecord]) -> list[str]:
    """Persist verified records with their run ids, update run summaries, publish events."""
    store: CapsuleStore = request.app.state.capsule_store
    runs: RunStore = request.app.state.run_store
    bus: CapsuleEventBus = request.app.state.capsule_event_bus
    workspace_id: str = request.state.workspace_id
    api_key_id: str = request.state.api_key_id
    run_ids = resolve_run_ids(records, header_run_id=valid_run_id(request.headers.get(RUN_ID_HEADER)))
    by_run: dict[str, list[AgDRRecord]] = {}
    for record, run_id in zip(records, run_ids, strict=True):
        store.append(StoredCapsule(workspace_id=workspace_id, record=record, api_key_id=api_key_id, run_id=run_id))
        bus.publish(CapsuleEvent(workspace_id=workspace_id, record=record))
        by_run.setdefault(run_id, []).append(record)
    for run_id, batch in by_run.items():
        runs.upsert(summarize_batch(workspace_id, run_id, batch, api_key_id=api_key_id))
    return run_ids


def _parse_record(raw: str | bytes, *, where: str) -> AgDRRecord:
    if len(raw) > MAX_RECORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"{where}: record is {len(raw)} bytes; AIR Cloud stores records up to {MAX_RECORD_BYTES} bytes. Use a CapturePolicy to reference large content.",
        )
    try:
        record = AgDRRecord.model_validate_json(raw)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{where}: {exc.errors()}") from exc
    ok, reason = verify_record(record)
    if not ok:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=f"{where}: {reason or 'record signature verification failed'}",
        )
    return record


class IngestResponse(BaseModel):
    step_id: str
    stored: bool
    workspace_id: str
    run_id: str


class BulkIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    stored: int
    run_ids: list[str]


class CapsulesPage(BaseModel):
    """One page of capsule records."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    count: int
    records: list[AgDRRecord]


@router.post(
    "/v1/capsules",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest one Signed Intent Capsule",
)
async def ingest(request: Request) -> IngestResponse:
    require(request, Capability.WRITE_CAPSULES)
    record = _parse_record(await request.body(), where="record")
    run_ids = _store_batch(request, [record])
    return IngestResponse(step_id=record.step_id, stored=True, workspace_id=request.state.workspace_id, run_id=run_ids[0])


@router.post(
    "/v1/capsules/bulk",
    response_model=BulkIngestResponse,
    summary="Ingest a batch of Signed Intent Capsules in one POST (NDJSON body)",
)
async def ingest_bulk(request: Request) -> BulkIngestResponse:
    """Ingest a chain in one request. Body: newline-delimited JSON of AgDR records.

    Every line is validated and signature-checked before anything is stored,
    so a bad line rejects the whole batch instead of leaving a partial run.
    """
    require(request, Capability.WRITE_CAPSULES)
    body = (await request.body()).decode("utf-8")
    if not body.strip():
        raise HTTPException(status_code=400, detail="empty body")
    records = [
        _parse_record(line, where=f"line {line_no}")
        for line_no, raw_line in enumerate(body.splitlines(), 1)
        if (line := raw_line.strip())
    ]
    run_ids = _store_batch(request, records)
    return BulkIngestResponse(workspace_id=request.state.workspace_id, stored=len(records), run_ids=sorted(set(run_ids)))


@router.get(
    "/v1/capsules",
    response_model=CapsulesPage,
    summary="List capsules in the calling key's workspace",
)
async def list_capsules(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> CapsulesPage:
    require(request, Capability.READ_CAPSULES)
    store: CapsuleStore = request.app.state.capsule_store
    workspace_id: str = request.state.workspace_id
    role: str = request.state.role
    if role in (Role.MEMBER, Role.VIEWER):
        items = store.for_key(workspace_id, request.state.api_key_id)
    else:
        items = store.for_workspace(workspace_id)
    page = items[offset : offset + limit]
    return CapsulesPage(
        workspace_id=workspace_id,
        count=len(items),
        records=[c.record for c in page],
    )


@router.get(
    "/v1/capsules/{step_id}",
    response_model=AgDRRecord,
    summary="Fetch one capsule by step_id (within the calling key's workspace)",
)
async def get_capsule(request: Request, step_id: str) -> AgDRRecord:
    require(request, Capability.READ_CAPSULES)
    store: CapsuleStore = request.app.state.capsule_store
    workspace_id: str = request.state.workspace_id
    for capsule in store.for_workspace(workspace_id):
        if capsule.record.step_id == step_id:
            return capsule.record
    raise HTTPException(status_code=404, detail=f"step_id {step_id!r} not found in this workspace")
