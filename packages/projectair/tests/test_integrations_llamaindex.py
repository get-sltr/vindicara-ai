"""Tests for the LlamaIndex LLM instrumentation wrapper.

Mocks the LlamaIndex LLM entirely; these tests never hit a real provider or
require llama-index to be installed.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from airsdk.agdr import load_chain, verify_chain
from airsdk.integrations.llamaindex import instrument_llamaindex
from airsdk.recorder import AIRRecorder
from airsdk.types import StepKind, VerificationStatus


def _completion_response(text: str) -> SimpleNamespace:
    """Shape mirrors llama_index.core.base.llms.types.CompletionResponse."""
    return SimpleNamespace(text=text, additional_kwargs={}, raw=None, delta=None)


def _chat_message(role: str, content: str, *, tool_calls: list[Any] | None = None) -> SimpleNamespace:
    additional: dict[str, Any] = {}
    if tool_calls is not None:
        additional["tool_calls"] = tool_calls
    return SimpleNamespace(role=role, content=content, additional_kwargs=additional)


def _chat_response(message: SimpleNamespace) -> SimpleNamespace:
    """Shape mirrors llama_index.core.base.llms.types.ChatResponse."""
    return SimpleNamespace(message=message, raw=None, delta=None)


def _fake_llm() -> MagicMock:
    llm = MagicMock()
    llm.complete = MagicMock(return_value=_completion_response("sync complete"))
    llm.chat = MagicMock(return_value=_chat_response(_chat_message("assistant", "sync chat")))
    return llm


def test_instrument_complete_emits_llm_start_and_end(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    llm = instrument_llamaindex(_fake_llm(), recorder)

    response = llm.complete("Hello?")

    assert response.text == "sync complete"
    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[0].payload.prompt == "Hello?"
    assert records[1].payload.response == "sync complete"
    assert verify_chain(records).status == VerificationStatus.OK


def test_instrument_chat_serialises_chat_messages(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    llm = instrument_llamaindex(fake, recorder)

    messages = [
        _chat_message("system", "You are helpful."),
        _chat_message("user", "Draft the report."),
    ]
    response = llm.chat(messages, temperature=0.2)

    assert response.message.content == "sync chat"
    fake.chat.assert_called_once()
    assert fake.chat.call_args.kwargs["temperature"] == 0.2

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "system: You are helpful." in prompt
    assert "user: Draft the report." in prompt
    assert records[1].payload.response == "sync chat"


def test_instrument_chat_captures_tool_calls(tmp_path: Path) -> None:
    tool_call = {"id": "call_1", "function": {"name": "crm_read", "arguments": '{"account": "acme"}'}}
    message = _chat_message("assistant", "", tool_calls=[tool_call])
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    fake.chat.return_value = _chat_response(message)
    llm = instrument_llamaindex(fake, recorder)

    llm.chat([_chat_message("user", "look up acme")])

    records = load_chain(tmp_path / "r.log")
    response_text = records[1].payload.response or ""
    assert "[tool_call crm_read" in response_text
    assert '"account": "acme"' in response_text


def test_instrument_chat_handles_role_enum(tmp_path: Path) -> None:
    role_enum = SimpleNamespace(value="user")
    user_msg = SimpleNamespace(role=role_enum, content="hi from enum role", additional_kwargs={})
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    llm = instrument_llamaindex(_fake_llm(), recorder)

    llm.chat([user_msg])

    records = load_chain(tmp_path / "r.log")
    assert "user: hi from enum role" in (records[0].payload.prompt or "")


def test_instrument_chat_handles_multimodal_blocks(tmp_path: Path) -> None:
    content_blocks = [
        {"type": "text", "text": "What is this?"},
        {"type": "image_url", "image_url": "https://example.com/x.png"},
    ]
    multimodal = SimpleNamespace(role="user", content=content_blocks, additional_kwargs={})
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    llm = instrument_llamaindex(_fake_llm(), recorder)

    llm.chat([multimodal])

    prompt = load_chain(tmp_path / "r.log")[0].payload.prompt or ""
    assert "What is this?" in prompt
    assert "[image_url block]" in prompt


def test_instrument_stream_complete_accumulates_deltas(tmp_path: Path) -> None:
    chunks = [
        SimpleNamespace(text="Hel", delta="Hel"),
        SimpleNamespace(text="Hello", delta="lo"),
        SimpleNamespace(text="Hello!", delta="!"),
    ]
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    fake.stream_complete = MagicMock(return_value=iter(chunks))
    llm = instrument_llamaindex(fake, recorder)

    stream = llm.stream_complete("stream please")
    collected = list(stream)
    assert len(collected) == 3

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "Hello!"


def test_instrument_stream_chat_accumulates_deltas(tmp_path: Path) -> None:
    # LlamaIndex chat streams carry the token delta on `.delta`; `message.content`
    # is cumulative on every chunk and MUST NOT be summed across chunks.
    chunks = [
        SimpleNamespace(message=_chat_message("assistant", "Hel"), delta="Hel"),
        SimpleNamespace(message=_chat_message("assistant", "Hello"), delta="lo"),
        SimpleNamespace(message=_chat_message("assistant", "Hello world"), delta=" world"),
    ]
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    fake.stream_chat = MagicMock(return_value=iter(chunks))
    llm = instrument_llamaindex(fake, recorder)

    collected = list(llm.stream_chat([_chat_message("user", "stream me")]))
    assert len(collected) == 3

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "Hello world"


def test_instrument_acomplete_emits_chain(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()

    async def _acomplete(prompt: str, **_: Any) -> SimpleNamespace:
        return _completion_response("async complete")

    fake.acomplete = _acomplete
    llm = instrument_llamaindex(fake, recorder)

    response = asyncio.run(llm.acomplete("ping"))
    assert response.text == "async complete"

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "async complete"


def test_instrument_astream_chat_accumulates_deltas(tmp_path: Path) -> None:
    async def _stream() -> Any:
        for piece in ["He", "ll", "o async"]:
            yield SimpleNamespace(message=_chat_message("assistant", piece), delta=piece)

    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()

    async def _astream_chat(messages: Any, **_: Any) -> Any:
        return _stream()

    fake.astream_chat = _astream_chat
    llm = instrument_llamaindex(fake, recorder)

    async def _drive() -> list[Any]:
        stream = await llm.astream_chat([_chat_message("user", "stream me")])
        collected: list[Any] = []
        async for chunk in stream:
            collected.append(chunk)
        return collected

    chunks = asyncio.run(_drive())
    assert len(chunks) == 3

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "Hello async"


def test_instrument_passes_through_other_attributes(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    fake.metadata = SimpleNamespace(model_name="gpt-4o", context_window=128000)
    fake.callback_manager = "sentinel-cb-manager"
    llm = instrument_llamaindex(fake, recorder)

    # Not instrumented; forwards to underlying LLM.
    assert llm.metadata.model_name == "gpt-4o"
    assert llm.metadata.context_window == 128000
    assert llm.callback_manager == "sentinel-cb-manager"

    # No records were written because no instrumented method was called.
    log = tmp_path / "r.log"
    assert not log.exists() or not log.read_text()


def test_instrument_stream_complete_flushes_on_close(tmp_path: Path) -> None:
    chunks = [SimpleNamespace(text="a", delta="a"), SimpleNamespace(text="ab", delta="b")]
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    fake.stream_complete = MagicMock(return_value=iter(chunks))
    llm = instrument_llamaindex(fake, recorder)

    stream = llm.stream_complete("hi")
    # Consume one chunk only, then close.
    next(iter(stream))
    stream.close()

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    # Only the first delta was accumulated before close.
    assert records[1].payload.response == "a"


def test_recorder_property_exposes_recorder(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    llm = instrument_llamaindex(_fake_llm(), recorder)
    assert llm.recorder is recorder


def test_instrument_astream_complete_handles_direct_async_generator(tmp_path: Path) -> None:
    # llama-index < 0.10 style: astream_* returns an async generator directly,
    # so the caller does not `await` it. Our wrapper must still work.
    async def _gen() -> Any:
        for piece in ["A", "B", "C"]:
            yield SimpleNamespace(text=piece, delta=piece)

    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_llm()
    # Non-async callable that returns the async generator directly.
    fake.astream_complete = MagicMock(return_value=_gen())
    llm = instrument_llamaindex(fake, recorder)

    async def _drive() -> list[Any]:
        stream = await llm.astream_complete("ping")
        collected: list[Any] = []
        async for chunk in stream:
            collected.append(chunk)
        return collected

    chunks = asyncio.run(_drive())
    assert len(chunks) == 3

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "ABC"


@pytest.mark.parametrize("prompt_value", ["plain string", "with\nnewlines", ""])
def test_complete_accepts_various_prompt_strings(tmp_path: Path, prompt_value: str) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    llm = instrument_llamaindex(_fake_llm(), recorder)

    llm.complete(prompt_value)

    records = load_chain(tmp_path / "r.log")
    assert records[0].payload.prompt == prompt_value
