# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin authoring API.

Public decorators and helpers plugin authors consume at module scope:

- ``@plugin(...)`` — class/function wrapper that stamps ``__plugin_meta__`` on the decorated object.
- ``@hook(spec, priority)`` — register a hook handler inside a plugin class.

Intended usage inside a plugin module::

    from mekong.plugins import plugin, hook, HookSpec

    @plugin(
        id="com.example.my-plugin",
        name="My Plugin",
        version="0.1.0",
        entry_point="src.hello.register",
    )
    class MyPlugin:
        @hook(HookSpec.BEFORE_COMMAND, priority=10)
        def before(self, ctx, command, args):
            ...
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union, Iterable

from .exceptions import PluginError
from .types import HookSpec, HookSpecRecord, PluginContext, Result

logger = logging.getLogger(__name__)

# Module-level registry of decorators used by plugin authors
_PLUGIN_REGISTRY: Dict[str, Dict[str, Any]] = {}


def plugin(
    *,
    id: str,
    name: str,
    version: str,
    description: str = "",
    author: str = "",
    license: str = "MIT",
    engine: str = "^6.0.0",
    permissions: Optional[list] = None,
    mcu_cost: int = 1,
    dependencies: Optional[list] = None,
    entry_point: Optional[str] = None,
    isolation: str = "none",
) -> Callable[[Type[Any]], Type[Any]]:
    """Class decorator: stamp ``__plugin_meta__`` on the class and index the plugin in global state."""

    def decorator(cls: Type[Any]) -> Type[Any]:
        meta: Dict[str, Any] = {
            "id": id,
            "name": name,
            "version": version,
            "description": description,
            "author": author,
            "license": license,
            "engine": engine,
            "permissions": list(permissions or []),
            "mcu_cost": int(mcu_cost),
            "dependencies": list(dependencies or []),
            "entry_point": entry_point,
            "isolation": isolation,
            "hooks": [],
        }
        # Convert nested hook records if the class already has hook() decorators applied
        hooks: list = getattr(cls, "_mekong_hooks", [])
        for rec in hooks:
            meta["hooks"].append(
                {
                    "spec": rec.spec.value,
                    "handler": rec.handler.__name__,
                    "priority": int(rec.priority),
                }
            )
        cls.__plugin_meta__ = meta  # type: ignore[attr-defined]
        _PLUGIN_REGISTRY[id] = meta
        return cls

    return decorator


def hook(
    spec: Union[HookSpec, str],
    priority: int = 50,
) -> Callable[[Callable[..., Result]], Callable[..., Result]]:
    """Method decorator: attach to ``_mekong_hooks`` on the owner class.

    Must be applied after ``@plugin`` (Python applies decorators inside->out,
    so actually the inner hook decorator runs first; we accumulate onto
    the class which is then wrapped by ``@plugin``).
    """

    def decorator(fn: Callable[..., Result]) -> Callable[..., Result]:
        spec_value = spec.value if isinstance(spec, HookSpec) else str(spec)
        try:
            hook_spec = HookSpec(spec_value)
        except ValueError as exc:
            raise PluginError(f"Unknown hook spec '{spec_value}'") from exc
        # Attach to the bound method; owner class picks these up in @plugin
        fn._mekong_hook = HookSpecRecord(spec=hook_spec, handler=fn, priority=priority)  # type: ignore[attr-defined]
        return fn

    return decorator


def command(
    name: Optional[str] = None,
) -> Callable[[Callable[..., Result]], Callable[..., Result]]:
    """Mark a plugin method as a CLI command.

    ``name`` defaults to the function/class-method name.
    """

    def decorator(fn: Callable[..., Result]) -> Callable[..., Result]:
        fn._mekong_command_name = name or fn.__name__  # type: ignore[attr-defined]
        return fn

    return decorator


def get_plugin_meta(plugin_id: str) -> Dict[str, Any]:
    """Return the cached meta for a plugin id (from earlier ``@plugin`` decoration).

    Raises ``KeyError`` if unknown.
    """
    if plugin_id not in _PLUGIN_REGISTRY:
        raise KeyError(f"Unknown plugin id '{plugin_id}' — did you apply @plugin?")
    return _PLUGIN_REGISTRY[plugin_id]


def iter_plugin_metas() -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield (plugin_id, meta) for all plugins decorated with ``@plugin``."""
    return iter(_PLUGIN_REGISTRY.items())


def build_register() -> Callable[[PluginContext], None]:
    """Return a default ``register(ctx)`` suitable for modules that import
    from ``mekong.plugins`` but don't define their own entry point.

    The returned function inspects ``_PLUGIN_REGISTRY`` for any plugin whose
    ``id`` matches the calling module's package name (best-effort) and wires
    its hooks + commands through the given context.
    """

    def _register(ctx: PluginContext) -> None:
        plugin_id = ctx.config.get("plugin_id") or getattr(ctx, "plugin_id", None)
        for candidate_id, meta in _PLUGIN_REGISTRY.items():
            if plugin_id and candidate_id != plugin_id:
                continue
            cls = meta.get("_decorated_cls")
            if cls is None:
                continue
            instance = cls()
            for hook_raw in meta.get("hooks", []):
                try:
                    spec = HookSpec(hook_raw["spec"])
                    handler = getattr(instance, hook_raw["handler"].split(".")[-1])
                    ctx.hook(spec, handler, priority=int(hook_raw.get("priority", 50)))
                except Exception:
                    pass
            for cmd_name in getattr(instance, "_mekong_commands", []):
                ctx.register_command(cmd_name, getattr(instance, cmd_name))

    return _register
