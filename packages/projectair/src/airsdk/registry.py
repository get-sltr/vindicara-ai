"""Agent identity registry for ASI03 Identity & Privilege Abuse and
ASI10 Rogue Agents (Zero-Trust enforcement).

The registry is an operator-supplied declaration of which agents exist, what
signing keys they use, and what each agent is authorised to do. Detectors
check live agent behaviour against the registry; without a registry,
the scope detectors emit no findings.

The registry is explicitly a Zero-Trust substrate, not a learned baseline.
If the operator has not declared scope, AIR refuses to fabricate anomalies
from a statistical model that does not exist.

Format
------
YAML (preferred for hand-authored policy) or JSON (stdlib, zero-dep at parse
time). The file extension drives the parser: ``.yaml`` / ``.yml`` uses
``yaml.safe_load``; ``.json`` uses ``json.loads``. Any other extension raises
``ValueError``.

Example (YAML)::

    agents:
      - id: sales-assistant-v2
        signer_key: "1a2b3c...64 hex chars..."
        permitted_tools: [crm_read, email_draft]
        privilege_tier: 1
        behavioral_scope:
          expected_tools: [crm_read, email_draft, draft_report]
          max_fan_out_targets: 3
          allowed_hours_utc: [13, 14, 15, 16, 17, 18, 19, 20, 21]
          max_session_tool_calls: 50

      - id: admin-bot
        signer_key: "..."
        permitted_tools: ["*"]
        privilege_tier: 3

    tool_privilege_tiers:
      admin_delete_records: 3
      shell_exec: 3
      db_migrate: 2
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

WILDCARD_TOOL = "*"
DEFAULT_PRIVILEGE_TIER = 0
HEX_64 = r"^[0-9a-fA-F]{64}$"

_HEX_64_RE = re.compile(HEX_64)


class BehavioralScope(BaseModel):
    """Declared behavioral envelope for an agent (ASI10 Zero-Trust enforcement).

    Every field is optional. Only declared fields are enforced; fields left
    unset are not checked. This lets operators opt into individual scope
    dimensions incrementally without having to declare them all.
    """

    model_config = ConfigDict(extra="forbid")

    expected_tools: list[str] = Field(default_factory=list)
    max_fan_out_targets: int | None = Field(default=None, ge=1)
    allowed_hours_utc: list[int] | None = None
    max_session_tool_calls: int | None = Field(default=None, ge=1)
    allowed_data_domains: list[str] = Field(default_factory=list)


class AgentDescriptor(BaseModel):
    """One registered agent.

    ``permitted_tools`` lists exact ``tool_name`` matches; the single entry
    ``"*"`` means the agent may invoke any tool. There is no pattern matching
    in v0.3.

    ``privilege_tier`` is an integer (higher means more privilege). It is
    compared against any tier requirement declared in
    ``AgentRegistry.tool_privilege_tiers``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    signer_key: str = Field(pattern=HEX_64)
    permitted_tools: list[str] = Field(default_factory=list)
    privilege_tier: int = Field(default=DEFAULT_PRIVILEGE_TIER, ge=0)
    behavioral_scope: BehavioralScope | None = None

    def allows_tool(self, tool_name: str) -> bool:
        if WILDCARD_TOOL in self.permitted_tools:
            return True
        return tool_name in self.permitted_tools


class AgentRegistry(BaseModel):
    """Operator-declared registry of agents and tool privilege tiers."""

    model_config = ConfigDict(extra="forbid")

    agents: list[AgentDescriptor] = Field(default_factory=list)
    tool_privilege_tiers: dict[str, int] = Field(default_factory=dict)

    def get(self, agent_id: str) -> AgentDescriptor | None:
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def required_tier_for_tool(self, tool_name: str) -> int:
        """Return the minimum tier required to invoke ``tool_name``.

        Tools not declared in ``tool_privilege_tiers`` return the default tier
        (0), so tier-escalation findings only fire for tools the operator has
        explicitly tagged with a required tier.
        """
        return self.tool_privilege_tiers.get(tool_name, DEFAULT_PRIVILEGE_TIER)


def load_registry(path: str | Path) -> AgentRegistry:
    """Parse a YAML or JSON agent registry from disk and validate it.

    The file extension drives the parser: ``.yaml`` / ``.yml`` uses
    ``yaml.safe_load``; ``.json`` uses ``json.loads``. Any other extension
    raises ``ValueError``.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"agent registry file not found: {file_path}")

    suffix = file_path.suffix.lower()
    raw = file_path.read_text(encoding="utf-8")

    data: Any
    if suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    elif suffix == ".json":
        data = json.loads(raw)
    else:
        raise ValueError(
            f"agent registry must have .yaml, .yml, or .json extension; got '{suffix}'"
        )

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(
            f"agent registry root must be a mapping, got {type(data).__name__}"
        )

    return AgentRegistry.model_validate(data)


def is_hex_64(value: str) -> bool:
    """True when ``value`` is exactly 64 hexadecimal characters.

    Used by detectors and callers that want to sanity-check Ed25519 public
    keys before comparing them against registry entries.
    """
    return bool(_HEX_64_RE.match(value))
