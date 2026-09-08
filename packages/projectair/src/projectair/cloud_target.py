"""Where the CLI talks to AIR Cloud, resolved once for every command.

Precedence, highest first: an explicit flag, the environment
(``AIRSDK_CLOUD_API_KEY`` / ``AIRSDK_CLOUD_URL`` / ``AIRSDK_CONSOLE_URL``), then
what ``air login`` saved in ``config.toml`` under ``[cloud]``. The SDK reads
only the environment (a library must not read a user's config file behind
their back); the CLI is the user, so it may.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from airsdk.cloud_config import DEFAULT_CLOUD_URL, DEFAULT_CONSOLE_URL
from projectair.config import get_config


@dataclass(frozen=True)
class CloudTarget:
    api_key: str | None
    url: str
    console_url: str

    @property
    def source(self) -> str:
        """Where the key came from, for messages: ``flag``, ``env``, ``config``, or ``none``."""
        return self._source

    _source: str = "none"


def _pick(flag: str | None, env_name: str, section_key: str) -> tuple[str | None, str]:
    if flag:
        return flag, "flag"
    from_env = os.environ.get(env_name, "").strip()
    if from_env:
        return from_env, "env"
    from_config = get_config("cloud", section_key)
    if from_config:
        return from_config, "config"
    return None, "none"


def resolve_cloud_target(api_key: str | None = None, url: str | None = None) -> CloudTarget:
    """Resolve the API key, ingest URL, and console URL for this invocation."""
    key, key_source = _pick(api_key, "AIRSDK_CLOUD_API_KEY", "api_key")
    base, _ = _pick(url, "AIRSDK_CLOUD_URL", "url")
    console, _ = _pick(None, "AIRSDK_CONSOLE_URL", "console_url")
    return CloudTarget(
        api_key=key,
        url=(base or DEFAULT_CLOUD_URL).rstrip("/"),
        console_url=(console or DEFAULT_CONSOLE_URL).rstrip("/"),
        _source=key_source,
    )


__all__ = ["CloudTarget", "resolve_cloud_target"]
