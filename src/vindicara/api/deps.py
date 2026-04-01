"""FastAPI dependency injection."""

from functools import lru_cache

from vindicara.engine.evaluator import Evaluator
from vindicara.engine.policy import PolicyRegistry
from vindicara.identity.authz import AuthzEngine
from vindicara.identity.registry import AgentRegistry
from vindicara.mcp.scanner import MCPScanner


@lru_cache(maxsize=1)
def get_evaluator() -> Evaluator:
    return Evaluator.with_builtins()


@lru_cache(maxsize=1)
def get_registry() -> PolicyRegistry:
    return PolicyRegistry.with_builtins()


@lru_cache(maxsize=1)
def get_scanner() -> MCPScanner:
    """Get the singleton MCP scanner instance."""
    return MCPScanner()


@lru_cache(maxsize=1)
def get_agent_registry() -> AgentRegistry:
    return AgentRegistry()


@lru_cache(maxsize=1)
def get_authz_engine() -> AuthzEngine:
    return AuthzEngine(get_agent_registry())
