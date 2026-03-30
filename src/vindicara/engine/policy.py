"""Policy model, registry, and built-in policy definitions."""

import time
from dataclasses import dataclass

from vindicara.engine.rules.base import Rule
from vindicara.engine.rules.deterministic import (
    KeywordBlocklistRule,
    PIIDetectionRule,
    RegexRule,
)
from vindicara.sdk.types import GuardResult, PolicyInfo, Severity, Verdict


@dataclass
class Policy:
    """A named collection of rules that evaluates text."""

    policy_id: str
    name: str
    rules: list[Rule]
    description: str = ""
    version: int = 1
    enabled: bool = True

    def evaluate(self, text: str) -> GuardResult:
        start = time.perf_counter()
        results = [rule.evaluate(text) for rule in self.rules]
        elapsed_ms = (time.perf_counter() - start) * 1000

        has_critical = any(r.triggered and r.severity == Severity.CRITICAL for r in results)
        has_high = any(r.triggered and r.severity == Severity.HIGH for r in results)
        has_triggered = any(r.triggered for r in results)

        if has_critical or has_high:
            verdict = Verdict.BLOCKED
        elif has_triggered:
            verdict = Verdict.FLAGGED
        else:
            verdict = Verdict.ALLOWED

        return GuardResult(
            verdict=verdict,
            policy_id=self.policy_id,
            rules=results,
            latency_ms=round(elapsed_ms, 3),
        )

    def to_info(self) -> PolicyInfo:
        return PolicyInfo(
            policy_id=self.policy_id,
            name=self.name,
            description=self.description,
            version=self.version,
            enabled=self.enabled,
            rule_count=len(self.rules),
        )


class PolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def register(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: str) -> Policy:
        return self._policies[policy_id]

    def list_policies(self) -> list[PolicyInfo]:
        return [p.to_info() for p in self._policies.values()]

    @classmethod
    def with_builtins(cls) -> "PolicyRegistry":
        registry = cls()
        registry.register(_build_content_safety_policy())
        registry.register(_build_pii_filter_policy())
        registry.register(_build_prompt_injection_policy())
        return registry


def _build_content_safety_policy() -> Policy:
    return Policy(
        policy_id="content-safety",
        name="Content Safety",
        description="Blocks harmful, toxic, and policy-violating content",
        rules=[
            KeywordBlocklistRule(
                rule_id="harmful-instructions",
                keywords=[
                    "how to hack",
                    "how to exploit",
                    "how to attack",
                    "how to steal",
                    "how to bypass security",
                ],
                severity=Severity.HIGH,
                message="Harmful instruction pattern detected",
            ),
            RegexRule(
                rule_id="credential-leak",
                pattern=r"(?i)(password|api[_\s]?key|secret[_\s]?key|token)\s*[:=]\s*\S+",
                severity=Severity.CRITICAL,
                message="Potential credential leak detected",
            ),
        ],
    )


def _build_pii_filter_policy() -> Policy:
    return Policy(
        policy_id="pii-filter",
        name="PII Filter",
        description="Detects and blocks personally identifiable information",
        rules=[
            PIIDetectionRule(rule_id="pii-detect", severity=Severity.CRITICAL),
        ],
    )


def _build_prompt_injection_policy() -> Policy:
    return Policy(
        policy_id="prompt-injection",
        name="Prompt Injection Defense",
        description="Detects common prompt injection patterns",
        rules=[
            RegexRule(
                rule_id="ignore-instructions",
                pattern=r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|context)",
                severity=Severity.CRITICAL,
                message="Prompt injection attempt: instruction override detected",
            ),
            RegexRule(
                rule_id="system-prompt-extract",
                pattern=r"(?i)(reveal|show|print|output|display)\s+(your\s+)?(system\s+prompt|instructions|rules)",
                severity=Severity.HIGH,
                message="Prompt injection attempt: system prompt extraction",
            ),
            RegexRule(
                rule_id="role-play-injection",
                pattern=r"(?i)you\s+are\s+now\s+(a|an|the)\s+\w+",
                severity=Severity.MEDIUM,
                message="Potential prompt injection: role reassignment",
            ),
        ],
    )
