"""Agent registry loader and validation behavior."""
from __future__ import annotations

from pathlib import Path

import pytest

from airsdk.registry import (
    DEFAULT_PRIVILEGE_TIER,
    WILDCARD_TOOL,
    AgentDescriptor,
    AgentRegistry,
    BehavioralScope,
    is_hex_64,
    load_registry,
)

VALID_HEX_KEY = "a" * 64
OTHER_HEX_KEY = "b" * 64


def test_load_yaml_registry(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text(
        "agents:\n"
        f"  - id: sales-agent\n"
        f"    signer_key: {VALID_HEX_KEY}\n"
        "    permitted_tools: [crm_read, email_draft]\n"
        "    privilege_tier: 1\n"
        "tool_privilege_tiers:\n"
        "  admin_delete: 3\n",
        encoding="utf-8",
    )
    registry = load_registry(registry_file)
    assert len(registry.agents) == 1
    assert registry.agents[0].id == "sales-agent"
    assert registry.agents[0].signer_key == VALID_HEX_KEY
    assert registry.agents[0].permitted_tools == ["crm_read", "email_draft"]
    assert registry.agents[0].privilege_tier == 1
    assert registry.tool_privilege_tiers == {"admin_delete": 3}


def test_load_json_registry(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(
        '{"agents":[{"id":"a","signer_key":"'
        + VALID_HEX_KEY
        + '","permitted_tools":["*"],"privilege_tier":0}]}',
        encoding="utf-8",
    )
    registry = load_registry(registry_file)
    assert registry.agents[0].id == "a"
    assert registry.agents[0].permitted_tools == [WILDCARD_TOOL]


def test_load_yml_extension_also_works(tmp_path: Path) -> None:
    """Both ``.yaml`` and ``.yml`` must select the YAML parser."""
    registry_file = tmp_path / "registry.yml"
    registry_file.write_text(
        f"agents:\n  - id: a\n    signer_key: {VALID_HEX_KEY}\n",
        encoding="utf-8",
    )
    registry = load_registry(registry_file)
    assert registry.agents[0].id == "a"


def test_load_registry_rejects_unknown_extension(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.toml"
    registry_file.write_text("agents = []", encoding="utf-8")
    with pytest.raises(ValueError, match="\\.yaml, \\.yml, or \\.json"):
        load_registry(registry_file)


def test_load_registry_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_registry(tmp_path / "does-not-exist.yaml")


def test_load_registry_raises_on_non_mapping_root(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be a mapping"):
        load_registry(registry_file)


def test_load_registry_tolerates_empty_yaml_file(tmp_path: Path) -> None:
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text("", encoding="utf-8")
    registry = load_registry(registry_file)
    assert registry.agents == []
    assert registry.tool_privilege_tiers == {}


def test_signer_key_must_be_hex_64() -> None:
    with pytest.raises(ValueError, match="signer_key"):
        AgentDescriptor(id="bad", signer_key="not-hex")
    with pytest.raises(ValueError, match="signer_key"):
        AgentDescriptor(id="bad", signer_key="a" * 63)
    with pytest.raises(ValueError, match="signer_key"):
        AgentDescriptor(id="bad", signer_key="a" * 65)


def test_signer_key_accepts_mixed_case_hex() -> None:
    mixed = "Aa1B" * 16
    assert len(mixed) == 64
    agent = AgentDescriptor(id="a", signer_key=mixed)
    assert agent.signer_key == mixed


def test_privilege_tier_rejects_negative() -> None:
    with pytest.raises(ValueError, match="privilege_tier"):
        AgentDescriptor(id="a", signer_key=VALID_HEX_KEY, privilege_tier=-1)


def test_agent_id_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="id"):
        AgentDescriptor(id="", signer_key=VALID_HEX_KEY)


def test_registry_get_by_id() -> None:
    registry = AgentRegistry(
        agents=[
            AgentDescriptor(id="a", signer_key=VALID_HEX_KEY),
            AgentDescriptor(id="b", signer_key=OTHER_HEX_KEY),
        ]
    )
    assert registry.get("a") is not None
    assert registry.get("a").id == "a"  # type: ignore[union-attr]
    assert registry.get("nope") is None


def test_allows_tool_exact_match_and_wildcard() -> None:
    exact = AgentDescriptor(id="a", signer_key=VALID_HEX_KEY, permitted_tools=["crm_read"])
    assert exact.allows_tool("crm_read") is True
    assert exact.allows_tool("crm_write") is False

    wild = AgentDescriptor(id="a", signer_key=VALID_HEX_KEY, permitted_tools=[WILDCARD_TOOL])
    assert wild.allows_tool("anything") is True


def test_required_tier_defaults_to_zero_for_untiered_tool() -> None:
    registry = AgentRegistry(tool_privilege_tiers={"admin_delete": 3})
    assert registry.required_tier_for_tool("admin_delete") == 3
    assert registry.required_tier_for_tool("crm_read") == DEFAULT_PRIVILEGE_TIER


def test_behavioral_scope_fields_are_all_optional() -> None:
    """Operator can opt into scope dimensions incrementally."""
    empty = BehavioralScope()
    assert empty.expected_tools == []
    assert empty.max_fan_out_targets is None
    assert empty.allowed_hours_utc is None
    assert empty.max_session_tool_calls is None
    assert empty.allowed_data_domains == []

    partial = BehavioralScope(max_fan_out_targets=3)
    assert partial.max_fan_out_targets == 3
    assert partial.allowed_hours_utc is None


def test_behavioral_scope_rejects_zero_fan_out() -> None:
    with pytest.raises(ValueError, match="max_fan_out_targets"):
        BehavioralScope(max_fan_out_targets=0)


def test_agent_descriptor_serialises_behavioral_scope(tmp_path: Path) -> None:
    """Round-trip an agent with a behavioral_scope through YAML to confirm schema coherence."""
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text(
        f"agents:\n"
        f"  - id: a\n"
        f"    signer_key: {VALID_HEX_KEY}\n"
        "    permitted_tools: [crm_read]\n"
        "    behavioral_scope:\n"
        "      expected_tools: [crm_read, email_draft]\n"
        "      max_fan_out_targets: 3\n"
        "      allowed_hours_utc: [13, 14, 15, 16]\n"
        "      max_session_tool_calls: 50\n",
        encoding="utf-8",
    )
    registry = load_registry(registry_file)
    agent = registry.agents[0]
    assert agent.behavioral_scope is not None
    assert agent.behavioral_scope.max_fan_out_targets == 3
    assert agent.behavioral_scope.allowed_hours_utc == [13, 14, 15, 16]
    assert agent.behavioral_scope.max_session_tool_calls == 50


def test_is_hex_64() -> None:
    assert is_hex_64("a" * 64) is True
    assert is_hex_64("A" * 64) is True
    assert is_hex_64("0123456789abcdefABCDEF" + "0" * 42) is True
    assert is_hex_64("a" * 63) is False
    assert is_hex_64("g" * 64) is False
    assert is_hex_64("") is False
