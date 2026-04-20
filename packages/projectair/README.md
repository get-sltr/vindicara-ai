<p align="center">
  <strong>Project AIR</strong><br>
  Forensic reconstruction and incident response for AI agents.
</p>

<p align="center">
  <a href="https://vindicara.io">vindicara.io</a> ·
  <a href="https://vindicara.io/blog/secure-ai-agents-5-minutes">Quickstart</a> ·
  <a href="https://vindicara.io/pricing">Pricing</a>
</p>

---

## What this is

When an AI agent goes off-script, AIR tells you what happened and proves it. Every agent decision is written as a signed AgDR (AI Decision Record) with a BLAKE3 content hash and an Ed25519 signature, chained to the previous step. The `air` CLI replays that chain, verifies every signature, and reports OWASP Top 10 for Agentic Applications (ASI01 to ASI10) violations.

One `pip install`. One callback. A signed forensic record of every agent run.

## Install

```bash
pip install projectair
```

This installs the `air` terminal command and the `airsdk` Python library.

## Try it with zero setup

Don't have an agent instrumented yet? Run:

```bash
air demo
```

That generates a fresh signed AgDR chain (13 steps, two baked-in OWASP ASI violations), verifies every signature, runs the detectors, and writes a `forensic-report.json` next to you. Full cold-start experience in one command, no LangChain wiring required.

## Instrument your agent

```python
from airsdk import AIRCallbackHandler
from langchain.agents import AgentExecutor

handler = AIRCallbackHandler(
    key="...",                           # Ed25519 signing key (hex or PEM); auto-generated when omitted
    log_path="my-agent.log",
    user_intent="Draft a Q3 sales report from the CRM data",
)

agent = AgentExecutor(callbacks=[handler], ...)
```

Every step the agent takes (`llm_start`, `llm_end`, `tool_start`, `tool_end`, `agent_finish`) is appended to `my-agent.log` as a signed AgDR record.

## Run the forensic trace

```bash
air trace my-agent.log
```

You get console output like this:

```
[AIR v0.1.3] Loaded 247 agent steps across 3 conversations.
[Chain verified] 247 signatures valid.

  ASI01 Agent Goal Hijack detected at step 47
    Tool `admin_delete_records` called with token overlap 0.03 against the user's stated intent.

  ASI02 Tool Misuse detected at step 51
    Tool `shell_exec` invoked with arguments matching pattern: shell metacharacters.

  ASI03 Prompt Injection detected at step 53
    Prompt matches the `ignore-previous-instructions` pattern.

Detector coverage:
  ASI01 Agent Goal Hijack          implemented
  ASI02 Tool Misuse                implemented
  ASI03 Prompt Injection           implemented
  ASI04 Memory Poisoning           not yet implemented
  ...

[Export] forensic-report.json
```

Export formats: `air trace --format pdf` emits a human-readable PDF for legal and insurance stakeholders; `--format siem` emits ArcSight CEF v0 events for SIEM ingestion (Splunk, Sumo, QRadar, Datadog).

## Session 1 scope

This release covers the minimum forensic surface end-to-end:

| Capability                              | Status                    |
|-----------------------------------------|---------------------------|
| BLAKE3 + Ed25519 signed AgDR chain      | implemented               |
| Chain verification (tamper detection)   | implemented               |
| LangChain callback handler              | implemented               |
| ASI01 Agent Goal Hijack detector        | implemented (heuristic)   |
| ASI02 Tool Misuse detector              | implemented (regex)       |
| ASI03 Prompt Injection detector         | implemented (heuristic)   |
| ASI04 through ASI10 detectors           | not yet implemented       |
| JSON forensic export                    | implemented               |
| PDF forensic export                     | implemented               |
| SIEM forensic export (ArcSight CEF v0)  | implemented               |
| Framework integrations beyond LangChain | not yet implemented       |

The detectors are honest first-pass heuristics. They will produce false positives and false negatives. The signed chain itself is production-grade cryptography.

## Why AIR exists

The prevention layer is crowded. Lakera, NeMo Guardrails, Bedrock Guardrails, and a dozen other tools sit in front of your agent and try to stop bad things from happening. None of them tell you what actually happened when an agent ran, and none of them produce evidence an auditor, a regulator, or an insurance carrier can use.

AIR is the forensic and incident response layer that runs behind those tools. It does not replace them. It gives you a signed record of every agent decision, mapped to a public taxonomy (OWASP ASI01 to ASI10), exportable to formats your SIEM, your compliance team, and your carrier already understand.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

This is pre-1.0 and the shape will evolve. Issues, traces that break the detectors, and new ASI detector PRs are all welcome at https://github.com/get-sltr/vindicara-ai.
