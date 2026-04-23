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


DEMO_ASI07_EXTRA_RECORDS = 6  # legit + forged agent_message + 4-target fan-out appended by write_sample_log


def test_sample_chain_round_trips_and_verifies(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    signer = write_sample_log(sample)

    records = load_chain(sample)
    assert len(records) == len(SAMPLE_STEPS) + DEMO_ASI07_EXTRA_RECORDS
    # Chain still verifies end-to-end: the forged signer was initialized with the
    # primary signer's head hash, so prev_hash linkage holds and each record
    # verifies against its own signer_key.
    assert verify_chain(records).status == VerificationStatus.OK
    # Every record up to and including the first (legitimate) agent_message is
    # signed by the primary key; the final forged record is signed by a different key.
    primary_signed = records[: len(SAMPLE_STEPS) + 1]
    assert all(r.signer_key == signer.public_key_hex for r in primary_signed)
    assert records[-1].signer_key != signer.public_key_hex


def test_sample_chain_carries_user_intent_on_every_step(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    write_sample_log(sample)
    records = load_chain(sample)
    assert all(r.payload.user_intent == SAMPLE_USER_INTENT for r in records)


def test_sample_chain_triggers_all_implemented_detectors(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    write_sample_log(sample)
    findings = run_detectors(load_chain(sample))
    detector_ids = {f.detector_id for f in findings}
    for expected in ("ASI01", "ASI02", "ASI04", "ASI05", "ASI06", "ASI07", "ASI08", "ASI09", "AIR-01", "AIR-02", "AIR-03", "AIR-04"):
        assert expected in detector_ids, f"{expected} missing from demo findings: {detector_ids}"


def test_air_demo_runs_end_to_end(tmp_path: Path) -> None:
    sample = tmp_path / "demo.log"
    report = tmp_path / "report.json"

    result = runner.invoke(app, ["demo", "--sample-path", str(sample), "--output", str(report)])

    assert result.exit_code == 0, result.stdout
    assert sample.exists()
    assert report.exists()
    assert "[Chain verified]" in result.stdout
    for asi in ("ASI01", "ASI02", "ASI04", "ASI05", "ASI06", "ASI07", "ASI08", "ASI09", "AIR-01", "AIR-02", "AIR-03", "AIR-04"):
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
