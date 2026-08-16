# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Agent Factory.

Loads agent definitions from YAML config and creates agent instances.
Stubs unknown/unimplemented agents via AgentMetadata; caches for idempotency.
"""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .base import AgentBase, Result, Task

logger = logging.getLogger(__name__)

# Default config path (project-root relative when cwd is mekong-cli root)
_CONFIG_PATH = os.environ.get(
    "MEKONG_AGENT_REGISTRY",
    "src/harness/agents/config/registry.yaml",
)


class AgentMetadata(AgentBase):
    """Stub agent for roles that have no concrete implementation.

    Provides plan/execute surface required by AgentBase without actual behavior.
    """

    def __init__(self, agent_id: str, defn: Dict[str, Any]) -> None:
        super().__init__(name=agent_id)
        self.id = agent_id
        self.name = defn.get("name", agent_id)
        self.role = defn.get("role", agent_id)
        self.tools = defn.get("tools", [])
        self._defn = defn

    def plan(self, input_data: str) -> list:  # type: ignore[override]
        """Return a single task stub."""
        return [
            Task(
                id=f"{self.id}_plan",
                description=f"{self.role} planned: {input_data[:80]}",
                input={"raw": input_data},
            )
        ]

    def execute(self, task: Task) -> Result:  # type: ignore[override]
        """Return a stub result — no real execution."""
        return Result(
            task_id=task.id,
            success=True,
            output={
                "agent_id": self.id,
                "role": self.role,
                "status": "stub — no implementation",
                "task": task.description,
            },
            error=None,
        )


class AgentFactory:
    """Creates agent instances from YAML config.

    Usage::

        factory = AgentFactory()
        agent = factory.create("ceo")       # returns CEOAgent or AgentMetadata
        ops = factory.create("ops")         # returns MonitorAgent
    """

    def __init__(self, config_path: str = _CONFIG_PATH) -> None:
        self._config_path = config_path
        self._defs: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, AgentBase] = {}
        self._load(config_path)

    # ── Config loading ──────────────────────────────────────────────

    def _load(self, path: str) -> None:
        config_path = Path(path)
        if not config_path.is_absolute():
            # Resolve from mekong-cli project root
            config_path = self._find_project_root() / config_path

        if not config_path.exists():
            raise FileNotFoundError(f"Agent registry not found: {config_path}")

        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}

        self._defs = {a["id"]: a for a in raw.get("agents", [])}
        if not self._defs:
            raise ValueError("Empty agent registry: no agents defined in YAML")

        logger.info("Loaded %d agent defs from %s", len(self._defs), config_path)

    @staticmethod
    def _find_project_root() -> Path:
        """Walk up from cwd to find the repo root (has .git or pyproject.toml)."""
        here = Path.cwd()
        for parent in [here] + list(here.parents):
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                return parent
        return here

    def load_config(self, yml_path: str) -> dict:
        """Reload config from a different YAML path and return the raw dict.

        Clears the instance cache on reload since defs may have changed.
        """
        self._cache.clear()
        path = Path(yml_path)
        if not path.is_absolute():
            path = self._find_project_root() / path
        with open(path) as f:
            return yaml.safe_load(f) or {}

    # ── Inspection ──────────────────────────────────────────────────

    def list_available(self) -> list:
        """Return sorted list of registered agent IDs."""
        return sorted(self._defs.keys())

    def get_definition(self, agent_id: str) -> Dict[str, Any]:
        """Return the raw defn dict for an agent ID.

        Raises:
            ValueError: if agent_id not found.
        """
        if agent_id not in self._defs:
            raise ValueError(f"Unknown agent: {agent_id}")
        return dict(self._defs[agent_id])

    # ── Instance creation ───────────────────────────────────────────

    def create(self, agent_id: str, llm: Any = None, memory: Any = None) -> AgentBase:
        """Return an agent instance — concrete class or AgentMetadata stub.

        First call instantiates; subsequent calls return the cached instance
        (idempotent — llm/memory params are ignored after first create).

        Raises:
            ValueError: if agent_id not in registry.
        """
        if agent_id in self._cache:
            return self._cache[agent_id]

        if agent_id not in self._defs:
            raise ValueError(f"Unknown agent: {agent_id}")

        defn = self._defs[agent_id]
        module_path = defn.get("module_path")

        instance: AgentBase
        if module_path:
            instance = self._instantiate(module_path, defn, llm, memory)
        else:
            instance = AgentMetadata(agent_id, defn)

        self._cache[agent_id] = instance
        logger.debug("Created agent %s -> %s", agent_id, type(instance).__name__)
        return instance

    def create_demo(self, agent_id: str) -> AgentMetadata:
        """Convenience: create a synthetic AgentMetadata for testing/demo.

        Does NOT require the ID to be in the registry.
        """
        stub: Dict[str, Any] = {
            "id": agent_id,
            "name": f"Demo {agent_id}",
            "role": f"Demo {agent_id}",
            "tools": ["demo"],
            "module_path": None,
        }
        return AgentMetadata(agent_id, stub)

    # ── Dynamic import ──────────────────────────────────────────────

    @staticmethod
    def _instantiate(
        module_path: str,
        defn: Dict[str, Any],
        llm: Any,
        memory: Any,
    ) -> AgentBase:
        """Import module_path (dot-separated) and call the class constructor."""
        try:
            module = importlib.import_module(module_path.rsplit(".", 1)[0])
            class_name = module_path.rsplit(".", 1)[1]
            cls = getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                f"Failed to load agent '{defn['id']}' from '{module_path}': {exc}"
            ) from exc

        # Tool: seed agents accept (name, role_prompt, llm, memory)
        # Tool: harness agents accept (name,)
        # Try LLM-init first, fall back to plain init
        try:
            return cls(
                name=defn.get("name", defn["id"]),
                role_prompt=defn.get("role_prompt", ""),
                llm=llm,
                memory=memory,
            )
        except TypeError:
            return cls(name=defn.get("name", defn["id"]))


# ── Module-level convenience API ────────────────────────────────────

_factory: Optional[AgentFactory] = None


def get_factory(config_path: str = _CONFIG_PATH) -> AgentFactory:
    """Singleton factory — safe for module-level use."""
    global _factory
    if _factory is None or _factory._config_path != config_path:
        _factory = AgentFactory(config_path)
    return _factory


# Public names
__all__ = [
    "AgentFactory",
    "AgentMetadata",
    "Result",
    "Task",
    "get_factory",
    "_CONFIG_PATH",
]
