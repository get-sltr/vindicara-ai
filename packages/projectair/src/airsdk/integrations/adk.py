"""Google ADK (Agent Development Kit) instrumentation.

Wires AIR callbacks into a ``google.adk.agents.LlmAgent`` so that every model
call and every tool execution writes signed AgDR records through the supplied
:class:`airsdk.recorder.AIRRecorder`.

Scope: ``before_model_callback`` and ``after_model_callback`` emit the
``llm_start`` + ``llm_end`` pair, capturing the full message history (with
system instruction) on the request side and text + ``function_call`` parts on
the response side. ``before_tool_callback`` and ``after_tool_callback`` emit
``tool_start`` + ``tool_end``. Callbacks already set on the agent are
preserved: AIR's callback runs first to record, then control falls through to
the user's callback (their return value is honoured).

Usage A (construction-time, recommended):

    from google.adk.agents import LlmAgent
    from airsdk.recorder import AIRRecorder
    from airsdk.integrations.adk import make_air_callbacks

    recorder = AIRRecorder(log_path="agent.log", user_intent="...")
    agent = LlmAgent(
        name="MyAgent",
        model="gemini-2.5-flash",
        instruction="...",
        tools=[...],
        **make_air_callbacks(recorder),
    )

Usage B (post-construction):

    from airsdk.integrations.adk import instrument_adk
    instrument_adk(agent, recorder)
"""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from airsdk.recorder import AIRRecorder

_CALLBACK_FIELDS = (
    "before_model_callback",
    "after_model_callback",
    "before_tool_callback",
    "after_tool_callback",
)


def _format_llm_request(llm_request: Any) -> str:
    """Render the full ADK ``LlmRequest`` (system + every content) into a prompt string.

    Walks ``llm_request.contents`` (every turn, not just the last) and emits
    ``role: text`` lines. Non-text parts are summarised. The system instruction,
    if present on ``llm_request.config``, is rendered as the first line so the
    ASI01 goal-hijack detector keeps its anchor across multi-turn loops.
    """
    parts: list[str] = []
    config = getattr(llm_request, "config", None)
    system_instruction = getattr(config, "system_instruction", None) if config is not None else None
    if system_instruction:
        parts.append(f"system: {system_instruction}")
    contents = getattr(llm_request, "contents", None) or []
    for content in contents:
        role = str(getattr(content, "role", None) or "user")
        content_parts = getattr(content, "parts", None) or []
        rendered: list[str] = []
        for block in content_parts:
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


def _extract_llm_response_text(llm_response: Any) -> str:
    """Stringify an ADK ``LlmResponse``, capturing text + function_call parts.

    The ``LlmResponse.content`` field is a ``types.Content`` with ``.parts``;
    each part can carry text or a function_call. Mirror the Anthropic /
    Gemini wrapper output shape so detector heuristics see consistent traces.
    """
    content = getattr(llm_response, "content", None)
    if content is None:
        return ""
    pieces: list[str] = []
    for block in getattr(content, "parts", None) or []:
        text = getattr(block, "text", None)
        if text:
            pieces.append(str(text))
            continue
        function_call = getattr(block, "function_call", None)
        if function_call is not None:
            name = getattr(function_call, "name", "tool")
            args = getattr(function_call, "args", {})
            pieces.append(f"[function_call {name}({args})]")
    return "\n".join(pieces)


async def _maybe_await(value: Any) -> Any:
    """Await ``value`` if it is awaitable, else return it as-is.

    ADK callbacks may be sync or async; user-supplied chained callbacks may be
    either. ADK awaits callback returns regardless, but when we invoke a
    user callback inside our own callback we have to handle both shapes.
    """
    if inspect.isawaitable(value):
        return await value
    return value


def _chain_before_model(recorder: AIRRecorder, existing: Any) -> Callable[..., Any]:
    async def _air_before_model(callback_context: Any, llm_request: Any) -> Any:
        recorder.llm_start(prompt=_format_llm_request(llm_request))
        if existing is None:
            return None
        return await _maybe_await(existing(callback_context, llm_request))

    return _air_before_model


def _chain_after_model(recorder: AIRRecorder, existing: Any) -> Callable[..., Any]:
    async def _air_after_model(callback_context: Any, llm_response: Any) -> Any:
        recorder.llm_end(response=_extract_llm_response_text(llm_response))
        if existing is None:
            return None
        return await _maybe_await(existing(callback_context, llm_response))

    return _air_after_model


def _chain_before_tool(recorder: AIRRecorder, existing: Any) -> Callable[..., Any]:
    async def _air_before_tool(tool: Any, args: dict[str, Any], tool_context: Any) -> Any:
        tool_name = str(getattr(tool, "name", None) or type(tool).__name__)
        recorder.tool_start(tool_name=tool_name, tool_args=dict(args) if args else {})
        if existing is None:
            return None
        return await _maybe_await(existing(tool, args, tool_context))

    return _air_before_tool


def _chain_after_tool(recorder: AIRRecorder, existing: Any) -> Callable[..., Any]:
    async def _air_after_tool(
        tool: Any,
        args: dict[str, Any],
        tool_context: Any,
        tool_response: Any,
    ) -> Any:
        recorder.tool_end(tool_output=_stringify_tool_output(tool_response))
        if existing is None:
            return None
        return await _maybe_await(existing(tool, args, tool_context, tool_response))

    return _air_after_tool


def _stringify_tool_output(tool_response: Any) -> str:
    """Render an ADK tool return value as a string for AgDR storage.

    ADK tool callbacks declare ``tool_response`` as ``dict``, but in practice
    framework code passes through whatever the tool returned (dicts, strings,
    Pydantic models). Cover all three.
    """
    if tool_response is None:
        return ""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        return str(tool_response)
    dumper = getattr(tool_response, "model_dump_json", None)
    if callable(dumper):
        return str(dumper())
    return str(tool_response)


def make_air_callbacks(recorder: AIRRecorder) -> dict[str, Callable[..., Any]]:
    """Return the four ADK callbacks (``before_model_callback`` / ``after_model_callback`` /
    ``before_tool_callback`` / ``after_tool_callback``) wired to ``recorder``.

    Spread the result into the ``LlmAgent(...)`` constructor::

        agent = LlmAgent(name="...", model="...", **make_air_callbacks(recorder))

    All four callbacks are async so they compose cleanly with user-supplied
    async callbacks; ADK awaits the return value either way.
    """
    return {
        "before_model_callback": _chain_before_model(recorder, None),
        "after_model_callback": _chain_after_model(recorder, None),
        "before_tool_callback": _chain_before_tool(recorder, None),
        "after_tool_callback": _chain_after_tool(recorder, None),
    }


def instrument_adk(agent: Any, recorder: AIRRecorder) -> Any:
    """Attach AIR callbacks to a constructed ``LlmAgent`` (or compatible) in-place.

    Preserves any callbacks already set on the agent: AIR's callback fires
    first to record, then chains to the original callback so its return value
    (which can short-circuit the model call or replace the response) is
    honoured. Returns the same ``agent`` for chaining.

    Raises ``AttributeError`` if ``agent`` has no callback fields. List-form
    callbacks (``BeforeToolCallback`` accepts ``list[single]``) are wrapped
    by treating the whole list as a single existing callback that ADK will
    iterate; AIR's callback runs first.
    """
    for field in _CALLBACK_FIELDS:
        if not hasattr(agent, field):
            raise AttributeError(f"agent has no field {field!r}; not an LlmAgent-shaped object")
    agent.before_model_callback = _chain_before_model(recorder, agent.before_model_callback)
    agent.after_model_callback = _chain_after_model(recorder, agent.after_model_callback)
    agent.before_tool_callback = _chain_before_tool(recorder, agent.before_tool_callback)
    agent.after_tool_callback = _chain_after_tool(recorder, agent.after_tool_callback)
    return agent
