<p align="center">
  <img src="https://vindicara.io/hero-mesh.png" alt="" width="100%">
</p>

<h1 align="center">Project AIR</h1>

<p align="center">
  <strong>Forensic reconstruction and incident response for AI agents.</strong><br>
  When your AI agent goes off-script, AIR tells you what happened and proves it.
</p>

<p align="center">
  <a href="https://vindicara.io">vindicara.io</a> ·
  <a href="https://vindicara.io/blog/secure-ai-agents-5-minutes">Quickstart</a> ·
  <a href="https://vindicara.io/pricing">Pricing</a> ·
  <a href="https://vindicara.io/blog">Blog</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/status-alpha-orange?style=flat-square" alt="Alpha">
</p>

---

## What AIR is

AIR writes a **signed forensic record** of every agent decision (llm, tool, finish) as an AgDR (AI Decision Record). Each record is content-hashed with BLAKE3, signed with Ed25519, and chained to the previous step. The `air` CLI replays the chain, verifies every signature, and reports OWASP Top 10 for Agentic Applications violations (5 of 10 detectors shipped today: ASI01, ASI02, ASI03, ASI05, ASI09. ASI04, ASI06, ASI07, ASI08, ASI10 on roadmap).

It is the layer that runs **behind** your guardrails. Prevention tools (Lakera, NeMo Guardrails, Bedrock Guardrails) try to stop bad things from happening. AIR produces the evidence of what actually happened, in a form security, legal, and insurance can act on.

## Install

```bash
pip install projectair
```

This installs both the `air` terminal command and the `airsdk` Python library.

## 10-second sanity check

```bash
air demo
```

Generates a fresh signed AgDR chain (13 steps, two baked-in ASI violations), verifies every signature, runs the detectors, and writes `forensic-report.json` next to you. No agent, no log file, no wiring required.

## 30-second usage

Instrument your LangChain agent:

```python
from airsdk import AIRCallbackHandler
from langchain.agents import AgentExecutor

handler = AIRCallbackHandler(
    key="...",                           # Ed25519 signing key; auto-generated when omitted
    log_path="my-agent.log",
    user_intent="Draft a Q3 sales report from the CRM data",
)
agent = AgentExecutor(callbacks=[handler], ...)
```

Every step the agent takes is appended to `my-agent.log` as a signed AgDR record.

Replay the trace:

```bash
air trace my-agent.log
```

You get a console report: signatures verified, ASI01/ASI02 findings flagged, detector coverage shown honestly, and `forensic-report.json` emitted alongside.

## What's in this repo

This is a monorepo.

- **[`packages/projectair/`](packages/projectair/)**: the MIT-licensed `projectair` package published to PyPI. Ships the `air` CLI and the `airsdk` Python library. This is the public, supported AIR surface.
- **[`site/`](site/)**: the SvelteKit source for [vindicara.io](https://vindicara.io).
- **`src/vindicara/`**: the older Apache-2.0 runtime security engine (policy evaluator, MCP scanner, agent IAM, drift monitor, compliance collector). This is now the engine substrate underneath AIR, not the public product surface. Retained for reference and for future integrations.

For the legacy five-pillar README that used to live here, see [`docs/legacy-vindicara-readme.md`](docs/legacy-vindicara-readme.md).

## Status

| Surface                                 | Status                    |
|-----------------------------------------|---------------------------|
| BLAKE3 + Ed25519 signed AgDR chain      | implemented, tested       |
| Tamper detection on chain replay        | implemented, tested       |
| LangChain `AIRCallbackHandler`          | implemented               |
| ASI01 Agent Goal Hijack detector        | implemented (heuristic)   |
| ASI02 Tool Misuse detector              | implemented (regex)       |
| ASI03 Prompt Injection detector         | implemented (heuristic)   |
| ASI05 Sensitive Data Exposure detector  | implemented (pattern set) |
| ASI09 Supply Chain / MCP Risk detector  | implemented (heuristic)   |
| ASI04, ASI06, ASI07, ASI08, ASI10       | not yet implemented       |
| JSON forensic export                    | implemented               |
| PDF forensic export                     | implemented (fpdf2)       |
| SIEM forensic export (ArcSight CEF v0)  | implemented               |
| LangChain callback integration          | implemented               |
| OpenAI SDK integration                  | implemented               |
| Anthropic, LlamaIndex, CrewAI, AutoGen  | not yet implemented       |
| AIR Cloud (hosted dashboards, SIEM)     | not yet implemented       |

Pre-1.0. The detector heuristics will produce false positives and false negatives. The signed chain itself is production-grade cryptography. See the [pricing page](https://vindicara.io/pricing) for what's planned next.

## Contributing

Issues, traces that break the detectors, and new ASI detector PRs are welcome. Bugs and feature requests: https://github.com/get-sltr/vindicara-ai/issues.

## License

- `packages/projectair/` and the `projectair` PyPI distribution: **MIT**. See [`packages/projectair/LICENSE`](packages/projectair/LICENSE).
- `src/vindicara/` (engine substrate, not published): **Apache-2.0**.
