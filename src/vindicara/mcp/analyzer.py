"""Static analysis of MCP server configurations."""

import re

from vindicara.mcp.findings import Finding, FindingCategory
from vindicara.sdk.types import Severity

_DANGEROUS_PATTERNS = re.compile(
    r"(?i)(shell_exec|eval|exec|run_command|execute_sql|raw_query|file_write|file_delete|"
    r"rm_rf|drop_table|system_call|subprocess|os_command)"
)

_WRITE_DELETE_PATTERNS = re.compile(
    r"(?i)(delete|remove|drop|write|update|modify|create|insert|put|post|patch|destroy|purge)"
)

_DESCRIPTION_INJECTION_PATTERNS = re.compile(
    r"(?i)(always call this|ignore other|ignore previous|call this first|"
    r"you must use|do not use any other|override|disregard)"
)

_BROAD_INPUT_PATTERNS = re.compile(
    r"(?i)(query|sql|command|script|code|expression|eval|shell|exec)"
)

_MAX_TOOLS_THRESHOLD = 25


def analyze_config(config: dict[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    tools = _get_tools(config)
    findings.extend(_check_dangerous_tools(tools))
    findings.extend(_check_missing_auth(config))
    findings.extend(_check_weak_auth(config))
    findings.extend(_check_overprivileged_tools(tools))
    findings.extend(_check_broad_input_schemas(tools))
    findings.extend(_check_description_injection(tools))
    findings.extend(_check_missing_rate_limit(config))
    findings.extend(_check_excessive_tools(tools))
    return findings


def _get_tools(config: dict[str, object]) -> list[dict[str, object]]:
    tools = config.get("tools", [])
    if isinstance(tools, list):
        return tools
    return []


def _check_dangerous_tools(tools: list[dict[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        desc = str(tool.get("description", ""))
        combined = f"{name} {desc}"
        if _DANGEROUS_PATTERNS.search(combined):
            findings.append(
                Finding(
                    finding_id=f"STATIC-DANGER-{name}",
                    category=FindingCategory.PERMISSIONS,
                    severity=Severity.CRITICAL,
                    title=f"Dangerous tool detected: {name}",
                    description=f"Tool '{name}' matches a dangerous execution pattern. "
                    f"Tools that execute arbitrary code, shell commands, or raw SQL are high-risk attack vectors.",
                    evidence=f"Tool name/description matched pattern: {combined[:200]}",
                    cwe_id="CWE-78",
                )
            )
    return findings


def _check_missing_auth(config: dict[str, object]) -> list[Finding]:
    auth = config.get("auth")
    if not auth:
        return [
            Finding(
                finding_id="STATIC-NO-AUTH",
                category=FindingCategory.AUTH,
                severity=Severity.CRITICAL,
                title="No authentication configured",
                description="Server config declares no authentication mechanism. Any agent or attacker can invoke tools without credentials.",
                cwe_id="CWE-306",
            )
        ]
    return []


def _check_weak_auth(config: dict[str, object]) -> list[Finding]:
    auth = config.get("auth")
    if not auth or not isinstance(auth, dict):
        return []
    auth_type = str(auth.get("type", "")).lower()
    if auth_type == "basic":
        return [
            Finding(
                finding_id="STATIC-WEAK-AUTH",
                category=FindingCategory.AUTH,
                severity=Severity.HIGH,
                title="Weak authentication: HTTP Basic Auth",
                description="Basic auth transmits credentials in base64 (not encrypted). Use OAuth 2.0 with PKCE instead.",
                cwe_id="CWE-522",
            )
        ]
    if auth_type == "oauth2" and not auth.get("pkce"):
        return [
            Finding(
                finding_id="STATIC-WEAK-AUTH",
                category=FindingCategory.AUTH,
                severity=Severity.HIGH,
                title="OAuth 2.0 without PKCE",
                description="OAuth without PKCE is vulnerable to authorization code interception. Enable PKCE.",
                cwe_id="CWE-345",
            )
        ]
    if auth_type in ("api_key", "apikey", "static_token"):
        return [
            Finding(
                finding_id="STATIC-WEAK-AUTH",
                category=FindingCategory.AUTH,
                severity=Severity.HIGH,
                title="Static API key authentication",
                description="Static API keys cannot be scoped per-agent, rotated automatically, or revoked granularly. Use OAuth 2.0.",
                cwe_id="CWE-798",
            )
        ]
    return []


def _check_overprivileged_tools(tools: list[dict[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        if not _WRITE_DELETE_PATTERNS.search(name):
            continue
        schema = tool.get("inputSchema", {})
        if not isinstance(schema, dict):
            continue
        props = schema.get("properties", {})
        if not isinstance(props, dict):
            continue
        unconstrained = []
        for param_name, param_def in props.items():
            if not isinstance(param_def, dict):
                continue
            if param_def.get("type") == "string" and "enum" not in param_def:
                unconstrained.append(param_name)
        if unconstrained:
            findings.append(
                Finding(
                    finding_id=f"STATIC-OVERPRIV-{name}",
                    category=FindingCategory.PERMISSIONS,
                    severity=Severity.HIGH,
                    title=f"Overprivileged tool: {name}",
                    description=f"Write/delete tool '{name}' has unconstrained string parameters: {', '.join(unconstrained)}.",
                    evidence=f"Unconstrained params: {unconstrained}",
                    cwe_id="CWE-269",
                )
            )
    return findings


def _check_broad_input_schemas(tools: list[dict[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        schema = tool.get("inputSchema", {})
        if not isinstance(schema, dict):
            continue
        props = schema.get("properties", {})
        if not isinstance(props, dict):
            continue
        for param_name, param_def in props.items():
            if not isinstance(param_def, dict):
                continue
            if (
                param_def.get("type") == "string"
                and _BROAD_INPUT_PATTERNS.search(param_name)
                and "enum" not in param_def
                and "pattern" not in param_def
            ):
                findings.append(
                    Finding(
                        finding_id=f"STATIC-BROAD-INPUT-{name}-{param_name}",
                        category=FindingCategory.INJECTION,
                        severity=Severity.MEDIUM,
                        title=f"Broad input schema: {name}.{param_name}",
                        description=f"Parameter '{param_name}' in tool '{name}' accepts unconstrained strings for a sensitive field.",
                        cwe_id="CWE-20",
                    )
                )
    return findings


def _check_description_injection(tools: list[dict[str, object]]) -> list[Finding]:
    findings: list[Finding] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        desc = str(tool.get("description", ""))
        if _DESCRIPTION_INJECTION_PATTERNS.search(desc):
            findings.append(
                Finding(
                    finding_id=f"STATIC-DESC-INJECT-{name}",
                    category=FindingCategory.INJECTION,
                    severity=Severity.HIGH,
                    title=f"Tool description injection: {name}",
                    description=f"Tool '{name}' has a description containing prompt-like instructions that could manipulate agent behavior.",
                    evidence=f"Description: {desc[:200]}",
                    cwe_id="CWE-74",
                )
            )
    return findings


def _check_missing_rate_limit(config: dict[str, object]) -> list[Finding]:
    rate_limit = config.get("rateLimit") or config.get("rate_limit")
    if not rate_limit:
        return [
            Finding(
                finding_id="STATIC-NO-RATELIMIT",
                category=FindingCategory.RATE_LIMIT,
                severity=Severity.MEDIUM,
                title="No rate limiting configured",
                description="Server config declares no rate limiting. Agents can overwhelm the server or exfiltrate data at high speed.",
                cwe_id="CWE-770",
            )
        ]
    return []


def _check_excessive_tools(tools: list[dict[str, object]]) -> list[Finding]:
    if len(tools) > _MAX_TOOLS_THRESHOLD:
        return [
            Finding(
                finding_id="STATIC-EXCESS-TOOLS",
                category=FindingCategory.CONFIG,
                severity=Severity.LOW,
                title=f"Excessive tool count: {len(tools)} tools",
                description=f"Server exposes {len(tools)} tools (threshold: {_MAX_TOOLS_THRESHOLD}). Consider splitting into focused MCP servers.",
            )
        ]
    return []
