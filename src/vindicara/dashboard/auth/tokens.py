"""JWT token creation, validation, and CSRF."""

import secrets
from datetime import UTC, datetime, timedelta

import jwt
import structlog

from vindicara.config.settings import VindicaraSettings

logger = structlog.get_logger()

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7
CSRF_TOKEN_BYTES = 32

_SECRET: str | None = None


def _get_secret() -> str:
    global _SECRET
    if _SECRET is None:
        settings = VindicaraSettings()
        _SECRET = settings.jwt_secret if settings.jwt_secret else secrets.token_hex(32)
    return _SECRET


def _reset_secret_for_tests() -> None:
    global _SECRET
    _SECRET = None


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def create_refresh_token(user_id: str, session_id: str) -> str:
    payload = {
        "sub": user_id,
        "sid": session_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def create_csrf_token() -> str:
    return secrets.token_hex(CSRF_TOKEN_BYTES)


def decode_token(token: str) -> dict[str, str]:
    if not token:
        return {}
    try:
        payload: dict[str, str] = jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.info("auth.token.expired")
        return {}
    except jwt.InvalidTokenError as exc:
        logger.warning("auth.token.invalid", error=str(exc))
        return {}


def verify_csrf(cookie_token: str, header_token: str) -> bool:
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(cookie_token, header_token)
