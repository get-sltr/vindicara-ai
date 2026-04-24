"""End-to-end demo: AIR forensic recording over NVIDIA NIM Llama3.

Demonstrates that any OpenAI-compatible inference endpoint, including NVIDIA
NIM, works with `airsdk.integrations.openai.instrument_openai` out of the box.
No NIM-specific code path is needed.

Prerequisites:

    pip install projectair openai
    export NVIDIA_API_KEY=nvapi-...   # from https://build.nvidia.com

Run:

    python packages/projectair/examples/nim_demo.py

The script sends a single prompt to a Llama3 NIM, records the call as a
Signed Intent Capsule, verifies the resulting chain, and prints the captured
prompt and response.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from airsdk.agdr import load_chain, verify_chain
from airsdk.integrations.openai import instrument_openai
from airsdk.recorder import AIRRecorder
from airsdk.types import VerificationStatus

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "meta/llama-3.3-70b-instruct"
LOG_PATH = Path(__file__).parent / "nim_demo_trace.log"


def main() -> int:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("error: set NVIDIA_API_KEY to a free-tier key from https://build.nvidia.com", file=sys.stderr)
        return 2

    try:
        from openai import OpenAI
    except ImportError:
        print("error: pip install openai", file=sys.stderr)
        return 2

    if LOG_PATH.exists():
        LOG_PATH.unlink()

    recorder = AIRRecorder(log_path=LOG_PATH, user_intent="Demo: AIR records a NIM call.")
    raw_client = OpenAI(base_url=NIM_BASE_URL, api_key=api_key)
    client = instrument_openai(raw_client, recorder)

    print(f"Calling {NIM_MODEL} via {NIM_BASE_URL} ...")
    response = client.chat.completions.create(
        model=NIM_MODEL,
        messages=[{"role": "user", "content": "Reply with exactly the word OK."}],
        max_tokens=8,
        temperature=0.0,
    )
    answer = response.choices[0].message.content or ""
    print(f"NIM responded: {answer.strip()!r}")

    records = load_chain(LOG_PATH)
    print(f"Wrote {len(records)} signed records to {LOG_PATH}")
    result = verify_chain(records)
    if result.status != VerificationStatus.OK:
        print(f"chain verification FAILED: {result.status}", file=sys.stderr)
        return 1

    print("Chain verifies. Public key:", recorder.public_key_hex)
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
