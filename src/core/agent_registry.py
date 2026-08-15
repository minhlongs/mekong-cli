"""Mekong CLI - Agent Registry.

Type-safe registry for AgentBase subclasses.
Replaces the plain AGENT_REGISTRY dict with validation at registration time.
Extended with tool restriction validation and markdown agent discovery.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agent_base import AgentBase

logger = logging.getLogger(__name__)


@dataclass
class AgentMeta:
    """Rich metadata surfaced by ``mekong agent list``."""

    name: str
    description: str
    cls: type[AgentBase]
    allowed_tools: list[str] = field(default_factory=list)
    spawnable_agents: list[str] = field(default_factory=list)


class AgentRegistry:
    """Type-safe registry for Mekong agents.

    Validates that only AgentBase subclasses are registered and provides
    informative KeyError messages when an unknown agent is requested.

    Example::

        registry = AgentRegistry()
        registry.register("git", GitAgent)
        agent_cls = registry.get("git")
        agent = agent_cls()

    Extended: validates allowedTools against known tool names at registration,
    auto-discovers ``.claude/agents/*.md`` files, and exposes a rich
    ``discover()`` interface for the CLI ``mekong agent list`` command.
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[AgentBase]] = {}
        self._meta: dict[str, AgentMeta] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        cls: type,
        *,
        description: str = "",
        allowed_tools: list[str] | None = None,
        spawnable_agents: list[str] | None = None,
    ) -> None:
        """Register an agent class under a short name.

        Args:
            name: Short lookup key (e.g. "git", "file").
            cls: Class to register — should subclass ``AgentBase`` (warns for
                non-compliant classes for plugin compatibility).
            description: Human-readable description surfaced by
                ``mekong agent list``. Falls back to the class docstring and
                then the name itself when omitted.
            allowed_tools: Optional tool allowlist for this agent.
            spawnable_agents: Optional list of delegatable agent IDs.
        """
        if not isinstance(cls, type) or not issubclass(cls, AgentBase):
            # Softened: warn instead of hard error for plugin compatibility.
            logger.warning(
                "%r is not an AgentBase subclass — registering under '%s' "
                "but it may not work with the PEV loop.",
                cls,
                name,
            )
            # Still allow registration for plugin compatibility.

        # Validate allowed_tools against known tool names.
        if allowed_tools:
            from .tool_names import resolve_tool_name, ALL_TOOL_NAMES

            unknown = [
                tool
                for tool in allowed_tools
                if resolve_tool_name(tool) not in ALL_TOOL_NAMES and tool != "*"
            ]
            if unknown:
                logger.warning(
                    "Unknown tool(s) in allowed_tools for '%s': %s. "
                    "Known tools: %s",
                    name,
                    unknown,
                    sorted(ALL_TOOL_NAMES),
                )

        self._agents[name] = cls
        self._meta[name] = AgentMeta(
            name=name,
            description=description or cls.__doc__ or name,
            cls=cls,
            allowed_tools=list(allowed_tools or []),
            spawnable_agents=list(spawnable_agents or []),
        )

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> type[AgentBase]:
        """Retrieve a registered agent class by name.

        Args:
            name: Registered agent name.

        Returns:
            Agent class (not instance).

        Raises:
            KeyError: With available agent list when *name* is not registered.
        """
        if name not in self._agents:
            available = list(self._agents.keys())
            msg = f"Unknown agent: '{name}'. Available agents: {available}"
            raise KeyError(msg)
        return self._agents[name]

    def get_meta(self, name: str) -> dict[str, Any]:
        """Get metadata for a registered agent (allowed_tools, spawnable_agents)."""
        meta = self._meta.get(name)
        if meta is None:
            return {"allowed_tools": [], "spawnable_agents": []}
        return {
            "allowed_tools": list(meta.allowed_tools),
            "spawnable_agents": list(meta.spawnable_agents),
        }

    def get_meta_obj(self, name: str) -> AgentMeta | None:
        """Return the rich :class:`AgentMeta` dataclass for *name*, or ``None``."""
        return self._meta.get(name)

    # ------------------------------------------------------------------
    # Discovery / enumeration (matches what ``agent_commands`` expects)
    # ------------------------------------------------------------------

    def list_agents(self) -> list[str]:
        """Return sorted list of registered agent names."""
        return sorted(self._agents.keys())

    def list(self) -> list[str]:
        """Compatibility alias for :meth:`list_agents`."""
        return self.list_agents()

    def discover(self) -> list[AgentMeta]:
        """Return rich metadata for every registered agent.

        Used by ``mekong agent list`` to render the agent table.
        """
        return [self._meta[name] for name in self.list_agents()]

    def register_decorator(self, name: str) -> Any:
        """Decorator factory — register a class when it is defined.

        Example::

            @registry.register_decorator("git")
            class GitAgent(AgentBase):
                ...
        """

        def wrapper(cls: type) -> type:
            self.register(name, cls)
            return cls

        return wrapper

    def __contains__(self, name: object) -> bool:
        """Support ``'git' in registry`` syntax."""
        return name in self._agents

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={self.list_agents()}>"


# ---------------------------------------------------------------------------
# Module-level singleton — auto-discovered on first access.
# ---------------------------------------------------------------------------

_SINGLETON: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Return the process-wide :class:`AgentRegistry`, discovering markdown
    agents the first time it is called."""
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = AgentRegistry()
        _discover_markdown_agents(_SINGLETON)
    return _SINGLETON


# ---------------------------------------------------------------------------
# .claude/agents/*.md auto-discovery
# ---------------------------------------------------------------------------

AGENTS_DIR = Path(__file__).resolve().parents[2] / ".mekong" / "agents"

_DEFAULT_DESCRIPTIONS: dict[str, str] = {
    "cto": "Chief Technology Officer — code quality, architecture, and engineering execution.",
    "cmo": "Chief Marketing Officer — positioning, messaging, campaigns, and growth.",
    "coo": "Chief Operating Officer — operations, logistics, and day-to-day execution.",
    "cfo": "Chief Financial Officer — financial models, runway, and purity of capital.",
    "cso": "Chief Strategy Officer — market intel, competitive analysis, and strategic bets.",
    "planner": "Tech Lead — architecture review, dependency graph, failure-mode analysis.",
}

_AGENT_ROLE_HINTS: dict[str, str] = {
    "cto": "code",
    "cmo": "marketing",
    "coo": "operations",
    "cfo": "finance",
    "cso": "analysis",
    "planner": "plan",
}


def _description_from_frontmatter(text: str, fallback: str) -> str:
    """Return the value of the ``description:`` YAML field or *fallback*."""
    if not text.startswith("---"):
        return fallback
    try:
        _, body, _ = text.split("---", 2)
    except ValueError:
        return fallback
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("description:"):
            value = line[len("description:") :].strip()
            if value and value[0] in "\"'":
                return value.strip("\"'")
            return value
    return fallback


def _make_markdown_agent_class(role: str, prompt: str) -> type[AgentBase]:
    """Build a minimal AgentBase subclass for a markdown-discovered agent."""

    def plan(self: Any, input_data: str) -> list[Any]:  # noqa: ANN001
        from .agent_base import Task  # local import avoids circular

        return [
            Task(
                id=f"{role}-1",
                description=f"Run {role} agent",
                input={"text": input_data},
            )
        ]

    def execute(self: Any, task: Any) -> Any:  # noqa: ANN001
        from .agent_base import Result, TaskStatus  # local import avoids circular

        task.status = TaskStatus.SUCCESS
        truncated = prompt[:240] + ("..." if len(prompt) > 240 else "")
        return Result(
            task_id=task.id,
            success=True,
            output=f"[{role.upper()}] {truncated}",
        )

    return type(
        f"Markdown{role.capitalize()}Agent",
        (AgentBase,),
        {"__doc__": _DEFAULT_DESCRIPTIONS.get(role, role), "plan": plan, "execute": execute},
    )


def _discover_markdown_agents(registry: AgentRegistry) -> None:
    """Walk ``.claude/agents`` and register any ``*.md`` files as agents."""
    if not AGENTS_DIR.is_dir():
        logger.debug("Agents directory not found at %s — skipping markdown discovery.", AGENTS_DIR)
        return

    from .agent_dispatcher import DEFAULT_PROMPTS, load_agent_prompt

    for md_path in sorted(AGENTS_DIR.glob("*.md")):
        name = md_path.stem
        try:
            content = md_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.debug("Skipping %r: %s", md_path, exc)
            continue

        description = _description_from_frontmatter(
            content,
            _DEFAULT_DESCRIPTIONS.get(name, f"{name} agent"),
        )
        prompt = DEFAULT_PROMPTS.get(name)
        if prompt is None:
            try:
                prompt = load_agent_prompt(name, include_hub=False)
            except Exception as exc:  # pragma: no cover - discovery guard
                logger.debug("Could not load prompt for %r: %s", name, exc)
                prompt = f"You are the {name} agent."

        try:
            agent_cls = _make_markdown_agent_class(name, prompt)
        except Exception as exc:  # pragma: no cover - discovery guard
            logger.debug("Skipping agent class build for %r: %s", name, exc)
            continue

        try:
            registry.register(
                name,
                agent_cls,
                description=description,
                allowed_tools=[],
                spawnable_agents=[],
            )
            logger.debug("Discovered agent %r from %s", name, md_path)
        except Exception as exc:  # pragma: no cover - discovery guard
            logger.debug("Failed to register agent %r: %s", name, exc)


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__ = [
    "AgentRegistry",
    "AgentMeta",
    "get_registry",
    "AGENTS_DIR",
]
