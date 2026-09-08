"""Self-serve sign-in: verify an identity-provider token, provision a workspace.

This is the seam ``admin.py`` reserved: an end user never touches the operator
admin token. They sign in with the identity provider the service trusts, and
the service turns that identity into a personal workspace with an owner key.

Trust is service-level (``ServiceOidc``: one issuer, one audience, an optional
allowlist of client ids), not per-workspace, because a first-time visitor has
no workspace yet. Verification reuses ``verify_oidc_token`` unchanged by
wrapping the service trust in an ``SsoConfig``; the JWKS client is cached per
URI so a busy demo does not fetch the key set on every sign-in.

Provisioning is link-first and idempotent: bind the identity to a fresh
workspace id, then create the workspace and owner key only if they do not
already exist. A crash between the steps is repaired on the next sign-in.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from jwt import PyJWKClient

from vindicara.cloud.identity_store import IdentityLink, IdentityStore, identity_id_for
from vindicara.cloud.sso import SsoConfig, SsoVerificationError, verify_oidc_token
from vindicara.cloud.workspace import ApiKey, ApiKeyStore, Workspace, WorkspaceStore, generate_api_key

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_log = logging.getLogger(__name__)

EMAIL_CLAIM = "https://vindicara.io/email"
EMAIL_VERIFIED_CLAIM = "https://vindicara.io/email_verified"
_USERINFO_TIMEOUT_SECONDS = 3


@dataclass(frozen=True)
class ServiceOidc:
    """The identity provider this deployment trusts for sign-in."""

    issuer: str
    audience: str
    jwks_uri: str | None = None
    client_ids: frozenset[str] = frozenset()

    def as_sso_config(self) -> SsoConfig:
        return SsoConfig(workspace_id="_service", issuer=self.issuer, audience=self.audience, jwks_uri=self.jwks_uri)


def service_oidc_from_env(environ: Mapping[str, str] | None = None) -> ServiceOidc | None:
    """Read the service trust from ``AIR_CLOUD_OIDC_*``; ``None`` when not configured."""
    env = environ if environ is not None else os.environ
    issuer, audience = env.get("AIR_CLOUD_OIDC_ISSUER", ""), env.get("AIR_CLOUD_OIDC_AUDIENCE", "")
    if not issuer or not audience:
        return None
    raw_ids = env.get("AIR_CLOUD_OIDC_CLIENT_IDS", "")
    client_ids = frozenset(part.strip() for part in raw_ids.split(",") if part.strip())
    return ServiceOidc(issuer=issuer, audience=audience, jwks_uri=env.get("AIR_CLOUD_OIDC_JWKS_URI") or None, client_ids=client_ids)


@lru_cache(maxsize=8)
def _cached_jwks_client(uri: str) -> PyJWKClient:
    return PyJWKClient(uri, cache_keys=True)


@dataclass(frozen=True)
class VerifiedIdentity:
    issuer: str
    sub: str
    email: str | None
    email_verified: bool


def _userinfo_email(issuer: str, token: str) -> tuple[str | None, bool]:
    request = urllib.request.Request(  # noqa: S310 (issuer is operator-configured https)
        f"{issuer.rstrip('/')}/userinfo", headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=_USERINFO_TIMEOUT_SECONDS) as response:  # noqa: S310
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        _log.info("air_cloud.signup.userinfo_unavailable", extra={"error": str(exc)})
        return None, False
    email = body.get("email") if isinstance(body, dict) else None
    verified = bool(body.get("email_verified", False)) if isinstance(body, dict) else False
    return (email if isinstance(email, str) else None), verified


def resolve_email(
    claims: Mapping[str, Any], token: str, issuer: str, *, userinfo: Callable[[str, str], tuple[str | None, bool]] = _userinfo_email
) -> tuple[str | None, bool]:
    """Best available email for the identity: token claims first, then the userinfo endpoint."""
    for email_claim, verified_claim in ((EMAIL_CLAIM, EMAIL_VERIFIED_CLAIM), ("email", "email_verified")):
        email = claims.get(email_claim)
        if isinstance(email, str) and "@" in email:
            return email, bool(claims.get(verified_claim, False))
    return userinfo(issuer, token)


def verify_identity(token: str, oidc: ServiceOidc, *, jwks_client_factory: Callable[[str], Any] | None = None) -> VerifiedIdentity:
    """Verify ``token`` against the service trust; raise ``SsoVerificationError`` otherwise."""
    factory = jwks_client_factory if jwks_client_factory is not None else _cached_jwks_client
    claims = verify_oidc_token(token, config=oidc.as_sso_config(), jwks_client_factory=factory)
    azp = claims.get("azp")
    if oidc.client_ids and (not isinstance(azp, str) or azp not in oidc.client_ids):
        raise SsoVerificationError("token was issued to a client this service does not accept")
    email, verified = resolve_email(claims, token, oidc.issuer)
    return VerifiedIdentity(issuer=oidc.issuer, sub=str(claims["sub"]), email=email, email_verified=verified)


def new_workspace_id() -> str:
    return "ws_" + secrets.token_hex(6)


def workspace_name_for(email: str | None, sub: str) -> str:
    if email and "@" in email:
        return f"{email.split('@', 1)[0]}'s workspace"
    return f"workspace {sub[-8:]}"


@dataclass(frozen=True)
class Provisioned:
    workspace: Workspace
    key_id: str
    role: str
    api_key: ApiKey | None  # the secret, only when minted in this call
    created: bool


def _find_link(identity: VerifiedIdentity, identity_store: IdentityStore) -> IdentityLink | None:
    link = identity_store.get(identity_id_for(identity.issuer, identity.sub))
    if link is not None or not (identity.email and identity.email_verified):
        return link
    return identity_store.get_by_email(identity.issuer, identity.email)


def provision_identity(
    identity: VerifiedIdentity,
    *,
    workspace_store: WorkspaceStore,
    api_key_store: ApiKeyStore,
    identity_store: IdentityStore,
) -> Provisioned:
    """Get or create the workspace and owner key for a verified identity."""
    identity_id = identity_id_for(identity.issuer, identity.sub)
    existing = _find_link(identity, identity_store)
    workspace_id = existing.workspace_id if existing is not None else new_workspace_id()
    link = identity_store.link(
        IdentityLink(
            identity_id=identity_id, issuer=identity.issuer, sub=identity.sub, workspace_id=workspace_id,
            email=identity.email, email_verified=identity.email_verified,
        )
    )
    workspace = workspace_store.get(link.workspace_id)
    created = False
    if workspace is None:
        workspace = Workspace(
            workspace_id=link.workspace_id, name=workspace_name_for(identity.email, identity.sub),
            owner_email=identity.email or "", tier="free",
        )
        try:
            workspace_store.create(workspace)
            created = True
        except ValueError:
            fetched = workspace_store.get(link.workspace_id)
            if fetched is None:
                raise
            workspace = fetched
    key_id = f"key_{workspace.workspace_id}_owner"
    keys = api_key_store.for_workspace(workspace.workspace_id)
    active = next((k for k in keys if k.key_id == key_id and k.revoked_at is None), None)
    if active is not None:
        return Provisioned(workspace=workspace, key_id=key_id, role="owner", api_key=None, created=created)
    minted = ApiKey(key_id=key_id, workspace_id=workspace.workspace_id, key=generate_api_key(), role="owner", name="owner key (issued at sign-in)")
    if any(k.key_id == key_id for k in keys):
        # The owner key was revoked on purpose; the console still signs in but no secret is handed back.
        return Provisioned(workspace=workspace, key_id=key_id, role="owner", api_key=None, created=created)
    api_key_store.issue(minted)
    return Provisioned(workspace=workspace, key_id=key_id, role="owner", api_key=minted, created=created)


__all__ = [
    "EMAIL_CLAIM",
    "Provisioned",
    "ServiceOidc",
    "VerifiedIdentity",
    "provision_identity",
    "resolve_email",
    "service_oidc_from_env",
    "verify_identity",
    "workspace_name_for",
]
