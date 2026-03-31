"""Tests for risk scoring."""

from vindicara.mcp.findings import Finding, FindingCategory, RiskLevel
from vindicara.mcp.risk import compute_risk_level, compute_risk_score
from vindicara.sdk.types import Severity


class TestRiskScore:
    def test_no_findings(self) -> None:
        assert compute_risk_score([]) == 0.0

    def test_single_critical(self) -> None:
        findings = [
            Finding(finding_id="a", category=FindingCategory.AUTH, severity=Severity.CRITICAL, title="t", description="d")
        ]
        score = compute_risk_score(findings)
        assert 0.25 <= score <= 0.35

    def test_multiple_critical_caps(self) -> None:
        findings = [
            Finding(finding_id=f"c{i}", category=FindingCategory.AUTH, severity=Severity.CRITICAL, title="t", description="d")
            for i in range(5)
        ]
        score = compute_risk_score(findings)
        assert score <= 1.0

    def test_mixed_severities(self) -> None:
        findings = [
            Finding(finding_id="c1", category=FindingCategory.AUTH, severity=Severity.CRITICAL, title="t", description="d"),
            Finding(finding_id="h1", category=FindingCategory.PERMISSIONS, severity=Severity.HIGH, title="t", description="d"),
            Finding(finding_id="m1", category=FindingCategory.RATE_LIMIT, severity=Severity.MEDIUM, title="t", description="d"),
        ]
        score = compute_risk_score(findings)
        assert 0.4 <= score <= 0.6

    def test_low_only(self) -> None:
        findings = [
            Finding(finding_id="l1", category=FindingCategory.CONFIG, severity=Severity.LOW, title="t", description="d")
        ]
        score = compute_risk_score(findings)
        assert score <= 0.1


class TestRiskLevel:
    def test_low(self) -> None:
        assert compute_risk_level(0.1) == RiskLevel.LOW

    def test_medium(self) -> None:
        assert compute_risk_level(0.45) == RiskLevel.MEDIUM

    def test_high(self) -> None:
        assert compute_risk_level(0.7) == RiskLevel.HIGH

    def test_critical(self) -> None:
        assert compute_risk_level(0.9) == RiskLevel.CRITICAL
