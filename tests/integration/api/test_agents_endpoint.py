"""Tests for agent identity endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_register_agent(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/agents",
            json={"name": "sales-bot", "permitted_tools": ["crm_read", "email_send"], "data_scope": ["accounts.sales"], "limits": {"max_actions_per_minute": 60}},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "sales-bot"
    assert data["status"] == "active"
    assert data["agent_id"].startswith("agent_")


@pytest.mark.asyncio
async def test_list_agents(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/v1/agents", json={"name": "bot-a"}, headers={"X-Vindicara-Key": "vnd_test"})
        response = await client.get("/v1/agents", headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_check_permission_allowed(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post("/v1/agents", json={"name": "bot", "permitted_tools": ["crm_read"]}, headers={"X-Vindicara-Key": "vnd_test"})
        agent_id = reg.json()["agent_id"]
        response = await client.post(f"/v1/agents/{agent_id}/check", json={"tool": "crm_read"}, headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    assert response.json()["allowed"] is True


@pytest.mark.asyncio
async def test_check_permission_denied(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post("/v1/agents", json={"name": "bot", "permitted_tools": ["crm_read"]}, headers={"X-Vindicara-Key": "vnd_test"})
        agent_id = reg.json()["agent_id"]
        response = await client.post(f"/v1/agents/{agent_id}/check", json={"tool": "admin_delete"}, headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    assert response.json()["allowed"] is False


@pytest.mark.asyncio
async def test_suspend_agent(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post("/v1/agents", json={"name": "bot", "permitted_tools": ["crm_read"]}, headers={"X-Vindicara-Key": "vnd_test"})
        agent_id = reg.json()["agent_id"]
        response = await client.post(f"/v1/agents/{agent_id}/suspend", json={"reason": "Anomalous behavior detected"}, headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


@pytest.mark.asyncio
async def test_suspended_agent_denied_permission(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post("/v1/agents", json={"name": "bot", "permitted_tools": ["crm_read"]}, headers={"X-Vindicara-Key": "vnd_test"})
        agent_id = reg.json()["agent_id"]
        await client.post(f"/v1/agents/{agent_id}/suspend", json={"reason": "Kill switch"}, headers={"X-Vindicara-Key": "vnd_test"})
        response = await client.post(f"/v1/agents/{agent_id}/check", json={"tool": "crm_read"}, headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    assert response.json()["allowed"] is False


@pytest.mark.asyncio
async def test_get_nonexistent_agent(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/agents/nonexistent", headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 404
