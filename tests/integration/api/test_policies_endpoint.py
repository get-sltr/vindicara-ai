"""Tests for the policies endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_list_policies(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/policies", headers={"X-Vindicara-Key": "vnd_test"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    policy_ids = [p["policy_id"] for p in data]
    assert "content-safety" in policy_ids
    assert "pii-filter" in policy_ids
    assert "prompt-injection" in policy_ids
