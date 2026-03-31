"""Risk score computation from scan findings."""

from vindicara.mcp.findings import Finding, RiskLevel
from vindicara.sdk.types import Severity

_SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.CRITICAL: 0.3,
    Severity.HIGH: 0.15,
    Severity.MEDIUM: 0.05,
    Severity.LOW: 0.02,
}

_SEVERITY_CAPS: dict[Severity, float] = {
    Severity.CRITICAL: 0.9,
    Severity.HIGH: 0.6,
    Severity.MEDIUM: 0.3,
    Severity.LOW: 0.1,
}


def compute_risk_score(findings: list[Finding]) -> float:
    if not findings:
        return 0.0
    by_severity: dict[Severity, float] = {}
    for f in findings:
        weight = _SEVERITY_WEIGHTS.get(f.severity, 0.02)
        cap = _SEVERITY_CAPS.get(f.severity, 0.1)
        current = by_severity.get(f.severity, 0.0)
        by_severity[f.severity] = min(current + weight, cap)
    total = sum(by_severity.values())
    return round(min(total, 1.0), 3)


def compute_risk_level(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.6:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
