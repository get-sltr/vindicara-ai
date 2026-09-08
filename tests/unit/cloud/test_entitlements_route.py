"""Console grants: the workspace tier is the authority, on every tier, and the token is signed."""

from __future__ import annotations

import json
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("VINDICARA_SESSION_SECRET", "test_secret_for_unit_tests_only_0000")

from airsdk import features

from vindicara.cloud.factory import create_air_cloud_app
from vindicara.cloud.workspace import ApiKey, InMemoryApiKeyStore, InMemoryWorkspaceStore, Workspace
from vindicara.licensing import LicenseIssuanceError, plan_for_tier

KEY = Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _expect_this_test_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the issuer's key guard at this module's throwaway key.

    The issuer refuses to mint under a key whose public half is not the one
    airsdk_pro embeds. That guard is the point in production, so rather than
    weaken it, tests declare which key they are signing with.
    """
    monkeypatch.setattr(
        "vindicara.licensing.issuer.EXPECTED_LICENSE_PUBLIC_KEY_HEX",
        KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex(),
    )
KEY_PEM = KEY.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()


def _stores(tier: str) -> tuple[InMemoryWorkspaceStore, InMemoryApiKeyStore]:
    ws_store, key_store = InMemoryWorkspaceStore(), InMemoryApiKeyStore()
    ws_store.create(Workspace(workspace_id="ws_t", name="T", owner_email="owner@acme.io", tier=tier))
    key_store.issue(ApiKey(key_id="key_t", workspace_id="ws_t", key="air_" + "ab" * 16, role="viewer"))
    return ws_store, key_store


async def _grant(tier: str, *, pem: str | None = KEY_PEM) -> tuple[int, dict[str, object]]:
    ws_store, key_store = _stores(tier)
    app = create_air_cloud_app(workspace_store=ws_store, api_key_store=key_store, license_signing_key_pem=pem or "")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/entitlements/grant", headers={"X-API-Key": "air_" + "ab" * 16})
    return resp.status_code, resp.json()


def _verify(token: dict[str, object]) -> None:
    payload = {k: v for k, v in token.items() if k != "signature"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    KEY.public_key().verify(bytes.fromhex(str(token["signature"])), canonical)


@pytest.mark.anyio
async def test_free_tier_grant_is_signed_and_grants_nothing() -> None:
    status, body = await _grant("free")
    assert status == 200, body
    assert body["tier"] == "free"
    assert body["features"] == []
    assert body["email"] == "owner@acme.io"
    token = body["token"]
    assert token["tier"] == "free"
    assert token["features"] == []
    _verify(token)


@pytest.mark.anyio
async def test_pro_tier_grant_carries_the_pro_bundle() -> None:
    status, body = await _grant("pro")
    assert status == 200, body
    assert body["tier"] == "pro"
    assert features.FLIGHTDECK_HOSTED in body["features"]
    assert features.PREMIUM_DETECTORS in body["features"]
    assert features.MONITOR not in body["features"]
    assert body["token"]["features"] == body["features"]
    assert body["expires_at"] == body["token"]["expires_at"]
    _verify(body["token"])


@pytest.mark.anyio
async def test_enterprise_grant_adds_the_enterprise_boundary_features() -> None:
    _, body = await _grant("enterprise")
    assert features.REPORT_SOC2_AI in body["features"]
    assert features.HL7_FHIR in body["features"]
    assert features.MONITOR in body["features"]


@pytest.mark.anyio
async def test_missing_signing_key_fails_closed() -> None:
    status, body = await _grant("pro", pem=None)
    assert status == 503
    assert "no license signing key" in body["detail"]


@pytest.mark.anyio
async def test_unknown_tier_is_refused() -> None:
    status, body = await _grant("platinum")
    assert status == 500
    assert "unknown workspace tier" in body["detail"]


@pytest.mark.anyio
async def test_grant_requires_auth() -> None:
    ws_store, key_store = _stores("pro")
    app = create_air_cloud_app(workspace_store=ws_store, api_key_store=key_store, license_signing_key_pem=KEY_PEM)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/entitlements/grant")
    assert resp.status_code == 401


def test_plan_for_tier_rejects_unknown() -> None:
    with pytest.raises(LicenseIssuanceError, match="unknown workspace tier"):
        plan_for_tier("gold")
    assert plan_for_tier("team").duration_days == 30
