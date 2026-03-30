"""Audit storage backends. DynamoDB and S3 implementations for AWS deployment."""

from typing import Protocol

from vindicara.audit.logger import AuditEvent


class AuditStorage(Protocol):
    """Protocol for audit event storage backends."""

    def store(self, event: AuditEvent) -> None: ...

    def query(self, policy_id: str, start_time: float, end_time: float) -> list[AuditEvent]: ...


class LocalAuditStorage:
    """In-memory audit storage for local development and testing."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def store(self, event: AuditEvent) -> None:
        self._events.append(event)

    def query(self, policy_id: str, start_time: float, end_time: float) -> list[AuditEvent]:
        return [
            e
            for e in self._events
            if e.policy_id == policy_id and start_time <= e.timestamp <= end_time
        ]
