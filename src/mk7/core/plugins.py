"""Mekong CLI 7 — Plugin hooks (port of opencode plugin events).

Two events: tool.execute.before and tool.execute.after. Plugins are
callables registered per event; they may block (before) or annotate (after).
Config-driven plugins live in ~/.mekong/plugins/*.py exporting
`register(hooks)`.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .config import CONFIG_DIR

PLUGINS_DIR = CONFIG_DIR / "plugins"

BeforeHook = Callable[[str, dict[str, Any]], dict[str, Any] | None]
AfterHook = Callable[[str, dict[str, Any], dict[str, Any]], None]


class PluginBlocked(RuntimeError):
    """Raised by a before-hook to block a tool execution."""

    def __init__(self, reason: str = "blocked by plugin"):
        super().__init__(reason)
        self.reason = reason


@dataclass
class HookRegistry:
    before: list[tuple[str, BeforeHook]] = field(default_factory=list)
    after: list[tuple[str, AfterHook]] = field(default_factory=list)

    def on_before(self, name: str, hook: BeforeHook) -> None:
        self.before.append((name, hook))

    def on_after(self, name: str, hook: AfterHook) -> None:
        self.after.append((name, hook))

    def run_before(self, tool: str, args: dict[str, Any]) -> dict[str, Any] | None:
        """Run all before hooks; first PluginBlocked aborts (re-raised)."""
        modified = args
        for name, hook in self.before:
            result = hook(tool, modified)
            if isinstance(result, dict):
                modified = result
        return modified

    def run_after(self, tool: str, args: dict[str, Any], result: dict[str, Any]) -> None:
        for name, hook in self.after:
            try:
                hook(tool, args, result)
            except Exception:
                continue  # after-hooks never break execution


class PluginLoader:
    """Load plugin modules from ~/.mekong/plugins/*.py.

    Each module exports `register(hooks: HookRegistry) -> None`.
    """

    def __init__(self, directory: Path | None = None):
        self.directory = directory or PLUGINS_DIR

    def load_all(self) -> list[str]:
        if not self.directory.is_dir():
            return []
        loaded: list[str] = []
        for py in sorted(self.directory.glob("*.py")):
            if py.name.startswith("_"):
                continue
            try:
                name = f"mekong_plugin_{py.stem}"
                spec = importlib.util.spec_from_file_location(name, py)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[name] = mod
                    spec.loader.exec_module(mod)
                loaded.append(py.stem)
            except Exception as e:
                print(f"[plugins] failed to load {py.name}: {e}")
        return loaded


def register_hook(registry: HookRegistry, plugin_path: Path | None = None) -> HookRegistry:
    """Convenience: load plugins from the default dir and return the registry."""
    loader = PluginLoader(plugin_path.parent if plugin_path else None)
    loader.load_all()
    return registry
