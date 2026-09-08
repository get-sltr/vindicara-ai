"""Runs: one precomputed summary per (workspace, run).

A run is one recorder session: every record signed by one ``AIRRecorder``
from its genesis record on. The console's Runs list must be one query, not
a scan over every capsule in the workspace, so ingest upserts a summary
row per run (counts, first and last timestamps, kinds, intent, signer) and
the detail view writes back what it computed (verification, findings) so
the list can show them without recomputing.
"""

from __future__ import annotations

import threading
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class RunSummary(BaseModel):
    """What the Runs list shows for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    workspace_id: str
    api_key_id: str = ""
    first_at: str
    last_at: str
    records: int
    kinds: dict[str, int] = Field(default_factory=dict)
    user_intent: str | None = None
    signer_key: str = ""
    verification: str | None = None  # "ok" | "tampered" | "broken_chain", once assessed
    findings: int | None = None
    max_severity: str | None = None
    assessed_at: str | None = None

    def merged_with(self, other: RunSummary) -> RunSummary:
        """Fold a newer partial summary (from an ingest batch) into this one."""
        kinds = dict(self.kinds)
        for kind, count in other.kinds.items():
            kinds[kind] = kinds.get(kind, 0) + count
        return self.model_copy(
            update={
                "first_at": min(self.first_at, other.first_at),
                "last_at": max(self.last_at, other.last_at),
                "records": self.records + other.records,
                "kinds": kinds,
                "user_intent": self.user_intent or other.user_intent,
                "signer_key": self.signer_key or other.signer_key,
                "api_key_id": self.api_key_id or other.api_key_id,
                # Assessment is stale once new records land; the detail view redoes it.
                "verification": None,
                "findings": None,
                "max_severity": None,
                "assessed_at": None,
            }
        )


@runtime_checkable
class RunStore(Protocol):
    def get(self, workspace_id: str, run_id: str) -> RunSummary | None: ...
    def upsert(self, summary: RunSummary) -> RunSummary:
        """Merge ``summary`` into the stored row (create on first sight); return the result."""
        ...
    def assess(self, summary: RunSummary) -> None:
        """Replace the stored row with an assessed summary (verification, findings filled in)."""
        ...
    def list(self, workspace_id: str, *, limit: int, offset: int) -> tuple[list[RunSummary], int]:
        """Newest ``last_at`` first; returns the page and the total count."""
        ...


class InMemoryRunStore:
    """Thread-safe dict-backed run store. Tests and local dev only."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], RunSummary] = {}
        self._lock = threading.Lock()

    def get(self, workspace_id: str, run_id: str) -> RunSummary | None:
        with self._lock:
            return self._items.get((workspace_id, run_id))

    def upsert(self, summary: RunSummary) -> RunSummary:
        key = (summary.workspace_id, summary.run_id)
        with self._lock:
            existing = self._items.get(key)
            merged = existing.merged_with(summary) if existing is not None else summary
            self._items[key] = merged
            return merged

    def assess(self, summary: RunSummary) -> None:
        with self._lock:
            self._items[(summary.workspace_id, summary.run_id)] = summary

    def list(self, workspace_id: str, *, limit: int, offset: int) -> tuple[list[RunSummary], int]:
        with self._lock:
            rows = [s for (ws, _), s in self._items.items() if ws == workspace_id]
        rows.sort(key=lambda s: s.last_at, reverse=True)
        return rows[offset : offset + limit], len(rows)


__all__ = ["InMemoryRunStore", "RunStore", "RunSummary"]
