"""Framework-agnostic recorder for writing signed AgDR records.

``AIRRecorder`` is the primitive. It wraps a ``Signer`` and one or more
:class:`Transport` sinks, and exposes one method per AgDR step kind.
Framework integrations (LangChain, OpenAI SDK, Anthropic SDK, and any
custom code) all build on top of it.

By default a recorder writes to a single :class:`FileTransport` so the
historical ``log_path``-only constructor still works unchanged. Callers
that want to also push records to AIR Cloud or any custom sink pass an
explicit ``transports=`` list.
"""
from __future__ import annotations

import atexit
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from airsdk.agdr import (
    _HAS_MLDSA,
    MLDSA65PrivateKey,
    Signer,
    SigningKey,
    _require_mldsa,
    _uuid7,
)
from airsdk.cloud_config import CloudConfig, cloud_config_from_env, genesis_step_id, run_url
from airsdk.containment import (
    ApprovalInvalidError,
    Auth0Verifier,
    BlockedActionError,
    ChallengeNotFoundError,
    ContainmentPolicy,
    Decision,
    DelegationPolicy,
    StepUpRequiredError,
    evaluate_require_delegation,
)
from airsdk.live import LiveAlerts, live_enabled_from_env
from airsdk.reference_vault import ReferenceVault, salted_digest
from airsdk.transport import FileTransport, HTTPTransport, Transport
from airsdk.types import (
    GENESIS_PREV_HASH,
    AgDRPayload,
    AgDRRecord,
    AuditReview,
    CapturePolicy,
    DataAssetRef,
    DataSubjectRef,
    DecisionProvenance,
    DelegationGrant,
    HumanApproval,
    IntentSpec,
    SignatureMeaning,
    SigningAlgorithm,
    StepKind,
)
from airsdk.verification.types import IntentVerdict
from airsdk.verification.verifier import verify_intent as _verify_intent

if TYPE_CHECKING:
    from airsdk.anchoring import AnchoringOrchestrator
    from airsdk.attestation import AttestationProvider, GPUAttestationConfig
    from airsdk.types import Finding

def resolve_signing_key(
    key: str | SigningKey | None,
    algorithm: SigningAlgorithm = SigningAlgorithm.ED25519,
) -> SigningKey | None:
    """Accept a private key as hex seed, PEM, or raw key instance.

    PEM keys are auto-detected (Ed25519 or ML-DSA-65). Hex seeds use
    ``algorithm`` to pick the right key type. Returns ``None`` when
    ``key`` is ``None`` so callers can fall back to ``Signer.generate()``.
    """
    if key is None:
        return None
    if not isinstance(key, str):
        # Already a key instance (SigningKey = Ed25519PrivateKey | MLDSA65PrivateKey).
        return key
    data = key.strip()
    if data.startswith("-----BEGIN"):
        priv = load_pem_private_key(data.encode(), password=None)
        if isinstance(priv, Ed25519PrivateKey):
            return priv
        if _HAS_MLDSA and isinstance(priv, MLDSA65PrivateKey):
            return priv
        raise ValueError(f"key PEM must hold Ed25519 or ML-DSA-65, got {type(priv).__name__}")
    try:
        seed = bytes.fromhex(data)
    except ValueError as exc:
        raise ValueError("key must be a PEM-encoded private key or a 64-char hex seed") from exc
    if len(seed) != 32:
        raise ValueError(f"hex key must decode to 32 bytes, got {len(seed)}")
    if algorithm == SigningAlgorithm.ML_DSA_65:
        _require_mldsa()
        return MLDSA65PrivateKey.from_seed_bytes(seed)
    return Ed25519PrivateKey.from_private_bytes(seed)


_log = logging.getLogger(__name__)
_SHUTDOWN_DRAIN_SECONDS = 5.0


def default_log_path() -> Path:
    """A fresh chain file per run: ``.air/air-trace-<unix ms>.log`` in the working directory."""
    return Path(".air") / f"air-trace-{int(time.time() * 1000)}.log"


class AIRRecorder:
    """Write signed AgDR records to one or more transports. Framework-agnostic.

    Parameters
    ----------
    log_path:
        Where AgDR records are appended on disk; passed to the default
        ``FileTransport`` when ``transports`` is not provided. Defaults to
        ``.air/air-trace-<unix ms>.log`` under the working directory, so every
        run gets its own file and ``air trace`` never sees two chains in one.
        Parent directories are created on first write.
    key:
        Ed25519 signing key. Accepts a 64-char hex seed, a PEM-encoded
        private key, or a raw ``Ed25519PrivateKey``. When ``None``, a fresh
        keypair is generated for the session.
    user_intent:
        Optional plain-text statement of what the user asked the agent to
        do. Attached to every record this recorder emits, so the ASI01
        Goal Hijack detector has a reliable anchor even if the underlying
        chain never echoes the original prompt.
    transports:
        Optional list of :class:`Transport` sinks. When omitted the
        recorder uses ``FileTransport(log_path)`` and, when
        ``AIRSDK_CLOUD_API_KEY`` is set, an ``HTTPTransport`` mirroring every
        record to AIR Cloud (:mod:`airsdk.cloud_config`). Pass an explicit
        list to compose your own sinks.
    live:
        Print a banner, each finding as it fires, and an exit summary to
        stderr (see :mod:`airsdk.live`). ``None`` (default) follows the
        ``AIR_LIVE`` environment variable, which defaults to on. Pass
        ``False`` for a silent recorder.
    live_min_severity:
        Lowest severity printed live; ``medium`` by default.
    """

    def __init__(
        self,
        log_path: str | Path | None = None,
        key: str | SigningKey | None = None,
        *,
        user_intent: str | None = None,
        intent_spec: IntentSpec | None = None,
        delegation: DelegationGrant | None = None,
        attestation: GPUAttestationConfig | None = None,
        attestation_provider: AttestationProvider | None = None,
        transports: list[Transport] | None = None,
        containment: ContainmentPolicy | None = None,
        delegation_policy: DelegationPolicy | None = None,
        auth0_verifier: Auth0Verifier | None = None,
        capture_policy: CapturePolicy | None = None,
        reference_vault: ReferenceVault | None = None,
        signing_algorithm: SigningAlgorithm = SigningAlgorithm.ED25519,
        verify_on_step: bool = False,
        live: bool | None = None,
        live_min_severity: str = "medium",
    ) -> None:
        priv = resolve_signing_key(key, algorithm=signing_algorithm)
        self._signer = Signer(priv) if priv is not None else Signer.generate(signing_algorithm)
        self._log_path = Path(log_path).expanduser() if log_path is not None else default_log_path()
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if delegation is not None and intent_spec is not None:
            raise ValueError(
                "pass either delegation= or intent_spec=, not both; the "
                "delegation already carries the authorized scope as its IntentSpec"
            )
        if attestation is not None and delegation is None:
            raise ValueError(
                "GPU attestation requires delegation=; the attestation nonce "
                "binds to the DELEGATION genesis record, so a session must be "
                "delegated before it can be attested."
            )
        self._attestation = attestation
        self._attestation_provider = attestation_provider
        self._user_intent = user_intent
        self._intent_spec = delegation.scope if delegation is not None else intent_spec
        self._cloud: CloudConfig | None = None
        if transports is not None:
            self._transports: list[Transport] = transports
        else:
            self._transports = [FileTransport(self._log_path)]
            self._cloud = cloud_config_from_env()
            if self._cloud is not None:
                self._transports.append(HTTPTransport.from_config(self._cloud))
        self._orchestrator: AnchoringOrchestrator | None = None
        self._containment = containment
        self._delegation_policy = delegation_policy
        self._auth0 = auth0_verifier
        self._capture_policy = capture_policy
        self._reference_vault = reference_vault
        self._pending: dict[str, dict[str, Any]] = {}
        # Single-use ledger of consumed approval-token JTIs. A valid token may
        # approve at most one challenge: replaying it (same jti) is rejected.
        self._consumed_jtis: set[str] = set()
        self._prior_findings: list[Finding] = []
        self._verify_on_step = verify_on_step
        self._chain_records: list[AgDRRecord] = []
        self._live: LiveAlerts | None = None
        if live if live is not None else live_enabled_from_env():
            self._live = LiveAlerts(self._log_path, min_severity=live_min_severity)
        atexit.register(self._shutdown)

        if delegation is not None:
            genesis = self.open_delegation(delegation)
            if attestation is not None:
                self._emit_gpu_attestation(genesis.content_hash)
        elif intent_spec is not None:
            self._emit(StepKind.INTENT_DECLARATION, {
                "user_intent": intent_spec.goal,
                "intent_spec": intent_spec,
            })

    @property
    def public_key_hex(self) -> str:
        """Ed25519 public key of the signer. Verifiers use this."""
        return self._signer.public_key_hex

    @property
    def log_path(self) -> Path:
        """Where this recorder appends its JSONL (default ``FileTransport`` only)."""
        return self._log_path

    @property
    def cloud(self) -> CloudConfig | None:
        """The AIR Cloud mirror configuration in effect, or ``None`` when local only."""
        return self._cloud

    @property
    def run_id(self) -> str | None:
        """The genesis step_id, once the first record is signed."""
        return genesis_step_id(self._chain_records)

    @property
    def run_url(self) -> str | None:
        """The Flightdeck page for this run, when mirroring is on and a record exists."""
        run_id = self.run_id
        if self._cloud is None or run_id is None:
            return None
        return run_url(self._cloud.console_url, run_id)

    def _shutdown(self) -> None:
        """Flush every transport, then print the live summary (so the run link is honest)."""
        for transport in self._transports:
            try:
                transport.drain(_SHUTDOWN_DRAIN_SECONDS)
            except Exception as exc:
                _log.warning("airsdk.recorder transport drain failed: %s", exc)
        if self._live is not None:
            self._live.summarize(self._chain_records, run_url=self.run_url)

    @property
    def live(self) -> LiveAlerts | None:
        """The live stderr alerter, or ``None`` when the recorder is silent."""
        return self._live

    @property
    def transports(self) -> list[Transport]:
        """Live list of transports this recorder is fanning records out to."""
        return self._transports

    def add_transport(self, transport: Transport) -> None:
        """Register an additional transport sink at runtime.

        Useful when the cloud endpoint or API key is only known after the
        recorder has been constructed (e.g. lazy login flow).
        """
        self._transports.append(transport)

    # -- Step emitters -----------------------------------------------------

    def llm_start(
        self,
        *,
        prompt: str,
        provenance: DecisionProvenance | None = None,
        data_assets: list[DataAssetRef] | None = None,
        data_subjects: list[DataSubjectRef] | None = None,
        **extra: Any,
    ) -> AgDRRecord:
        """Agent is about to call an LLM with ``prompt``."""
        fields: dict[str, Any] = {"prompt": prompt, **extra}
        if provenance is not None:
            fields["provenance"] = provenance
        if data_assets is not None:
            fields["data_assets"] = data_assets
        if data_subjects is not None:
            fields["data_subjects"] = data_subjects
        return self._emit(StepKind.LLM_START, fields)

    def llm_end(
        self,
        *,
        response: str,
        provenance: DecisionProvenance | None = None,
        **extra: Any,
    ) -> AgDRRecord:
        """LLM returned ``response``.

        ``provenance`` records the stochastic conditions that produced the
        output (model snapshot, backend fingerprint, sampling parameters,
        logprobs) so the signed record is faithful for a non-deterministic
        decision. See :class:`airsdk.types.DecisionProvenance`.
        """
        fields: dict[str, Any] = {"response": response, **extra}
        if provenance is not None:
            fields["provenance"] = provenance
        return self._emit(StepKind.LLM_END, fields)

    def tool_start(
        self,
        *,
        tool_name: str,
        tool_args: dict[str, Any] | None = None,
        prior_findings: list[Finding] | None = None,
        data_assets: list[DataAssetRef] | None = None,
        data_subjects: list[DataSubjectRef] | None = None,
        **extra: Any,
    ) -> AgDRRecord:
        """Agent is about to invoke a tool.

        When a containment policy is attached, this is the gate where
        deny / step-up rules are enforced. The policy is consulted
        before any side effect happens. Three outcomes:

        - allowed: write a normal TOOL_START and return it
        - blocked: write a TOOL_START with ``blocked=True`` plus the
          reason, then raise ``BlockedActionError`` so the agent does
          not call the tool
        - step-up: write a TOOL_START with ``blocked=True`` and a
          ``challenge_id``, then raise ``StepUpRequiredError`` so the
          agent can route the human through Auth0 and call
          ``approve(challenge_id, token)`` to resume

        ``prior_findings`` is the detector findings list for
        ``block_on_findings`` rules. Pass the output of
        ``run_detectors`` over the chain so far.
        """
        fields: dict[str, Any] = {
            "tool_name": tool_name,
            "tool_args": tool_args or {},
            **extra,
        }
        if data_assets is not None:
            fields["data_assets"] = data_assets
        if data_subjects is not None:
            fields["data_subjects"] = data_subjects

        delegation_result = evaluate_require_delegation(
            self._chain_records,
            policy=self._delegation_policy,
        )
        if delegation_result.blocked:
            fields["blocked"] = True
            fields["blocked_reason"] = delegation_result.reason
            self._emit(StepKind.TOOL_START, fields)
            raise BlockedActionError(delegation_result.reason, tool_name=tool_name)

        if self._containment is None:
            return self._emit(StepKind.TOOL_START, fields)

        verdict = self._containment.evaluate(
            tool_name=tool_name,
            tool_args=tool_args,
            prior_findings=prior_findings if prior_findings is not None else self._prior_findings,
            records=self._chain_records,
        )
        if verdict.decision == Decision.ALLOW:
            return self._emit(StepKind.TOOL_START, fields)

        # Both BLOCK and STEP_UP write a tool_start record with blocked=True
        # so the chain captures the attempt for forensic posterity. The
        # difference is whether the action can be resumed via approve().
        fields["blocked"] = True
        fields["blocked_reason"] = verdict.reason
        if verdict.decision == Decision.STEP_UP:
            assert verdict.challenge_id is not None
            fields["challenge_id"] = verdict.challenge_id
            self._pending[verdict.challenge_id] = {
                "tool_name": tool_name,
                "tool_args": tool_args or {},
                "extra": extra,
            }
            self._emit(StepKind.TOOL_START, fields)
            raise StepUpRequiredError(
                verdict.reason,
                challenge_id=verdict.challenge_id,
                tool_name=tool_name,
            )
        # Decision.BLOCK
        self._emit(StepKind.TOOL_START, fields)
        raise BlockedActionError(verdict.reason, tool_name=tool_name)

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

    def open_delegation(self, grant: DelegationGrant) -> AgDRRecord:
        """Emit the session-genesis DELEGATION record, then declare its scope.

        Binds the entire chain to the human who authorized this agent: who,
        under which policy, within which scope, until when. Because every later
        record hash-chains from this genesis, binding the genesis to an
        authenticated human binds the whole session.

        Must be the chain root. The authorized scope is also emitted as an
        ``INTENT_DECLARATION`` so Structural Verification enforces exactly what
        the human authorized. Raises ``RuntimeError`` if the recorder has
        already emitted records (so a caller cannot slip records in ahead of
        the delegation).
        """
        if self._signer.head_hash != GENESIS_PREV_HASH:
            raise RuntimeError(
                "open_delegation must be the first record on the chain; the "
                "recorder has already emitted records. Construct the recorder "
                "without intent_spec= and call open_delegation before any step."
            )
        record = self._emit(
            StepKind.DELEGATION,
            {"delegation": grant, "user_intent": grant.scope.goal},
        )
        self._emit(
            StepKind.INTENT_DECLARATION,
            {"user_intent": grant.scope.goal, "intent_spec": grant.scope},
        )
        return record

    def _emit_gpu_attestation(self, genesis_content_hash: str) -> AgDRRecord:
        """Emit the GPU_ATTESTATION record right after the DELEGATION genesis.

        The attestation nonce is derived from the genesis content hash, so the
        NVIDIA-signed token binds to this exact authorized session. Purely
        additive: only runs when the recorder was built with ``attestation=``
        (which requires ``delegation=``).
        """
        from airsdk.attestation import attest_session

        assert self._attestation is not None
        attestation = attest_session(
            genesis_content_hash,
            self._attestation,
            provider=self._attestation_provider,
        )
        return self._emit(StepKind.GPU_ATTESTATION, {"attestation": attestation})

    # -- Internal ---------------------------------------------------------

    @property
    def signer(self) -> Signer:
        """The chain signer this recorder writes through.

        Exposed so an :class:`AnchoringOrchestrator` can sign anchor
        records onto the same chain rather than starting a parallel one.
        """
        return self._signer

    @property
    def orchestrator(self) -> AnchoringOrchestrator | None:
        return self._orchestrator

    def update_findings(self, findings: list[Finding]) -> None:
        """Refresh the detector-finding state the containment policy reads.

        Operators that run detectors continuously (every N steps) call
        this with the latest findings list so ``block_on_findings`` rules
        see them on the next tool_start.
        """
        self._prior_findings = list(findings)

    def approve(
        self,
        challenge_id: str,
        auth0_token: str,
        *,
        signature_meaning: SignatureMeaning = SignatureMeaning.APPROVAL,
    ) -> AgDRRecord:
        """Verify a step-up approval token and resume the halted action.

        Validates ``auth0_token`` against the configured ``Auth0Verifier``,
        writes a ``HUMAN_APPROVAL`` record carrying the verified claims
        and the original signed token (for offline re-verification),
        then re-emits the originally-halted tool_start as a real (non-
        blocked) record. The agent that was awaiting approval now
        resumes with that record's step_id.

        ``signature_meaning`` records the 21 CFR Part 11 §11.50 meaning of the
        signature (approval / review / responsibility / authorship) so the
        HUMAN_APPROVAL is a complete Part 11 electronic signature.

        Raises ``ApprovalInvalidError`` if the token does not verify or has
        already been used to approve another challenge (single-use jti), or
        ``ChallengeNotFoundError`` if no pending challenge matches. All leave
        the action permanently halted; an attacker submitting a forged or
        replayed token cannot drive the agent forward.
        """
        if self._auth0 is None:
            raise ChallengeNotFoundError(
                "no Auth0Verifier configured; pass auth0_verifier= to AIRRecorder",
            )
        if challenge_id not in self._pending:
            raise ChallengeNotFoundError(
                f"challenge {challenge_id!r} is not pending; either expired, "
                "already resolved, or never issued",
            )
        claims = self._auth0.verify(auth0_token)
        # Replay defense: a token carrying a jti may be consumed exactly once.
        if claims.jti is not None:
            if claims.jti in self._consumed_jtis:
                raise ApprovalInvalidError(
                    f"approval token jti {claims.jti!r} has already been used; "
                    "replayed approval tokens are rejected",
                )
            self._consumed_jtis.add(claims.jti)

        approval = HumanApproval(
            challenge_id=challenge_id,
            decision="approve",
            approver_sub=claims.sub,
            approver_email=claims.email,
            issuer=claims.issuer,
            audience=claims.audience,
            token_jti=claims.jti,
            issued_at=claims.issued_at,
            expires_at=claims.expires_at,
            signed_token=auth0_token,
            meaning=signature_meaning,
        )
        approval_record = self._emit(
            StepKind.HUMAN_APPROVAL,
            {
                "challenge_id": challenge_id,
                "human_approval": approval,
            },
        )
        # Resume the halted action with a fresh non-blocked TOOL_START.
        pending = self._pending.pop(challenge_id)
        resumed_fields: dict[str, Any] = {
            "tool_name": pending["tool_name"],
            "tool_args": pending["tool_args"],
            **pending["extra"],
        }
        self._emit(StepKind.TOOL_START, resumed_fields)
        return approval_record

    def record_audit_review(
        self,
        reviewer_token: str,
        *,
        reviewed_from_step: str,
        reviewed_to_step: str,
        outcome: str = "accepted",
        notes: str | None = None,
        reason: str | None = None,
    ) -> AgDRRecord:
        """Record an IdP-verified audit-trail review (Part 11 §11.10(e) / Annex 11 §9).

        Verifies ``reviewer_token`` against the configured ``Auth0Verifier`` and
        writes a signed, tamper-evident ``AUDIT_REVIEW`` record attributing the
        review of steps ``reviewed_from_step``..``reviewed_to_step`` to the named
        reviewer, with an ``outcome`` ("accepted" / "exceptions_noted"). ``reason``
        carries a reason-for-change note when the review records a correction.

        Unlike ``approve``, a review token is not single-use: the same qualified
        reviewer may review multiple ranges. Raises ``ChallengeNotFoundError`` if
        no ``Auth0Verifier`` is configured; the token itself must verify.
        """
        if self._auth0 is None:
            raise ChallengeNotFoundError(
                "no Auth0Verifier configured; pass auth0_verifier= to AIRRecorder",
            )
        claims = self._auth0.verify(reviewer_token)
        review = AuditReview(
            reviewer_sub=claims.sub,
            reviewer_email=claims.email,
            issuer=claims.issuer,
            audience=claims.audience,
            token_jti=claims.jti,
            reviewed_at=claims.issued_at,
            signed_token=reviewer_token,
            reviewed_from_step=reviewed_from_step,
            reviewed_to_step=reviewed_to_step,
            outcome=outcome,
            notes=notes,
            reason=reason,
        )
        return self._emit(StepKind.AUDIT_REVIEW, {"audit_review": review})

    def attach_orchestrator(self, orchestrator: AnchoringOrchestrator) -> None:
        """Wire an :class:`AnchoringOrchestrator` to this recorder.

        Construct the orchestrator with this recorder's ``signer`` and
        ``transports`` so anchor records chain forward correctly and land
        on the same disk file::

            recorder = AIRRecorder("chain.jsonl")
            orchestrator = AnchoringOrchestrator(
                signer=recorder.signer,
                transports=recorder.transports,
                rfc3161_client=RFC3161Client(),
                rekor_client=RekorClient(signing_key=load_anchoring_key()),
            )
            recorder.attach_orchestrator(orchestrator)

        Calling twice is a no-op except the most recent orchestrator wins.
        """
        self._orchestrator = orchestrator
        orchestrator.register_atexit()

    def _apply_capture_policy(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Replace plaintext of policy-named fields with a per-record **salted**
        BLAKE3 digest so PHI never enters the signed chain, and the digest is
        neither reversible nor correlatable. The salt + plaintext go to the
        reference vault (access-controlled, erasable), never the chain. See
        :class:`airsdk.types.CapturePolicy` and
        :class:`airsdk.reference_vault.ReferenceVault`."""
        policy = self._capture_policy
        if policy is None or not policy.hash_fields:
            return fields
        out = dict(fields)
        refs: dict[str, str] = dict(out.get("content_refs") or {})
        for name in policy.hash_fields:
            value = out.get(name)
            if value is None:
                continue
            salt = os.urandom(16)
            ref = salted_digest(value, salt)
            refs[name] = ref
            if self._reference_vault is not None:
                self._reference_vault.store(ref, salt, name, value)
            out[name] = None
        if refs:
            out["content_refs"] = refs
        return out

    def _emit(self, kind: StepKind, fields: dict[str, Any]) -> AgDRRecord:
        if self._user_intent and "user_intent" not in fields:
            fields = {**fields, "user_intent": self._user_intent}
        fields = self._apply_capture_policy(fields)
        payload = AgDRPayload.model_validate(fields)
        record = self._signer.sign(kind=kind, payload=payload)
        for transport in self._transports:
            transport.emit(record)
        self._chain_records.append(record)
        if self._live is not None:
            if len(self._chain_records) == 1 and (link := self.run_url) is not None:
                self._live.announce_cloud(link)
            self._live.observe(self._chain_records)
        if self._orchestrator is not None:
            self._orchestrator.observe_step(record)
        if (
            self._verify_on_step
            and self._intent_spec is not None
            and kind == StepKind.TOOL_END
        ):
            result = _verify_intent(self._chain_records, self._intent_spec)
            if result.verdict == IntentVerdict.FAILED:
                raise BlockedActionError(
                    f"Structural verification failed: {result.summary}",
                    tool_name=fields.get("tool_name", ""),
                )
        return record
