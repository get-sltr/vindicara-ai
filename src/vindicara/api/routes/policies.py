"""Policy management endpoints."""

from fastapi import APIRouter, Depends

from vindicara.api.deps import get_registry
from vindicara.engine.policy import PolicyRegistry
from vindicara.sdk.types import PolicyInfo

router = APIRouter(prefix="/v1")


@router.get("/policies", response_model=list[PolicyInfo])
async def list_policies(
    registry: PolicyRegistry = Depends(get_registry),
) -> list[PolicyInfo]:
    return registry.list_policies()
