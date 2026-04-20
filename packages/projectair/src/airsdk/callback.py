"""LangChain callback that writes a signed AgDR chain for every agent step."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from langchain_core.agents import AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from airsdk.agdr import Signer
from airsdk.types import AgDRPayload, AgDRRecord, StepKind


def _resolve_key(key: str | Ed25519PrivateKey | None) -> Ed25519PrivateKey | None:
    if key is None:
        return None
    if isinstance(key, Ed25519PrivateKey):
        return key
    data = key.strip()
    if data.startswith("-----BEGIN"):
        priv = load_pem_private_key(data.encode(), password=None)
        if not isinstance(priv, Ed25519PrivateKey):
            raise ValueError(f"key PEM must hold an Ed25519 key, got {type(priv).__name__}")
        return priv
    try:
        seed = bytes.fromhex(data)
    except ValueError as exc:
        raise ValueError("key must be a PEM-encoded private key or a 64-char hex Ed25519 seed") from exc
    if len(seed) != 32:
        raise ValueError(f"hex key must decode to 32 bytes, got {len(seed)}")
    return Ed25519PrivateKey.from_private_bytes(seed)


class AIRCallbackHandler(BaseCallbackHandler):
    """Writes a signed AgDR record for every agent step to a JSON-lines log file.

    Parameters
    ----------
    key:
        Ed25519 signing key. Accepts a 64-char hex seed, a PEM-encoded private key,
        or a raw ``Ed25519PrivateKey``. When ``None``, a fresh keypair is generated
        for the session and the public half is written on every record.
    log_path:
        Where AgDR records are appended. Defaults to ``air-trace-<unix>.log`` in
        the current working directory.
    user_intent:
        Optional plain-text statement of what the user asked the agent to do.
        Attached to every record so the ASI01 Goal Hijack detector has a reliable
        anchor even if the underlying chain never echoes the prompt.
    """

    def __init__(
        self,
        key: str | Ed25519PrivateKey | None = None,
        log_path: str | Path | None = None,
        *,
        user_intent: str | None = None,
    ) -> None:
        super().__init__()
        priv = _resolve_key(key)
        self._signer = Signer(priv) if priv is not None else Signer.generate()
        self.log_path = Path(log_path) if log_path else Path(f"air-trace-{int(time.time())}.log")
        self._log_path_resolved = self.log_path.expanduser()
        self._log_path_resolved.parent.mkdir(parents=True, exist_ok=True)
        self._user_intent = user_intent

    @property
    def public_key_hex(self) -> str:
        """The Ed25519 public key all written records can be verified against."""
        return self._signer.public_key_hex

    def _emit(self, kind: StepKind, payload_data: dict[str, Any]) -> AgDRRecord:
        if self._user_intent and "user_intent" not in payload_data:
            payload_data = {**payload_data, "user_intent": self._user_intent}
        payload = AgDRPayload.model_validate(payload_data)
        record = self._signer.sign(kind=kind, payload=payload)
        with self._log_path_resolved.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json(exclude_none=True))
            handle.write("\n")
        return record

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
        self._emit(
            StepKind.LLM_START,
            {"prompt": "\n".join(prompts)},
        )

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
        self._emit(StepKind.LLM_END, {"response": "\n".join(texts)})

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
        self._emit(
            StepKind.TOOL_START,
            {"tool_name": str(tool_name), "tool_args": {"input": input_str}},
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._emit(StepKind.TOOL_END, {"tool_output": str(output)})

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        final = finish.return_values.get("output") if isinstance(finish.return_values, dict) else str(finish.return_values)
        self._emit(StepKind.AGENT_FINISH, {"final_output": str(final) if final is not None else ""})
