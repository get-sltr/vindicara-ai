"""Tests for the Google Gemini SDK instrumentation wrapper.

Mocks the SDK entirely; these tests never hit Google or require ``google-genai``
to be installed.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from airsdk.agdr import load_chain, verify_chain
from airsdk.integrations.gemini import instrument_gemini
from airsdk.recorder import AIRRecorder
from airsdk.types import StepKind, VerificationStatus


def _response(text: str, function_calls: list[Any] | None = None) -> SimpleNamespace:
    """Shape mirrors google.genai.types.GenerateContentResponse."""
    return SimpleNamespace(text=text, function_calls=function_calls or [])


def _function_call(name: str, args: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(name=name, args=args)


def _content(role: str, *part_blocks: Any) -> SimpleNamespace:
    return SimpleNamespace(role=role, parts=list(part_blocks))


def _text_part(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, function_call=None, function_response=None)


def _fake_client() -> MagicMock:
    client = MagicMock()
    client.models = MagicMock()
    client.models.generate_content = MagicMock(return_value=_response("sync hello"))
    client.chats = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.chats = MagicMock()
    return client


def test_generate_content_emits_llm_start_and_end(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    client = instrument_gemini(fake, recorder)

    response = client.models.generate_content(model="gemini-2.5-flash", contents="Hello?")

    assert response.text == "sync hello"
    fake.models.generate_content.assert_called_once_with(model="gemini-2.5-flash", contents="Hello?")

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[0].payload.prompt == "user: Hello?"
    assert records[1].payload.response == "sync hello"
    assert verify_chain(records).status == VerificationStatus.OK


def test_generate_content_includes_system_instruction(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    client = instrument_gemini(fake, recorder)

    config = SimpleNamespace(system_instruction="You are helpful.")
    client.models.generate_content(model="m", contents="Hi.", config=config)

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "system: You are helpful." in prompt
    assert "user: Hi." in prompt


def test_generate_content_serialises_content_objects(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    client = instrument_gemini(fake, recorder)

    contents = [
        _content("user", _text_part("Look up acme.")),
        _content("model", _text_part(""), SimpleNamespace(text=None, function_call=_function_call("crm_read", {"id": "acme"}), function_response=None)),
    ]
    client.models.generate_content(model="m", contents=contents)

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "user: Look up acme." in prompt
    assert "[function_call crm_read({'id': 'acme'})]" in prompt


def test_generate_content_captures_function_calls_in_response(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.models.generate_content.return_value = _response(
        "let me check",
        function_calls=[_function_call("crm_read", {"account": "acme"})],
    )
    client = instrument_gemini(fake, recorder)

    client.models.generate_content(model="m", contents="ping")

    records = load_chain(tmp_path / "r.log")
    response_text = records[1].payload.response or ""
    assert "let me check" in response_text
    assert "[function_call crm_read({'account': 'acme'})]" in response_text


def test_generate_content_stream_accumulates_deltas(tmp_path: Path) -> None:
    chunks = [_response("Hel"), _response("lo"), _response("!")]
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.models.generate_content_stream = MagicMock(return_value=iter(chunks))
    client = instrument_gemini(fake, recorder)

    stream = client.models.generate_content_stream(model="m", contents="stream please")
    collected = list(stream)
    assert len(collected) == 3

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "Hello!"


def test_generate_content_stream_flushes_on_close(tmp_path: Path) -> None:
    chunks = [_response("a"), _response("b")]
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.models.generate_content_stream = MagicMock(return_value=iter(chunks))
    client = instrument_gemini(fake, recorder)

    stream = client.models.generate_content_stream(model="m", contents="hi")
    next(iter(stream))
    stream.close()

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "a"


def test_async_generate_content_emits_chain(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()

    async def _async_generate_content(*, contents: Any, **_: Any) -> SimpleNamespace:
        return _response("async hello")

    fake.aio.models.generate_content = _async_generate_content
    client = instrument_gemini(fake, recorder)

    response = asyncio.run(client.aio.models.generate_content(model="m", contents="ping"))
    assert response.text == "async hello"

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "async hello"


def test_async_stream_accumulates_deltas(tmp_path: Path) -> None:
    async def _gen() -> Any:
        for piece in ["A", "B", "C"]:
            yield _response(piece)

    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.aio.models.generate_content_stream = MagicMock(return_value=_gen())
    client = instrument_gemini(fake, recorder)

    async def _drive() -> list[Any]:
        stream = await client.aio.models.generate_content_stream(model="m", contents="hi")
        collected: list[Any] = []
        async for chunk in stream:
            collected.append(chunk)
        return collected

    chunks = asyncio.run(_drive())
    assert len(chunks) == 3

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "ABC"


def test_chat_send_message(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    chat_session = MagicMock()
    chat_session.send_message = MagicMock(return_value=_response("chat reply"))
    fake.chats.create = MagicMock(return_value=chat_session)
    client = instrument_gemini(fake, recorder)

    chat = client.chats.create(model="m")
    response = chat.send_message("how are you?")
    assert response.text == "chat reply"

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[0].payload.prompt == "user: how are you?"
    assert records[1].payload.response == "chat reply"


def test_chat_send_message_stream(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    chat_session = MagicMock()
    chat_session.send_message_stream = MagicMock(return_value=iter([_response("st"), _response("ream")]))
    fake.chats.create = MagicMock(return_value=chat_session)
    client = instrument_gemini(fake, recorder)

    chat = client.chats.create(model="m")
    list(chat.send_message_stream("ping"))

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "stream"


def test_async_chat_send_message(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    chat_session = MagicMock()

    async def _async_send(message: Any, **_: Any) -> SimpleNamespace:
        return _response("async chat reply")

    chat_session.send_message = _async_send
    fake.aio.chats.create = MagicMock(return_value=chat_session)
    client = instrument_gemini(fake, recorder)

    async def _drive() -> Any:
        chat = client.aio.chats.create(model="m")
        return await chat.send_message("ping")

    response = asyncio.run(_drive())
    assert response.text == "async chat reply"

    records = load_chain(tmp_path / "r.log")
    assert records[1].payload.response == "async chat reply"


def test_passthrough_unwrapped_attributes(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.files = "sentinel-files"
    client = instrument_gemini(fake, recorder)

    assert client.files == "sentinel-files"
    log = tmp_path / "r.log"
    assert not log.exists() or not log.read_text()


def test_recorder_property_exposes_recorder(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    client = instrument_gemini(_fake_client(), recorder)
    assert client.recorder is recorder


@pytest.mark.parametrize("contents", ["plain", ["a", "b"], "with\nnewlines"])
def test_format_contents_accepts_string_and_list_forms(tmp_path: Path, contents: Any) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    client = instrument_gemini(_fake_client(), recorder)

    client.models.generate_content(model="m", contents=contents)

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    if isinstance(contents, str):
        assert contents in prompt
    else:
        for item in contents:
            assert item in prompt
