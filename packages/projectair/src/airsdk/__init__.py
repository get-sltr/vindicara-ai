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
    detect_mcp_supply_chain_risk,
    detect_prompt_injection,
    detect_resource_consumption,
    detect_sensitive_data_exposure,
    detect_tool_misuse,
    detect_untraceable_action,
    run_detectors,
)
from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.recorder import AIRRecorder, resolve_signing_key
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

__version__ = "0.1.5"

__all__ = [
    "AGDR_VERSION",
    "UNIMPLEMENTED_DETECTORS",
    "AIRCallbackHandler",
    "AIRRecorder",
    "AgDRPayload",
    "AgDRRecord",
    "Finding",
    "ForensicReport",
    "Signer",
    "StepKind",
    "VerificationResult",
    "VerificationStatus",
    "__version__",
    "detect_goal_hijack",
    "detect_mcp_supply_chain_risk",
    "detect_prompt_injection",
    "detect_resource_consumption",
    "detect_sensitive_data_exposure",
    "detect_tool_misuse",
    "detect_untraceable_action",
    "export_json",
    "export_pdf",
    "export_siem",
    "load_chain",
    "resolve_signing_key",
    "run_detectors",
    "verify_chain",
    "verify_record",
]
