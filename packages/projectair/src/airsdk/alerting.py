"""Local, real-time alerting over a growing AgDR chain (free tier).

:class:`LocalAlerter` is the reusable core behind ``air watch``: it runs the
detectors over the records captured so far and returns only the findings it has
not surfaced before, deduplicated by ``(detector_id, step_index)`` so a growing,
append-only chain never re-alerts the same finding.

The same core is intended to later back the recorder hook and hosted cloud
delivery, so the alerting logic lives in exactly one place. This module performs
no I/O and prints nothing; callers (e.g. the ``air watch`` CLI) decide how to
deliver an alert.
"""

from __future__ import annotations

from airsdk.detections import run_detectors
from airsdk.registry import AgentRegistry
from airsdk.types import AgDRRecord, Finding


class LocalAlerter:
    """Surfaces *new* detector findings as a chain grows.

    Call :meth:`new_findings` with the records seen so far; it returns only the
    findings not already reported. Deduplication is by ``(detector_id,
    step_index)`` so repeated calls over an append-only chain never repeat an
    alert.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry
        self._seen: set[tuple[str, int]] = set()

    def new_findings(
        self,
        records: list[AgDRRecord],
        *,
        exclude: frozenset[str] = frozenset(),
    ) -> list[Finding]:
        """Run the detectors over ``records``; return findings not yet seen.

        Safe to call repeatedly on a growing chain: only findings whose
        ``(detector_id, step_index)`` has not been surfaced before come back.

        ``exclude`` names detector ids to hold back on this call. Held-back
        findings are neither returned nor marked seen, so a later call
        without the exclusion still surfaces them (the live recorder hook
        holds AIR-04 until the chain is complete).
        """
        fresh: list[Finding] = []
        for finding in run_detectors(records, registry=self._registry):
            if finding.detector_id in exclude:
                continue
            key = (finding.detector_id, finding.step_index)
            if key not in self._seen:
                self._seen.add(key)
                fresh.append(finding)
        return fresh

    @property
    def seen_count(self) -> int:
        """Number of distinct findings surfaced so far this session."""
        return len(self._seen)
