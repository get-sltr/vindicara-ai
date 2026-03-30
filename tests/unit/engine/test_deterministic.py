"""Tests for deterministic policy rules."""

import pytest

from vindicara.engine.rules.deterministic import (
    KeywordBlocklistRule,
    PIIDetectionRule,
    RegexRule,
)
from vindicara.sdk.types import Severity


class TestRegexRule:
    def test_matches_pattern(self) -> None:
        rule = RegexRule(
            rule_id="no-urls",
            pattern=r"https?://\S+",
            severity=Severity.MEDIUM,
            message="URL detected",
        )
        result = rule.evaluate("Visit https://evil.com for details")
        assert result.triggered
        assert result.severity == Severity.MEDIUM

    def test_no_match(self) -> None:
        rule = RegexRule(
            rule_id="no-urls",
            pattern=r"https?://\S+",
            severity=Severity.MEDIUM,
            message="URL detected",
        )
        result = rule.evaluate("No URLs here")
        assert not result.triggered

    def test_case_insensitive(self) -> None:
        rule = RegexRule(
            rule_id="no-secret",
            pattern=r"(?i)secret\s*key",
            severity=Severity.HIGH,
            message="Secret key reference detected",
        )
        result = rule.evaluate("My SECRET KEY is abc123")
        assert result.triggered


class TestKeywordBlocklistRule:
    def test_blocks_keyword(self) -> None:
        rule = KeywordBlocklistRule(
            rule_id="toxicity",
            keywords=["hack", "exploit", "attack"],
            severity=Severity.HIGH,
            message="Blocked keyword detected",
        )
        result = rule.evaluate("How to hack a server")
        assert result.triggered

    def test_case_insensitive(self) -> None:
        rule = KeywordBlocklistRule(
            rule_id="toxicity",
            keywords=["hack"],
            severity=Severity.HIGH,
            message="Blocked keyword detected",
        )
        result = rule.evaluate("HACKING is bad")
        assert result.triggered

    def test_clean_input(self) -> None:
        rule = KeywordBlocklistRule(
            rule_id="toxicity",
            keywords=["hack", "exploit"],
            severity=Severity.HIGH,
            message="Blocked keyword detected",
        )
        result = rule.evaluate("How to build a secure server")
        assert not result.triggered


class TestPIIDetectionRule:
    def test_detects_ssn(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-ssn", severity=Severity.CRITICAL)
        result = rule.evaluate("My SSN is 123-45-6789")
        assert result.triggered
        assert "SSN" in result.message

    def test_detects_email(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-email", severity=Severity.HIGH)
        result = rule.evaluate("Contact me at john@example.com")
        assert result.triggered
        assert "email" in result.message.lower()

    def test_detects_credit_card(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-cc", severity=Severity.CRITICAL)
        result = rule.evaluate("Card: 4111-1111-1111-1111")
        assert result.triggered

    def test_detects_phone(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-phone", severity=Severity.MEDIUM)
        result = rule.evaluate("Call me at (555) 123-4567")
        assert result.triggered

    def test_no_pii(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-all", severity=Severity.HIGH)
        result = rule.evaluate("The weather is sunny today")
        assert not result.triggered

    @pytest.mark.adversarial
    def test_obfuscated_ssn_with_spaces(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-ssn", severity=Severity.CRITICAL)
        result = rule.evaluate("SSN: 123 45 6789")
        assert result.triggered

    @pytest.mark.adversarial
    def test_ssn_without_dashes(self) -> None:
        rule = PIIDetectionRule(rule_id="pii-ssn", severity=Severity.CRITICAL)
        result = rule.evaluate("My number is 123456789 for tax")
        assert result.triggered
