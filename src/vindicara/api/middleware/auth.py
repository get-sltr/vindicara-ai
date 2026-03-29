"""API key authentication middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from vindicara.config.constants import API_KEY_HEADER, API_KEY_PREFIX

_PUBLIC_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get(API_KEY_HEADER, "")
        if not api_key or not api_key.startswith(API_KEY_PREFIX):
            return JSONResponse(
                status_code=401,
                content={"detail": f"Missing or invalid API key. Provide via {API_KEY_HEADER} header."},
            )

        request.state.api_key = api_key
        return await call_next(request)
