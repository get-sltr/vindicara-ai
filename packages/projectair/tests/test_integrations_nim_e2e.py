"""End-to-end test: ``instrument_openai`` against a real NVIDIA NIM endpoint.

NIM endpoints expose an OpenAI-compatible chat-completions API, so the
existing OpenAI integration handles them with no NIM-specific code path.
This test proves it: it points an ``openai.OpenAI`` client at the public
NIM endpoint, sends one prompt, and verifies the resulting AgDR chain.

Marked ``network`` so the default ``pytest`` invocation skips it. Skipped
unconditionally when ``NVIDIA_API_KEY`` is not in the environment so the
test never blocks an offline developer.

Manual run:

    NVIDIA_API_KEY=nvapi-... pytest -m network packages/projectair/tests/test_integrations_nim_e2e.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from airsdk.agdr import load_chain, verify_chain
from airsdk.recorder import AIRRecorder
from airsdk.types import StepKind, VerificationStatus

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "meta/llama-3.3-70b-instruct"

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        not os.environ.get("NVIDIA_API_KEY"),
        reason="NVIDIA_API_KEY not set; skipping NIM E2E test.",
    ),
]


def test_instrument_openai_against_real_nim_endpoint(tmp_path: Path) -> None:
    pytest.importorskip("openai")
    from openai import OpenAI

    from airsdk.integrations.openai import instrument_openai

    recorder = AIRRecorder(log_path=tmp_path / "nim.log", user_intent="NIM E2E test.")
    raw = OpenAI(base_url=NIM_BASE_URL, api_key=os.environ["NVIDIA_API_KEY"])
    client = instrument_openai(raw, recorder)

    response = client.chat.completions.create(
        model=NIM_MODEL,
        messages=[{"role": "user", "content": "Reply with exactly the word OK."}],
        max_tokens=8,
        temperature=0.0,
    )

    answer = response.choices[0].message.content or ""
    assert answer.strip(), "NIM returned empty content"

    records = load_chain(tmp_path / "nim.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert (records[0].payload.prompt or "").startswith("user: Reply with exactly the word OK.")
    assert (records[1].payload.response or "").strip() == answer.strip()
    assert verify_chain(records).status == VerificationStatus.OK
