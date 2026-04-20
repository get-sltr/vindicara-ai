"""OWASP Top 10 for Agentic Applications detectors (session 1 coverage).

Only ASI01 and ASI02 are implemented in session 1. The rest are declared in
``UNIMPLEMENTED_DETECTORS`` so the CLI can surface honest coverage state instead
of silently pretending we checked them.
"""
from __future__ import annotations

import re

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

# ASI02 dangerous-argument patterns. Defensible surface; expands over time.
DANGEROUS_ARG_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("shell metacharacters", re.compile(r"(?:\||;|&&|\$\(|`).*(?:rm|curl|wget|nc\s|bash|sh\s)", re.IGNORECASE)),
    ("path traversal", re.compile(r"\.\./|\.\.\\|/etc/passwd|/etc/shadow|%2e%2e", re.IGNORECASE)),
    ("unbounded SQL DELETE", re.compile(r"delete\s+from\s+\w+(?:\s*;|\s*$)", re.IGNORECASE)),
    ("unbounded SQL UPDATE", re.compile(r"update\s+\w+\s+set\s+[^;]*?(?:;|$)(?!.*where)", re.IGNORECASE | re.DOTALL)),
    ("SSRF-shaped URL", re.compile(r"https?://(?:127\.|0\.0\.0\.0|localhost|169\.254\.|10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)", re.IGNORECASE)),
    ("credential leak", re.compile(r"(?:aws_secret|api[_-]?key|password|bearer\s+[a-z0-9]{20,})", re.IGNORECASE)),
)

UNIMPLEMENTED_DETECTORS: tuple[tuple[str, str], ...] = (
    ("ASI03", "Prompt Injection"),
    ("ASI04", "Memory Poisoning"),
    ("ASI05", "Sensitive Data Exposure"),
    ("ASI06", "Excessive Agency"),
    ("ASI07", "Unrestricted Resource Consumption"),
    ("ASI08", "Plan Corruption"),
    ("ASI09", "Supply Chain and MCP Risk"),
    ("ASI10", "Untraceable Action"),
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
    """ASI01: user asked for one thing, agent invokes tools unrelated to it."""
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
                    asi_id="ASI01",
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
    """ASI02: tool invoked with arguments matching known dangerous patterns."""
    findings: list[Finding] = []
    for index, record in enumerate(records):
        if record.kind != StepKind.TOOL_START or not record.payload.tool_args:
            continue
        arg_blob = " ".join(str(v) for v in record.payload.tool_args.values())
        for label, pattern in DANGEROUS_ARG_PATTERNS:
            if pattern.search(arg_blob):
                findings.append(
                    Finding(
                        asi_id="ASI02",
                        title="Tool Misuse",
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


def run_detectors(records: list[AgDRRecord]) -> list[Finding]:
    """Run every implemented detector and return a flat list of findings."""
    return [
        *detect_goal_hijack(records),
        *detect_tool_misuse(records),
    ]
