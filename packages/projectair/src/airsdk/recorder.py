"""Framework-agnostic recorder for writing signed AgDR records.

``AIRRecorder`` is the primitive. It wraps a ``Signer`` and a log file, and
exposes one method per AgDR step kind. Framework integrations (LangChain,
OpenAI SDK, Anthropic SDK, and any custom code) all build on top of it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from airsdk.agdr import Signer, _uuid7
from airsdk.types import AgDRPayload, AgDRRecord, StepKind


def resolve_signing_key(key: str | Ed25519PrivateKey | None) -> Ed25519PrivateKey | None:
    """Accept an Ed25519 private key as hex seed, PEM, or raw key instance.

    Returns ``None`` when ``key`` is ``None`` so callers can fall back to
    ``Signer.generate()`` explicitly.
    """
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


class AIRRecorder:
    """Write signed AgDR records to a JSONL log. Framework-agnostic.

    Parameters
    ----------
    log_path:
        Where AgDR records are appended. Parent directories are created on
        first write. Required.
    key:
        Ed25519 signing key. Accepts a 64-char hex seed, a PEM-encoded
        private key, or a raw ``Ed25519PrivateKey``. When ``None``, a fresh
        keypair is generated for the session.
    user_intent:
        Optional plain-text statement of what the user asked the agent to
        do. Attached to every record this recorder emits, so the ASI01
        Goal Hijack detector has a reliable anchor even if the underlying
        chain never echoes the original prompt.
    """

    def __init__(
        self,
        log_path: str | Path,
        key: str | Ed25519PrivateKey | None = None,
        *,
        user_intent: str | None = None,
    ) -> None:
        priv = resolve_signing_key(key)
        self._signer = Signer(priv) if priv is not None else Signer.generate()
        self._log_path = Path(log_path).expanduser()
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_intent = user_intent

    @property
    def public_key_hex(self) -> str:
        """Ed25519 public key of the signer. Verifiers use this."""
        return self._signer.public_key_hex

    @property
    def log_path(self) -> Path:
        """Where this recorder appends its JSONL."""
        return self._log_path

    # -- Step emitters -----------------------------------------------------

    def llm_start(self, *, prompt: str, **extra: Any) -> AgDRRecord:
        """Agent is about to call an LLM with ``prompt``."""
        return self._emit(StepKind.LLM_START, {"prompt": prompt, **extra})

    def llm_end(self, *, response: str, **extra: Any) -> AgDRRecord:
        """LLM returned ``response``."""
        return self._emit(StepKind.LLM_END, {"response": response, **extra})

    def tool_start(
        self,
        *,
        tool_name: str,
        tool_args: dict[str, Any] | None = None,
        **extra: Any,
    ) -> AgDRRecord:
        """Agent is about to invoke a tool."""
        return self._emit(
            StepKind.TOOL_START,
            {"tool_name": tool_name, "tool_args": tool_args or {}, **extra},
        )

    def tool_end(self, *, tool_output: str, **extra: Any) -> AgDRRecord:
        """Tool returned ``tool_output``."""
        return self._emit(StepKind.TOOL_END, {"tool_output": tool_output, **extra})

    def agent_finish(self, *, final_output: str, **extra: Any) -> AgDRRecord:
        """Agent run completed with ``final_output``."""
        return self._emit(StepKind.AGENT_FINISH, {"final_output": final_output, **extra})

    def agent_message(
        self,
        *,
        source_agent_id: str,
        target_agent_id: str,
        message_content: str,
        message_id: str | None = None,
        **extra: Any,
    ) -> AgDRRecord:
        """Inter-agent message from ``source_agent_id`` to ``target_agent_id``.

        Emits an ``agent_message`` record that the ASI07 detector (OWASP Top 10
        for Agentic Applications, Insecure Inter-Agent Communication) walks to
        check for missing identity, missing nonces, sender/key mismatch, replay,
        and protocol downgrade across inter-agent exchanges.

        ``message_id`` is a per-message nonce. When omitted, a UUIDv7 is
        generated so replay defense is on by default; callers that carry their
        own protocol's message id should pass it through.
        """
        resolved_id = message_id if message_id is not None else _uuid7()
        return self._emit(
            StepKind.AGENT_MESSAGE,
            {
                "source_agent_id": source_agent_id,
                "target_agent_id": target_agent_id,
                "message_content": message_content,
                "message_id": resolved_id,
                **extra,
            },
        )

    # -- Internal ---------------------------------------------------------

    def _emit(self, kind: StepKind, fields: dict[str, Any]) -> AgDRRecord:
        if self._user_intent and "user_intent" not in fields:
            fields = {**fields, "user_intent": self._user_intent}
        payload = AgDRPayload.model_validate(fields)
        record = self._signer.sign(kind=kind, payload=payload)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json(exclude_none=True))
            handle.write("\n")
        return record
