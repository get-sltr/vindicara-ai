"""Tests for MCP scan models."""

from vindicara.mcp.findings import (
    Finding,
    FindingCategory,
    Remediation,
    RiskLevel,
    ScanMode,
    ScanReport,
)
from vindicara.sdk.types import Severity


class TestFinding:
    def test_create_finding(self) -> None:
        f = Finding(
            finding_id="auth-001",
            category=FindingCategory.AUTH,
            severity=Severity.CRITICAL,
            title="No authentication configured",
            description="Server accepts unauthenticated requests",
            evidence="tools/list returned 5 tools without auth",
        )
        assert f.severity == Severity.CRITICAL
        assert f.category == FindingCategory.AUTH

    def test_finding_with_cwe(self) -> None:
        f = Finding(
            finding_id="inj-001",
            category=FindingCategory.INJECTION,
            severity=Severity.CRITICAL,
            title="SQL injection in query tool",
            description="Tool parameter accepts raw SQL",
            cwe_id="CWE-89",
        )
        assert f.cwe_id == "CWE-89"


class TestScanReport:
    def test_empty_report(self) -> None:
        report = ScanReport(
            scan_id="test-001",
            mode=ScanMode.STATIC,
            risk_score=0.0,
            risk_level=RiskLevel.LOW,
            findings=[],
            remediation=[],
            tools_discovered=0,
            scan_duration_ms=5.0,
            timestamp="2026-03-31T00:00:00Z",
        )
        assert report.risk_score == 0.0
        assert report.risk_level == RiskLevel.LOW

    def test_report_with_findings(self) -> None:
        finding = Finding(
            finding_id="auth-001",
            category=FindingCategory.AUTH,
            severity=Severity.CRITICAL,
            title="No auth",
            description="No auth",
        )
        remediation = Remediation(
            finding_id="auth-001",
            priority=1,
            action="Configure OAuth 2.0 with PKCE",
        )
        report = ScanReport(
            scan_id="test-002",
            mode=ScanMode.LIVE,
            risk_score=0.85,
            risk_level=RiskLevel.CRITICAL,
            findings=[finding],
            remediation=[remediation],
            tools_discovered=5,
            scan_duration_ms=1200.0,
            timestamp="2026-03-31T00:00:00Z",
        )
        assert len(report.findings) == 1
        assert report.remediation[0].priority == 1
