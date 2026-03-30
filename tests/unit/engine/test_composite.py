"""Tests for composite rule chains."""

from vindicara.engine.rules.composite import AllOfRule, AnyOfRule, NotRule
from vindicara.engine.rules.deterministic import KeywordBlocklistRule, RegexRule
from vindicara.sdk.types import Severity


class TestAnyOfRule:
    def test_triggers_if_any_child_triggers(self) -> None:
        rule = AnyOfRule(
            rule_id="any-danger",
            rules=[
                KeywordBlocklistRule(
                    rule_id="kw", keywords=["hack"], severity=Severity.HIGH, message="kw"
                ),
                RegexRule(
                    rule_id="url", pattern=r"https?://", severity=Severity.MEDIUM, message="url"
                ),
            ],
            severity=Severity.HIGH,
        )
        result = rule.evaluate("Visit https://safe.com")
        assert result.triggered

    def test_does_not_trigger_if_none_trigger(self) -> None:
        rule = AnyOfRule(
            rule_id="any-danger",
            rules=[
                KeywordBlocklistRule(
                    rule_id="kw", keywords=["hack"], severity=Severity.HIGH, message="kw"
                ),
            ],
            severity=Severity.HIGH,
        )
        result = rule.evaluate("This is safe text")
        assert not result.triggered


class TestAllOfRule:
    def test_triggers_only_if_all_children_trigger(self) -> None:
        rule = AllOfRule(
            rule_id="all-danger",
            rules=[
                KeywordBlocklistRule(
                    rule_id="kw", keywords=["hack"], severity=Severity.HIGH, message="kw"
                ),
                RegexRule(
                    rule_id="url", pattern=r"https?://", severity=Severity.MEDIUM, message="url"
                ),
            ],
            severity=Severity.CRITICAL,
        )
        result = rule.evaluate("hack the site at https://evil.com")
        assert result.triggered

    def test_does_not_trigger_if_only_some_trigger(self) -> None:
        rule = AllOfRule(
            rule_id="all-danger",
            rules=[
                KeywordBlocklistRule(
                    rule_id="kw", keywords=["hack"], severity=Severity.HIGH, message="kw"
                ),
                RegexRule(
                    rule_id="url", pattern=r"https?://", severity=Severity.MEDIUM, message="url"
                ),
            ],
            severity=Severity.CRITICAL,
        )
        result = rule.evaluate("hack the system")
        assert not result.triggered


class TestNotRule:
    def test_inverts_trigger(self) -> None:
        inner = KeywordBlocklistRule(
            rule_id="kw", keywords=["safe"], severity=Severity.LOW, message="safe word"
        )
        rule = NotRule(rule_id="not-safe", inner=inner, severity=Severity.MEDIUM)
        result = rule.evaluate("This is dangerous content")
        assert result.triggered

    def test_inverts_no_trigger(self) -> None:
        inner = KeywordBlocklistRule(
            rule_id="kw", keywords=["safe"], severity=Severity.LOW, message="safe word"
        )
        rule = NotRule(rule_id="not-safe", inner=inner, severity=Severity.MEDIUM)
        result = rule.evaluate("This is safe content")
        assert not result.triggered
