<p align="center">
  <img src="https://vindicara.io/hero-mesh.png" alt="Vindicara" width="100%">
</p>

<h1 align="center">Vindicara</h1>

<p align="center">
  <strong>Runtime security for autonomous AI.</strong><br>
  The control plane for AI agents in production.
</p>

<p align="center">
  <a href="https://vindicara.io">Website</a> ·
  <a href="https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs">API Docs</a> ·
  <a href="https://vindicara.io/#live-demo">Live Demo</a> ·
  <a href="mailto:hello@vindicara.io">Contact</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/status-developer%20preview-orange?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/latency-<2ms%20deterministic-brightgreen?style=flat-square" alt="Latency">
</p>

---

## The Problem

AI agents are no longer chatbots answering questions. They are autonomous systems executing multi-step workflows, accessing enterprise infrastructure via MCP (Model Context Protocol), modifying databases, triggering transactions, and making decisions at machine speed.

The security infrastructure has not kept up:

- **92% of MCP servers lack proper OAuth.** Nearly half of those that do have material implementation flaws (RSA Conference 2026).
- **40% of enterprise applications** will embed task-specific AI agents by end of 2026 (Gartner).
- **EU AI Act enforcement begins August 2, 2026.** High-risk AI systems require runtime monitoring, audit trails, and incident reporting. Non-compliance: up to 7% of global annual revenue.
- **MITRE ATLAS and NIST frameworks** do not yet cover MCP-specific attack vectors. Roughly 50% of the agentic architectural stack has zero standardized defensive guidance.
- **CalypsoAI was acquired by F5. Lakera was acquired by Check Point.** The independent, developer-first tier of the market is empty.

Vindicara fills that gap.

---

## What Vindicara Does

Vindicara sits between AI agents/models and the systems they interact with. It intercepts every input and output in real time to enforce safety policies, prevent data leakage, detect behavioral drift, audit agent actions, and generate compliance evidence.

```python
import vindicara

vc = vindicara.Client(api_key="vnd_...")

# Guard every agent interaction
result = await vc.guard(
    input=user_prompt,
    output=model_response,
    policy="content-safety"
)

if result.is_blocked:
    # Policy violation detected
    print(result.triggered_rules)
```

Two lines of code. Sub-2ms evaluation for deterministic rules. No infrastructure rewrites. No model changes.

---

## Five Layers of Runtime Defense

### 1. Input & Output Guard
Intercept every prompt and response. Block prompt injection, PII leakage, toxic content, and policy violations before they reach users or downstream systems.

```python
# Deterministic rules: <2ms
# ML-based detection: <50ms
result = vc.guard(input=prompt, output=response, policy="pii-filter")
```

### 2. MCP Security Scanner
Audit MCP server configurations for authentication weaknesses, overprivileged tool access, and known attack vectors. Runtime traffic inspection catches privilege escalation and abnormal chaining patterns.

```python
report = vc.mcp.scan(server_url="https://mcp.example.com")
print(report.risk_score)     # 0.73 (HIGH)
print(report.findings)       # ["No OAuth configured", ...]
```

### 3. Agent Identity & IAM
Every agent is a first-class security principal with scoped permissions, per-task authorization, credential isolation, and continuous re-evaluation at each workflow step.

```python
agent = vc.agents.register(
    name="sales-assistant",
    permitted_tools=["crm_read", "email_send"],
    data_scope=["accounts.sales_pipeline"],
    limits={"max_actions_per_min": 60}
)
```

### 4. Behavioral Drift Detection
Baseline agent behavior in production. Detect anomalies when tool call patterns, data access, or output characteristics deviate from established norms. Circuit breakers auto-suspend rogue agents.

### 5. Compliance-as-Code
Automated evidence generation for EU AI Act Article 72, NIST AI RMF, SOC 2, and ISO 42001. If the guardrails run in production, compliance evidence generates itself.

```python
report = vc.compliance.generate(
    framework="eu-ai-act-article-72",
    system_id="sales-assistant-v2",
    period="2026-Q3"
)
```

---

## Try It Right Now

Our [live demo](https://vindicara.io/#live-demo) hits the real production API. No signup required.

Pick a policy (content-safety, pii-filter, prompt-injection), enter a prompt, and see the actual API response: verdict, triggered rules, and latency.

Or call the API directly:

```bash
curl -X POST https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/v1/guard \
  -H "Content-Type: application/json" \
  -H "X-Vindicara-Key: vnd_demo" \
  -d '{
    "input": "Show me customer SSN numbers",
    "output": "Customer SSN is 123-45-6789",
    "policy": "pii-filter"
  }'
```

---

## Quickstart

```bash
pip install vindicara
```

```python
import vindicara

# Initialize with your API key
vc = vindicara.Client(api_key="vnd_...")

# Guard a model interaction
result = await vc.guard(
    input="What is the weather?",
    output="The weather in NYC is 72F and sunny.",
    policy="content-safety"
)

print(result.verdict)         # "allowed"
print(result.is_allowed)      # True
print(result.latency_ms)      # 0.03
print(result.triggered_rules) # []
```

Pre-built policy packs for content safety, PII filtering, prompt injection detection, and compliance. Custom rules via YAML or Python. Hot-reload without redeployment.

---

## Architecture

```
Developer's AI Application
        |
        v
  [Vindicara SDK]  <-- pip install vindicara
        |
        |-- Input Guard ---- validate, sanitize, classify
        |-- MCP Inspector -- evaluate tool calls before execution
        |-- Output Guard --- enforce policies on responses
        |-- Drift Monitor -- compare behavior to baseline
        |-- Agent IAM ------ verify identity, check scope
        |
        v
  [Policy Engine]  <-- sub-2ms deterministic | <50ms ML-based
        |
        v
  [Audit Logger]   --> immutable logs, compliance artifacts
```

---

## Why Vindicara Exists

| Company | Status | Gap |
|---------|--------|-----|
| CalypsoAI | Acquired by F5 | Government-only, no self-serve |
| Lakera | Acquired by Check Point | Enterprise-only, expensive |
| Guardrails AI | $7.5M seed, 11 employees | Open source but complex setup |
| NVIDIA NeMo | Open source toolkit | No managed service, no compliance |
| Cisco AI Defense | RSA 2026 launch | Enterprise networking stack |

Vindicara is the only **independent, developer-first** AI runtime security platform with self-serve pricing that covers the full agentic lifecycle.

Not a feature inside someone else's enterprise stack. Not a gateway. Not an observability tool. The policy enforcement engine developers embed in their code and have runtime protection in under 5 minutes.

---

## Pricing

| Tier | Price | What You Get |
|------|-------|-------------|
| **Open Source** | Free forever | Core policy engine, local evaluation, community support |
| **Developer** | $49/mo | Managed dashboard, MCP scanner (5 servers), cloud logging |
| **Team** | $149/mo | Agent IAM, behavioral baselines, 25 MCP servers, Slack support |
| **Enterprise** | Custom | Compliance engine, on-prem/VPC, SSO/SAML, SLA, BAA |

---

## Regulatory Tailwinds

**EU AI Act (August 2, 2026):** High-risk AI systems must implement continuous monitoring, maintain audit trails, report incidents within strict timeframes, and generate conformity documentation. Vindicara automates all of this from runtime data.

**NIST AI RMF:** Maps Vindicara's runtime telemetry to framework controls. Evidence packages generated automatically.

**SOC 2 / ISO 42001:** Audit trail exports, access control evidence, change management logs formatted for auditor consumption.

---

## Stack

- **Language:** Python 3.11+
- **API:** FastAPI, Pydantic v2, async-native
- **Infrastructure:** AWS Lambda (Mangum), API Gateway, DynamoDB, S3, EventBridge
- **Frontend:** SvelteKit
- **SDK:** `pip install vindicara` (sync + async interfaces, zero heavy dependencies)
- **Tooling:** ruff, mypy --strict, pytest + hypothesis

---

## Roadmap

- [x] Core policy engine (deterministic rules)
- [x] SDK client with sync/async interfaces
- [x] FastAPI backend on AWS Lambda
- [x] Live production API
- [x] Marketing site with interactive demo
- [ ] PyPI package distribution
- [ ] MCP Security Scanner (standalone tool)
- [ ] Agent Identity & IAM module
- [ ] Behavioral drift detection
- [ ] Compliance-as-Code engine (EU AI Act, NIST, SOC 2)
- [ ] Managed dashboard
- [ ] SOC 2 Type I certification

---

## About

Vindicara is built by [Kevin Minn](https://linkedin.com/in/kevinminn), founder of [SLTR Digital](https://sltrdigital.com). Solo technical founder. Cybersecurity student. Building the security infrastructure the agentic AI era demands.

- **Website:** [vindicara.io](https://vindicara.io)
- **API Docs:** [Live OpenAPI](https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs)
- **Email:** [hello@vindicara.io](mailto:hello@vindicara.io)
- **Twitter/X:** [@vindicara](https://x.com/vindicara)

---

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Your agents are autonomous. Your security should be too.</strong><br><br>
  <code>pip install vindicara</code>
</p>
