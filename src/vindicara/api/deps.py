"""FastAPI dependency injection."""

from functools import lru_cache

from vindicara.engine.evaluator import Evaluator
from vindicara.engine.policy import PolicyRegistry


@lru_cache(maxsize=1)
def get_evaluator() -> Evaluator:
    return Evaluator.with_builtins()


@lru_cache(maxsize=1)
def get_registry() -> PolicyRegistry:
    return PolicyRegistry.with_builtins()
