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

When an AI agent goes off-script, AIR tells you what happened and proves it. Every agent decision is written as a signed AgDR (AI Decision Record) with a BLAKE3 content hash and an Ed25519 signature, chained to the previous step. The `air` CLI replays that chain, verifies every signature, and reports OWASP Top 10 for Agentic Applications violations (5 of 10 detectors shipped: ASI01, ASI02, ASI03, ASI05, ASI09 today; ASI04, ASI06, ASI07, ASI08, ASI10 on roadmap).

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

# From now on chat completions write llm_start + llm_end AgDR records automatically.
response = client.chat.completions.create(
    model="gpt-4o",
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

Every call appends a signed AgDR record to the log. No framework required.

## Run the forensic trace

```bash
air trace my-agent.log
```

You get console output like this:

```
[AIR v0.1.4] Loaded 247 agent steps across 3 conversations.
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
| ASI05 Sensitive Data Exposure detector  | implemented (pattern set) |
| ASI09 Supply Chain / MCP Risk detector  | implemented (heuristic)   |
| ASI04, ASI06, ASI07, ASI08, ASI10       | not yet implemented       |
| JSON forensic export                    | implemented               |
| PDF forensic export                     | implemented               |
| SIEM forensic export (ArcSight CEF v0)  | implemented               |
| LangChain callback integration          | implemented               |
| OpenAI SDK integration                  | implemented               |
| Anthropic / LlamaIndex / CrewAI / AutoGen | not yet implemented     |

The detectors are honest first-pass heuristics. They will produce false positives and false negatives. The signed chain itself is production-grade cryptography.

## Why AIR exists

The prevention layer is crowded. Lakera, NeMo Guardrails, Bedrock Guardrails, and a dozen other tools sit in front of your agent and try to stop bad things from happening. None of them tell you what actually happened when an agent ran, and none of them produce evidence an auditor, a regulator, or an insurance carrier can use.

AIR is the forensic and incident response layer that runs behind those tools. It does not replace them. It gives you a signed record of every agent decision, findings mapped to the OWASP Top 10 for Agentic Applications public taxonomy, exportable to formats your SIEM, your compliance team, and your carrier already understand.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

This is pre-1.0 and the shape will evolve. Issues, traces that break the detectors, and new ASI detector PRs are all welcome at https://github.com/get-sltr/vindicara-ai.
