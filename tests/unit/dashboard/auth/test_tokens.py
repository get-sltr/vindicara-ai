"""Unit tests for JWT token module."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from vindicara.dashboard.auth import tokens


@pytest.fixture(autouse=True)
def reset_secret_cache() -> None:
    tokens._reset_secret_for_tests()


def test_secret_is_stable_across_calls() -> None:
    first = tokens._get_secret()
    second = tokens._get_secret()
    assert first == second
    assert len(first) >= 32


def test_access_token_round_trip() -> None:
    token = tokens.create_access_token("user_abc", "x@example.com")
    payload = tokens.decode_token(token)
    assert payload["sub"] == "user_abc"
    assert payload["email"] == "x@example.com"
    assert payload["type"] == "access"


def test_refresh_token_round_trip() -> None:
    token = tokens.create_refresh_token("user_abc", "sess_xyz")
    payload = tokens.decode_token(token)
    assert payload["sub"] == "user_abc"
    assert payload["sid"] == "sess_xyz"
    assert payload["type"] == "refresh"


def test_decode_empty_token_returns_empty_dict() -> None:
    assert tokens.decode_token("") == {}


def test_decode_invalid_token_returns_empty_dict() -> None:
    assert tokens.decode_token("not-a-real-jwt") == {}


def test_decode_expired_token_returns_empty_dict() -> None:
    payload = {
        "sub": "user_abc",
        "email": "x@example.com",
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
        "iat": datetime.now(UTC) - timedelta(hours=1),
    }
    expired = jwt.encode(payload, tokens._get_secret(), algorithm=tokens.ALGORITHM)
    assert tokens.decode_token(expired) == {}


def test_csrf_verify_requires_match() -> None:
    token = tokens.create_csrf_token()
    assert tokens.verify_csrf(token, token) is True
    assert tokens.verify_csrf(token, "other") is False
    assert tokens.verify_csrf("", token) is False
    assert tokens.verify_csrf(token, "") is False


def test_csrf_tokens_are_unique() -> None:
    assert tokens.create_csrf_token() != tokens.create_csrf_token()
