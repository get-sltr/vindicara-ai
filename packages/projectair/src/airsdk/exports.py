"""Forensic report export adapters.

Session 1 ships real JSON export. PDF and SIEM raise ``NotImplementedError`` with
an actionable message so the CLI can surface honest coverage instead of producing
placeholder files that look real.
"""
from __future__ import annotations

import json
from pathlib import Path

from airsdk.types import ForensicReport


def export_json(report: ForensicReport, path: str | Path) -> Path:
    """Write the full ForensicReport as pretty-printed JSON."""
    out = Path(path)
    out.write_text(report.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    return out


def export_pdf(report: ForensicReport, path: str | Path) -> Path:  # noqa: ARG001
    raise NotImplementedError(
        "PDF export ships in a later session. Use --format json for now, or "
        "open an issue at https://github.com/get-sltr/vindicara-ai/issues."
    )


def export_siem(report: ForensicReport, path: str | Path) -> Path:  # noqa: ARG001
    raise NotImplementedError(
        "SIEM export ships in a later session. Use --format json for now, or "
        "open an issue at https://github.com/get-sltr/vindicara-ai/issues."
    )
