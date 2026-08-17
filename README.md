<p align="center">
  <img src="https://vindicara.io/hero-mesh.png" alt="" width="100%">
</p>

<h1 align="center">Project AIR</h1>

<p align="center">
  <strong>Evidence-grade infrastructure for accountable AI agents.</strong><br>
  Cryptographic chain-of-custody. Court-supportable records. Rekor-anchored proof.
</p>

<p align="center">
  <a href="https://vindicara.io">vindicara.io</a> ·
  <a href="https://vindicara.io/blog/secure-ai-agents-5-minutes">Quickstart</a> ·
  <a href="https://vindicara.io/pricing">Pricing</a> ·
  <a href="https://vindicara.io/ops-chain">Verify our ops chain</a> ·
  <a href="https://vindicara.io/blog">Blog</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/pypi/v/projectair?style=flat-square&color=blue" alt="PyPI">
</p>

---

## What AIR is

AIR writes a **Signed Intent Capsule** for every agent decision. Each capsule carries a BLAKE3 content hash and an Ed25519 signature (with opt-in experimental ML-DSA-65 / FIPS 204 post-quantum signing), chained to the previous step. The chain root is anchored to [Sigstore Rekor](https://docs.sigstore.dev/) (public transparency log) and RFC 3161 trusted timestamps. The result is evidence that survives subpoena, survives the vendor, and survives the auditor's first question.

```bash
pip install projectair
air demo
```

> **Requires Python 3.10+.** macOS's default `python3` is often older. If `pip install` reports `ERROR: ... (from versions: none)`, you're on an older interpreter. Install into a venv built with a newer Python: `python3.12 -m venv ~/air-venv && ~/air-venv/bin/pip install projectair`.

## The five-layer stack

| Layer | What it does | Status |
|---|---|---|
| **0. Detection** | 10 OWASP Agentic + 3 OWASP LLM + 3 AIR-native (16 detectors) | shipped |
| **1. External Trust Anchor** | RFC 3161 timestamps + Sigstore Rekor transparency log | shipped (0.4.0) |
| **2. Causal Reasoning** | `air explain` walks the chain, explains why a step happened | shipped (0.5.0) |
| **3. Containment + Step-Up** | Halt agent actions; require Auth0-verified human approval | shipped (0.6.0) |
| **4. AgDR Handoff Protocol (A2A)** | Cross-agent chain of custody with W3C Trace Context + Rekor counter-attestation | shipped (0.7.0, Wave 1 alpha) |
| **5. Data Governance** | Data-asset lineage, data-subject tracking, DSAR, OpenLineage export | shipped (1.0.0, Pro) |

## We run it on our own infrastructure

Vindicara dogfoods Project AIR. Every API request to `vindicara.io` is recorded as a signed AgDR chain using the same `airsdk` library customers use, anchored to public Sigstore Rekor every 60 seconds, and published as redacted JSONL.

Verify it yourself:

```bash
curl https://vindicara-ops-chain-public-399827112476.s3.us-west-2.amazonaws.com/ops-chain/manifest.json
```

The chain catalog, manifest, and every Rekor anchor are independently verifiable with zero Vindicara infrastructure in the path. See [vindicara.io/ops-chain](https://vindicara.io/ops-chain) for the live dashboard.

## Detector coverage

**OWASP Top 10 for Agentic Applications (10 of 10):** ASI01 Agent Goal Hijack, ASI02 Tool Misuse, ASI03 Identity & Privilege Abuse (Zero-Trust `AgentRegistry`), ASI04 Agentic Supply Chain (partial, MCP), ASI05 Unexpected Code Execution, ASI06 Memory & Context Poisoning, ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Exploitation, ASI10 Rogue Agents (Zero-Trust `BehavioralScope`).

**OWASP Top 10 for LLM Applications (3 categories):** AIR-01 Prompt Injection (LLM01), AIR-02 Sensitive Data Exposure (LLM06), AIR-03 Unrestricted Resource Consumption (LLM04).

**AIR-native (3):** AIR-04 Untraceable Action (forensic-chain-integrity check), AIR-05 NemoGuard Safety Classification (NVIDIA NemoGuard NIM findings), AIR-06 NemoGuard Corroboration (AIR heuristic + NVIDIA safety model agree independently).

Total: **16 detectors** (10 + 3 + 3) running over every chain, mapped to public taxonomies.

## Framework integrations

| Framework | Integration | Since |
|---|---|---|
| LangChain | `AIRCallbackHandler` | 0.1.0 |
| OpenAI SDK | `instrument_openai` | 0.1.0 |
| Anthropic SDK | `instrument_anthropic` | 0.1.0 |
| LlamaIndex | `instrument_llamaindex` | 0.3.1 |
| Google Gemini SDK | `instrument_gemini` | 0.3.2 |
| Google ADK | `instrument_adk` | 0.3.2 |
| NVIDIA NIM / vLLM / TGI / Together / Groq / Mistral / Fireworks | via `instrument_openai` (OpenAI-compatible) | 0.3.2 |
| Custom code | `AIRRecorder` directly | 0.1.0 |

## What's in this repo

This is a monorepo.

- **[`packages/projectair/`](packages/projectair/)**: the MIT-licensed `projectair` package on PyPI. Ships the `air` CLI and the `airsdk` Python library. This is the public product.
- **[`vindicara-site/`](vindicara-site/)**: the SvelteKit source for [vindicara.io](https://vindicara.io) and the Flightdeck console.
- **`src/vindicara/`**: the Apache-2.0 engine substrate (policy evaluator, MCP scanner, agent IAM, drift monitor, compliance collector, ops chain). Powers AIR Cloud.
- **[`packages/air-dashboard/`](packages/air-dashboard/)**: the AIR Cloud dashboard (SvelteKit + Three.js).

## CLI surface

```
air demo                  Cold-start demo (SSH-exfil attack chain, 16 detectors)
air trace <chain>         Verify signatures, run detectors, emit forensic report
air verify-public <chain> Verify using only public infrastructure (no Vindicara calls)
air anchor <chain>        Anchor the chain to RFC 3161 + Sigstore Rekor
air explain <chain>       Causal explanation: --step <id> | --finding <detector_id>
air approve               Layer 3 step-up: --token | --device | --authorize-url
air handoff verify        Layer 4: eight-step cross-agent chain-of-custody verifier
air report article72      EU AI Act Article 72 post-market monitoring template
air governance dsar       Layer 5: data-subject access report (Pro)
air attest                Hardware root of trust: NVIDIA NRAS attestation (experimental)
```

## Backed by

<p align="center">
  <a href="https://www.nvidia.com/en-us/startups/"><img src="assets/nvidia-inception-program-badge.svg" alt="NVIDIA Inception Program member" height="64"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://e2b.dev/startups"><img src="assets/e2b-startups.svg" alt="Sponsored by E2B for Startups" height="30"></a>
</p>

## License

- `packages/projectair/` and the `projectair` PyPI distribution: **MIT**. See [`packages/projectair/LICENSE`](packages/projectair/LICENSE).
- `src/vindicara/` (engine substrate): **Apache-2.0**.
