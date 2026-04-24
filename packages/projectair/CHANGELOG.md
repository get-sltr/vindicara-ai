# Changelog

All notable changes to `projectair` are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [0.3.1] - 2026-04-23

### Added
- LlamaIndex LLM integration: `airsdk.integrations.llamaindex.instrument_llamaindex(llm, recorder)`. Wraps any `llama_index.core.llms.LLM` subclass as a transparent proxy that emits signed `llm_start` + `llm_end` Intent Capsules for every `complete` / `acomplete` / `stream_complete` / `astream_complete` / `chat` / `achat` / `stream_chat` / `astream_chat` call. Tool-call content on chat responses is captured in the `llm_end` payload. Every other attribute passes through unchanged, so the wrapped object drops into LlamaIndex query engines, chat engines, and agents wherever a plain LLM is expected.

## [0.3.0] - 2026-04-22

### Added
- ASI03 Identity & Privilege Abuse detector: Zero-Trust-for-agents enforcement via operator-declared `AgentRegistry` (identity forgery, unknown agent, out-of-scope tool, privilege-tier escalation).
- ASI10 Rogue Agents detector: Zero-Trust behavioral-scope enforcement via declared `BehavioralScope` (unexpected tool, fan-out breach, off-hours activity, session tool budget).
- `air report article72` command: EU AI Act Article 72 post-market monitoring Markdown template generation.
- `AgentRegistry`, `AgentDescriptor`, `BehavioralScope` pydantic schemas exported from the top-level `airsdk` package.

### Changed
- Public OWASP coverage framing is now "10 OWASP Agentic + 3 OWASP LLM + 1 AIR-native." `UNIMPLEMENTED_DETECTORS` is empty.

## [0.2.4] - 2026

### Added
- ASI08 Cascading Failures detector: oscillating-pair threshold (4 cycles) + fan-out threshold (5 distinct targets within 10-record window) over `agent_message` records.

## [0.2.3] - 2026

### Added
- ASI05 Unexpected Code Execution detector: tool-name / argument pattern match for execution semantics (eval, exec, shell).
- ASI09 Human-Agent Trust Exploitation detector: fabricated-rationale and manipulation-language scan preceding sensitive actions.

## [0.2.1] - 2026

### Added
- ASI06 Memory & Context Poisoning detector (heuristic: retrieval-output + memory-write scans).
- ASI07 Insecure Inter-Agent Communication detector (identity, nonce, replay, downgrade, descriptor-forgery checks over `agent_message` records).

## [0.1.x] - 2026

### Added
- Initial public release. BLAKE3 + Ed25519 Signed Intent Capsule chain (AgDR-compatible format). Chain verification and tamper detection. LangChain callback handler (`AIRCallbackHandler`). OpenAI SDK integration (`instrument_openai`). Anthropic SDK integration (`instrument_anthropic`). ASI01 Agent Goal Hijack, ASI02 Tool Misuse & Exploitation, and partial ASI04 Agentic Supply Chain (MCP only) detectors. AIR-01 Prompt Injection (OWASP LLM01), AIR-02 Sensitive Data Exposure (OWASP LLM06), AIR-03 Resource Consumption (OWASP LLM04), AIR-04 Untraceable Action (AIR-native). JSON, PDF, and SIEM (ArcSight CEF v0) forensic exports. `air` Typer CLI with `demo`, `trace`, `report` commands.
