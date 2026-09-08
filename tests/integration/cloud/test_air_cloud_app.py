"""Integration tests for the AIR Cloud hosted ingest FastAPI app.

Drive the app through the real ASGI stack (`httpx.AsyncClient` +
`ASGITransport`) so middleware, routing, and serialization all run
end-to-end.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx
import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
from airsdk.agdr import Signer
from airsdk.types import AgDRPayload, AgDRRecord, StepKind

from vindicara.cloud.capsule_store import InMemoryCapsuleStore
from vindicara.cloud.factory import create_air_cloud_app
from vindicara.cloud.workspace import (
    ApiKey,
    InMemoryApiKeyStore,
    InMemoryWorkspaceStore,
    Workspace,
)


def _signed_record(signer: Signer, *, prompt: str = "hi") -> AgDRRecord:
    return signer.sign(
        kind=StepKind.LLM_START,
        payload=AgDRPayload.model_validate({"prompt": prompt}),
    )


@pytest_asyncio.fixture
async def cloud_client() -> AsyncIterator[tuple[httpx.AsyncClient, dict]]:
    """An ASGI client + a context dict with one workspace + key pre-seeded."""
    capsule_store = InMemoryCapsuleStore()
    workspace_store = InMemoryWorkspaceStore()
    api_key_store = InMemoryApiKeyStore()

    workspace = Workspace(workspace_id="acme", name="Acme Corp", owner_email="ops@acme.io")
    workspace_store.create(workspace)
    api_key = ApiKey(
        key_id="key_acme_owner",
        workspace_id="acme",
        key="air_test_acme",
        role="owner",
        name="bootstrap",
    )
    api_key_store.issue(api_key)

    app = create_air_cloud_app(
        capsule_store=capsule_store,
        workspace_store=workspace_store,
        api_key_store=api_key_store,
        admin_token="admin_test_secret",
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield (
            client,
            {
                "capsule_store": capsule_store,
                "workspace_store": workspace_store,
                "api_key_store": api_key_store,
                "api_key": api_key.key,
                "admin_token": "admin_test_secret",
            },
        )


@pytest.fixture
def signer() -> Signer:
    return Signer.generate()


@pytest.mark.asyncio
async def test_health_is_unauthenticated(cloud_client: tuple[httpx.AsyncClient, dict]) -> None:
    client, _ = cloud_client
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_v1_routes_require_api_key(cloud_client: tuple[httpx.AsyncClient, dict]) -> None:
    client, _ = cloud_client
    response = await client.get("/v1/workspaces/me")
    assert response.status_code == 401
    assert "X-API-Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_v1_routes_reject_unknown_key(cloud_client: tuple[httpx.AsyncClient, dict]) -> None:
    client, _ = cloud_client
    response = await client.get("/v1/workspaces/me", headers={"X-API-Key": "air_unknown"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_workspace_whoami(cloud_client: tuple[httpx.AsyncClient, dict]) -> None:
    client, ctx = cloud_client
    response = await client.get(
        "/v1/workspaces/me",
        headers={"X-API-Key": ctx["api_key"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["workspace_id"] == "acme"
    assert body["owner_email"] == "ops@acme.io"


@pytest.mark.asyncio
async def test_capsule_ingest_persists_record_under_workspace(
    cloud_client: tuple[httpx.AsyncClient, dict],
    signer: Signer,
) -> None:
    client, ctx = cloud_client
    record = _signed_record(signer)
    response = await client.post(
        "/v1/capsules",
        headers={"X-API-Key": ctx["api_key"]},
        content=record.model_dump_json(),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["stored"] is True
    assert body["workspace_id"] == "acme"
    assert ctx["capsule_store"].count("acme") == 1


@pytest.mark.asyncio
async def test_capsule_ingest_rejects_tampered_signature(
    cloud_client: tuple[httpx.AsyncClient, dict],
    signer: Signer,
) -> None:
    client, ctx = cloud_client
    record = _signed_record(signer)
    body = json.loads(record.model_dump_json())
    body["signature"] = "00" * 64  # invalid signature
    response = await client.post(
        "/v1/capsules",
        headers={"X-API-Key": ctx["api_key"]},
        content=json.dumps(body),
    )
    assert response.status_code == 422
    assert ctx["capsule_store"].count("acme") == 0


@pytest.mark.asyncio
async def test_bulk_ingest_accepts_chain_in_one_post(
    cloud_client: tuple[httpx.AsyncClient, dict],
    signer: Signer,
) -> None:
    client, ctx = cloud_client
    r1 = _signed_record(signer, prompt="s1")
    r2 = _signed_record(signer, prompt="s2")
    body = "\n".join(record.model_dump_json() for record in [r1, r2])
    response = await client.post(
        "/v1/capsules/bulk",
        headers={"X-API-Key": ctx["api_key"]},
        content=body,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_id"] == "acme"
    assert payload["stored"] == 2
    # Ingest also reports the run the batch landed in (cloud/runs.py). Asserting
    # the whole dict broke when run_ids was added; assert the contract instead.
    assert len(payload["run_ids"]) == 1
    assert ctx["capsule_store"].count("acme") == 2


@pytest.mark.asyncio
async def test_capsule_list_returns_workspace_capsules(
    cloud_client: tuple[httpx.AsyncClient, dict],
    signer: Signer,
) -> None:
    client, ctx = cloud_client
    r1 = _signed_record(signer, prompt="s1")
    r2 = _signed_record(signer, prompt="s2")
    expected_step_ids = {r1.step_id, r2.step_id}
    for record in [r1, r2]:
        await client.post(
            "/v1/capsules",
            headers={"X-API-Key": ctx["api_key"]},
            content=record.model_dump_json(),
        )
    response = await client.get("/v1/capsules", headers={"X-API-Key": ctx["api_key"]})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert {r["step_id"] for r in body["records"]} == expected_step_ids


@pytest.mark.asyncio
async def test_capsule_get_returns_404_for_other_workspace_step_id(
    cloud_client: tuple[httpx.AsyncClient, dict],
    signer: Signer,
) -> None:
    """Workspace isolation: a record stored under workspace beta is invisible to acme."""
    client, ctx = cloud_client

    beta_key = ApiKey(key_id="key_beta_owner", workspace_id="beta", key="air_test_beta", role="owner")
    ctx["workspace_store"].create(Workspace(workspace_id="beta", name="Beta", owner_email="b@b.io"))
    ctx["api_key_store"].issue(beta_key)

    r = _signed_record(signer, prompt="beta-only")
    await client.post(
        "/v1/capsules",
        headers={"X-API-Key": "air_test_beta"},
        content=r.model_dump_json(),
    )

    # The acme key cannot see beta's record.
    response = await client.get(
        f"/v1/capsules/{r.step_id}",
        headers={"X-API-Key": ctx["api_key"]},  # acme key
    )
    assert response.status_code == 404
    # The beta key can.
    response = await client.get(
        f"/v1/capsules/{r.step_id}",
        headers={"X-API-Key": "air_test_beta"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_workspace_returns_bootstrap_key(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, ctx = cloud_client
    response = await client.post(
        "/v1/workspaces",
        headers={"X-Admin-Token": ctx["admin_token"]},
        json={"workspace_id": "newco", "name": "NewCo", "owner_email": "x@newco.io"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["workspace"]["workspace_id"] == "newco"
    assert body["bootstrap_api_key"]["key"].startswith("air_")
    assert body["bootstrap_api_key"]["role"] == "owner"


@pytest.mark.asyncio
async def test_create_workspace_conflicts_on_duplicate(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, ctx = cloud_client
    response = await client.post(
        "/v1/workspaces",
        headers={"X-Admin-Token": ctx["admin_token"]},
        json={"workspace_id": "acme", "name": "x", "owner_email": "y@y.io"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_workspace_rejects_missing_admin_token(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, _ = cloud_client
    response = await client.post(
        "/v1/workspaces",
        json={"workspace_id": "nope", "name": "Nope", "owner_email": "x@nope.io"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_workspace_rejects_wrong_admin_token(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, _ = cloud_client
    response = await client.post(
        "/v1/workspaces",
        headers={"X-Admin-Token": "wrong"},
        json={"workspace_id": "nope", "name": "Nope", "owner_email": "x@nope.io"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_workspace_rejects_tenant_api_key(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    """A tenant's own API key can no longer mint additional workspaces."""
    client, ctx = cloud_client
    response = await client.post(
        "/v1/workspaces",
        headers={"X-API-Key": ctx["api_key"]},
        json={"workspace_id": "sneaky", "name": "Sneaky", "owner_email": "x@sneaky.io"},
    )
    assert response.status_code == 401
    assert ctx["workspace_store"].get("sneaky") is None


@pytest.mark.asyncio
async def test_create_workspace_disabled_when_no_admin_token_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no admin token configured the route fails closed with 503."""
    monkeypatch.delenv("AIR_CLOUD_ADMIN_TOKEN", raising=False)
    app = create_air_cloud_app(
        capsule_store=InMemoryCapsuleStore(),
        workspace_store=InMemoryWorkspaceStore(),
        api_key_store=InMemoryApiKeyStore(),
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/workspaces",
            headers={"X-Admin-Token": "anything"},
            json={"workspace_id": "x", "name": "X", "owner_email": "x@x.io"},
        )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_issue_key_then_list_then_revoke(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, ctx = cloud_client
    issue = await client.post(
        "/v1/keys",
        headers={"X-API-Key": ctx["api_key"]},
        json={"name": "ci", "role": "owner"},
    )
    assert issue.status_code == 201
    issued = issue.json()
    assert issued["key"].startswith("air_")
    new_key_id = issued["key_id"]

    listing = await client.get("/v1/keys", headers={"X-API-Key": ctx["api_key"]})
    assert listing.status_code == 200
    redacted = listing.json()
    assert all("key" not in k for k in redacted)
    assert any(k["key_id"] == new_key_id for k in redacted)

    revoke = await client.delete(
        f"/v1/keys/{new_key_id}",
        headers={"X-API-Key": ctx["api_key"]},
    )
    assert revoke.status_code == 200
    assert revoke.json()["revoked"] is True


@pytest.mark.asyncio
async def test_revoked_key_loses_access(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, ctx = cloud_client
    issue = await client.post(
        "/v1/keys",
        headers={"X-API-Key": ctx["api_key"]},
        json={"name": "temp"},
    )
    secondary_key = issue.json()["key"]
    secondary_key_id = issue.json()["key_id"]

    # secondary key works
    ok = await client.get("/v1/workspaces/me", headers={"X-API-Key": secondary_key})
    assert ok.status_code == 200

    # revoke it
    await client.delete(f"/v1/keys/{secondary_key_id}", headers={"X-API-Key": ctx["api_key"]})

    # now it does not
    blocked = await client.get("/v1/workspaces/me", headers={"X-API-Key": secondary_key})
    assert blocked.status_code == 401


@pytest.mark.asyncio
async def test_non_owner_role_cannot_issue_or_revoke_keys(
    cloud_client: tuple[httpx.AsyncClient, dict],
) -> None:
    client, ctx = cloud_client
    viewer = ApiKey(
        key_id="key_acme_viewer",
        workspace_id="acme",
        key="air_viewer_key",
        role="viewer",
    )
    ctx["api_key_store"].issue(viewer)

    deny_issue = await client.post(
        "/v1/keys",
        headers={"X-API-Key": viewer.key},
        json={"name": "x"},
    )
    assert deny_issue.status_code == 403

    deny_revoke = await client.delete(
        "/v1/keys/key_acme_owner",
        headers={"X-API-Key": viewer.key},
    )
    assert deny_revoke.status_code == 403
