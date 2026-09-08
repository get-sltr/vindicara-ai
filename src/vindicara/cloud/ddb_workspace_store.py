"""DynamoDB-backed workspace store for AIR Cloud.

Table schema:
    pk: workspace_id (String)
    attrs: name (String), owner_email (String), created_at (String), tier (String)

Implements the ``WorkspaceStore`` protocol from ``workspace.py``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from vindicara.cloud.workspace import Workspace

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

_log = logging.getLogger(__name__)


class DDBWorkspaceStore:
    """DynamoDB-backed workspace store for production AIR Cloud."""

    def __init__(self, table: Table) -> None:
        self._table = table

    def create(self, workspace: Workspace) -> None:
        self._table.put_item(
            Item={
                "workspace_id": workspace.workspace_id,
                "name": workspace.name,
                "owner_email": workspace.owner_email,
                "created_at": workspace.created_at,
                "tier": workspace.tier,
            },
            ConditionExpression="attribute_not_exists(workspace_id)",
        )

    def get(self, workspace_id: str) -> Workspace | None:
        resp = self._table.get_item(Key={"workspace_id": workspace_id})
        item = resp.get("Item")
        if item is None:
            return None
        # This table stores only String attributes; narrow the boto3
        # attribute-value union at the boundary.
        row = cast("dict[str, str]", item)
        return Workspace(
            workspace_id=row["workspace_id"],
            name=row["name"],
            owner_email=row["owner_email"],
            created_at=row["created_at"],
            tier=row.get("tier", "free"),
        )

    def list(self) -> list[Workspace]:
        # DynamoDB resource items are typed as a broad attribute-value union;
        # this table stores only String attributes (see module docstring), so
        # we narrow at the boundary with an explicit cast.
        items: list[dict[str, str]] = []
        resp = self._table.scan()
        items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
        last_key = resp.get("LastEvaluatedKey")
        while last_key:
            resp = self._table.scan(ExclusiveStartKey=last_key)
            items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
            last_key = resp.get("LastEvaluatedKey")

        workspaces = [
            Workspace(
                workspace_id=item["workspace_id"],
                name=item["name"],
                owner_email=item["owner_email"],
                created_at=item["created_at"],
                tier=item.get("tier", "free"),
            )
            for item in items
        ]
        return sorted(workspaces, key=lambda w: w.created_at)
