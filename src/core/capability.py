# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical Capability abstraction + CapabilityBus Protocol.

Provides the governance layer between ToolRegistry and the Policy/Autonomy Engine.
Every tool (local, shell, MCP, Cloudflare, external service) is represented as a
Capability instance with risk_level, cost estimate, and authorization requirements.
"""

from __future__ import annotations

import time
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
    # AUTONOMY_GAPS #9 — ownership fields
    registered_by: Optional[str] = None
    registered_at: Optional[float] = None
    expires_at: Optional[float] = None

    def __post_init__(self) -> None:
        """Default registered_at to now when not supplied."""
        if self.registered_at is None:
            self.registered_at = time.time()

    def is_expired(self, now: float | None = None) -> bool:
        """True when the capability has a registered expiration in the past."""
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) > self.expires_at

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

    def cleanup(self) -> int:
        """Remove expired capabilities. Returns count removed."""
        ...


__all__ = [
    "Capability",
    "CapabilitySource",
    "CapabilityBus",
    "InMemoryCapabilityBus",
]


class InMemoryCapabilityBus:
    """Canonical in-memory CapabilityBus implementation.

    Tracks who registered each capability and when, and can evict stale
    registrations (AUTONOMY_GAPS #9). The Protocol exists so adapters can
    depend on the interface; this class is the default implementation.
    """

    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register a capability, stamping ownership if not already set."""
        if capability.registered_by is None:
            capability.registered_by = "default"
        if capability.registered_at is None:
            capability.registered_at = time.time()
        self._caps[capability.id] = capability

    def unregister(self, capability_id: str) -> bool:
        if capability_id in self._caps:
            del self._caps[capability_id]
            return True
        return False

    def get(self, capability_id: str) -> Capability | None:
        return self._caps.get(capability_id)

    def list_capabilities(self, risk_level: str | None = None, source: CapabilitySource | None = None) -> List[Capability]:
        caps = list(self._caps.values())
        if risk_level:
            caps = [c for c in caps if c.risk_level == risk_level]
        if source:
            caps = [c for c in caps if c.source == source]
        return caps

    def discover(self, query: str) -> List[Capability]:
        q = query.lower()
        return [c for c in self._caps.values()
                if q in c.name.lower() or q in c.description.lower()
                or any(q in t.lower() for t in c.tags)]

    def execute(self, capability_id: str, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        cap = self._caps.get(capability_id)
        if cap is None:
            return {"error": f"Capability {capability_id} not found"}
        if cap.is_expired():
            return {"error": f"Capability {capability_id} expired"}
        return cap.execute(params, context)

    def check_authorization(self, capability_id: str, principal: str) -> bool:
        cap = self._caps.get(capability_id)
        if cap is None or cap.authorization is None:
            return True
        return principal == cap.authorization

    def cleanup(self, now: float | None = None) -> int:
        """Remove expired capabilities. Returns count removed."""
        expired = [cid for cid, cap in self._caps.items() if cap.is_expired(now)]
        for cid in expired:
            del self._caps[cid]
        return len(expired)