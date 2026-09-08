"""Tests for the filesystem-backed workspace + API-key stores.

These back the self-hosted / air-gapped unit, where in-memory stores would
forget every tenant on restart. Durability across instances is therefore the
contract under test, not an implementation detail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vindicara.cloud.file_stores import JSONApiKeyStore, JSONWorkspaceStore
from vindicara.cloud.workspace import (
    ApiKey,
    ApiKeyStore,
    Workspace,
    WorkspaceStore,
)


def _workspace(workspace_id: str = "acme", created_at: str = "2026-01-01T00:00:00Z") -> Workspace:
    return Workspace(
        workspace_id=workspace_id,
        name=workspace_id.title(),
        owner_email=f"ops@{workspace_id}.io",
        created_at=created_at,
    )


def _key(key_id: str = "key_1", workspace_id: str = "acme", key: str = "air_secret_1") -> ApiKey:
    # created_at is pinned so two calls compare equal; the default is now().
    return ApiKey(
        key_id=key_id,
        workspace_id=workspace_id,
        key=key,
        created_at="2026-01-01T00:00:00Z",
    )


class TestJSONWorkspaceStore:
    def test_satisfies_the_workspace_store_protocol(self, tmp_path: Path) -> None:
        assert isinstance(JSONWorkspaceStore(tmp_path), WorkspaceStore)

    def test_create_then_get_round_trips_every_field(self, tmp_path: Path) -> None:
        store = JSONWorkspaceStore(tmp_path)
        workspace = _workspace()
        store.create(workspace)
        assert store.get("acme") == workspace

    def test_survives_restart(self, tmp_path: Path) -> None:
        """The reason this module exists: a new instance sees prior writes."""
        JSONWorkspaceStore(tmp_path).create(_workspace())
        assert JSONWorkspaceStore(tmp_path).get("acme") == _workspace()

    def test_get_unknown_workspace_returns_none(self, tmp_path: Path) -> None:
        assert JSONWorkspaceStore(tmp_path).get("nope") is None

    def test_duplicate_create_is_rejected(self, tmp_path: Path) -> None:
        store = JSONWorkspaceStore(tmp_path)
        store.create(_workspace())
        with pytest.raises(ValueError, match="already exists"):
            store.create(_workspace())

    def test_list_is_ordered_by_creation_time(self, tmp_path: Path) -> None:
        store = JSONWorkspaceStore(tmp_path)
        store.create(_workspace("later", created_at="2026-06-01T00:00:00Z"))
        store.create(_workspace("earlier", created_at="2026-01-01T00:00:00Z"))
        assert [w.workspace_id for w in store.list()] == ["earlier", "later"]

    def test_list_on_a_fresh_root_is_empty(self, tmp_path: Path) -> None:
        assert JSONWorkspaceStore(tmp_path).list() == []

    def test_write_is_atomic_and_leaves_no_temp_file(self, tmp_path: Path) -> None:
        store = JSONWorkspaceStore(tmp_path)
        store.create(_workspace())
        assert (tmp_path / "workspaces.json").exists()
        assert list(tmp_path.glob("*.tmp")) == []

    def test_root_is_created_when_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "does" / "not" / "exist"
        JSONWorkspaceStore(nested).create(_workspace())
        assert (nested / "workspaces.json").exists()


class TestJSONApiKeyStore:
    def test_satisfies_the_api_key_store_protocol(self, tmp_path: Path) -> None:
        assert isinstance(JSONApiKeyStore(tmp_path), ApiKeyStore)

    def test_issue_then_lookup_round_trips(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        key = _key()
        store.issue(key)
        assert store.lookup("air_secret_1") == key

    def test_survives_restart(self, tmp_path: Path) -> None:
        JSONApiKeyStore(tmp_path).issue(_key())
        assert JSONApiKeyStore(tmp_path).lookup("air_secret_1") == _key()

    def test_lookup_of_unknown_key_returns_none(self, tmp_path: Path) -> None:
        assert JSONApiKeyStore(tmp_path).lookup("air_nope") is None

    def test_duplicate_key_id_is_rejected(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        with pytest.raises(ValueError, match="already exists"):
            store.issue(_key(key="air_different_secret"))

    def test_duplicate_secret_is_rejected_as_a_collision(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        with pytest.raises(ValueError, match="collision"):
            store.issue(_key(key_id="key_2"))

    def test_for_workspace_filters_by_tenant(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key("key_a", "acme", "air_a"))
        store.issue(_key("key_b", "other", "air_b"))
        assert [k.key_id for k in store.for_workspace("acme")] == ["key_a"]

    def test_for_workspace_with_no_keys_is_empty(self, tmp_path: Path) -> None:
        assert JSONApiKeyStore(tmp_path).for_workspace("acme") == []

    def test_revoke_stops_lookup_and_is_durable(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        assert store.revoke("key_1") is True
        assert store.lookup("air_secret_1") is None
        # A revoked key must stay revoked across a restart.
        assert JSONApiKeyStore(tmp_path).lookup("air_secret_1") is None

    def test_revoke_preserves_the_record_for_audit(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        store.revoke("key_1")
        surviving = store.for_workspace("acme")
        assert len(surviving) == 1
        assert surviving[0].revoked_at is not None

    def test_revoking_twice_reports_no_change(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        assert store.revoke("key_1") is True
        assert store.revoke("key_1") is False

    def test_revoking_an_unknown_key_returns_false(self, tmp_path: Path) -> None:
        assert JSONApiKeyStore(tmp_path).revoke("key_nope") is False

    def test_update_role_persists(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        updated = store.update_role("key_1", "viewer")
        assert updated is not None
        assert updated.role == "viewer"
        assert JSONApiKeyStore(tmp_path).lookup("air_secret_1").role == "viewer"  # type: ignore[union-attr]

    def test_update_role_leaves_the_secret_and_id_untouched(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        updated = store.update_role("key_1", "viewer")
        assert updated is not None
        assert (updated.key_id, updated.key) == ("key_1", "air_secret_1")

    def test_update_role_on_a_revoked_key_is_refused(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        store.revoke("key_1")
        assert store.update_role("key_1", "owner") is None

    def test_update_role_on_an_unknown_key_returns_none(self, tmp_path: Path) -> None:
        assert JSONApiKeyStore(tmp_path).update_role("key_nope", "owner") is None

    def test_write_leaves_no_temp_file(self, tmp_path: Path) -> None:
        store = JSONApiKeyStore(tmp_path)
        store.issue(_key())
        assert (tmp_path / "api_keys.json").exists()
        assert list(tmp_path.glob("*.tmp")) == []


def test_both_stores_share_one_data_directory(tmp_path: Path) -> None:
    """The self-hosted unit points both stores at a single data dir."""
    JSONWorkspaceStore(tmp_path).create(_workspace())
    JSONApiKeyStore(tmp_path).issue(_key())
    written = {p.name for p in tmp_path.iterdir()}
    assert written == {"workspaces.json", "api_keys.json"}
