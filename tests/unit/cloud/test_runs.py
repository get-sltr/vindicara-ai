"""Run lineage: the header wins, a batch resolves itself in any order, legacy rows regroup."""

from __future__ import annotations

from airsdk.agdr import Signer
from airsdk.types import AgDRPayload, StepKind

from vindicara.cloud.capsule_store import StoredCapsule
from vindicara.cloud.run_store import InMemoryRunStore, RunSummary
from vindicara.cloud.runs import assess_run, group_runs, order_chain, resolve_run_ids, summarize_batch, valid_run_id


def _chain(n: int, signer: Signer | None = None) -> list:  # type: ignore[type-arg]
    signer = signer or Signer.generate()
    out = []
    for i in range(n):
        kind = StepKind.LLM_START if i % 2 == 0 else StepKind.LLM_END
        payload = AgDRPayload(prompt=f"p{i}") if i % 2 == 0 else AgDRPayload(response=f"r{i}")
        out.append(signer.sign(kind, payload))
    return out


def test_header_wins_for_every_record() -> None:
    records = _chain(3)
    assert resolve_run_ids(records, header_run_id="run_from_client") == ["run_from_client"] * 3


def test_batch_resolves_lineage_in_any_order() -> None:
    records = _chain(4)
    shuffled = [records[2], records[0], records[3], records[1]]
    assert resolve_run_ids(shuffled, header_run_id=None) == [records[0].step_id] * 4


def test_two_chains_in_one_batch_stay_apart() -> None:
    a, b = _chain(2), _chain(2)
    mixed = [a[1], b[0], a[0], b[1]]
    assert resolve_run_ids(mixed, header_run_id=None) == [a[0].step_id, b[0].step_id, a[0].step_id, b[0].step_id]


def test_orphan_without_parent_or_header_is_its_own_run() -> None:
    records = _chain(3)
    tail = [records[2]]
    assert resolve_run_ids(tail, header_run_id=None) == [records[2].step_id]


def test_valid_run_id_filters_garbage() -> None:
    step_id = _chain(1)[0].step_id
    assert valid_run_id(step_id) == step_id
    assert valid_run_id("") is None
    assert valid_run_id(None) is None
    assert valid_run_id("<script>") is None


def test_order_chain_restores_genesis_first_order() -> None:
    records = _chain(5)
    ordered = order_chain([records[3], records[0], records[4], records[1], records[2]])
    assert [r.step_id for r in ordered] == [r.step_id for r in records]


def test_group_runs_rejoins_legacy_rows_without_run_id() -> None:
    a, b = _chain(3), _chain(2)
    capsules = [StoredCapsule(workspace_id="ws", record=r) for r in [*a, *b]]
    groups = group_runs(capsules)
    assert set(groups) == {a[0].step_id, b[0].step_id}
    assert len(groups[a[0].step_id]) == 3


def test_summarize_and_merge_batches() -> None:
    records = _chain(4)
    records[0] = records[0]  # genesis carries no intent in this helper; set one via a fresh signer below
    store = InMemoryRunStore()
    first = store.upsert(summarize_batch("ws", "run", records[:2], api_key_id="k1"))
    assert first.records == 2
    merged = store.upsert(summarize_batch("ws", "run", records[2:], api_key_id="k1"))
    assert merged.records == 4
    assert merged.kinds == {"llm_start": 2, "llm_end": 2}
    assert merged.first_at == records[0].timestamp
    assert merged.last_at == records[3].timestamp
    assert merged.assessed_at is None
    page, total = store.list("ws", limit=10, offset=0)
    assert total == 1 and page[0].run_id == "run"


def test_assess_run_fills_verification_findings_and_timeline() -> None:
    records = _chain(4)
    summary = summarize_batch("ws", records[0].step_id, records, api_key_id="k1")
    detail = assess_run(summary, list(reversed(records)), console_url="http://c/flightdeck/")
    assert detail.verification.status.value == "ok"
    assert detail.summary.verification == "ok"
    assert detail.summary.assessed_at is not None
    assert [e.ordinal for e in detail.timeline.entries] == [0, 1, 2, 3]
    assert detail.health.level.value in {"ok", "warn", "fail"}
    assert detail.console_url == f"http://c/flightdeck/runs/{records[0].step_id}"
    assert isinstance(detail.summary, RunSummary)
