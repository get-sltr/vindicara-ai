"""Live active probing of MCP servers."""

import asyncio

import structlog

from vindicara.mcp.findings import Finding, FindingCategory
from vindicara.mcp.transport import MCPClient, MCPResponse
from vindicara.sdk.types import Severity

logger = structlog.get_logger()

_INJECTION_PAYLOADS = [
    ("path_traversal", "../../etc/passwd"),
    ("command_injection", "; ls -la /"),
    ("sql_injection", "' OR 1=1 --"),
    ("template_injection", "{{7*7}}"),
]

_INJECTION_SUCCESS_INDICATORS = [
    "root:x:0",
    "total ",
    "drwx",
    "49",
    "rows affected",
    "SELECT",
]

_AUTH_BYPASS_TOKENS = [
    ("empty", "Bearer "),
    ("null", "Bearer null"),
    ("undefined", "Bearer undefined"),
]

_RATE_LIMIT_BURST = 20
_OVERSIZE_PAYLOAD_LENGTH = 1_000_000
_SCAN_TEST_MARKER = "VINDICARA_SCAN_TEST_00000"


def _create_client(server_url: str, timeout: float, auth_header: str = "") -> MCPClient:
    return MCPClient(server_url=server_url, timeout=timeout, auth_header=auth_header)


async def probe_server(
    server_url: str,
    timeout: float = 10.0,
) -> list[Finding]:
    findings: list[Finding] = []
    client = _create_client(server_url, timeout)

    tools = await _probe_unauth_enumeration(client, findings)
    await _probe_auth_bypass(client, findings)
    await _probe_rate_limiting(client, findings)
    if tools:
        await _probe_input_injection(client, tools, findings)
        await _probe_oversized_input(client, tools, findings)

    return findings


async def _probe_unauth_enumeration(
    client: MCPClient,
    findings: list[Finding],
) -> list[dict[str, object]]:
    resp = await client.send("tools/list", include_auth=False)
    tools: list[dict[str, object]] = []

    if resp.is_success and resp.has_result:
        result = resp.result
        if isinstance(result, dict):
            raw_tools = result.get("tools", [])
            if isinstance(raw_tools, list):
                tools = raw_tools

        if tools:
            findings.append(
                Finding(
                    finding_id="LIVE-UNAUTH-ENUM",
                    category=FindingCategory.AUTH,
                    severity=Severity.CRITICAL,
                    title="Unauthenticated tool enumeration",
                    description=f"Server returned {len(tools)} tools without authentication.",
                    evidence=f"tools/list returned {len(tools)} tools with no auth header",
                    cwe_id="CWE-306",
                )
            )
    return tools


async def _probe_auth_bypass(
    client: MCPClient,
    findings: list[Finding],
) -> None:
    for label, token in _AUTH_BYPASS_TOKENS:
        bypass_client = _create_client(client._server_url, client._timeout, auth_header=token)
        resp = await bypass_client.send("tools/list")
        if resp.is_success and resp.has_result:
            findings.append(
                Finding(
                    finding_id=f"LIVE-AUTH-BYPASS-{label}",
                    category=FindingCategory.AUTH,
                    severity=Severity.CRITICAL,
                    title=f"Auth bypass: {label} token accepted",
                    description=f"Server accepted a '{label}' authorization token and returned tool data.",
                    evidence=f"Authorization: {token} returned 200 with result",
                    cwe_id="CWE-287",
                )
            )


async def _probe_rate_limiting(
    client: MCPClient,
    findings: list[Finding],
) -> None:
    tasks = [client.send("tools/list") for _ in range(_RATE_LIMIT_BURST)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    valid_responses = [r for r in responses if isinstance(r, MCPResponse)]
    throttled = [r for r in valid_responses if r.status_code == 429]

    if len(throttled) == 0 and len(valid_responses) == _RATE_LIMIT_BURST:
        findings.append(
            Finding(
                finding_id="LIVE-NO-RATELIMIT",
                category=FindingCategory.RATE_LIMIT,
                severity=Severity.MEDIUM,
                title="No rate limiting detected",
                description=f"Sent {_RATE_LIMIT_BURST} requests in rapid succession. All succeeded with no 429 responses.",
                evidence=f"{_RATE_LIMIT_BURST}/{_RATE_LIMIT_BURST} requests succeeded, 0 throttled",
                cwe_id="CWE-770",
            )
        )


async def _probe_input_injection(
    client: MCPClient,
    tools: list[dict[str, object]],
    findings: list[Finding],
) -> None:
    target_tool = tools[0] if tools else None
    if not target_tool:
        return

    tool_name = str(target_tool.get("name", "unknown"))

    for payload_type, payload in _INJECTION_PAYLOADS:
        resp = await client.send(
            "tools/call",
            params={
                "name": tool_name,
                "arguments": {"input": payload, "_scan_marker": _SCAN_TEST_MARKER},
            },
        )

        if resp.is_success and resp.has_result:
            result_str = str(resp.result).lower()
            for indicator in _INJECTION_SUCCESS_INDICATORS:
                if indicator.lower() in result_str:
                    findings.append(
                        Finding(
                            finding_id=f"LIVE-INJECTION-{payload_type}-{tool_name}",
                            category=FindingCategory.INJECTION,
                            severity=Severity.CRITICAL,
                            title=f"Input injection succeeded: {payload_type} on {tool_name}",
                            description=f"Tool '{tool_name}' processed a {payload_type} payload and returned suspicious output.",
                            evidence=f"Payload: {payload}, Response contained: {indicator}",
                            cwe_id="CWE-74",
                        )
                    )
                    break

        if resp.reveals_internals:
            findings.append(
                Finding(
                    finding_id=f"LIVE-INFO-LEAK-{payload_type}-{tool_name}",
                    category=FindingCategory.DATA_LEAK,
                    severity=Severity.HIGH,
                    title=f"Server internals leaked via {payload_type} on {tool_name}",
                    description=f"Adversarial input to '{tool_name}' caused an error response that reveals server internals.",
                    evidence=f"Response body (truncated): {resp.body[:300]}",
                    cwe_id="CWE-209",
                )
            )


async def _probe_oversized_input(
    client: MCPClient,
    tools: list[dict[str, object]],
    findings: list[Finding],
) -> None:
    target_tool = tools[0] if tools else None
    if not target_tool:
        return

    tool_name = str(target_tool.get("name", "unknown"))
    oversized = "A" * _OVERSIZE_PAYLOAD_LENGTH

    resp = await client.send(
        "tools/call",
        params={
            "name": tool_name,
            "arguments": {"input": oversized, "_scan_marker": _SCAN_TEST_MARKER},
        },
    )

    if resp.timed_out:
        findings.append(
            Finding(
                finding_id=f"LIVE-OVERSIZE-DOS-{tool_name}",
                category=FindingCategory.RATE_LIMIT,
                severity=Severity.HIGH,
                title=f"Potential DoS via oversized input: {tool_name}",
                description=f"Sending a 1MB payload to '{tool_name}' caused a timeout.",
                evidence="Request timed out with 1MB payload",
                cwe_id="CWE-400",
            )
        )
    elif resp.is_success:
        findings.append(
            Finding(
                finding_id=f"LIVE-OVERSIZE-ACCEPTED-{tool_name}",
                category=FindingCategory.CONFIG,
                severity=Severity.MEDIUM,
                title=f"No input size validation: {tool_name}",
                description=f"Tool '{tool_name}' accepted a 1MB input payload without rejection.",
                evidence="1MB payload accepted and processed",
                cwe_id="CWE-770",
            )
        )
