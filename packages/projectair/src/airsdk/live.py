"""In-process live alerts: findings print the moment they fire (free tier).

Before this module, ``AIRRecorder`` was write-only. It signed each record to a
JSONL file and never ran a detector, never printed, never summarized; all
sixteen detectors only ran when someone separately typed ``air trace``. Wiring
AIR into a real agent therefore looked like nothing happened.

:class:`LiveAlerts` is the recorder hook :mod:`airsdk.alerting` was written to
back. It writes three things to stderr, and nothing else:

1. A one-line banner on the first record, naming the chain file so the user
   knows where the evidence is going.
2. An alert the instant a detector fires on the chain so far, with the exact
   ``air explain`` command that unpacks it.
3. A summary at interpreter exit: steps recorded, alerts raised, and the
   ``air trace`` command for the full report. "0 alerts across 214 steps,
   chain signed" is how silence stops meaning "broken".

Seeing findings in the terminal is free everywhere. Routing them (Slack,
PagerDuty, hosted retention) is the paid tier.

Disable with ``AIRRecorder(..., live=False)`` or ``AIR_LIVE=0`` in the
environment. Colour follows ``NO_COLOR`` and whether stderr is a TTY.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from airsdk.alerting import LocalAlerter

if TYPE_CHECKING:
    from airsdk.registry import AgentRegistry
    from airsdk.types import AgDRRecord, Finding

#: Environment switch. Any of ``0`` / ``false`` / ``no`` / ``off`` disables.
LIVE_ENV_VAR = "AIR_LIVE"

#: Detectors that only make sense over a finished chain. AIR-04 flags a
#: ``tool_start`` with no ``tool_end`` yet, which is every tool call that is
#: still running. It is held back inline and evaluated once at exit.
INLINE_EXCLUDED_DETECTORS: frozenset[str] = frozenset({"AIR-04"})

#: Run the detectors on every record for the first ``DENSE_SCAN_STEPS``
#: records, then every ``SPARSE_SCAN_EVERY`` records. Detectors re-read the
#: whole chain, so scanning every record forever is quadratic.
DENSE_SCAN_STEPS = 200
SPARSE_SCAN_EVERY = 10

_SEVERITY_RANK: dict[str, int] = {"critical": 3, "high": 2, "medium": 1, "low": 0}
_SEVERITY_COLOR: dict[str, str] = {"critical": "31", "high": "33", "medium": "36"}
_PREFIX = "[air]"
_DESCRIPTION_LIMIT = 160


def live_enabled_from_env() -> bool:
    """``True`` unless ``AIR_LIVE`` is set to an off value."""
    value = os.environ.get(LIVE_ENV_VAR, "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _truncate(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


class LiveAlerts:
    """Print detector findings to stderr as a chain grows.

    Parameters
    ----------
    log_path:
        The chain file the recorder is writing; named in the banner and in
        every ``air`` command hint.
    stream:
        Where to write. ``None`` resolves ``sys.stderr`` at write time so test
        capture and late redirection both work.
    registry:
        Optional agent registry; enables the ASI03 / ASI10 Zero-Trust alerts.
    min_severity:
        Lowest severity printed inline (``medium`` by default). Everything
        the detectors find is still in the chain for ``air trace``.
    """

    def __init__(
        self,
        log_path: str | Path,
        *,
        stream: TextIO | None = None,
        registry: AgentRegistry | None = None,
        min_severity: str = "medium",
    ) -> None:
        if min_severity not in _SEVERITY_RANK:
            raise ValueError(f"min_severity must be one of {sorted(_SEVERITY_RANK)}, got {min_severity!r}")
        self._log_path = Path(log_path)
        self._stream = stream
        self._alerter = LocalAlerter(registry=registry)
        self._min_rank = _SEVERITY_RANK[min_severity]
        self._banner_shown = False
        self._summarized = False
        self._steps = 0
        self._alerts: list[Finding] = []
        self._cloud_url: str | None = None

    # -- Public surface ------------------------------------------------------

    @property
    def alerts(self) -> list[Finding]:
        """Every finding printed so far, in the order it was printed."""
        return list(self._alerts)

    @property
    def steps(self) -> int:
        """Number of records observed so far."""
        return self._steps

    def observe(self, records: list[AgDRRecord]) -> list[Finding]:
        """Called by the recorder after each emit with the chain so far.

        Prints the banner on the first call, then runs the detectors on the
        scan cadence and prints any new finding at or above ``min_severity``.
        Returns the findings printed by this call.
        """
        self._steps = len(records)
        if not self._banner_shown:
            self._banner_shown = True
            self._print_banner()
        if not self._should_scan(len(records)):
            return []
        return self._scan(records, exclude=INLINE_EXCLUDED_DETECTORS)

    def announce_cloud(self, url: str) -> None:
        """Say once, right after the banner, that records are being mirrored and where the run lives."""
        if self._cloud_url is not None:
            return
        self._cloud_url = url
        if not self._banner_shown:
            self._banner_shown = True
            self._print_banner()
        self._write(f"{_PREFIX} mirroring every record (prompts, responses, tool output) to AIR Cloud: {url}")
        self._write(f"{_PREFIX} stop mirroring with AIRSDK_CLOUD=off")

    def summarize(self, records: list[AgDRRecord], *, run_url: str | None = None) -> None:
        """Final pass plus a one-line summary. Idempotent; a no-op on an empty chain."""
        if self._summarized or not records:
            return
        if run_url is not None:
            self._cloud_url = run_url
        self._summarized = True
        self._steps = len(records)
        self._scan(records, exclude=frozenset())
        self._print_summary()

    # -- Internals -----------------------------------------------------------

    @staticmethod
    def _should_scan(count: int) -> bool:
        return count <= DENSE_SCAN_STEPS or count % SPARSE_SCAN_EVERY == 0

    def _scan(self, records: list[AgDRRecord], *, exclude: frozenset[str]) -> list[Finding]:
        shown: list[Finding] = []
        for finding in self._alerter.new_findings(records, exclude=exclude):
            if _SEVERITY_RANK.get(finding.severity, 0) < self._min_rank:
                continue
            self._print_alert(finding)
            shown.append(finding)
        self._alerts.extend(shown)
        return shown

    def _out(self) -> TextIO:
        return self._stream if self._stream is not None else sys.stderr

    def _paint(self, text: str, code: str, *, bold: bool = False) -> str:
        stream = self._out()
        is_tty = getattr(stream, "isatty", lambda: False)()
        if not is_tty or os.environ.get("NO_COLOR"):
            return text
        weight = "1;" if bold else ""
        return f"\x1b[{weight}{code}m{text}\x1b[0m"

    def _write(self, line: str) -> None:
        stream = self._out()
        stream.write(line + "\n")
        stream.flush()

    def _print_banner(self) -> None:
        self._write(f"{_PREFIX} recording signed chain: {self._log_path}")
        self._write(f"{_PREFIX} findings print here as they fire. Report any time: air trace {self._log_path}")

    def _print_alert(self, finding: Finding) -> None:
        color = _SEVERITY_COLOR.get(finding.severity, "37")
        head = f"ALERT  {finding.detector_id}  {finding.severity.upper()}  {finding.title}  (step {finding.step_index})"
        self._write(f"{_PREFIX} {self._paint(head, color, bold=True)}")
        self._write(f"{_PREFIX}        {_truncate(finding.description, _DESCRIPTION_LIMIT)}")
        self._write(f"{_PREFIX}        explain: air explain {self._log_path} --step {finding.step_index}")

    def _print_summary(self) -> None:
        counts: dict[str, int] = {}
        for finding in self._alerts:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        total = len(self._alerts)
        if total:
            breakdown = ", ".join(
                f"{counts[sev]} {sev}" for sev in sorted(counts, key=lambda s: -_SEVERITY_RANK.get(s, 0))
            )
            alerts = f"{total} alert{'s' if total != 1 else ''} ({breakdown})"
            color = "31" if "critical" in counts else "33"
        else:
            alerts = "0 alerts"
            color = "32"
        summary = f"done: {self._steps} step{'s' if self._steps != 1 else ''} recorded, {alerts}, chain signed."
        self._write(f"{_PREFIX} {self._paint(summary, color, bold=True)}")
        self._write(f"{_PREFIX} full report: air trace {self._log_path}")
        if self._cloud_url is not None:
            self._write(f"{_PREFIX} Flightdeck: {self._cloud_url}")
