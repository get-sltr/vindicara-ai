"""Tests for the POST /v1/guard endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_guard_allowed(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={
                "input": "What is the weather?",
                "output": "It is sunny today.",
                "policy": "content-safety",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    assert response.json()["verdict"] == "allowed"


@pytest.mark.asyncio
async def test_guard_blocked_pii(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={"input": "Show info", "output": "SSN: 123-45-6789", "policy": "pii-filter"},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    assert response.json()["verdict"] == "blocked"


@pytest.mark.asyncio
async def test_guard_missing_api_key(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={"input": "test", "output": "test", "policy": "content-safety"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_guard_unknown_policy(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={"input": "test", "output": "test", "policy": "nonexistent"},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_guard_empty_input_and_output(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={"input": "", "output": "", "policy": "content-safety"},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_guard_has_request_id(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/guard",
            json={"input": "test", "output": "test", "policy": "content-safety"},
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert "x-request-id" in response.headers
