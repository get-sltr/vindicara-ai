"""CLI configuration management for Project AIR.

Manages ``~/.config/projectair/`` (or the platform/XDG equivalent) on behalf
of the ``air`` CLI. The same directory is used by ``airsdk.anchoring.identity``
for ``anchoring_key.pem``; the ``config_dir()`` function here deliberately
mirrors ``default_key_dir()`` in that module so both subsystems always agree on
the path.

Files managed here:

- ``config.toml``   -- persistent user preferences (TOML, human-readable)
- ``session.json``  -- short-lived auth session data (JSON, mode 0600)
- ``prompted``      -- zero-byte marker: user has seen the first-run email prompt
"""
from __future__ import annotations

import json
import os
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 backport
    import tomli as tomllib
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

def config_dir() -> Path:
    """Return the platform-appropriate configuration directory.

    Resolution order (mirrors ``airsdk.anchoring.identity.default_key_dir``):

    1. ``APPDATA/projectair`` on Windows.
    2. ``XDG_CONFIG_HOME/projectair`` when the env var is set.
    3. ``~/.config/projectair`` as the universal fallback.
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "projectair"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "projectair"
    return Path.home() / ".config" / "projectair"


# ---------------------------------------------------------------------------
# config.toml helpers
# ---------------------------------------------------------------------------

_CONFIG_FILE = "config.toml"


def _config_path() -> Path:
    return config_dir() / _CONFIG_FILE


def _read_toml() -> dict[str, Any]:
    """Read config.toml; return empty dict when the file does not exist."""
    path = _config_path()
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _write_toml(data: dict[str, Any]) -> None:
    """Serialise *data* to config.toml using a simple hand-written TOML writer.

    Only string values are stored (callers convert to/from string as needed).
    The format is intentionally minimal: ``[section]\\nkey = "value"\\n`` blocks.
    No ``tomli-w`` dependency required.
    """
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for section, mapping in sorted(data.items()):
        lines.append(f"[{section}]")
        for key, value in sorted(mapping.items()):
            # Escape backslashes and double-quotes inside values.
            escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{escaped}"')
        lines.append("")
    # The file may hold the workspace API key saved by `air login`; keep it private.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    os.chmod(path, 0o600)


def get_config(section: str, key: str) -> str | None:
    """Return the string value at *section*/*key*, or ``None`` if absent."""
    data = _read_toml()
    sec = data.get(section)
    if not isinstance(sec, dict):
        return None
    value = sec.get(key)
    return str(value) if value is not None else None


def set_config(section: str, key: str, value: str) -> None:
    """Persist *value* at *section*/*key* in ``config.toml``."""
    data = _read_toml()
    if section not in data or not isinstance(data[section], dict):
        data[section] = {}
    data[section][key] = value
    _write_toml(data)


def list_config() -> dict[str, dict[str, str]]:
    """Return all configuration as a nested ``{section: {key: value}}`` dict."""
    raw = _read_toml()
    result: dict[str, dict[str, str]] = {}
    for section, mapping in raw.items():
        if isinstance(mapping, dict):
            result[section] = {k: str(v) for k, v in mapping.items()}
    return result


# ---------------------------------------------------------------------------
# session.json helpers
# ---------------------------------------------------------------------------

_SESSION_FILE = "session.json"


def session_path() -> Path:
    """Return the absolute path to ``session.json``."""
    return config_dir() / _SESSION_FILE


def load_session() -> dict[str, Any] | None:
    """Read ``session.json``; return ``None`` when the file does not exist."""
    sp = session_path()
    if not sp.exists():
        return None
    return json.loads(sp.read_text(encoding="utf-8"))


def save_session(data: dict[str, Any]) -> None:
    """Write *data* to ``session.json`` with mode ``0o600``.

    The directory is created if absent. The file is written with restricted
    permissions so credentials stored in the session are not world-readable.
    """
    sp = session_path()
    sp.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, indent=2)
    fd = os.open(str(sp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(raw)
    except Exception:
        sp.unlink(missing_ok=True)
        raise


def delete_session() -> bool:
    """Delete ``session.json``.

    Returns ``True`` if the file existed and was removed, ``False`` otherwise.
    """
    sp = session_path()
    if not sp.exists():
        return False
    sp.unlink()
    return True


# ---------------------------------------------------------------------------
# First-run prompt marker
# ---------------------------------------------------------------------------

_PROMPTED_FILE = "prompted"


def has_been_prompted() -> bool:
    """Return ``True`` if the first-run email prompt marker exists."""
    return (config_dir() / _PROMPTED_FILE).exists()


def mark_prompted() -> None:
    """Create the first-run prompt marker (idempotent)."""
    marker = config_dir() / _PROMPTED_FILE
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)
