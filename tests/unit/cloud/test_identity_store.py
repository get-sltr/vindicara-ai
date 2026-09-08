"""Identity links: put-if-absent semantics, verified-email lookup, DynamoDB conditional puts."""

from __future__ import annotations

from typing import Any

from vindicara.cloud.ddb_identity_store import DDBIdentityStore
from vindicara.cloud.identity_store import IdentityLink, InMemoryIdentityStore, identity_id_for


class ConditionalCheckFailedException(Exception):  # noqa: N818 (mirrors the boto3 exception name)
    pass


class FakeTable:
    """In-memory stand-in for the boto3 Table calls the identity store uses."""

    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}

    def put_item(self, *, Item: dict[str, Any], ConditionExpression: str = "", **_: Any) -> None:  # noqa: N803
        if ConditionExpression and Item["identity_id"] in self.items:
            raise ConditionalCheckFailedException("exists")
        self.items[Item["identity_id"]] = dict(Item)

    def get_item(self, *, Key: dict[str, str], **_: Any) -> dict[str, Any]:  # noqa: N803
        item = self.items.get(Key["identity_id"])
        return {"Item": dict(item)} if item else {}

    def query(self, *, ExpressionAttributeValues: dict[str, str], Limit: int | None = None, **_: Any) -> dict[str, Any]:  # noqa: N803
        ek = ExpressionAttributeValues[":ek"]
        hits = [dict(i) for i in self.items.values() if i.get("email_key") == ek]
        return {"Items": hits[:Limit] if Limit else hits}


def _link(sub: str = "auth0|1", ws: str = "ws_a", email: str | None = "kev@x.io", verified: bool = True) -> IdentityLink:
    return IdentityLink(identity_id=identity_id_for("https://t/", sub), issuer="https://t/", sub=sub, workspace_id=ws, email=email, email_verified=verified)


def test_identity_id_is_stable_and_opaque() -> None:
    assert identity_id_for("https://t/", "auth0|1") == identity_id_for("https://t/", "auth0|1")
    assert identity_id_for("https://t/", "auth0|1") != identity_id_for("https://t/", "auth0|2")
    assert identity_id_for("https://t/", "auth0|1").startswith("idn_")
    assert "auth0" not in identity_id_for("https://t/", "auth0|1")


def test_in_memory_link_is_put_if_absent() -> None:
    store = InMemoryIdentityStore()
    first = store.link(_link(ws="ws_a"))
    second = store.link(_link(ws="ws_b"))
    assert second.workspace_id == "ws_a"
    assert first == second
    assert store.get_by_email("https://t/", "KEV@x.io") == first


def test_in_memory_unverified_email_is_not_indexed() -> None:
    store = InMemoryIdentityStore()
    store.link(_link(verified=False))
    assert store.get_by_email("https://t/", "kev@x.io") is None


def test_ddb_link_returns_the_winner_on_a_lost_race() -> None:
    table = FakeTable()
    store = DDBIdentityStore(table)  # type: ignore[arg-type]
    first = store.link(_link(ws="ws_a"))
    second = store.link(_link(ws="ws_b"))
    assert first.workspace_id == "ws_a"
    assert second.workspace_id == "ws_a"
    assert table.items[first.identity_id]["email_key"] == "https://t/|kev@x.io"
    assert store.get(first.identity_id) == first
    assert store.get_by_email("https://t/", "kev@x.io") == first
    assert store.get("idn_missing") is None


def test_ddb_link_without_email_writes_no_email_attributes() -> None:
    table = FakeTable()
    store = DDBIdentityStore(table)  # type: ignore[arg-type]
    link = store.link(_link(email=None, verified=False))
    assert "email" not in table.items[link.identity_id]
    assert "email_key" not in table.items[link.identity_id]
    assert store.get(link.identity_id) == link
