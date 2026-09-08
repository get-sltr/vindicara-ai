"""Authority resolution for the incident timeline.

Every record in a chain executed under *some* authority, and the chain
already carries the evidence: a ``DELEGATION`` genesis binds the session
to an identity-verified human, a ``HUMAN_APPROVAL`` binds one halted
action to the approver who released it, a ``KEY_TRANSITION`` is the prior
key vouching for the next, an ``ANCHOR`` is an outside witness. What the
chain does not do is say, per step, which of those applied. This module
walks the chain once and answers that for every record, so the timeline
can print "under whose authority" next to "what executed".

The resolver never asserts more than the records show. A step with no
delegation, no approval, and no declared intent is labelled ``agent-key``:
the only thing vouching for it is the agent's own signing key.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from airsdk._compat import UTC, StrEnum
from airsdk.types import AgDRRecord, DelegationGrant, HumanApproval, StepKind


class AuthorityKind(StrEnum):
    DELEGATED = "delegated"  # session opened by an identity-verified human; grant valid at this step
    APPROVED = "approved"  # this action was halted and released by a verified human approval
    HALTED = "halted"  # policy halted the action; no approval released it at this record
    DECLARED = "declared"  # scope declared up front, but no human identity bound to it
    EXPIRED = "expired"  # a delegation exists but had expired when this step ran
    AGENT_KEY = "agent-key"  # only the agent's signing key vouches for this step
    ROTATED = "rotated"  # signing key handoff authorized by the prior key
    WITNESSED = "witnessed"  # external anchor: an outside party witnessed the chain root
    REVIEWED = "reviewed"  # a verified human reviewed a range of the chain
    ATTESTED = "attested"  # hardware root of trust for the session


#: Record kinds that are themselves authority events rather than agent actions.
AUTHORITY_EVENT_KINDS: frozenset[StepKind] = frozenset({
    StepKind.DELEGATION,
    StepKind.INTENT_DECLARATION,
    StepKind.HUMAN_APPROVAL,
    StepKind.AUDIT_REVIEW,
    StepKind.KEY_TRANSITION,
    StepKind.GPU_ATTESTATION,
    StepKind.ANCHOR,
})


class Authority(BaseModel):
    """Who or what vouched for one record, and the evidence for saying so."""

    model_config = ConfigDict(extra="forbid")

    kind: AuthorityKind
    subject: str | None = None  # IdP subject, WebAuthn handle, key id, or anchor service
    issuer: str | None = None  # IdP issuer URL when a token backs the subject
    detail: str

    def label(self) -> str:
        """Short column text: kind plus subject when there is one."""
        return f"{self.kind.value}: {self.subject}" if self.subject else self.kind.value


def _epoch(timestamp: str) -> float | None:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _iso(seconds: int) -> str:
    return datetime.fromtimestamp(seconds, tz=UTC).isoformat().replace("+00:00", "Z")


def _session_authority(
    record: AgDRRecord, grant: DelegationGrant | None, declared_goal: str | None
) -> Authority:
    """Authority inherited from the session genesis for an ordinary step."""
    if grant is not None:
        at = _epoch(record.timestamp)
        if at is not None and at > grant.expires_at:
            return Authority(
                kind=AuthorityKind.EXPIRED,
                subject=grant.authorizer_sub,
                issuer=grant.issuer,
                detail=f"delegation {grant.delegation_id} expired at {_iso(grant.expires_at)}",
            )
        return Authority(
            kind=AuthorityKind.DELEGATED,
            subject=grant.authorizer_sub,
            issuer=grant.issuer,
            detail=f"delegation {grant.delegation_id} ({grant.auth_method.value}), policy {grant.policy_id}",
        )
    if declared_goal is not None:
        return Authority(kind=AuthorityKind.DECLARED, detail=f"declared scope: {declared_goal}")
    return Authority(
        kind=AuthorityKind.AGENT_KEY,
        subject=record.signer_key[:16],
        detail="no delegation, approval, or declared scope; only the agent signing key vouches",
    )


def _approval_authority(approval: HumanApproval, prefix: str) -> Authority:
    meaning = f", meaning={approval.meaning.value}" if approval.meaning is not None else ""
    return Authority(
        kind=AuthorityKind.APPROVED,
        subject=approval.approver_email or approval.approver_sub,
        issuer=approval.issuer,
        detail=f"{prefix} challenge {approval.challenge_id} via {approval.issuer}{meaning}",
    )


def _event_authority(record: AgDRRecord) -> Authority | None:
    """Authority carried by a record that is itself an authority event."""
    p = record.payload
    if record.kind == StepKind.DELEGATION and p.delegation is not None:
        g = p.delegation
        if g.decision != "authorize":
            return Authority(
                kind=AuthorityKind.HALTED, subject=g.authorizer_sub, issuer=g.issuer,
                detail=f"delegation {g.delegation_id} denied by the authorizer",
            )
        return Authority(
            kind=AuthorityKind.DELEGATED, subject=g.authorizer_sub, issuer=g.issuer,
            detail=(
                f"session for agent {g.agent_id} authorized via {g.auth_method.value} "
                f"under policy {g.policy_id}, valid until {_iso(g.expires_at)}"
            ),
        )
    if record.kind == StepKind.HUMAN_APPROVAL and p.human_approval is not None:
        return _approval_authority(p.human_approval, "released")
    if record.kind == StepKind.AUDIT_REVIEW and p.audit_review is not None:
        r = p.audit_review
        return Authority(
            kind=AuthorityKind.REVIEWED, subject=r.reviewer_email or r.reviewer_sub, issuer=r.issuer,
            detail=f"reviewed {r.reviewed_from_step[:8]}..{r.reviewed_to_step[:8]}: {r.outcome}",
        )
    if record.kind == StepKind.KEY_TRANSITION and p.key_transition is not None:
        return Authority(
            kind=AuthorityKind.ROTATED, subject=p.key_transition.new_signer_key[:16],
            detail=f"key handoff ({p.key_transition.reason}) signed by the outgoing key {record.signer_key[:16]}",
        )
    if record.kind == StepKind.ANCHOR:
        services = [s for s in (p.rfc3161.tsa_url if p.rfc3161 else None, p.rekor.rekor_url if p.rekor else None) if s]
        return Authority(
            kind=AuthorityKind.WITNESSED, subject=", ".join(services) or None,
            detail="chain root witnessed by an external service",
        )
    if record.kind == StepKind.GPU_ATTESTATION and p.attestation is not None:
        return Authority(
            kind=AuthorityKind.ATTESTED, subject=p.attestation.gpu_arch,
            detail=f"NRAS attestation, RIM matched={p.attestation.rim_matched}",
        )
    return None


def resolve_authority(records: list[AgDRRecord]) -> list[Authority]:
    """Return one :class:`Authority` per record, in chain order."""
    grant: DelegationGrant | None = None
    declared_goal: str | None = None
    pending_release: HumanApproval | None = None
    approvals_by_challenge: dict[str, tuple[int, HumanApproval]] = {}
    for index, record in enumerate(records):
        if record.kind == StepKind.HUMAN_APPROVAL and record.payload.human_approval is not None:
            approvals_by_challenge[record.payload.human_approval.challenge_id] = (index, record.payload.human_approval)

    out: list[Authority] = []
    for record in records:
        p = record.payload
        event = _event_authority(record)
        if record.kind == StepKind.DELEGATION and p.delegation is not None and p.delegation.decision == "authorize":
            grant = p.delegation
        if record.kind == StepKind.INTENT_DECLARATION:
            declared_goal = p.intent_spec.goal if p.intent_spec is not None else p.user_intent
            out.append(event or Authority(
                kind=AuthorityKind.DELEGATED if grant else AuthorityKind.DECLARED,
                subject=grant.authorizer_sub if grant else None,
                detail=f"scope declared: {declared_goal or '?'}",
            ))
            continue
        if record.kind == StepKind.HUMAN_APPROVAL and p.human_approval is not None:
            pending_release = p.human_approval
        if event is not None:
            out.append(event)
            continue
        if record.kind == StepKind.TOOL_START and p.blocked:
            released = approvals_by_challenge.get(p.challenge_id or "")
            if released is not None:
                approved_index, approval = released
                out.append(Authority(
                    kind=AuthorityKind.HALTED, subject=approval.approver_email or approval.approver_sub,
                    issuer=approval.issuer,
                    detail=f"halted pending approval; released at step {approved_index}",
                ))
            else:
                out.append(Authority(kind=AuthorityKind.HALTED, detail=p.blocked_reason or "halted by policy"))
            continue
        if record.kind == StepKind.TOOL_START and pending_release is not None:
            out.append(_approval_authority(pending_release, "resumed under"))
            pending_release = None
            continue
        out.append(_session_authority(record, grant, declared_goal))
    return out
