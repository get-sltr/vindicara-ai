"""Evidence health: every level comes from the chain, and the CLI exit code follows the worst check."""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from airsdk._compat import UTC
from airsdk._concrete_demo import build_concrete_demo_log
from airsdk.agdr import Signer, load_chain
from airsdk.health import ANCHOR_TAIL_STEPS, HealthLevel, assess_health
from airsdk.types import (
    AgDRPayload,
    AgDRRecord,
    AuthMethod,
    DelegationGrant,
    IntentSpec,
    RekorAnchor,
    StepKind,
)
from projectair.cli import app

NOW = int(time.time())


def _chain(steps: list[tuple[StepKind, dict[str, object]]], signer: Signer | None = None) -> list[AgDRRecord]:
    signer = signer or Signer.generate()
    return [signer.sign(kind, AgDRPayload.model_validate(fields)) for kind, fields in steps]


def _clean(signer: Signer | None = None) -> list[AgDRRecord]:
    return _chain([
        (StepKind.LLM_START, {"prompt": "summarize q3"}),
        (StepKind.LLM_END, {"response": "revenue up"}),
        (StepKind.TOOL_START, {"tool_name": "read_file", "tool_args": {"path": "q3.csv"}}),
        (StepKind.TOOL_END, {"tool_output": "revenue,12"}),
        (StepKind.AGENT_FINISH, {"final_output": "revenue up"}),
    ], signer)


def _anchor(signer: Signer, records: list[AgDRRecord]) -> AgDRRecord:
    return _chain([(StepKind.ANCHOR, {
        "anchored_chain_root": records[-1].content_hash,
        "anchored_step_range": {"from_step_id": records[0].step_id, "to_step_id": records[-1].step_id},
        "rekor": RekorAnchor(log_index=7, uuid="u", integrated_time=0, log_id="l", inclusion_proof={}, rekor_url="https://rekor.sigstore.dev"),
    })], signer)[0]


def _grant(expires_at: int = NOW + 3600) -> DelegationGrant:
    return DelegationGrant(
        delegation_id="d1", agent_id="bot", auth_method=AuthMethod.AUTH0, authorizer_sub="auth0|kev",
        issuer="https://t.auth0.com/", policy_id="p", policy_hash="h", scope=IntentSpec(goal="summarize q3"),
        granted_at=NOW - 60, expires_at=expires_at,
    )


def _levels(records: list[AgDRRecord]) -> dict[str, HealthLevel]:
    return {c.key: c.level for c in assess_health(records, source_log="x").checks}


def test_clean_chain_warns_only_on_anchoring_and_authority() -> None:
    health = assess_health(_clean(), source_log="x")
    assert health.level == HealthLevel.WARN
    levels = {c.key: c.level for c in health.checks}
    assert levels == {
        "integrity": HealthLevel.OK, "custody": HealthLevel.OK, "verifiable": HealthLevel.OK,
        "completeness": HealthLevel.OK, "anchoring": HealthLevel.WARN, "authority": HealthLevel.WARN,
        "detectors": HealthLevel.OK, "freshness": HealthLevel.OK,
    }
    completeness = health.check("completeness")
    assert completeness.metrics["tool_calls"] == 1
    assert completeness.metrics["tool_calls_closed"] == 1
    assert "closed" in completeness.detail
    assert health.check("detectors").metrics["active"] == 14


def test_fully_evidenced_chain_is_ok() -> None:
    signer = Signer.generate()
    records = _chain([
        (StepKind.DELEGATION, {"delegation": _grant(), "user_intent": "summarize q3"}),
        (StepKind.INTENT_DECLARATION, {"user_intent": "summarize q3", "intent_spec": _grant().scope}),
    ], signer) + _clean(signer)
    records.append(_anchor(signer, records))
    health = assess_health(records, source_log="x")
    assert health.level == HealthLevel.OK, [(c.key, c.detail) for c in health.checks if c.level != HealthLevel.OK]
    assert health.check("anchoring").metrics["unanchored_records"] == 0
    assert "Rekor" in health.check("anchoring").detail


def test_tampered_chain_fails_integrity(tmp_path: Path) -> None:
    log = tmp_path / "demo.jsonl"
    build_concrete_demo_log(log)
    records = load_chain(log)
    records[7] = records[7].model_copy(update={"payload": AgDRPayload(tool_output="nothing")})
    health = assess_health(records, source_log=str(log))
    assert health.level == HealthLevel.FAIL
    assert health.check("integrity").level == HealthLevel.FAIL
    assert "tampered at record 7" in health.check("integrity").detail


def test_unauthorized_key_change_fails_custody() -> None:
    records = _clean(Signer.generate())[:2] + _chain([(StepKind.AGENT_FINISH, {"final_output": "x"})])
    levels = _levels(records)
    assert levels["custody"] == HealthLevel.FAIL


def test_missing_outcome_and_open_tail_warn_completeness() -> None:
    records = _chain([
        (StepKind.TOOL_START, {"tool_name": "shell", "tool_args": {}}),
        (StepKind.AGENT_FINISH, {"final_output": "done"}),
        (StepKind.LLM_START, {"prompt": "again"}),
    ])
    check = assess_health(records, source_log="x").check("completeness")
    assert check.level == HealthLevel.WARN
    assert "1 of 1 tool call(s) never recorded an outcome" in check.detail
    assert "ends on an open llm_start" in check.detail
    assert check.metrics["last_record"] == "llm_start"


def test_halted_tool_start_does_not_count_against_completeness() -> None:
    records = _chain([
        (StepKind.TOOL_START, {"tool_name": "rm", "tool_args": {}, "blocked": True, "blocked_reason": "denied"}),
        (StepKind.AGENT_FINISH, {"final_output": "stopped"}),
    ])
    check = assess_health(records, source_log="x").check("completeness")
    assert check.level == HealthLevel.OK
    assert check.metrics["tool_calls"] == 0


def test_long_unanchored_tail_warns() -> None:
    signer = Signer.generate()
    records = _clean(signer)
    records.append(_anchor(signer, records))
    for _ in range(ANCHOR_TAIL_STEPS + 1):
        records += _chain([(StepKind.LLM_START, {"prompt": "x"}), (StepKind.LLM_END, {"response": "y"})], signer)
    check = assess_health(records, source_log="x").check("anchoring")
    assert check.level == HealthLevel.WARN
    assert check.metrics["unanchored_records"] == 2 * (ANCHOR_TAIL_STEPS + 1)


def test_expired_delegation_warns_authority() -> None:
    records = _chain([(StepKind.DELEGATION, {"delegation": _grant(expires_at=NOW - 10)})]) + _clean()
    check = assess_health(records, source_log="x").check("authority")
    assert check.level == HealthLevel.WARN
    assert "after the delegation expired" in check.detail


def test_declared_scope_without_human_warns_authority() -> None:
    records = _chain([(StepKind.INTENT_DECLARATION, {"user_intent": "q3", "intent_spec": IntentSpec(goal="q3")})]) + _clean()
    check = assess_health(records, source_log="x").check("authority")
    assert check.level == HealthLevel.WARN
    assert "no human identity is bound" in check.detail


def test_mldsa_chain_fails_verification_support_when_extra_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    records = _clean()
    records[0] = records[0].model_copy(update={"signature_algorithm": "ml-dsa-65"})
    monkeypatch.setattr("airsdk.health.mldsa_available", lambda: False)
    check = assess_health(records, source_log="x").check("verifiable")
    assert check.level == HealthLevel.FAIL
    assert "projectair[pqc]" in check.detail


def test_freshness_reports_age_and_flags_stale() -> None:
    records = _clean()
    later = datetime.now(UTC) + timedelta(days=2)
    check = assess_health(records, source_log="x", now=later).check("freshness")
    assert check.level == HealthLevel.OK
    assert "older than 24h" in check.detail


def test_empty_chain_fails() -> None:
    health = assess_health([], source_log="x")
    assert health.level == HealthLevel.FAIL
    assert health.check("integrity").detail == "chain is empty"


# ------- CLI -------

def test_cli_single_chain_exit_codes(tmp_path: Path) -> None:
    log = tmp_path / "demo.jsonl"
    build_concrete_demo_log(log)
    result = CliRunner().invoke(app, ["health", str(log)])
    assert result.exit_code == 0, result.output
    assert "Evidence health (beta)" in result.output
    assert "WARN   Completeness" in result.output
    assert "air anchor <chain>" in result.output
    assert CliRunner().invoke(app, ["health", str(log), "--strict"]).exit_code == 1


def test_cli_directory_mode_summarizes_and_fails_on_unloadable(tmp_path: Path) -> None:
    build_concrete_demo_log(tmp_path / "a.jsonl")
    (tmp_path / "b.log").write_text('{"bad": 1}\n')
    (tmp_path / "notes.txt").write_text("ignored")
    result = CliRunner().invoke(app, ["health", str(tmp_path)])
    assert result.exit_code == 1, result.output
    assert "2 chain(s)" in result.output
    assert "cannot load: malformed AgDR record on line 1" in result.output
    assert "0 ok, 1 warn, 1 fail" in result.output


def test_cli_json_single_and_list(tmp_path: Path) -> None:
    build_concrete_demo_log(tmp_path / "a.jsonl")
    single = json.loads(CliRunner().invoke(app, ["health", str(tmp_path / "a.jsonl"), "--json"]).output)
    assert single["level"] == "warn"
    assert [c["key"] for c in single["checks"]][:3] == ["integrity", "custody", "verifiable"]
    many = json.loads(CliRunner().invoke(app, ["health", str(tmp_path), "--json"]).output)
    assert isinstance(many, list)
    assert len(many) == 1


def test_cli_empty_directory_exits_2(tmp_path: Path) -> None:
    assert CliRunner().invoke(app, ["health", str(tmp_path)]).exit_code == 2
