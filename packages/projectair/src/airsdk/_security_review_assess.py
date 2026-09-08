"""Per-question evidence extraction for the security-review pack.

Each ``_assess_*`` reads one control's evidence from the signed chain and
returns a :class:`QuestionResult`. Split from ``security_review.py`` (which
renders) to keep both under the 300-line limit.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from airsdk._security_review_content import (
    QUESTIONS,
    STATUS_EVIDENCED,
    STATUS_NOT_EVIDENCED,
    STATUS_PARTIAL,
    Question,
)
from airsdk.detections import IMPLEMENTED_AIR_DETECTORS, IMPLEMENTED_ASI_DETECTORS
from airsdk.types import AgDRRecord, Finding, StepKind, VerificationStatus


@dataclass(frozen=True)
class QuestionResult:
    """Status, evidence, and draft answer for one reviewer question."""

    question: Question
    status: str
    evidence: list[str]
    answer: str


def _short_key(key: str) -> str:
    return f"{key[:16]}..." if len(key) > 16 else key


def _kinds(records: list[AgDRRecord]) -> Counter[str]:
    return Counter(r.kind.value for r in records)


def _of_kind(records: list[AgDRRecord], kind: StepKind) -> list[AgDRRecord]:
    return [r for r in records if r.kind is kind]


def timestamp_range(records: list[AgDRRecord]) -> tuple[str, str]:
    """(earliest, latest) record timestamps, or ('', '') for an empty chain."""
    stamps = sorted(r.timestamp for r in records if r.timestamp)
    return (stamps[0], stamps[-1]) if stamps else ("", "")


def _q(key: str) -> Question:
    return next(q for q in QUESTIONS if q.key == key)




def _assess_logging(records: list[AgDRRecord]) -> QuestionResult:
    kinds = _kinds(records)
    earliest, latest = timestamp_range(records)
    llm = kinds.get("llm_start", 0)
    tools = kinds.get("tool_start", 0)
    status = STATUS_EVIDENCED if records else STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(records)} signed records between {earliest} and {latest} (UTC).",
        f"{llm} model calls, {tools} tool calls, {kinds.get('agent_finish', 0)} final outputs recorded.",
        "Record kinds: " + ", ".join(f"{k} x{n}" for k, n in sorted(kinds.items())) + ".",
    ]
    answer = (
        f"Every model call, tool call, and final output is written at the moment of action as a signed "
        f"record (an AgDR-format Intent Capsule). The attached chain holds {len(records)} records covering "
        f"{llm} model calls and {tools} tool calls."
    )
    return QuestionResult(_q("logging"), status, evidence, answer)


def _assess_integrity(records: list[AgDRRecord], verification: VerificationStatus) -> QuestionResult:
    keys = sorted({r.signer_key for r in records if r.signer_key})
    algos = sorted({r.signature_algorithm for r in records})
    ok = verification is VerificationStatus.OK
    status = STATUS_EVIDENCED if ok and records else STATUS_NOT_EVIDENCED
    evidence = [
        f"Chain verification: {verification.value}.",
        f"Each record carries a BLAKE3 content hash and a {' / '.join(algos)} signature over the previous "
        "hash, so altering or deleting any record breaks verification at that record.",
        f"{len(keys)} signer key(s): " + ", ".join(_short_key(k) for k in keys) + ".",
        "Third-party verification: `air trace <chain>` with the publicly available `projectair` package (verification is licensed to everyone), no vendor API required.",
    ]
    answer = (
        "Logs are hash-chained and signed per record. A reviewer verifies them with open-source tooling "
        f"and the chain file alone. The attached chain verifies {verification.value}."
    )
    return QuestionResult(_q("integrity"), status, evidence, answer)


def _assess_anchoring(records: list[AgDRRecord]) -> QuestionResult:
    anchors = _of_kind(records, StepKind.ANCHOR)
    rekor = [r.payload.rekor for r in anchors if r.payload.rekor is not None]
    tsa = [r.payload.rfc3161 for r in anchors if r.payload.rfc3161 is not None]
    if rekor and tsa:
        status = STATUS_EVIDENCED
    elif anchors:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_EVIDENCED
    evidence = [f"{len(anchors)} anchor record(s) in the chain."]
    if rekor:
        evidence.append(
            "Sigstore Rekor log indices: " + ", ".join(str(a.log_index) for a in rekor[-5:]) + "."
        )
    if tsa:
        evidence.append("RFC 3161 timestamp authorities: " + ", ".join(sorted({a.tsa_url for a in tsa})) + ".")
    answer = (
        "Chain roots are timestamped by an RFC 3161 authority and logged in the public Sigstore Rekor "
        "transparency log, so a reviewer can confirm the records existed at the stated time using public "
        "services only (`air verify-public`)."
        if status is STATUS_EVIDENCED
        else "External anchoring is available and not present in the attached chain for this period."
    )
    return QuestionResult(_q("anchoring"), status, evidence, answer)


def _assess_scope(records: list[AgDRRecord], findings: list[Finding]) -> QuestionResult:
    intents = _of_kind(records, StepKind.INTENT_DECLARATION)
    delegations = _of_kind(records, StepKind.DELEGATION)
    declared = [r.payload.user_intent for r in records if r.payload.user_intent]
    scope_findings = [f for f in findings if f.detector_id in {"ASI01", "ASI03", "ASI10"}]
    if intents or delegations:
        status = STATUS_EVIDENCED
    elif declared:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(intents)} intent declaration(s) and {len(delegations)} delegation grant(s) open the chain.",
        f"{len(declared)} of {len(records)} records carry the declared user intent.",
        f"{len(scope_findings)} scope-related finding(s) (ASI01 / ASI03 / ASI10) in this chain.",
    ]
    answer = (
        "The authorized goal and scope are the first signed record of the session, and every later step "
        "is checked against it by the goal-hijack and Zero-Trust scope detectors."
        if status is STATUS_EVIDENCED
        else "The declared user intent travels with each record; a signed scope declaration at session start is not present in this chain."
    )
    return QuestionResult(_q("scope"), status, evidence, answer)


def _assess_oversight(records: list[AgDRRecord]) -> QuestionResult:
    blocked = [r for r in records if r.payload.blocked]
    challenges = [r for r in blocked if r.payload.challenge_id]
    approvals = [r.payload.human_approval for r in _of_kind(records, StepKind.HUMAN_APPROVAL)]
    issuers = sorted({a.issuer for a in approvals if a is not None})
    if approvals:
        status = STATUS_EVIDENCED
    elif blocked:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(blocked)} action(s) halted by policy, {len(challenges)} of them pending human approval.",
        f"{len(approvals)} human approval record(s), each carrying the verified identity-provider token.",
    ]
    if issuers:
        evidence.append("Approval issuers: " + ", ".join(issuers) + ".")
    answer = (
        "Sensitive tools halt until a human approves through the identity provider; the approval is a signed "
        "record carrying the verified token, and a forged or replayed token leaves the action halted."
        if status is STATUS_EVIDENCED
        else "Containment with identity-bound human approval is available; this chain records no approvals for the period."
    )
    return QuestionResult(_q("oversight"), status, evidence, answer)


def _assess_detection(findings: list[Finding]) -> QuestionResult:
    by_detector = Counter(f.detector_id for f in findings)
    asi = ", ".join(code for code, _, _ in IMPLEMENTED_ASI_DETECTORS)
    air = ", ".join(code for code, _, _ in IMPLEMENTED_AIR_DETECTORS)
    evidence = [
        f"Coverage: 10 OWASP Agentic ({asi}) + 3 OWASP LLM + 3 AIR-native ({air}) = 16 detectors.",
        f"{len(findings)} finding(s) in this chain"
        + (": " + ", ".join(f"{d} x{n}" for d, n in sorted(by_detector.items())) if findings else "")
        + ".",
        "ASI03 and ASI10 are declared-scope Zero-Trust checks and need an agent registry to fire.",
    ]
    answer = (
        "Sixteen detectors mapped to the OWASP Top 10 for Agentic Applications and OWASP LLM Top 10 run over "
        f"every chain, including prompt injection, goal hijack, tool misuse, and sensitive-data exposure. "
        f"This chain produced {len(findings)} finding(s), listed in the appendix."
    )
    return QuestionResult(_q("detection"), STATUS_EVIDENCED, evidence, answer)


def _assess_data_handling(records: list[AgDRRecord], findings: list[Finding]) -> QuestionResult:
    referenced = [r for r in records if r.payload.content_refs]
    exposures = [f for f in findings if f.detector_id == "AIR-02"]
    if referenced and not exposures:
        status = STATUS_EVIDENCED
    elif referenced or not exposures:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(referenced)} record(s) store sensitive fields as salted digests with the plaintext in an erasable vault.",
        f"{len(exposures)} sensitive-data exposure finding(s) (AIR-02) in this chain.",
    ]
    answer = (
        "Sensitive fields never enter the signed chain in plaintext: a capture policy replaces them with "
        "per-record salted digests, and the plaintext lives in an access-controlled, erasable vault."
        if referenced
        else "The chain is scanned for credentials and personal data on every run (AIR-02); a capture policy that keeps such fields out of the chain by construction is available."
    )
    return QuestionResult(_q("data_handling"), status, evidence, answer)


def _assess_attribution(records: list[AgDRRecord]) -> QuestionResult:
    delegations = [r.payload.delegation for r in _of_kind(records, StepKind.DELEGATION)]
    approvals = _of_kind(records, StepKind.HUMAN_APPROVAL)
    keys = {r.signer_key for r in records if r.signer_key}
    if delegations:
        status = STATUS_EVIDENCED
    elif approvals or keys:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_EVIDENCED
    methods = sorted({d.auth_method.value for d in delegations if d is not None})
    evidence = [
        f"{len(delegations)} session(s) opened by an identity-verified human authorization"
        + (f" ({', '.join(methods)})" if methods else "") + ".",
        f"{len(keys)} agent signing key(s) sign every record; {len(approvals)} human approval(s) carry an IdP-verified subject.",
    ]
    answer = (
        "Each session opens with a signed delegation record binding the chain to the human who authorized the "
        "agent, and every record is signed by the agent's key, so accountability is cryptographic rather than declared."
        if status is STATUS_EVIDENCED
        else "Every record is signed by the agent's key; a session-genesis human authorization record is available and not present in this chain."
    )
    return QuestionResult(_q("attribution"), status, evidence, answer)


def _assess_review(records: list[AgDRRecord]) -> QuestionResult:
    reviews = [r.payload.audit_review for r in _of_kind(records, StepKind.AUDIT_REVIEW)]
    outcomes = Counter(r.outcome for r in reviews if r is not None)
    status = STATUS_EVIDENCED if reviews else STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(reviews)} signed audit-trail review(s)"
        + (": " + ", ".join(f"{o} x{n}" for o, n in sorted(outcomes.items())) if reviews else "") + "."
    ]
    answer = (
        "Periodic reviews are recorded in the chain itself as signed, identity-verified records naming the range reviewed and the outcome."
        if reviews
        else "Signed audit-trail review records are available and none are present in this chain for the period."
    )
    return QuestionResult(_q("review"), status, evidence, answer)


def _assess_key_custody(records: list[AgDRRecord]) -> QuestionResult:
    transitions = [r.payload.key_transition for r in _of_kind(records, StepKind.KEY_TRANSITION)]
    keys = sorted({r.signer_key for r in records if r.signer_key})
    status = STATUS_EVIDENCED if transitions else STATUS_PARTIAL if keys else STATUS_NOT_EVIDENCED
    evidence = [
        f"{len(transitions)} signed key transition(s); {len(keys)} distinct signer key(s) across the chain.",
        "Reasons: " + ", ".join(sorted({t.reason for t in transitions if t is not None})) + "."
        if transitions else "No key rotation recorded in this chain.",
    ]
    answer = (
        "Signing keys rotate through signed handoff records in which the outgoing key authorizes the incoming key, "
        "verifiable end to end with `verify_key_custody`."
        if transitions
        else "Records are signed by a per-agent key; signed key rotation is available and no rotation occurred in this period."
    )
    return QuestionResult(_q("key_custody"), status, evidence, answer)


def assess_security_review(records: list[AgDRRecord], findings: list[Finding], verification: VerificationStatus) -> list[QuestionResult]:
    """Compute status, evidence, and draft answer for every reviewer question, in question order."""
    return [
        _assess_logging(records),
        _assess_integrity(records, verification),
        _assess_anchoring(records),
        _assess_scope(records, findings),
        _assess_oversight(records),
        _assess_detection(findings),
        _assess_data_handling(records, findings),
        _assess_attribution(records),
        _assess_review(records),
        _assess_key_custody(records),
    ]


