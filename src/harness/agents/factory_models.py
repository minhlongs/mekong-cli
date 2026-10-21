# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stub agent metadata and dynamic instantiation helpers for AgentFactory."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict

from .base import AgentBase, Result, Task


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


def find_project_root() -> Path:
    """Walk up from cwd to find the repo root (has .git or pyproject.toml)."""
    here = Path.cwd()
    for parent in [here] + list(here.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return here


def instantiate_agent_class(
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

    try:
        return cls(
            name=defn.get("name", defn["id"]),
            role_prompt=defn.get("role_prompt", ""),
            llm=llm,
            memory=memory,
        )
    except TypeError:
        return cls(name=defn.get("name", defn["id"]))
