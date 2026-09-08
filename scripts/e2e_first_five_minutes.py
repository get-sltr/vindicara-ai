"""The first five minutes, end to end and offline.

1. A throwaway identity provider (RSA key, JWKS served locally) mints a token.
2. AIR Cloud runs in-process with in-memory stores and trusts that provider.
3. POST /v1/auth/exchange creates the workspace and hands back the owner key.
4. A fresh venv installs projectair from this tree and runs a six-line agent
   with AIRSDK_CLOUD_API_KEY set: the chain stays on disk and mirrors up.
5. GET /v1/runs shows the run; GET /v1/runs/{id} verifies it and builds the
   timeline; a second exchange returns the same workspace without a key.

Usage: python scripts/e2e_first_five_minutes.py  (from the repo root, with the
engine venv active; uses `uv` for the fresh venv when available).
"""
# ruff: noqa: S603, S607, PT018  (a proof runner: every subprocess argument is ours, and compound asserts read as steps)
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
AUDIENCE = "https://api.vindicara.io"
CLIENT_ID = "e2e-client"


def _jwks_server(public_pem: bytes) -> tuple[HTTPServer, str]:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(serialization.load_pem_public_key(public_pem), as_dict=True)
    jwk["kid"] = "e2e"
    body = json.dumps({"keys": [jwk]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            return None

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def _cloud_server(issuer: str, jwks_uri: str) -> tuple[object, str]:
    import uvicorn

    from vindicara.cloud.factory import create_air_cloud_app
    from vindicara.cloud.signup import ServiceOidc

    os.environ.setdefault("VINDICARA_SESSION_SECRET", "e2e-session-secret-0000000000000000")
    app = create_air_cloud_app(
        service_oidc=ServiceOidc(issuer=issuer, audience=AUDIENCE, jwks_uri=jwks_uri, client_ids=frozenset({CLIENT_ID})),
        cloud_url="http://127.0.0.1:9477",
        console_url="http://127.0.0.1:5173/flightdeck",
    )
    config = uvicorn.Config(app, host="127.0.0.1", port=9477, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:9477/health", timeout=1).read()
            break
        except Exception:
            time.sleep(0.1)
    return server, "http://127.0.0.1:9477"


def _call(method: str, url: str, *, body: dict[str, object] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, object]]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


def _fresh_venv(workdir: Path) -> Path:
    venv = workdir / "venv"
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "-q", "-p", sys.executable, str(venv)], check=True)
        subprocess.run(["uv", "pip", "install", "-q", "--python", str(venv / "bin" / "python"), "-e", str(ROOT / "packages" / "projectair")], check=True)
    else:
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(venv / "bin" / "pip"), "install", "-q", "-e", str(ROOT / "packages" / "projectair")], check=True)
    return venv / "bin" / "python"


AGENT = '''
from airsdk import AIRRecorder
recorder = AIRRecorder(user_intent="What is the status of invoice INV-2291?")
recorder.llm_start(prompt="What is the status of invoice INV-2291?")
recorder.llm_end(response="I should look up the invoice first.")
recorder.tool_start(tool_name="lookup_invoice", tool_args={"invoice_id": "INV-2291"})
recorder.tool_end(tool_output='{"total_usd": 4820.00, "status": "unpaid"}')
recorder.agent_finish(final_output="Invoice INV-2291 is unpaid, total $4,820.00.")
'''


def main() -> int:
    started = time.monotonic()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    jwks, issuer = _jwks_server(public_pem)
    _, cloud_url = _cloud_server(issuer, f"{issuer}.well-known/jwks.json")
    now = int(time.time())
    token = jwt.encode(
        {"iss": issuer, "aud": AUDIENCE, "sub": "auth0|e2e", "azp": CLIENT_ID, "email": "e2e@vindicara.io", "email_verified": True, "iat": now, "exp": now + 600},
        key, algorithm="RS256", headers={"kid": "e2e"},
    )

    print("1. sign in: POST /v1/auth/exchange")
    status, first = _call("POST", f"{cloud_url}/v1/auth/exchange", body={"token": token})
    assert status == 201, (status, first)
    api_key = str(first["api_key"])
    session = str(first["session_token"])
    workspace = first["workspace"]
    assert isinstance(workspace, dict)
    print(f"   workspace {workspace['workspace_id']} ({workspace['name']}), key {api_key[:8]}... shown once")

    print("2. fresh venv, pip install projectair, run a six-line agent with the key set")
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        python = _fresh_venv(workdir)
        env = {**os.environ, "AIRSDK_CLOUD_API_KEY": api_key, "AIRSDK_CLOUD_URL": cloud_url, "AIRSDK_CONSOLE_URL": "http://127.0.0.1:5173/flightdeck", "NO_COLOR": "1", "AIR_LIVE": "1"}
        env.pop("AIRSDK_CLOUD", None)
        run = subprocess.run([str(python), "-c", AGENT], cwd=workdir, env=env, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stderr
        assert "mirroring every record" in run.stderr, run.stderr
        assert "[air] Flightdeck: http://127.0.0.1:5173/flightdeck/runs/" in run.stderr, run.stderr
        run_id = next(line for line in run.stderr.splitlines() if "[air] Flightdeck:" in line).rsplit("/", 1)[1]
        chains = list((workdir / ".air").glob("air-trace-*.log"))
        assert len(chains) == 1 and chains[0].stat().st_size > 0
        print(f"   local chain {chains[0].name}, run {run_id}")

    print("3. the run is on the console side")
    auth = {"Authorization": f"Bearer {session}"}
    status, runs = _call("GET", f"{cloud_url}/v1/runs", headers=auth)
    assert status == 200 and runs["count"] == 1, runs
    row = runs["runs"][0]
    assert isinstance(row, dict) and row["run_id"] == run_id and row["records"] == 5, row
    status, detail = _call("GET", f"{cloud_url}/v1/runs/{run_id}", headers=auth)
    assert status == 200, detail
    verification = detail["verification"]
    timeline = detail["timeline"]
    health = detail["health"]
    assert isinstance(verification, dict) and verification["status"] == "ok"
    assert isinstance(timeline, dict) and len(timeline["entries"]) == 5
    assert isinstance(health, dict) and health["level"] in {"ok", "warn", "fail"}
    status, page = _call("GET", f"{cloud_url}/v1/runs/{run_id}/records?limit=2", headers=auth)
    assert status == 200 and page["count"] == 5 and len(page["records"]) == 2
    print(f"   verified {verification['status']}, {len(timeline['entries'])} timeline rows, health {health['level']}, {detail['findings'].__len__()} finding(s)")

    print("4. second sign-in: same workspace, no key")
    status, second = _call("POST", f"{cloud_url}/v1/auth/exchange", body={"token": token})
    assert status == 200 and second["api_key"] is None and second["workspace"]["workspace_id"] == workspace["workspace_id"]  # type: ignore[index]

    jwks.shutdown()
    print(f"OK in {time.monotonic() - started:.1f}s: sign in, key, paste, run, see it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
