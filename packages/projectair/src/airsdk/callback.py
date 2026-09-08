"""LangChain callback that writes a signed AgDR chain for every agent step."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from langchain_core.agents import AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from airsdk.recorder import AIRRecorder
from airsdk.transport import Transport


class AIRCallbackHandler(BaseCallbackHandler):
    """Writes a signed AgDR record for every agent step to a JSON-lines log file.

    Thin LangChain-native wrapper over :class:`airsdk.recorder.AIRRecorder`.
    Prefer the recorder directly if you're not using LangChain.

    Parameters
    ----------
    key:
        Ed25519 signing key. Accepts a 64-char hex seed, a PEM-encoded private key,
        or a raw ``Ed25519PrivateKey``. When ``None``, a fresh keypair is generated.
    log_path:
        Where AgDR records are appended. Defaults to a fresh
        ``.air/air-trace-<unix ms>.log`` under the current working directory;
        the recorder prints the path on its first record.
    user_intent:
        Optional plain-text statement of what the user asked the agent to do.
        Attached to every record so the ASI01 Goal Hijack detector has a reliable
        anchor even when the underlying chain does not echo the original prompt.
    recorder:
        Use an existing recorder instead of building one; every other argument
        is then ignored. This is how a LangChain agent shares one chain with
        the rest of an application, and how it reaches AIR Cloud.
    transports:
        Explicit sinks for the recorder this handler builds (see
        :class:`airsdk.recorder.AIRRecorder`).
    """

    def __init__(
        self,
        key: str | Ed25519PrivateKey | None = None,
        log_path: str | Path | None = None,
        *,
        user_intent: str | None = None,
        recorder: AIRRecorder | None = None,
        transports: list[Transport] | None = None,
    ) -> None:
        super().__init__()
        if recorder is not None:
            self._recorder = recorder
            return
        self._recorder = AIRRecorder(
            log_path=Path(log_path) if log_path else None, key=key, user_intent=user_intent, transports=transports
        )

    @property
    def log_path(self) -> Path:
        return self._recorder.log_path

    @property
    def public_key_hex(self) -> str:
        return self._recorder.public_key_hex

    @property
    def recorder(self) -> AIRRecorder:
        """Expose the underlying recorder for users who need to emit tool events manually."""
        return self._recorder

    # --- LangChain BaseCallbackHandler hooks -------------------------------

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._recorder.llm_start(prompt="\n".join(prompts))

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        texts: list[str] = []
        for generation_batch in response.generations:
            for generation in generation_batch:
                if getattr(generation, "text", None):
                    texts.append(generation.text)
        self._recorder.llm_end(response="\n".join(texts))

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name") or serialized.get("id", ["unknown"])[-1]
        self._recorder.tool_start(tool_name=str(tool_name), tool_args={"input": input_str})

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._recorder.tool_end(tool_output=str(output))

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        final = finish.return_values.get("output") if isinstance(finish.return_values, dict) else str(finish.return_values)
        self._recorder.agent_finish(final_output=str(final) if final is not None else "")
