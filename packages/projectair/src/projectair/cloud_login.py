"""``air login`` second half: trade the identity-provider token for a workspace.

The device flow proves who the human is. This module hands that proof to
AIR Cloud (``POST /v1/auth/exchange``), which answers with the workspace
that identity owns, creating it on the first sign-in, and, exactly once,
the workspace's owner API key. The key is saved to ``config.toml`` with
mode 0600 so every later ``air push`` / ``air grant`` finds it without an
environment variable.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from projectair.config import set_config

_TIMEOUT_SECONDS = 15


class CloudLoginError(Exception):
    """AIR Cloud did not hand back a workspace."""


@dataclass(frozen=True)
class CloudLogin:
    workspace_id: str
    workspace_name: str
    tier: str
    role: str
    created: bool
    api_key: str | None  # only on the sign-in that minted it
    cloud_url: str
    console_url: str
    email: str | None


def exchange_device_token(cloud_url: str, access_token: str) -> CloudLogin:
    """POST the Auth0 access token to the exchange route and parse the answer."""
    base = cloud_url.rstrip("/")
    if not base.startswith(("https://", "http://")):
        raise CloudLoginError(f"cloud URL must be http(s): {base!r}")
    request = urllib.request.Request(  # noqa: S310 (scheme checked above)
        f"{base}/v1/auth/exchange",
        data=json.dumps({"token": access_token}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "air-cli"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise CloudLoginError(f"AIR Cloud answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CloudLoginError(f"could not reach {base}: {exc}") from exc
    if not isinstance(body, dict) or not isinstance(body.get("workspace"), dict):
        raise CloudLoginError("AIR Cloud response carried no workspace")
    workspace = body["workspace"]
    api_key = body.get("api_key")
    return CloudLogin(
        workspace_id=str(workspace.get("workspace_id", "")),
        workspace_name=str(workspace.get("name", "")),
        tier=str(workspace.get("tier", "free")),
        role=str(body.get("role", "")),
        created=bool(body.get("created", False)),
        api_key=api_key if isinstance(api_key, str) and api_key else None,
        cloud_url=str(body.get("cloud_url") or base),
        console_url=str(body.get("console_url") or ""),
        email=str(body["email"]) if isinstance(body.get("email"), str) else None,
    )


def store_cloud_login(login: CloudLogin) -> None:
    """Persist the workspace, URLs, and (when handed back) the key under ``[cloud]``."""
    set_config("cloud", "workspace_id", login.workspace_id)
    set_config("cloud", "workspace_name", login.workspace_name)
    set_config("cloud", "url", login.cloud_url.rstrip("/"))
    if login.console_url:
        set_config("cloud", "console_url", login.console_url.rstrip("/"))
    if login.api_key is not None:
        set_config("cloud", "api_key", login.api_key)


__all__ = ["CloudLogin", "CloudLoginError", "exchange_device_token", "store_cloud_login"]
