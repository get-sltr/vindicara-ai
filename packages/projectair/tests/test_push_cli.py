"""air push: bulk NDJSON per run with the run header, run links printed, single-post fallback."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from airsdk.agdr import Signer
from airsdk.types import AgDRPayload, StepKind
from projectair.cli import app
from projectair.push_cli import split_runs


@pytest.fixture(autouse=True)
def _own_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config.toml is written here; keep it away from every other test's config."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("AIRSDK_CLOUD_API_KEY", raising=False)
    monkeypatch.delenv("AIRSDK_CLOUD_URL", raising=False)
    monkeypatch.delenv("AIRSDK_CONSOLE_URL", raising=False)


def _write_chain(path: Path, runs: int = 2, length: int = 3) -> list[str]:
    genesis_ids: list[str] = []
    with path.open("w", encoding="utf-8") as fh:
        for _ in range(runs):
            signer = Signer.generate()
            for i in range(length):
                record = signer.sign(StepKind.LLM_START if i % 2 == 0 else StepKind.LLM_END, AgDRPayload(prompt=f"p{i}"))
                if i == 0:
                    genesis_ids.append(record.step_id)
                fh.write(record.model_dump_json(exclude_none=True) + "\n")
    return genesis_ids


def _mock_transport(calls: list[dict[str, Any]], *, bulk_status: int = 200) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append({"path": request.url.path, "run_id": request.headers.get("X-AIR-Run-Id"), "key": request.headers.get("X-API-Key"), "lines": len(request.content.decode().splitlines())})
        if request.url.path.endswith("/bulk"):
            return httpx.Response(bulk_status, json={"workspace_id": "ws", "stored": 3, "run_ids": ["x"]})
        return httpx.Response(201, json={"step_id": "x", "stored": True, "workspace_id": "ws", "run_id": "x"})

    return httpx.MockTransport(handler)


@pytest.fixture
def patched_client(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    state = {"bulk_status": 200}
    original = httpx.Client

    def client(*args: Any, **kwargs: Any) -> httpx.Client:
        kwargs["transport"] = _mock_transport(calls, bulk_status=state["bulk_status"])
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", client)
    calls.append({"_state": state})  # type: ignore[dict-item]
    return calls


def test_split_runs_starts_a_run_at_every_genesis(tmp_path: Path) -> None:
    from airsdk.agdr import load_chain

    _write_chain(tmp_path / "c.jsonl", runs=2, length=3)
    runs = split_runs(load_chain(tmp_path / "c.jsonl"))
    assert [len(r) for r in runs] == [3, 3]


def test_push_sends_one_bulk_per_run_and_prints_links(tmp_path: Path, patched_client: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIRSDK_CLOUD_API_KEY", "air_env")
    monkeypatch.setenv("AIRSDK_CLOUD_URL", "http://cloud.test")
    monkeypatch.setenv("AIRSDK_CONSOLE_URL", "http://console.test/flightdeck")
    genesis = _write_chain(tmp_path / "c.jsonl", runs=2, length=3)
    result = CliRunner().invoke(app, ["push", str(tmp_path / "c.jsonl")])
    assert result.exit_code == 0, result.output
    calls = [c for c in patched_client if "_state" not in c]
    assert [c["path"] for c in calls] == ["/v1/capsules/bulk", "/v1/capsules/bulk"]
    assert [c["run_id"] for c in calls] == genesis
    assert all(c["key"] == "air_env" and c["lines"] == 3 for c in calls)
    for run_id in genesis:
        assert f"http://console.test/flightdeck/runs/{run_id}" in result.output
    assert "Pushed 6/6 records." in result.output


def test_push_falls_back_to_single_posts_on_404(tmp_path: Path, patched_client: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIRSDK_CLOUD_API_KEY", "air_env")
    patched_client[0]["_state"]["bulk_status"] = 404
    _write_chain(tmp_path / "c.jsonl", runs=1, length=3)
    result = CliRunner().invoke(app, ["push", str(tmp_path / "c.jsonl")])
    assert result.exit_code == 0, result.output
    calls = [c for c in patched_client if "_state" not in c]
    assert [c["path"] for c in calls] == ["/v1/capsules/bulk", "/v1/capsules", "/v1/capsules", "/v1/capsules"]


def test_push_without_any_key_explains_air_login(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIRSDK_CLOUD_API_KEY", raising=False)
    _write_chain(tmp_path / "c.jsonl", runs=1, length=1)
    result = CliRunner().invoke(app, ["push", str(tmp_path / "c.jsonl")])
    assert result.exit_code == 2
    assert "air login" in result.output
