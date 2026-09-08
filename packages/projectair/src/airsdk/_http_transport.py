"""``HTTPTransport``: mirror signed records to AIR Cloud without blocking the agent.

Records are queued and shipped by a daemon worker in batches: one record goes
to ``/v1/capsules``, several go as NDJSON to ``/v1/capsules/bulk``. The worker
sends ``X-AIR-Run-Id`` (the genesis step_id it saw first) so the server never
has to reconstruct which run a record belongs to. A 429 or 5xx is retried with
backoff; a 401 or 403 stops the transport after one warning, because retrying
a bad key forever only fills the log. Records the server refuses for their
content (4xx) are logged and skipped; the local chain still has them.

``drain`` waits for the queue *and* the batch in flight, so a six-line script
that exits immediately still gets its records onto the wire.
"""
from __future__ import annotations

import atexit
import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from airsdk.types import GENESIS_PREV_HASH, AgDRRecord

if TYPE_CHECKING:
    from airsdk.cloud_config import CloudConfig

_log = logging.getLogger(__name__)

DEFAULT_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_QUEUE_CAPACITY = 10_000
DEFAULT_DRAIN_TIMEOUT_SECONDS = 5.0
DEFAULT_BATCH_SIZE = 100
API_KEY_HEADER = "X-API-Key"
RUN_ID_HEADER = "X-AIR-Run-Id"
_RETRY_DELAYS_SECONDS = (0.5, 1.0, 2.0)
_STOP_STATUSES = frozenset({401, 403})


class HTTPTransport:
    """POST records to a remote ``/v1/capsules`` endpoint on a background worker.

    Parameters
    ----------
    endpoint:
        Base URL of the receiving server; ``/v1/capsules`` and
        ``/v1/capsules/bulk`` are appended.
    api_key:
        Workspace API key, sent as ``X-API-Key`` (AIR Cloud and AIR Enterprise).
        Pass ``api_key_header=`` when pointing at a receiver that uses another name.
    timeout, queue_capacity, batch_size:
        Per-request timeout, the bound on queued records before drops begin,
        and the most records shipped per bulk request.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        *,
        api_key_header: str = API_KEY_HEADER,
        timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
        queue_capacity: int = DEFAULT_QUEUE_CAPACITY,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError(f"endpoint must start with http:// or https://, got {endpoint!r}")
        base = endpoint.rstrip("/")
        self._url = base + "/v1/capsules"
        self._bulk_url = base + "/v1/capsules/bulk"
        self._api_key = api_key
        self._api_key_header = api_key_header
        self._timeout = timeout
        self._batch_size = max(1, batch_size)
        self._queue: queue.Queue[AgDRRecord | None] = queue.Queue(maxsize=queue_capacity)
        self._outstanding = 0
        self._cv = threading.Condition()
        self._dropped = 0
        self._sent = 0
        self._stopped_reason: str | None = None
        self._run_id: str | None = None
        self._bulk_supported = True
        self._worker = threading.Thread(target=self._run, daemon=True, name="airsdk-http-transport")
        self._worker.start()
        atexit.register(self._atexit_drain)

    @classmethod
    def from_config(cls, config: CloudConfig) -> HTTPTransport:
        """A transport aimed at the cloud described by ``config``."""
        return cls(config.url, config.api_key)

    @property
    def endpoint(self) -> str:
        return self._url

    @property
    def dropped_count(self) -> int:
        """Records dropped because the queue was full or the transport was stopped."""
        return self._dropped

    @property
    def sent_count(self) -> int:
        """Records the server accepted."""
        return self._sent

    @property
    def run_id(self) -> str | None:
        """The run this transport is shipping, once a genesis record has been seen."""
        return self._run_id

    @property
    def stopped_reason(self) -> str | None:
        """Why the transport stopped shipping (a 401 or 403), or ``None`` while healthy."""
        return self._stopped_reason

    # -- Transport protocol -------------------------------------------------

    def emit(self, record: AgDRRecord) -> None:
        if self._run_id is None and record.prev_hash == GENESIS_PREV_HASH:
            self._run_id = record.step_id
        if self._stopped_reason is not None:
            self._dropped += 1
            return
        with self._cv:
            self._outstanding += 1
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            self._settle(1)
            self._dropped += 1
            _log.warning("airsdk.http_transport queue full; dropping record", extra={"step_id": record.step_id, "dropped_total": self._dropped})

    def drain(self, timeout: float) -> None:
        """Block up to ``timeout`` seconds until every queued and in-flight record is settled."""
        deadline = time.monotonic() + timeout
        with self._cv:
            while self._outstanding > 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                self._cv.wait(remaining)

    def close(self) -> None:
        """Signal the worker to exit and wait briefly for it to finish."""
        self._queue.put(None)
        self._worker.join(timeout=DEFAULT_DRAIN_TIMEOUT_SECONDS)

    # -- Internals ----------------------------------------------------------

    def _atexit_drain(self) -> None:
        self.drain(DEFAULT_DRAIN_TIMEOUT_SECONDS)

    def _settle(self, count: int) -> None:
        with self._cv:
            self._outstanding = max(0, self._outstanding - count)
            self._cv.notify_all()

    def _run(self) -> None:
        while True:
            first = self._queue.get()
            if first is None:
                return
            batch = [first]
            while len(batch) < self._batch_size:
                try:
                    more = self._queue.get_nowait()
                except queue.Empty:
                    break
                if more is None:
                    self._ship(batch)
                    return
                batch.append(more)
            self._ship(batch)

    def _ship(self, batch: list[AgDRRecord]) -> None:
        try:
            if self._stopped_reason is not None:
                self._dropped += len(batch)
            elif len(batch) == 1 or not self._bulk_supported:
                for record in batch:
                    self._post_with_retry(self._url, record.model_dump_json(exclude_none=True).encode("utf-8"), "application/json", count=1)
            else:
                body = "\n".join(r.model_dump_json(exclude_none=True) for r in batch).encode("utf-8")
                self._post_with_retry(self._bulk_url, body, "application/x-ndjson", count=len(batch))
        except Exception as exc:
            # The worker must never die: the local chain is the durable path.
            _log.warning("airsdk.http_transport batch failed", extra={"records": len(batch), "error": str(exc)})
        finally:
            self._settle(len(batch))

    def _headers(self, content_type: str) -> dict[str, str]:
        headers = {"Content-Type": content_type, "User-Agent": "airsdk-http-transport"}
        if self._api_key:
            headers[self._api_key_header] = self._api_key
        if self._run_id:
            headers[RUN_ID_HEADER] = self._run_id
        return headers

    def _post_with_retry(self, url: str, body: bytes, content_type: str, *, count: int) -> None:
        for attempt, delay in enumerate((*_RETRY_DELAYS_SECONDS, None)):
            status = self._post_once(url, body, content_type, count=count)
            if status is None:
                return
            if status in _STOP_STATUSES:
                self._stopped_reason = f"server answered {status}; check AIRSDK_CLOUD_API_KEY"
                _log.warning("airsdk.http_transport stopped: %s", self._stopped_reason)
                self._dropped += count
                return
            if status == 404 and url == self._bulk_url:
                self._bulk_supported = False
                for line in body.decode("utf-8").splitlines():
                    self._post_with_retry(self._url, line.encode("utf-8"), "application/json", count=1)
                return
            if status != 429 and status < 500:
                self._dropped += count
                return
            if delay is None or attempt >= len(_RETRY_DELAYS_SECONDS):
                self._dropped += count
                return
            time.sleep(delay)

    def _post_once(self, url: str, body: bytes, content_type: str, *, count: int) -> int | None:
        """POST once. ``None`` on success, else the HTTP status (0 for a network error)."""
        request = urllib.request.Request(url, data=body, headers=self._headers(content_type), method="POST")  # noqa: S310 - scheme enforced at construction
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - scheme enforced at construction
                response.read()
        except urllib.error.HTTPError as exc:
            detail = _detail(exc)
            _log.warning("airsdk.http_transport server answered %s: %s", exc.code, detail, extra={"status": exc.code, "records": count})
            return exc.code
        except Exception as exc:
            _log.warning("airsdk.http_transport request failed: %s", exc, extra={"records": count})
            return 0
        self._sent += count
        return None


def _detail(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return ""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:200]
    return str(parsed.get("detail", raw))[:200] if isinstance(parsed, dict) else raw[:200]


__all__ = ["API_KEY_HEADER", "RUN_ID_HEADER", "HTTPTransport"]
