"""Google Gemini SDK instrumentation.

Wraps a ``google.genai.Client`` so that every ``client.models.generate_content``,
``generate_content_stream``, and chat-session message call writes a signed
``llm_start`` + ``llm_end`` AgDR pair through the supplied
:class:`airsdk.recorder.AIRRecorder`.

Scope: sync and async ``generate_content`` / ``generate_content_stream`` on
``client.models`` and ``client.aio.models``; sync and async chat sessions
returned by ``client.chats.create`` / ``client.aio.chats.create``. Function-call
parts in a response are captured into the ``llm_end`` payload. Tool execution
itself happens in your code; emit ``recorder.tool_start`` / ``recorder.tool_end``
yourself around those calls.

Usage:

    from google import genai
    from airsdk.recorder import AIRRecorder
    from airsdk.integrations.gemini import instrument_gemini

    recorder = AIRRecorder(log_path="agent.log", user_intent="...")
    client = instrument_gemini(genai.Client(api_key="..."), recorder)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello.",
    )
"""
from __future__ import annotations

from typing import Any

from airsdk.integrations._gemini_streams import (
    AsyncStreamProxy,
    SyncStreamProxy,
    resolve_async_stream,
)
from airsdk.recorder import AIRRecorder


def _format_contents(contents: Any, system_instruction: str | None = None) -> str:
    """Flatten a Gemini ``contents`` argument into a single prompt string for AgDR storage.

    The SDK accepts strings, lists of strings, ``types.Part`` / ``types.Content``
    objects, or arbitrary iterables of those. Render every shape the same way
    so the ASI01 goal-hijack detector has a stable anchor.
    """
    parts: list[str] = []
    if system_instruction:
        parts.append(f"system: {system_instruction}")
    if isinstance(contents, str):
        parts.append(f"user: {contents}")
        return "\n".join(parts)
    if not isinstance(contents, (list, tuple)):
        contents = [contents]
    for item in contents:
        if isinstance(item, str):
            parts.append(f"user: {item}")
            continue
        role = str(getattr(item, "role", None) or "user")
        item_parts = getattr(item, "parts", None)
        if item_parts is None:
            parts.append(f"{role}: {item}")
            continue
        rendered: list[str] = []
        for block in item_parts:
            text = getattr(block, "text", None)
            if text:
                rendered.append(str(text))
                continue
            function_call = getattr(block, "function_call", None)
            if function_call is not None:
                name = getattr(function_call, "name", "tool")
                args = getattr(function_call, "args", {})
                rendered.append(f"[function_call {name}({args})]")
                continue
            function_response = getattr(block, "function_response", None)
            if function_response is not None:
                name = getattr(function_response, "name", "tool")
                rendered.append(f"[function_response {name}]")
                continue
            rendered.append(f"[{type(block).__name__} block]")
        parts.append(f"{role}: " + "\n".join(rendered))
    return "\n".join(parts)


def _extract_response_text(response: Any) -> str:
    """Stringify a ``GenerateContentResponse``, capturing text + function_call parts."""
    pieces: list[str] = []
    text = getattr(response, "text", None)
    if text:
        pieces.append(str(text))
    function_calls = getattr(response, "function_calls", None) or []
    for call in function_calls:
        name = getattr(call, "name", "tool")
        args = getattr(call, "args", {})
        pieces.append(f"[function_call {name}({args})]")
    return "\n".join(pieces)


def _system_instruction(config: Any) -> str | None:
    if config is None:
        return None
    text = getattr(config, "system_instruction", None)
    return str(text) if text else None


class _ModelsProxy:
    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    def generate_content(self, *, contents: Any, **kwargs: Any) -> Any:
        prompt = _format_contents(contents, _system_instruction(kwargs.get("config")))
        self._recorder.llm_start(prompt=prompt)
        response = self._wrapped.generate_content(contents=contents, **kwargs)
        self._recorder.llm_end(response=_extract_response_text(response))
        return response

    def generate_content_stream(self, *, contents: Any, **kwargs: Any) -> SyncStreamProxy:
        prompt = _format_contents(contents, _system_instruction(kwargs.get("config")))
        self._recorder.llm_start(prompt=prompt)
        stream = self._wrapped.generate_content_stream(contents=contents, **kwargs)
        return SyncStreamProxy(iter(stream), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _AsyncModelsProxy:
    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    async def generate_content(self, *, contents: Any, **kwargs: Any) -> Any:
        prompt = _format_contents(contents, _system_instruction(kwargs.get("config")))
        self._recorder.llm_start(prompt=prompt)
        response = await self._wrapped.generate_content(contents=contents, **kwargs)
        self._recorder.llm_end(response=_extract_response_text(response))
        return response

    async def generate_content_stream(self, *, contents: Any, **kwargs: Any) -> AsyncStreamProxy:
        prompt = _format_contents(contents, _system_instruction(kwargs.get("config")))
        self._recorder.llm_start(prompt=prompt)
        stream = await resolve_async_stream(self._wrapped.generate_content_stream(contents=contents, **kwargs))
        return AsyncStreamProxy(stream, self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _ChatProxy:
    """Wrap a sync ``Chat`` session so each message exchange emits AgDR records."""

    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    def send_message(self, message: Any, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=_format_contents(message))
        response = self._wrapped.send_message(message, **kwargs)
        self._recorder.llm_end(response=_extract_response_text(response))
        return response

    def send_message_stream(self, message: Any, **kwargs: Any) -> SyncStreamProxy:
        self._recorder.llm_start(prompt=_format_contents(message))
        stream = self._wrapped.send_message_stream(message, **kwargs)
        return SyncStreamProxy(iter(stream), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _AsyncChatProxy:
    """Wrap an async ``Chat`` session so each message exchange emits AgDR records."""

    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    async def send_message(self, message: Any, **kwargs: Any) -> Any:
        self._recorder.llm_start(prompt=_format_contents(message))
        response = await self._wrapped.send_message(message, **kwargs)
        self._recorder.llm_end(response=_extract_response_text(response))
        return response

    async def send_message_stream(self, message: Any, **kwargs: Any) -> AsyncStreamProxy:
        self._recorder.llm_start(prompt=_format_contents(message))
        stream = await resolve_async_stream(self._wrapped.send_message_stream(message, **kwargs))
        return AsyncStreamProxy(stream, self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _ChatsProxy:
    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    def create(self, **kwargs: Any) -> _ChatProxy:
        return _ChatProxy(self._wrapped.create(**kwargs), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _AsyncChatsProxy:
    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self._recorder = recorder

    def create(self, **kwargs: Any) -> _AsyncChatProxy:
        return _AsyncChatProxy(self._wrapped.create(**kwargs), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class _AsyncClientProxy:
    """Wrap ``client.aio`` so its ``models`` and ``chats`` attributes are instrumented."""

    def __init__(self, wrapped: Any, recorder: AIRRecorder) -> None:
        self._wrapped = wrapped
        self.models = _AsyncModelsProxy(wrapped.models, recorder)
        self.chats = _AsyncChatsProxy(wrapped.chats, recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class InstrumentedGeminiClient:
    """Transparent proxy around a ``google.genai.Client`` that instruments LLM calls."""

    def __init__(self, client: Any, recorder: AIRRecorder) -> None:
        self._client = client
        self._recorder = recorder
        self.models = _ModelsProxy(client.models, recorder)
        self.chats = _ChatsProxy(client.chats, recorder)
        self.aio = _AsyncClientProxy(client.aio, recorder)

    @property
    def recorder(self) -> AIRRecorder:
        return self._recorder

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def instrument_gemini(client: Any, recorder: AIRRecorder) -> InstrumentedGeminiClient:
    """Return a transparent proxy around a ``google.genai.Client`` that records every call.

    Wraps ``client.models``, ``client.chats``, and ``client.aio`` (which has
    its own ``.models`` and ``.chats``). Anything else (``client.files``,
    ``client.tunings``, ``client.batches``, etc.) falls through unchanged.
    """
    return InstrumentedGeminiClient(client, recorder)
