"""Tests for live MCP probing with mocked transport."""

from unittest.mock import AsyncMock, patch

import pytest

from vindicara.mcp.findings import FindingCategory
from vindicara.mcp.prober import probe_server
from vindicara.mcp.transport import MCPResponse
from vindicara.sdk.types import Severity


def _make_response(
    status_code: int = 200,
    body: str = '{"jsonrpc":"2.0","id":1,"result":{}}',
    headers: dict[str, str] | None = None,
    timed_out: bool = False,
) -> MCPResponse:
    return MCPResponse(
        status_code=status_code,
        body=body,
        headers=headers or {},
        timed_out=timed_out,
    )


def _tools_list_response(tools: list[dict[str, str]] | None = None) -> MCPResponse:
    if tools is None:
        tools = [{"name": "get_data", "description": "Get data"}]
    import json

    return _make_response(body=json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": tools}}))


class TestUnauthEnumeration:
    @pytest.mark.asyncio
    async def test_detects_unauth_tool_listing(self) -> None:
        mock_client = AsyncMock()
        mock_client.send = AsyncMock(return_value=_tools_list_response())

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        unauth = [f for f in findings if f.finding_id == "LIVE-UNAUTH-ENUM"]
        assert len(unauth) == 1
        assert unauth[0].severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_no_finding_when_auth_required(self) -> None:
        mock_client = AsyncMock()
        mock_client.send = AsyncMock(
            return_value=_make_response(status_code=401, body="Unauthorized")
        )

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        unauth = [f for f in findings if f.finding_id == "LIVE-UNAUTH-ENUM"]
        assert len(unauth) == 0


class TestAuthBypass:
    @pytest.mark.asyncio
    async def test_detects_empty_token_bypass(self) -> None:
        call_count = 0

        async def mock_send(
            method: str, params: object = None, include_auth: bool = True
        ) -> MCPResponse:
            nonlocal call_count
            call_count += 1
            if not include_auth:
                return _make_response(status_code=401)
            return _tools_list_response()

        mock_client = AsyncMock()
        mock_client.send = mock_send

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        bypass = [f for f in findings if f.finding_id.startswith("LIVE-AUTH-BYPASS")]
        assert len(bypass) >= 1


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_detects_no_rate_limit(self) -> None:
        mock_client = AsyncMock()
        mock_client.send = AsyncMock(return_value=_make_response())

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        rl = [f for f in findings if f.finding_id == "LIVE-NO-RATELIMIT"]
        assert len(rl) == 1
        assert rl[0].severity == Severity.MEDIUM

    @pytest.mark.asyncio
    async def test_no_finding_when_throttled(self) -> None:
        call_count = 0

        async def rate_limited_send(
            method: str, params: object = None, include_auth: bool = True
        ) -> MCPResponse:
            nonlocal call_count
            call_count += 1
            if call_count > 10:
                return _make_response(status_code=429, body="Rate limited")
            return _make_response()

        mock_client = AsyncMock()
        mock_client.send = rate_limited_send

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        rl = [f for f in findings if f.finding_id == "LIVE-NO-RATELIMIT"]
        assert len(rl) == 0


class TestInputInjection:
    @pytest.mark.asyncio
    async def test_detects_path_traversal_success(self) -> None:
        async def injection_send(
            method: str, params: object = None, include_auth: bool = True
        ) -> MCPResponse:
            if method == "tools/list":
                return _tools_list_response([{"name": "read_file", "description": "Read a file"}])
            if method == "tools/call":
                return _make_response(
                    body='{"jsonrpc":"2.0","id":1,"result":{"content":"root:x:0:0"}}'
                )
            return _make_response()

        mock_client = AsyncMock()
        mock_client.send = injection_send

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        inj = [
            f
            for f in findings
            if f.category == FindingCategory.INJECTION and "LIVE" in f.finding_id
        ]
        assert len(inj) >= 1


class TestOversizedInput:
    @pytest.mark.asyncio
    async def test_detects_no_size_validation(self) -> None:
        async def oversize_send(
            method: str, params: object = None, include_auth: bool = True
        ) -> MCPResponse:
            if method == "tools/list":
                return _tools_list_response([{"name": "echo", "description": "Echo input"}])
            return _make_response()

        mock_client = AsyncMock()
        mock_client.send = oversize_send

        with patch("vindicara.mcp.prober._create_client", return_value=mock_client):
            findings = await probe_server("https://mcp.test", timeout=5.0)

        oversize = [f for f in findings if f.finding_id.startswith("LIVE-OVERSIZE")]
        assert len(oversize) >= 1
