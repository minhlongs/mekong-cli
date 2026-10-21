# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PluginAgent operations for registry I/O and plugin install/remove/update/list."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.agent_base import Result, Task


def _plugin_mod() -> Any:
    import src.agents.plugin_agent as _mod
    return _mod


class PluginAgentOpsMixin:
    """Mixin providing plugin registry I/O and management operations."""

    cwd: Path
    registry_path: Path

    def _ensure_registry_dir(self) -> None:
        """Ensure registry directory exists."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_registry(self) -> dict[str, Any]:
        """Read plugins registry from JSON file."""
        if not self.registry_path.exists():
            return {"plugins": {}}
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_registry(self, registry: dict[str, Any]) -> None:
        """Write plugins registry to JSON file."""
        self._ensure_registry_dir()
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)

    def _list_plugins(self, task: Task) -> Result:
        """List all installed plugins."""
        registry = self._read_registry()
        plugins = registry.get("plugins", {})

        if not plugins:
            return Result(task_id=task.id, success=True, output="No plugins installed", error=None)

        output_lines = ["Installed plugins:"]
        for name, info in plugins.items():
            version = info.get("version", "unknown")
            output_lines.append(f"  - {name}@{version}")

        return Result(task_id=task.id, success=True, output="\n".join(output_lines), error=None)

    def _install_plugin(self, task: Task) -> Result:
        """Install a new plugin."""
        plugin = task.input.get("plugin", "")
        if not plugin:
            return Result(task_id=task.id, success=False, output=None, error="Plugin name required")

        registry = self._read_registry()
        plugins = registry.get("plugins", {})

        if plugin in plugins:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Plugin '{plugin}' is already installed",
            )

        plugins[plugin] = {"version": "1.0.0", "installed_at": str(Path.cwd())}
        registry["plugins"] = plugins
        self._write_registry(registry)

        return Result(
            task_id=task.id,
            success=True,
            output=f"Successfully installed plugin: {plugin}@1.0.0",
            error=None,
        )

    def _remove_plugin(self, task: Task) -> Result:
        """Remove an installed plugin."""
        plugin = task.input.get("plugin", "")
        if not plugin:
            return Result(task_id=task.id, success=False, output=None, error="Plugin name required")

        registry = self._read_registry()
        plugins = registry.get("plugins", {})

        if plugin not in plugins:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Plugin '{plugin}' is not installed",
            )

        del plugins[plugin]
        registry["plugins"] = plugins
        self._write_registry(registry)

        return Result(
            task_id=task.id,
            success=True,
            output=f"Successfully removed plugin: {plugin}",
            error=None,
        )

    def _update_plugin(self, task: Task) -> Result:
        """Update plugin(s) to latest version."""
        plugin = task.input.get("plugin", "all")

        registry = self._read_registry()
        plugins = registry.get("plugins", {})

        if not plugins:
            return Result(task_id=task.id, success=False, output=None, error="No plugins installed")

        if plugin != "all" and plugin not in plugins:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Plugin '{plugin}' is not installed",
            )

        updated = []
        target_plugins = [plugin] if plugin != "all" else list(plugins.keys())

        for name in target_plugins:
            if name in plugins:
                old_version = plugins[name].get("version", "unknown")
                plugins[name]["version"] = "1.0.0"
                updated.append(f"{name}: {old_version} → 1.0.0")

        registry["plugins"] = plugins
        self._write_registry(registry)

        output = "Updated plugins:\n" + "\n".join(f"  - {u}" for u in updated)
        return Result(task_id=task.id, success=True, output=output, error=None)

    def _run_subprocess(self, cmd: list[str], task: Task) -> Result:
        """Run external subprocess (for real plugin installations)."""
        sub = _plugin_mod().subprocess
        try:
            result = sub.run(
                cmd,
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout.strip() or result.stderr.strip()
            return Result(
                task_id=task.id,
                success=result.returncode == 0,
                output=output,
                error=result.stderr.strip() if result.returncode != 0 else None,
            )
        except sub.TimeoutExpired:
            return Result(task_id=task.id, success=False, output=None, error="Command timed out")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))
