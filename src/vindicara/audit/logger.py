"""Structured audit event logger."""

import time
import uuid
from dataclasses import dataclass, field

import structlog

from vindicara.config.constants import AUDIT_EVENT_GUARD

logger = structlog.get_logger()


@dataclass(frozen=True)
class AuditEvent:
    """An immutable audit event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = AUDIT_EVENT_GUARD
    timestamp: float = field(default_factory=time.time)
    api_key_hash: str = ""
    policy_id: str = ""
    verdict: str = ""
    latency_ms: float = 0.0
    evaluation_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class AuditLogger:
    """Logs audit events. Uses local logging; DynamoDB/S3 storage added when deployed."""

    def __init__(self) -> None:
        self._log = structlog.get_logger("vindicara.audit")

    def log_evaluation(self, event: AuditEvent) -> None:
        self._log.info(
            "audit.event",
            event_id=event.event_id,
            event_type=event.event_type,
            policy_id=event.policy_id,
            verdict=event.verdict,
            latency_ms=event.latency_ms,
            evaluation_id=event.evaluation_id,
        )
