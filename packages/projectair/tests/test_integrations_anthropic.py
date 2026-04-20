"""Tests for the Anthropic SDK instrumentation wrapper.

Mocks the Anthropic client entirely; these tests never hit the Anthropic API.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from airsdk.agdr import load_chain, verify_chain
from airsdk.integrations.anthropic import instrument_anthropic
from airsdk.recorder import AIRRecorder
from airsdk.types import StepKind, VerificationStatus


def _fake_response(*blocks: SimpleNamespace) -> SimpleNamespace:
    """Assemble a response shaped like anthropic.Message."""
    return SimpleNamespace(
        id="msg_test",
        role="assistant",
        model="claude-sonnet-4-6",
        content=list(blocks),
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(name: str, tool_input: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id="toolu_1", name=name, input=tool_input)


def _fake_client(response: SimpleNamespace | None = None) -> MagicMock:
    client = MagicMock()
    default = response if response is not None else _fake_response(_text_block("Hi from Claude"))
    client.messages.create = MagicMock(return_value=default)
    return client


def test_instrument_emits_llm_start_and_llm_end(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    client = instrument_anthropic(_fake_client(_fake_response(_text_block("Hi from Claude"))), recorder)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.content[0].text == "Hi from Claude"
    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert "user: hello" in (records[0].payload.prompt or "")
    assert records[1].payload.response == "Hi from Claude"
    assert verify_chain(records).status == VerificationStatus.OK


def test_instrument_threads_system_prompt(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    client = instrument_anthropic(fake, recorder)

    client.messages.create(
        model="claude-sonnet-4-6",
        system="You are a helpful assistant.",
        max_tokens=128,
        messages=[{"role": "user", "content": "hi"}],
    )

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "system: You are a helpful assistant." in prompt
    # System was passed through to the underlying create call.
    fake.messages.create.assert_called_once()
    assert fake.messages.create.call_args.kwargs["system"] == "You are a helpful assistant."


def test_instrument_captures_tool_use_blocks(tmp_path: Path) -> None:
    response = _fake_response(
        _text_block("I'll look it up."),
        _tool_use_block("crm_read", {"account": "acme"}),
    )
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    client = instrument_anthropic(_fake_client(response), recorder)

    client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[{"role": "user", "content": "look up acme"}],
    )

    records = load_chain(tmp_path / "r.log")
    llm_end = records[1]
    response_text = llm_end.payload.response or ""
    assert "I'll look it up." in response_text
    assert "[tool_use crm_read" in response_text


def test_instrument_handles_multimodal_content(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    client = instrument_anthropic(_fake_client(), recorder)

    client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image", "source": {"type": "base64", "data": "..."}},
                ],
            }
        ],
    )

    records = load_chain(tmp_path / "r.log")
    prompt = records[0].payload.prompt or ""
    assert "What's in this image?" in prompt
    assert "[image block]" in prompt


def test_instrument_supports_streaming(tmp_path: Path) -> None:
    def _delta_event(text: str) -> SimpleNamespace:
        return SimpleNamespace(type="content_block_delta", delta=SimpleNamespace(text=text))

    events = [
        SimpleNamespace(type="message_start"),
        _delta_event("Hel"),
        _delta_event("lo, "),
        _delta_event("Claude!"),
        SimpleNamespace(type="message_stop"),
    ]

    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.messages.create.return_value = iter(events)
    client = instrument_anthropic(fake, recorder)

    stream = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[{"role": "user", "content": "stream me"}],
        stream=True,
    )
    collected = list(stream)
    assert len(collected) == len(events)

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert records[1].payload.response == "Hello, Claude!"


def test_instrument_passes_through_other_attributes(tmp_path: Path) -> None:
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    fake = _fake_client()
    fake.models.list = MagicMock(return_value=["claude-sonnet-4-6", "claude-opus-4-7"])
    client = instrument_anthropic(fake, recorder)

    # Not instrumented; forwards to underlying client.
    result = client.models.list()
    assert result == ["claude-sonnet-4-6", "claude-opus-4-7"]
    # No records written since we didn't call messages.create.
    assert not (tmp_path / "r.log").exists() or not (tmp_path / "r.log").read_text()
