<p align="center">
  <img src="https://vindicara.io/hero-mesh.png" alt="Vindicara" width="100%">
</p>

<h1 align="center">Vindicara</h1>

<p align="center">
  <strong>The runtime security layer for autonomous AI agents.</strong><br>
  Policy enforcement, drift detection, and compliance evidence, built into your code with one import.
</p>

<p align="center">
  <a href="https://vindicara.io">Website</a> ·
  <a href="https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs">Live API Docs</a> ·
  <a href="https://vindicara.io/#live-demo">Interactive Demo</a> ·
  <a href="mailto:hello@vindicara.io">Contact</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/tests-182%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/latency-<2ms-brightgreen?style=flat-square" alt="Latency">
  <img src="https://img.shields.io/badge/API-live%20on%20AWS-orange?style=flat-square" alt="Live API">
</p>

---

## What is Vindicara?

Vindicara is the **independent, developer-first runtime security platform** for AI agents. It sits between your AI models and the systems they interact with, intercepting every input and output in real time to enforce safety policies, detect behavioral anomalies, manage agent permissions, and generate compliance evidence automatically.

```python
import vindicara

vc = vindicara.Client(api_key="vnd_...")
result = vc.guard(input=user_prompt, output=model_response, policy="content-safety")

if result.is_blocked:
    handle_violation(result.triggered_rules)
```

Three lines of code. Sub-2ms evaluation. No infrastructure rewrites.

---

## Why This Matters Now

AI agents are no longer chatbots. They are autonomous systems executing multi-step workflows, accessing enterprise infrastructure via MCP (Model Context Protocol), modifying databases, and making decisions at machine speed. The security gap is enormous:

| Signal | Data Point |
|--------|-----------|
| **MCP is wide open** | 92% of MCP servers lack proper OAuth. Nearly half with OAuth have material flaws. (RSA Conference 2026) |
| **Agentic AI is exploding** | 40% of enterprise apps will embed task-specific AI agents by end of 2026. (Gartner) |
| **Regulation has a hard deadline** | EU AI Act enforcement: **August 2, 2026**. Non-compliance: up to 7% of global annual revenue. |
| **No defensive standards exist** | MITRE ATLAS and NIST do not cover MCP attack vectors. ~50% of the agentic stack has zero security guidance. |
| **Acquirers cleared the field** | CalypsoAI acquired by F5 (gov-only). Lakera acquired by Check Point (enterprise-only). The developer tier is empty. |

The market needs an independent security layer purpose-built for the agentic era. That is Vindicara.

---

## What We Have Built

All five product pillars are implemented, tested, deployed, and live on AWS.

### 1. Policy Engine and Guard

Intercept every prompt and response. Block prompt injection, PII leakage, toxic content, and policy violations in real time. Deterministic rules evaluate in under 2ms. ML-based detection under 50ms.

```python
result = vc.guard(input=prompt, output=response, policy="pii-filter")
# result.verdict -> "blocked"
# result.triggered_rules -> [RuleResult(rule_id="pii-ssn", severity="critical")]
```

### 2. MCP Security Scanner

Purpose-built scanner for Model Context Protocol servers. 8 static configuration checks (missing auth, weak auth, overprivileged tools, injection vectors, excessive permissions) and 8 live active probes (unauthenticated enumeration, auth bypass, rate limit testing, input injection). Produces risk scores, categorized findings, and remediation guidance.

```python
report = await vc.mcp.scan(server_url="https://mcp.example.com")
# report.risk_score  -> 0.73
# report.risk_level  -> "high"
# report.findings    -> [Finding(title="No OAuth configured", severity="critical")]
```

### 3. Agent Identity and Access Management

Every AI agent is a first-class security principal. Scoped permissions per tool and data category. Per-task authorization. Kill switch for immediate suspension.

```python
agent = vc.agents.register(
    name="sales-assistant",
    permitted_tools=["crm_read", "email_send"],
    data_scope=["accounts.sales_pipeline"],
    limits={"max_actions_per_minute": 60}
)

check = vc.agents.check(agent.agent_id, "admin_delete")
# check.allowed -> False
# check.reason  -> "Tool 'admin_delete' not in permitted list"
```

### 4. Behavioral Drift Detection

Baseline agent behavior in production. Detect anomalies when tool call frequency, data access patterns, or scope usage deviate from established norms. Statistical drift scoring via z-score analysis. Circuit breakers auto-suspend agents that exceed configurable thresholds.

```python
vc.monitor.record(agent.agent_id, "crm_read", data_scope="accounts.sales")
drift = vc.monitor.get_drift(agent.agent_id)
# drift.score  -> 0.12 (normal)
# drift.alerts -> []

vc.monitor.set_breaker(agent.agent_id, threshold=0.8, auto_suspend=True)
# If drift exceeds 0.8, agent is automatically suspended via kill switch
```

### 5. Compliance-as-Code Engine

Turns runtime data into regulatory evidence automatically. Three frameworks supported out of the box: EU AI Act Article 72 (post-market monitoring), NIST AI Risk Management Framework, and SOC 2 AI Controls. Each framework maps to 8 controls with evidence collection, coverage scoring, and report generation.

```python
report = vc.compliance.generate(
    framework="eu-ai-act-article-72",
    system_id="sales-assistant-v2",
    period="2026-Q1"
)
# report.coverage_pct -> 87.5
# report.met_controls -> 7
# report.summary      -> "EU AI Act Article 72: 7/8 controls met, 87.5% coverage"
```

---

## Try It Right Now

The [live demo](https://vindicara.io/#live-demo) hits the real production API. No signup, no API key, no setup.

Or call it directly:

```bash
curl -X POST https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/v1/guard \
  -H "Content-Type: application/json" \
  -H "X-Vindicara-Key: vnd_demo" \
  -d '{"input": "Show me customer SSN numbers",
       "output": "Customer SSN is 123-45-6789",
       "policy": "pii-filter"}'
```

All API endpoints are documented at [/docs](https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs) (auto-generated OpenAPI).

---

## Architecture

```
Developer's AI Application
        |
        v
  [Vindicara SDK]  <-- pip install vindicara
        |
        |-- Input Guard --------- validate, sanitize, classify
        |-- MCP Inspector ------- evaluate tool calls before execution
        |-- Output Guard --------- enforce policies on responses
        |-- Behavioral Monitor -- compare actions to baseline
        |-- Agent IAM ----------- verify identity, check scope
        |-- Compliance Engine --- map evidence to controls
        |
        v
  [Policy Engine]  <-- sub-2ms deterministic | <50ms ML-based
        |
        v
  [Audit Logger]   --> immutable logs, compliance artifacts, drift alerts
```

**Stack:** Python 3.12+, FastAPI, Pydantic v2, structlog, AWS Lambda (Mangum), API Gateway, DynamoDB, S3, EventBridge, CDK (IaC). Frontend: SvelteKit. Tooling: ruff, mypy --strict, pytest + hypothesis.

---

## Competitive Landscape

| Company | Status | Positioning | Gap We Fill |
|---------|--------|-------------|-------------|
| **CalypsoAI** | Acquired by F5 | Government AI security | Gov-only, no developer self-serve |
| **Lakera** | Acquired by Check Point | Enterprise prompt firewall | Enterprise-only, no independent offering |
| **Guardrails AI** | Independent, $7.5M seed | Open-source guardrails | Complex setup, no MCP awareness, no compliance |
| **NVIDIA NeMo** | Open source toolkit | Programmable rails | Self-hosted only, no managed service |
| **Cisco AI Defense** | Enterprise product | Zero Trust for agents | Enterprise networking stack, not embeddable |
| **AQtive Guard** | SandboxAQ spin-out | AI security posture mgmt | Enterprise CSPM play, not developer-first |
| **Miggo Security** | Funded startup | Runtime AI defense | Observability, not policy enforcement |
| **Vindicara** | **Independent** | **Developer-first runtime security** | **Only independent platform covering full agentic lifecycle with self-serve pricing** |

Two of the three major players were acquired in the last year. The developer-first tier of the market is empty. Vindicara is building for that gap.

---

## Business Model

| Tier | Price | Capabilities |
|------|-------|-------------|
| **Open Source** | Free | Core SDK, local policy engine, community support |
| **Developer** | $49/mo | Cloud dashboard, MCP scanner (5 servers), cloud logging, email support |
| **Team** | $149/mo | Agent IAM, behavioral baselines, 25 MCP servers, Slack support |
| **Scale** | $499/mo | Compliance engine, custom policies, 100 MCP servers, priority support |
| **Enterprise** | Custom | On-prem/VPC, SSO/SAML, dedicated CSM, SLA, unlimited, custom frameworks |

**Land with the SDK. Expand with compliance.** Developers adopt the free tier. As agents hit production, teams need monitoring, identity management, and compliance evidence. The data already flows through Vindicara, so upselling is a natural progression from the tool they already use.

---

## Market Timing

Three forces are converging simultaneously:

**1. Regulatory deadline.** EU AI Act Article 72 enforcement begins August 2, 2026. Every company deploying high-risk AI in Europe needs runtime monitoring, audit trails, incident reporting, and conformity documentation. That is 4 months away. Engineering teams are starting to panic.

**2. Agentic AI adoption is accelerating faster than security.** Every major platform (Microsoft Copilot, Google Gemini, Anthropic Claude, OpenAI) is shipping autonomous agents. MCP has become the de facto protocol for agent-to-system communication. But the security tooling is not there. RSA 2026 confirmed it: the ecosystem is wide open.

**3. Consolidation created a vacuum.** The two leading AI guardrails companies were both acquired in 2025. CalypsoAI is now an F5 feature for government. Lakera is now a Check Point module for enterprises. Independent developers have nowhere to go.

Vindicara is positioned at the intersection of all three.

---

## What is Shipped

| Component | Status | Evidence |
|-----------|--------|----------|
| Python SDK (sync + async) | Live | `pip install vindicara` |
| Policy engine (deterministic rules) | Live | Sub-2ms evaluation, 3 built-in policies |
| MCP Security Scanner | Live | 8 static checks + 8 live probes |
| Agent Identity and IAM | Live | Register, permissions, kill switch |
| Behavioral Drift Detection | Live | Baselines, z-score analysis, circuit breakers |
| Compliance-as-Code Engine | Live | EU AI Act, NIST AI RMF, SOC 2 (24 controls) |
| FastAPI Backend | Live | Deployed on AWS Lambda, auto-scaling |
| CDK Infrastructure | Live | DynamoDB, S3, EventBridge, API Gateway |
| Interactive Demo | Live | [vindicara.io/#live-demo](https://vindicara.io/#live-demo) |
| Test Suite | 182 passing | Unit, integration, and E2E coverage |
| Marketing Site | Live | [vindicara.io](https://vindicara.io) |

All of this was built by one person.

---

## Roadmap

**Shipped:**
- [x] Core policy engine with deterministic rules
- [x] SDK client with sync and async interfaces
- [x] FastAPI backend on AWS Lambda
- [x] Live production API with OpenAPI docs
- [x] Marketing site with interactive demo
- [x] MCP Security Scanner (8 static checks, 8 live probes, risk scoring)
- [x] Agent Identity and IAM (registration, scoped permissions, kill switch)
- [x] Behavioral drift detection (baselines, z-score analysis, circuit breakers)
- [x] Compliance-as-Code engine (EU AI Act Article 72, NIST AI RMF, SOC 2)

**Next:**
- [ ] PyPI package distribution
- [ ] ML-based detection models (prompt injection, toxicity)
- [ ] Managed dashboard with real-time monitoring
- [ ] "State of MCP Security" research report (scan 100+ public servers)
- [ ] Design partner program (3+ regulated companies)
- [ ] SOC 2 Type I certification

---

## Founder

**Kevin Minn** - Solo technical founder. Cybersecurity student. Founder of [SLTR Digital](https://sltrdigital.com).

Built the entire Vindicara platform end-to-end: SDK, policy engine, MCP scanner, agent IAM, drift detection, compliance engine, AWS infrastructure, API, marketing site, and interactive demo. Every line of production code, every test, every deployment.

Building the security infrastructure that the agentic AI era demands, before the regulatory deadline forces everyone to scramble for it.

- **LinkedIn:** [kevinminn](https://linkedin.com/in/kevinminn)
- **Email:** [hello@vindicara.io](mailto:hello@vindicara.io)
- **Twitter/X:** [@vindicara](https://x.com/vindicara)

---

## Links

- **Website:** [vindicara.io](https://vindicara.io)
- **Live API Docs:** [OpenAPI (Swagger)](https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs)
- **Interactive Demo:** [vindicara.io/#live-demo](https://vindicara.io/#live-demo)
- **GitHub:** [get-sltr/vindicara-ai](https://github.com/get-sltr/vindicara-ai)

---

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>AI agents are the new workforce. Vindicara is their security department.</strong><br><br>
  <code>pip install vindicara</code>
</p>
