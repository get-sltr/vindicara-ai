"""Tests for evidence collector."""

import time
from datetime import UTC, datetime

from vindicara.audit.logger import AuditEvent
from vindicara.compliance.collector import EvidenceCollector
from vindicara.compliance.models import EvidenceType
from vindicara.config.constants import (
    AUDIT_EVENT_AGENT_SUSPENDED,
    AUDIT_EVENT_GUARD,
    AUDIT_EVENT_MCP_SCAN,
    AUDIT_EVENT_POLICY_CREATE,
)


class TestEvidenceCollector:
    def test_record_and_collect(self) -> None:
        collector = EvidenceCollector()
        event = AuditEvent(
            event_type=AUDIT_EVENT_GUARD,
            policy_id="content-safety",
            verdict="allowed",
            timestamp=time.time(),
        )
        collector.record(event)
        evidence = collector.collect(system_id="test")
        assert len(evidence[EvidenceType.GUARD_EVALUATION]) == 1

    def test_collect_empty(self) -> None:
        collector = EvidenceCollector()
        evidence = collector.collect(system_id="test")
        for events in evidence.values():
            assert len(events) == 0

    def test_maps_event_types_correctly(self) -> None:
        collector = EvidenceCollector()
        now = time.time()
        collector.record(AuditEvent(event_type=AUDIT_EVENT_GUARD, timestamp=now))
        collector.record(AuditEvent(event_type=AUDIT_EVENT_POLICY_CREATE, timestamp=now))
        collector.record(AuditEvent(event_type=AUDIT_EVENT_MCP_SCAN, timestamp=now))
        collector.record(AuditEvent(event_type=AUDIT_EVENT_AGENT_SUSPENDED, timestamp=now))

        evidence = collector.collect(system_id="test")
        assert len(evidence[EvidenceType.GUARD_EVALUATION]) == 1
        assert len(evidence[EvidenceType.POLICY_CHANGE]) == 1
        assert len(evidence[EvidenceType.MCP_SCAN]) == 1
        assert len(evidence[EvidenceType.AGENT_SUSPENSION]) == 1

    def test_collect_with_period_filter(self) -> None:
        collector = EvidenceCollector()
        now = time.time()
        old_event = AuditEvent(event_type=AUDIT_EVENT_GUARD, timestamp=0.0)
        new_event = AuditEvent(event_type=AUDIT_EVENT_GUARD, timestamp=now)
        collector.record(old_event)
        collector.record(new_event)

        # Derive the quarter from the event itself. Hardcoding one made this
        # pass only while the wall clock sat inside it, so it started failing
        # the moment real time left that quarter.
        stamp = datetime.fromtimestamp(now, tz=UTC)
        period = f"{stamp.year}-Q{(stamp.month - 1) // 3 + 1}"

        evidence = collector.collect(system_id="test", period=period)
        assert len(evidence[EvidenceType.GUARD_EVALUATION]) == 1
