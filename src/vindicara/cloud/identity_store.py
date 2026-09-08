"""Identity links: which workspace a signed-in human belongs to.

Self-serve sign-in needs a durable answer to "this OIDC identity has been here
before, which workspace is theirs?". The link is keyed on ``(issuer, sub)``,
the only pair an identity provider guarantees stable. A second, optional key
on the *verified* email for the same issuer lets a person who signs in with
Google today and a password tomorrow land in the same workspace instead of
getting a second, empty one.

``link`` is put-if-absent and returns the winner, so two concurrent first
sign-ins for the same identity converge on one workspace and the loser's
provisional workspace id is simply never used.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def identity_id_for(issuer: str, sub: str) -> str:
    """Stable, opaque id for an ``(issuer, sub)`` pair."""
    digest = hashlib.sha256(f"{issuer}|{sub}".encode()).hexdigest()[:32]
    return f"idn_{digest}"


def email_key_for(issuer: str, email: str) -> str:
    """Secondary lookup key: the same issuer plus a normalised, verified email."""
    return f"{issuer}|{email.strip().lower()}"


@dataclass(frozen=True)
class IdentityLink:
    """One OIDC identity bound to one workspace."""

    identity_id: str
    issuer: str
    sub: str
    workspace_id: str
    email: str | None = None
    email_verified: bool = False
    created_at: str = field(default_factory=_now_iso)

    @property
    def email_key(self) -> str | None:
        if self.email and self.email_verified:
            return email_key_for(self.issuer, self.email)
        return None


@runtime_checkable
class IdentityStore(Protocol):
    def get(self, identity_id: str) -> IdentityLink | None: ...
    def get_by_email(self, issuer: str, email: str) -> IdentityLink | None: ...
    def link(self, link: IdentityLink) -> IdentityLink: ...


class InMemoryIdentityStore:
    """Thread-safe dict-backed identity store. Tests and local dev only."""

    def __init__(self) -> None:
        self._items: dict[str, IdentityLink] = {}
        self._by_email: dict[str, IdentityLink] = {}
        self._lock = threading.Lock()

    def get(self, identity_id: str) -> IdentityLink | None:
        with self._lock:
            return self._items.get(identity_id)

    def get_by_email(self, issuer: str, email: str) -> IdentityLink | None:
        with self._lock:
            return self._by_email.get(email_key_for(issuer, email))

    def link(self, link: IdentityLink) -> IdentityLink:
        """Bind the identity to its workspace unless already bound; return the binding."""
        with self._lock:
            existing = self._items.get(link.identity_id)
            if existing is not None:
                return existing
            self._items[link.identity_id] = link
            key = link.email_key
            if key is not None:
                self._by_email.setdefault(key, link)
            return link


__all__ = [
    "IdentityLink",
    "IdentityStore",
    "InMemoryIdentityStore",
    "email_key_for",
    "identity_id_for",
]
