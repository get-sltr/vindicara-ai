"""Tests for policy model and registry."""

import pytest

from vindicara.engine.policy import Policy, PolicyRegistry
from vindicara.engine.rules.deterministic import KeywordBlocklistRule, PIIDetectionRule
from vindicara.sdk.types import Severity, Verdict


class TestPolicy:
    def test_evaluate_allowed(self) -> None:
        policy = Policy(
            policy_id="test",
            name="Test Policy",
            rules=[
                KeywordBlocklistRule(
                    rule_id="kw", keywords=["hack"], severity=Severity.HIGH, message="blocked"
                )
            ],
        )
        result = policy.evaluate("This is clean text")
        assert result.verdict == Verdict.ALLOWED

    def test_evaluate_blocked(self) -> None:
        policy = Policy(
            policy_id="test",
            name="Test Policy",
            rules=[PIIDetectionRule(rule_id="pii", severity=Severity.CRITICAL)],
        )
        result = policy.evaluate("My SSN is 123-45-6789")
        assert result.verdict == Verdict.BLOCKED


class TestPolicyRegistry:
    def test_register_and_get(self) -> None:
        registry = PolicyRegistry()
        policy = Policy(policy_id="test", name="Test", rules=[])
        registry.register(policy)
        assert registry.get("test") is policy

    def test_get_missing_raises(self) -> None:
        registry = PolicyRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_policies(self) -> None:
        registry = PolicyRegistry()
        registry.register(Policy(policy_id="a", name="A", rules=[]))
        registry.register(Policy(policy_id="b", name="B", rules=[]))
        assert len(registry.list_policies()) == 2

    def test_builtin_policies_loaded(self) -> None:
        registry = PolicyRegistry.with_builtins()
        assert registry.get("content-safety") is not None
        assert registry.get("pii-filter") is not None
