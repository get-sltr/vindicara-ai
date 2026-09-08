"""Self-serve sign-in: one identity, one workspace, the owner key shown exactly once."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("VINDICARA_SESSION_SECRET", "test_secret_for_unit_tests_only_0000")

from vindicara.cloud.factory import create_air_cloud_app
from vindicara.cloud.identity_store import InMemoryIdentityStore
from vindicara.cloud.signup import (
    ServiceOidc,
    VerifiedIdentity,
    provision_identity,
    resolve_email,
    service_oidc_from_env,
    verify_identity,
    workspace_name_for,
)
from vindicara.cloud.sso import SsoVerificationError
from vindicara.cloud.workspace import InMemoryApiKeyStore, InMemoryWorkspaceStore

OIDC = ServiceOidc(issuer="https://tenant.example/", audience="https://api.vindicara.io", client_ids=frozenset({"cli-app"}))


def _app(oidc: ServiceOidc | None = OIDC) -> Any:
    return create_air_cloud_app(
        workspace_store=InMemoryWorkspaceStore(),
        api_key_store=InMemoryApiKeyStore(),
        identity_store=InMemoryIdentityStore(),
        service_oidc=oidc,
        cloud_url="http://cloud.test",
        console_url="http://console.test/flightdeck",
    )


def _identity(sub: str = "auth0|kev", email: str | None = "kev@vindicara.io", verified: bool = True) -> VerifiedIdentity:
    return VerifiedIdentity(issuer=OIDC.issuer, sub=sub, email=email, email_verified=verified)


async def _exchange(app: Any, token: str = "t") -> tuple[int, dict[str, Any]]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/v1/auth/exchange", json={"token": token})
    return resp.status_code, resp.json()


@pytest.mark.anyio
async def test_first_exchange_creates_workspace_and_shows_key_once() -> None:
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity()):
        status, first = await _exchange(app)
        status2, second = await _exchange(app)
    assert status == 201, first
    assert first["created"] is True
    assert first["api_key"].startswith("air_")
    assert first["role"] == "owner"
    assert first["workspace"]["name"] == "kev's workspace"
    assert first["workspace"]["tier"] == "free"
    assert first["cloud_url"] == "http://cloud.test"
    assert first["console_url"] == "http://console.test/flightdeck"
    assert status2 == 200
    assert second["created"] is False
    assert second["api_key"] is None
    assert second["workspace"]["workspace_id"] == first["workspace"]["workspace_id"]


@pytest.mark.anyio
async def test_session_token_from_exchange_acts_as_owner() -> None:
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity()):
        _, body = await _exchange(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/keys", headers={"Authorization": f"Bearer {body['session_token']}"})
        me = await client.get("/v1/workspaces/me", headers={"Authorization": f"Bearer {body['session_token']}"})
    assert resp.status_code == 200
    assert [k["key_id"] for k in resp.json()] == [body["key_id"]]
    assert me.json()["workspace_id"] == body["workspace"]["workspace_id"]


@pytest.mark.anyio
async def test_different_subjects_get_different_workspaces() -> None:
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("auth0|a", "a@x.io")):
        _, a = await _exchange(app)
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("auth0|b", "b@x.io")):
        _, b = await _exchange(app)
    assert a["workspace"]["workspace_id"] != b["workspace"]["workspace_id"]


@pytest.mark.anyio
async def test_same_verified_email_on_another_connection_shares_the_workspace() -> None:
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("google-oauth2|1", "kev@vindicara.io")):
        _, first = await _exchange(app)
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("auth0|2", "kev@vindicara.io")):
        status, second = await _exchange(app)
    assert status == 200
    assert second["workspace"]["workspace_id"] == first["workspace"]["workspace_id"]
    assert second["api_key"] is None


@pytest.mark.anyio
async def test_unverified_email_never_joins_an_existing_workspace() -> None:
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("google-oauth2|1", "kev@vindicara.io")):
        _, first = await _exchange(app)
    with patch("vindicara.cloud.routes.auth.verify_identity", return_value=_identity("auth0|2", "kev@vindicara.io", verified=False)):
        _, second = await _exchange(app)
    assert second["workspace"]["workspace_id"] != first["workspace"]["workspace_id"]


@pytest.mark.anyio
async def test_no_service_oidc_is_503_and_bad_token_is_401() -> None:
    status, body = await _exchange(_app(oidc=None))
    assert status == 503
    assert "AIR_CLOUD_OIDC_ISSUER" in body["detail"]
    app = _app()
    with patch("vindicara.cloud.routes.auth.verify_identity", side_effect=SsoVerificationError("token verification failed: bad")):
        status, body = await _exchange(app)
    assert status == 401
    assert "bad" in body["detail"]


def test_provisioning_repairs_a_link_whose_workspace_is_missing() -> None:
    ws, keys, ids = InMemoryWorkspaceStore(), InMemoryApiKeyStore(), InMemoryIdentityStore()
    first = provision_identity(_identity(), workspace_store=ws, api_key_store=keys, identity_store=ids)
    assert first.created and first.api_key is not None
    # Simulate a crash between link and workspace creation on a fresh deployment.
    ws2, keys2 = InMemoryWorkspaceStore(), InMemoryApiKeyStore()
    repaired = provision_identity(_identity(), workspace_store=ws2, api_key_store=keys2, identity_store=ids)
    assert repaired.workspace.workspace_id == first.workspace.workspace_id
    assert repaired.created and repaired.api_key is not None


def test_revoked_owner_key_is_not_reminted_silently() -> None:
    ws, keys, ids = InMemoryWorkspaceStore(), InMemoryApiKeyStore(), InMemoryIdentityStore()
    first = provision_identity(_identity(), workspace_store=ws, api_key_store=keys, identity_store=ids)
    assert keys.revoke(first.key_id)
    again = provision_identity(_identity(), workspace_store=ws, api_key_store=keys, identity_store=ids)
    assert again.api_key is None
    assert again.key_id == first.key_id


def test_workspace_name_fallback_without_email() -> None:
    assert workspace_name_for("kev@vindicara.io", "auth0|x") == "kev's workspace"
    assert workspace_name_for(None, "auth0|1234567890") == "workspace 34567890"


def test_resolve_email_prefers_claims_then_userinfo() -> None:
    assert resolve_email({"https://vindicara.io/email": "a@x.io", "https://vindicara.io/email_verified": True}, "t", OIDC.issuer) == ("a@x.io", True)
    assert resolve_email({"email": "b@x.io"}, "t", OIDC.issuer) == ("b@x.io", False)
    calls: list[tuple[str, str]] = []

    def fake_userinfo(issuer: str, token: str) -> tuple[str | None, bool]:
        calls.append((issuer, token))
        return "c@x.io", True

    assert resolve_email({}, "tok", OIDC.issuer, userinfo=fake_userinfo) == ("c@x.io", True)
    assert calls == [(OIDC.issuer, "tok")]


def test_verify_identity_rejects_foreign_client_ids() -> None:
    claims = {"sub": "auth0|kev", "azp": "someone-elses-app", "email": "k@x.io", "email_verified": True}
    with patch("vindicara.cloud.signup.verify_oidc_token", return_value=claims), pytest.raises(SsoVerificationError, match="client"):
        verify_identity("t", OIDC, jwks_client_factory=lambda uri: None)
    claims["azp"] = "cli-app"
    with patch("vindicara.cloud.signup.verify_oidc_token", return_value=claims):
        identity = verify_identity("t", OIDC, jwks_client_factory=lambda uri: None)
    assert identity.sub == "auth0|kev"
    assert identity.email == "k@x.io"


def test_service_oidc_from_env() -> None:
    assert service_oidc_from_env({}) is None
    oidc = service_oidc_from_env({
        "AIR_CLOUD_OIDC_ISSUER": "https://t/", "AIR_CLOUD_OIDC_AUDIENCE": "aud", "AIR_CLOUD_OIDC_CLIENT_IDS": "a, b",
    })
    assert oidc is not None
    assert oidc.client_ids == frozenset({"a", "b"})
    assert oidc.as_sso_config().resolved_jwks_uri() == "https://t/.well-known/jwks.json"
