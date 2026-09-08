"""Shared test setup for the projectair package.

The CLI now enforces a first-run activation email (see
``projectair.firstrun.ensure_identity``), and CLI tests invoke the app through
the Typer callback, so the gate would fire during the suite. Isolate it: point
config at a throwaway dir, supply ``AIR_EMAIL``, and pre-create the
``registered`` marker so the gate is satisfied with zero network calls. Tests
that exercise the gate itself override these via ``monkeypatch``.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _activation_isolation(tmp_path_factory: pytest.TempPathFactory) -> None:
    cfg = tmp_path_factory.mktemp("air-config")
    os.environ["XDG_CONFIG_HOME"] = str(cfg)
    os.environ.setdefault("AIR_EMAIL", "ci@vindicara.io")
    # Recorders print live alerts to stderr by default; tests that exercise
    # the live hook opt in explicitly with AIRRecorder(..., live=True).
    os.environ.setdefault("AIR_LIVE", "0")
    marker_dir = cfg / "projectair"
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "registered").touch()
