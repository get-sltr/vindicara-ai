"""airsdk: signed forensic records for AI agents.

    from airsdk import AIRCallbackHandler
    handler = AIRCallbackHandler(key="...")
    agent = AgentExecutor(callbacks=[handler])
"""
from airsdk.agdr import Signer, load_chain, verify_chain, verify_record
from airsdk.article72 import generate_article72_report
from airsdk.callback import AIRCallbackHandler
from airsdk.detections import (
    UNIMPLEMENTED_DETECTORS,
    detect_cascading_failures,
    detect_goal_hijack,
    detect_human_agent_trust_exploitation,
    detect_identity_privilege_abuse,
    detect_insecure_inter_agent_communication,
    detect_mcp_supply_chain_risk,
    detect_memory_context_poisoning,
    detect_prompt_injection,
    detect_resource_consumption,
    detect_rogue_agent,
    detect_sensitive_data_exposure,
    detect_tool_misuse,
    detect_unexpected_code_execution,
    detect_untraceable_action,
    run_detectors,
)
from airsdk.exports import export_json, export_pdf, export_siem
from airsdk.recorder import AIRRecorder, resolve_signing_key
from airsdk.registry import (
    AgentDescriptor,
    AgentRegistry,
    BehavioralScope,
    load_registry,
)
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

__version__ = "0.3.0"

__all__ = [
    "AGDR_VERSION",
    "UNIMPLEMENTED_DETECTORS",
    "AIRCallbackHandler",
    "AIRRecorder",
    "AgDRPayload",
    "AgDRRecord",
    "AgentDescriptor",
    "AgentRegistry",
    "BehavioralScope",
    "Finding",
    "ForensicReport",
    "Signer",
    "StepKind",
    "VerificationResult",
    "VerificationStatus",
    "__version__",
    "detect_cascading_failures",
    "detect_goal_hijack",
    "detect_human_agent_trust_exploitation",
    "detect_identity_privilege_abuse",
    "detect_insecure_inter_agent_communication",
    "detect_mcp_supply_chain_risk",
    "detect_memory_context_poisoning",
    "detect_prompt_injection",
    "detect_resource_consumption",
    "detect_rogue_agent",
    "detect_sensitive_data_exposure",
    "detect_tool_misuse",
    "detect_unexpected_code_execution",
    "detect_untraceable_action",
    "export_json",
    "export_pdf",
    "export_siem",
    "generate_article72_report",
    "load_chain",
    "load_registry",
    "resolve_signing_key",
    "run_detectors",
    "verify_chain",
    "verify_record",
]
