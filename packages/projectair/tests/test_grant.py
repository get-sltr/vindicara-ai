"""``air grant``: the console's answer is installed verbatim, and a free grant unlocks nothing."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from projectair import grant_cli
from projectair.cli import app

TOKEN = {"v": 1, "email": "owner@acme.io", "tier": "pro", "issued_at": 1, "expires_at": 2, "features": ["anchor"], "signature": "00"}


def _grant(tier: str = "pro", features: list[str] | None = None) -> grant_cli.GrantPayload:
    return grant_cli.GrantPayload(
        workspace_id="ws_t", tier=tier, email="owner@acme.io", expires_at=2,
        features=features if features is not None else ["anchor"], token={**TOKEN, "tier": tier},
    )


def _fake_pro(monkeypatch: pytest.MonkeyPatch, installed: list[str]) -> None:
    fake_pro = types.ModuleType("airsdk_pro")
    fake_license = types.ModuleType("airsdk_pro.license")

    class _Installed:
        days_remaining = 30

    class LicenseError(Exception):
        pass

    def install_license(text: str) -> _Installed:
        if "REFUSE" in text:
            raise LicenseError("license signature does not verify against vendor public key")
        installed.append(text)
        return _Installed()

    fake_license.install_license = install_license  # type: ignore[attr-defined]
    fake_license.LicenseError = LicenseError  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "airsdk_pro", fake_pro)
    monkeypatch.setitem(sys.modules, "airsdk_pro.license", fake_license)


def test_grant_requires_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIRSDK_CLOUD_API_KEY", raising=False)
    result = CliRunner().invoke(app, ["grant"])
    assert result.exit_code == 2
    assert "AIRSDK_CLOUD_API_KEY" in result.output


def test_grant_installs_the_console_token_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    installed: list[str] = []
    _fake_pro(monkeypatch, installed)
    seen: dict[str, str] = {}

    def fetch(base_url: str, api_key: str) -> grant_cli.GrantPayload:
        seen.update(base_url=base_url, api_key=api_key)
        return _grant()

    monkeypatch.setattr(grant_cli, "fetch_grant", fetch)
    result = CliRunner().invoke(app, ["grant", "--api-key", "air_x", "--url", "https://cloud.example/"])
    assert result.exit_code == 0, result.output
    assert seen == {"base_url": "https://cloud.example", "api_key": "air_x"}
    assert json.loads(installed[0]) == {**TOKEN, "tier": "pro"}
    assert "pro tier" in result.output
    assert "30 day(s) remaining" in result.output


def test_free_grant_without_pro_installed_says_nothing_to_install(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "airsdk_pro", None)  # type: ignore[arg-type]
    monkeypatch.setattr(grant_cli, "fetch_grant", lambda base_url, api_key: _grant("free", []))
    result = CliRunner().invoke(app, ["grant", "--api-key", "air_x"])
    assert result.exit_code == 0, result.output
    assert "(none: free tier)" in result.output
    assert "Nothing to install" in result.output


def test_paid_grant_without_pro_installed_points_at_the_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "airsdk_pro", None)  # type: ignore[arg-type]
    monkeypatch.setattr(grant_cli, "fetch_grant", lambda base_url, api_key: _grant("team"))
    result = CliRunner().invoke(app, ["grant", "--api-key", "air_x"])
    assert result.exit_code == 0, result.output
    assert "pip install projectair-pro" in result.output


def test_console_errors_are_reported_and_exit_1(monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(base_url: str, api_key: str) -> grant_cli.GrantPayload:
        raise grant_cli.GrantError("console answered 401: invalid or revoked api key")

    monkeypatch.setattr(grant_cli, "fetch_grant", fetch)
    result = CliRunner().invoke(app, ["grant", "--api-key", "air_x"])
    assert result.exit_code == 1
    assert "console answered 401" in result.output


def test_fetch_grant_rejects_non_http_urls() -> None:
    with pytest.raises(grant_cli.GrantError, match="must be http"):
        grant_cli.fetch_grant("file:///etc/passwd", "air_x")


def test_fetch_grant_parses_the_console_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"workspace_id": "ws_t", "tier": "pro", "email": "o@a.io", "expires_at": 2, "features": ["anchor"], "token": TOKEN}).encode()

    monkeypatch.setattr(grant_cli.urllib.request, "urlopen", lambda request, timeout: _Resp())
    grant = grant_cli.fetch_grant("https://cloud.example", "air_x")
    assert grant["tier"] == "pro"
    assert grant["token"] == TOKEN


def test_license_gate_uses_paid_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pro = types.ModuleType("airsdk_pro")
    fake_license = types.ModuleType("airsdk_pro.license")
    fake_license.is_pro_active = lambda: False  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "airsdk_pro", fake_pro)
    monkeypatch.setitem(sys.modules, "airsdk_pro.license", fake_license)
    from airsdk._concrete_demo import build_concrete_demo_log

    log = tmp_path / "demo.jsonl"
    build_concrete_demo_log(log)
    result = CliRunner().invoke(app, ["incident", str(log), "-o", str(tmp_path / "pack.md")])
    assert result.exit_code == 2
    assert "air grant" in result.output


def test_a_token_the_local_verifier_refuses_is_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    installed: list[str] = []
    _fake_pro(monkeypatch, installed)
    bad = _grant()
    bad["token"] = {**TOKEN, "signature": "REFUSE"}
    monkeypatch.setattr(grant_cli, "fetch_grant", lambda base_url, api_key: bad)
    result = CliRunner().invoke(app, ["grant", "--api-key", "air_x"])
    assert result.exit_code == 1
    assert "refused by the local verifier" in result.output
    assert installed == []
