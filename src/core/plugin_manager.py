"""Mekong CLI - Plugin Manager.

Coordinates plugin lifecycle: load, validate, activate, deactivate.
Bridges PluginLoader (discovery) and PluginRegistry (metadata).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .plugin_loader import PluginLoader, DEFAULT_PLUGIN_DIR
from .plugin_registry import PluginRegistry, PluginManifest, PluginStatus

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Lightweight plugin info descriptor.

    Used by tests and UI layers for quick plugin summaries
    without loading the full PluginManifest.
    """

    name: str
    version: str = "0.0.0"
    plugin_type: str = "agent"
    status: str = "available"
    description: str = ""
    author: str = ""
    source: str = "local"
    entry_point: str = ""
    error_message: str = ""

    @classmethod
    def from_manifest(cls, manifest: PluginManifest) -> "PluginInfo":
        """Create PluginInfo from a PluginManifest."""
        return cls(
            name=manifest.name,
            version=manifest.version,
            plugin_type=manifest.plugin_type.value,
            status=manifest.status.value,
            description=manifest.description,
            author=manifest.author,
            source=manifest.source,
            entry_point=manifest.entry_point,
            error_message=manifest.error_message,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "name": self.name,
            "version": self.version,
            "plugin_type": self.plugin_type,
            "status": self.status,
            "description": self.description,
            "author": self.author,
            "source": self.source,
            "entry_point": self.entry_point,
            "error_message": self.error_message,
        }


class PluginManager:
    """Coordinates plugin lifecycle operations.

    Wraps PluginLoader and PluginRegistry to provide a unified
    interface for plugin management.
    """

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        """Initialize with an optional registry (uses default if None)."""
        self._registry = registry or PluginRegistry()
        self._loader = PluginLoader()

    @property
    def registry(self) -> PluginRegistry:
        """Access the underlying plugin registry."""
        return self._registry

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover(self) -> list[PluginInfo]:
        """Discover all available plugins across sources.

        Returns list of PluginInfo for discovered plugins.
        """
        manifests = self._registry.discover()
        return [PluginInfo.from_manifest(m) for m in manifests]

    def discover_local(self, directory: str | None = None) -> list[PluginInfo]:
        """Discover plugins from a local directory."""
        target = Path(directory) if directory else DEFAULT_PLUGIN_DIR
        if not target.exists():
            return []
        manifests = self._registry._discover_local()
        return [PluginInfo.from_manifest(m) for m in manifests]

    # ── Install ───────────────────────────────────────────────────────────

    def install(self, package_name: str) -> PluginInfo:
        """Install a plugin from PyPI or local path.

        Returns PluginInfo of the installed plugin.
        """
        manifest = self._registry.install(package_name)
        return PluginInfo.from_manifest(manifest)

    def install_local(self, file_path: str) -> PluginInfo:
        """Install a local .py plugin file."""
        from pathlib import Path
        manifest = self._registry.install_local(Path(file_path))
        return PluginInfo.from_manifest(manifest)

    # ── Validation ────────────────────────────────────────────────────────

    def validate(self, plugin_name: str) -> tuple[bool, str]:
        """Validate a plugin's integrity and loadability.

        Returns (is_valid, message).
        """
        return self._registry.validate(plugin_name)

    # ── Activation ────────────────────────────────────────────────────────

    def activate(self, plugin_name: str) -> bool:
        """Activate a plugin — load it into runtime.

        Returns True if activation succeeded.
        """
        return self._registry.activate(plugin_name, self._loader)

    def deactivate(self, plugin_name: str) -> bool:
        """Deactivate a plugin (mark as disabled)."""
        return self._registry.deactivate(plugin_name)

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self, plugin_name: str) -> PluginInfo | None:
        """Load and activate a plugin by name.

        Returns PluginInfo on success, None on failure.
        """
        manifest = self._registry.get(plugin_name)
        if manifest is None:
            logger.error("Plugin '%s' not found in registry", plugin_name)
            return None

        is_valid, msg = self._registry.validate(plugin_name)
        if not is_valid:
            logger.error("Plugin '%s' validation failed: %s", plugin_name, msg)
            manifest.status = PluginStatus.ERROR
            manifest.error_message = msg
            self._registry._save_index()
            return PluginInfo.from_manifest(manifest)

        if self._registry.activate(plugin_name, self._loader):
            manifest.status = PluginStatus.ACTIVE
            manifest.error_message = ""
            self._registry._save_index()

        return PluginInfo.from_manifest(manifest)

    def unload(self, plugin_name: str) -> bool:
        """Unload and deactivate a plugin."""
        return self._registry.deactivate(plugin_name)

    def uninstall(self, plugin_name: str) -> bool:
        """Uninstall a plugin completely (remove files + registry entry)."""
        return self._registry.uninstall(plugin_name)

    # ── Query ─────────────────────────────────────────────────────────────

    def list_plugins(self, plugin_type: str | None = None) -> list[PluginInfo]:
        """List all registered plugins, optionally filtered by type."""
        from .plugin_registry import PluginType
        ptype = PluginType(plugin_type) if plugin_type else None
        manifests = self._registry.list_plugins(plugin_type=ptype)
        return [PluginInfo.from_manifest(m) for m in manifests]

    def get_info(self, plugin_name: str) -> PluginInfo | None:
        """Get PluginInfo for a specific plugin."""
        manifest = self._registry.get(plugin_name)
        if manifest is None:
            return None
        return PluginInfo.from_manifest(manifest)

    def __repr__(self) -> str:
        return f"<PluginManager plugins={self._registry.count}>"


# ─── Public API ────────────────────────────────────────────────────────────────

__all__ = [
    "PluginManager",
    "PluginInfo",
]
