# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""mekong-cli plugin ecosystem — public re-exports.

Typical consumer entry points:

- ``from mekong.plugins import plugin, hook, command`` — plugin author
  decorators.
- ``from mekong.plugins import PluginRegistry, PluginLoader, PluginContext``
  — runtime helpers.
- ``from mekong.plugins.types import Manifest, PluginId, HookSpec, Result``
  — typed primitives.

Object-mode loading::

    loader = PluginLoader(registry)
    record = loader.load_object("com.example.x", manifest_dict, source_code)
"""
from __future__ import annotations

from . import api, exceptions, loader, registry, types  # noqa: F401  (package)
from .api import command, hook, plugin  # noqa: F401
from .exceptions import (  # noqa: F401
    DependencyError,
    ManifestError,
    PermissionDeniedError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    RegistryCorruptedError,
)
from .loader import PluginLoader  # noqa: F401
from .registry import PluginRegistry  # noqa: F401
from .types import (  # noqa: F401
    HookSpec,
    HookSpecRecord,
    Manifest,
    PluginContext,
    PluginId,
    Result,
    ResultStatus,
)

__all__ = [
    "plugin",
    "hook",
    "command",
    "PluginRegistry",
    "PluginLoader",
    "PluginContext",
    "Manifest",
    "HookSpec",
    "HookSpecRecord",
    "PluginId",
    "Result",
    "ResultStatus",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "ManifestError",
    "DuplicatePluginError",
    "DependencyError",
    "PermissionDeniedError",
    "RegistryCorruptedError",
]
