"""Console grants: ``GET /v1/entitlements/grant``.

The workspace's ``tier`` in AIR Cloud is the single authority for what a
customer may do, on every tier including free. This route turns that tier
into the same Ed25519-signed license token ``airsdk_pro.license`` already
verifies offline, so the CLI (``air grant``) and the Flightdeck console pull
their entitlements from the console instead of from an emailed file.

Grants are short-lived (``GRANT_DAYS``) and re-issued on request; a
workspace that downgrades or lapses simply stops renewing. The signing key
is the same vendor key the Stripe fulfilment path uses. Without it the
route fails closed with 503 rather than minting anything unsigned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from vindicara.cloud.roles import Capability, require
from vindicara.licensing import LicenseIssuanceError, issue_license_token, plan_for_tier

if TYPE_CHECKING:
    from vindicara.cloud.workspace import WorkspaceStore

router = APIRouter(tags=["entitlements"])


class Grant(BaseModel):
    """A console-issued entitlement grant for the calling workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    tier: str
    email: str
    expires_at: int
    features: list[str]
    token: dict[str, object]  # the signed license token, verbatim


@router.get(
    "/v1/entitlements/grant",
    response_model=Grant,
    summary="Issue the calling workspace's entitlement grant from its tier.",
)
async def get_grant(request: Request) -> Grant:
    require(request, Capability.READ_WORKSPACE)
    store: WorkspaceStore = request.app.state.cloud_workspaces
    workspace_id: str = request.state.workspace_id
    workspace = store.get(workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"workspace {workspace_id!r} no longer exists"
        )
    signing_key_pem: str | None = getattr(request.app.state, "license_signing_key_pem", None)
    if not signing_key_pem:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AIR Cloud not configured: no license signing key; grants are disabled",
        )
    try:
        plan = plan_for_tier(workspace.tier)
        token = issue_license_token(email=workspace.owner_email, plan=plan, signing_key_pem=signing_key_pem)
    except LicenseIssuanceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return Grant(
        workspace_id=workspace.workspace_id,
        tier=plan.tier,
        email=workspace.owner_email,
        expires_at=int(str(token["expires_at"])),
        features=sorted(plan.features),
        token=token,
    )
