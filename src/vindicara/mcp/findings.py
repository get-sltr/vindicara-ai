"""MCP scan data models: findings, remediation, scan reports."""

from enum import StrEnum

from pydantic import BaseModel, Field

from vindicara.sdk.types import Severity


class ScanMode(StrEnum):
    STATIC = "static"
    LIVE = "live"
    AUTO = "auto"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(StrEnum):
    AUTH = "auth"
    PERMISSIONS = "permissions"
    INJECTION = "injection"
    RATE_LIMIT = "rate_limit"
    CONFIG = "config"
    DATA_LEAK = "data_leak"


class Finding(BaseModel):
    finding_id: str
    category: FindingCategory
    severity: Severity
    title: str
    description: str
    evidence: str = ""
    cwe_id: str = ""


class Remediation(BaseModel):
    finding_id: str
    priority: int
    action: str
    reference: str = ""


class ScanRequest(BaseModel):
    server_url: str = ""
    config: dict[str, object] = Field(default_factory=dict)
    mode: ScanMode = ScanMode.AUTO
    timeout_seconds: float = 30.0
    dry_run: bool = False


class ScanReport(BaseModel):
    scan_id: str
    server_url: str = ""
    mode: ScanMode
    risk_score: float
    risk_level: RiskLevel
    findings: list[Finding] = Field(default_factory=list)
    remediation: list[Remediation] = Field(default_factory=list)
    tools_discovered: int = 0
    scan_duration_ms: float = 0.0
    timestamp: str = ""
