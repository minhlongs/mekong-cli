# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - PluginAgent

Agent for plugin management: list, install, remove, update plugins.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from ..core.agent_base import AgentBase, Result, Task
from .plugin_agent_ops import PluginAgentOpsMixin


class PluginAgent(PluginAgentOpsMixin, AgentBase):
    """
    Agent for plugin/package management operations.

    Supports:
    - list: List installed plugins
    - install: Install new plugin
    - remove: Remove installed plugin
    - update: Update plugin to latest version
    """

    def __init__(self, cwd: str = ".", registry_path: Optional[str] = None) -> None:
        """Initialize PluginAgent."""
        super().__init__(name="PluginAgent")
        self.cwd = Path(cwd).resolve()
        self.registry_path = Path(registry_path) if registry_path else self.cwd / ".mekong" / "plugins.json"

    def plan(self, input_data: str) -> list[Task]:
        """Parse plugin command string into tasks."""
        stripped = input_data.strip()
        if not stripped:
            return [
                Task(
                    id="error",
                    description="Empty command",
                    input={"error": "Command cannot be empty"},
                )
            ]

        parts = stripped.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "list":
            return [Task(id="list_plugins", description="List installed plugins", input={})]

        elif command == "install":
            if not args:
                return [
                    Task(
                        id="error",
                        description="install requires plugin name",
                        input={"error": "Plugin name required"},
                    )
                ]
            return [
                Task(
                    id="install_plugin",
                    description=f"Install plugin: {args}",
                    input={"plugin": args},
                )
            ]

        elif command == "remove":
            if not args:
                return [
                    Task(
                        id="error",
                        description="remove requires plugin name",
                        input={"error": "Plugin name required"},
                    )
                ]
            return [
                Task(
                    id="remove_plugin",
                    description=f"Remove plugin: {args}",
                    input={"plugin": args},
                )
            ]

        elif command == "update":
            plugin = args if args else "all"
            return [
                Task(
                    id="update_plugin",
                    description=f"Update plugin: {plugin}",
                    input={"plugin": plugin},
                )
            ]

        else:
            return [
                Task(
                    id="error",
                    description=f"Unknown command: {command}",
                    input={"error": f"Unknown command: {command}"},
                )
            ]

    def execute(self, task: Task) -> Result:
        """Execute plugin management task."""
        try:
            if task.id == "list_plugins":
                return self._list_plugins(task)
            elif task.id == "install_plugin":
                return self._install_plugin(task)
            elif task.id == "remove_plugin":
                return self._remove_plugin(task)
            elif task.id == "update_plugin":
                return self._update_plugin(task)
            elif task.id == "error":
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=task.input.get("error", "Unknown error"),
                )
            else:
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=f"Unknown task: {task.id}",
                )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))


__all__ = ["PluginAgent", "subprocess"]
