"""The LangChain callback can share a recorder, and so reach AIR Cloud."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from airsdk import AIRCallbackHandler
from airsdk.agdr import load_chain
from airsdk.recorder import AIRRecorder
from airsdk.types import AgDRRecord


class _Sink:
    def __init__(self) -> None:
        self.records: list[AgDRRecord] = []

    def emit(self, record: AgDRRecord) -> None:
        self.records.append(record)

    def drain(self, timeout: float) -> None:
        return None


def test_handler_uses_the_given_recorder(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "shared.log", user_intent="summarize", live=False)
    handler = AIRCallbackHandler(recorder=recorder)
    assert handler.recorder is recorder
    handler.on_llm_start({"name": "llm"}, ["hello"], run_id=uuid4())
    records = load_chain(tmp_path / "shared.log")
    assert [r.kind.value for r in records] == ["llm_start"]
    assert records[0].payload.user_intent == "summarize"


def test_handler_passes_transports_to_the_recorder_it_builds(tmp_path: Path) -> None:
    sink = _Sink()
    handler = AIRCallbackHandler(log_path=tmp_path / "h.log", transports=[sink], user_intent="x")
    handler.on_llm_start({"name": "llm"}, ["hello"], run_id=uuid4())
    assert [r.kind.value for r in sink.records] == ["llm_start"]
    assert not (tmp_path / "h.log").exists()


def test_handler_default_path_is_a_fresh_file_under_dot_air(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    handler = AIRCallbackHandler()
    assert handler.log_path.parent == Path(".air")
    assert handler.log_path.name.startswith("air-trace-")
