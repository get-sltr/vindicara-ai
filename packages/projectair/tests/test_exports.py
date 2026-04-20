"""Export adapter tests: JSON, PDF, SIEM/CEF."""
from __future__ import annotations

from pathlib import Path

import pytest

from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.types import (
    Finding,
    ForensicReport,
    VerificationResult,
    VerificationStatus,
)


def _sample_report(findings: list[Finding] | None = None) -> ForensicReport:
    return ForensicReport(
        air_version="0.1.3",
        report_id="report-abc-123",
        source_log="./demo.log",
        generated_at="2026-04-20T12:00:00Z",
        records=13,
        conversations=1,
        verification=VerificationResult(status=VerificationStatus.OK, records_verified=13),
        findings=findings if findings is not None else [
            Finding(
                asi_id="ASI01",
                title="Agent Goal Hijack",
                severity="high",
                step_id="019da999-0000-7000-8000-aaaaaaaaaaaa",
                step_index=6,
                description="Tool admin_delete_records called with low overlap.",
            ),
            Finding(
                asi_id="ASI02",
                title="Tool Misuse",
                severity="critical",
                step_id="019da999-0000-7000-8000-bbbbbbbbbbbb",
                step_index=10,
                description="shell_exec invoked with shell metacharacters.",
            ),
        ],
    )


# ---------- JSON ----------

def test_export_json_roundtrips(tmp_path: Path) -> None:
    out = export_json(_sample_report(), tmp_path / "r.json")
    assert out.exists()
    text = out.read_text()
    assert '"ASI01"' in text
    assert '"records_verified": 13' in text


# ---------- PDF ----------

def test_export_pdf_writes_a_pdf_file(tmp_path: Path) -> None:
    out = export_pdf(_sample_report(), tmp_path / "r.pdf")
    assert out.exists()
    assert out.stat().st_size > 500  # minimum plausible PDF size
    header = out.read_bytes()[:8]
    assert header.startswith(b"%PDF-"), f"not a PDF: {header!r}"


def test_export_pdf_handles_empty_findings(tmp_path: Path) -> None:
    out = export_pdf(_sample_report(findings=[]), tmp_path / "clean.pdf")
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF-")


def test_export_pdf_handles_verification_failure(tmp_path: Path) -> None:
    report = _sample_report()
    report = report.model_copy(update={
        "verification": VerificationResult(
            status=VerificationStatus.TAMPERED,
            records_verified=5,
            failed_step_id="019da999-ffff-7000-8000-dead",
            reason="content_hash mismatch",
        ),
    })
    out = export_pdf(report, tmp_path / "tampered.pdf")
    assert out.read_bytes().startswith(b"%PDF-")


# ---------- SIEM / CEF ----------

def test_export_siem_produces_cef_lines(tmp_path: Path) -> None:
    out = export_siem(_sample_report(), tmp_path / "r.siem")
    lines = out.read_text().strip().splitlines()
    # One meta verification event + one per finding.
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("CEF:0|Vindicara|AIR|")


def test_export_siem_header_fields_correct(tmp_path: Path) -> None:
    out = export_siem(_sample_report(), tmp_path / "r.siem")
    lines = out.read_text().strip().splitlines()
    verify_line = lines[0]
    finding1 = lines[1]
    # CEF header has 7 pipe-separated fields before the extension block.
    assert verify_line.split("|")[4] == "AIR-VERIFY"
    assert finding1.split("|")[4] == "ASI01"
    # Severity mapping
    assert finding1.split("|")[6].split(" ", 1)[0] == "8"  # "high"


def test_export_siem_escapes_pipes_and_equals(tmp_path: Path) -> None:
    report = _sample_report(findings=[
        Finding(
            asi_id="ASI02",
            title="Tool | with = in fields",
            severity="critical",
            step_id="019da999-0000-7000-8000-cccccccccccc",
            step_index=1,
            description="args=|cat /etc/passwd",
        ),
    ])
    out = export_siem(report, tmp_path / "escaped.siem")
    text = out.read_text()
    # Header escapes: title has pipe and equals escaped.
    assert "Tool \\| with \\= in fields" in text
    # Extension escapes: equals inside a value becomes \=, but pipes are allowed
    # inside extension values per the ArcSight CEF spec.
    assert "msg=args\\=|cat /etc/passwd" in text


def test_export_siem_verification_event_severity_on_tamper(tmp_path: Path) -> None:
    report = _sample_report()
    report = report.model_copy(update={
        "verification": VerificationResult(
            status=VerificationStatus.TAMPERED,
            records_verified=5,
            failed_step_id="019da999-ffff-7000-8000-dead",
            reason="content_hash mismatch",
        ),
    })
    out = export_siem(report, tmp_path / "tampered.siem")
    verify_line = out.read_text().strip().splitlines()[0]
    # Tamper => severity 10
    assert verify_line.rsplit("|", 1)[0].endswith("|10")


def test_export_notimplementederror_still_catchable_at_boundary(tmp_path: Path) -> None:
    """Sanity: exports no longer raise NotImplementedError for pdf/siem."""
    with pytest.raises(NotImplementedError):  # type: ignore[unreachable]
        raise NotImplementedError("sanity check")
    # Confirm real exports return paths, not exceptions.
    assert export_pdf(_sample_report(), tmp_path / "ok.pdf").exists()
    assert export_siem(_sample_report(), tmp_path / "ok.siem").exists()
