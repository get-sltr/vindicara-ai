"""Self-serve sign-in: ``POST /v1/auth/exchange``.

The console and the CLI both sign the human in with the identity provider,
then trade that token here for three things: an AIR Cloud session token, the
workspace that identity owns (created on first sign-in), and, exactly once,
the workspace's owner API key. Unauthenticated by design: the caller has no
AIR Cloud credential yet.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict

from vindicara.cloud.session_token import SessionClaims, create_session_token
from vindicara.cloud.signup import ServiceOidc, provision_identity, verify_identity
from vindicara.cloud.sso import SsoVerificationError
from vindicara.cloud.workspace import Workspace  # noqa: TC001 (pydantic resolves the field type at runtime)

_log = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

SESSION_TTL_SECONDS = 3600


class ExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str


class ExchangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_token: str
    workspace: Workspace
    role: str
    key_id: str
    api_key: str | None  # shown once: only on the sign-in that minted it
    created: bool
    email: str | None
    sub: str
    cloud_url: str
    console_url: str


@router.post(
    "/v1/auth/exchange",
    response_model=ExchangeResponse,
    summary="Trade an identity-provider token for a session, a workspace, and (once) its owner key.",
)
async def exchange(request: Request, payload: ExchangeRequest, response: Response) -> ExchangeResponse:
    oidc: ServiceOidc | None = getattr(request.app.state, "service_oidc", None)
    if oidc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="sign-in is not configured: no service identity provider (AIR_CLOUD_OIDC_ISSUER / _AUDIENCE)",
        )
    try:
        identity = verify_identity(payload.token, oidc)
    except SsoVerificationError as exc:
        _log.info("air_cloud.auth.exchange", extra={"outcome": "rejected", "reason": str(exc)})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    provisioned = provision_identity(
        identity,
        workspace_store=request.app.state.cloud_workspaces,
        api_key_store=request.app.state.cloud_api_keys,
        identity_store=request.app.state.cloud_identities,
    )
    claims = SessionClaims(
        workspace_id=provisioned.workspace.workspace_id, role=provisioned.role, sub=identity.sub, key_id=provisioned.key_id
    )
    outcome = "created" if provisioned.created else "returning"
    _log.info(
        "air_cloud.auth.exchange",
        extra={"outcome": outcome, "workspace_id": provisioned.workspace.workspace_id, "key_minted": provisioned.api_key is not None},
    )
    response.status_code = status.HTTP_201_CREATED if provisioned.created else status.HTTP_200_OK
    return ExchangeResponse(
        session_token=create_session_token(claims, ttl_seconds=SESSION_TTL_SECONDS),
        workspace=provisioned.workspace,
        role=provisioned.role,
        key_id=provisioned.key_id,
        api_key=provisioned.api_key.key if provisioned.api_key is not None else None,
        created=provisioned.created,
        email=identity.email,
        sub=identity.sub,
        cloud_url=str(request.app.state.cloud_url),
        console_url=str(request.app.state.console_url),
    )
