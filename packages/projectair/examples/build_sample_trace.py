"""Generate examples/sample_trace.log from the canonical demo chain.

Both this script and the `air demo` CLI command call ``airsdk._demo.write_sample_log``
so the in-repo sample and the runtime demo can never drift apart.

Run me with the airsdk-installed venv:

    python packages/projectair/examples/build_sample_trace.py
"""
from pathlib import Path

from airsdk._demo import write_sample_log


def main() -> None:
    out_path = Path(__file__).parent / "sample_trace.log"
    signer = write_sample_log(out_path)
    print(f"Wrote {out_path}")
    print(f"Signer public key: {signer.public_key_hex}")


if __name__ == "__main__":
    main()
