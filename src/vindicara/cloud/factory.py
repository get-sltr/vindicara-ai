"""Application factory for the AIR Cloud hosted ingest service.

Standalone FastAPI app that serves the public ingest surface for
hosted multi-tenant deployments. Distinct from the existing
``vindicara.api.create_app`` which is the Vindicara engine API; this
factory wires only the AIR-Cloud-specific routes (capsules ingest,
capsule list, workspace introspection, key management).

The split lets the AIR Cloud service deploy independently: a single
FastAPI process behind one Lambda or container, with the engine API
deployed alongside or skipped entirely depending on tier.

When ``AIR_CLOUD_CAPSULES_TABLE``, ``AIR_CLOUD_WORKSPACES_TABLE``, and
``AIR_CLOUD_API_KEYS_TABLE`` env vars are set, the factory auto-wires
DynamoDB-backed stores. Otherwise it falls back to in-memory stores
for tests and local development.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from vindicara.cloud.capsule_store import CapsuleStore, InMemoryCapsuleStore
from vindicara.cloud.event_bus import CapsuleEventBus
from vindicara.cloud.identity_store import IdentityStore, InMemoryIdentityStore
from vindicara.cloud.middleware import AirCloudAuthMiddleware
from vindicara.cloud.routes import (
    analytics,
    auth,
    capsules,
    compliance,
    entitlements,
    findings,
    identity,
    keys,
    runs,
    sso,
    workspaces,
)
from vindicara.cloud.routes import stream as stream_route
from vindicara.cloud.run_store import InMemoryRunStore, RunStore
from vindicara.cloud.signup import ServiceOidc, service_oidc_from_env
from vindicara.cloud.sso import InMemorySsoConfigStore, SsoConfigStore
from vindicara.cloud.workspace import (
    ApiKeyStore,
    InMemoryApiKeyStore,
    InMemoryWorkspaceStore,
    WorkspaceStore,
)

_log = logging.getLogger(__name__)


def _seed_sso_from_env(store: SsoConfigStore) -> None:
    """Pre-load SSO config from env vars so it survives Lambda cold starts."""
    workspace_id = os.environ.get("AIR_CLOUD_SSO_WORKSPACE")
    issuer = os.environ.get("AIR_CLOUD_SSO_ISSUER")
    audience = os.environ.get("AIR_CLOUD_SSO_AUDIENCE")
    if not all([workspace_id, issuer, audience]):
        return
    from vindicara.cloud.sso import SsoConfig

    store.put(
        SsoConfig(
            workspace_id=workspace_id or "",
            issuer=issuer or "",
            audience=audience or "",
            default_role=os.environ.get("AIR_CLOUD_SSO_DEFAULT_ROLE", "admin"),
        )
    )
    _log.info("air_cloud.sso.seeded_from_env", extra={"workspace_id": workspace_id})


def _build_ddb_stores() -> tuple[CapsuleStore, WorkspaceStore, ApiKeyStore, IdentityStore, RunStore] | None:
    """Build DDB stores if the table env vars are set."""
    capsules_table = os.environ.get("AIR_CLOUD_CAPSULES_TABLE")
    workspaces_table = os.environ.get("AIR_CLOUD_WORKSPACES_TABLE")
    api_keys_table = os.environ.get("AIR_CLOUD_API_KEYS_TABLE")
    identities_table = os.environ.get("AIR_CLOUD_IDENTITIES_TABLE")
    runs_table = os.environ.get("AIR_CLOUD_RUNS_TABLE")

    if capsules_table is None or workspaces_table is None or api_keys_table is None:
        return None

    import boto3

    from vindicara.cloud.ddb_api_key_store import DDBApiKeyStore
    from vindicara.cloud.ddb_capsule_store import DDBCapsuleStore
    from vindicara.cloud.ddb_identity_store import DDBIdentityStore
    from vindicara.cloud.ddb_run_store import DDBRunStore
    from vindicara.cloud.ddb_workspace_store import DDBWorkspaceStore

    ddb = boto3.resource("dynamodb")
    identities: IdentityStore = (
        DDBIdentityStore(ddb.Table(identities_table)) if identities_table else InMemoryIdentityStore()
    )
    if not identities_table:
        _log.warning("air_cloud.identities.in_memory: AIR_CLOUD_IDENTITIES_TABLE unset; sign-ins will not persist")
    run_store: RunStore = DDBRunStore(ddb.Table(runs_table)) if runs_table else InMemoryRunStore()
    if not runs_table:
        _log.warning("air_cloud.runs.in_memory: AIR_CLOUD_RUNS_TABLE unset; the runs list will not persist")
    _log.info("air_cloud.ddb_stores.wired")
    return (
        DDBCapsuleStore(ddb.Table(capsules_table)),
        DDBWorkspaceStore(ddb.Table(workspaces_table)),
        DDBApiKeyStore(ddb.Table(api_keys_table)),
        identities,
        run_store,
    )


def _resolve_admin_token(explicit: str | None) -> str | None:
    """Resolve the operator admin token for workspace creation (W3.10).

    Precedence: explicit kwarg, then ``AIR_CLOUD_ADMIN_TOKEN`` env, then the
    Secrets Manager secret named by ``AIR_CLOUD_ADMIN_TOKEN_SECRET_ARN``.
    When none resolve, returns ``None`` and workspace creation stays
    disabled (fail-closed).

    A secret-fetch failure disables only workspace creation; it must not
    take down ingestion, so the error is caught and downgraded to None
    rather than propagated out of app construction.
    """
    if explicit is not None:
        return explicit
    env_token = os.environ.get("AIR_CLOUD_ADMIN_TOKEN")
    if env_token:
        return env_token
    secret_arn = os.environ.get("AIR_CLOUD_ADMIN_TOKEN_SECRET_ARN")
    if not secret_arn:
        return None

    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    client = boto3.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=secret_arn)
    except (BotoCoreError, ClientError):
        _log.warning("air_cloud.admin_token.fetch_failed")
        return None
    secret = response.get("SecretString")
    if not secret:
        _log.warning("air_cloud.admin_token.secret_empty")
        return None
    return str(secret)


def create_air_cloud_app(
    *,
    capsule_store: CapsuleStore | None = None,
    workspace_store: WorkspaceStore | None = None,
    api_key_store: ApiKeyStore | None = None,
    sso_config_store: SsoConfigStore | None = None,
    admin_token: str | None = None,
    license_signing_key_pem: str | None = None,
    identity_store: IdentityStore | None = None,
    run_store: RunStore | None = None,
    service_oidc: ServiceOidc | None = None,
    cloud_url: str | None = None,
    console_url: str | None = None,
    title: str = "AIR Cloud",
    version: str = "0.1.0",
) -> FastAPI:
    """Build the AIR Cloud hosted ingest FastAPI app.

    Defaults to in-memory stores for tests / local runs. When DDB table
    env vars are set, auto-wires DynamoDB-backed stores. Explicit kwargs
    always win (for tests).

    ``admin_token`` gates ``POST /v1/workspaces`` (W3.10). Explicit kwarg
    wins; otherwise the ``AIR_CLOUD_ADMIN_TOKEN`` env var is used. When
    neither is set, workspace creation is disabled (fail-closed) rather
    than left open.

    ``license_signing_key_pem`` signs console grants (``GET
    /v1/entitlements/grant``). Explicit kwarg wins; otherwise the
    ``VINDICARA_LICENSE_SIGNING_KEY_PEM`` env var. When neither is set the
    grant route answers 503 (fail-closed) rather than minting unsigned tokens.

    ``service_oidc`` is the identity provider ``POST /v1/auth/exchange`` trusts
    for self-serve sign-in; defaults to ``AIR_CLOUD_OIDC_*``. ``identity_store``
    binds identities to workspaces (DynamoDB when ``AIR_CLOUD_IDENTITIES_TABLE``
    is set). ``cloud_url`` / ``console_url`` are echoed to clients so the Keys
    screen and the CLI print the right addresses.
    """
    ddb_stores = None
    if capsule_store is None and workspace_store is None and api_key_store is None:
        ddb_stores = _build_ddb_stores()

    app = FastAPI(
        title=title,
        version=version,
        description=(
            "Hosted ingest service for Project AIR signed forensic chains. "
            "Customers POST signed Intent Capsules to /v1/capsules; the dashboard "
            "and report generators read them back through workspace-scoped GET routes."
        ),
    )

    if ddb_stores is not None:
        app.state.capsule_store = ddb_stores[0]
        app.state.cloud_workspaces = ddb_stores[1]
        app.state.cloud_api_keys = ddb_stores[2]
        app.state.cloud_identities = identity_store or ddb_stores[3]
        app.state.run_store = run_store or ddb_stores[4]
    else:
        app.state.capsule_store = capsule_store or InMemoryCapsuleStore()
        app.state.cloud_workspaces = workspace_store or InMemoryWorkspaceStore()
        app.state.cloud_api_keys = api_key_store or InMemoryApiKeyStore()
        app.state.cloud_identities = identity_store or InMemoryIdentityStore()
        app.state.run_store = run_store or InMemoryRunStore()
    app.state.service_oidc = service_oidc if service_oidc is not None else service_oidc_from_env()
    app.state.cloud_url = cloud_url or os.environ.get("AIR_CLOUD_PUBLIC_URL", "https://cloud.vindicara.io")
    app.state.console_url = console_url or os.environ.get("AIR_CLOUD_CONSOLE_URL", "https://vindicara.io/flightdeck")

    # First-run lead capture store (public /v1/identity/register). Wired only
    # when the table env var is set; without it the route no-ops (returns 200
    # without storing), which keeps tests and local runs working.
    identity_table = os.environ.get("VINDICARA_IDENTITY_TABLE")
    if identity_table:
        import boto3

        from vindicara.cloud.routes.identity import IdentityRegistrationStore

        app.state.identity_registrations = IdentityRegistrationStore(
            boto3.resource("dynamodb").Table(identity_table)
        )

    sso_store = sso_config_store or InMemorySsoConfigStore()
    _seed_sso_from_env(sso_store)
    app.state.cloud_sso_configs = sso_store
    app.state.capsule_event_bus = CapsuleEventBus()
    app.state.cloud_admin_token = _resolve_admin_token(admin_token)
    app.state.license_signing_key_pem = (
        license_signing_key_pem if license_signing_key_pem is not None else os.environ.get("VINDICARA_LICENSE_SIGNING_KEY_PEM")
    )

    app.add_middleware(AirCloudAuthMiddleware, prefix="/v1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.state.finding_actions = findings.FindingActionStore()

    app.include_router(capsules.router)
    app.include_router(findings.router)
    app.include_router(identity.router)
    app.include_router(workspaces.router)
    app.include_router(keys.router)
    app.include_router(sso.router)
    app.include_router(stream_route.router)
    app.include_router(compliance.router)
    app.include_router(analytics.router)
    app.include_router(entitlements.router)
    app.include_router(auth.router)
    app.include_router(runs.router)

    @app.get("/health")
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def _ready() -> dict[str, str]:
        return {"status": "ready"}

    return app


__all__ = ["create_air_cloud_app"]
