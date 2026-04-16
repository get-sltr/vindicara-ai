"""Shared test fixtures."""

import os

os.environ.setdefault("VINDICARA_JWT_SECRET", "test-jwt-secret-do-not-use-in-production-0123456789abcdef")
os.environ.setdefault("VINDICARA_STAGE", "test")

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from vindicara.api.app import create_app

TEST_API_KEY = "vnd_test"
TEST_PASSWORD = "TestPassword123"  # noqa: S105


@pytest.fixture
def app() -> FastAPI:
    """Create a test app with a pre-registered dev API key."""
    return create_app(dev_api_keys=[TEST_API_KEY])


@pytest.fixture
async def authed_cookies(app: FastAPI) -> dict[str, str]:
    """Sign up a unique test user and return auth cookies."""
    email = f"test-{uuid.uuid4().hex[:8]}@vindicara.io"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
        resp = await client.post(
            "/dashboard/api/auth/signup",
            data={"email": email, "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD},
        )
        return dict(resp.cookies)
