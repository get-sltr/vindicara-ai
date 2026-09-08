"""Question bank and prose for the AI agent security-review evidence pack.

Every question here is one an enterprise security reviewer or procurement
questionnaire asks a vendor that ships an AI agent. Framework references
are limited to public, checkable sources: EU AI Act Regulation (EU)
2024/1689 Article 12 (record-keeping) and Article 14 (human oversight),
NIST AI RMF 1.0 core functions, SOC 2 Trust Services Criteria CC7.2 and
CC7.3 (system monitoring and security-event evaluation), HIPAA 45 CFR
164.312(b) audit controls, and the OWASP Top 10 for Agentic Applications.
Do not add clause numbers that have not been verified against the source.

Kept separate from ``security_review.py`` so the generator stays focused on
evidence extraction and under the 300-line file limit.
"""
from __future__ import annotations

from typing import NamedTuple

#: Readiness label printed on the report. Promote to production once a
#: customer has handed the pack to a reviewer and closed on it.
READINESS = "beta"

STATUS_EVIDENCED = "EVIDENCED"
STATUS_PARTIAL = "PARTIAL"
STATUS_NOT_EVIDENCED = "NOT EVIDENCED"


class Question(NamedTuple):
    """One reviewer question and the public frameworks it maps to."""

    key: str
    number: int
    text: str
    frameworks: str


QUESTIONS: tuple[Question, ...] = (
    Question(
        "logging", 1,
        "Do you log every action the AI agent takes, including model calls, tool calls, and final outputs?",
        "EU AI Act Art. 12; NIST AI RMF MEASURE; SOC 2 CC7.2; HIPAA 45 CFR 164.312(b)",
    ),
    Question(
        "integrity", 2,
        "Are the agent logs tamper-evident, and can a third party verify them without trusting you?",
        "EU AI Act Art. 12; SOC 2 CC7.2; HIPAA 45 CFR 164.312(c)",
    ),
    Question(
        "anchoring", 3,
        "Is log existence and timing attested by an independent external party?",
        "EU AI Act Art. 12; NIST AI RMF GOVERN",
    ),
    Question(
        "scope", 4,
        "Is the agent's authorized goal and scope declared up front, and is behavior checked against it?",
        "OWASP ASI01, ASI03, ASI10; NIST AI RMF MAP",
    ),
    Question(
        "oversight", 5,
        "Can a human halt sensitive agent actions, and is human approval bound to a verified identity?",
        "EU AI Act Art. 14; NIST AI RMF MANAGE; OWASP ASI09",
    ),
    Question(
        "detection", 6,
        "Do you detect prompt injection, goal hijack, tool misuse, and data exfiltration in agent behavior?",
        "OWASP Top 10 for Agentic Applications ASI01 to ASI10; OWASP LLM01, LLM04, LLM06; SOC 2 CC7.3",
    ),
    Question(
        "data_handling", 7,
        "How are secrets, PII, and PHI kept out of the agent's logs?",
        "HIPAA 45 CFR 164.312; EU AI Act Art. 12; OWASP LLM06",
    ),
    Question(
        "attribution", 8,
        "Who is accountable for each agent session, and is that identity cryptographically bound to the record?",
        "EU AI Act Art. 14; NIST AI RMF GOVERN; SOC 2 CC7.3",
    ),
    Question(
        "review", 9,
        "Are the agent logs reviewed periodically, and is the review itself recorded?",
        "SOC 2 CC7.3; 21 CFR Part 11 11.10(e); EU Annex 11 section 9",
    ),
    Question(
        "key_custody", 10,
        "How are the signing keys behind the logs managed and rotated?",
        "NIST AI RMF GOVERN; SOC 2 CC7.2",
    ),
)

INTRO = (
    "This pack answers the questions an enterprise security review asks about an AI agent, "
    "with each answer drawn from the agent's own signed Intent Capsule chain rather than from "
    "policy documents. Every figure below was computed from the chain named in the header and "
    "can be recomputed by the reviewer with `air trace` and `air verify-public` using only "
    "public infrastructure."
)

SCOPE_BOUNDARY = (
    "This pack evidences what the recorded chain shows for the period covered. It is not a "
    "penetration test, a certification, or a statement about systems outside the chain. Where a "
    "control is marked NOT EVIDENCED, the chain contains no record of it; that is a finding about "
    "the evidence, not proof the control is absent. Answers marked as drafts must be reviewed and "
    "adapted by the vendor before submission."
)

VERIFY_INSTRUCTIONS = (
    "1. Obtain the chain file named in the header from the vendor.\n"
    "2. `pip install projectair` and run `air trace <chain>` to re-verify every signature and re-run the detectors.\n"
    "3. If anchors are present, run `air verify-public <chain>` to check the RFC 3161 timestamps and "
    "Sigstore Rekor inclusion proofs against public services with no vendor API in the path.\n"
    "4. Compare the figures you obtain with the ones in this pack."
)

REMEDIATION: dict[str, str] = {
    "anchoring": "Run `air anchor <chain>` or attach an `AnchoringOrchestrator` so chain roots are timestamped by an RFC 3161 TSA and logged in Sigstore Rekor.",
    "scope": "Construct the recorder with `intent_spec=IntentSpec(...)` or open the session with a `DelegationGrant` so the authorized scope is the first signed record.",
    "oversight": "Attach a `ContainmentPolicy` with `step_up_for_actions` and an `Auth0Verifier` so sensitive tools halt until a verified human approves.",
    "data_handling": "Use `CapturePolicy.phi_safe()` with a `ReferenceVault` so sensitive fields enter the chain as salted digests, never as plaintext.",
    "attribution": "Open each session with a `DelegationGrant` bound to an IdP-verified human, and route approvals through `AIRRecorder.approve()`.",
    "review": "Record periodic reviews with `AIRRecorder.record_audit_review()` so the review is itself a signed, IdP-verified record.",
    "key_custody": "Rotate with `rotate_signer()` so each key handoff is a signed `KEY_TRANSITION` record verifiable by `verify_key_custody()`.",
    "detection": "Register the agent in an `AgentRegistry` to enable the ASI03 and ASI10 Zero-Trust detectors alongside the fourteen that run unconditionally.",
}
