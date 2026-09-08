"""AI agent security-review evidence pack (beta).

The moment a vendor's sale is blocked is an enterprise security questionnaire
asking how the AI agent is logged, whether the logs can be trusted, and
whether a human can stop it. This module answers those questions from the
agent's own signed Intent Capsule chain: it computes a status per question,
lists the evidence, and drafts an answer the vendor can paste, with every
figure recomputable by the reviewer.

``assess_security_review`` returns the structured assessment (used by the CLI
for the free status preview); ``generate_security_review_report`` renders the
full Markdown pack. Evidence extraction lives in ``_security_review_assess.py``
and question text in ``_security_review_content.py``.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from airsdk._compat import UTC
from airsdk._security_review_assess import QuestionResult, assess_security_review, timestamp_range
from airsdk._security_review_content import (
    INTRO,
    READINESS,
    REMEDIATION,
    SCOPE_BOUNDARY,
    STATUS_EVIDENCED,
    STATUS_NOT_EVIDENCED,
    STATUS_PARTIAL,
    VERIFY_INSTRUCTIONS,
)
from airsdk.types import AgDRRecord, Finding, ForensicReport

__all__ = [
    "STATUS_EVIDENCED",
    "STATUS_NOT_EVIDENCED",
    "STATUS_PARTIAL",
    "QuestionResult",
    "assess_security_review",
    "generate_security_review_report",
]


def _render_question(result: QuestionResult) -> str:
    q = result.question
    lines = [f"### {q.number}. {q.text}", "", f"- **Status:** {result.status}", f"- **Frameworks:** {q.frameworks}"]
    lines += [f"- **Evidence:** {result.evidence[0]}"] + [f"  - {line}" for line in result.evidence[1:]]
    lines += ["", f"**Draft answer.** {result.answer}"]
    if result.status != STATUS_EVIDENCED and q.key in REMEDIATION:
        lines += ["", f"**To evidence this:** {REMEDIATION[q.key]}"]
    return "\n".join(lines) + "\n"


def _render_findings(findings: list[Finding]) -> str:
    if not findings:
        return "No detector findings in this chain.\n"
    rows = [f"| {f.detector_id} | {f.severity} | {f.step_index} | {f.title} |" for f in findings]
    return "| Detector | Severity | Step | Title |\n|---|---|---|---|\n" + "\n".join(rows) + "\n"


def generate_security_review_report(
    report: ForensicReport,
    records: list[AgDRRecord],
    *,
    vendor: str = "[Vendor]",
    system_name: str = "[AI agent / system name]",
) -> str:
    """Render the full Markdown evidence pack for ``records``."""
    results = assess_security_review(records, report.findings, report.verification.status)
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    earliest, latest = timestamp_range(records)
    counts = Counter(r.status for r in results)
    summary_rows = "\n".join(f"| {r.question.number} | {r.question.text} | {r.status} |" for r in results)
    return f"""# AI Agent Security Review Evidence Pack

**Vendor:** {vendor}
**System:** {system_name}
**Source chain:** `{report.source_log}`
**Records:** {report.records}  **Period:** {earliest or '(none)'} to {latest or '(none)'} (UTC)
**Chain verification:** {report.verification.status.value}
**Generated:** {generated_at}  **AIR version:** {report.air_version}  **Readiness:** {READINESS}

{INTRO}

> **Scope boundary.** {SCOPE_BOUNDARY}

## Summary

{counts.get(STATUS_EVIDENCED, 0)} evidenced, {counts.get(STATUS_PARTIAL, 0)} partial, {counts.get(STATUS_NOT_EVIDENCED, 0)} not evidenced.

| # | Question | Status |
|---|---|---|
{summary_rows}

## Questions and evidence

{"".join(_render_question(r) + chr(10) for r in results)}## Appendix A: detector findings in this chain

{_render_findings(report.findings)}
## Appendix B: how the reviewer verifies this pack

{VERIFY_INSTRUCTIONS}
"""
