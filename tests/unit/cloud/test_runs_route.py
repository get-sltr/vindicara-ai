"""Runs routes: ingest lands a run, the list is one row, detail and records page correctly."""

from __future__ import annotations

import os
from typing import Any

import pytest
from airsdk.agdr import Signer
from airsdk.types import AgDRPayload, StepKind
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("VINDICARA_SESSION_SECRET", "test_secret_for_unit_tests_only_0000")

from vindicara.cloud.factory import create_air_cloud_app
from vindicara.cloud.workspace import ApiKey, InMemoryApiKeyStore, InMemoryWorkspaceStore, Workspace

OWNER_KEY = "air_" + "a" * 32
MEMBER_KEY = "air_" + "b" * 32


def _app() -> Any:
    ws_store, key_store = InMemoryWorkspaceStore(), InMemoryApiKeyStore()
    ws_store.create(Workspace(workspace_id="ws_r", name="R", owner_email="o@x.io"))
    key_store.issue(ApiKey(key_id="k_owner", workspace_id="ws_r", key=OWNER_KEY, role="owner"))
    key_store.issue(ApiKey(key_id="k_member", workspace_id="ws_r", key=MEMBER_KEY, role="member"))
    return create_air_cloud_app(workspace_store=ws_store, api_key_store=key_store, console_url="http://c/flightdeck")


def _chain(n: int = 4) -> list:  # type: ignore[type-arg]
    signer = Signer.generate()
    out = [signer.sign(StepKind.LLM_START, AgDRPayload(prompt="What is the status of INV-2291?", user_intent="check invoice"))]
    out.append(signer.sign(StepKind.LLM_END, AgDRPayload(response="Looking it up.")))
    out.append(signer.sign(StepKind.TOOL_START, AgDRPayload(tool_name="lookup_invoice", tool_args={"id": "INV-2291"})))
    out.append(signer.sign(StepKind.TOOL_END, AgDRPayload(tool_output="unpaid, $4,820")))
    return out[:n]


def _ndjson(records: list) -> str:  # type: ignore[type-arg]
    return "\n".join(r.model_dump_json(exclude_none=True) for r in records)


@pytest.mark.anyio
async def test_bulk_ingest_lands_one_run_with_detail_and_records() -> None:
    app = _app()
    records = _chain()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ingest = await client.post("/v1/capsules/bulk", content=_ndjson(records), headers={"X-API-Key": OWNER_KEY, "X-AIR-Run-Id": records[0].step_id})
        assert ingest.status_code == 200, ingest.text
        assert ingest.json()["run_ids"] == [records[0].step_id]

        listed = await client.get("/v1/runs", headers={"X-API-Key": OWNER_KEY})
        assert listed.status_code == 200
        body = listed.json()
        assert body["count"] == 1
        row = body["runs"][0]
        assert row["run_id"] == records[0].step_id
        assert row["records"] == 4
        assert row["user_intent"] == "check invoice"
        assert row["kinds"] == {"llm_start": 1, "llm_end": 1, "tool_start": 1, "tool_end": 1}
        assert row["verification"] is None
        assert row["console_url"] == f"http://c/flightdeck/runs/{records[0].step_id}"

        detail = await client.get(f"/v1/runs/{records[0].step_id}", headers={"X-API-Key": OWNER_KEY})
        assert detail.status_code == 200, detail.text
        d = detail.json()
        assert d["verification"]["status"] == "ok"
        assert len(d["timeline"]["entries"]) == 4
        assert d["timeline"]["entries"][2]["summary"].startswith("lookup_invoice(")
        assert d["health"]["level"] in {"ok", "warn", "fail"}
        assert "records" not in d

        relisted = await client.get("/v1/runs", headers={"X-API-Key": OWNER_KEY})
        assert relisted.json()["runs"][0]["verification"] == "ok"

        page = await client.get(f"/v1/runs/{records[0].step_id}/records?limit=2&offset=1", headers={"X-API-Key": OWNER_KEY})
        assert page.status_code == 200
        p = page.json()
        assert p["count"] == 4
        assert [r["step_id"] for r in p["records"]] == [records[1].step_id, records[2].step_id]


@pytest.mark.anyio
async def test_single_posts_without_header_join_by_lineage_and_return_run_id() -> None:
    app = _app()
    records = _chain(3)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/v1/capsules", content=records[0].model_dump_json(exclude_none=True), headers={"X-API-Key": OWNER_KEY})
        assert first.status_code == 201
        assert first.json()["run_id"] == records[0].step_id
        second = await client.post("/v1/capsules", content=records[1].model_dump_json(exclude_none=True), headers={"X-API-Key": OWNER_KEY, "X-AIR-Run-Id": records[0].step_id})
        assert second.json()["run_id"] == records[0].step_id
        listed = await client.get("/v1/runs", headers={"X-API-Key": OWNER_KEY})
        assert listed.json()["count"] == 1
        assert listed.json()["runs"][0]["records"] == 2


@pytest.mark.anyio
async def test_member_sees_only_runs_its_own_key_ingested() -> None:
    app = _app()
    owner_chain, member_chain = _chain(2), _chain(2)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/v1/capsules/bulk", content=_ndjson(owner_chain), headers={"X-API-Key": OWNER_KEY})
        await client.post("/v1/capsules/bulk", content=_ndjson(member_chain), headers={"X-API-Key": MEMBER_KEY})
        mine = await client.get("/v1/runs", headers={"X-API-Key": MEMBER_KEY})
        assert [r["run_id"] for r in mine.json()["runs"]] == [member_chain[0].step_id]
        blocked = await client.get(f"/v1/runs/{owner_chain[0].step_id}", headers={"X-API-Key": MEMBER_KEY})
        assert blocked.status_code == 404
        everything = await client.get("/v1/runs", headers={"X-API-Key": OWNER_KEY})
        assert everything.json()["count"] == 2


@pytest.mark.anyio
async def test_oversized_record_is_413_and_bad_batch_stores_nothing() -> None:
    app = _app()
    records = _chain(2)
    huge = records[0].model_copy(update={"payload": AgDRPayload(prompt="x" * 400_000)})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/v1/capsules", content=huge.model_dump_json(exclude_none=True), headers={"X-API-Key": OWNER_KEY})
        assert resp.status_code == 413
        assert "CapturePolicy" in resp.json()["detail"]
        tampered = records[1].model_copy(update={"payload": AgDRPayload(response="changed")})
        bad = await client.post("/v1/capsules/bulk", content=_ndjson([records[0], tampered]), headers={"X-API-Key": OWNER_KEY})
        assert bad.status_code == 422
        assert "line 2" in bad.json()["detail"]
        listed = await client.get("/v1/runs", headers={"X-API-Key": OWNER_KEY})
        assert listed.json()["count"] == 0


@pytest.mark.anyio
async def test_unknown_run_is_404() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/runs/nope", headers={"X-API-Key": OWNER_KEY})
    assert resp.status_code == 404
