"""Tests for the MCP scan orchestrator."""

from unittest.mock import AsyncMock, patch

import pytest

from vindicara.mcp.findings import ScanMode
from vindicara.mcp.scanner import MCPScanner


class TestMCPScanner:
    @pytest.mark.asyncio
    async def test_static_scan(self) -> None:
        scanner = MCPScanner()
        config = {
            "tools": [
                {"name": "shell_exec", "description": "Run shell commands", "inputSchema": {}}
            ]
        }
        report = await scanner.scan(config=config, mode=ScanMode.STATIC)
        assert report.mode == ScanMode.STATIC
        assert report.risk_score > 0
        assert len(report.findings) > 0
        assert len(report.remediation) > 0
        assert report.scan_id != ""

    @pytest.mark.asyncio
    async def test_static_scan_clean_config(self) -> None:
        scanner = MCPScanner()
        config = {
            "tools": [{"name": "get_weather", "description": "Get weather", "inputSchema": {}}],
            "auth": {"type": "oauth2", "pkce": True},
            "rateLimit": {"maxRequestsPerMinute": 100},
        }
        report = await scanner.scan(config=config, mode=ScanMode.STATIC)
        assert report.risk_score < 0.3

    @pytest.mark.asyncio
    async def test_live_scan_with_mock(self) -> None:
        scanner = MCPScanner()
        with patch("vindicara.mcp.scanner.probe_server", new_callable=AsyncMock) as mock_probe:
            mock_probe.return_value = []
            report = await scanner.scan(server_url="https://mcp.test", mode=ScanMode.LIVE)
            assert report.mode == ScanMode.LIVE
            mock_probe.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_mode_with_url_and_config(self) -> None:
        scanner = MCPScanner()
        config = {"tools": [], "auth": {"type": "oauth2", "pkce": True}, "rateLimit": {"max": 100}}
        with patch("vindicara.mcp.scanner.probe_server", new_callable=AsyncMock) as mock_probe:
            mock_probe.return_value = []
            report = await scanner.scan(
                server_url="https://mcp.test", config=config, mode=ScanMode.AUTO
            )
            assert report.mode == ScanMode.AUTO
            mock_probe.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run(self) -> None:
        scanner = MCPScanner()
        report = await scanner.scan(server_url="https://mcp.test", mode=ScanMode.LIVE, dry_run=True)
        assert report.findings == []
        assert report.risk_score == 0.0

    @pytest.mark.asyncio
    async def test_remediation_generated(self) -> None:
        scanner = MCPScanner()
        config = {"tools": [{"name": "shell_exec", "description": "exec", "inputSchema": {}}]}
        report = await scanner.scan(config=config, mode=ScanMode.STATIC)
        assert len(report.remediation) >= 1
        assert report.remediation[0].priority >= 1
