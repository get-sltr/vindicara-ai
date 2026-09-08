"""DynamoDB-backed run store for AIR Cloud.

Table schema:
    pk: workspace_id (String)
    sk: run_id (String)
    GSI 'by_last_at': pk workspace_id, sk last_at (String) for newest-first listing
    attrs: summary_json (String) plus first_at / last_at / records copied out
           for the index and for cheap inspection

``upsert`` is read-merge-write. Two batches of the same run landing in the
same instant can lose a count to each other; the detail view recomputes
from the capsules, so the summary is a cache, never the evidence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from vindicara.cloud.run_store import RunSummary

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

GSI_BY_LAST_AT = "by_last_at"


class DDBRunStore:
    """DynamoDB-backed run store for production AIR Cloud."""

    def __init__(self, table: Table) -> None:
        self._table = table

    def _put(self, summary: RunSummary) -> None:
        self._table.put_item(
            Item={
                "workspace_id": summary.workspace_id,
                "run_id": summary.run_id,
                "first_at": summary.first_at,
                "last_at": summary.last_at,
                "records": summary.records,
                "summary_json": summary.model_dump_json(),
            }
        )

    def get(self, workspace_id: str, run_id: str) -> RunSummary | None:
        resp = self._table.get_item(Key={"workspace_id": workspace_id, "run_id": run_id})
        item = resp.get("Item")
        if item is None:
            return None
        return RunSummary.model_validate_json(str(cast("dict[str, object]", item)["summary_json"]))

    def upsert(self, summary: RunSummary) -> RunSummary:
        existing = self.get(summary.workspace_id, summary.run_id)
        merged = existing.merged_with(summary) if existing is not None else summary
        self._put(merged)
        return merged

    def assess(self, summary: RunSummary) -> None:
        self._put(summary)

    def list(self, workspace_id: str, *, limit: int, offset: int) -> tuple[list[RunSummary], int]:
        wanted = offset + limit
        items: list[dict[str, object]] = []
        kwargs: dict[str, object] = {
            "IndexName": GSI_BY_LAST_AT,
            "KeyConditionExpression": "workspace_id = :ws",
            "ExpressionAttributeValues": {":ws": workspace_id},
            "ScanIndexForward": False,
            "Limit": wanted,
        }
        resp = self._table.query(**kwargs)  # type: ignore[arg-type]
        items.extend(cast("list[dict[str, object]]", resp.get("Items", [])))
        last_key = resp.get("LastEvaluatedKey")
        while last_key and len(items) < wanted:
            resp = self._table.query(ExclusiveStartKey=last_key, **kwargs)  # type: ignore[arg-type]
            items.extend(cast("list[dict[str, object]]", resp.get("Items", [])))
            last_key = resp.get("LastEvaluatedKey")
        count_resp = self._table.query(
            IndexName=GSI_BY_LAST_AT,
            KeyConditionExpression="workspace_id = :ws",
            ExpressionAttributeValues={":ws": workspace_id},
            Select="COUNT",
        )
        total = int(count_resp.get("Count", len(items)))
        page = [RunSummary.model_validate_json(str(item["summary_json"])) for item in items[offset:wanted]]
        return page, total


__all__ = ["GSI_BY_LAST_AT", "DDBRunStore"]
