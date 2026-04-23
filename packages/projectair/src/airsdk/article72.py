"""EU AI Act Article 72 post-market monitoring report generator.

Article 72 of Regulation (EU) 2024/1689 (the AI Act) requires providers of
high-risk AI systems to establish and document a post-market monitoring
system that actively and systematically collects, documents, and analyses
relevant data on the system's performance throughout its lifetime. The plan
forms part of the technical documentation required by Article 11.

This module takes a ``ForensicReport`` produced by ``air trace`` and emits
a Markdown report template populated with data from the signed Intent
Capsule chain: incident timeline, severity roll-up, chain-integrity
attestation, and placeholder structure for corrective actions and operator
sign-off.

The output is a populated template, not a filed compliance artefact.
Operators must review, adapt, supplement with deployer-contributed data
(per Article 72(2)), have a qualified person sign the attestation, and
consult counsel before relying on the report as evidence of Article 72
compliance or Article 73 serious-incident reporting.

Prose blocks live in ``_article72_content.py`` to keep this module focused
on orchestration and under the 300-line file limit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime

from airsdk._article72_content import (
    ATTESTATION_PARAGRAPH,
    CHAIN_FAIL_STATEMENT,
    CHAIN_OK_STATEMENT,
    CORRECTIVE_ACTIONS_PREAMBLE,
    DISCLAIMER,
    METHODOLOGY,
    SERIOUS_INCIDENT_PREAMBLE,
    SUMMARY_PARAGRAPH,
)
from airsdk.types import AgDRRecord, Finding, ForensicReport, VerificationStatus

SEVERITY_ORDER = ("critical", "high", "medium", "low")


def _timestamp_range(records: list[AgDRRecord]) -> tuple[str, str]:
    """Return (earliest, latest) timestamps from the chain, or ('', '') if empty."""
    timestamps = [r.timestamp for r in records if r.timestamp]
    if not timestamps:
        return ("", "")
    return (min(timestamps), max(timestamps))


def _unique_signer_keys(records: list[AgDRRecord]) -> list[str]:
    return sorted({r.signer_key for r in records if r.signer_key})


def _findings_by_severity(findings: list[Finding]) -> dict[str, list[Finding]]:
    buckets: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        buckets[finding.severity].append(finding)
    return buckets


def _format_finding_row(finding: Finding, record: AgDRRecord | None) -> str:
    timestamp = record.timestamp if record is not None else ""
    desc = finding.description.replace("|", "\\|").replace("\n", " ")
    return (
        f"| {finding.step_index} | {timestamp} | {finding.detector_id} | "
        f"{finding.severity} | {desc} |"
    )


def _render_findings_table(
    findings: list[Finding],
    records_by_id: dict[str, AgDRRecord],
    empty_message: str,
) -> str:
    if not findings:
        return empty_message
    rows = [
        "| Step | Timestamp (UTC) | Detector | Severity | Description |",
        "|---|---|---|---|---|",
    ]
    rows.extend(_format_finding_row(f, records_by_id.get(f.step_id)) for f in findings)
    return "\n".join(rows)


def _render_severity_rollup(severities: dict[str, list[Finding]]) -> str:
    lines: list[str] = []
    for severity in SEVERITY_ORDER:
        count = len(severities.get(severity, []))
        if count:
            lines.append(f"- **Findings of {severity} severity:** {count}")
    return "\n".join(lines)


def _render_detector_table(counts: Counter[str]) -> str:
    if not counts:
        return "No findings surfaced during this reporting period."
    rows = ["| Detector | Count |", "|---|---|"]
    rows.extend(f"| `{code}` | {counts[code]} |" for code in sorted(counts))
    return "\n".join(rows)


def generate_article72_report(
    report: ForensicReport,
    records: list[AgDRRecord],
    system_id: str,
    system_name: str = "[high-risk AI system name]",
    operator_entity: str = "[Provider / Operator entity]",
    monitoring_period: str = "[reporting period, e.g. 2026-Q3]",
) -> str:
    """Render a Markdown Article 72 post-market monitoring report template.

    The output is deterministic for a given input. Safe to diff across runs;
    regenerate whenever the underlying chain changes.
    """
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    earliest, latest = _timestamp_range(records)
    severities = _findings_by_severity(report.findings)
    detector_counts = Counter(f.detector_id for f in report.findings)
    signer_keys = _unique_signer_keys(records)
    verification = report.verification
    records_by_id = {r.step_id: r for r in records}

    chain_statement = (
        CHAIN_OK_STATEMENT
        if verification.status == VerificationStatus.OK
        else CHAIN_FAIL_STATEMENT
    )
    failure_row = (
        f"\n- **Failure step_id:** `{verification.failed_step_id}`"
        if verification.failed_step_id else ""
    )
    reason_row = f"\n- **Reason:** {verification.reason}" if verification.reason else ""
    time_range_line = (
        f"- **Observed time range:** {earliest} to {latest} (UTC)\n"
        if earliest and latest else ""
    )
    severity_rollup = _render_severity_rollup(severities)
    severity_rollup_block = f"\n{severity_rollup}" if severity_rollup else ""
    signer_display = (
        ", ".join(f"`{k[:16]}...`" for k in signer_keys) if signer_keys else "(none)"
    )
    critical_table = _render_findings_table(
        severities.get("critical", []), records_by_id,
        "No critical-severity findings in this reporting period.",
    )
    high_table = _render_findings_table(
        severities.get("high", []), records_by_id,
        "No high-severity findings in this reporting period.",
    )
    full_table = _render_findings_table(
        report.findings, records_by_id, "No findings in this reporting period."
    )
    detector_table = _render_detector_table(detector_counts)
    attestation = ATTESTATION_PARAGRAPH.format(air_version=report.air_version)

    return f"""# EU AI Act Article 72 Post-Market Monitoring Report

**System:** {system_name}
**System ID:** `{system_id}`
**Provider / Operator:** {operator_entity}
**Reporting period:** {monitoring_period}
**Report generated:** {generated_at}
**Source log:** `{report.source_log}`
**Project AIR version:** {report.air_version}

> {DISCLAIMER}

---

## 1. Executive Summary

{SUMMARY_PARAGRAPH}

- **Records analysed:** {report.records}
- **Conversations / sessions:** {report.conversations}
{time_range_line}- **Chain integrity:** {verification.status.value.upper()}
- **Records cryptographically verified:** {verification.records_verified}
- **Unique signing keys observed:** {len(signer_keys)}
- **Total findings:** {len(report.findings)}{severity_rollup_block}

---

## 2. System Identification (Article 11 Annex IV)

| Field | Value |
|---|---|
| System identifier | `{system_id}` |
| System name | {system_name} |
| Provider / Operator | {operator_entity} |
| Monitoring period | {monitoring_period} |
| Monitoring system | Project AIR signed Intent Capsule chain (AgDR format v0.2) |
| Log file (chain source) | `{report.source_log}` |
| Signing keys (Ed25519 public keys, hex) | {signer_display} |

---

## 3. Monitoring Methodology

{METHODOLOGY}

---

## 4. Chain-Integrity Attestation

- **Verification status:** `{verification.status.value}`
- **Records verified:** {verification.records_verified}{failure_row}{reason_row}

{chain_statement}

---

## 5. Detector Findings Summary

{detector_table}

---

## 6. Serious-Incident Candidates (Article 73 cross-reference)

{SERIOUS_INCIDENT_PREAMBLE}

{critical_table}

---

## 7. High-Severity Findings

{high_table}

---

## 8. Corrective Actions

{CORRECTIVE_ACTIONS_PREAMBLE}

| Finding (step, detector) | Action taken | Owner | Status | Completion date |
|---|---|---|---|---|
| [step_index] [detector_id] | [description] | [owner] | [open/in progress/closed] | [date] |

---

## 9. Attestation

{attestation}

| Field | Value |
|---|---|
| Name | [Full name] |
| Title | [Role, e.g. DPO / Compliance Officer / CTO] |
| Entity | [Provider entity] |
| Date | [YYYY-MM-DD] |
| Signature | [signature] |

---

## Appendix A: Full Finding List

{full_table}
"""
