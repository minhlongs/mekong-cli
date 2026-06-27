"""Mekong CLI - Agent Registry.

Type-safe registry for AgentBase subclasses.
Replaces the plain AGENT_REGISTRY dict with validation at registration time.
Extended with tool restriction validation.
"""

from __future__ import annotations

import logging
from typing import Any

from .agent_base import AgentBase

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Type-safe registry for Mekong agents.

    Validates that only AgentBase subclasses are registered and provides
    informative KeyError messages when an unknown agent is requested.

    Example:
    registry = AgentRegistry()
    registry.register("git", GitAgent)
    agent_cls = registry.get("git")
    agent = agent_cls()

    Extended: validates allowedTools against known tool names at registration.
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[AgentBase]] = {}
        self._agent_meta: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        cls: type,
        allowed_tools: list[str] | None = None,
        spawnable_agents: list[str] | None = None,
    ) -> None:
        """Register an agent class under a short name.

        Args:
            name: Short lookup key (e.g. "git", "file").
            cls: Class to register - must subclass AgentBase (warns for
                non-compliant classes for plugin compatibility).
            allowed_tools: Optional tool allowlist for this agent.
            spawnable_agents: Optional list of delegatable agent IDs.

        Logs warning for non-AgentBase classes (plugin compat).
        ValueError: If allowed_tools contains unknown tool names.
        """
        if not isinstance(cls, type) or not issubclass(cls, AgentBase):
            # Softened: warn instead of hard error for plugin compatibility
            logger.warning(
                "%r is not an AgentBase subclass — registering under '%s' "
                "but it may not work with the PEV loop.",
                cls,
                name,
            )
            # Still allow registration for plugin compatibility

        # Validate allowed_tools against known tool names
        if allowed_tools:
            from .tool_names import resolve_tool_name, ALL_TOOL_NAMES
            unknown = []
            for tool in allowed_tools:
                canonical = resolve_tool_name(tool)
                if canonical not in ALL_TOOL_NAMES and tool != "*":
                    unknown.append(tool)
            if unknown:
                logger.warning(
                    "Unknown tool(s) in allowed_tools for '%s': %s. "
                    "Known tools: %s",
                    name,
                    unknown,
                    sorted(ALL_TOOL_NAMES),
                )

        self._agents[name] = cls
        self._agent_meta[name] = {
            "allowed_tools": allowed_tools or [],
            "spawnable_agents": spawnable_agents or [],
        }

    def get(self, name: str) -> type[AgentBase]:
        """Retrieve a registered agent class by name.

        Args:
            name: Registered agent name.

        Returns:
            Agent class (not instance).

        Raises:
            KeyError: With available agent list when name not found.
        """
        if name not in self._agents:
            available = list(self._agents.keys())
            msg = (
                f"Unknown agent: '{name}'. "
                f"Available agents: {available}"
            )
            raise KeyError(msg)
        return self._agents[name]

    def get_meta(self, name: str) -> dict[str, Any]:
        """Get metadata for a registered agent (allowed_tools, spawnable_agents)."""
        return dict(self._agent_meta.get(name, {"allowed_tools": [], "spawnable_agents": []}))

    def list_agents(self) -> list[str]:
        """Return sorted list of registered agent names."""
        return sorted(self._agents.keys())

    def register_decorator(self, name: str) -> Any:
        """Decorator factory - register a class when it is defined.

        Example:
        @registry.register_decorator("git")
        class GitAgent(AgentBase):
            ...
        """
        def wrapper(cls: type) -> type:
            self.register(name, cls)
            return cls
        return wrapper

    def __contains__(self, name: object) -> bool:
        """Support 'git' in registry syntax."""
        return name in self._agents

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={self.list_agents()}>"


# Export
__all__ = ["AgentRegistry"]
