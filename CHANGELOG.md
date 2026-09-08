# Changelog

All notable changes to `vindicara` (the engine substrate) are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

The Apache-2.0-licensed developer SDK ships as `projectair` and has its own changelog at `packages/projectair/CHANGELOG.md`.

## [0.3.0] - 2026-05-08

**Vindicara dogfoods Project AIR.** Every API request and (post-launch) every dashboard auth event is now recorded as a signed AgDR record using the same `airsdk` library customers use, with chains anchored to public Sigstore Rekor. The public chain catalog is published as redacted JSONL and verifiable end-to-end via `air verify-public`.

The trust contract matches customer chains exactly: signatures bind to the moment of action, in-process, with the recorder's key. Anchoring is async via separate cron Lambdas. The published JSONL has bodies replaced by BLAKE3 hashes against a per-kind whitelist (default deny); the cryptographic ordering is preserved end-to-end.

### Added
- `vindicara.ops`: new package implementing the Vindicara ops chain.
  - `vindicara.ops.schema`: 11 event kinds (`vindicara.api.request`, `vindicara.dashboard.auth.*`, `vindicara.ops.*`) plus per-kind redaction whitelist plus denylist field-name list for the property-based test.
  - `vindicara.ops.ddb_transport.DDBTransport`: implements `airsdk.transport.Transport`. Writes each signed AgDR record to a DynamoDB table partitioned by chain_id (Lambda request id) + sort key ord. Two failure modes: HARD (re-raise) for high-stakes operator paths, SOFT (log + continue) for the API hot path.
  - `vindicara.ops.redaction.redact_record`: applies the per-effective-kind whitelist to a record's payload. Default deny; everything not whitelisted becomes `"blake3:" || hex` of the original value's canonical-JSON encoding. Drops the signature field from the public copy because the public payload is no longer the bytes the signature covered.
  - `vindicara.ops.recorder.OpsRecorder`: wrapper around `airsdk.AIRRecorder` exposing Vindicara-specific helpers (`api_request`, `auth_event`, `time_request` context manager). Each helper emits a `tool_start` / `tool_end` pair carrying the same `tool_name` so the redactor can find the right policy entry.
  - `vindicara.ops.recorder.request_chain`: context manager opening one signed chain per Lambda invocation, scoped to a chain_id (Lambda request id or `dashboard:<session>`).
  - `vindicara.ops.anchorer.lambda_handler`: cron Lambda. Scans complete-but-unanchored chains (heuristic: most-recent record older than 5s = chain done). For each, computes BLAKE3 chain root, SHA-256s it for Rekor, submits via `airsdk.anchoring.RekorClient`, writes the returned `log_index` back to every record in the chain.
  - `vindicara.ops.publisher.lambda_handler`: cron Lambda. Reads anchored-but-unpublished chains, applies `redact_record` per row, writes JSONL to `s3://vindicara-ops-chain-public-{account}/ops-chain/<chain-id>.jsonl`. Updates `ops-chain/manifest.json` with the latest log index.
- `vindicara.api.middleware.ops_chain.OpsChainMiddleware`: FastAPI middleware that brackets every API request with a chain entry. Outermost in the middleware stack so auth failures and rate-limit hits are also recorded. Skips public health/docs paths. No-op when `VINDICARA_OPS_CHAIN_TABLE` env is unset (for local dev / tests).
- `vindicara.infra.stacks.ops_chain_stack.OpsChainStack`: provisions DDB table (`vindicara-ops-chain`), public S3 bucket (`vindicara-ops-chain-public-{account}` with public-read on the `ops-chain/*` prefix only), and two cron Lambdas (anchorer, publisher) on a 60s cadence (EventBridge rate minimum). The CDK app wires the api stack against `ops_chain_table` so prod Lambda invocations can write.
- `scripts/e2e_ops_chain.py`: offline smoke test of the full pipeline using in-memory fakes for DDB, S3, and Rekor. Runs in 0.01s, verifies that an `auth_token: "Bearer ..."` payload field never appears in the published JSONL.
- `site/src/routes/ops-chain/+page.svelte`: public verify page on vindicara.io. Fetches the manifest live, shows the latest Rekor log index plus a verify-on-Sigstore link, and explains the trust model + redaction policy.
- `docs/ops-chain.md`: operator-facing runbook (anchorer-falling-behind, publisher-falling-behind, retraction procedure, break-glass key) plus the trust-model statement that backs the public claim.
- `docs/design/ops-chain.md`: architecture rationale, advisor-incorporated trust-model decision (in-process sign at action time vs reconstruct from logs), per-component sequencing, slip-friendly schedule.

### Tests
- 41 unit tests in `tests/unit/ops/`: DDBTransport, redaction (including a 200-case hypothesis property test asserting no denylisted field name leaks into the published JSONL), anchorer (chain-completion detection, anchor failure isolation, log-index write-back), publisher (whitelist passthrough, manifest write, idempotency on failure), recorder (context manager, exception propagation, tool_name pairing).
- 4 unit tests in `tests/unit/ops/test_middleware.py`: the FastAPI middleware records requests, skips health, no-ops when unavailable, attaches `ops` to request state.
- 30 pre-existing API integration tests still pass: the new middleware is non-disruptive in test env.
- ruff clean and mypy --strict clean across `src/vindicara/ops/` and `src/vindicara/api/middleware/ops_chain.py`.

### Notes
- This is engine-side work. Customers do not need to install or import anything new. The `airsdk` library is unchanged.
- Public chain URL stabilizes once `OpsChainStack` is deployed against the Vindicara, Inc. C-Corp account 399827112476 in us-west-2. Until then the manifest 404s and the public verify page shows a "pending deployment" placeholder.
- Cost envelope at launch traffic (~1k req/day): under $5/month total across DDB, two Lambdas, S3, and CloudWatch Logs. Rekor itself is free.
