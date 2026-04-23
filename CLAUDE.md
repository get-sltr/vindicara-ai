# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state (2026-04-22)
Brand hierarchy:
- Company: Vindicara
- Flagship initiative (external-facing, gravity surfaces): Project AIR
- Product tier names (developer-facing, light surfaces): AIR SDK, AIR Cloud, AIR Enterprise
- Technical artifacts (package names, imports, CLI): air, airsdk, vindicara

Rule: use "Project AIR" on hero pages, pitch decks, whitepapers, legal documents, press, investor materials. Use "AIR" in code, docs, CLI, and technical copy where brevity matters.
The AIR pivot shipped. The OSS promise is live on PyPI. Read this before doing anything substantive.

**On PyPI:**
- `projectair` **0.3.0** is the latest live release (published 2026-04-22). MIT. Ships the `air` CLI and the `airsdk` library. This is the public product. **Full 10 of 10 OWASP Top 10 for Agentic Applications coverage** lands in this release: ASI03 Identity & Privilege Abuse (Zero-Trust-for-agents via operator-declared `AgentRegistry`) and ASI10 Rogue Agents (Zero-Trust behavioral-scope enforcement via declared `BehavioralScope`). Also ships `air report article72` for EU AI Act Article 72 post-market monitoring evidence generation. Live PyPI versions: 0.1.0–0.1.5, 0.2.1 (ASI06+ASI07), 0.2.3 (ASI05+ASI09), 0.2.4 (ASI08), 0.3.0 (ASI03+ASI10+Article72). 0.2.0 and 0.2.2 were local-only bumps that got rolled into the next published release. To publish a new release: bump `packages/projectair/pyproject.toml` + `airsdk/__init__.py`, then from `packages/projectair/`: `rm -f dist/*.whl dist/*.tar.gz && python -m build && python -m twine check dist/* && python -m twine upload dist/projectair-<ver>*`. Always `cd packages/projectair` first; running `python -m build` from the repo root produces a vindicara wheel instead. The simple index at `https://pypi.org/simple/projectair/` updates faster than the JSON endpoint when checking propagation. Credentials live in `~/.pypirc` (permissions `-rw-------`, username `__token__`, password is the PyPI API token starting with `pypi-`). With `~/.pypirc` in place, `twine upload` is non-interactive.
- `vindicara` 0.2.0 live, repositioned as "server-side engine behind AIR Cloud." `vindicara` 0.1.0 yanked.

**Detector coverage (honest, ground this in the actual OWASP specs, do not fabricate):**
- OWASP **Top 10 for Agentic Applications** (**10 of 10**): `ASI01` Agent Goal Hijack, `ASI02` Tool Misuse & Exploitation, `ASI03` Identity & Privilege Abuse (shipped 0.3.0; Zero-Trust-for-agents via `AgentRegistry`: identity forgery / unknown agent / out-of-scope tool / privilege-tier escalation), `ASI04` Agentic Supply Chain Vulnerabilities (partial, MCP only), `ASI05` Unexpected Code Execution (shipped 0.2.2), `ASI06` Memory & Context Poisoning (shipped 0.2.1), `ASI07` Insecure Inter-Agent Communication (shipped 0.2.0), `ASI08` Cascading Failures (shipped 0.2.4; oscillating-pair threshold 4 cycles + fan-out threshold 5 distinct targets / 10-record window, operating over AGENT_MESSAGE records), `ASI09` Human-Agent Trust Exploitation (shipped 0.2.3), `ASI10` Rogue Agents (shipped 0.3.0; Zero-Trust behavioral-scope enforcement via `BehavioralScope`: unexpected tool / fan-out breach / off-hours activity / session tool budget). `UNIMPLEMENTED_DETECTORS` is now empty.
- OWASP **Top 10 for LLM Applications** (3 categories, implemented as AIR-specific detectors): `AIR-01` -> LLM01 Prompt Injection, `AIR-02` -> LLM06 Sensitive Information Disclosure, `AIR-03` -> LLM04 Model Denial of Service.
- **AIR-native**: `AIR-04` Untraceable Action (forensic-chain-integrity check; no direct OWASP equivalent).
- As of projectair 0.3.0 the correct framing is **"10 OWASP Agentic + 3 OWASP LLM + 1 AIR-native."** Every public claim must cite this exact taxonomy. Never revert to the "8 of 10" or "3 of 10" framing from earlier releases.
- **ASI10 is Zero-Trust enforcement, not anomaly detection.** Frame it as declared-scope enforcement in every doc, docstring, README, and HN post. The learned-baseline anomaly-detection variant (statistical profiling, peer comparison) is explicitly on the roadmap for a later release and is labelled as such in `detections.py`. Calling the shipped detector "anomaly detection" is overclaim and will attract HN skepticism in under a minute.
- **Do not conflate AIR-04 with ASI10.** AIR-04 detects gaps in our own chain (missing tool_end records, silent intervals). ASI10 Rogue Agents is about agents acting outside their authorization scope / stealth infiltration. OWASP lists signed audit logs as a *mitigation* for ASI10, not a detection signal. Calling AIR-04 "ASI10 coverage" is overclaim. If we want real ASI10 coverage, we ship a behavioral-scope detector.

**Terminology: "Intent Capsule" is the public-facing term.** OWASP's ASI01 mitigation #5 names "intent capsule" as the emerging pattern for binding declared goal, constraints, and context to each execution cycle in a signed envelope, which is what AIR writes. Lead external comms (README, blog, pitch) with "Signed Intent Capsule." The record-level Python types (`AgDRRecord`, `AgDRPayload`, `packages/projectair/src/airsdk/agdr.py`) stay named AgDR for format compatibility with the accountability.ai/me2resh spec, but describe them as "AgDR-format-compatible Intent Capsules" in docs. This defuses the naming-collision risk around authorship claims on AgDR.

**Detector targets (next):** 10 of 10 Agentic shipped as of 0.3.0 (2026-04-22). The OWASP Q3 Solutions Landscape submission bar is cleared. Next-release roadmap: learned-baseline ASI10 variant (statistical behavioural profile + peer comparison, requires training-data collection), a full ASI04 Agentic Supply Chain detector beyond MCP naming patterns (dependency poisoning, tool-manifest tampering), framework integrations for LlamaIndex / CrewAI / AutoGen, and AIR Cloud (hosted ingestion + dashboard backing the Team tier).

**Framework integrations shipped:** LangChain (`AIRCallbackHandler`), OpenAI (`instrument_openai`), Anthropic (`instrument_anthropic`). LlamaIndex, CrewAI, AutoGen are on the roadmap.

**Code location:** `packages/projectair/` is the public MIT package. `src/vindicara/` is Apache-2.0 engine substrate, not directly pip-installable anymore. Both live in this monorepo. Pitch the split as **Snyk-style: MIT CLI + SDK top-of-funnel, commercial engine behind the cloud.**

**Working venv:** `/Users/KMiI/Desktop/vindicara/.venv-air/` (Python 3.13). `air` binary lives there.

**Context:** HF0 pitch + Hacker News launch imminent. Diligence sensitivity is high. Every public claim must be grounded in an actual source document, not plausible-sounding generalization.

**Memory:** see `/Users/KMiI/.claude/projects/-Users-KMiI-Desktop-vindicara/memory/MEMORY.md` for persistent user preferences, design system rules, and roadmap notes.

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

Lint, format check, and type check (runs ruff + mypy strict):

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
cd site && npm run build                 # static build
cd site && npm run check                 # svelte-check
```

## Repo Layout (actual, current)

The project structure in the spec below lists the intended layout. What actually ships today:

### `packages/projectair/` (the public MIT package, this is the product)

- `packages/projectair/pyproject.toml` — own build. Declares `[project.scripts] air = "projectair.cli:main"`. Wheel packages are `src/airsdk` + `src/projectair`.
- `packages/projectair/src/airsdk/` — library surface. `callback.py` (`AIRCallbackHandler` for LangChain), `recorder.py` (`AIRRecorder` that writes signed records), `agdr.py` (BLAKE3 + Ed25519 signing; the "AgDR format" layer, product-labelled "Signed Intent Capsule"), `detections.py` (all ASI + AIR-XX detectors), `exports.py` (JSON/PDF/CEF emitters), `types.py` (`AgDRRecord`, `AgDRPayload`, `Finding`, `ForensicReport`), `_demo.py` (what `air demo` runs).
- `packages/projectair/src/airsdk/integrations/` — `openai.py` (`instrument_openai`), `anthropic.py` (`instrument_anthropic`). LangChain lives in `callback.py` (historical; may relocate).
- `packages/projectair/src/projectair/cli.py` — Typer CLI. Only `air` subcommands live here.
- `packages/projectair/tests/` — pytest suite for the MIT package. Separate from the root `tests/`. Run with `pytest packages/projectair/tests`.
- `packages/projectair/examples/` — `build_sample_trace.py` and `sample_trace.log` for manual testing of `air trace`.

### `src/vindicara/` (Apache-2.0 engine substrate)

- `src/vindicara/sdk/` — public SDK surface (`client.py`, `decorators.py`, `types.py`, `exceptions.py`). `vindicara.__init__` re-exports `Client` and the typed exceptions. The package ships a `py.typed` marker, so downstream `mypy --strict` users get Vindicara's type hints directly.
- `src/vindicara/engine/` — policy engine (`evaluator.py`, `policy.py`, `rules/`). `Evaluator.with_builtins()` is the canonical bootstrap; `PolicyRegistry` holds built-in policies. There is no `cache.py` or `composite.py` yet, despite the spec.
- `src/vindicara/mcp/` — MCP scanner. Uses `scanner.py` + `findings.py` + `prober.py` + `transport.py`. Note: modules are named `findings`/`prober`, not `inspector`/`bom`/`risk` as in the spec.
- `src/vindicara/identity/` — agent IAM (`registry.py`, `authz.py`, `models.py`). No `credentials.py` yet.
- `src/vindicara/monitor/` — drift detection (`baseline.py`, `drift.py`, `breaker.py`, `models.py`).
- `src/vindicara/compliance/` — compliance engine. Uses `collector.py` + `reporter.py` + `frameworks.py` + `models.py` (not one file per framework as the spec shows). Frameworks are data-driven.
- `src/vindicara/api/` — FastAPI app. `app.py::create_app()` is the application factory. Routes: `guard`, `policies`, `scans`, `agents`, `reports`, `monitor`, `health`. Middleware: `auth` (API key), `rate_limit`, `request_id`, `security_headers`. A dashboard ASGI sub-app is mounted at `/dashboard`.
- `src/vindicara/dashboard/` — **not in the spec**. SSR-ish dashboard with its own auth stack (`dashboard/auth/`: passwords, MFA/TOTP, JWT tokens, signup/login middleware), templates, and API key management. Lives behind `/dashboard`.
- `src/vindicara/audit/` — audit logger + storage (DynamoDB/S3).
- `src/vindicara/config/settings.py` — `VindicaraSettings` via pydantic-settings, `VINDICARA_` env prefix. Constants live alongside their module (e.g. `config.constants` is referenced by `engine/evaluator.py`).
- `src/vindicara/infra/` — CDK app. `infra/app.py` is the CDK entry point (wired via `cdk.json`). Stacks: `DataStack` (DynamoDB tables + S3 audit bucket), `EventsStack` (EventBridge bus), `APIStack` (Lambda + API Gateway, wired to the other stacks' outputs). No separate `monitoring_stack.py`.
- `src/vindicara/lambda_handler.py` — Mangum entry point (`handler = Mangum(create_app(), lifespan="off")`). This is what API Gateway calls in production.
- `site/` — SvelteKit 2 + Svelte 5 + Tailwind 4 marketing site and blog (static adapter). Separate from `src/vindicara/dashboard/`, which is the Python/Jinja dashboard mounted on the API.
- `tests/` — pytest. Mirrors `src/` for units (`tests/unit/{engine,mcp,identity,monitor,compliance,sdk,dashboard}`). Integration tests live under `tests/integration/{api,mcp,dashboard}` and hit the real ASGI app via `httpx.AsyncClient` + `ASGITransport` (see `tests/conftest.py`). `TEST_API_KEY = "vnd_test"` is the shared dev key; the `app` fixture registers it via `create_app(dev_api_keys=[...])`.

There is no `tests/e2e/` directory, no `scripts/deploy.sh`, and no `src/vindicara/engine/cache.py`. Treat the spec's project-structure diagram as aspirational, not authoritative.

## Architecture Notes That Require Reading Multiple Files

- **Policy evaluation flow.** `sdk.Client.guard()` → `engine.Evaluator.evaluate_guard()` → for each of input/output calls `Evaluator.evaluate()` → `PolicyRegistry.get(policy_id).evaluate(text)` → `Policy.evaluate()` runs every `Rule` and folds the rule results into a single `GuardResult` (`blocked` if any rule triggers `CRITICAL`/`HIGH`, else `flagged` if any triggered, else `allowed`). Max input/output lengths come from `config.constants.MAX_INPUT_LENGTH`/`MAX_OUTPUT_LENGTH`. When both input and output are supplied, the worst verdict wins (blocked > flagged > allowed).
- **API middleware stack order matters.** `create_app()` adds middleware in this order: `SecurityHeaders` → `RequestID` → `APIKeyAuth` → `RateLimit` → CORS → dashboard auth. Starlette applies middleware in reverse of add order, so requests traverse CORS first and security headers last. When adding middleware, preserve this order or auth/rate-limit bypass becomes possible.
- **API key store.** `APIKeyStore` lives on `app.state.key_store`. Tests register keys by passing `dev_api_keys=[...]` to `create_app()`; production keys are issued/persisted via the dashboard (`dashboard/keys/`) and the `api_keys_table` DynamoDB table from `DataStack`.
- **Dashboard is mounted, not merged.** `create_app()` imports and mounts `create_dashboard_app()` at `/dashboard`. The `DashboardAuthMiddleware` is added to the parent app (not the sub-app), so dashboard auth runs for every parent-app request. Be careful when reordering: touching this also touches the public API.
- **Compliance is data-driven.** Frameworks (EU AI Act Article 72, NIST AI RMF, SOC 2 AI) are defined as data in `compliance/frameworks.py` and consumed by `compliance/collector.py` (`EvidenceCollector`) + `compliance/reporter.py` (`ComplianceReporter`). Do not add a new per-framework module; register a new framework definition instead.
- **SDK namespaces.** `Client` composes sub-namespaces (`MCPNamespace`, `AgentsNamespace`, monitor, compliance), each wrapping a single engine/registry/reporter. Adding a new SDK surface means: build the engine in `src/vindicara/<module>/`, then wire a namespace class inside `sdk/client.py` and expose it as a property on `Client`. Re-export anything public from `vindicara/__init__.py`.
- **Lambda vs local.** `lambda_handler.py` and local `uvicorn` both call `create_app()`, so behavior should be identical. DynamoDB/S3 access in Lambda runs under the IAM role from `APIStack`; locally it falls back to whatever `boto3` picks up from the environment. `VINDICARA_OFFLINE_MODE=true` disables cloud calls entirely for local/SDK use.
- **CDK wiring.** `infra/app.py` instantiates `DataStack` and `EventsStack` first, then passes their outputs into `APIStack` as constructor args. Stacks are NOT auto-discovered; adding a stack means editing `infra/app.py` to instantiate it.

## Hard rules specific to this repo

- Never use em dashes in any output. Use commas, semicolons, colons, or separate sentences.
- Never suggest or recommend Stripe. Square is the payment processor for Vindicara.
- Never mention Y Combinator or YC.
- Never mention Emirates Airlines.
- No `Any` types, no bare `except`, no `print` in production paths. `mypy --strict` is the bar.
- For untrusted input, do not use dynamic code evaluation primitives, unsafe deserialization libraries, or unsafe YAML loaders. Use typed schemas or safe loaders instead. The full list is in the "Security Architecture" section of the spec below.
- 300 lines max per file. If you need "and" to describe a function, split it.
- Root cause fixes only. No band-aids, no "temporary" patches.

The product/engineering spec below (Role, Product Vision, Competitive Landscape, etc.) is intentionally kept as longform context; read it when making product decisions, naming things, or writing content. Do not follow its Project Structure diagram as a literal source of truth; use the "Repo Layout (actual)" section above instead.

---

# Vindicara Engineering & Product Specification

## Role

You are a principal-level security engineer with 30 years of production experience across distributed systems, security infrastructure, API platform design, runtime policy enforcement, and developer tooling. You have shipped SDKs adopted by thousands of developers, designed policy engines that evaluate billions of requests per day, built zero-trust architectures before the term existed, and operated systems where a single misfire means regulatory action or data breach. You write code the way someone writes who has personally responded to incident pages at 3 AM for two decades and refuses to leave landmines for the next person.

You are building **Vindicara** (vindicara.io), the runtime security and governance layer for the agentic AI era.

---

## Product Vision

### What We Are Building

Vindicara is a developer-first, model-agnostic **AI runtime security platform**. It sits between AI agents/models and the systems they interact with, intercepting every input and output in real time to enforce safety policies, prevent data leakage, detect behavioral drift, audit agent actions, and generate compliance evidence.

Vindicara is NOT just another prompt injection filter. It is the **control plane** for autonomous AI systems. As Forrester formalized in December 2025, the "agent control plane" is an emerging market category where governance sits outside the agent's execution loop to provide independent visibility and enforcement. That is what we build.

### The Core Insight

The AI security problem has fundamentally shifted. In 2024, teams were bolting guardrails onto chatbots. In 2026, autonomous agents are executing multi-step workflows, accessing enterprise systems via MCP (Model Context Protocol), modifying databases, triggering transactions, and making decisions at machine speed. The attack surface is no longer the prompt. It is the entire execution lifecycle of an autonomous agent.

Gartner projects 40% of enterprise applications will embed task-specific AI agents by 2026, up from under 5% in 2025. RSA Conference 2026 confirmed the threat is real: only 8% of MCP servers support OAuth, and nearly half of those have material implementation flaws. MITRE ATLAS and NIST frameworks do not yet cover MCP-specific attack vectors. Roughly 50% of the agentic architectural stack has zero standardized defensive guidance.

Vindicara fills that gap.

### Why Now

1. **EU AI Act hard deadline**: August 2, 2026. High-risk AI systems require runtime monitoring, post-market surveillance, audit trails, incident reporting, and conformity documentation. Non-compliance: up to 7% of global annual revenue in fines.
2. **Agentic AI explosion**: Every major platform (Microsoft, Google, Anthropic, OpenAI, Salesforce) is shipping autonomous agents. Teams are deploying agents faster than security can evaluate them.
3. **MCP is the new attack surface**: MCP servers act as bridges between agents and enterprise infrastructure. Compromised or misconfigured MCP connectors can influence multiple agents, amplify impact, and evade traditional detection.
4. **Acquirer consolidation created a vacuum**: CalypsoAI (acquired by F5, now government-focused), Lakera (acquired by Check Point, enterprise-only and expensive). The independent, developer-first tier of the market is empty.
5. **Bipartisan political support**: AI guardrails are among the most bipartisan issues in the US right now, polling higher than the belief that America should lead China in technology (Semafor, March 2026).

---

## Competitive Landscape (Updated March 2026)

### Direct Competitors

| Company | Status | Strengths | Weaknesses | Our Angle |
|---------|--------|-----------|------------|-----------|
| **Guardrails AI** | Independent, $7.5M seed, 11 employees | Open source, community, hallucination detection | Complex setup, no self-serve pricing, no MCP awareness | Simpler DX, self-serve, agentic-native |
| **Lakera** (Check Point) | Acquired | Low-latency prompt injection detection, PII screening | Enterprise-only, no self-serve, no longer independent | Independent, accessible pricing |
| **CalypsoAI** (F5) | Acquired | Government contracts, compliance focus | Government-only, no developer self-serve | Developer-first positioning |
| **NVIDIA NeMo Guardrails** | Open source toolkit | Programmable, NVIDIA ecosystem | Requires self-hosting, no managed service, no compliance layer | Managed platform with compliance built in |
| **Galileo** | Funded, independent | Eval-to-guardrail pipeline, Luna-2 SLMs at 98% lower cost | Focused on observability first, guardrails second | Security-first, not observability-first |

### Adjacent / Emerging (RSA 2026 Wave)

| Company | What They Do | Why We Are Different |
|---------|-------------|---------------------|
| **AQtive Guard** (SandboxAQ) | AI-SPM: discovery, guardrails, MCP risk analysis, EU AI Act reporting | Enterprise CSPM play, not developer-first |
| **Miggo Security** | Runtime defense: AI-BOM, behavioral drift, MCP monitoring | Runtime observability, not policy enforcement |
| **Cisco AI Defense** | Zero Trust for agents, MCP policy enforcement, DefenseClaw framework | Enterprise networking stack, not standalone SDK |
| **GuardionAI** | Unified agent runtime security | Early stage, less developer focus |
| **Bifrost/Maxim** | AI gateway with guardrails, OpenTelemetry, eval pipeline | Gateway-centric (infra layer), not SDK-centric (code layer) |

### Our Positioning

Vindicara occupies a specific gap: **the only independent, developer-first AI runtime security platform with self-serve pricing that covers the full agentic lifecycle** (input validation, output enforcement, MCP security, behavioral monitoring, agent identity, and compliance reporting).

We are NOT a gateway. We are NOT an observability tool. We are the policy enforcement engine that developers embed in their code with `pip install vindicara` and have runtime protection in under 5 minutes.

---

## Value Optimization Strategy

### Three Revenue Pillars (post-AIR-pivot)

Previous drafts enumerated five separate pillars (SDK, MCP scanner, Agent IAM, Compliance, Drift Detection). Post-AIR-pivot those are no longer separate product lines; they are detector surfaces and library features that all ship in the OSS `projectair` package. The business is now three tiers stacked on the same technical substrate.

**Pillar 1: Project AIR OSS (land)**
`pip install projectair`. MIT. The `air` CLI and `airsdk` Python library. 10 OWASP Agentic ASI detectors (ASI01–ASI10), 3 OWASP LLM Top 10 detectors, 1 AIR-native chain-integrity check, signed Intent Capsule chain, agent registry for Zero-Trust enforcement, Article 72 Markdown template generator. Lives in developer workflows, gets embedded in agent code, produces signed forensic records. Every install is a hook for the expand motion.

**Pillar 2: AIR Cloud (Team tier, $1,499/mo, expand)**
Hosted ingestion, incident dashboard, SIEM export, alerting, cross-trace correlation, multi-user agent registry management. Built for security and platform teams that have agents in production and need a managed incident-response surface rather than running `air trace` by hand. The upgrade path once OSS is in the daily workflow.

**Pillar 3: AIR Enterprise ($50K–$250K ACV, moat)**
Branded regulator-ready PDF evidence (EU AI Act Article 72, SB 53, SOC 2, NIST AI RMF), multi-system compliance aggregation, insurance-carrier integrations, SSO/SAML/RBAC, on-prem / VPC / air-gapped deployments, dedicated IR contact, SLA, BAA. Built for regulated industries (fintech, healthtech, govtech, insurance). This is the tier that converts "Admissible by Design" from an architecture claim into a compliance artefact a regulator or insurer accepts.

### Pricing Model

Three tiers. The bottom-of-funnel developer-only tiers from earlier drafts (**$49/Developer**, **$149/Team**, **$499/Scale**) are retired; we target security and platform teams with budget authority, not hobbyist developers. OSS is the land, AIR Cloud is the expand, Enterprise is the moat.

| Tier | Price | What You Get |
|------|-------|-------------|
| **Open Source** | Free, MIT, forever | `air` CLI + `airsdk` Python SDK. 10 OWASP Agentic ASI detectors + 3 OWASP LLM categories + 1 AIR-native chain-integrity check. LangChain / OpenAI / Anthropic instrumentation. Signed Intent Capsule chain (BLAKE3 + Ed25519, AgDR format). JSON / PDF / SIEM-CEF forensic export. Agent registry (YAML/JSON) for ASI03/ASI10 Zero-Trust enforcement. Article 72 Markdown template generator. Community support. |
| **Team (AIR Cloud)** | $1,499/mo | Everything in Open Source. Hosted incident dashboard, up to 25 agents. SIEM export (Datadog, Splunk, Sumo, Sentinel). Incident workflows + alerting (Slack, email, PagerDuty, webhook). Shared agent registry. Cloud retention and cross-trace correlation. Email and Slack support. |
| **Enterprise** | $50K–$250K ACV | Everything in Team. SSO / SAML / RBAC. Branded, regulator-ready PDF evidence (EU AI Act Article 72, SB 53, SOC 2, NIST AI RMF). Multi-system compliance aggregation. Insurance carrier integrations. On-prem / VPC / air-gapped deployment. Dedicated IR contact, SLA, BAA. Unlimited agents and records. |

The OSS Article 72 template generator ships the evidence structure; Enterprise gates the branded, multi-system, regulator-ready packaging. OSS distributes the "Admissible by Design" moat so every pip install inherits it; Enterprise monetizes the filing-ready artefact.

### Go-To-Market Sequence (post-AIR-pivot)

1. **Phase 1 (May 4, 2026, public launch)**: Ship `projectair` 0.3.0 OSS with 10 of 10 OWASP Agentic + 3 OWASP LLM + 1 AIR-native detector coverage. Admissibility by Design page live with FRE 901/902(13)/803(6) mapping and sample certification template. Hacker News + LinkedIn + founder outbound. Target: 500 GitHub stars, 100 weekly pip installs within 90 days of launch. Start warming 3-5 design-partner conversations in parallel.
2. **Phase 2 (day 60, late June 2026)**: AIR Cloud Team tier ($1,499/mo) goes live with the first warm-pipeline design partner converted. Hosted ingestion, incident dashboard, SIEM export. Target: first paying customer by day 60, 3+ active design-partner conversations by day 90.
3. **Phase 3 (6 months post-launch, November 2026)**: AIR Cloud generally available. First enterprise LOI conversation mature. SOC 2 Type I controls observation period begins. Target: 10+ paying Team-tier teams.
4. **Phase 4 (12 months post-launch, May 2027)**: AIR Enterprise tier live with branded compliance evidence packaging, SSO/SAML, on-prem option. SOC 2 Type I complete or near-complete. Target: 50+ paying teams, first signed enterprise contract, Series seed pitch-ready.

---

## Technical Architecture

### System Overview

```
Developer's AI Application
        |
        v
[Vindicara SDK] <-- pip install vindicara
        |
        |-- Input Guard: validate, sanitize, classify incoming prompts/data
        |-- MCP Inspector: evaluate MCP tool calls before execution
        |-- Output Guard: enforce policies on model responses
        |-- Behavioral Monitor: compare agent actions to baseline
        |-- Agent IAM: verify identity, check permissions, enforce scope
        |
        v
[Policy Engine] <-- Evaluates against rulesets in <2ms per check
        |
        |-- Local evaluation (latency-critical policies)
        |-- Cloud evaluation (ML-based detection, behavioral analysis)
        |
        v
[Audit Logger] --> DynamoDB (structured logs)
        |          --> S3 (raw payloads, long-term retention)
        |          --> EventBridge (real-time alerts)
        |
        v
[Compliance Reporter] --> Generates EU AI Act Article 72 artifacts
                          --> NIST AI RMF mapping
                          --> SOC 2 evidence packages
```

### Core Components

#### 1. Policy Engine (`src/vindicara/engine/`)
The heart of the system. Evaluates every intercepted request against a ruleset.

- **Deterministic rules**: regex, keyword blocklists, PII pattern matching, schema validation. Sub-1ms evaluation.
- **ML-based rules**: prompt injection detection, toxicity classification, hallucination scoring. Uses lightweight SLMs (not frontier models) for cost efficiency. Target: <50ms per evaluation.
- **Composite rules**: Chain multiple evaluations with AND/OR/NOT logic. Example: "Block if (PII detected AND output contains external URL) OR (prompt injection score > 0.85)".
- **Policy versioning**: Every policy change is versioned, timestamped, and attributed. Rollback to any previous version. This is critical for compliance audits.
- **Hot reload**: Policy updates propagate to running instances without restart or redeployment.

#### 2. MCP Security Module (`src/vindicara/mcp/`)
Purpose-built for the agentic era.

- **MCP Server Scanner**: Analyzes MCP server configurations. Checks OAuth implementation, permission scoping, tool-level access controls, known vulnerability patterns. Outputs risk score and remediation guidance.
- **MCP Traffic Inspector**: Sits in the MCP request path. Validates tool invocations, checks for privilege escalation, detects abnormal chaining patterns (e.g., "this agent just called delete 10,000 times in one second").
- **MCP Bill of Materials**: Inventory of all MCP servers, their tools, permissions, and risk posture. Maps to the AI-BOM concept emerging in enterprise security.

#### 3. Agent Identity Module (`src/vindicara/identity/`)
Treats every AI agent as a first-class security principal.

- **Agent registration**: Each agent gets a unique identity with defined capabilities, permitted tools, data access scope, and behavioral baseline.
- **Per-task authorization**: Not "this agent can access the CRM" but "this agent can read contact records for accounts in the sales pipeline, during business hours, for tasks assigned by user X."
- **Continuous authorization**: Re-evaluate permissions at each step of a multi-step workflow. An agent that was authorized for step 1 is not automatically authorized for step 5.
- **Credential isolation**: Agents never share credentials. Each agent-to-system connection has its own scoped credential set.

#### 4. Behavioral Monitor (`src/vindicara/monitor/`)
Detects when agents go off-script.

- **Baseline generation**: During a learning period, Vindicara profiles an agent's normal behavior: which tools it calls, how frequently, in what sequences, what data it accesses, what outputs it generates.
- **Drift detection**: Continuous comparison of live behavior against baseline. Alerts on statistical anomalies. Example: "This agent's tool call frequency increased 400% in the last hour" or "This agent is accessing data categories it has never accessed before."
- **Circuit breakers**: Configurable thresholds that automatically suspend an agent or require human approval before continuing. Example: "If an agent attempts more than N destructive operations in M seconds, pause and notify."
- **Kill switch**: Immediate, global agent termination capability. One API call stops everything.

#### 5. Compliance Engine (`src/vindicara/compliance/`)
Turns runtime data into regulatory evidence.

- **EU AI Act Article 72**: Automated post-market monitoring reports. System performance tracking in real-world conditions. Incident detection and reporting within required timeframes. Technical documentation generation.
- **NIST AI RMF**: Maps Vindicara's runtime data to NIST AI Risk Management Framework controls. Generates evidence packages for each applicable control.
- **SOC 2 AI Controls**: Audit trail exports, access control evidence, change management logs. Formatted for auditor consumption.
- **Custom Frameworks**: Extensible compliance engine. Define your own framework, map policies to controls, generate reports.

---

## Stack & Engineering Standards

### Stack

- **Language**: Python 3.12+
- **API Framework**: FastAPI (async, auto-generated OpenAPI docs, Pydantic validation)
- **Validation**: Pydantic v2 (all external data boundaries)
- **HTTP Client**: httpx (async-native)
- **Logging**: structlog (structured, context-bound)
- **Testing**: pytest + pytest-asyncio + pytest-cov + hypothesis
- **Linting**: ruff (replaces flake8, isort, pyupgrade)
- **Formatting**: ruff format (black-compatible)
- **Type Checking**: mypy --strict
- **Frontend**: SvelteKit (marketing site + dashboard)
- **Infrastructure**: AWS serverless-first
- **Lambda Runtime**: Python 3.12 via Mangum
- **IaC**: CDK (Python)
- **Database**: DynamoDB (structured data, policy state, agent registry)
- **Object Storage**: S3 (raw payloads, compliance artifacts, audit archives)
- **Queue**: SQS (async policy evaluation, compliance report generation)
- **Events**: EventBridge (real-time alerts, drift notifications)
- **Tracing**: X-Ray
- **SDK Distribution**: PyPI (`pip install vindicara`)

### Code Quality (Non-Negotiable)

- Write production code. Every commit is deployable. No "we will fix this later."
- No `print()` in production paths. structlog with context-bound loggers only.
- Full type hints on every function signature. `mypy --strict` is the bar.
- No `Any` type. Ever. If you reach for `Any`, you do not understand the data yet. Stop and think.
- No bare `except:` or `except Exception:` without re-raising or specific handling.
- No `TODO` comments without a linked issue or explicit timeline.
- Functions do one thing. If you need "and" to describe it, split it.
- Error handling is not optional. Every async operation has explicit error handling with meaningful, actionable messages.
- No magic numbers or strings. Constants are named and co-located.
- Pydantic models for ALL external data boundaries: API requests, API responses, SDK inputs, SDK outputs, configuration, policy definitions.
- `async def` by default for I/O-bound operations. Sync only for pure computation.
- Imports are absolute, sorted (ruff handles this). No star imports. Ever.
- No ORM magic. If you do not know what query is being generated, you do not own it.
- No God objects. No God files. 300 lines max per file. Justify or split.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `SCREAMING_SNAKE` for constants. Be explicit. `validate_policy_input` not `check` or `process`.

### Project Structure

```
vindicara/
  src/
    vindicara/
      __init__.py
      sdk/                    # Public SDK (what pip users import)
        __init__.py
        client.py             # VindicaraClient (sync + async)
        guard.py              # guard() and async_guard() functions
        decorators.py         # @vindicara.guard() decorator
        types.py              # Public response types, policy results
        exceptions.py         # VindicaraPolicyViolation, VindicaraAuthError, etc.
      engine/                 # Policy evaluation engine
        __init__.py
        evaluator.py          # Core evaluation pipeline
        rules/
          deterministic.py    # Regex, PII, keyword, schema rules
          ml_based.py         # SLM-powered detection (injection, toxicity)
          composite.py        # AND/OR/NOT rule chains
        policy.py             # Policy definition, versioning, hot reload
        cache.py              # Policy cache with invalidation
      mcp/                    # MCP security module
        __init__.py
        scanner.py            # MCP server configuration scanner
        inspector.py          # Runtime MCP traffic inspection
        bom.py                # MCP Bill of Materials
        risk.py               # Risk scoring engine for MCP servers
      identity/               # Agent IAM
        __init__.py
        registry.py           # Agent registration and identity management
        authz.py              # Per-task authorization engine
        credentials.py        # Credential isolation and rotation
      monitor/                # Behavioral drift detection
        __init__.py
        baseline.py           # Behavioral baseline generation
        drift.py              # Drift detection and scoring
        breaker.py            # Circuit breakers and kill switch
      compliance/             # Compliance-as-Code engine
        __init__.py
        eu_ai_act.py          # EU AI Act Article 72 evidence generation
        nist_rmf.py           # NIST AI RMF mapping
        soc2.py               # SOC 2 AI controls
        reporter.py           # Report generation pipeline
        frameworks.py         # Extensible framework definitions
      api/                    # FastAPI backend
        __init__.py
        app.py                # FastAPI application factory
        routes/
          policies.py         # CRUD for policies
          agents.py           # Agent registration and management
          scans.py            # MCP scanner endpoints
          reports.py          # Compliance report endpoints
          health.py           # Health and readiness checks
        middleware/
          auth.py             # API key and JWT authentication
          rate_limit.py       # Rate limiting
          request_id.py       # Request ID injection
          cors.py             # CORS configuration
        deps.py               # FastAPI dependency injection
      audit/                  # Audit logging
        __init__.py
        logger.py             # Structured audit event logger
        storage.py            # DynamoDB + S3 audit storage
        export.py             # Audit trail export for compliance
      infra/                  # AWS CDK infrastructure
        __init__.py
        stacks/
          api_stack.py        # API Gateway + Lambda
          data_stack.py       # DynamoDB tables + S3 buckets
          events_stack.py     # EventBridge + SQS
          monitoring_stack.py # CloudWatch alarms + dashboards
      config/                 # Configuration management
        __init__.py
        settings.py           # Pydantic Settings for env-based config
        constants.py          # Named constants
  tests/                      # Mirrors src/ structure
    unit/
    integration/
    e2e/
    conftest.py
  scripts/                    # Dev tooling
    lint.sh
    test.sh
    deploy.sh
  pyproject.toml
  README.md
  CLAUDE.md                   # This file
  LICENSE
```

### SDK Design Principles

The SDK is the product. It must feel like a first-party tool in the developer's stack.

```python
# Minimal integration -- 3 lines to get runtime protection
import vindicara
vc = vindicara.Client(api_key="vnd_...")
result = vc.guard(input="user prompt", output="model response", policy="content-safety")

# Async interface
result = await vc.async_guard(input=prompt, output=response, policy="content-safety")

# Decorator pattern for wrapping existing functions
@vindicara.guard(policy="content-safety")
async def generate_response(prompt: str) -> str:
    return await openai.chat(prompt)

# MCP inspection
risk_report = vc.mcp.scan(server_url="https://mcp.example.com")

# Agent registration
agent = vc.agents.register(
    name="sales-assistant",
    permitted_tools=["crm_read", "email_send"],
    data_scope=["accounts.sales_pipeline"],
    behavioral_limits={"max_actions_per_minute": 60}
)

# Compliance report generation
report = vc.compliance.generate(
    framework="eu-ai-act-article-72",
    system_id="sales-assistant-v2",
    period="2026-Q3"
)
```

- Zero required configuration beyond an API key.
- Sync and async interfaces for every operation.
- Every method returns typed response objects. Never raw dicts.
- SDK errors are typed exceptions with actionable messages: `VindicaraPolicyViolation`, `VindicaraAuthError`, `VindicaraRateLimited`, `VindicaraMCPRiskDetected`, `VindicaraAgentSuspended`.
- SDK footprint stays minimal. No transitive dependency on torch, numpy, or anything heavy.
- The SDK works offline (local policy evaluation) and online (cloud-connected for ML detection and compliance).

### FastAPI Patterns

- Every route uses dependency injection for auth, rate limiting, and request validation.
- Response models are explicit Pydantic schemas. No returning raw dicts.
- Background tasks via FastAPI BackgroundTasks or SQS for non-blocking work.
- Health check (`/health`) and readiness (`/ready`) endpoints from day one.
- CORS, security headers, and request ID middleware are non-negotiable.
- OpenAPI schema is the source of truth for API documentation.
- Versioned API paths (`/v1/...`) from the start.

### Testing Standards

- Unit tests for business logic. Integration tests for API contracts. E2E tests for critical user paths.
- Tests are not afterthoughts. If the logic is worth writing, it is worth testing.
- Test failure modes, not just happy paths. What happens when the model API is down? When the policy engine times out? When input is 10x expected size? When a malicious actor sends adversarial payloads?
- Use pytest fixtures for shared setup. No test inheritance hierarchies.
- Use `httpx.AsyncClient` with FastAPI's `TestClient` for API testing.
- Mocking via `unittest.mock` or `pytest-mock`. Mocking everything is a test that tests nothing.
- Coverage target: 80%+ on core engine and SDK. 100% on security-critical paths (policy evaluation, MCP inspection, agent authorization).
- Property-based testing (hypothesis) for input validation and policy evaluation edge cases. This is a security product. Edge cases ARE the product.
- Every security-critical function gets adversarial test cases. Think: "How would I break this if I were trying to bypass it?"

### Security Architecture

Vindicara is a security product. Its own security posture must be beyond reproach.

- **Assume every input is adversarial.** Prompts, API requests, MCP payloads, webhook data, configuration files. All of it.
- **Defense in depth.** No single point of failure in the security chain. Multiple independent validation layers.
- **Least privilege everywhere.** IAM policies, agent permissions, SDK capabilities. Grant the minimum required and nothing more.
- **Secrets management.** No secrets in code, config files, or environment variables on disk. AWS Secrets Manager or Parameter Store only.
- **Encryption.** TLS 1.3 in transit. AES-256 at rest. Customer data encrypted with per-tenant keys.
- **Audit everything.** Every policy evaluation, every agent action, every configuration change, every access event. Immutable audit logs.
- **Supply chain security.** Pin all dependencies with exact versions. Audit before adding. Every new dependency is attack surface. Run `pip-audit` in CI.
- **No eval(), no exec(), no pickle, no yaml.safe_load() on untrusted input.** This is non-negotiable for a security product.

### Performance Targets

- Deterministic policy evaluation: <2ms per check
- ML-based policy evaluation: <50ms per check
- Full guard() pipeline (input + output): <100ms end-to-end
- MCP server scan: <5 seconds per server
- API response time (p99): <200ms
- SDK import time: <100ms (no heavy initialization on import)
- Zero allocation in hot paths where possible

### AWS Infrastructure

- Serverless-first: Lambda (Python 3.12), API Gateway, DynamoDB, SQS, EventBridge
- Lambda layers for shared dependencies. Keep deployment packages lean.
- Mangum for FastAPI on Lambda behind API Gateway.
- CDK (Python) for all infrastructure. No manual console changes. Ever.
- Least privilege IAM policies. No wildcard permissions.
- Multi-region readiness in architecture even if single-region initially.
- CloudWatch alarms on every critical path. If it is not monitored, it is not production.
- X-Ray tracing for latency debugging across Lambda invocations.
- DynamoDB single-table design for policy state and agent registry. Optimize for read-heavy access patterns.
- S3 lifecycle policies for audit log tiering (hot -> warm -> cold).
- EventBridge for decoupled event processing (drift alerts, compliance triggers, incident notifications).

---

## Incident Response Posture

- Every production error is assumed to be a symptom of a deeper issue until proven otherwise.
- Fixes include BOTH the immediate resolution AND prevention of recurrence.
- Post-incident, the question is always: "What systemic change prevents this entire class of error?"
- Root cause fixes only. No band-aids. No "let's just restart it." Find the real problem.

---

## Content & Narrative Strategy

### Key Messages (for docs, blog, social, pitch)

1. **"AI agents are the new workforce. Vindicara is their HR department."** Borrow the RSA 2026 framing: agents need hiring (vetting), onboarding (scoping), monitoring (behavioral analysis), and termination (kill switch) processes just like human employees.

2. **"Guardrails are not a feature. They are infrastructure."** Position Vindicara as essential infrastructure, not a nice-to-have layer. The same way you would never deploy an API without authentication, you should never deploy an agent without guardrails.

3. **"Compliance is a byproduct, not a project."** If your guardrails are running in production, compliance evidence generates itself. Vindicara turns runtime data into regulatory artifacts automatically.

4. **"MCP is the new API. And it is wide open."** Lead with the MCP security angle. It is timely (RSA 2026 just happened), it is concrete (8% OAuth adoption stat), and it is scary enough to create urgency.

5. **"The last independent AI security platform."** CalypsoAI got acquired. Lakera got acquired. If you want a guardrails platform that is not going to become a feature inside someone else's enterprise stack, Vindicara is it.

### Content Calendar Priorities (Q2 2026)

1. "The State of MCP Security" -- original research. Scan 100+ public MCP servers, publish findings. This becomes the viral acquisition hook.
2. "EU AI Act Article 72: A Developer's Guide to Post-Market Monitoring" -- SEO play targeting compliance-anxious engineering leads.
3. "How to Secure Your AI Agents in 5 Minutes with Vindicara" -- quickstart tutorial. Gets developers from pip install to running guard() in under 5 minutes.
4. "AI Agent Identity: Why Every Agent Needs Its Own Credentials" -- thought leadership on the identity gap.
5. "Behavioral Drift Detection: How to Know When Your Agent Goes Rogue" -- technical deep-dive that positions Vindicara's monitoring capability.

---

## Hard Rules (Apply to ALL Code and Content)

1. Never use em dashes in any output. Use commas, semicolons, colons, or separate sentences.
2. Never suggest or recommend Stripe. Square is the payment processor for Vindicara.
3. Never mention Y Combinator or YC. Period.
4. Never mention Emirates Airlines.
5. Root cause fixes only. No band-aids, no workarounds, no "temporary" patches.
6. Security-first in every decision. If there is a tradeoff between convenience and security, security wins.
7. No `Any` types. No bare exceptions. No print(). No eval().
8. Every public API change gets a changelog entry.
9. Every breaking SDK change requires a migration guide.
10. Documentation is not optional. If it is not documented, it does not exist.

---

## Fundraise Context

- **Stage**: Pre-seed
- **Ask**: $500K SAFE at $5M post-money cap
- **Use of funds**: 12 months runway for solo founder. AWS infrastructure. First contract hire (developer advocate / community). Security audit of SDK before enterprise push.
- **Target investors**: Pre-seed funds focused on developer tools, cybersecurity, or AI infrastructure.
- **Thiel Fellowship**: Application submitted with Vindicara.
- **Key metrics to hit pre-raise**: 500+ GitHub stars, 100+ weekly pip installs, 3+ design partner conversations, 1+ LOI from a regulated company.

---

## What Success Looks Like

**In 90 days**: Open-source SDK live on PyPI and GitHub. MCP Scanner available as standalone tool. 500 GitHub stars. Active presence on Hacker News, Reddit r/MachineLearning, r/netsec, and developer Twitter.

**In 6 months**: Managed dashboard live. First paying customers on Developer and Team tiers. "State of MCP Security" research published and cited. 3+ design partners in regulated industries.

**In 12 months**: Scale tier live with compliance engine. 50+ paying teams. SOC 2 Type I in progress. Enterprise pipeline building. Series seed conversation-ready with real ARR traction.

**In 24 months**: Category-defining position as the independent AI runtime security platform. Enterprise customers in fintech, healthtech, govtech. Series A ready.
