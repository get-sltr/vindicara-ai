"""Public response types for the Vindicara SDK."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    """Result of a policy evaluation."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FLAGGED = "flagged"


class Severity(StrEnum):
    """Severity level for a rule trigger."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleResult(BaseModel):
    """Result of evaluating a single rule within a policy."""

    rule_id: str
    triggered: bool
    severity: Severity
    message: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class GuardResult(BaseModel):
    """Result of a guard() evaluation."""

    verdict: Verdict
    policy_id: str
    rules: list[RuleResult] = Field(default_factory=list)
    latency_ms: float = 0.0
    evaluation_id: str = ""

    @property
    def is_allowed(self) -> bool:
        """True if the evaluation passed without blocking."""
        return self.verdict == Verdict.ALLOWED

    @property
    def is_blocked(self) -> bool:
        """True if the evaluation resulted in a block."""
        return self.verdict == Verdict.BLOCKED

    @property
    def triggered_rules(self) -> list[RuleResult]:
        """Rules that were triggered during evaluation."""
        return [r for r in self.rules if r.triggered]


class PolicyInfo(BaseModel):
    """Information about a registered policy."""

    policy_id: str
    name: str
    description: str = ""
    version: int = 1
    enabled: bool = True
    rule_count: int = 0
