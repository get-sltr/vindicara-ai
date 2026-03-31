"""MCP JSON-RPC client over HTTP for scanner probes."""

import json

import httpx
import structlog

logger = structlog.get_logger()

SCANNER_USER_AGENT = "Vindicara-MCP-Scanner/0.1.0"


class MCPTransportError(Exception):
    def __init__(self, message: str, status_code: int = 0) -> None:
        self.status_code = status_code
        super().__init__(message)


class MCPClient:
    def __init__(
        self,
        server_url: str,
        timeout: float = 10.0,
        auth_header: str = "",
    ) -> None:
        self._server_url = server_url.rstrip("/")
        self._timeout = timeout
        self._auth_header = auth_header
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _build_headers(self, include_auth: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": SCANNER_USER_AGENT,
        }
        if include_auth and self._auth_header:
            headers["Authorization"] = self._auth_header
        return headers

    def _build_request(
        self, method: str, params: dict[str, object] | None = None
    ) -> dict[str, object]:
        req: dict[str, object] = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            req["params"] = params
        return req

    async def send(
        self,
        method: str,
        params: dict[str, object] | None = None,
        include_auth: bool = True,
    ) -> "MCPResponse":
        payload = self._build_request(method, params)
        headers = self._build_headers(include_auth)
        log = logger.bind(method=method, url=self._server_url)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    self._server_url,
                    json=payload,
                    headers=headers,
                )
                log.info("mcp.transport.response", status=resp.status_code)
                return MCPResponse(
                    status_code=resp.status_code,
                    body=resp.text,
                    headers=dict(resp.headers),
                )
        except httpx.TimeoutException:
            log.warning("mcp.transport.timeout")
            return MCPResponse(status_code=0, body="", headers={}, timed_out=True)
        except httpx.ConnectError as exc:
            log.warning("mcp.transport.connect_error", error=str(exc))
            return MCPResponse(status_code=0, body=str(exc), headers={}, connection_failed=True)


class MCPResponse:
    def __init__(
        self,
        status_code: int,
        body: str,
        headers: dict[str, str],
        timed_out: bool = False,
        connection_failed: bool = False,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers
        self.timed_out = timed_out
        self.connection_failed = connection_failed

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def json_body(self) -> dict[str, object]:
        try:
            parsed = json.loads(self.body)
            if isinstance(parsed, dict):
                return parsed
            return {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def has_result(self) -> bool:
        return "result" in self.json_body

    @property
    def has_error(self) -> bool:
        return "error" in self.json_body

    @property
    def result(self) -> object:
        return self.json_body.get("result")

    @property
    def error_message(self) -> str:
        err = self.json_body.get("error")
        if isinstance(err, dict):
            return str(err.get("message", ""))
        return ""

    @property
    def reveals_internals(self) -> bool:
        body_lower = self.body.lower()
        leak_patterns = [
            "traceback",
            "stack trace",
            "at line",
            'file "/',
            "exception in",
            "/usr/",
            "/home/",
            "/var/",
            "node_modules",
            "site-packages",
        ]
        return any(p in body_lower for p in leak_patterns)
