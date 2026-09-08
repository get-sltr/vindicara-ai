"""DynamoDB-backed identity store for AIR Cloud.

Table schema:
    pk: identity_id (String)
    GSI 'by_email': pk email_key (String), written only for verified emails
    attrs: issuer, sub, workspace_id, email (String | absent), email_verified
           (Bool), created_at (String)

``link`` is a conditional put on ``attribute_not_exists(identity_id)``; on a
lost race it reads back the winner so the caller always gets the binding that
actually exists.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from vindicara.cloud.identity_store import IdentityLink, email_key_for

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

_log = logging.getLogger(__name__)

GSI_BY_EMAIL = "by_email"


def _to_link(row: dict[str, object]) -> IdentityLink:
    email = row.get("email")
    return IdentityLink(
        identity_id=str(row["identity_id"]),
        issuer=str(row["issuer"]),
        sub=str(row["sub"]),
        workspace_id=str(row["workspace_id"]),
        email=str(email) if isinstance(email, str) else None,
        email_verified=bool(row.get("email_verified", False)),
        created_at=str(row["created_at"]),
    )


class DDBIdentityStore:
    """DynamoDB-backed identity store for production AIR Cloud."""

    def __init__(self, table: Table) -> None:
        self._table = table

    def get(self, identity_id: str) -> IdentityLink | None:
        resp = self._table.get_item(Key={"identity_id": identity_id})
        item = resp.get("Item")
        if item is None:
            return None
        return _to_link(cast("dict[str, object]", item))

    def get_by_email(self, issuer: str, email: str) -> IdentityLink | None:
        resp = self._table.query(
            IndexName=GSI_BY_EMAIL,
            KeyConditionExpression="email_key = :ek",
            ExpressionAttributeValues={":ek": email_key_for(issuer, email)},
            Limit=1,
        )
        items = cast("list[dict[str, object]]", resp.get("Items", []))
        if not items:
            return None
        return _to_link(items[0])

    def link(self, link: IdentityLink) -> IdentityLink:
        item: dict[str, object] = {
            "identity_id": link.identity_id,
            "issuer": link.issuer,
            "sub": link.sub,
            "workspace_id": link.workspace_id,
            "email_verified": link.email_verified,
            "created_at": link.created_at,
        }
        if link.email is not None:
            item["email"] = link.email
        key = link.email_key
        if key is not None:
            item["email_key"] = key
        try:
            self._table.put_item(
                Item=item,  # type: ignore[arg-type]
                ConditionExpression="attribute_not_exists(identity_id)",
            )
        except Exception as exc:
            if type(exc).__name__ != "ConditionalCheckFailedException":
                raise
            existing = self.get(link.identity_id)
            if existing is None:
                raise
            _log.info("air_cloud.identity.link_race_lost", extra={"identity_id": link.identity_id})
            return existing
        return link


__all__ = ["GSI_BY_EMAIL", "DDBIdentityStore"]
