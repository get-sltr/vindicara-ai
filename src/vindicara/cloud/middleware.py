"""ASGI middleware that authenticates AIR Cloud requests.

Accepts two credential forms on protected routes:

- ``X-API-Key: <key>`` -- SDK and agent ingestion; looked up in the
  configured :class:`ApiKeyStore`.
- ``Authorization: Bearer <token>`` -- dashboard session tokens issued
  by ``vindicara.cloud.session_token.create_session_token``; verified
  with ``verify_session_token``.

On success ``request.state.workspace_id``, ``request.state.api_key_id``,
and ``request.state.role`` are set so downstream routes scope their
queries to the right tenant. On failure the request is rejected with 401
before it touches a route.

Routes that are public (health, OpenAPI docs) are listed in
``UNAUTHED_PATHS``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from vindicara.cloud.session_token import SessionTokenError, verify_session_token

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.types import ASGIApp

    from vindicara.cloud.workspace import ApiKeyStore

UNAUTHED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/ready",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
        # /v1/sso/login is the authentication step itself; it cannot require
        # an API key because the caller does not have one yet.
        "/v1/sso/login",
        # /v1/identity/register is first-run lead capture; a fresh installer
        # has no API key yet, so it must be public.
        "/v1/identity/register",
        # /v1/auth/exchange is self-serve sign-in: the caller trades an
        # identity-provider token for its first AIR Cloud credential.
        "/v1/auth/exchange",
    }
)

API_KEY_HEADER = "X-API-Key"
# projectair 1.3.x HTTPTransport sent the key under this name; accept it so
# an SDK already in the field keeps working after the server moves on.
LEGACY_API_KEY_HEADER = "X-Vindicara-Key"

# Routes that carry their own operator admin-token gate
# (vindicara.cloud.admin.require_admin) instead of API-key / session auth.
# They must bypass the middleware's API-key check because a first-time
# workspace bootstrap has no tenant key yet. The route itself fails closed
# when no admin token is configured.
ADMIN_GATED_ROUTES: frozenset[tuple[str, str]] = frozenset({("POST", "/v1/workspaces")})


class AirCloudAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate every non-public AIR Cloud request.

    Accepts ``X-API-Key`` (SDK/agent ingestion) or
    ``Authorization: Bearer <session-token>`` (dashboard). The middleware
    reads the configured :class:`ApiKeyStore` from
    ``app.state.cloud_api_keys``; if the store is missing it returns 503
    (the service is misconfigured, not the caller's fault). On a
    successful auth check ``request.state.workspace_id`` is populated and
    the downstream handler runs.
    """

    def __init__(self, app: ASGIApp, *, prefix: str = "/v1") -> None:
        super().__init__(app)
        self._prefix = prefix

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "OPTIONS":
            return Response(status_code=200)
        path = request.url.path
        if path in UNAUTHED_PATHS:
            return await call_next(request)
        if not path.startswith(self._prefix):
            return await call_next(request)
        if (request.method, path) in ADMIN_GATED_ROUTES:
            # Operator admin-token routes enforce their own gate downstream.
            return await call_next(request)

        store: ApiKeyStore | None = getattr(request.app.state, "cloud_api_keys", None)
        if store is None:
            return JSONResponse(
                {"detail": "AIR Cloud not configured: no api-key store"},
                status_code=503,
            )

        api_key_header = request.headers.get(API_KEY_HEADER) or request.headers.get(LEGACY_API_KEY_HEADER)
        bearer_header = request.headers.get("Authorization", "")

        if api_key_header:
            api_key = store.lookup(api_key_header)
            if api_key is None:
                return JSONResponse({"detail": "invalid or revoked api key"}, status_code=401)
            request.state.workspace_id = api_key.workspace_id
            request.state.api_key_id = api_key.key_id
            request.state.role = api_key.role
        elif bearer_header.startswith("Bearer "):
            raw_token = bearer_header[7:]
            try:
                claims = verify_session_token(raw_token)
            except SessionTokenError:
                return JSONResponse({"detail": "invalid or expired session token"}, status_code=401)
            request.state.workspace_id = claims.workspace_id
            request.state.api_key_id = claims.key_id
            request.state.role = claims.role
        else:
            return JSONResponse(
                {"detail": "missing X-API-Key or Authorization header"},
                status_code=401,
            )

        return await call_next(request)


__all__ = [
    "ADMIN_GATED_ROUTES",
    "API_KEY_HEADER",
    "UNAUTHED_PATHS",
    "AirCloudAuthMiddleware",
]
