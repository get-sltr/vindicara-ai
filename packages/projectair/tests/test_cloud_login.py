"""air login's second half: the exchange call, what gets saved, and how failure is reported."""
from __future__ import annotations

import io
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from projectair import cloud_login, cloud_target
from projectair.cli import app
from projectair.config import _config_path, get_config


@pytest.fixture(autouse=True)
def _own_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config.toml is written here; keep it away from every other test's config."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("AIRSDK_CLOUD_API_KEY", raising=False)
    monkeypatch.delenv("AIRSDK_CLOUD_URL", raising=False)
    monkeypatch.delenv("AIRSDK_CONSOLE_URL", raising=False)

EXCHANGE = {
    "session_token": "s", "workspace": {"workspace_id": "ws_abc", "name": "kev's workspace", "owner_email": "kev@x.io", "created_at": "2026-09-07T00:00:00Z", "tier": "free"},
    "role": "owner", "key_id": "key_ws_abc_owner", "api_key": "air_" + "c" * 32, "created": True, "email": "kev@x.io", "sub": "auth0|1",
    "cloud_url": "http://cloud.test", "console_url": "http://console.test/flightdeck",
}


class _Resp(io.BytesIO):
    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_exchange_parses_and_store_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _Resp:
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        return _Resp(json.dumps(EXCHANGE).encode())

    monkeypatch.setattr(cloud_login.urllib.request, "urlopen", fake_urlopen)
    login = cloud_login.exchange_device_token("http://cloud.test/", "tok")
    assert seen == {"url": "http://cloud.test/v1/auth/exchange", "body": {"token": "tok"}}
    assert login.workspace_id == "ws_abc"
    assert login.created is True
    assert login.api_key == "air_" + "c" * 32
    cloud_login.store_cloud_login(login)
    assert get_config("cloud", "workspace_id") == "ws_abc"
    assert get_config("cloud", "api_key") == "air_" + "c" * 32
    assert get_config("cloud", "console_url") == "http://console.test/flightdeck"
    assert oct(_config_path().stat().st_mode & 0o777) == "0o600"
    target = cloud_target.resolve_cloud_target()
    assert target.api_key == "air_" + "c" * 32
    assert target.source == "config"
    assert target.url == "http://cloud.test"


def test_returning_login_keeps_the_saved_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cloud_login.urllib.request, "urlopen", lambda request, timeout: _Resp(json.dumps(EXCHANGE).encode()))
    cloud_login.store_cloud_login(cloud_login.exchange_device_token("http://cloud.test", "tok"))
    returning = {**EXCHANGE, "api_key": None, "created": False}
    monkeypatch.setattr(cloud_login.urllib.request, "urlopen", lambda request, timeout: _Resp(json.dumps(returning).encode()))
    login = cloud_login.exchange_device_token("http://cloud.test", "tok")
    assert login.api_key is None
    cloud_login.store_cloud_login(login)
    assert get_config("cloud", "api_key") == "air_" + "c" * 32


def test_exchange_errors_are_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error

    def boom(request: Any, timeout: float) -> _Resp:
        raise urllib.error.HTTPError(request.full_url, 503, "nope", {}, io.BytesIO(b'{"detail":"sign-in is not configured"}'))  # type: ignore[arg-type]

    monkeypatch.setattr(cloud_login.urllib.request, "urlopen", boom)
    with pytest.raises(cloud_login.CloudLoginError, match="503"):
        cloud_login.exchange_device_token("http://cloud.test", "tok")
    with pytest.raises(cloud_login.CloudLoginError, match="http"):
        cloud_login.exchange_device_token("ftp://cloud.test", "tok")


def test_target_precedence_flag_env_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIRSDK_CLOUD_API_KEY", raising=False)
    monkeypatch.delenv("AIRSDK_CLOUD_URL", raising=False)
    assert cloud_target.resolve_cloud_target().api_key is None
    assert cloud_target.resolve_cloud_target().url == "https://cloud.vindicara.io"
    from projectair.config import set_config

    set_config("cloud", "api_key", "air_config")
    set_config("cloud", "url", "http://from-config/")
    assert cloud_target.resolve_cloud_target().api_key == "air_config"
    assert cloud_target.resolve_cloud_target().url == "http://from-config"
    monkeypatch.setenv("AIRSDK_CLOUD_API_KEY", "air_env")
    assert cloud_target.resolve_cloud_target().api_key == "air_env"
    assert cloud_target.resolve_cloud_target().source == "env"
    assert cloud_target.resolve_cloud_target("air_flag").api_key == "air_flag"


def test_login_command_claims_a_workspace_and_fails_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_flows = types.ModuleType("airsdk.containment.auth0_flows")

    class Device:
        verification_uri = "https://auth/activate"
        user_code = "ABCD"
        device_code = "d"
        interval = 0

    fake_flows.Auth0Tenant = lambda **kw: object()  # type: ignore[attr-defined]
    fake_flows.start_device_flow = lambda tenant: Device()  # type: ignore[attr-defined]
    fake_flows.poll_device_token = lambda tenant, code, interval: "header.payload.sig"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "airsdk.containment.auth0_flows", fake_flows)
    fake_jwt = types.ModuleType("jwt")
    fake_jwt.decode = lambda token, options: {"email": "kev@x.io", "sub": "auth0|1", "exp": 4102444800}  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "jwt", fake_jwt)
    monkeypatch.setattr(cloud_login, "exchange_device_token", lambda url, token: cloud_login.CloudLogin(
        workspace_id="ws_abc", workspace_name="kev's workspace", tier="free", role="owner", created=True,
        api_key="air_" + "d" * 32, cloud_url="http://cloud.test", console_url="http://console.test/flightdeck", email="kev@x.io",
    ))
    result = CliRunner().invoke(app, ["login"])
    assert result.exit_code == 0, result.output
    assert "Created: kev's workspace (ws_abc), free tier, role owner" in result.output
    assert "export AIRSDK_CLOUD_API_KEY=air_" in result.output
    assert get_config("cloud", "api_key") == "air_" + "d" * 32
    who = CliRunner().invoke(app, ["whoami"])
    assert "workspace: kev's workspace (ws_abc)" in who.output

    def refuse(url: str, token: str) -> cloud_login.CloudLogin:
        raise cloud_login.CloudLoginError("AIR Cloud answered 401: token verification failed")

    monkeypatch.setattr(cloud_login, "exchange_device_token", refuse)
    result = CliRunner().invoke(app, ["login"])
    assert result.exit_code == 1
    assert "No workspace was issued" in result.output
    assert "https://api.vindicara.io" in result.output
