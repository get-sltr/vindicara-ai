"""Forensic report export adapters.

Each export writes the same ForensicReport to a different consumer surface:
- json  - canonical machine-readable artifact, consumed by downstream tools.
- pdf   - human-readable incident summary for legal, insurance, exec stakeholders.
- siem  - ArcSight CEF v0, one event per finding, ready for SIEM ingestion.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from airsdk.types import Finding, ForensicReport, VerificationStatus

# ---------- JSON ----------

def export_json(report: ForensicReport, path: str | Path) -> Path:
    """Write the full ForensicReport as pretty-printed JSON."""
    out = Path(path)
    out.write_text(report.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    return out


# ---------- PDF ----------

_SEVERITY_TO_RGB = {
    "critical": (220, 38, 38),
    "high": (202, 138, 4),
    "medium": (14, 165, 233),
    "low": (120, 120, 120),
}


def _ascii_safe(text: str) -> str:
    """fpdf2's core font set is latin-1. Strip to ASCII-safe chars for body text."""
    return text.encode("ascii", errors="replace").decode("ascii")


def _pdf_section_header(pdf: FPDF, title: str) -> None:
    pdf.set_font("helvetica", style="B", size=13)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)
    pdf.cell(0, 7, _ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
    pdf.ln(3)


def _pdf_kv(pdf: FPDF, key: str, value: str) -> None:
    pdf.set_font("helvetica", style="B", size=10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(40, 5, _ascii_safe(f"{key}:"))
    pdf.set_font("helvetica", style="", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5, _ascii_safe(value), new_x="LMARGIN", new_y="NEXT")


def _pdf_finding(pdf: FPDF, finding: Finding) -> None:
    color = _SEVERITY_TO_RGB.get(finding.severity, (0, 0, 0))
    pdf.set_font("helvetica", style="B", size=10)
    pdf.set_text_color(*color)
    pdf.cell(
        0, 5,
        _ascii_safe(f"[{finding.severity.upper()}] {finding.asi_id} {finding.title} (step {finding.step_index})"),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("helvetica", style="", size=9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4.5, _ascii_safe(finding.description), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", style="I", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, _ascii_safe(f"step_id: {finding.step_id}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def export_pdf(report: ForensicReport, path: str | Path) -> Path:
    """Render the ForensicReport as a human-readable PDF.

    Layout is intentionally plain: stakeholders reading this are auditors,
    lawyers, insurance carriers, and executives. They want to scan, not admire.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", style="B", size=18)
    pdf.cell(0, 10, "AIR Forensic Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", style="", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, _ascii_safe(f"Project AIR v{report.air_version}  |  report {report.report_id}"), new_x="LMARGIN", new_y="NEXT")

    _pdf_section_header(pdf, "Source")
    _pdf_kv(pdf, "Log file", report.source_log)
    _pdf_kv(pdf, "Generated at", report.generated_at)
    _pdf_kv(pdf, "Agent steps", str(report.records))
    _pdf_kv(pdf, "Conversations", str(report.conversations))

    _pdf_section_header(pdf, "Signature verification")
    status_color = (16, 160, 16) if report.verification.status == VerificationStatus.OK else (220, 38, 38)
    pdf.set_font("helvetica", style="B", size=11)
    pdf.set_text_color(*status_color)
    pdf.cell(0, 6, _ascii_safe(report.verification.status.value.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", style="", size=10)
    pdf.set_text_color(0, 0, 0)
    _pdf_kv(pdf, "Records verified", str(report.verification.records_verified))
    if report.verification.reason:
        _pdf_kv(pdf, "Reason", report.verification.reason)
    if report.verification.failed_step_id:
        _pdf_kv(pdf, "Failed step_id", report.verification.failed_step_id)

    _pdf_section_header(pdf, f"Findings ({len(report.findings)})")
    if not report.findings:
        pdf.set_font("helvetica", style="I", size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "No detector findings on this trace.", new_x="LMARGIN", new_y="NEXT")
    else:
        for finding in report.findings:
            _pdf_finding(pdf, finding)

    _pdf_section_header(pdf, "Detector coverage")
    pdf.set_font("helvetica", style="", size=9)
    pdf.set_text_color(0, 0, 0)
    for line in (
        "ASI01 Agent Goal Hijack    implemented",
        "ASI02 Tool Misuse          implemented",
        "ASI03 Prompt Injection     implemented",
        "ASI04 Memory Poisoning     not yet implemented",
        "ASI05 Sensitive Data       not yet implemented",
        "ASI06 Excessive Agency     not yet implemented",
        "ASI07 Resource Exhaustion  not yet implemented",
        "ASI08 Plan Corruption      not yet implemented",
        "ASI09 Supply Chain / MCP   not yet implemented",
        "ASI10 Untraceable Action   not yet implemented",
    ):
        pdf.cell(0, 4.5, _ascii_safe(line), new_x="LMARGIN", new_y="NEXT")

    out = Path(path)
    pdf.output(str(out))
    return out


# ---------- SIEM (CEF) ----------

CEF_VERSION = 0
CEF_VENDOR = "Vindicara"
CEF_PRODUCT = "AIR"


# CEF severity is 0..10. Map from our textual severity.
_CEF_SEVERITY = {
    "critical": 10,
    "high": 8,
    "medium": 5,
    "low": 3,
}


def _cef_escape(value: str) -> str:
    """CEF requires backslash, pipe and equals in values to be escaped."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("=", "\\=")


def _cef_extension_escape(value: str) -> str:
    """Inside the extension dictionary, equals and newline need escaping."""
    return value.replace("\\", "\\\\").replace("=", "\\=").replace("\n", "\\n").replace("\r", "")


def _finding_to_cef(finding: Finding, report: ForensicReport) -> str:
    severity = _CEF_SEVERITY.get(finding.severity, 5)
    header = "|".join([
        f"CEF:{CEF_VERSION}",
        _cef_escape(CEF_VENDOR),
        _cef_escape(CEF_PRODUCT),
        _cef_escape(report.air_version),
        _cef_escape(finding.asi_id),
        _cef_escape(finding.title),
        str(severity),
    ])
    extensions = {
        "rt": report.generated_at,
        "cs1": finding.step_id,
        "cs1Label": "step_id",
        "cs2": str(finding.step_index),
        "cs2Label": "step_index",
        "cs3": report.report_id,
        "cs3Label": "report_id",
        "cs4": report.source_log,
        "cs4Label": "source_log",
        "msg": finding.description,
        "cat": finding.severity,
    }
    body = " ".join(f"{k}={_cef_extension_escape(v)}" for k, v in extensions.items())
    return f"{header}|{body}"


def _verification_event(report: ForensicReport) -> str:
    """Emit a meta event for the chain verification status itself."""
    ok = report.verification.status == VerificationStatus.OK
    severity = 1 if ok else 10
    title = f"Chain verification: {report.verification.status.value}"
    header = "|".join([
        f"CEF:{CEF_VERSION}",
        _cef_escape(CEF_VENDOR),
        _cef_escape(CEF_PRODUCT),
        _cef_escape(report.air_version),
        "AIR-VERIFY",
        _cef_escape(title),
        str(severity),
    ])
    extensions: dict[str, str] = {
        "rt": report.generated_at,
        "cs1": report.report_id,
        "cs1Label": "report_id",
        "cs2": str(report.verification.records_verified),
        "cs2Label": "records_verified",
        "cs3": report.source_log,
        "cs3Label": "source_log",
        "cs4": str(report.records),
        "cs4Label": "total_records",
        "msg": report.verification.reason or "All signatures valid.",
        "cat": "verification",
    }
    if report.verification.failed_step_id:
        extensions["cs5"] = report.verification.failed_step_id
        extensions["cs5Label"] = "failed_step_id"
    body = " ".join(f"{k}={_cef_extension_escape(v)}" for k, v in extensions.items())
    return f"{header}|{body}"


def export_siem(report: ForensicReport, path: str | Path) -> Path:
    """Write the ForensicReport as ArcSight CEF v0, one event per line.

    Format: one verification meta-event followed by one event per finding.
    Compatible with Splunk, Sumo, QRadar, Datadog, and any SIEM that speaks CEF.
    """
    lines = [_verification_event(report)]
    for finding in report.findings:
        lines.append(_finding_to_cef(finding, report))
    out = Path(path)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
