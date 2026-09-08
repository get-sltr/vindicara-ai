"""AIRRecorder + resolve_signing_key tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from airsdk.agdr import load_chain, verify_chain
from airsdk.recorder import AIRRecorder, resolve_signing_key
from airsdk.types import StepKind, VerificationStatus


def test_recorder_writes_each_step_kind(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    recorder.llm_start(prompt="hi")
    recorder.llm_end(response="hello")
    recorder.tool_start(tool_name="search", tool_args={"q": "pizza"})
    recorder.tool_end(tool_output="done")
    recorder.agent_finish(final_output="ok")

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [
        StepKind.LLM_START, StepKind.LLM_END, StepKind.TOOL_START, StepKind.TOOL_END, StepKind.AGENT_FINISH,
    ]
    assert verify_chain(records).status == VerificationStatus.OK


def test_recorder_attaches_user_intent(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log", user_intent="Draft a sales report")
    recorder.llm_start(prompt="Start working")
    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.user_intent == "Draft a sales report"


def test_recorder_does_not_overwrite_explicit_user_intent(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log", user_intent="Default intent")
    recorder.llm_start(prompt="x", user_intent="Explicit per-step intent")
    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.user_intent == "Explicit per-step intent"


def test_recorder_creates_parent_directory(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested" / "r.log"
    recorder = AIRRecorder(log_path=nested)
    recorder.llm_start(prompt="hi")
    assert nested.exists()


def test_resolve_signing_key_accepts_hex() -> None:
    hex_seed = "0" * 64
    key = resolve_signing_key(hex_seed)
    assert isinstance(key, Ed25519PrivateKey)


def test_resolve_signing_key_rejects_wrong_length() -> None:
    with pytest.raises(ValueError, match="must decode to 32 bytes"):
        resolve_signing_key("deadbeef")


def test_resolve_signing_key_rejects_non_hex_non_pem() -> None:
    with pytest.raises(ValueError, match="PEM-encoded"):
        resolve_signing_key("this-is-obviously-not-a-key")


def test_resolve_signing_key_passthrough_existing_key() -> None:
    key = Ed25519PrivateKey.generate()
    assert resolve_signing_key(key) is key


def test_resolve_signing_key_none_returns_none() -> None:
    assert resolve_signing_key(None) is None


def test_recorder_mirrors_to_cloud_when_env_key_is_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from airsdk.transport import FileTransport, HTTPTransport

    monkeypatch.setenv("AIRSDK_CLOUD_API_KEY", "air_env")
    monkeypatch.setenv("AIRSDK_CLOUD_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("AIRSDK_CONSOLE_URL", "http://console.test/flightdeck")
    recorder = AIRRecorder(log_path=tmp_path / "r.log", live=False)
    assert [type(t) for t in recorder.transports] == [FileTransport, HTTPTransport]
    assert recorder.cloud is not None
    assert recorder.cloud.api_key == "air_env"
    recorder.llm_start(prompt="x")
    assert recorder.run_url == f"http://console.test/flightdeck/runs/{recorder.run_id}"
    assert (tmp_path / "r.log").exists()
    monkeypatch.setenv("AIRSDK_CLOUD", "off")
    assert [type(t) for t in AIRRecorder(log_path=tmp_path / "s.log", live=False).transports] == [FileTransport]


def test_recorder_default_log_path_lands_under_dot_air(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    recorder = AIRRecorder(live=False)
    recorder.llm_start(prompt="x")
    assert recorder.log_path.parent == Path(".air")
    assert recorder.log_path.exists()
