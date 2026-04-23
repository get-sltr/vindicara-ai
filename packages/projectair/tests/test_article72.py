"""Article 72 post-market monitoring report generator."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from airsdk.article72 import generate_article72_report
from airsdk.types import (
    AgDRPayload,
    AgDRRecord,
    Finding,
    ForensicReport,
    StepKind,
    VerificationResult,
    VerificationStatus,
)

DUMMY_HASH = "0" * 64
DUMMY_SIG = "aa" * 64
DUMMY_KEY = "bb" * 32


def _record(
    kind: StepKind = StepKind.LLM_START,
    step_id: str = "test-step-1",
    timestamp: str = "2026-04-21T12:00:00Z",
    **payload_fields: object,
) -> AgDRRecord:
    return AgDRRecord(
        step_id=step_id,
        timestamp=timestamp,
        kind=kind,
        payload=AgDRPayload.model_validate(payload_fields),
        prev_hash=DUMMY_HASH,
        content_hash=DUMMY_HASH,
        signature=DUMMY_SIG,
        signer_key=DUMMY_KEY,
    )


def _report(
    findings: list[Finding] | None = None,
    verification_status: VerificationStatus = VerificationStatus.OK,
    verification_reason: str | None = None,
    verification_failed_step_id: str | None = None,
    records: int = 1,
) -> ForensicReport:
    return ForensicReport(
        air_version="0.3.0",
        report_id=str(uuid4()),
        source_log="/var/log/air/test-fixture.log",
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        records=records,
        conversations=1,
        verification=VerificationResult(
            status=verification_status,
            records_verified=records,
            reason=verification_reason,
            failed_step_id=verification_failed_step_id,
        ),
        findings=findings or [],
    )


def _finding(
    detector_id: str = "ASI01",
    severity: str = "high",
    step_id: str = "test-step-1",
    description: str = "test",
) -> Finding:
    return Finding(
        detector_id=detector_id,
        title=f"{detector_id} test",
        severity=severity,
        step_id=step_id,
        step_index=0,
        description=description,
    )


def test_article72_renders_header_with_system_identity() -> None:
    records = [_record()]
    report = _report(records=1)
    out = generate_article72_report(
        report, records, "sys-001",
        system_name="Sales Assist",
        operator_entity="Acme EU",
        monitoring_period="2026-Q3",
    )
    assert "# EU AI Act Article 72 Post-Market Monitoring Report" in out
    assert "**System:** Sales Assist" in out
    assert "**System ID:** `sys-001`" in out
    assert "**Provider / Operator:** Acme EU" in out
    assert "**Reporting period:** 2026-Q3" in out


def test_article72_includes_disclaimer_prominently() -> None:
    out = generate_article72_report(_report(), [_record()], "sys-001")
    assert "INFORMATIONAL TEMPLATE, NOT LEGAL ADVICE" in out
    assert "consult counsel" in out


def test_article72_chain_ok_emits_ok_statement() -> None:
    records = [_record()]
    out = generate_article72_report(
        _report(verification_status=VerificationStatus.OK, records=1),
        records, "sys-001",
    )
    assert "chain verified cleanly" in out.lower()
    assert "`ok`" in out.lower()


def test_article72_chain_tampered_emits_failure_warning() -> None:
    records = [_record()]
    out = generate_article72_report(
        _report(
            verification_status=VerificationStatus.TAMPERED,
            verification_reason="signature mismatch at step 3",
            verification_failed_step_id="test-step-3",
            records=1,
        ),
        records, "sys-001",
    )
    assert "Chain verification did not complete successfully" in out
    assert "signature mismatch at step 3" in out
    assert "`test-step-3`" in out


def test_article72_critical_findings_surfaced_as_serious_incident_candidates() -> None:
    findings = [
        _finding("ASI03", "critical", description="identity forgery"),
        _finding("ASI02", "high", description="shell injection"),
    ]
    records = [_record()]
    out = generate_article72_report(_report(findings=findings, records=1), records, "sys-001")
    assert "Serious-Incident Candidates" in out
    assert "Article 3(49)" in out
    assert "identity forgery" in out
    # high-severity findings appear in their own section, not as serious-incident candidates
    assert "shell injection" in out


def test_article72_empty_findings_emits_no_findings_messages() -> None:
    records = [_record()]
    out = generate_article72_report(_report(findings=[], records=1), records, "sys-001")
    assert "No findings surfaced during this reporting period." in out
    assert "No critical-severity findings" in out
    assert "No high-severity findings" in out
    assert "No findings in this reporting period." in out


def test_article72_severity_rollup_counts_findings_by_severity() -> None:
    findings = [
        _finding("ASI03", "critical"),
        _finding("ASI03", "critical"),
        _finding("ASI02", "high"),
        _finding("ASI07", "medium"),
    ]
    records = [_record()]
    out = generate_article72_report(_report(findings=findings, records=1), records, "sys-001")
    assert "**Findings of critical severity:** 2" in out
    assert "**Findings of high severity:** 1" in out
    assert "**Findings of medium severity:** 1" in out


def test_article72_detector_summary_table_groups_by_detector() -> None:
    findings = [
        _finding("ASI03"),
        _finding("ASI03"),
        _finding("ASI10"),
    ]
    records = [_record()]
    out = generate_article72_report(_report(findings=findings, records=1), records, "sys-001")
    assert "| `ASI03` | 2 |" in out
    assert "| `ASI10` | 1 |" in out


def test_article72_observed_time_range_reflects_first_and_last_record() -> None:
    records = [
        _record(step_id="s1", timestamp="2026-04-01T08:00:00Z"),
        _record(step_id="s2", timestamp="2026-04-05T23:59:59Z"),
        _record(step_id="s3", timestamp="2026-04-03T12:00:00Z"),
    ]
    out = generate_article72_report(_report(records=3), records, "sys-001")
    assert "2026-04-01T08:00:00Z to 2026-04-05T23:59:59Z" in out


def test_article72_attestation_references_air_version() -> None:
    out = generate_article72_report(_report(), [_record()], "sys-001")
    assert "`air trace`, v0.3.0" in out


def test_article72_appendix_contains_every_finding() -> None:
    findings = [
        _finding("ASI01", "high", step_id="s1", description="goal hijack"),
        _finding("ASI07", "medium", step_id="s2", description="missing nonce"),
    ]
    records = [_record(step_id="s1"), _record(step_id="s2")]
    out = generate_article72_report(_report(findings=findings, records=2), records, "sys-001")
    appendix_start = out.find("## Appendix A: Full Finding List")
    assert appendix_start > 0
    appendix = out[appendix_start:]
    assert "goal hijack" in appendix
    assert "missing nonce" in appendix


def test_article72_appendix_escapes_pipe_characters_in_descriptions() -> None:
    """Pipe characters in a description would break the markdown table layout."""
    findings = [
        _finding(description="tool called with arg: foo | bar pipe"),
    ]
    records = [_record()]
    out = generate_article72_report(_report(findings=findings, records=1), records, "sys-001")
    # Escaped form survives in the output
    assert "foo \\| bar pipe" in out


def test_article72_output_is_deterministic_modulo_generation_timestamp() -> None:
    """Two runs with the same inputs differ only in the `Report generated` line."""
    records = [_record()]
    report = _report(records=1)
    a = generate_article72_report(report, records, "sys-001")
    b = generate_article72_report(report, records, "sys-001")
    # Strip the generated-at timestamps before comparison.
    def strip_ts(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines() if not line.startswith("**Report generated:**")
        )
    assert strip_ts(a) == strip_ts(b)


def test_article72_signer_keys_deduped_and_truncated_in_header() -> None:
    key_a = "a" * 64
    key_b = "b" * 64
    r1 = AgDRRecord(
        step_id="s1",
        timestamp="2026-04-21T12:00:00Z",
        kind=StepKind.LLM_START,
        payload=AgDRPayload(prompt="hi"),
        prev_hash=DUMMY_HASH,
        content_hash=DUMMY_HASH,
        signature=DUMMY_SIG,
        signer_key=key_a,
    )
    r2 = AgDRRecord(
        step_id="s2",
        timestamp="2026-04-21T12:01:00Z",
        kind=StepKind.LLM_END,
        payload=AgDRPayload(response="ok"),
        prev_hash=DUMMY_HASH,
        content_hash=DUMMY_HASH,
        signature=DUMMY_SIG,
        signer_key=key_b,
    )
    r3 = AgDRRecord(
        step_id="s3",
        timestamp="2026-04-21T12:02:00Z",
        kind=StepKind.LLM_END,
        payload=AgDRPayload(response="again"),
        prev_hash=DUMMY_HASH,
        content_hash=DUMMY_HASH,
        signature=DUMMY_SIG,
        signer_key=key_a,  # same as r1
    )
    out = generate_article72_report(_report(records=3), [r1, r2, r3], "sys-001")
    assert "**Unique signing keys observed:** 2" in out
    assert f"`{key_a[:16]}...`" in out
    assert f"`{key_b[:16]}...`" in out


def test_article72_defaults_placeholder_for_missing_fields() -> None:
    """When operator/system-name/period are not supplied, placeholder text appears."""
    out = generate_article72_report(_report(), [_record()], "sys-001")
    assert "[high-risk AI system name]" in out
    assert "[Provider / Operator entity]" in out
    assert "[reporting period" in out
