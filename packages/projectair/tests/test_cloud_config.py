"""Zero-config mirroring: env parsing, the kill switch, run ids, run links."""
from __future__ import annotations

from pathlib import Path

from airsdk.agdr import Signer
from airsdk.cloud_config import (
    DEFAULT_CLOUD_URL,
    DEFAULT_CONSOLE_URL,
    CloudConfig,
    cloud_config_from_env,
    genesis_step_id,
    run_url,
)
from airsdk.recorder import AIRRecorder, default_log_path
from airsdk.types import AgDRPayload, StepKind


def test_no_key_means_no_config() -> None:
    assert cloud_config_from_env({}) is None
    assert cloud_config_from_env({"AIRSDK_CLOUD_API_KEY": "   "}) is None


def test_key_alone_uses_hosted_defaults() -> None:
    cfg = cloud_config_from_env({"AIRSDK_CLOUD_API_KEY": "air_x"})
    assert cfg == CloudConfig(api_key="air_x", url=DEFAULT_CLOUD_URL, console_url=DEFAULT_CONSOLE_URL)


def test_urls_are_overridable_and_trailing_slashes_dropped() -> None:
    cfg = cloud_config_from_env({
        "AIRSDK_CLOUD_API_KEY": "air_x", "AIRSDK_CLOUD_URL": "http://127.0.0.1:9477/", "AIRSDK_CONSOLE_URL": "http://c/flightdeck/",
    })
    assert cfg is not None
    assert cfg.url == "http://127.0.0.1:9477"
    assert cfg.console_url == "http://c/flightdeck"


def test_kill_switch_wins_over_a_key() -> None:
    for off in ("off", "0", "false", "NO"):
        assert cloud_config_from_env({"AIRSDK_CLOUD_API_KEY": "air_x", "AIRSDK_CLOUD": off}) is None
    assert cloud_config_from_env({"AIRSDK_CLOUD_API_KEY": "air_x", "AIRSDK_CLOUD": "on"}) is not None


def test_genesis_step_id_and_run_url() -> None:
    signer = Signer.generate()
    first = signer.sign(StepKind.LLM_START, AgDRPayload(prompt="hi"))
    second = signer.sign(StepKind.LLM_END, AgDRPayload(response="yo"))
    assert genesis_step_id([first, second]) == first.step_id
    assert genesis_step_id([second]) == second.step_id
    assert genesis_step_id([]) is None
    assert run_url("http://c/flightdeck/", first.step_id) == f"http://c/flightdeck/runs/{first.step_id}"


def test_recorder_run_id_without_cloud(tmp_path: Path) -> None:
    path = default_log_path()
    assert path.parent == Path(".air")
    assert path.name.startswith("air-trace-")
    recorder = AIRRecorder(log_path=tmp_path / "r.log", live=False)
    assert recorder.cloud is None
    assert recorder.run_id is None
    first = recorder.llm_start(prompt="x")
    assert recorder.run_id == first.step_id
    assert recorder.run_url is None
