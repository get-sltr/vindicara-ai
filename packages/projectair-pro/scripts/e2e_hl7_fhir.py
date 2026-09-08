"""E2E demo: HL7v2 clinical evidence sidecar.

Demonstrates the full HL7v2 pipeline without requiring a Pro license:
  - parse_hl7v2, map_to_fhir, project_for_chain, RedactionPolicy are OSS-tier
  - instrument_hl7 and ClinicalSidecar are Pro-gated (not used here)

Usage:
    python scripts/e2e_hl7_fhir.py
    python scripts/e2e_hl7_fhir.py --phi-raw
"""
from __future__ import annotations

import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

from airsdk.agdr import load_chain, verify_chain
from airsdk.recorder import AIRRecorder
from airsdk.types import DataSubjectRef, IntentSpec

from airsdk_pro.hl7.fhir import MappedResource, map_to_fhir, project_for_chain
from airsdk_pro.hl7.parser import parse_hl7v2
from airsdk_pro.hl7.redaction import PHIMode, RedactionPolicy

# ---------------------------------------------------------------------------
# Sample HL7v2 messages
# ---------------------------------------------------------------------------

SAMPLE_ORU = (
    "MSH|^~\\&|LAB|HOSP-MAIN|AI-AGENT|VINDICARA|20260511120000||ORU^R01|MSG001|P|2.5\r"
    "PID|1||MRN-0042^^^HOSP-MAIN^MR||DOE^JANE||19850315|F\r"
    "OBR|1|ORD001|FIL001|14749-6^HbA1c^LN|||20260511\r"
    "OBX|1|NM|14749-6^HbA1c^LN||8.4|%|<7.0|H|||F\r"
    "OBX|2|NM|2345-7^Glucose^LN||186|mg/dL|74-106|H|||F\r"
    "OBX|3|ST|LOCAL001^Custom Test^LOCAL||Positive||||F\r"
)

UNAUTHORIZED_ORU = (
    "MSH|^~\\&|LAB|HOSP-MAIN|AI-AGENT|VINDICARA|20260511130000||ORU^R01|MSG002|P|2.5\r"
    "PID|1||MRN-9999^^^HOSP-MAIN^MR||SMITH^JOHN||19700101|M\r"
    "OBR|1|ORD002|FIL002|2345-7^Glucose^LN|||20260511\r"
    "OBX|1|NM|2345-7^Glucose^LN||95|mg/dL|74-106||||F\r"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def _sanitize(obj: Any) -> Any:
    """Recursively convert Decimal to float so FHIR projections are JSON-safe.

    fhir.resources uses Pydantic v1 which serializes numeric fields as Decimal.
    stdlib json.dumps does not handle Decimal; convert before chain emission.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _print_resources(resources: list[MappedResource]) -> None:
    for r in resources:
        proj = project_for_chain(r)
        rtype = proj.get("resourceType", "?")
        rid = str(proj.get("id", "?"))[:12]
        code_info = ""
        if "code" in proj:
            codings = proj["code"].get("coding", [{}])
            if codings:
                code_info = f" code={codings[0].get('code', '?')}"
        ident_info = ""
        if "identifier" in proj:
            idents = proj["identifier"]
            if idents:
                ident_info = f" id={str(idents[0].get('value', '?'))[:16]}..."
        print(f"    {rtype}/{rid}{code_info}{ident_info}")


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------


def main() -> None:
    phi_raw = "--phi-raw" in sys.argv

    print("Project AIR Pro -- HL7v2 Clinical Evidence Sidecar Demo")
    print("=" * 60)
    if phi_raw:
        print("NOTE: PHI_RAW mode active (for demo only)")

    # 1. Declare intent capsule with allowed_entities
    _section("Step 1: Declare intent capsule")
    intent = IntentSpec(
        goal="Process lab results for authorized patient MRN-0042",
        allowed_entities=["MRN-0042"],
    )
    print(f"  Goal:             {intent.goal}")
    print(f"  Allowed entities: {intent.allowed_entities}")

    # 2. Create RedactionPolicy (BAA always required)
    _section("Step 2: Configure PHI redaction policy")
    phi_mode = PHIMode.RAW if phi_raw else PHIMode.REDACTED
    policy = RedactionPolicy(baa_acknowledged=True, phi_mode=phi_mode)
    print(f"  PHI mode:          {policy.phi_mode.value}")
    print(f"  BAA acknowledged:  {policy.baa_acknowledged}")

    # mkstemp creates the file atomically (O_EXCL, mode 0600), avoiding the
    # predictable-name race of tempfile.mktemp (CWE-377). Close our handle; the
    # recorder reopens the path to append records.
    _fd, _log_name = tempfile.mkstemp(suffix=".jsonl", prefix="air-e2e-")
    os.close(_fd)
    log_path = Path(_log_name)
    rec = AIRRecorder(log_path=log_path, intent_spec=intent)

    # 3. Parse authorized ORU^R01 (MRN-0042)
    _section("Step 3: Parse authorized ORU^R01 (MRN-0042)")
    msg_ok = parse_hl7v2(SAMPLE_ORU)
    print(f"  Message type:     {msg_ok.message_type}")
    print(f"  Sending facility: {msg_ok.sending_facility}")
    print(f"  Patient MRN:      {msg_ok.pid.primary_mrn if msg_ok.pid else 'N/A'}")
    print(f"  Observations:     {len(msg_ok.obx)}")

    # 4. Map to FHIR R4
    _section("Step 4: Map to FHIR R4")
    fhir_resources = map_to_fhir(msg_ok, redaction_policy=policy)
    print(f"  Resources mapped: {len(fhir_resources)}")
    _print_resources(fhir_resources)

    # 5. Capture as signed capsules with default PHI redaction
    _section("Step 5: Capture as signed intent capsules")
    mrn = msg_ok.pid.primary_mrn if msg_ok.pid else "UNKNOWN"

    # Projections must be sanitized: fhir.resources returns Decimal for numerics
    fhir_projections = [_sanitize(project_for_chain(r)) for r in fhir_resources]

    data_subjects = [
        DataSubjectRef(
            subject_id=mrn,
            subject_type="patient",
            jurisdiction="HIPAA",
        )
    ]

    start_ok = rec.tool_start(
        tool_name="hl7v2_receive",
        tool_args={
            "message_type": msg_ok.message_type,
            "sending_facility": msg_ok.sending_facility,
            "patient_mrn": mrn,
        },
        data_subjects=data_subjects,
        hl7v2_message_type=msg_ok.message_type,
        fhir_resources=fhir_projections,
    )
    rec.tool_end(tool_output="ACK|AA")
    print(f"  tool_start record: {start_ok.step_id[:16]}...")
    print(f"  FHIR resources in chain: {len(start_ok.payload.fhir_resources or [])}")

    # 6. Run detectors (nothing fires for in-scope access)
    _section("Step 6: Run detectors on in-scope access")
    from airsdk.detections import run_detectors

    chain_so_far = load_chain(log_path)
    findings = run_detectors(chain_so_far)
    print(f"  Records in chain: {len(chain_so_far)}")
    print(f"  Findings:         {len(findings)}")
    if findings:
        for f in findings:
            print(f"    [{f.severity}] {f.detector_id}: {f.description[:60]}")
    else:
        print("  No findings -- authorized access is clean.")

    # 7. Inject unauthorized ORU^R01 (MRN-9999)
    _section("Step 7: Inject unauthorized ORU^R01 (MRN-9999)")
    msg_bad = parse_hl7v2(UNAUTHORIZED_ORU)
    bad_mrn = msg_bad.pid.primary_mrn if msg_bad.pid else "UNKNOWN"
    print(f"  Message type:     {msg_bad.message_type}")
    print(f"  Patient MRN:      {bad_mrn}")
    print(f"  (not in allowed_entities -- should trigger SV-ENTITY-01)")

    fhir_bad = map_to_fhir(msg_bad, redaction_policy=policy)
    fhir_bad_projections = [_sanitize(project_for_chain(r)) for r in fhir_bad]

    rec.tool_start(
        tool_name="hl7v2_receive",
        tool_args={
            "message_type": msg_bad.message_type,
            "sending_facility": msg_bad.sending_facility,
            "patient_mrn": bad_mrn,
        },
        data_subjects=[
            DataSubjectRef(
                subject_id=bad_mrn,
                subject_type="patient",
                jurisdiction="HIPAA",
            )
        ],
        hl7v2_message_type=msg_bad.message_type,
        fhir_resources=fhir_bad_projections,
    )
    rec.tool_end(tool_output="ACK|AA")
    print(f"  Injected {len(fhir_bad)} FHIR resource(s) for unauthorized patient.")

    # 8. Verify chain integrity
    _section("Step 8: Verify chain integrity")
    full_chain = load_chain(log_path)
    result = verify_chain(full_chain)
    chain_ok = result.status.value == "ok"
    print(f"  Total records:  {len(full_chain)}")
    print(f"  Chain status:   {result.status.value}")
    print(f"  Chain valid:    {chain_ok}")
    if not chain_ok and result.reason:
        print(f"  Reason:         {result.reason}")

    # 9. Run structural verification (SV-ENTITY-01 fires on MRN-9999)
    _section("Step 9: Structural verification (SV-ENTITY-01)")
    from airsdk.verification import verify_intent

    sv_result = verify_intent(full_chain, intent_spec=intent)
    print(f"  Verdict:          {sv_result.verdict.value}")
    print(f"  Checked steps:    {sv_result.checked_steps} / {sv_result.total_steps}")
    print(f"  Violations:       {len(sv_result.violations)}")
    for v in sv_result.violations:
        print(f"    [{v.severity.upper()}] {v.check_id}: {v.title}")
        print(f"      Evidence: {v.evidence}")
    print(f"  Summary: {sv_result.summary}")

    # 10. Sidecar result summary
    _section("Step 10: Sidecar result summary")
    from airsdk_pro.hl7.types import SidecarResult

    entity_violations = [v for v in sv_result.violations if v.check_id == "SV-ENTITY-01"]
    authorized_result = SidecarResult(
        message_type=msg_ok.message_type,
        patient_mrn=mrn,
        records_written=2,
        fhir_resource_types=[r.resource_type for r in fhir_resources],
        findings_count=0,
    )
    unauthorized_result = SidecarResult(
        message_type=msg_bad.message_type,
        patient_mrn=bad_mrn,
        records_written=2,
        fhir_resource_types=[r.resource_type for r in fhir_bad],
        findings_count=len(entity_violations),
    )

    print(f"  Message 1 (authorized):")
    print(f"    type={authorized_result.message_type}  mrn={authorized_result.patient_mrn}")
    print(f"    records_written={authorized_result.records_written}")
    print(f"    fhir={authorized_result.fhir_resource_types}")
    print(f"    findings={authorized_result.findings_count}")
    print(f"  Message 2 (unauthorized):")
    print(f"    type={unauthorized_result.message_type}  mrn={unauthorized_result.patient_mrn}")
    print(f"    records_written={unauthorized_result.records_written}")
    print(f"    fhir={unauthorized_result.fhir_resource_types}")
    print(f"    findings={unauthorized_result.findings_count}  (SV-ENTITY-01 fired)")

    log_path.unlink(missing_ok=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
