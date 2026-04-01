"""Agent identity management endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from vindicara.api.deps import get_agent_registry, get_authz_engine
from vindicara.identity.authz import AuthzEngine
from vindicara.identity.models import (
    AgentIdentity,
    CheckRequest,
    CheckResult,
    RegisterAgentRequest,
    SuspendRequest,
)
from vindicara.identity.registry import AgentNotFoundError, AgentRegistry

logger = structlog.get_logger()

router = APIRouter(prefix="/v1")


@router.post("/agents", response_model=AgentIdentity)
async def register_agent(
    request: RegisterAgentRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentIdentity:
    log = logger.bind(agent_name=request.name)
    log.info("api.agent.register")
    return registry.register(
        name=request.name,
        permitted_tools=request.permitted_tools,
        data_scope=request.data_scope,
        limits=request.limits,
    )


@router.get("/agents", response_model=list[AgentIdentity])
async def list_agents(
    registry: AgentRegistry = Depends(get_agent_registry),
) -> list[AgentIdentity]:
    return registry.list_agents()


@router.get("/agents/{agent_id}", response_model=AgentIdentity)
async def get_agent(
    agent_id: str,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentIdentity:
    try:
        return registry.get(agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/agents/{agent_id}/check", response_model=CheckResult)
async def check_permission(
    agent_id: str,
    request: CheckRequest,
    engine: AuthzEngine = Depends(get_authz_engine),
) -> CheckResult:
    try:
        if request.data_scope:
            return engine.check_data_scope(agent_id, request.data_scope)
        return engine.check_tool(agent_id, request.tool)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/agents/{agent_id}/suspend", response_model=AgentIdentity)
async def suspend_agent(
    agent_id: str,
    request: SuspendRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentIdentity:
    try:
        return registry.suspend(agent_id, reason=request.reason)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
