"""Tests for POST /v1/mcp/scan endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_static_scan(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/mcp/scan",
            json={
                "config": {
                    "tools": [
                        {"name": "shell_exec", "description": "Run commands", "inputSchema": {}}
                    ]
                },
                "mode": "static",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 0
    assert len(data["findings"]) > 0
    assert data["mode"] == "static"


@pytest.mark.asyncio
async def test_static_scan_clean(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/mcp/scan",
            json={
                "config": {
                    "tools": [{"name": "get_weather", "description": "Weather", "inputSchema": {}}],
                    "auth": {"type": "oauth2", "pkce": True},
                    "rateLimit": {"maxRequestsPerMinute": 100},
                },
                "mode": "static",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] < 0.3


@pytest.mark.asyncio
async def test_scan_requires_auth(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/mcp/scan",
            json={"config": {"tools": []}, "mode": "static"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_dry_run(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/mcp/scan",
            json={"server_url": "https://mcp.test", "mode": "live", "dry_run": True},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 0.0
    assert data["findings"] == []
