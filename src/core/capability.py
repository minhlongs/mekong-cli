# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Canonical Capability abstraction + CapabilityBus Protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class CapabilitySource(str, Enum):
    BUILTIN = "builtin"
    CLI = "cli"
    API = "api"
    MCP = "mcp"
    CUSTOM = "custom"


@dataclass
class Capability:
    """Canonical capability descriptor."""
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
    registered_by: Optional[str] = None
    registered_at: Optional[float] = None
    expires_at: Optional[float] = None

    def __post_init__(self) -> None:
        if self.registered_at is None:
            self.registered_at = time.time()

    def is_expired(self, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) > self.expires_at

    def execute(self, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        raise NotImplementedError(f"Capability {self.id} has no execute() implementation")


@runtime_checkable
class CapabilityBus(Protocol):
    """Canonical capability bus — wraps ToolRegistry with governance."""

    def register(self, capability: Capability) -> None: ...
    def unregister(self, capability_id: str) -> bool: ...
    def get(self, capability_id: str) -> Capability | None: ...
    def list_capabilities(self, risk_level: str | None = None, source: CapabilitySource | None = None) -> List[Capability]: ...
    def discover(self, query: str) -> List[Capability]: ...
    def execute(self, capability_id: str, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]: ...
    def check_authorization(self, capability_id: str, principal: str) -> bool: ...
    def cleanup(self) -> int: ...


class InMemoryCapabilityBus:
    """Canonical in-memory CapabilityBus implementation."""

    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
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
        return [
            c for c in self._caps.values()
            if q in c.name.lower() or q in c.description.lower() or any(q in t.lower() for t in c.tags)
        ]

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
        expired = [cid for cid, cap in self._caps.items() if cap.is_expired(now)]
        for cid in expired:
            del self._caps[cid]
        return len(expired)


__all__ = ["Capability", "CapabilitySource", "CapabilityBus", "InMemoryCapabilityBus"]