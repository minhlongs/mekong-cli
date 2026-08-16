# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin system exception hierarchy.

All plugin-facing errors inherit from PluginError so callers can
catch ``except PluginError`` when they want a broad safety net.
"""

from __future__ import annotations


class PluginError(Exception):
    """Base error for the plugin subsystem."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin id cannot be resolved."""


class PluginLoadError(PluginError):
    """Raised when a plugin module fails to import or initialise."""


class ManifestError(PluginError):
    """Raised when ``.mekong-plugin.json`` is missing or invalid."""


class DuplicatePluginError(PluginError):
    """Raised when attempting to install an already-registered plugin id."""


class DependencyError(PluginError):
    """Raised when a plugin declares an unsatisfiable dependency."""


class PermissionDeniedError(PluginError):
    """Raised when a plugin attempts an action outside its declared permissions."""


class RegistryCorruptedError(PluginError):
    """Raised when the on-disk registry file can't be parsed."""
