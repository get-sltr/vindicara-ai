"""MCP scan orchestrator: coordinates static analysis and live probing."""

import time
import uuid
from datetime import UTC, datetime

import structlog

from vindicara.mcp.analyzer import analyze_config
from vindicara.mcp.findings import (
    Finding,
    Remediation,
    RiskLevel,
    ScanMode,
    ScanReport,
)
from vindicara.mcp.prober import probe_server
from vindicara.mcp.risk import compute_risk_level, compute_risk_score
from vindicara.sdk.types import Severity

logger = structlog.get_logger()


class MCPScanner:
    async def scan(
        self,
        server_url: str = "",
        config: dict[str, object] | None = None,
        mode: ScanMode = ScanMode.AUTO,
        timeout: float = 30.0,
        dry_run: bool = False,
    ) -> ScanReport:
        scan_id = str(uuid.uuid4())
        start = time.perf_counter()
        log = logger.bind(scan_id=scan_id, mode=mode, server_url=server_url)
        log.info("mcp.scan.started")

        if dry_run:
            log.info("mcp.scan.dry_run")
            return ScanReport(
                scan_id=scan_id,
                server_url=server_url,
                mode=mode,
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                findings=[],
                remediation=[],
                scan_duration_ms=0.0,
                timestamp=datetime.now(UTC).isoformat(),
            )

        findings: list[Finding] = []
        tools_discovered = 0

        run_static = mode in (ScanMode.STATIC, ScanMode.AUTO) and config is not None
        run_live = mode in (ScanMode.LIVE, ScanMode.AUTO) and server_url

        if run_static and config is not None:
            static_findings = analyze_config(config)
            findings.extend(static_findings)
            tools_raw = config.get("tools", [])
            if isinstance(tools_raw, list):
                tools_discovered = len(tools_raw)

        if run_live:
            live_findings = await probe_server(server_url, timeout=timeout)
            findings.extend(live_findings)

        risk_score = compute_risk_score(findings)
        risk_level = compute_risk_level(risk_score)
        remediation = _generate_remediation(findings)
        elapsed_ms = (time.perf_counter() - start) * 1000

        log.info(
            "mcp.scan.completed",
            findings_count=len(findings),
            risk_score=risk_score,
            risk_level=risk_level,
            duration_ms=round(elapsed_ms, 2),
        )

        return ScanReport(
            scan_id=scan_id,
            server_url=server_url,
            mode=mode,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            remediation=remediation,
            tools_discovered=tools_discovered,
            scan_duration_ms=round(elapsed_ms, 2),
            timestamp=datetime.now(UTC).isoformat(),
        )


def _generate_remediation(findings: list[Finding]) -> list[Remediation]:
    severity_priority = {
        Severity.CRITICAL: 1,
        Severity.HIGH: 2,
        Severity.MEDIUM: 3,
        Severity.LOW: 4,
    }

    sorted_findings = sorted(findings, key=lambda f: severity_priority.get(f.severity, 5))

    remediation: list[Remediation] = []
    for i, f in enumerate(sorted_findings):
        action = _remediation_action(f)
        if action:
            remediation.append(
                Remediation(
                    finding_id=f.finding_id,
                    priority=i + 1,
                    action=action,
                    reference=f"CWE: {f.cwe_id}" if f.cwe_id else "",
                )
            )
    return remediation


_REMEDIATION_MAP: dict[str, str] = {
    "STATIC-NO-AUTH": "Configure OAuth 2.0 with PKCE for all MCP server endpoints.",
    "STATIC-WEAK-AUTH": "Upgrade to OAuth 2.0 with PKCE and short-lived tokens. Remove static API keys and basic auth.",
    "STATIC-NO-RATELIMIT": "Add rate limiting (recommended: 60 requests/minute per agent). Use token bucket or sliding window.",
    "STATIC-EXCESS-TOOLS": "Split into focused MCP servers with smaller tool surfaces. Each server should serve one domain.",
    "LIVE-UNAUTH-ENUM": "Require authentication for tools/list endpoint. No tool should be discoverable without credentials.",
    "LIVE-NO-RATELIMIT": "Implement server-side rate limiting. Return HTTP 429 when limits are exceeded.",
}


def _remediation_action(finding: Finding) -> str:
    for prefix, action in _REMEDIATION_MAP.items():
        if finding.finding_id.startswith(prefix):
            return action
    if finding.category.value == "auth":
        return "Review and strengthen authentication configuration."
    if finding.category.value == "injection":
        return "Validate and sanitize all tool input parameters. Use allowlists over denylists."
    if finding.category.value == "permissions":
        return "Apply least privilege: scope tool permissions, use enums for constrained inputs."
    if finding.category.value == "data_leak":
        return "Suppress detailed error messages in production. Log internally, return generic errors to clients."
    return "Review and address this security finding."
