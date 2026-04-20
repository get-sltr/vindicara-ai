"""End-to-end tests for the canonical demo chain and the `air demo` CLI."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from airsdk._demo import SAMPLE_STEPS, SAMPLE_USER_INTENT, write_sample_log
from airsdk.agdr import load_chain, verify_chain
from airsdk.detections import run_detectors
from airsdk.types import VerificationStatus
from projectair.cli import app

runner = CliRunner()


def test_sample_chain_round_trips_and_verifies(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    signer = write_sample_log(sample)

    records = load_chain(sample)
    assert len(records) == len(SAMPLE_STEPS)
    assert verify_chain(records).status == VerificationStatus.OK
    assert all(r.signer_key == signer.public_key_hex for r in records)


def test_sample_chain_carries_user_intent_on_every_step(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    write_sample_log(sample)
    records = load_chain(sample)
    assert all(r.payload.user_intent == SAMPLE_USER_INTENT for r in records)


def test_sample_chain_triggers_all_implemented_detectors(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    write_sample_log(sample)
    findings = run_detectors(load_chain(sample))
    asi_ids = {f.asi_id for f in findings}
    for expected in ("ASI01", "ASI02", "ASI03", "ASI05", "ASI07", "ASI09", "ASI10"):
        assert expected in asi_ids, f"{expected} missing from demo findings: {asi_ids}"


def test_air_demo_runs_end_to_end(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    report = tmp_path / "report.json"

    result = runner.invoke(app, ["demo", "--sample-path", str(sample), "--output", str(report)])

    assert result.exit_code == 0, result.stdout
    assert sample.exists()
    assert report.exists()
    assert "[Chain verified]" in result.stdout
    for asi in ("ASI01", "ASI02", "ASI03", "ASI05", "ASI07", "ASI09", "ASI10"):
        assert asi in result.stdout, f"{asi} not surfaced by `air demo`"


def test_air_trace_on_demo_sample(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    report = tmp_path / "report.json"
    write_sample_log(sample)

    result = runner.invoke(app, ["trace", str(sample), "--output", str(report)])

    assert result.exit_code == 0, result.stdout
    assert "[Chain verified]" in result.stdout
    assert report.exists()


def test_air_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "air / airsdk" in result.stdout
