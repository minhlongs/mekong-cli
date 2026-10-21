# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin manifest dataclass and hydration."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.plugins.credential_schema import CredentialRequirement, PluginCredentials
from src.plugins.types_identifiers import HookSpec, Result


@dataclass
class HookSpecRecord:
    """Declaration of a single hook a plugin wants to subscribe to."""

    spec: HookSpec
    handler: Callable[..., Result]
    priority: int = 50
    once: bool = False

    def sort_key(self) -> tuple[int, str]:
        return (self.priority, self.handler.__name__)


@dataclass
class Manifest:
    """In-memory representation of a plugin descriptor."""

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    engine: str = "^6.0.0"
    permissions: List[str] = field(default_factory=list)
    mcu_cost: int = 1
    dependencies: List[str] = field(default_factory=list)
    entry_point: Optional[str] = None
    isolation: str = "none"
    hooks: List[HookSpecRecord] = field(default_factory=list)
    installed_at: float = field(default_factory=time.time)
    enabled: bool = True
    checksum: str = ""
    credentials: Optional[PluginCredentials] = None

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id, "name": self.name, "version": self.version,
            "description": self.description, "author": self.author, "license": self.license,
            "engine": self.engine, "permissions": list(self.permissions), "mcu_cost": self.mcu_cost,
            "dependencies": list(self.dependencies), "entry_point": self.entry_point,
            "isolation": self.isolation, "enabled": self.enabled, "installed_at": self.installed_at,
            "checksum": self.checksum,
        }
        if self.credentials is not None:
            data["credentials"] = [
                {"provider": r.provider, "env_fallback": r.env_fallback, "required": r.required, "scope": r.scope, "description": r.description}
                for r in self.credentials.requirements
            ]
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Manifest:
        hooks = []
        for raw_hook in data.get("hooks", []):
            try:
                hooks.append(HookSpecRecord(
                    spec=HookSpec(raw_hook["spec"]), handler=raw_hook["handler"],
                    priority=int(raw_hook.get("priority", 50)),
                ))
            except Exception:
                continue
        creds = PluginCredentials(
            requirements=[CredentialRequirement(**req) for req in data.get("credentials") or []]
        ) if data.get("credentials") else None
        return Manifest(
            id=data["id"], name=data["name"], version=data["version"],
            description=data.get("description", ""), author=data.get("author", ""),
            license=data.get("license", "MIT"), engine=data.get("engine", "^6.0.0"),
            permissions=list(data.get("permissions", [])), mcu_cost=int(data.get("mcu_cost", 1)),
            dependencies=list(data.get("dependencies", [])), entry_point=data.get("entry_point"),
            isolation=data.get("isolation", "none"), hooks=hooks, enabled=bool(data.get("enabled", True)),
            installed_at=float(data.get("installed_at", time.time())), checksum=data.get("checksum", ""),
            credentials=creds,
        )

    @staticmethod
    def from_module(module: Any) -> Manifest:
        meta = getattr(module, "__plugin_meta__", None)
        if not isinstance(meta, dict):
            raise ValueError("Plugin module must expose __plugin_meta__ dict")
        return Manifest.from_dict(meta)
