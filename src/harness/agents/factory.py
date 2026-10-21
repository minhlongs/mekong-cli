# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Agent Factory.

Loads agent definitions from YAML config and creates agent instances.
Stubs unknown/unimplemented agents via AgentMetadata; caches for idempotency.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .base import AgentBase, Result, Task
from .factory_models import (
    AgentMetadata,
    find_project_root,
    instantiate_agent_class,
)

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.environ.get(
    "MEKONG_AGENT_REGISTRY",
    "agents/registry.yaml",
)


class AgentFactory:
    """Creates agent instances from YAML config."""

    _CONFIG_PATH = _CONFIG_PATH

    def __init__(self, config_path: str = _CONFIG_PATH) -> None:
        self._config_path = config_path
        self._defs: Dict[str, Dict[str, Any]] = {}
        self._cache: Dict[str, AgentBase] = {}
        self._load(config_path)

    def _load(self, path: str) -> None:
        config_path = Path(path)
        if not config_path.is_absolute():
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
        return find_project_root()

    def load_config(self, yml_path: str) -> dict:
        """Reload config from a different YAML path and return the raw dict."""
        self._cache.clear()
        path = Path(yml_path)
        if not path.is_absolute():
            path = self._find_project_root() / path
        with open(path) as f:
            return yaml.safe_load(f) or {}

    def list_available(self) -> list:
        """Return sorted list of registered agent IDs."""
        return sorted(self._defs.keys())

    def get_definition(self, agent_id: str) -> Dict[str, Any]:
        """Return the raw defn dict for an agent ID."""
        if agent_id not in self._defs:
            raise ValueError(f"Unknown agent: {agent_id}")
        return dict(self._defs[agent_id])

    def create(self, agent_id: str, llm: Any = None, memory: Any = None) -> AgentBase:
        """Return an agent instance — concrete class or AgentMetadata stub."""
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
        """Convenience: create a synthetic AgentMetadata for testing/demo."""
        stub: Dict[str, Any] = {
            "id": agent_id,
            "name": f"Demo {agent_id}",
            "role": f"Demo {agent_id}",
            "tools": ["demo"],
            "module_path": None,
        }
        return AgentMetadata(agent_id, stub)

    @staticmethod
    def _instantiate(
        module_path: str,
        defn: Dict[str, Any],
        llm: Any,
        memory: Any,
    ) -> AgentBase:
        """Import module_path (dot-separated) and call the class constructor."""
        return instantiate_agent_class(module_path, defn, llm, memory)


_factory: Optional[AgentFactory] = None


def get_factory(config_path: str = _CONFIG_PATH) -> AgentFactory:
    """Singleton factory — safe for module-level use."""
    global _factory
    if _factory is None or _factory._config_path != config_path:
        _factory = AgentFactory(config_path)
    return _factory


__all__ = [
    "AgentFactory",
    "AgentMetadata",
    "Result",
    "Task",
    "get_factory",
    "_CONFIG_PATH",
]
