"""Tests for ``airsdk.transport``: FileTransport, HTTPTransport, recorder fan-out."""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import ClassVar

import pytest

from airsdk.agdr import Signer, load_chain, verify_chain
from airsdk.recorder import AIRRecorder
from airsdk.transport import FileTransport, HTTPTransport, Transport
from airsdk.types import AgDRPayload, AgDRRecord, StepKind, VerificationStatus


def _signed_record(prompt: str = "hello") -> AgDRRecord:
    signer = Signer.generate()
    return signer.sign(StepKind.LLM_START, AgDRPayload.model_validate({"prompt": prompt}))


def test_file_transport_appends_jsonl(tmp_path: Path) -> None:
    transport = FileTransport(tmp_path / "out.log")
    transport.emit(_signed_record("a"))
    transport.emit(_signed_record("b"))
    transport.drain(timeout=1.0)

    lines = (tmp_path / "out.log").read_text().splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["payload"]["prompt"] == "a"
    assert parsed[1]["payload"]["prompt"] == "b"


def test_file_transport_creates_parent_directories(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c.log"
    transport = FileTransport(nested)
    transport.emit(_signed_record())
    assert nested.exists()


def test_recorder_default_uses_file_transport(tmp_path: Path) -> None:
    """Backward-compat: AIRRecorder(log_path=...) keeps writing to disk."""
    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    assert len(recorder.transports) == 1
    assert isinstance(recorder.transports[0], FileTransport)

    recorder.llm_start(prompt="hi")
    recorder.llm_end(response="hello")

    records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert verify_chain(records).status == VerificationStatus.OK


def test_recorder_fans_out_to_multiple_transports(tmp_path: Path) -> None:
    """Compose disk + custom sink via the explicit transports kwarg."""
    captured: list[AgDRRecord] = []

    class _Sink:
        def emit(self, record: AgDRRecord) -> None:
            captured.append(record)

        def drain(self, timeout: float) -> None:
            del timeout

    file_transport = FileTransport(tmp_path / "r.log")
    sink: Transport = _Sink()
    recorder = AIRRecorder(log_path=tmp_path / "r.log", transports=[file_transport, sink])

    recorder.llm_start(prompt="hi")
    recorder.llm_end(response="ok")

    disk_records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in disk_records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert [r.kind for r in captured] == [StepKind.LLM_START, StepKind.LLM_END]
    assert disk_records[0].step_id == captured[0].step_id


def test_recorder_add_transport_at_runtime(tmp_path: Path) -> None:
    captured: list[AgDRRecord] = []

    class _Sink:
        def emit(self, record: AgDRRecord) -> None:
            captured.append(record)

        def drain(self, timeout: float) -> None:
            del timeout

    recorder = AIRRecorder(log_path=tmp_path / "r.log")
    recorder.llm_start(prompt="before")
    recorder.add_transport(_Sink())
    recorder.llm_end(response="after")

    # First record goes to disk only; second goes to disk and the new sink.
    disk = load_chain(tmp_path / "r.log")
    assert len(disk) == 2
    assert len(captured) == 1
    assert captured[0].kind == StepKind.LLM_END


# -- HTTPTransport tests use a real localhost HTTP server (stdlib) ---------


class _CapturingHandler(BaseHTTPRequestHandler):
    received: ClassVar[list[dict]] = []
    response_status: ClassVar[int] = 201

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8")
        self.__class__.received.append({
            "path": self.path,
            "api_key": self.headers.get("X-API-Key"),
            "run_id": self.headers.get("X-AIR-Run-Id"),
            "content_type": self.headers.get("Content-Type"),
            "body": [json.loads(line) for line in body.splitlines() if line.strip()] if "ndjson" in (self.headers.get("Content-Type") or "") else json.loads(body),
        })
        self.send_response(self.response_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"step_id":"x","stored":true}')

    def log_message(self, format: str, *args) -> None:
        # Suppress test stderr noise.
        return


@pytest.fixture
def http_server():
    _CapturingHandler.received = []
    _CapturingHandler.response_status = 201
    server = HTTPServer(("127.0.0.1", 0), _CapturingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield f"http://127.0.0.1:{port}", _CapturingHandler
    finally:
        server.shutdown()
        thread.join(timeout=2.0)


def test_http_transport_posts_signed_record(http_server) -> None:
    base_url, handler = http_server
    transport = HTTPTransport(endpoint=base_url, api_key="vnd_test")

    record = _signed_record("over the wire")
    transport.emit(record)
    transport.drain(timeout=2.0)
    transport.close()

    assert len(handler.received) == 1
    posted = handler.received[0]
    assert posted["path"] == "/v1/capsules"
    assert posted["api_key"] == "vnd_test"
    assert posted["content_type"] == "application/json"
    assert posted["body"]["payload"]["prompt"] == "over the wire"
    assert posted["body"]["step_id"] == record.step_id


def test_http_transport_does_not_block_emit(http_server) -> None:
    """A slow receiver must not stall the calling thread."""
    base_url, _ = http_server
    transport = HTTPTransport(endpoint=base_url, api_key="vnd_test")

    start = time.monotonic()
    for i in range(50):
        transport.emit(_signed_record(f"msg {i}"))
    elapsed = time.monotonic() - start
    transport.drain(timeout=3.0)
    transport.close()

    # Fifty enqueues should be effectively instant; 250ms is a generous bound.
    assert elapsed < 0.25, f"emit blocked too long: {elapsed}s"


def test_http_transport_drops_when_queue_full() -> None:
    """Bounded queue: dropped records are counted, not crashed on."""
    transport = HTTPTransport(endpoint="http://127.0.0.1:1", api_key=None, queue_capacity=2)

    # Stuff well past the capacity. The worker thread will be slow because
    # 127.0.0.1:1 refuses connections, so many enqueues will hit the bound.
    for i in range(20):
        transport.emit(_signed_record(f"drop {i}"))

    transport.close()
    assert transport.dropped_count > 0


def test_recorder_with_http_transport_writes_disk_and_posts(http_server, tmp_path: Path) -> None:
    """Production composition: disk durable buffer + HTTP push."""
    base_url, handler = http_server
    recorder = AIRRecorder(
        log_path=tmp_path / "r.log",
        transports=[FileTransport(tmp_path / "r.log"), HTTPTransport(base_url, api_key="vnd_test")],
    )

    recorder.llm_start(prompt="hi cloud")
    recorder.llm_end(response="ack")

    # Wait briefly for the HTTP worker to drain.
    deadline = time.monotonic() + 2.0
    while len(handler.received) < 2 and time.monotonic() < deadline:
        time.sleep(0.05)

    disk_records = load_chain(tmp_path / "r.log")
    assert [r.kind for r in disk_records] == [StepKind.LLM_START, StepKind.LLM_END]
    assert len(handler.received) == 2
    posted_kinds = [r["body"]["kind"] for r in handler.received]
    assert posted_kinds == ["llm_start", "llm_end"]


def test_http_transport_sends_run_id_and_batches_as_ndjson(http_server) -> None:
    base_url, handler = http_server
    transport = HTTPTransport(endpoint=base_url, api_key="air_test")
    signer = Signer.generate()
    records = [signer.sign(StepKind.LLM_START, AgDRPayload(prompt=f"p{i}")) for i in range(3)]
    for record in records:
        transport.emit(record)
    transport.drain(timeout=5.0)
    assert transport.run_id == records[0].step_id
    assert transport.sent_count == 3
    assert all(r["api_key"] == "air_test" for r in handler.received)
    assert all(r["run_id"] == records[0].step_id for r in handler.received)
    posted = [rec for r in handler.received for rec in (r["body"] if isinstance(r["body"], list) else [r["body"]])]
    assert [p["step_id"] for p in posted] == [r.step_id for r in records]


def test_http_transport_stops_after_401_and_counts_drops(http_server) -> None:
    base_url, handler = http_server
    handler.response_status = 401
    transport = HTTPTransport(endpoint=base_url, api_key="air_bad")
    signer = Signer.generate()
    transport.emit(signer.sign(StepKind.LLM_START, AgDRPayload(prompt="a")))
    transport.drain(timeout=5.0)
    assert transport.stopped_reason is not None
    assert "401" in transport.stopped_reason
    transport.emit(signer.sign(StepKind.LLM_END, AgDRPayload(response="b")))
    transport.drain(timeout=1.0)
    assert transport.dropped_count == 2
    assert len(handler.received) == 1


def test_http_transport_falls_back_to_single_posts_when_bulk_is_404(http_server) -> None:
    base_url, handler = http_server
    handler.response_status = 201
    original = handler.do_POST

    def do_post(self: object) -> None:  # bulk unsupported on this server
        if self.path.endswith("/bulk"):  # type: ignore[attr-defined]
            self.__class__.response_status = 404  # type: ignore[attr-defined]
        else:
            self.__class__.response_status = 201  # type: ignore[attr-defined]
        original(self)  # type: ignore[arg-type]

    handler.do_POST = do_post  # type: ignore[method-assign]
    try:
        transport = HTTPTransport(endpoint=base_url, api_key="air_test")
        signer = Signer.generate()
        for i in range(3):
            transport.emit(signer.sign(StepKind.LLM_START, AgDRPayload(prompt=f"p{i}")))
        transport.drain(timeout=5.0)
    finally:
        handler.do_POST = original  # type: ignore[method-assign]
    singles = [r for r in handler.received if not r["path"].endswith("/bulk")]
    assert len(singles) == 3
    assert transport.sent_count == 3
