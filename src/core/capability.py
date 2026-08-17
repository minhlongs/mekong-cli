# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical Capability abstraction + CapabilityBus Protocol.

Provides the governance layer between ToolRegistry and the Policy/Autonomy Engine.
Every tool (local, shell, MCP, Cloudflare, external service) is represented as a
Capability instance with risk_level, cost estimate, and authorization requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ─── Capability Source ──────────────────────────────────────────────────

class CapabilitySource(str, Enum):
    """Where a capability originates."""
    BUILTIN = "builtin"
    CLI = "cli"
    API = "api"
    MCP = "mcp"
    CUSTOM = "custom"


# ─── Capability Dataclass ───────────────────────────────────────────────

@dataclass
class Capability:
    """Canonical capability descriptor.

    Every tool in the system (local tool, shell command, MCP tool, etc.)
    is represented as a Capability instance.

    Fields:
        id: Unique identifier (e.g., "git:status", "shell:run", "mcp:search")
        name: Human-readable name
        description: What the capability does
        input_schema: JSON Schema dict for input validation
        output_schema: JSON Schema dict for output (optional)
        risk_level: LOW | MEDIUM | HIGH | CRITICAL
        source: Where this capability originates
        cost: Estimated cost (MCU or arbitrary units)
        authorization: Required permission (None = public)
        tags: Categorization tags
        metadata: Extra provider-specific data
    """
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "LOW"
    source: CapabilitySource = CapabilitySource.BUILTIN
    cost: float = 0.0
    authorization: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def execute(self, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Execute this capability with given parameters.

        Subclasses or adapters override this to provide real execution.
        Default raises NotImplementedError — adapter must implement.
        """
        raise NotImplementedError(f"Capability {self.id} has no execute() implementation")


# ─── CapabilityBus Protocol ─────────────────────────────────────────────

@runtime_checkable
class CapabilityBus(Protocol):
    """Canonical capability bus — wraps ToolRegistry with governance.

    Provides:
    - Capability discovery (list, filter by risk/source/tag)
    - Capability execution with policy checks
    - MCP tool wrapping as Capability instances
    """

    def register(self, capability: Capability) -> None:
        """Register a capability."""
        ...

    def unregister(self, capability_id: str) -> bool:
        """Remove a capability by ID. Returns True if found."""
        ...

    def get(self, capability_id: str) -> Capability | None:
        """Get a capability by ID."""
        ...

    def list_capabilities(self, risk_level: str | None = None, source: CapabilitySource | None = None) -> List[Capability]:
        """List capabilities, optionally filtered."""
        ...

    def discover(self, query: str) -> List[Capability]:
        """Discover capabilities by text query (fuzzy match on name/description/tags)."""
        ...

    def execute(self, capability_id: str, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Execute a capability by ID, with policy checks."""
        ...

    def check_authorization(self, capability_id: str, principal: str) -> bool:
        """Check if principal is authorized to use this capability."""
        ...


__all__ = [
    "Capability",
    "CapabilitySource",
    "CapabilityBus",
]