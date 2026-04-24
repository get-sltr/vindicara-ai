# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Routine code edits only need this file. For product decisions, external content, new subsystem design, or full engineering standards, see the **Further reading** section at the bottom.

## Current state (2026-04-24)

Brand hierarchy:
- Company: Vindicara
- Flagship initiative (external-facing, gravity surfaces): Project AIR
- Product tier names (developer-facing, light surfaces): AIR SDK, AIR Cloud, AIR Enterprise
- Technical artifacts (package names, imports, CLI): `air`, `airsdk`, `vindicara`

Rule: use "Project AIR" on hero pages, pitch decks, whitepapers, legal documents, press, investor materials. Use "AIR" in code, docs, CLI, and technical copy where brevity matters.

The AIR pivot shipped. The OSS promise is live on PyPI. Read this before doing anything substantive.

### On PyPI

- `projectair` **0.3.1** is the latest live release (published 2026-04-23). MIT. Ships the `air` CLI and the `airsdk` library. This is the public product. 0.3.1 adds the LlamaIndex LLM integration (`instrument_llamaindex`); detector coverage and Zero-Trust surface are unchanged from 0.3.0.
- 0.3.0 (2026-04-22) is when **full 10 of 10 OWASP Top 10 for Agentic Applications coverage** landed: ASI03 Identity & Privilege Abuse (Zero-Trust-for-agents via operator-declared `AgentRegistry`) and ASI10 Rogue Agents (Zero-Trust behavioral-scope enforcement via declared `BehavioralScope`). Same release shipped `air report article72` for EU AI Act Article 72 post-market monitoring evidence generation.
- Live PyPI versions: 0.1.0–0.1.5, 0.2.1 (ASI06+ASI07), 0.2.3 (ASI05+ASI09), 0.2.4 (ASI08), 0.3.0 (ASI03+ASI10+Article72), 0.3.1 (LlamaIndex). 0.2.0 and 0.2.2 were local-only bumps that got rolled into the next published release.
- To publish a new release: add a `[<ver>]` section to `packages/projectair/CHANGELOG.md` (Keep a Changelog format), bump `packages/projectair/pyproject.toml` + `airsdk/__init__.py`, then from `packages/projectair/`: `rm -f dist/*.whl dist/*.tar.gz && python -m build && python -m twine check dist/* && python -m twine upload dist/projectair-<ver>*`. Always `cd packages/projectair` first; running `python -m build` from the repo root produces a vindicara wheel instead.
- The simple index at `https://pypi.org/simple/projectair/` updates faster than the JSON endpoint when checking propagation. Credentials live in `~/.pypirc` (permissions `-rw-------`, username `__token__`, password is the PyPI API token starting with `pypi-`). With `~/.pypirc` in place, `twine upload` is non-interactive.
- `vindicara` 0.2.0 live, repositioned as "server-side engine behind AIR Cloud." `vindicara` 0.1.0 yanked.

### Detector coverage (honest, ground in actual OWASP specs, do not fabricate)

- OWASP **Top 10 for Agentic Applications** (**10 of 10**):
  - `ASI01` Agent Goal Hijack
  - `ASI02` Tool Misuse & Exploitation
  - `ASI03` Identity & Privilege Abuse (shipped 0.3.0; Zero-Trust-for-agents via `AgentRegistry`: identity forgery / unknown agent / out-of-scope tool / privilege-tier escalation)
  - `ASI04` Agentic Supply Chain Vulnerabilities (partial, MCP only)
  - `ASI05` Unexpected Code Execution (shipped 0.2.2)
  - `ASI06` Memory & Context Poisoning (shipped 0.2.1)
  - `ASI07` Insecure Inter-Agent Communication (shipped 0.2.0)
  - `ASI08` Cascading Failures (shipped 0.2.4; oscillating-pair threshold 4 cycles + fan-out threshold 5 distinct targets / 10-record window, operating over AGENT_MESSAGE records)
  - `ASI09` Human-Agent Trust Exploitation (shipped 0.2.3)
  - `ASI10` Rogue Agents (shipped 0.3.0; Zero-Trust behavioral-scope enforcement via `BehavioralScope`: unexpected tool / fan-out breach / off-hours activity / session tool budget)
- `UNIMPLEMENTED_DETECTORS` is now empty.
- OWASP **Top 10 for LLM Applications** (3 categories, implemented as AIR-specific detectors): `AIR-01` → LLM01 Prompt Injection, `AIR-02` → LLM06 Sensitive Information Disclosure, `AIR-03` → LLM04 Model Denial of Service.
- **AIR-native**: `AIR-04` Untraceable Action (forensic-chain-integrity check; no direct OWASP equivalent).
- Correct public framing as of 0.3.0: **"10 OWASP Agentic + 3 OWASP LLM + 1 AIR-native."** Every public claim must cite this exact taxonomy. Never revert to the "8 of 10" or "3 of 10" framing from earlier releases.
- **ASI10 is Zero-Trust enforcement, not anomaly detection.** Frame it as declared-scope enforcement in every doc, docstring, README, and HN post. The learned-baseline anomaly-detection variant (statistical profiling, peer comparison) is explicitly on the roadmap for a later release and is labelled as such in `detections.py`. Calling the shipped detector "anomaly detection" is overclaim.
- **Do not conflate AIR-04 with ASI10.** AIR-04 detects gaps in our own chain (missing tool_end records, silent intervals). ASI10 Rogue Agents is about agents acting outside their authorization scope / stealth infiltration. OWASP lists signed audit logs as a *mitigation* for ASI10, not a detection signal. Calling AIR-04 "ASI10 coverage" is overclaim. Real ASI10 coverage requires a behavioral-scope detector.

### Terminology: "Intent Capsule" is the public-facing term

OWASP's ASI01 mitigation #5 names "intent capsule" as the emerging pattern for binding declared goal, constraints, and context to each execution cycle in a signed envelope. That is what AIR writes. Lead external comms (README, blog, pitch) with "Signed Intent Capsule." The record-level Python types (`AgDRRecord`, `AgDRPayload`, `packages/projectair/src/airsdk/agdr.py`) stay named AgDR for format compatibility with the accountability.ai/me2resh spec, but describe them as "AgDR-format-compatible Intent Capsules" in docs. This defuses the naming-collision risk around authorship claims on AgDR.

### Roadmap (next)

10 of 10 Agentic shipped as of 0.3.0 (2026-04-22). The OWASP Q3 Solutions Landscape submission bar is cleared. Next-release targets:
- Learned-baseline ASI10 variant (statistical behavioural profile + peer comparison, requires training-data collection)
- Full ASI04 Agentic Supply Chain detector beyond MCP naming patterns (dependency poisoning, tool-manifest tampering)
- Framework integrations: Google Gemini SDK (`google-genai`) and Google ADK (Agent Development Kit, Python + Java); CrewAI; AutoGen (Microsoft v0.4+ line and AG2 community fork are separate targets)
- A2A (Agent-to-Agent) protocol capture as ASI07-aligned new surface, distinct from SDK wrappers
- AIR Cloud (hosted ingestion + dashboard backing the Team tier)

### Framework integrations shipped

LangChain (`AIRCallbackHandler`), OpenAI (`instrument_openai`), Anthropic (`instrument_anthropic`), LlamaIndex (`instrument_llamaindex`, shipped 0.3.1).

**Any OpenAI-compatible endpoint also works via `instrument_openai`** including NVIDIA NIM (`Llama 3.3 70B Instruct NIM`, etc.), vLLM, TGI, Together AI, Groq, Mistral, and Fireworks. Verified by network-gated E2E test at `tests/test_integrations_nim_e2e.py` and runnable demo at `examples/nim_demo.py` (requires `NVIDIA_API_KEY` from build.nvidia.com). This is compatibility through the existing OpenAI integration, not a separate integration module.

On the roadmap: Google Gemini SDK + Google ADK (built locally 2026-04-24, ship in 0.3.2 post-launch), CrewAI, Microsoft AutoGen v0.4+, AG2. A2A protocol capture is tracked separately as a new surface area, not an SDK wrapper. NeMo Guardrails ingestion lands in AIR Cloud Phase 1.5; see `project_nvidia_partnership_roadmap.md` in memory for the full 4-tier NVIDIA roadmap.

### Code location

- `packages/projectair/` is the public MIT package
- `src/vindicara/` is Apache-2.0 engine substrate, not directly pip-installable anymore
- Both live in this monorepo
- Pitch the split as **Snyk-style: MIT CLI + SDK top-of-funnel, commercial engine behind the cloud**

### Working venv

`/Users/KMiI/Desktop/vindicara/.venv-air/` (Python 3.13). `air` binary lives there.

### Context

HF0 pitch + Hacker News launch imminent. Diligence sensitivity is high. Every public claim must be grounded in an actual source document, not plausible-sounding generalization.

### Memory

`/Users/KMiI/.claude/projects/-Users-KMiI-Desktop-vindicara/memory/MEMORY.md` holds persistent user preferences, design system rules, and roadmap notes.

## Commands

Install dev environment (editable, with API + dev extras):

```bash
pip install -e ".[api,dev]"
```

The public `projectair` package has its own pyproject and dev extras:

```bash
pip install -e "packages/projectair[dev]"    # installs the `air` CLI + `airsdk` editable
pytest packages/projectair/tests              # runs the MIT package's own test suite
air demo                                      # 10-second sanity check: signed chain + report
air trace path/to/agent.log                   # replay chain, verify signatures, emit forensic-report.json
```

Lint, format check, type check (runs ruff + mypy strict):

```bash
./scripts/lint.sh
```

Run the full test suite with coverage (fails under 80%):

```bash
./scripts/test.sh
```

Common pytest invocations:

```bash
pytest tests/unit/engine/test_policy.py          # single file
pytest tests/unit/engine/test_policy.py::test_x  # single test
pytest -k "guard and not adversarial"            # keyword filter
pytest -m adversarial                            # adversarial marker only
```

Run the FastAPI backend locally (reload on change):

```bash
uvicorn vindicara.api.app:create_app --factory --reload
```

CDK infrastructure (requires `[cdk]` extra and AWS creds):

```bash
VINDICARA_AWS_ACCOUNT_ID=... cdk synth
VINDICARA_AWS_ACCOUNT_ID=... cdk deploy VindicaraData VindicaraEvents VindicaraAPI
```

Marketing + dashboard site (SvelteKit, `site/`):

```bash
cd site && npm install && npm run dev    # dev server
cd site && npm run check                 # svelte-check (this is the lint bar; failures block deploy)
cd site && npm run build                 # static build (run after check passes)
```

Site deploy script: `scripts/deploy-site.sh`. See `reference_site_deploy.md` in memory for the S3/CloudFront wiring.

## Repo Layout (actual, current)

`docs/SPEC.md` contains an aspirational project-structure diagram inherited from early planning. Ignore it when writing code. The ground truth is below.

### `packages/projectair/` (the public MIT package, this is the product)

- `packages/projectair/pyproject.toml` — own build. Declares `[project.scripts] air = "projectair.cli:main"`. Wheel packages are `src/airsdk` + `src/projectair`.
- `packages/projectair/src/airsdk/` — library surface:
  - `callback.py` (`AIRCallbackHandler` for LangChain)
  - `recorder.py` (`AIRRecorder` that writes signed records)
  - `agdr.py` (BLAKE3 + Ed25519 signing; the "AgDR format" layer, product-labelled "Signed Intent Capsule")
  - `detections.py` (all ASI + AIR-XX detectors)
  - `registry.py` (`AgentRegistry`, `AgentDescriptor`, `BehavioralScope` pydantic schemas; YAML/JSON loader for the operator-supplied Zero-Trust declaration that ASI03 + ASI10 enforce against)
  - `article72.py` + `_article72_content.py` (Markdown report generator behind `air report article72`)
  - `exports.py` (JSON/PDF/CEF emitters)
  - `types.py` (`AgDRRecord`, `AgDRPayload`, `Finding`, `ForensicReport`)
  - `_demo.py` (what `air demo` runs)
- `packages/projectair/src/airsdk/integrations/` — `openai.py` (`instrument_openai`), `anthropic.py` (`instrument_anthropic`), `llamaindex.py` (`instrument_llamaindex`, transparent proxy over any `llama_index.core.llms.LLM` subclass). LangChain lives in `callback.py` (top-level, not in `integrations/`); not planned to relocate.
- `packages/projectair/src/projectair/cli.py` — Typer CLI. Only `air` subcommands live here.
- `packages/projectair/tests/` — pytest suite for the MIT package. Separate from the root `tests/`. Run with `pytest packages/projectair/tests`.
- `packages/projectair/examples/` — `build_sample_trace.py` and `sample_trace.log` for manual testing of `air trace`.

### `src/vindicara/` (Apache-2.0 engine substrate)

- `src/vindicara/sdk/` — public SDK surface (`client.py`, `decorators.py`, `types.py`, `exceptions.py`). `vindicara.__init__` re-exports `Client` and the typed exceptions. The package ships a `py.typed` marker, so downstream `mypy --strict` users get Vindicara's type hints directly.
- `src/vindicara/engine/` — policy engine (`evaluator.py`, `policy.py`, `rules/`). `Evaluator.with_builtins()` is the canonical bootstrap; `PolicyRegistry` holds built-in policies. There is no `cache.py` or `composite.py` yet.
- `src/vindicara/mcp/` — MCP scanner. Uses `scanner.py` + `findings.py` + `prober.py` + `transport.py`. Modules are named `findings`/`prober`, not `inspector`/`bom`/`risk`.
- `src/vindicara/identity/` — agent IAM (`registry.py`, `authz.py`, `models.py`). No `credentials.py` yet.
- `src/vindicara/monitor/` — drift detection (`baseline.py`, `drift.py`, `breaker.py`, `models.py`).
- `src/vindicara/compliance/` — compliance engine. Uses `collector.py` + `reporter.py` + `frameworks.py` + `models.py` (not one file per framework). Frameworks are data-driven.
- `src/vindicara/api/` — FastAPI app. `app.py::create_app()` is the application factory. Routes: `guard`, `policies`, `scans`, `agents`, `reports`, `monitor`, `health`. Middleware: `auth` (API key), `rate_limit`, `request_id`, `security_headers`. A dashboard ASGI sub-app is mounted at `/dashboard`.
- `src/vindicara/dashboard/` — SSR-ish dashboard with its own auth stack (`dashboard/auth/`: passwords, MFA/TOTP, JWT tokens, signup/login middleware), templates, and API key management. Lives behind `/dashboard`.
- `src/vindicara/audit/` — audit logger + storage (DynamoDB/S3).
- `src/vindicara/config/settings.py` — `VindicaraSettings` via pydantic-settings, `VINDICARA_` env prefix. Constants live alongside their module (e.g. `config.constants` is referenced by `engine/evaluator.py`).
- `src/vindicara/infra/` — CDK app. `infra/app.py` is the CDK entry point (wired via `cdk.json`). Stacks: `DataStack` (DynamoDB tables + S3 audit bucket), `EventsStack` (EventBridge bus), `APIStack` (Lambda + API Gateway, wired to the other stacks' outputs). No separate `monitoring_stack.py`.
- `src/vindicara/lambda_handler.py` — Mangum entry point (`handler = Mangum(create_app(), lifespan="off")`). This is what API Gateway calls in production.
- `site/` — SvelteKit 2 + Svelte 5 + Tailwind 4 marketing site and blog (static adapter). Separate from `src/vindicara/dashboard/`.
- `tests/` — pytest. Mirrors `src/` for units (`tests/unit/{engine,mcp,identity,monitor,compliance,sdk,dashboard}`). Integration tests live under `tests/integration/{api,mcp,dashboard}` and hit the real ASGI app via `httpx.AsyncClient` + `ASGITransport` (see `tests/conftest.py`). `TEST_API_KEY = "vnd_test"` is the shared dev key; the `app` fixture registers it via `create_app(dev_api_keys=[...])`.

There is no `tests/e2e/` directory, no `scripts/deploy.sh`, and no `src/vindicara/engine/cache.py`.

## Architecture Notes That Require Reading Multiple Files

- **Policy evaluation flow.** `sdk.Client.guard()` → `engine.Evaluator.evaluate_guard()` → for each of input/output calls `Evaluator.evaluate()` → `PolicyRegistry.get(policy_id).evaluate(text)` → `Policy.evaluate()` runs every `Rule` and folds the rule results into a single `GuardResult` (`blocked` if any rule triggers `CRITICAL`/`HIGH`, else `flagged` if any triggered, else `allowed`). Max input/output lengths come from `config.constants.MAX_INPUT_LENGTH`/`MAX_OUTPUT_LENGTH`. When both input and output are supplied, the worst verdict wins (blocked > flagged > allowed).
- **API middleware stack order matters.** `create_app()` adds middleware in this order: `SecurityHeaders` → `RequestID` → `APIKeyAuth` → `RateLimit` → CORS → dashboard auth. Starlette applies middleware in reverse of add order, so requests traverse CORS first and security headers last. When adding middleware, preserve this order or auth/rate-limit bypass becomes possible.
- **API key store.** `APIKeyStore` lives on `app.state.key_store`. Tests register keys by passing `dev_api_keys=[...]` to `create_app()`; production keys are issued/persisted via the dashboard (`dashboard/keys/`) and the `api_keys_table` DynamoDB table from `DataStack`.
- **Dashboard is mounted, not merged.** `create_app()` imports and mounts `create_dashboard_app()` at `/dashboard`. The `DashboardAuthMiddleware` is added to the parent app (not the sub-app), so dashboard auth runs for every parent-app request. Reordering this also touches the public API.
- **Compliance is data-driven.** Frameworks (EU AI Act Article 72, NIST AI RMF, SOC 2 AI) are defined as data in `compliance/frameworks.py` and consumed by `compliance/collector.py` (`EvidenceCollector`) + `compliance/reporter.py` (`ComplianceReporter`). Do not add a new per-framework module; register a new framework definition instead.
- **SDK namespaces.** `Client` composes sub-namespaces (`MCPNamespace`, `AgentsNamespace`, monitor, compliance), each wrapping a single engine/registry/reporter. Adding a new SDK surface means: build the engine in `src/vindicara/<module>/`, then wire a namespace class inside `sdk/client.py` and expose it as a property on `Client`. Re-export anything public from `vindicara/__init__.py`.
- **Lambda vs local.** `lambda_handler.py` and local `uvicorn` both call `create_app()`, so behavior should be identical. DynamoDB/S3 access in Lambda runs under the IAM role from `APIStack`; locally it falls back to whatever `boto3` picks up from the environment. `VINDICARA_OFFLINE_MODE=true` disables cloud calls entirely for local/SDK use.
- **CDK wiring.** `infra/app.py` instantiates `DataStack` and `EventsStack` first, then passes their outputs into `APIStack` as constructor args. Stacks are NOT auto-discovered; adding a stack means editing `infra/app.py` to instantiate it.

## Quality gates (apply to every roadmap item)

Every shipped feature, OSS or Cloud, must address all four:
1. **End-to-End Proof** — runnable demo a customer can execute in under 60 seconds (`air demo` is the exemplar).
2. **Test Coverage Proof** — measured numbers in release notes, coverage badge or report committed; 80% floor enforced by `./scripts/test.sh`.
3. **Deployment / Readiness Boundary** — explicit `experimental` / `beta` / `production` label on docs, pricing page, and CLI surface. Pricing-page features must be at minimum `beta`. `production` requires SLO + monitoring + runbook.
4. **Customer-Facing Value** — one-sentence customer-language description before engineering starts. If you can't write it, the feature isn't ready to scope.

See `feedback_four_quality_gates.md` in memory for the full discipline.

## Hard rules specific to this repo

- Never use em dashes in any output. Use commas, semicolons, colons, or separate sentences.
- Never suggest or recommend Stripe. Square is the payment processor for Vindicara.
- Never mention Y Combinator or YC.
- Never mention Emirates Airlines.
- No `Any` types, no bare `except`, no `print` in production paths. `mypy --strict` is the bar.
- For untrusted input, do not use dynamic code evaluation primitives, unsafe deserialization libraries, or unsafe YAML loaders. Use typed schemas or safe loaders instead.
- 300 lines max per file. If you need "and" to describe a function, split it.
- Root cause fixes only. No band-aids, no "temporary" patches.

Full engineering standards live in `docs/STANDARDS.md`.

## Further reading (not loaded here)

- `docs/SPEC.md` — product vision, competitive landscape, pricing, GTM sequence, architecture deep-dive, content strategy, fundraise context
- `docs/STANDARDS.md` — full code quality rules, SDK design principles, FastAPI patterns, testing standards, security architecture, performance targets, AWS infrastructure guidance
- `MEMORY.md` (outside repo) — persistent user preferences, design system rules, roadmap notes

Read these when making product decisions, writing external content, or designing a new subsystem. Do not load them for routine code edits.
