# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hardened plugin manifest types for the autonomous OS plugin system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PluginCapability(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    DEPLOYMENT_TARGET = "deployment_target"
    MEMORY_BACKEND = "memory_backend"


@dataclass(frozen=True)
class PluginManifestV2:
    name: str
    version: str
    capabilities: tuple[PluginCapability, ...]
    entry_point: str
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    checksum: str = ""
    isolated: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
