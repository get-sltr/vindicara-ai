"""Deterministic policy rules: regex, keyword blocklist, PII detection."""

import re
from dataclasses import dataclass, field

from vindicara.sdk.types import RuleResult, Severity

_SSN_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
_PHONE_PATTERN = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("SSN", _SSN_PATTERN),
    ("email address", _EMAIL_PATTERN),
    ("credit card number", _CREDIT_CARD_PATTERN),
    ("phone number", _PHONE_PATTERN),
]


@dataclass(frozen=True)
class RegexRule:
    """Evaluates text against a regex pattern."""

    rule_id: str
    pattern: str
    severity: Severity
    message: str
    _compiled: re.Pattern[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.pattern))

    def evaluate(self, text: str) -> RuleResult:
        triggered = bool(self._compiled.search(text))
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            severity=self.severity,
            message=self.message if triggered else "",
        )


@dataclass(frozen=True)
class KeywordBlocklistRule:
    """Evaluates text against a list of blocked keywords."""

    rule_id: str
    keywords: list[str]
    severity: Severity
    message: str

    def evaluate(self, text: str) -> RuleResult:
        text_lower = text.lower()
        matched = [kw for kw in self.keywords if kw.lower() in text_lower]
        triggered = len(matched) > 0
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            severity=self.severity,
            message=self.message if triggered else "",
            metadata={"matched_keywords": ",".join(matched)} if triggered else {},
        )


@dataclass(frozen=True)
class PIIDetectionRule:
    """Detects personally identifiable information in text."""

    rule_id: str
    severity: Severity

    def evaluate(self, text: str) -> RuleResult:
        detected: list[str] = []
        for pii_type, pattern in _PII_PATTERNS:
            if pattern.search(text):
                detected.append(pii_type)
        triggered = len(detected) > 0
        return RuleResult(
            rule_id=self.rule_id,
            triggered=triggered,
            severity=self.severity,
            message=f"PII detected: {', '.join(detected)}" if triggered else "",
            metadata={"pii_types": ",".join(detected)} if triggered else {},
        )
