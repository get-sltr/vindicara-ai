"""Incident timeline: what executed, under whose authority, where evidence is missing.

Every assertion here is about a column value the reviewer will read, so a
regression in authority resolution or evidence status fails a named test
rather than silently mislabelling a row.
"""
from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path

import pytest
from typer.testing import CliRunner

from airsdk._concrete_demo import build_concrete_demo_log
from airsdk._incident_authority import AuthorityKind, resolve_authority
from airsdk._incident_render import render_incident_markdown
from airsdk.agdr import Signer, load_chain
from airsdk.detections import detect_untraceable_action, run_detectors
from airsdk.incident import EvidenceStatus, assemble_incident
from airsdk.types import (
    AgDRPayload,
    AgDRRecord,
    AuthMethod,
    DelegationGrant,
    HumanApproval,
    IntentSpec,
    RekorAnchor,
    StepKind,
    VerificationStatus,
)
from projectair.cli import app

NOW = int(time.time())


def _grant(*, expires_at: int = NOW + 3600) -> DelegationGrant:
    return DelegationGrant(
        delegation_id="d1", agent_id="claims-bot", auth_method=AuthMethod.AUTH0,
        authorizer_sub="auth0|clinician", authorizer_email="clinician@hospital.org",
        issuer="https://tenant.auth0.com/", policy_id="claims-v2", policy_hash="b3:00",
        scope=IntentSpec(goal="adjudicate claims", allowed_tools=["claims.read"]),
        granted_at=NOW - 60, expires_at=expires_at,
    )


def _approval(challenge_id: str = "c1") -> HumanApproval:
    return HumanApproval(
        challenge_id=challenge_id, decision="approve", approver_sub="auth0|lead", approver_email="lead@acme.io",
        issuer="https://tenant.auth0.com/", audience="air", issued_at=NOW, expires_at=NOW + 60,
        signed_token="jwt",  # noqa: S106
    )


def _chain(steps: list[tuple[StepKind, dict[str, object]]], signer: Signer | None = None) -> list[AgDRRecord]:
    signer = signer or Signer.generate()
    return [signer.sign(kind, AgDRPayload.model_validate(fields)) for kind, fields in steps]


def _demo(tmp_path: Path) -> tuple[Path, list[AgDRRecord]]:
    log = tmp_path / "demo.jsonl"
    build_concrete_demo_log(log)
    return log, load_chain(log)


# ------- authority -------

def test_plain_steps_are_vouched_for_by_the_agent_key_only(tmp_path: Path) -> None:
    _, records = _demo(tmp_path)
    kinds = {a.kind for a in resolve_authority(records)}
    assert kinds == {AuthorityKind.AGENT_KEY}
    assert resolve_authority(records)[0].subject == records[0].signer_key[:16]


def test_delegation_binds_every_later_step_to_the_authorizer() -> None:
    records = _chain([
        (StepKind.DELEGATION, {"delegation": _grant(), "user_intent": "adjudicate claims"}),
        (StepKind.INTENT_DECLARATION, {"user_intent": "adjudicate claims", "intent_spec": _grant().scope}),
        (StepKind.TOOL_START, {"tool_name": "claims.read", "tool_args": {}}),
        (StepKind.TOOL_END, {"tool_output": "ok"}),
    ])
    authorities = resolve_authority(records)
    assert [a.kind for a in authorities] == [AuthorityKind.DELEGATED] * 4
    assert authorities[2].subject == "auth0|clinician"
    assert authorities[2].issuer == "https://tenant.auth0.com/"
    assert "claims-v2" in authorities[2].detail


def test_expired_delegation_is_labelled_expired_not_delegated() -> None:
    records = _chain([
        (StepKind.DELEGATION, {"delegation": _grant(expires_at=NOW - 10)}),
        (StepKind.TOOL_START, {"tool_name": "claims.read", "tool_args": {}}),
    ])
    assert resolve_authority(records)[1].kind == AuthorityKind.EXPIRED


def test_declared_intent_without_a_human_is_declared_not_delegated() -> None:
    records = _chain([
        (StepKind.INTENT_DECLARATION, {"user_intent": "refactor auth", "intent_spec": IntentSpec(goal="refactor auth")}),
        (StepKind.LLM_START, {"prompt": "go"}),
    ])
    authorities = resolve_authority(records)
    assert authorities[0].kind == AuthorityKind.DECLARED
    assert authorities[1].kind == AuthorityKind.DECLARED
    assert authorities[1].subject is None


def test_halted_action_released_by_approval_names_the_approver() -> None:
    records = _chain([
        (StepKind.TOOL_START, {"tool_name": "wire", "tool_args": {}, "blocked": True, "blocked_reason": "step-up", "challenge_id": "c1"}),
        (StepKind.HUMAN_APPROVAL, {"challenge_id": "c1", "human_approval": _approval("c1")}),
        (StepKind.TOOL_START, {"tool_name": "wire", "tool_args": {}}),
        (StepKind.TOOL_END, {"tool_output": "sent"}),
        (StepKind.TOOL_START, {"tool_name": "rm", "tool_args": {}, "blocked": True, "blocked_reason": "denied by policy"}),
    ])
    halted, approval, resumed, ended, denied = resolve_authority(records)
    assert halted.kind == AuthorityKind.HALTED
    assert "released at step 1" in halted.detail
    assert approval.kind == AuthorityKind.APPROVED
    assert approval.subject == "lead@acme.io"
    assert resumed.kind == AuthorityKind.APPROVED
    assert "resumed under" in resumed.detail
    assert ended.kind == AuthorityKind.AGENT_KEY
    assert denied.kind == AuthorityKind.HALTED
    assert denied.detail == "denied by policy"


def test_halted_start_is_not_an_untraceable_action() -> None:
    records = _chain([
        (StepKind.TOOL_START, {"tool_name": "rm", "tool_args": {}, "blocked": True, "blocked_reason": "denied"}),
        (StepKind.AGENT_FINISH, {"final_output": "stopped"}),
    ])
    assert detect_untraceable_action(records) == []


# ------- evidence -------

def test_demo_focus_on_asi02_marks_target_ancestry_and_gap(tmp_path: Path) -> None:
    log, records = _demo(tmp_path)
    timeline = assemble_incident(records, run_detectors(records), source_log=str(log), detector="ASI02")
    assert timeline.focus == "detector ASI02"
    assert [e.ordinal for e in timeline.entries if e.target] == [8]
    assert {e.ordinal for e in timeline.entries if e.in_ancestry} == {2, 3, 4, 5, 6, 7, 8}
    exfil = timeline.entries[8]
    assert exfil.evidence == EvidenceStatus.GAP
    assert "AIR-04" in exfil.findings
    assert "ASI02" in exfil.findings
    assert timeline.entries[7].evidence == EvidenceStatus.SIGNED
    assert any(gap.startswith("step 8:") for gap in timeline.gaps)
    assert any("no external anchor" in gap for gap in timeline.gaps)
    assert {e.ordinal for e in timeline.focused()} == {2, 3, 4, 5, 6, 7, 8}


def test_anchor_range_marks_covered_steps_anchored_and_reports_the_tail() -> None:
    signer = Signer.generate()
    records = _chain([
        (StepKind.LLM_START, {"prompt": "go"}),
        (StepKind.LLM_END, {"response": "ok"}),
    ], signer)
    records += _chain([(StepKind.ANCHOR, {
        "anchored_chain_root": records[-1].content_hash,
        "anchored_step_range": {"from_step_id": records[0].step_id, "to_step_id": records[1].step_id},
        "rekor": RekorAnchor(log_index=42, uuid="u", integrated_time=0, log_id="l", inclusion_proof={}, rekor_url="https://rekor.sigstore.dev"),
    })], signer)
    records += _chain([(StepKind.AGENT_FINISH, {"final_output": "done"})], signer)
    timeline = assemble_incident(records, [], source_log="x")
    assert [e.evidence for e in timeline.entries] == [
        EvidenceStatus.ANCHORED, EvidenceStatus.ANCHORED, EvidenceStatus.SIGNED, EvidenceStatus.SIGNED,
    ]
    assert "Rekor 42" in timeline.entries[0].evidence_detail
    assert timeline.entries[2].authority.kind == AuthorityKind.WITNESSED
    assert timeline.anchors == 1
    assert timeline.unanchored_records == 1
    assert any("1 record(s) after the last anchor" in gap for gap in timeline.gaps)


def test_tampered_record_marks_it_and_everything_after_unverified(tmp_path: Path) -> None:
    log, records = _demo(tmp_path)
    tampered = records[7].model_copy(update={"payload": AgDRPayload(tool_output="nothing to see")})
    records = [*records[:7], tampered, *records[8:]]
    timeline = assemble_incident(records, [], source_log=str(log))
    assert timeline.verification.status == VerificationStatus.TAMPERED
    assert [e.evidence for e in timeline.entries[:7]] == [EvidenceStatus.SIGNED] * 7
    assert [e.evidence for e in timeline.entries[7:]] == [EvidenceStatus.UNVERIFIED] * 3
    assert "tampered" in timeline.entries[7].evidence_detail
    assert "after tampered at step 7" in timeline.entries[8].evidence_detail
    assert any(gap.startswith("step 7: tampered") for gap in timeline.gaps)


def test_focus_by_step_and_mutual_exclusion(tmp_path: Path) -> None:
    log, records = _demo(tmp_path)
    timeline = assemble_incident(records, [], source_log=str(log), step=8)
    assert timeline.focus == "step 8"
    assert timeline.entries[8].target
    with pytest.raises(ValueError, match="at most one"):
        assemble_incident(records, [], source_log=str(log), step=1, detector="ASI02")


# ------- rendering and CLI -------

def test_markdown_pack_carries_table_gaps_and_authority(tmp_path: Path) -> None:
    log, records = _demo(tmp_path)
    timeline = assemble_incident(records, run_detectors(records), source_log=str(log), detector="ASI02")
    md = render_incident_markdown(timeline)
    assert "| # | Time (UTC) | Step | What executed | Authority | Evidence | Findings |" in md
    assert "| **8** |" in md
    assert "| gap |" in md
    assert "3 record(s) outside the focus omitted" in md
    assert "## Where the evidence is missing" in md
    assert "no external anchor" in md
    assert "**agent-key:** 10 record(s)" in md
    full = render_incident_markdown(timeline, full=True)
    assert "omitted" not in full
    assert "| 0 |" in full
    assert "| 0 |" not in md


def test_cli_prints_timeline_free_and_gates_the_pack(tmp_path: Path) -> None:
    log, _ = _demo(tmp_path)
    result = CliRunner().invoke(app, ["incident", str(log), "--finding", "ASI02"])
    assert result.exit_code == 0, result.output
    assert "Incident timeline (beta)" in result.output
    assert "agent-key" in result.output
    assert "gap" in result.output
    assert "Where the evidence is missing" in result.output

    gated = CliRunner().invoke(app, ["incident", str(log), "-o", str(tmp_path / "pack.md")])
    assert gated.exit_code == 2, gated.output
    assert not (tmp_path / "pack.md").exists()


def test_cli_writes_the_pack_when_licensed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pro = types.ModuleType("airsdk_pro")
    fake_license = types.ModuleType("airsdk_pro.license")
    fake_license.current_license = lambda: {"tier": "team"}  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "airsdk_pro", fake_pro)
    monkeypatch.setitem(sys.modules, "airsdk_pro.license", fake_license)
    log, _ = _demo(tmp_path)
    out = tmp_path / "pack.md"
    result = CliRunner().invoke(app, ["incident", str(log), "--step", "8", "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_text().startswith("# Incident timeline (beta)")


def test_cli_json_output_round_trips(tmp_path: Path) -> None:
    log, _ = _demo(tmp_path)
    result = CliRunner().invoke(app, ["incident", str(log), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["focus"] is None
    assert len(payload["entries"]) == 10
    assert payload["entries"][8]["evidence"] == "gap"


def test_cli_rejects_bad_step_and_both_focus_flags(tmp_path: Path) -> None:
    log, _ = _demo(tmp_path)
    assert CliRunner().invoke(app, ["incident", str(log), "--step", "99"]).exit_code == 2
    assert CliRunner().invoke(app, ["incident", str(log), "--step", "1", "--finding", "ASI02"]).exit_code == 2
