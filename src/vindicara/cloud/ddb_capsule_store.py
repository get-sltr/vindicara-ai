"""DynamoDB-backed capsule store for AIR Cloud.

Table schema:
    pk: workspace_id (String)
    sk: step_id (String)
    GSI 'by_run': pk workspace_id, sk run_id (String)
    attrs: record_json (String), kind (String), timestamp (String),
           created_at (String), api_key_id (String), run_id (String)

Implements the ``CapsuleStore`` protocol from ``capsule_store.py``.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from airsdk.types import AgDRRecord

from vindicara.cloud.capsule_store import StoredCapsule

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

_log = logging.getLogger(__name__)

GSI_BY_RUN = "by_run"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class DDBCapsuleStore:
    """DynamoDB-backed capsule store for production AIR Cloud."""

    def __init__(self, table: Table) -> None:
        self._table = table

    def append(self, capsule: StoredCapsule) -> None:
        record_json = capsule.record.model_dump_json(exclude_none=True)
        self._table.put_item(
            Item={
                "workspace_id": capsule.workspace_id,
                "step_id": capsule.record.step_id,
                "api_key_id": capsule.api_key_id,
                "run_id": capsule.run_id,
                "record_json": record_json,
                "kind": capsule.record.kind.value
                if hasattr(capsule.record.kind, "value")
                else str(capsule.record.kind),
                "timestamp": capsule.record.timestamp,
                "created_at": _now_iso(),
            },
        )

    def for_workspace(self, workspace_id: str) -> list[StoredCapsule]:
        # This table stores only String attributes; narrow the broad
        # DynamoDB attribute-value union at the boundary with a cast.
        items: list[dict[str, str]] = []
        resp = self._table.query(
            KeyConditionExpression="workspace_id = :ws",
            ExpressionAttributeValues={":ws": workspace_id},
        )
        items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
        last_key = resp.get("LastEvaluatedKey")
        while last_key:
            resp = self._table.query(
                KeyConditionExpression="workspace_id = :ws",
                ExpressionAttributeValues={":ws": workspace_id},
                ExclusiveStartKey=last_key,
            )
            items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
            last_key = resp.get("LastEvaluatedKey")

        return [self._to_capsule(workspace_id, item) for item in items]

    @staticmethod
    def _to_capsule(workspace_id: str, item: dict[str, str]) -> StoredCapsule:
        return StoredCapsule(
            workspace_id=workspace_id,
            record=AgDRRecord.model_validate(json.loads(item["record_json"])),
            api_key_id=item.get("api_key_id", ""),
            run_id=item.get("run_id", ""),
        )

    def for_key(self, workspace_id: str, api_key_id: str) -> list[StoredCapsule]:
        return [c for c in self.for_workspace(workspace_id) if c.api_key_id == api_key_id]

    def for_run(self, workspace_id: str, run_id: str) -> list[StoredCapsule]:
        items: list[dict[str, str]] = []
        kwargs: dict[str, object] = {
            "IndexName": GSI_BY_RUN,
            "KeyConditionExpression": "workspace_id = :ws AND run_id = :run",
            "ExpressionAttributeValues": {":ws": workspace_id, ":run": run_id},
        }
        resp = self._table.query(**kwargs)  # type: ignore[arg-type]
        items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
        last_key = resp.get("LastEvaluatedKey")
        while last_key:
            resp = self._table.query(ExclusiveStartKey=last_key, **kwargs)  # type: ignore[arg-type]
            items.extend(cast("list[dict[str, str]]", resp.get("Items", [])))
            last_key = resp.get("LastEvaluatedKey")
        return [self._to_capsule(workspace_id, item) for item in items]

    def count(self, workspace_id: str | None = None) -> int:
        if workspace_id is not None:
            resp = self._table.query(
                KeyConditionExpression="workspace_id = :ws",
                ExpressionAttributeValues={":ws": workspace_id},
                Select="COUNT",
            )
            return int(resp.get("Count", 0))
        resp = self._table.scan(Select="COUNT")
        return int(resp.get("Count", 0))
