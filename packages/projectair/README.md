<p align="center">
  <strong>Project AIR™</strong><br>
  Forensic reconstruction and incident response for AI agents.
</p>

<p align="center">
  <a href="https://vindicara.io">vindicara.io</a> ·
  <a href="https://vindicara.io/blog/secure-ai-agents-5-minutes">Quickstart</a> ·
  <a href="https://vindicara.io/pricing">Pricing</a>
</p>

---

## What this is

When an AI agent goes off-script, AIR tells you what happened and proves it. Every agent decision is written as a **Signed Intent Capsule** (the pattern named in [OWASP Top 10 for Agentic Applications v12.6](https://owasp.org/www-project-top-10-for-large-language-model-applications/) as ASI01 mitigation #5: a signed envelope binding the declared goal, constraints, and context to each execution cycle). Each capsule carries a BLAKE3 content hash and an Ed25519 signature, chained to the previous step. The on-disk format is AgDR-compatible (AI Decision Record schema, accountability.ai). The `air` CLI replays that chain, verifies every signature, and reports findings across two public OWASP taxonomies plus one AIR-native check.

**Coverage today:**

- **OWASP Top 10 for Agentic Applications** (8 of 10 implemented): ASI01 Agent Goal Hijack, ASI02 Tool Misuse & Exploitation, ASI04 Agentic Supply Chain Vulnerabilities (partial, MCP supply-chain risk only), ASI05 Unexpected Code Execution (RCE), ASI06 Memory & Context Poisoning, ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Exploitation. ASI03, ASI10 are on the roadmap.
- **OWASP Top 10 for LLM Applications** (3 categories covered): LLM01 Prompt Injection, LLM04 Model Denial of Service, LLM06 Sensitive Information Disclosure.
- **AIR-native** (1 detector): forensic-chain-integrity check (no direct OWASP equivalent).

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

That generates a fresh signed capsule chain (13 steps, two baked-in OWASP ASI violations), verifies every signature, runs the detectors, and writes a `forensic-report.json` next to you. Full cold-start experience in one command, no LangChain wiring required.

## Instrument your agent

### LangChain

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

### OpenAI SDK

```python
from openai import OpenAI
from airsdk import AIRRecorder
from airsdk.integrations.openai import instrument_openai

recorder = AIRRecorder(log_path="my-agent.log", user_intent="Draft a Q3 sales report")
client = instrument_openai(OpenAI(), recorder)

# From now on chat completions write llm_start + llm_end Signed Intent Capsules automatically.
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "..."}],
)
```

### Anthropic SDK

```python
from anthropic import Anthropic
from airsdk import AIRRecorder
from airsdk.integrations.anthropic import instrument_anthropic

recorder = AIRRecorder(log_path="my-agent.log", user_intent="Draft a Q3 sales report")
client = instrument_anthropic(Anthropic(), recorder)

# From now on messages.create writes llm_start + llm_end Signed Intent Capsules automatically.
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
)
```

For tool calls your code executes, wrap them with `recorder.tool_start(...)` / `recorder.tool_end(...)` so the forensic chain captures them too.

### Custom code (any framework)

```python
from airsdk import AIRRecorder

recorder = AIRRecorder(log_path="my-agent.log")
recorder.llm_start(prompt="...")
# ... call your model ...
recorder.llm_end(response="...")
recorder.tool_start(tool_name="crm_read", tool_args={"account": "acme"})
# ... call your tool ...
recorder.tool_end(tool_output="...")
recorder.agent_finish(final_output="...")
```

Every call appends a signed Signed Intent Capsule to the log. No framework required.

## Run the forensic trace

```bash
air trace my-agent.log
```

You get console output like this:

```
[AIR v0.1.6] Loaded 34 agent steps across 1 conversations.
[Chain verified] 34 signatures valid.

  ASI01 Agent Goal Hijack detected at step 8
  ASI02 Tool Misuse & Exploitation detected at step 32
  ASI04 Agentic Supply Chain Vulnerabilities detected at step 6
  AIR-01 Prompt Injection detected at step 4
  AIR-02 Sensitive Data Exposure detected at step 11
  AIR-03 Unrestricted Resource Consumption detected at step 30
  AIR-04 Untraceable Action detected at step 32

OWASP Top 10 for Agentic Applications coverage (8 implemented, 2 on roadmap):
  ASI01 Agent Goal Hijack                         implemented
  ASI02 Tool Misuse & Exploitation                implemented
  ASI04 Agentic Supply Chain Vulnerabilities      partial: MCP supply-chain risk only
  ASI03 Identity & Privilege Abuse                not yet implemented
  ...

Additional detectors (OWASP LLM Top 10 + AIR-native):
  AIR-01 Prompt Injection           OWASP LLM01 Prompt Injection
  AIR-02 Sensitive Data Exposure    OWASP LLM06 Sensitive Information Disclosure
  AIR-03 Resource Consumption       OWASP LLM04 Model Denial of Service
  AIR-04 Untraceable Action         AIR-native (no direct OWASP equivalent)

[Export] forensic-report.json
```

Export formats: `air trace --format pdf` emits a human-readable PDF for legal and insurance stakeholders; `--format siem` emits ArcSight CEF v0 events for SIEM ingestion (Splunk, Sumo, QRadar, Datadog).

## Session 1 scope

This release covers the minimum forensic surface end-to-end:

| Capability                              | Status                    |
|-----------------------------------------|---------------------------|
| BLAKE3 + Ed25519 Signed Intent Capsule chain (AgDR-format) | implemented |
| Chain verification (tamper detection)   | implemented               |
| LangChain callback handler              | implemented               |
| ASI01 Agent Goal Hijack                    | implemented (heuristic)                           |
| ASI02 Tool Misuse & Exploitation           | implemented (regex)                               |
| ASI04 Agentic Supply Chain Vulnerabilities | implemented (partial: MCP supply-chain risk only) |
| ASI05 Unexpected Code Execution (RCE)      | implemented (execution-semantics tool-name patterns) |
| ASI06 Memory & Context Poisoning           | implemented (heuristic: retrieval-output + memory-write scans) |
| ASI07 Insecure Inter-Agent Communication   | implemented (identity, nonce, replay, downgrade, descriptor-forgery checks) |
| ASI08 Cascading Failures                   | implemented (oscillating-pair + fan-out burst checks over inter-agent messages) |
| ASI09 Human-Agent Trust Exploitation       | implemented (fabricated-rationale + manipulation-language scan preceding sensitive actions) |
| ASI03, ASI10                               | not yet implemented                               |
| AIR-01 Prompt Injection                    | implemented - maps to OWASP LLM01                 |
| AIR-02 Sensitive Data Exposure             | implemented - maps to OWASP LLM06                 |
| AIR-03 Unrestricted Resource Consumption   | implemented - maps to OWASP LLM04                 |
| AIR-04 Untraceable Action                  | implemented - AIR-native, no OWASP equivalent     |
| JSON forensic export                       | implemented                                       |
| PDF forensic export                        | implemented                                       |
| SIEM forensic export (ArcSight CEF v0)     | implemented                                       |
| LangChain callback integration             | implemented                                       |
| OpenAI SDK integration                     | implemented                                       |
| Anthropic SDK integration                  | implemented                                       |
| LlamaIndex / CrewAI / AutoGen              | not yet implemented                               |

The detectors are honest first-pass heuristics. They will produce false positives and false negatives. The signed chain itself is production-grade cryptography.

## Why AIR exists

The prevention layer is crowded. Lakera, NeMo Guardrails, Bedrock Guardrails, and a dozen other tools sit in front of your agent and try to stop bad things from happening. None of them tell you what actually happened when an agent ran, and none of them produce evidence an auditor, a regulator, or an insurance carrier can use.

AIR is the forensic and incident response layer that runs behind those tools. It does not replace them. It gives you a signed record of every agent decision, findings mapped to the OWASP Top 10 for Agentic Applications public taxonomy, exportable to formats your SIEM, your compliance team, and your carrier already understand.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

This is pre-1.0 and the shape will evolve. Issues, traces that break the detectors, and new ASI detector PRs are all welcome at https://github.com/get-sltr/vindicara-ai.
