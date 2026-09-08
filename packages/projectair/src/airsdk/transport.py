"""Transport sinks for ``AIRRecorder`` to write Signed Intent Capsules to.

A transport receives every signed AgDR record the recorder emits and is
responsible for getting it somewhere durable. Two implementations ship in
the OSS package:

- :class:`FileTransport` appends each record as a JSONL line to a local
  log file. This is the historical default behaviour of ``AIRRecorder`` and
  remains what callers get when they pass no ``transports=`` argument.
- :class:`HTTPTransport` (implemented in :mod:`airsdk._http_transport`)
  mirrors records to a remote ingestion endpoint (AIR Cloud, an in-VPC AIR
  Enterprise deployment, or any HTTP server that accepts the AgDR record
  schema) on a background worker thread, so the agent loop is never blocked
  on the network. Set ``AIRSDK_CLOUD_API_KEY`` and every recorder built
  without ``transports=`` gets one automatically (see :mod:`airsdk.cloud_config`).

Recorders accept a list of transports, so callers can compose them: write
to disk *and* push to AIR Cloud, write to disk *and* a custom test sink,
etc. The :class:`Transport` Protocol is intentionally minimal so additional
sinks (S3, Kafka, syslog) can land later without touching the recorder.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Protocol, runtime_checkable

from airsdk._http_transport import HTTPTransport
from airsdk.types import AgDRRecord

_log = logging.getLogger(__name__)


@runtime_checkable
class Transport(Protocol):
    """A sink the recorder hands every signed record to.

    Implementations must be safe to call from any thread the recorder runs
    on. ``emit`` is allowed to be slow on its own time (e.g. disk fsync) but
    must not raise; durability is the implementation's job. ``drain`` is
    called at process shutdown to flush any in-flight work.
    """

    def emit(self, record: AgDRRecord) -> None:
        """Hand a single signed record to this transport."""
        ...

    def drain(self, timeout: float) -> None:
        """Block up to ``timeout`` seconds for in-flight work to complete."""
        ...


class FileTransport:
    """Append each record as a JSONL line to ``log_path``.

    This is the OSS-default transport. Writes are synchronous and force a
    fsync per record so the chain on disk survives power loss. The chain
    file is the canonical state the anchoring orchestrator recovers from at
    startup, so durability of every individual record is load-bearing.

    Throughput, measured by ``scripts/bench_fsync.py`` on macOS APFS
    (1,000 records x 5 runs, median across runs):

    - ``fsync=True`` (default): ~9,000-9,500 records/sec, ~0.11 ms/record
    - ``fsync=False``:           ~9,500-10,200 records/sec, ~0.10 ms/record

    The 5-10% overhead on macOS is a lower bound: macOS ``os.fsync`` flushes
    to the disk controller but does not force the platter write (the strong
    sync is ``fcntl(fd, F_FULLFSYNC)``, not yet wired here). On Linux ext4
    or xfs with real ``fsync`` semantics, expect ~50-200 us per record on
    NVMe and meaningfully more on rotational disks. Agents emitting more
    than ~1,000 steps/sec on a Linux HDD should benchmark before relying
    on the default. ``fsync=False`` weakens crash recovery to "best effort"
    because the OS may buffer the last few records past a power loss.

    Parent directories are created on first write.
    """

    def __init__(self, log_path: str | Path, *, fsync: bool = True) -> None:
        self._log_path = Path(log_path).expanduser()
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._fsync = fsync

    @property
    def log_path(self) -> Path:
        return self._log_path

    def emit(self, record: AgDRRecord) -> None:
        line = record.model_dump_json(exclude_none=True)
        with self._lock, self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")
            handle.flush()
            if self._fsync:
                os.fsync(handle.fileno())

    def drain(self, timeout: float) -> None:
        # Disk writes are synchronous; nothing to wait on.
        del timeout


__all__ = ["FileTransport", "HTTPTransport", "Transport"]
