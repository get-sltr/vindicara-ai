"""Health and readiness endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "vindicara"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "vindicara"}
