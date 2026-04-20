"""airsdk: signed forensic records for AI agents.

    from airsdk import AIRCallbackHandler
    handler = AIRCallbackHandler(key="...")
    agent = AgentExecutor(callbacks=[handler])
"""
from airsdk.agdr import Signer, load_chain, verify_chain, verify_record
from airsdk.callback import AIRCallbackHandler
from airsdk.detections import (
    UNIMPLEMENTED_DETECTORS,
    detect_goal_hijack,
    detect_tool_misuse,
    run_detectors,
)
from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.types import (
    AGDR_VERSION,
    AgDRPayload,
    AgDRRecord,
    Finding,
    ForensicReport,
    StepKind,
    VerificationResult,
    VerificationStatus,
)

__version__ = "0.1.1"

__all__ = [
    "AGDR_VERSION",
    "AIRCallbackHandler",
    "AgDRPayload",
    "AgDRRecord",
    "Finding",
    "ForensicReport",
    "Signer",
    "StepKind",
    "UNIMPLEMENTED_DETECTORS",
    "VerificationResult",
    "VerificationStatus",
    "__version__",
    "detect_goal_hijack",
    "detect_tool_misuse",
    "export_json",
    "export_pdf",
    "export_siem",
    "load_chain",
    "run_detectors",
    "verify_chain",
    "verify_record",
]
