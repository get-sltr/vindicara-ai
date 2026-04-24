"""LlamaIndex LLM instrumentation.

Wraps a LlamaIndex LLM (any subclass of ``llama_index.core.llms.LLM``) so that
every ``llm.complete(...)``, ``llm.chat(...)`` call, plus their sync / async
streaming variants, writes a signed ``llm_start`` + ``llm_end`` AgDR pair
through the supplied :class:`airsdk.recorder.AIRRecorder`.

Scope: ``complete`` / ``acomplete`` / ``stream_complete`` / ``astream_complete``
and ``chat`` / ``achat`` / ``stream_chat`` / ``astream_chat``. Tool-call content
emitted as part of a chat response is captured into the ``llm_end`` payload;
the wrapper does not auto-emit ``tool_start`` records because the actual tool
invocation happens inside the agent loop, not inside the LLM call. Emit
``recorder.tool_start`` / ``recorder.tool_end`` yourself around those calls,
or register an AIR-aware LlamaIndex callback.

Usage:

    from llama_index.llms.openai import OpenAI
    from airsdk.recorder import AIRRecorder
    from airsdk.integrations.llamaindex import instrument_llamaindex

    recorder = AIRRecorder(log_path="agent.log", user_intent="...")
    llm = instrument_llamaindex(OpenAI(model="gpt-4o"), recorder)

    response = llm.complete("Hello, world.")
"""
from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Iterator
from typing import Any

from airsdk.recorder import AIRRecorder


async def _resolve_async_stream(maybe_coro: Any) -> AsyncIterator[Any]:
    """Resolve the two LlamaIndex ``astream_*`` call styles into an async iterator.

    llama-index >= 0.10 returns a coroutine that resolves to an async generator
    (so callers must ``await``). Older releases had methods that were themselves
    async generators, which do not need awaiting. Handle both by awaiting only
    when the underlying call returned a coroutine.
    """
    if inspect.iscoroutine(maybe_coro):
        return await maybe_coro  # type: ignore[no-any-return]
    return maybe_coro  # type: ignore[no-any-return]


def _format_chat_messages(messages: Any) -> str:
    """Flatten LlamaIndex ``ChatMessage`` objects (or dicts) into a prompt string."""
    parts: list[str] = []
    for message in messages:
        if isinstance(message, dict):
            role = str(message.get("role", "user"))
            content = message.get("content", "")
        else:
            role_attr = getattr(message, "role", None)
            role = str(getattr(role_attr, "value", role_attr) or "user")
            content = getattr(message, "content", None)
        if content is None:
            content = ""
        if isinstance(content, list):
            rendered: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type") or block.get("block_type")
                    if block_type == "text":
                        rendered.append(str(block.get("text", "")))
                    elif block_type in {"image", "image_url"}:
                        rendered.append(f"[{block_type} block]")
                    else:
                        rendered.append(f"[{block_type or 'content'} block]")
                else:
                    text = getattr(block, "text", None)
                    if text is not None:
                        rendered.append(str(text))
                    else:
                        kind = getattr(block, "block_type", None) or type(block).__name__
                        rendered.append(f"[{kind} block]")
            content = "\n".join(rendered)
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _extract_completion_text(response: Any) -> str:
    """Pull text from a LlamaIndex ``CompletionResponse`` (or anything with ``.text``)."""
    text = getattr(response, "text", None)
    if text is not None:
        return str(text)
    return str(response) if response is not None else ""


def _extract_chat_text(response: Any) -> str:
    """Stringify a LlamaIndex ``ChatResponse``, tool calls included."""
    message = getattr(response, "message", None)
    if message is None:
        return ""
    content = getattr(message, "content", None) or ""
    extras = getattr(message, "additional_kwargs", None) or {}
    tool_calls = extras.get("tool_calls") if isinstance(extras, dict) else None
    if not tool_calls:
        return str(content)
    summaries: list[str] = []
    for call in tool_calls:
        if isinstance(call, dict):
            function = call.get("function") or {}
            name = function.get("name") if isinstance(function, dict) else None
            args = function.get("arguments") if isinstance(function, dict) else None
            name = name or call.get("name") or "tool"
            args = args if args is not None else call.get("arguments", "")
        else:
            function = getattr(call, "function", None)
            name = getattr(function, "name", None) or getattr(call, "name", "tool")
            args = getattr(function, "arguments", None)
            if args is None:
                args = getattr(call, "arguments", "")
        summaries.append(f"[tool_call {name}({args})]")
    joined = "\n".join(summaries)
    return f"{content}\n{joined}" if content else joined


class _SyncStreamProxy:
    """Wrap a LlamaIndex sync stream, accumulate ``delta`` text, emit ``llm_end`` on exhaust."""

    def __init__(self, stream: Iterator[Any], recorder: AIRRecorder) -> None:
        self._stream = stream
        self._recorder = recorder
        self._chunks: list[str] = []
        self._emitted = False

    def __iter__(self) -> _SyncStreamProxy:
        return self

    def __next__(self) -> Any:
        try:
            chunk = next(self._stream)
        except StopIteration:
            self._flush()
            raise
        self._accumulate(chunk)
        return chunk

    def _accumulate(self, chunk: Any) -> None:
        # LlamaIndex stream chunks always carry the token delta on `.delta`; the
        # `message.content` field is cumulative and must not be summed across chunks.
        delta = getattr(chunk, "delta", None)
        if delta:
            self._chunks.append(str(delta))

    def _flush(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        self._recorder.llm_end(response="".join(self._chunks))

    def close(self) -> None:
        """Best-effort stream close; also flushes ``llm_end`` if the stream was not fully iterated."""
        closer = getattr(self._stream, "close", None)
        if callable(closer):
            closer()
        self._flush()


class _AsyncStreamProxy:
    """Wrap a LlamaIndex async stream, accumulate ``delta`` text, emit ``llm_end`` on exhaust."""

    def __init__(self, stream: AsyncIterator[Any], recorder: AIRRecorder) -> None:
        self._stream = stream
        self._recorder = recorder
        self._chunks: list[str] = []
        self._emitted = False

    def __aiter__(self) -> _AsyncStreamProxy:
        return self

    async def __anext__(self) -> Any:
        try:
            chunk = await self._stream.__anext__()
        except StopAsyncIteration:
            self._flush()
            raise
        self._accumulate(chunk)
        return chunk

    def _accumulate(self, chunk: Any) -> None:
        # LlamaIndex stream chunks always carry the token delta on `.delta`; the
        # `message.content` field is cumulative and must not be summed across chunks.
        delta = getattr(chunk, "delta", None)
        if delta:
            self._chunks.append(str(delta))

    def _flush(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        self._recorder.llm_end(response="".join(self._chunks))

    async def aclose(self) -> None:
        """Close the underlying stream and flush ``llm_end`` if the stream was not fully iterated."""
        closer = getattr(self._stream, "aclose", None)
        if callable(closer):
            result = closer()
            if inspect.isawaitable(result):
                await result
        self._flush()


class InstrumentedLlamaIndexLLM:
    """Transparent proxy around a LlamaIndex LLM that instruments completion + chat methods."""

    def __init__(self, llm: Any, recorder: AIRRecorder) -> None:
        self._llm = llm
        self._recorder = recorder

    @property
    def recorder(self) -> AIRRecorder:
        return self._recorder

    # -- Completion surface ------------------------------------------------

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=str(prompt))
        response = self._llm.complete(prompt, **kwargs)
        self._recorder.llm_end(response=_extract_completion_text(response))
        return response

    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=str(prompt))
        response = await self._llm.acomplete(prompt, **kwargs)
        self._recorder.llm_end(response=_extract_completion_text(response))
        return response

    def stream_complete(self, prompt: str, **kwargs: Any) -> _SyncStreamProxy:
        self._recorder.llm_start(prompt=str(prompt))
        stream = self._llm.stream_complete(prompt, **kwargs)
        return _SyncStreamProxy(iter(stream), self._recorder)

    async def astream_complete(self, prompt: str, **kwargs: Any) -> _AsyncStreamProxy:
        self._recorder.llm_start(prompt=str(prompt))
        stream = await _resolve_async_stream(self._llm.astream_complete(prompt, **kwargs))
        return _AsyncStreamProxy(stream, self._recorder)

    # -- Chat surface ------------------------------------------------------

    def chat(self, messages: Any, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=_format_chat_messages(messages))
        response = self._llm.chat(messages, **kwargs)
        self._recorder.llm_end(response=_extract_chat_text(response))
        return response

    async def achat(self, messages: Any, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=_format_chat_messages(messages))
        response = await self._llm.achat(messages, **kwargs)
        self._recorder.llm_end(response=_extract_chat_text(response))
        return response

    def stream_chat(self, messages: Any, **kwargs: Any) -> _SyncStreamProxy:
        self._recorder.llm_start(prompt=_format_chat_messages(messages))
        stream = self._llm.stream_chat(messages, **kwargs)
        return _SyncStreamProxy(iter(stream), self._recorder)

    async def astream_chat(self, messages: Any, **kwargs: Any) -> _AsyncStreamProxy:
        self._recorder.llm_start(prompt=_format_chat_messages(messages))
        stream = await _resolve_async_stream(self._llm.astream_chat(messages, **kwargs))
        return _AsyncStreamProxy(stream, self._recorder)

    # -- Passthrough -------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # Anything we don't explicitly proxy (metadata, tokenizer, callback_manager,
        # structured output helpers, model-specific extras) falls through unchanged.
        return getattr(self._llm, name)


def instrument_llamaindex(llm: Any, recorder: AIRRecorder) -> InstrumentedLlamaIndexLLM:
    """Return a transparent proxy around a LlamaIndex ``LLM`` that records every call.

    Only the eight standard LLM entry points are wrapped: ``complete`` / ``acomplete`` /
    ``stream_complete`` / ``astream_complete`` and ``chat`` / ``achat`` / ``stream_chat``
    / ``astream_chat``. Every other attribute access (``metadata``, ``callback_manager``,
    ``structured_predict``, etc.) forwards to the underlying LLM so you can drop the
    wrapped object anywhere a plain LlamaIndex LLM is expected, including query engines,
    chat engines, and agents.
    """
    return InstrumentedLlamaIndexLLM(llm, recorder)
