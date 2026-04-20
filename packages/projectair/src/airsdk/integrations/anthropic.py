"""Anthropic SDK instrumentation.

Wraps an ``anthropic.Anthropic`` client so that every
``client.messages.create(...)`` call writes a signed
``llm_start`` + ``llm_end`` AgDR pair through the supplied
:class:`airsdk.recorder.AIRRecorder`.

Scope: non-streaming and streaming message APIs. Tool-use content
blocks in the response are captured into the llm_end payload; the
wrapper does not auto-emit ``tool_start`` records for them because
the actual tool execution happens in your code. Emit
``recorder.tool_start`` / ``recorder.tool_end`` yourself around
those calls.

Usage:

    from anthropic import Anthropic
    from airsdk.recorder import AIRRecorder
    from airsdk.integrations.anthropic import instrument_anthropic

    recorder = AIRRecorder(log_path="agent.log", user_intent="...")
    client = instrument_anthropic(Anthropic(), recorder)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": "..."}],
    )
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from airsdk.recorder import AIRRecorder


def _format_messages(messages: list[dict[str, Any]], system: str | None = None) -> str:
    """Flatten Anthropic messages (plus optional system prompt) into a prompt string."""
    parts: list[str] = []
    if system:
        parts.append(f"system: {system}")
    for message in messages:
        role = str(message.get("role", "user"))
        content = message.get("content", "")
        if isinstance(content, list):
            rendered: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        rendered.append(str(block.get("text", "")))
                    elif block.get("type") == "tool_use":
                        rendered.append(f"[tool_use {block.get('name', 'tool')}({block.get('input', {})})]")
                    elif block.get("type") == "tool_result":
                        rendered.append(f"[tool_result {block.get('tool_use_id', '')}]")
                    elif block.get("type") == "image":
                        rendered.append("[image block]")
                    else:
                        rendered.append(f"[{block.get('type', 'content')} block]")
                else:
                    rendered.append(str(block))
            content = "\n".join(rendered)
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _extract_response_text(response: Any) -> str:
    """Stringify an Anthropic Message response, capturing text + tool_use blocks."""
    content = getattr(response, "content", None)
    if not content:
        return ""
    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            parts.append(str(getattr(block, "text", "")))
        elif block_type == "tool_use":
            name = getattr(block, "name", "tool")
            tool_input = getattr(block, "input", {})
            parts.append(f"[tool_use {name}({tool_input})]")
        elif block_type is not None:
            parts.append(f"[{block_type} block]")
    return "\n".join(parts)


class _MessageStreamProxy:
    """Wrap a streaming message iterator: accumulate text deltas, emit llm_end on exhaust."""

    def __init__(self, stream: Iterator[Any], recorder: AIRRecorder) -> None:
        self._stream = stream
        self._recorder = recorder
        self._chunks: list[str] = []
        self._emitted = False

    def __iter__(self) -> _MessageStreamProxy:
        return self

    def __next__(self) -> Any:
        try:
            event = next(self._stream)
        except StopIteration:
            self._flush()
            raise
        # Anthropic streams `content_block_delta` events with text deltas.
        event_type = getattr(event, "type", None)
        if event_type == "content_block_delta":
            delta = getattr(event, "delta", None)
            if delta is not None:
                text = getattr(delta, "text", None)
                if text:
                    self._chunks.append(str(text))
        return event

    def _flush(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        self._recorder.llm_end(response="".join(self._chunks))

    def close(self) -> None:
        closer = getattr(self._stream, "close", None)
        if callable(closer):
            closer()
        self._flush()


class _MessagesProxy:
    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    def create(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        **kwargs: Any,
    ) -> Any:
        prompt_text = _format_messages(messages, system=system)
        self._recorder.llm_start(prompt=prompt_text)
        call_kwargs: dict[str, Any] = {"messages": messages, **kwargs}
        if system is not None:
            call_kwargs["system"] = system
        response = self._wrapped.create(**call_kwargs)
        if kwargs.get("stream"):
            return _MessageStreamProxy(iter(response), self._recorder)
        self._recorder.llm_end(response=_extract_response_text(response))
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class InstrumentedAnthropic:
    """Transparent proxy around an Anthropic client that instruments messages.create."""

    def __init__(self, client: Any, recorder: AIRRecorder) -> None:
        self._client = client
        self._recorder = recorder
        self.messages = _MessagesProxy(client.messages, recorder)

    @property
    def recorder(self) -> AIRRecorder:
        return self._recorder

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def instrument_anthropic(client: Any, recorder: AIRRecorder) -> InstrumentedAnthropic:
    """Return a transparent proxy around ``client`` that records message creations.

    Forwards any attribute we don't explicitly proxy back to the underlying client
    (``client.completions`` legacy, ``client.models``, etc. keep working unchanged).
    Only ``client.messages.create`` is wrapped.
    """
    return InstrumentedAnthropic(client, recorder)
