"""Tests for compliance report endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from vindicara.compliance.frameworks import FRAMEWORKS


@pytest.mark.asyncio
async def test_list_frameworks(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/v1/compliance/frameworks",
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    # Frameworks are data (compliance/frameworks.py); the registry is the source
    # of truth. Asserting a literal count broke as soon as HIPAA was registered.
    ids = {f["framework_id"] for f in data}
    assert ids == {fw.value for fw in FRAMEWORKS}
    assert "eu-ai-act-article-72" in ids
    assert "nist-ai-rmf" in ids
    assert "soc2-ai" in ids


@pytest.mark.asyncio
async def test_generate_report(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/compliance/reports",
            json={
                "framework": "eu-ai-act-article-72",
                "system_id": "test-system",
                "period": "2026-Q1",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "eu-ai-act-article-72"
    assert data["system_id"] == "test-system"
    assert data["total_controls"] == 8
    assert data["report_id"].startswith("rpt_")


@pytest.mark.asyncio
async def test_generate_nist_report(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/compliance/reports",
            json={
                "framework": "nist-ai-rmf",
                "system_id": "sales-bot",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    assert response.json()["total_controls"] == 8


@pytest.mark.asyncio
async def test_generate_soc2_report(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/compliance/reports",
            json={
                "framework": "soc2-ai",
                "system_id": "test",
            },
            headers={"X-Vindicara-Key": "vnd_test"},
        )
    assert response.status_code == 200
    assert response.json()["total_controls"] == 8
