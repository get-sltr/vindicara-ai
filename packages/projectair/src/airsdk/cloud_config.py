"""Zero-config AIR Cloud mirroring, driven by two environment variables.

The Keys screen hands a developer one line to export, ``AIRSDK_CLOUD_API_KEY``.
When it is set, every :class:`~airsdk.recorder.AIRRecorder` that is built
without an explicit ``transports=`` list keeps writing its local chain and
also mirrors each signed record to AIR Cloud. Nothing else changes.

- ``AIRSDK_CLOUD_API_KEY``: the workspace key (``air_...``). Required.
- ``AIRSDK_CLOUD_URL``: the ingest base URL. Defaults to the hosted service.
- ``AIRSDK_CONSOLE_URL``: where run links point. Defaults to Flightdeck.
- ``AIRSDK_CLOUD``: set to ``off`` (or ``0`` / ``false`` / ``no``) to disable
  mirroring even when a key is present. The kill switch exists because a key
  in the environment ships prompts, responses, and tool output off the
  machine, and an operator must be able to stop that without editing code.

The run id is the genesis record's ``step_id``: every recorder starts a new
chain, so the first record it signs identifies the run on both sides.
"""
from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from airsdk.types import GENESIS_PREV_HASH, AgDRRecord

DEFAULT_CLOUD_URL = "https://cloud.vindicara.io"
DEFAULT_CONSOLE_URL = "https://vindicara.io/flightdeck"

API_KEY_ENV = "AIRSDK_CLOUD_API_KEY"
CLOUD_URL_ENV = "AIRSDK_CLOUD_URL"
CONSOLE_URL_ENV = "AIRSDK_CONSOLE_URL"
KILL_SWITCH_ENV = "AIRSDK_CLOUD"

_OFF_VALUES = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True)
class CloudConfig:
    """Where a recorder mirrors its chain and where its run link points."""

    api_key: str
    url: str = DEFAULT_CLOUD_URL
    console_url: str = DEFAULT_CONSOLE_URL


def cloud_config_from_env(environ: Mapping[str, str] | None = None) -> CloudConfig | None:
    """The mirror configuration in ``environ`` (default ``os.environ``), or ``None``."""
    env = environ if environ is not None else os.environ
    if env.get(KILL_SWITCH_ENV, "").strip().lower() in _OFF_VALUES:
        return None
    api_key = env.get(API_KEY_ENV, "").strip()
    if not api_key:
        return None
    return CloudConfig(
        api_key=api_key,
        url=(env.get(CLOUD_URL_ENV) or DEFAULT_CLOUD_URL).rstrip("/"),
        console_url=(env.get(CONSOLE_URL_ENV) or DEFAULT_CONSOLE_URL).rstrip("/"),
    )


def genesis_step_id(records: Sequence[AgDRRecord]) -> str | None:
    """The run id of a chain: the step_id of its genesis record, if present."""
    for record in records:
        if record.prev_hash == GENESIS_PREV_HASH:
            return record.step_id
    return records[0].step_id if records else None


def run_url(console_url: str, run_id: str) -> str:
    """The Flightdeck page for one run."""
    return f"{console_url.rstrip('/')}/runs/{run_id}"


__all__ = [
    "API_KEY_ENV",
    "CLOUD_URL_ENV",
    "CONSOLE_URL_ENV",
    "DEFAULT_CLOUD_URL",
    "DEFAULT_CONSOLE_URL",
    "KILL_SWITCH_ENV",
    "CloudConfig",
    "cloud_config_from_env",
    "genesis_step_id",
    "run_url",
]
