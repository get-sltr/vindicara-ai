"""Tests for the Google ADK callback instrumentation.

Mocks the ADK shapes entirely; these tests never require ``google-adk`` to be
installed.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from airsdk.agdr import load_chain, verify_chain
from airsdk.integrations.adk import instrument_adk, make_air_callbacks
from airsdk.recorder import AIRRecorder
from airsdk.types import StepKind, VerificationStatus


def _content(role: str, *part_blocks: Any) -> SimpleNamespace:
    return SimpleNamespace(role=role, parts=list(part_blocks))


def _text_part(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, function_call=None, function_response=None)


def _function_call_part(name: str, args: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(text=None, function_call=SimpleNamespace(name=name, args=args), function_response=None)


def _llm_request(system: str | None, *contents: Any) -> SimpleNamespace:
    config = SimpleNamespace(system_instruction=system)
    return SimpleNamespace(config=config, contents=list(contents))


def _llm_response(*part_blocks: Any) -> SimpleNamespace:
    return SimpleNamespace(content=SimpleNamespace(parts=list(part_blocks)))


def _agent_stub() -> SimpleNamespace:
    return SimpleNamespace(
        before_model_callback=None,
        after_model_callback=None,
        before_tool_callback=None,
        after_tool_callback=None,
    )


def test_make_air_callbacks_returns_four_keys(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    assert set(cbs.keys()) == {
        "before_model_callback",
        "after_model_callback",
        "before_tool_callback",
        "after_tool_callback",
    }


def test_before_model_records_full_history_with_system(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    request = SimpleNamespace(
        config=SimpleNamespace(system_instruction="You are helpful."),
        contents=[
            _content("user", _text_part("Hi.")),
            _content("model", _text_part("Hello!")),
            _content("user", _text_part("Tell me about acme.")),
        ],
    )

    asyncio.run(cbs["before_model_callback"](SimpleNamespace(), request))

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START]
    prompt = records[0].payload.prompt or ""
    assert "system: You are helpful." in prompt
    assert "user: Hi." in prompt
    assert "model: Hello!" in prompt
    assert "user: Tell me about acme." in prompt


def test_after_model_records_text_response(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)

    asyncio.run(
        cbs["after_model_callback"](SimpleNamespace(), _llm_response(_text_part("the answer is 42")))
    )

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_END]
    assert records[0].payload.response == "the answer is 42"


def test_after_model_captures_function_call_part(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    response = _llm_response(
        _text_part("calling tool"),
        _function_call_part("crm_read", {"account": "acme"}),
    )

    asyncio.run(cbs["after_model_callback"](SimpleNamespace(), response))

    records = load_chain(tmp_path / "r.log")
    text = records[0].payload.response or ""
    assert "calling tool" in text
    assert "[function_call crm_read({'account': 'acme'})]" in text


def test_before_tool_records_tool_start(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    tool = SimpleNamespace(name="crm_read")

    asyncio.run(cbs["before_tool_callback"](tool, {"account": "acme"}, SimpleNamespace()))

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.TOOL_START]
    assert records[0].payload.tool_name == "crm_read"
    assert records[0].payload.tool_args == {"account": "acme"}


def test_after_tool_records_dict_output(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    tool = SimpleNamespace(name="crm_read")

    asyncio.run(
        cbs["after_tool_callback"](tool, {"account": "acme"}, SimpleNamespace(), {"status": "ok", "rows": 1})
    )

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.TOOL_END]
    assert "status" in (records[0].payload.tool_output or "")


def test_after_tool_handles_string_output(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    tool = SimpleNamespace(name="echo")

    asyncio.run(cbs["after_tool_callback"](tool, {}, SimpleNamespace(), "raw string output"))

    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.tool_output == "raw string output"


def test_full_round_trip_chain_verifies(tmp_path: Path) -> None:
    """Drive the full sequence (before_model → after_model → before_tool → after_tool)
    and confirm the chain verifies end to end."""
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)

    request = _llm_request("You are a helper.", _content("user", _text_part("look up acme")))
    response = _llm_response(_function_call_part("crm_read", {"account": "acme"}))
    tool = SimpleNamespace(name="crm_read")

    async def _drive() -> None:
        await cbs["before_model_callback"](SimpleNamespace(), request)
        await cbs["after_model_callback"](SimpleNamespace(), response)
        await cbs["before_tool_callback"](tool, {"account": "acme"}, SimpleNamespace())
        await cbs["after_tool_callback"](tool, {"account": "acme"}, SimpleNamespace(), {"rows": 1})

    asyncio.run(_drive())

    records = load_chain(tmp_path / "r.log")
    kinds = [r.kind for r in records]
    assert kinds == [StepKind.LLM_START, StepKind.LLM_END, StepKind.TOOL_START, StepKind.TOOL_END]
    assert verify_chain(records).status == VerificationStatus.OK


def test_instrument_adk_attaches_all_four_callbacks(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    agent = _agent_stub()

    returned = instrument_adk(agent, recorder)
    assert returned is agent

    assert callable(agent.before_model_callback)
    assert callable(agent.after_model_callback)
    assert callable(agent.before_tool_callback)
    assert callable(agent.after_tool_callback)


def test_instrument_adk_chains_existing_callback(tmp_path: Path) -> None:
    """If the user has set a callback, AIR records first then the user's runs."""
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    user_calls: list[Any] = []

    async def _user_after_model(callback_context: Any, llm_response: Any) -> Any:
        user_calls.append(("after_model", llm_response))
        return None

    agent = _agent_stub()
    agent.after_model_callback = _user_after_model
    instrument_adk(agent, recorder)

    response = _llm_response(_text_part("hi"))
    asyncio.run(agent.after_model_callback(SimpleNamespace(), response))

    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.response == "hi"
    assert len(user_calls) == 1
    assert user_calls[0][0] == "after_model"


def test_instrument_adk_chains_existing_sync_callback(tmp_path: Path) -> None:
    """Chained user callbacks may be sync; AIR's wrapper handles both shapes."""
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    user_calls: list[str] = []

    def _user_before_model(callback_context: Any, llm_request: Any) -> Any:
        user_calls.append("called")
        return None

    agent = _agent_stub()
    agent.before_model_callback = _user_before_model
    instrument_adk(agent, recorder)

    request = _llm_request("sys", _content("user", _text_part("hi")))
    asyncio.run(agent.before_model_callback(SimpleNamespace(), request))

    assert user_calls == ["called"]
    records = load_chain(tmp_path / "r.log")
    assert records[0].kind == StepKind.LLM_START


def test_instrument_adk_rejects_non_agent(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    with pytest.raises(AttributeError):
        instrument_adk(SimpleNamespace(), recorder)


def test_before_model_handles_request_without_system_instruction(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)
    request = SimpleNamespace(config=None, contents=[_content("user", _text_part("hi"))])

    asyncio.run(cbs["before_model_callback"](SimpleNamespace(), request))

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "user: hi" in prompt
    assert "system:" not in prompt


def test_after_model_handles_empty_content(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    cbs = make_air_callbacks(recorder)

    asyncio.run(cbs["after_model_callback"](SimpleNamespace(), SimpleNamespace(content=None)))

    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.response == ""
