"""Prose content blocks for the Article 72 report generator.

Separated from ``article72.py`` so the generator logic stays under the
300-line file limit. These strings are legally-precise template copy; edit
with care and prefer whitespace-level edits over content changes without
review.
"""
from __future__ import annotations

DISCLAIMER = (
    "**INFORMATIONAL TEMPLATE, NOT LEGAL ADVICE.** This report is a populated "
    "template generated from a Project AIR signed forensic chain. It is "
    "intended as a starting point for Article 72 post-market monitoring "
    "evidence, not a filed compliance artefact. The provider must review the "
    "contents, adapt them to their high-risk AI system context, incorporate "
    "deployer-contributed data per Article 72(2), have a qualified person "
    "execute the attestation, and consult counsel qualified in the applicable "
    "jurisdiction before relying on this document as evidence of Article 72 "
    "compliance or for any filing under Article 73 (reporting of serious "
    "incidents)."
)

METHODOLOGY = (
    "Every agent action (LLM call, tool invocation, inter-agent message, "
    "final output) produces an append-only signed record. Each record is "
    "content-hashed with BLAKE3 and signed with Ed25519 (RFC 8032); the "
    "signature binds the record to the previous record's hash, producing a "
    "forward-chained audit log in which any alteration, insertion, deletion, "
    "or reordering is detected deterministically by replay. The open-source "
    "verifier `air trace` reproduces the verification offline using only the "
    "log file and the signer's public key. Detector coverage spans the OWASP "
    "Top 10 for Agentic Applications (10 of 10 in v0.3.0), three OWASP Top 10 "
    "for LLM Applications categories (prompt injection, sensitive data "
    "exposure, unrestricted resource consumption), and one AIR-native "
    "chain-integrity check."
)

CHAIN_OK_STATEMENT = (
    "The chain verified cleanly. Every record's BLAKE3 content hash was "
    "recomputed from its canonicalised payload and matched; every record's "
    "Ed25519 signature verified against its declared public key; and every "
    "record's `prev_hash` matched the previous record's content hash. The "
    "forensic chain is tamper-evident and has not been altered since "
    "production."
)

CHAIN_FAIL_STATEMENT = (
    "**Chain verification did not complete successfully.** The log is either "
    "tampered, truncated, or malformed. Investigate before relying on the "
    "records below as evidence. Preserve the original log file for forensic "
    "analysis."
)

SERIOUS_INCIDENT_PREAMBLE = (
    "Under Article 3(49), a 'serious incident' is an incident or "
    "malfunctioning of an AI system that directly or indirectly leads to "
    "death or serious health harm, irreversible disruption of critical "
    "infrastructure, infringement of fundamental-rights obligations, or "
    "serious harm to property or the environment. Article 73 requires "
    "providers to report such incidents to the market surveillance authority "
    "within the deadlines set out in Article 73(2)-(4).\n\n"
    "**The findings below are candidates for Article 73 classification, not "
    "automatic serious incidents.** Severity 'critical' indicates a high-risk "
    "pattern detected in the chain; the provider must assess each finding "
    "against the Article 3(49) criteria to determine whether it constitutes a "
    "serious incident, a malfunction, or a detected-and-mitigated deviation."
)

CORRECTIVE_ACTIONS_PREAMBLE = (
    "Article 72 requires providers to act on the monitoring data they "
    "collect. For each finding above, document the corrective action the "
    "provider has taken or plans to take. Examples: tightening an agent's "
    "permitted_tools list, rotating a compromised signing key, updating a "
    "policy to catch a bypass pattern, pausing the system pending a fix."
)

SUMMARY_PARAGRAPH = (
    "This report documents the post-market monitoring activity for the "
    "above-identified high-risk AI system over the stated reporting period, "
    "collected from a signed Intent Capsule chain produced by Project AIR "
    "(BLAKE3 content hashing + Ed25519 signatures + forward hash chain). See "
    "`vindicara.io/admissibility` for the cryptographic architecture and its "
    "mapping to evidentiary frameworks."
)

ATTESTATION_PARAGRAPH = (
    "I, the undersigned qualified person for the above-identified provider, "
    "attest that the monitoring data summarised in this report was collected "
    "from the Project AIR signed Intent Capsule chain identified above in the "
    "regular course of the provider's operation of the high-risk AI system, "
    "that the chain verified cleanly using the open-source Project AIR "
    "verifier (`air trace`, v{air_version}), and that the findings and "
    "corrective actions recorded above are a true and correct record of the "
    "post-market monitoring activity for the reporting period."
)
