"""Vindicara: Runtime security for autonomous AI."""

from vindicara.sdk.client import VindicaraClient as Client
from vindicara.sdk.exceptions import (
    VindicaraAuthError,
    VindicaraError,
    VindicaraPolicyViolation,
    VindicaraRateLimited,
)
from vindicara.sdk.types import GuardResult, PolicyInfo

__all__ = [
    "Client",
    "GuardResult",
    "PolicyInfo",
    "VindicaraAuthError",
    "VindicaraError",
    "VindicaraPolicyViolation",
    "VindicaraRateLimited",
]

__version__ = "0.1.0"
