# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Project AIR by Vindicara: forensic accountability SDK for AI agents. Apache-2.0 CLI (`air`) + library (`airsdk`) on PyPI as `projectair` (MIT through 1.3.1); paid tiers are the hosted product and the Pro package (open core). Layered architecture: detection (0), external trust anchor (1), causal reasoning (2), containment (3), cross-agent trust (4), structural verification + data governance (5, Pro).

Routine code edits only need this file. Product decisions, external copy, and subsystem design: read `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/STANDARDS.md`, `docs/DETECTORS.md` (see **Detailed docs** at the bottom).

## Brand hierarchy

- Company: Vindicara
- Flagship initiative (external-facing, gravity surfaces): Project AIR
- Product tier names (developer-facing): AIR SDK, AIR Cloud, AIR Enterprise
- Technical artifacts (package names, imports, CLI): `air`, `airsdk`, `airsdk_pro`, `vindicara`

Rule: "Project AIR" on hero pages, pitch decks, whitepapers, legal, press, investor materials. "AIR" in code, docs, CLI, and technical copy. "Signed Intent Capsule" is the public-facing term for an AgDR record (OWASP ASI01 mitigation #5 names "intent capsule"); the Python types stay named `AgDRRecord` / `AgDRPayload` for format compatibility with the accountability.ai/me2resh spec and are described in docs as "AgDR-format-compatible Intent Capsules."

## Current state (verified 2026-09-06)

- `projectair` **1.3.1** on PyPI (2026-07-23); working tree is **1.4.0** (unreleased). The license is **Apache License 2.0 from 1.4.0** (MIT through 1.3.1; the user chose Apache 2.0 on 2026-09-07 so the whole repo is under one license); 1.4.0 is the first release under the tiered open-core model (free open-source core on your machine; paid hosted tiers, see `packages/projectair/LICENSING.md`). A BSL 1.1 move was drafted and rejected the same day; do not propose license changes. Python 3.10+, PyPI classifier Production/Stable. Full lineage in `packages/projectair/CHANGELOG.md`; milestones: 0.3.0 (10/10 OWASP Agentic), 0.4.0 (Layer 1), 0.5.0 (Layer 2), 0.6.0 (Layer 3), 0.7.0 (Layer 4 Wave 1), 0.8.0 (ML-DSA-65), 0.9.0 (NVIDIA NeMo/NemoGuard), 1.0.0 (Structural Verification + Data Governance), 1.1.0 (`air watch`, GPU attestation, key custody, delegation, Layer 4 Wave 2), 1.2.0 (`[anchoring]` extra), 1.3.0 (pressure-test hardening: `meta_signed`, fail-closed handoff verify, provenance capture, PHI `ReferenceVault`, ALCOA+, Part 11 e-signatures, `[pqc]` extra), 1.3.1 (first-run capture repointed to `cloud.vindicara.io`; free tier stripped to `air demo` + `air trace`), 1.4.0 (live alerts, `air watch` free, security-review pack, `air incident`, `air health`, Pro $30).
- `projectair-pro` **0.8.0** (`airsdk_pro`, commercial, not on PyPI; requires `projectair>=1.3.0,<2.0`, Python 3.12+). License = locally verified Ed25519-signed token at `~/.airsdk/license.json`; no phone-home at check time. The token is a **console grant**: `GET /v1/entitlements/grant` on AIR Cloud mints it from the workspace's `tier` (free / pro / team / enterprise, 30-day lifetime) and `air grant` installs it; every tier gets one, and a free grant unlocks nothing (`LicenseToken.is_paid`, `is_pro_active()`, `@requires_pro`, and the CLI gate all require a paid tier). Emailed Stripe tokens still install via `air install-license`. Feature strings come only from `airsdk.features` (single source of truth shared by the issuer in `vindicara.licensing`, the `@requires_pro` gate in `airsdk_pro.gate`, and the console).
- `vindicara` engine **0.3.0** in-repo (Apache-2.0; 0.2.0 is the last confirmed PyPI release, 0.1.0 yanked). Positioned as "server-side engine behind AIR Cloud."
- AgDR schema **v0.7** (`AGDR_VERSION` in `airsdk/types.py`). Records set `meta_signed=True`: the signature covers step_id / timestamp / kind / signature_algorithm plus prev_hash + content_hash. Legacy records without `meta_signed` verify over prev_hash + content_hash unchanged.
- Core `cryptography` floor `>=42.0.0,<47.0` (Ed25519 everywhere). ML-DSA-65 (FIPS 204, experimental) needs the `[pqc]` extra (`cryptography>=48`); imports are guarded and raise a clear `RuntimeError` when absent. Layer 1 anchoring (`sigstore` + `rfc3161-client`) is the `[anchoring]` extra; `[dev]` pulls it in. `[webauthn]` covers native WebAuthn delegation.
- Pricing (the site `vindicara-site/src/routes/pricing/+page.svelte` is the source of truth; `air upgrade` mirrors it): Free $0 (`air demo` + `air trace` only), Pro $30/mo (single seat; $99 until 2026-09-07, $25 for one day, $30 from 2026-09-08; the Stripe price and Payment Link are recreated on every change), Team $599/mo base (5 seats + 250k actions/mo, $1.50/1k overage, +$99/seat), Enterprise talk-to-us (self-hosted / air-gapped unit in `deploy/`). The older Individual $39 / Pro $45 models are retired.
- Site deploy model: `vindicara-site` is **adapter-node SSR on ECS Fargate behind an ALB** (CDK stack `VindicaraSiteServer`). The old static S3 + CloudFront sync is gone; do not reintroduce it.
- AWS: workload account `399827112476`, region `us-west-2` (migration from SLTR `335741630084` is complete; nothing hardcodes an account ID any more, `data_stack.py` derives the bucket name from `self.account`). `MIGRATION_PLAN.md` is historical.
- Working venvs (`.venv-air/`, `.venv-infra/`) are **not present** on this machine after the reset; system `python3` is 3.14. Create one before running anything: `python3.13 -m venv .venv-air && .venv-air/bin/pip install -e "packages/projectair[dev]" -e ".[api,dev]"`.

## Claims discipline (enforced on every response)

- Detector count: **"10 OWASP Agentic + 3 OWASP LLM + 3 AIR-native = 16 total."** Never "14" or "8 of 10." AIR-native = AIR-04 Untraceable Action, AIR-05 NemoGuard Safety Classification, AIR-06 NemoGuard Corroboration.
- ASI10 is **declared-scope Zero-Trust enforcement** (`BehavioralScope`), NOT anomaly detection. Learned-baseline variant is roadmap.
- AIR-04 (chain-integrity gap) is NOT ASI10 coverage. Do not conflate.
- ASI04 is partial (MCP naming patterns only). Say so.
- Readiness labels are mandatory on every surface: `experimental` (ML-DSA-65, GPU attestation `air attest`, Layer 4 Wave 1), `beta` (`air watch`, `air report alcoa`, `air report security-review`, `air incident`, `air health`, delegation, self-hosted Enterprise unit), `production` (key custody, IORails bridge, core chain). Pricing-page features must be at least `beta`.
- ALCOA+ / Part 11 language: AIR evidences a faithful, tamper-evident *record*, not a validated (CSV / GAMP 5) *system*. See `packages/projectair/docs/part11-annex11-gap-assessment.md`.
- Every public claim must be grounded in an actual source document. HF0 pitch + Hacker News launch are diligence-sensitive.

## Repo map

- `packages/projectair/` -- the product. Apache-2.0 `air` CLI (`src/projectair/`) + `airsdk` library (`src/airsdk/`). Own `pyproject.toml`, tests, scripts, CHANGELOG.
- `packages/projectair-pro/` -- `airsdk_pro`: license gate, AIR Cloud client, SIEM emitters, alerts, HL7, governance, premium detectors, NIST AI RMF + SOC2-AI reports, `serve.py` (self-hosted server entry). Not on PyPI.
- `packages/air-dashboard/` -- AIR Cloud dashboard (SvelteKit 2, Svelte 5, Tailwind 4, Three.js, Vitest, static adapter, bundle budget).
- `vindicara-site/` -- the deployed product site AND the Flightdeck console (`src/lib/console/`, Auth0 PKCE, live `/v1/*` API). SvelteKit 2 + Svelte 5 + Tailwind 4, adapter-node. Its `Dockerfile` is both the vindicara.io image and the self-hostable Flightdeck artifact.
- `site/` -- LEGACY, not deployed. Do not edit unless explicitly migrating.
- `src/vindicara/` -- Apache-2.0 engine: policy engine, MCP scanner, agent IAM, drift monitor, compliance, `api/` (engine FastAPI), `cloud/` (AIR Cloud ingest FastAPI, separate factory), `ops/` (dogfooded ops chain), `licensing/` (token issuer), `webhooks/` (Stripe), `notifications/` (Resend email), `dashboard/` (legacy SSR dashboard mounted at `/dashboard`), `infra/` (CDK).
- `deploy/` -- AIR Enterprise self-hosted / air-gapped container (beta): `Dockerfile` builds all three Python packages, boots only after the offline license gate passes.
- `tests/` -- pytest for `src/vindicara/` (`unit/`, `integration/`). Separate from `packages/projectair/tests/`.
- `docs/` -- see **Detailed docs**. `docs/superpowers/{plans,specs}` are dated design plans.
- `axiisium/` -- separate exploratory project (multimodal AML model on the Vindicara signing substrate). Not part of the product; leave alone unless asked.
- Root strays: `bedrock_chat.py` (Gradio Bedrock chat), `air-demo-out/`, `air-demo-registry.yaml`, `PRESSURE_TEST_2026-06-22.md` + `FIXES_APPLIED_2026-06-22.md` (audit trail), `AGENTS.md` (Codex mirror of an older CLAUDE.md; stale).
- When the user says "the dashboard," confirm which: `packages/air-dashboard`, Flightdeck (`vindicara-site` `/dashboard`), or legacy `src/vindicara/dashboard/`.

Pitch the split as **open core on a Snyk-style funnel, the Langfuse / LangSmith model: Apache-2.0 CLI + SDK free on your own machine, hosted FlightDeck and evidence packs from $30/month, Team and Enterprise for shared retention and self-hosting**.

## Commands

```bash
# Install (create the venv first; see Current state)
pip install -e "packages/projectair[dev]"          # OSS package (dev pulls [anchoring])
pip install -e "packages/projectair[dev,pqc]"      # + ML-DSA-65
pip install -e "packages/projectair-pro[dev]"      # commercial tier
pip install -e ".[api,dev]"                        # engine + FastAPI
pip install -e ".[cdk]"                            # CDK app deps

# Test: projectair (default addopts skip `network` and `integration` markers)
pytest packages/projectair/tests
pytest packages/projectair/tests/handoff/test_handoff_record.py -k acceptance
pytest packages/projectair/tests -m network        # needs outbound network
pytest packages/projectair/tests -m integration    # needs AIR_AUTH0_* creds
air demo                                           # 60-second end-to-end proof

# Test: engine (80% coverage floor, asyncio_mode=auto, `adversarial` marker)
./scripts/test.sh
pytest tests/unit/engine/test_policy.py
pytest -m adversarial

# Lint + type check (engine: src/ + tests/ only; ruff check + ruff format --check + mypy)
./scripts/lint.sh
cd packages/projectair && ruff check . && mypy src   # OSS package (mypy strict, py310 target)

# E2E demos (from repo root, projectair[dev] installed)
python packages/projectair/scripts/e2e_layer1.py [--live-tsa --live-rekor]
python packages/projectair/scripts/e2e_layer3.py
python packages/projectair/scripts/e2e_layer4.py [--live-rekor]
python packages/projectair/scripts/e2e_attestation.py
python packages/projectair/scripts/e2e_key_rotation.py
python packages/projectair/scripts/e2e_provenance.py
python scripts/e2e_air_cloud.py        # agent -> AIR Cloud -> dashboard, in-process
python scripts/e2e_ops_chain.py        # offline ops-chain pipeline smoke test

# Engine API local
uvicorn vindicara.api.app:create_app --factory --reload

# Product site + Flightdeck console (deployed dir)
cd vindicara-site && npm install && npm run dev     # open /dashboard for Flightdeck
cd vindicara-site && npm run check                  # svelte-check; failures block deploy
cd vindicara-site && npm run test                   # vitest
cd vindicara-site && npm run build

# AIR Cloud dashboard
cd packages/air-dashboard && npm run ci             # check + test + build + bundle:check

# Self-hosted Enterprise unit
docker build -f deploy/Dockerfile -t air-enterprise:local .

# CDK (Python app: cdk.json -> python3 -m vindicara.infra.app)
./scripts/build-lambda.sh
VINDICARA_AWS_ACCOUNT_ID=399827112476 cdk synth
VINDICARA_AWS_ACCOUNT_ID=399827112476 cdk deploy VindicaraData VindicaraEvents VindicaraAPI
VINDICARA_AWS_ACCOUNT_ID=399827112476 scripts/deploy-site.sh   # VindicaraSiteServer; needs Docker

# Publish projectair (ALWAYS cd packages/projectair first; from the root you get a vindicara wheel)
cd packages/projectair && rm -f dist/*.whl dist/*.tar.gz && python -m build && python -m twine check dist/* && python -m twine upload dist/projectair-<ver>*
```

Release checklist: add a `[<ver>]` section to `packages/projectair/CHANGELOG.md` (Keep a Changelog), bump `packages/projectair/pyproject.toml` and `airsdk/__init__.py` `__version__` (and `projectair.__version__`), then publish. `https://pypi.org/simple/projectair/` updates faster than the JSON endpoint. Credentials in `~/.pypirc` (`__token__`).

CI: `ci-projectair.yml` (ruff + pytest on 3.12 / 3.13, gates `packages/projectair/**`), `deploy-site.yml` (site `npm run check`, then `cdk deploy VindicaraSiteServer` via OIDC on push to `main` touching `vindicara-site/**` or the site stack), `sca.yml` (Trivy vuln + license + SBOM, report-only).

## `air` CLI surface (`packages/projectair/src/projectair/`)

`cli.py` hosts `demo`, `trace`, `watch`, `report {article72,alcoa,nist-rmf,soc2-ai}`, `config {set,get,list}`, `version`, `install-license`, `login`, `logout`, `whoami`, `status`, `upgrade`. Every other command lives in its own `*_cli.py` with a `register(app)` function called from `cli.py`: `anchor` / `verify` / `verify-public` (Layer 1), `explain` (Layer 2), `incident` (timeline: what executed / under whose authority / where evidence is missing; terminal free, `--output` pack licensed), `health` (eight evidence checks over a chain or directory, exit code for cron / CI, free), `grant` (pull the workspace's console grant), `login` (Auth0 device flow, then `POST /v1/auth/exchange` for the workspace and the shown-once owner key, saved to `config.toml` 0600), `push` (NDJSON batches per run with `X-AIR-Run-Id`, prints run links), `approve` (Layer 3), `handoff verify` (Layer 4), `verify-intent`, `authorize` / `verify-delegation`, `push`, `attest`, and the Pro commands `cloud {push-webhook,push-s3}`, `siem {datadog,splunk,sumo,sentinel,slack}`, `alert {slack,pagerduty,webhook}`, `governance {index,query,dsar,export,classify}`, `hl7 {parse,capture}`, `detect-premium`. Pro command bodies import `airsdk_pro` lazily so OSS-only installs still load the CLI and print an upgrade prompt. `firstrun.py` is the first-run email capture (posts to `https://cloud.vindicara.io/v1/identity/register`, best-effort, never blocks).

## `airsdk` layout (`packages/projectair/src/airsdk/`)

- Core: `recorder.py` (`AIRRecorder`; consumes `containment=`, `auth0_verifier=`, `intent_spec=`, `capture_policy=`), `agdr.py` (BLAKE3 + Ed25519 / ML-DSA-65 signing, `meta_signed`), `types.py` (`AgDRRecord`, `StepKind`, `SigningAlgorithm`, `AGDR_VERSION`), `transport.py` (`FileTransport` fsyncs per record; `HTTPTransport`), `detections.py` (all 16 detectors), `registry.py` (`AgentRegistry`, `BehavioralScope`), `exports.py` (JSON / PDF / CEF), `callback.py` (LangChain `AIRCallbackHandler`, at the top level, not under `integrations/`). `incident.py` + `_incident_authority.py` + `_incident_render.py` back `air incident`; authority is resolved only from records the chain carries (delegation, approval, intent, key transition, anchor) and a step with none is `agent-key`. `health.py` backs `air health` (integrity, custody, verification support, completeness, anchoring, authority, detectors, freshness); it counts anchors, never re-verifies them. `cloud_config.py`: `AIRSDK_CLOUD_API_KEY` makes every recorder built without `transports=` mirror to AIR Cloud (`AIRSDK_CLOUD=off` kills it); `_http_transport.py` is the batching, retrying `HTTPTransport` (header `X-API-Key`, `X-AIR-Run-Id` = genesis step_id). `log_path` defaults to a fresh `.air/air-trace-<unix ms>.log` per run.
- `_compat.py`: import `UTC` and `StrEnum` from here, never from the stdlib (3.10 support). `features.py`: the entitlement-feature vocabulary; never introduce a bare feature string.
- Layers: `anchoring/` (1), `causal/` (2), `containment/` (3), `handoff/` (4), `verification/` (structural verification, SV-SECRET / SV-NET / SV-SCOPE / SV-EXFIL / SV-AUTH), `delegation/` (Delegated Authority genesis + WebAuthn), `attestation/` (NVIDIA NRAS GPU attestation), `key_custody.py` (`rotate_signer` / `verify_key_custody`).
- Regulated-industry additions (1.3.0): `esignature.py` (21 CFR Part 11 §11.50 `SignatureMeaning`), `alcoa.py` (`air report alcoa`), `reference_vault.py` (`CapturePolicy.phi_safe()` + erasable `ReferenceVault`; salted BLAKE3 digests replace PHI before signing).
- `integrations/`: `openai`, `anthropic`, `llamaindex`, `gemini` (+ `_gemini_streams`), `adk`, `nemo_guardrails`, `nemoguard`, `nemoclaw`; `_provenance.py` builds the shared `DecisionProvenance`. NVIDIA NIM / vLLM / Groq etc. go through `instrument_openai`.
- Demos: `_concrete_demo.py` is what `air demo` runs (poisoned README to SSH-key exfil); `_healthcare_demo.py`; `_demo.py` is the old sanity demo.
- Tests mirror the subpackages (`tests/anchoring/`, `causal/`, `containment/`, `handoff/`, `verification/`, `delegation/`, `attestation/`).

## Architecture notes that require reading multiple files

- **The five-minute loop (AIR Cloud self-serve).** `POST /v1/auth/exchange` (`cloud/routes/auth.py`, `cloud/signup.py`) verifies an Auth0 token against the service trust (`AIR_CLOUD_OIDC_ISSUER` / `_AUDIENCE` = `https://api.vindicara.io` / `_CLIENT_IDS`), links `(issuer, sub)` (and verified email) to one personal workspace (`cloud/identity_store.py`, DynamoDB `air-cloud-identities`), creates it and the owner key on first sign-in, and returns a session token plus the key exactly once. Runs: ingest resolves `run_id` (header first, then in-batch lineage; `cloud/runs.py`), upserts `air-cloud-runs` (`cloud/run_store.py`), and `GET /v1/runs`, `/v1/runs/{id}`, `/v1/runs/{id}/records` back the Flightdeck Runs screens (`vindicara-site/src/lib/console/screens/{Keys,Runs,RunDetail}.svelte`, client `api/cloud.ts`, session `stores/cloud.ts`). The Lambda hydrates secrets from Secrets Manager at cold start (`cloud/secrets.py`) and refuses to start if a configured secret is unreadable. Tenant-side prerequisites: the Auth0 API `https://api.vindicara.io` exists, both the SPA and the CLI client are authorized for it, and (recommended) an Action adds `https://vindicara.io/email` + `email_verified` claims.
- **Two FastAPI apps in the engine.** `vindicara.api.app.create_app()` is the engine API (guard / policies / scans / agents / reports / monitor / capsules / Stripe webhook, dashboard mounted at `/dashboard`). `vindicara.cloud.factory` builds the separate AIR Cloud ingest app (`/v1/capsules`, workspaces, keys, findings, analytics, SSO, stream) that `AirCloudStack` deploys and `airsdk_pro.serve` runs self-hosted; it auto-wires DynamoDB stores when `AIR_CLOUD_*_TABLE` env vars are set, in-memory otherwise.
- **Engine middleware order.** `create_app()` adds, in order: `OpsChain`, `SecurityHeaders`, `RequestID`, `APIKeyAuth`, `RateLimit`, CORS, then `DashboardAuth` after routers. Starlette's `add_middleware` inserts at index 0 and wraps in reverse, so the LAST added is OUTERMOST. The inline comment claiming OpsChain is outermost "because it is added first" contradicts this; verify with a test before relying on ops-chain coverage of auth-rejected requests. Preserve add order when adding middleware or auth / rate-limit bypass becomes possible.
- **Policy evaluation flow.** `sdk.Client.guard()` -> `engine.Evaluator.evaluate_guard()` -> per input/output `Evaluator.evaluate()` -> `PolicyRegistry.get(id).evaluate(text)` -> `Policy.evaluate()` folds rule results into one `GuardResult` (`blocked` on CRITICAL/HIGH, else `flagged`, else `allowed`; worst verdict wins across input + output). Lengths from `config.constants`.
- **Compliance is data-driven.** Frameworks live as data in `compliance/frameworks.py`, consumed by `collector.py` + `reporter.py`. Register a definition; do not add per-framework modules.
- **SDK namespaces.** `Client` composes namespaces each wrapping one engine. New surface = engine in `src/vindicara/<module>/`, namespace in `sdk/client.py`, re-export from `vindicara/__init__.py`.
- **CDK wiring.** `infra/app.py` instantiates every stack explicitly (`VindicaraData`, `VindicaraEvents`, `VindicaraOpsChain`, `AirCloud`, `VindicaraAPI`, `SiteStack`, `VindicaraSiteServer`); stacks are not auto-discovered. Account resolves from `CDK_DEFAULT_ACCOUNT` / `VINDICARA_AWS_ACCOUNT_ID`.
- **Lambda vs local.** `lambda_handler.py` (Mangum) and `uvicorn` both call `create_app()`. `VINDICARA_OFFLINE_MODE=true` disables cloud calls.
- **Chain signing keys vs anchoring keys.** Chain signer is Ed25519 (default) or ML-DSA-65; `Signer` autodetects from key type and `AgDRRecord.signature_algorithm` dispatches verification; mixed chains verify. Layer 1 `RekorClient` signs the already-hashed 32-byte chain root with **ECDSA P-256 in `Prehashed` mode**. Do not "fix" anchoring to Ed25519 or ML-DSA: both break Rekor inclusion-proof verification empirically. Two-key model is intentional.
- **Layer 1 chain-as-spool.** `AnchoringOrchestrator` keeps no in-memory pending buffer; the fsynced on-disk chain is the spool and `hydrate_from_chain` re-emits pending anchors on startup. Default cadence every 100 steps or 10 s. macOS `os.fsync` is weaker than `F_FULLFSYNC` (not wired); ~5% APFS overhead per `bench_fsync.py`. `FileTransport(path, fsync=False)` opts out.
- **Layer 3 fail-closed.** Forged / wrong-issuer / replayed approval tokens leave the halted action halted (`approve()` keeps a single-use jti ledger). Deny rules in `ContainmentPolicy` always override step-up rules. `Auth0Verifier` is generic OIDC + JWKS (RS256/384/512), named for the documented target.
- **Layer 4 fail-closed.** `reconcile_channels` hard-fails when JWT `air_ptid`, W3C `traceparent`, and `Air-Parent-Trace-Id` disagree; `AdapterRouter` rejects unregistered issuers; verifier step 7 uses two-bound temporal math (naive `>` forbidden); `validation_proof` hashes every identifier so public Rekor carries no topology. `air handoff verify` fails closed without an issuer-signed capability-token JWT (`--allow-unverified-token` opts into the sidecar model); the library `CrossAgentVerifier(require_capability_token_jwt=...)` defaults permissive. `canonicalize` (RFC 8785) deliberately rejects bytes / datetime / UUID / Decimal / Enum / pathlib / tuple; do not relax without coordinating every IdP adapter. Only `Auth0Adapter` is live; Okta / Entra / Spiffe raise `IdPNotImplementedError`.
- **License and entitlement.** `vindicara.licensing.issuer` mints Ed25519 tokens after the Stripe webhook (`api/routes/stripe_webhook.py`, mounted on the engine app and deployed by `APIStack`; it handles `checkout.session.completed` and `invoice.paid`, returns `{"status": ...}` / `{"error": ...}`, and 5xxs on any fulfillment failure so Stripe retries) confirms checkout and `notifications/email.py` delivers them via Resend; `airsdk_pro.license` verifies locally against the embedded public key; `airsdk.features` is the only place feature strings are defined. Tests assert the three sites agree.
- **Ops chain (dogfooding).** `api/middleware/ops_chain.py` records every engine request as a signed AgDR record via `vindicara.ops` (DDB transport, redaction at publish time, anchorer + publisher cron Lambdas at 60 s from `OpsChainStack`); no-op when `VINDICARA_OPS_CHAIN_TABLE` is unset. Public catalog at `https://vindicara.io/ops-chain/`. Trust contract equals customer chains.

## Quality gates (apply to every roadmap item)

1. **End-to-End Proof**: runnable demo under 60 seconds (`air demo` is the exemplar).
2. **Test Coverage Proof**: measured numbers in release notes; 80% floor via `./scripts/test.sh`.
3. **Deployment / Readiness Boundary**: explicit `experimental` / `beta` / `production` label on docs, pricing page, CLI. `production` requires SLO + monitoring + runbook.
4. **Customer-Facing Value**: one-sentence customer-language description before engineering starts.

## Hard rules specific to this repo

- Never use em dashes in any output. Use commas, semicolons, colons, or separate sentences.
- Never mention Emirates Airlines.
- The "AIR" wordmark is ALWAYS rendered in brand red (`--air` / `#e63946`) everywhere it appears. The full lockup is `V/P AIR` with "AIR" in red. Never render "AIR" in a neutral color.
- Never use the SF Mono typeface anywhere in the stack. Use the approved monospace instead.
- No dim / low-contrast text on any user-facing surface. Readable text is full-contrast white (`--white`); de-emphasize with weight / size / position, never with a faint color. Fix existing dim text opportunistically when already in the file.
- No `Any` types, no bare `except`, no `print` in production paths. `mypy --strict` is the bar (projectair: py310 target + pydantic plugin; engine: py312).
- No dynamic code evaluation (`eval`, `exec`, `pickle`, unsafe YAML) on untrusted input.
- 300 lines max per file. If you need "and" to describe a function, split it.
- Root cause fixes only. No band-aids, no "temporary" patches.
- Import `UTC` / `StrEnum` from `airsdk._compat`, never from the stdlib, inside `packages/projectair/`.

## Roadmap (next)

- Layer 4 v1.5: private / enterprise federation (custom CA roots, archived JWKS); live `OktaAdapter` / `EntraAdapter` / `SpiffeAdapter`.
- Layer 1: anchoring key rotation with key transparency log; bundled TSA root set; `docs/anchoring.md` + `docs/threat-model.md`.
- Learned-baseline ASI10 variant (statistical profile + peer comparison).
- Full ASI04 supply-chain detector beyond MCP naming patterns.
- Framework integrations: CrewAI; AutoGen (Microsoft v0.4+ and AG2 fork are separate targets). A2A capture is a separate surface, not an SDK wrapper.
- LangChain / OpenAI tool-call interceptor wrappers so containment fires without manual `tool_start`.
- AIR Cloud: hosted ingestion + dashboard backing the Team tier; NeMo Guardrails ingestion in Phase 1.5.

## Detailed docs (read when working in the relevant area)

- `docs/DETECTORS.md` -- full detector taxonomy and framing discipline. Read before editing detectors or public copy.
- `docs/ARCHITECTURE.md` -- layered spine, crypto trust contracts, release details, integrations, ops chain, roadmap. Its "current state" header lags CHANGELOG (says 1.3.0); trust CHANGELOG for versions.
- `docs/STANDARDS.md` -- engineering standards, SDK design, FastAPI patterns, testing, security, performance, AWS infra.
- `docs/SPEC.md` -- product vision, competitive landscape, pricing, GTM, fundraise. Its project-structure diagram is aspirational; the **Repo map** above is ground truth.
- `docs/CLAUDE.md` -- claims discipline for doc edits. `docs/ops-chain.md`, `docs/ops-chain-deploy.md`, `docs/air-cloud-deploy.md`, `docs/admissibility.md`, `docs/ci-deploy-role-iam.md`, `docs/pro-tier-spec.md`, `docs/team-tier-spec.md`, `deploy/README.md`.

Memory: `/Users/itsthekev/.claude/projects/-Users-itsthekev-Developer-projectair/memory/MEMORY.md` (empty after the machine reset; the older memory notes referenced in past versions of this file are gone).
