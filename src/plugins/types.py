"""
Typed interfaces for the mekong-cli plugin ecosystem.

Public surface:
- PluginId, HookId, CommandId — strongly-typed identifiers.
- Manifest — validated `.mekong-plugin.json` contract for each plugin.
- PluginContext — runtime handoff: registry + config + protected ops.
- HookSpec — declared hook point (before/after/instead).
- Result — operation outcome with optional error text.

All fields use snake_case for Python ergonomics; JSON counterparts live in
the `.mekong-plugin.json` manifest and are translated by registry.sync().
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PluginId(str):
    """Reverse-domain plugin id, e.g. ``com.example.my-plugin``.

    Validated at construction.
    """

    _PATTERN = r"^[a-z0-9]+([.\-][a-z0-9]+)*\.[a-z0-9]+$"

    def __new__(cls, raw: str) -> "PluginId":
        import re

        if not isinstance(raw, str) or not re.match(cls._PATTERN, raw):
            raise ValueError(
                f"Invalid plugin id '{raw}': expected reverse-domain "
                "(e.g. com.example.my-plugin)"
            )
        return super().__new__(cls, raw)


class HookId(str):
    """Identifier of a hook point registered inside a plugin."""

    def __new__(cls, raw: str) -> "HookId":
        if not raw or not isinstance(raw, str):
            raise ValueError("HookId must be a non-empty string")
        return super().__new__(cls, raw)


class HookSpec(str, Enum):
    """Lifecycle hook points exposed by the plugin system."""

    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    ON_ERROR = "on_error"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"


class ResultStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Result:
    """Operation outcome from a plugin action."""

    status: ResultStatus
    value: Any = None
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------
    @staticmethod
    def ok(value: Any = None, **meta: Any) -> "Result":
        return Result(status=ResultStatus.OK, value=value, meta=meta)

    @staticmethod
    def err(error: str, **meta: Any) -> "Result":
        return Result(status=ResultStatus.ERROR, error=error, meta=meta)

    @staticmethod
    def skip(reason: str = "skipped", **meta: Any) -> "Result":
        return Result(status=ResultStatus.SKIPPED, error=reason, meta=meta)

    @staticmethod
    def na(**meta: Any) -> "Result":
        return Result(status=ResultStatus.NOT_APPLICABLE, meta=meta)


@dataclass
class HookSpecRecord:
    """Declaration of a single hook a plugin wants to subscribe to."""

    spec: HookSpec
    handler: Callable[..., Result]  # registered callable
    priority: int = 50  # lower number runs first
    once: bool = False  # if True, auto-unsubscribe after first fire

    def sort_key(self) -> tuple[int, str]:
        return (self.priority, self.handler.__name__)


@dataclass
class Manifest:
    """In-memory representation of a plugin descriptor.

    Created either from ``.mekong-plugin.json`` on disk, from
    a plugin module's ``__plugin_meta__`` attribute, or by code.
    """

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def has_permission(self, perm: str) -> bool:
        """Return True if the plugin explicitly requests *perm*."""
        return perm in self.permissions

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "engine": self.engine,
            "permissions": list(self.permissions),
            "mcu_cost": self.mcu_cost,
            "dependencies": list(self.dependencies),
            "entry_point": self.entry_point,
            "isolation": self.isolation,
            "enabled": self.enabled,
            "installed_at": self.installed_at,
            "checksum": self.checksum,
        }
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Manifest":
        """Hydrate a Manifest from a plain dict (e.g. parsed JSON)."""
        hooks = []
        for raw_hook in data.get("hooks", []):
            try:
                hooks.append(
                    HookSpecRecord(
                        spec=HookSpec(raw_hook["spec"]),
                        handler=raw_hook["handler"],
                        priority=int(raw_hook.get("priority", 50)),
                    )
                )
            except Exception:
                continue
        return Manifest(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", "MIT"),
            engine=data.get("engine", "^6.0.0"),
            permissions=list(data.get("permissions", [])),
            mcu_cost=int(data.get("mcu_cost", 1)),
            dependencies=list(data.get("dependencies", [])),
            entry_point=data.get("entry_point"),
            isolation=data.get("isolation", "none"),
            hooks=hooks,
            enabled=bool(data.get("enabled", True)),
            installed_at=float(data.get("installed_at", time.time())),
            checksum=data.get("checksum", ""),
        )

    @staticmethod
    def from_module(module: Any) -> "Manifest":
        """Build a Manifest from ``__plugin_meta__`` on a plugin module.

        Raises ``ValueError`` if mandatory fields are missing.
        """
        meta = getattr(module, "__plugin_meta__", None)
        if not isinstance(meta, dict):
            raise ValueError("Plugin module must expose __plugin_meta__ dict")
        return Manifest.from_dict(meta)


@dataclass
class PluginContext:
    """Runtime handoff object passed into plugin ``register()``.

    Provides:
    - ``registry`` — the PluginRegistry instance (read-mostly).
    - ``commands`` — the command registry (register_command stub).
    - ``config`` — key/value configuration for this plugin (no writes to disk).
    - ``hook()`` — subscribe to a hook point.
    - ``log`` — stdlib logger namespaced under this plugin id.
    """

    registry: Any
    commands: Any
    config: Dict[str, Any]
    _hook_cb: Optional[
        Callable[["PluginId", HookSpec, Callable[..., Result], int], None]
    ] = None
    _log_factory: Optional[Callable[[str], Any]] = None

    def hook(
        self,
        spec: HookSpec,
        handler: Callable[..., Result],
        priority: int = 50,
    ) -> None:
        """Subscribe *handler* to the *spec* hook point.

        No-op if the runtime hook channel is not wired yet (graceful).
        """
        if self._hook_cb is None:
            return
        self._hook_cb(
            PluginId(self.config.get("plugin_id", "unknown")), spec, handler, priority
        )

    def log(self, name: str) -> Any:
        """Return a namespaced logger for this plugin."""
        if self._log_factory is not None:
            return self._log_factory(name)
        import logging  # noqa: F811 — stdlib, local to this method

        return logging.getLogger(f"mekong.plugin.{name}")

    # Backwards compatible alias — earlier designs exposed register_command()
    def register_command(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a command handler by name."""
        self.commands.register(name, fn)
