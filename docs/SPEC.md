# Vindicara Engineering & Product Specification

This document holds the longform context for product decisions, external content, and subsystem design. For day-to-day code edits, use `CLAUDE.md` at the repo root. For code quality and security standards, use `docs/STANDARDS.md`.

---

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
`pip install projectair`. Apache 2.0. The `air` CLI and `airsdk` Python library. 10 OWASP Agentic ASI detectors (ASI01–ASI10), 3 OWASP LLM Top 10 detectors, 1 AIR-native chain-integrity check, signed Intent Capsule chain, agent registry for Zero-Trust enforcement, Article 72 Markdown template generator. Lives in developer workflows, gets embedded in agent code, produces signed forensic records. Every install is a hook for the expand motion.

**Pillar 2: AIR Cloud (Team tier, $1,499/mo, expand)**
Hosted ingestion, incident dashboard, SIEM export, alerting, cross-trace correlation, multi-user agent registry management. Built for security and platform teams that have agents in production and need a managed incident-response surface rather than running `air trace` by hand. The upgrade path once OSS is in the daily workflow.

**Pillar 3: AIR Enterprise ($50K–$250K ACV, moat)**
Branded regulator-ready PDF evidence (EU AI Act Article 72, SB 53, SOC 2, NIST AI RMF), multi-system compliance aggregation, insurance-carrier integrations, SSO/SAML/RBAC, on-prem / VPC / air-gapped deployments, dedicated IR contact, SLA, BAA. Built for regulated industries (fintech, healthtech, govtech, insurance). This is the tier that converts "Admissible by Design" from an architecture claim into a compliance artefact a regulator or insurer accepts.

### Pricing Model

Three tiers. The bottom-of-funnel developer-only tiers from earlier drafts ($49/Developer, $149/Team, $499/Scale) are retired; we target security and platform teams with budget authority, not hobbyist developers. OSS is the land, AIR Cloud is the expand, Enterprise is the moat.

| Tier | Price | What You Get |
|------|-------|-------------|
| **Open Source** | Free, Apache 2.0, forever | `air` CLI + `airsdk` Python SDK. 10 OWASP Agentic ASI detectors + 3 OWASP LLM categories + 1 AIR-native chain-integrity check. LangChain / OpenAI / Anthropic instrumentation. Signed Intent Capsule chain (BLAKE3 + Ed25519, AgDR format). JSON / PDF / SIEM-CEF forensic export. Agent registry (YAML/JSON) for ASI03/ASI10 Zero-Trust enforcement. Article 72 Markdown template generator. Community support. |
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

## Aspirational Project Structure

This diagram is aspirational, not ground truth. Use the "Repo Layout (actual, current)" section in `CLAUDE.md` when navigating the codebase. This version is preserved for design discussions about where new subsystems could fit.

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
  CLAUDE.md
  LICENSE
```

---

## Content & Narrative Strategy

### Key Messages (for docs, blog, social, pitch)

1. **"AI agents are the new workforce. Vindicara is their HR department."** Borrow the RSA 2026 framing: agents need hiring (vetting), onboarding (scoping), monitoring (behavioral analysis), and termination (kill switch) processes just like human employees.

2. **"Guardrails are not a feature. They are infrastructure."** Position Vindicara as essential infrastructure, not a nice-to-have layer. The same way you would never deploy an API without authentication, you should never deploy an agent without guardrails.

3. **"Compliance is a byproduct, not a project."** If your guardrails are running in production, compliance evidence generates itself. Vindicara turns runtime data into regulatory artifacts automatically.

4. **"MCP is the new API. And it is wide open."** Lead with the MCP security angle. It is timely (RSA 2026 just happened), it is concrete (8% OAuth adoption stat), and it is scary enough to create urgency.

5. **"The last independent AI security platform."** CalypsoAI got acquired. Lakera got acquired. If you want a guardrails platform that is not going to become a feature inside someone else's enterprise stack, Vindicara is it.

### Content Calendar Priorities (Q2 2026)

1. "The State of MCP Security" — original research. Scan 100+ public MCP servers, publish findings. This becomes the viral acquisition hook.
2. "EU AI Act Article 72: A Developer's Guide to Post-Market Monitoring" — SEO play targeting compliance-anxious engineering leads.
3. "How to Secure Your AI Agents in 5 Minutes with Vindicara" — quickstart tutorial. Gets developers from pip install to running guard() in under 5 minutes.
4. "AI Agent Identity: Why Every Agent Needs Its Own Credentials" — thought leadership on the identity gap.
5. "Behavioral Drift Detection: How to Know When Your Agent Goes Rogue" — technical deep-dive that positions Vindicara's monitoring capability.

---

## Fundraise Context

- **Stage**: Pre-seed
- **Ask**: $500K SAFE at $5M post-money cap
- **Use of funds**: 12 months runway for solo founder. AWS infrastructure. First contract hire (developer advocate / community). Security audit of SDK before enterprise push.
- **Target investors**: Pre-seed funds focused on developer tools, cybersecurity, or AI infrastructure.
- **Key metrics to hit pre-raise**: 500+ GitHub stars, 100+ weekly pip installs, 3+ design partner conversations, 1+ LOI from a regulated company.

---

## What Success Looks Like

**In 90 days**: Open-source SDK live on PyPI and GitHub. MCP Scanner available as standalone tool. 500 GitHub stars. Active presence on Hacker News, Reddit r/MachineLearning, r/netsec, and developer Twitter.

**In 6 months**: Managed dashboard live. First paying customers on Developer and Team tiers. "State of MCP Security" research published and cited. 3+ design partners in regulated industries.

**In 12 months**: Scale tier live with compliance engine. 50+ paying teams. SOC 2 Type I in progress. Enterprise pipeline building. Series seed conversation-ready with real ARR traction.

**In 24 months**: Category-defining position as the independent AI runtime security platform. Enterprise customers in fintech, healthtech, govtech. Series A ready.
