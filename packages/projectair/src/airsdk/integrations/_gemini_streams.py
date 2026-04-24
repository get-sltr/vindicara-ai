"""Sync and async stream proxies used by ``airsdk.integrations.gemini``.

Extracted from ``gemini.py`` to keep that module under the project's 300-line
ceiling. Not part of the public surface; import directly from
``airsdk.integrations.gemini`` instead.
"""
from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Iterator
from typing import Any

from airsdk.recorder import AIRRecorder


def chunk_delta(chunk: Any) -> str:
    """Pull the per-chunk text delta from a streaming ``GenerateContentResponse``.

    Gemini stream chunks contain only the new parts for that chunk, so
    ``chunk.text`` is a delta and is safe to concatenate across chunks.
    """
    text = getattr(chunk, "text", None)
    return str(text) if text else ""


async def resolve_async_stream(maybe_coro: Any) -> AsyncIterator[Any]:
    """Resolve the two ``aio`` streaming call styles into an async iterator.

    ``client.aio.models.generate_content_stream`` returns a coroutine that
    resolves to an async iterator. Older or alternate forms return an async
    iterator directly. Handle both by awaiting only when the call returned a
    coroutine.
    """
    if inspect.iscoroutine(maybe_coro):
        return await maybe_coro  # type: ignore[no-any-return]
    return maybe_coro  # type: ignore[no-any-return]


class SyncStreamProxy:
    """Wrap a sync stream, accumulate per-chunk text deltas, emit ``llm_end`` on exhaust."""

    def __init__(self, stream: Iterator[Any], recorder: AIRRecorder) -> None:
        self._stream = stream
        self._recorder = recorder
        self._chunks: list[str] = []
        self._emitted = False

    def __iter__(self) -> SyncStreamProxy:
        return self

    def __next__(self) -> Any:
        try:
            chunk = next(self._stream)
        except StopIteration:
            self._flush()
            raise
        delta = chunk_delta(chunk)
        if delta:
            self._chunks.append(delta)
        return chunk

    def _flush(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        self._recorder.llm_end(response="".join(self._chunks))

    def close(self) -> None:
        """Best-effort stream close; flushes ``llm_end`` if the stream was not fully iterated."""
        closer = getattr(self._stream, "close", None)
        if callable(closer):
            closer()
        self._flush()


class AsyncStreamProxy:
    """Wrap an async stream, accumulate per-chunk text deltas, emit ``llm_end`` on exhaust."""

    def __init__(self, stream: AsyncIterator[Any], recorder: AIRRecorder) -> None:
        self._stream = stream
        self._recorder = recorder
        self._chunks: list[str] = []
        self._emitted = False

    def __aiter__(self) -> AsyncStreamProxy:
        return self

    async def __anext__(self) -> Any:
        try:
            chunk = await self._stream.__anext__()
        except StopAsyncIteration:
            self._flush()
            raise
        delta = chunk_delta(chunk)
        if delta:
            self._chunks.append(delta)
        return chunk

    def _flush(self) -> None:
        if self._emitted:
            return
        self._emitted = True
        self._recorder.llm_end(response="".join(self._chunks))

    async def aclose(self) -> None:
        """Close the underlying stream and flush ``llm_end`` if not fully iterated."""
        closer = getattr(self._stream, "aclose", None)
        if callable(closer):
            result = closer()
            if inspect.isawaitable(result):
                await result
        self._flush()
