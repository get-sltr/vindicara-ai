"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vindicara.api.middleware.auth import APIKeyAuthMiddleware
from vindicara.api.middleware.request_id import RequestIDMiddleware
from vindicara.api.routes import guard, health, policies


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vindicara API",
        description="Runtime security for autonomous AI",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(APIKeyAuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(guard.router)
    app.include_router(policies.router)

    return app
