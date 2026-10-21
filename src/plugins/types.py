# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin runtime context and re-exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.plugins.manifest import HookSpecRecord, Manifest
from src.plugins.types_identifiers import HookId, HookSpec, PluginId, Result, ResultStatus


@dataclass
class PluginContext:
    """Runtime handoff object passed into plugin ``register()``."""

    registry: Any
    commands: Any
    config: Dict[str, Any]
    _hook_cb: Optional[Callable[[PluginId, HookSpec, Callable[..., Result], int], None]] = None
    _log_factory: Optional[Callable[[str], Any]] = None
    isolation: str = "none"

    def hook(self, spec: HookSpec, handler: Callable[..., Result], priority: int = 50) -> None:
        if self._hook_cb is None:
            return
        self._hook_cb(PluginId(self.config.get("plugin_id", "unknown")), spec, handler, priority)

    def log(self, name: str) -> Any:
        if self._log_factory is not None:
            return self._log_factory(name)
        import logging
        return logging.getLogger(f"mekong.plugin.{name}")

    def register_command(self, name: str, fn: Callable[..., Any]) -> None:
        self.commands.register(name, fn)

    def resolve_provider_key(self, provider: str) -> Optional[str]:
        plugin_id = self.config.get("plugin_id", "unknown")
        try:
            from src.core.provider_adapter import resolve_provider_key as _resolve
        except ImportError:
            return None
        key, _ = _resolve(plugin_id, provider)
        return key

    def has_credential(self, provider: str) -> bool:
        return self.resolve_provider_key(provider) is not None


__all__ = [
    "PluginId",
    "HookId",
    "HookSpec",
    "ResultStatus",
    "Result",
    "HookSpecRecord",
    "Manifest",
    "PluginContext",
]
