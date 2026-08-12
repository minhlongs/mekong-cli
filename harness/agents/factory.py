"""Agent factory — config-driven agent construction.

Reads agents/registry.yaml, provides create() and list_available().
No hard dependencies on optional packages. Safe stubs when library absent.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.core.agent_base import Result  # noqa: E402 (re-exported for tests)

logger = logging.getLogger(__name__)


def _load_registry() -> dict[str, dict[str, Any]]:
    """Load registry.yaml via harness.config (or stub)."""
    try:
        from harness.config import load_registry
        return load_registry()
    except ImportError:
        pass
    try:
        import yaml
    except ImportError:
        return _stub_load()

    from pathlib import Path
    yaml_path = Path(__file__).resolve().parents[1] / "agents" / "registry.yaml"
    if not yaml_path.exists():
        yaml_path = Path.cwd() / "agents" / "registry.yaml"
    if not yaml_path.exists():
        logger.warning("registry.yaml not found, returning empty registry")
        return {}
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not data or "agents" not in data:
        return {}
    return {a["id"]: a for a in data["agents"]}


def _stub_load() -> dict[str, dict[str, Any]]:
    """Minimal stub when PyYAML absent."""
    return {
        a["id"]: a for a in [
            {"id": "ceo", "name": "CEO Solo", "role": "Chief Executive Officer", "model": "sonnet"},
            {"id": "ae", "name": "AE", "role": "Account Executive", "model": "sonnet"},
            {"id": "pm", "name": "PM", "role": "Product Manager", "model": "sonnet"},
            {"id": "eng", "name": "ENG", "role": "Engineering", "model": "sonnet"},
            {"id": "ops", "name": "OPS", "role": "Operations", "model": "sonnet"},
        ]
    }


class AgentFactory:
    """Config-driven agent construction."""

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, Any]] = _load_registry()
        self._instances: dict[str, Any] = {}

    def list_available(self) -> list[str]:
        """Return list of agent id keys in the registry."""
        return list(self._registry.keys())

    def get_definition(self, agent_id: str) -> dict[str, Any] | None:
        """Return raw agent definition dict or None."""
        return self._registry.get(agent_id)

    def create(self, agent_id: str, llm: Any = None, memory: Any = None) -> Any:
        """Create an Agent instance from registry config.

        Returns AgentBase subclass instance when available,
        or AgentMetadata stub when module import is unavailable.
        """
        if agent_id not in self._registry:
            raise ValueError(f"Unknown agent: {agent_id}")

        if agent_id in self._instances:
            return self._instances[agent_id]

        defn = self._registry[agent_id]
        agent = self._try_import(agent_id, defn, llm, memory)
        if agent is None:
            agent = AgentMetadata(agent_id, defn)

        self._instances[agent_id] = agent
        return agent

    def create_demo(self, name: str = "demo") -> "AgentMetadata":
        """Return a stateless dummy agent for quick testing."""
        return AgentMetadata(name, {"id": name, "name": name, "role": "demo"})

    # --- Internal ---

    def _try_import(
        self, agent_id: str, defn: dict[str, Any], llm: Any, memory: Any
    ) -> Any | None:
        """Try to import a concrete agent from src.agents using the registry."""
        module_map: dict[str, str] = {
            "eng": "src.agents.file_agent",
            "ops": "src.agents.monitor_agent",
            "database": "src.agents.database_agent",
            "monitor": "src.agents.monitor_agent",
            "social": "src.agents.social_reply_agent",
            "review": "src.agents.review_agent",
        }
        module_path = module_map.get(agent_id)
        if not module_path:
            # ceo/ae/pm have no concrete module yet — return None (stub)
            return None
        try:
            from importlib import import_module
            mod = import_module(module_path)
            for _name in dir(mod):
                cls = getattr(mod, _name)
                if isinstance(cls, type) and hasattr(cls, "plan"):
                    return cls()
        except (ImportError, AttributeError, TypeError):
            pass
        return None


class AgentMetadata:
    """Graceful fallback: agent stub with metadata only."""

    def __init__(self, agent_id: str, defn: dict[str, Any]) -> None:
        self.id = agent_id
        self.name = defn.get("name", agent_id)
        self.role = defn.get("role", "unknown")
        self.model = defn.get("model", "sonnet")
        self.tools: list[str] = defn.get("tools", [])
        self.context_budget: int = defn.get("context_budget", 30000)
        self.definition = defn

    def plan(self, input_data: Any) -> list[Any]:
        """Stub plan — returns empty task list."""
        return []

    def execute(self, task: Any) -> Result:
        return Result(task_id=getattr(task, "id", "?"), success=True, output={"agent": self.id})

    def verify(self, result: Any) -> bool:
        return getattr(result, "success", False)

    def __repr__(self) -> str:
        return f"<AgentMetadata id={self.id} role={self.role}>"


# --- Singleton support ---

_CONFIG_PATH = os.environ.get("HARNESS_CONFIG_PATH")

_factory: AgentFactory | None = None


def get_factory(config_path: str = _CONFIG_PATH) -> AgentFactory:
    """Singleton factory — safe for module-level use."""
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory


# Public names
__all__ = [
    "AgentFactory",
    "AgentMetadata",
    "Result",
    "get_factory",
]
