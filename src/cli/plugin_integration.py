# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin command binding — E4d.

Wires loaded plugin commands into the Mekong Typer root so that
``mekong <plugin-id> <command>`` routes to the loaded plugin.

SDK commands expose: ``.name``, ``.description``, ``.handler(**kwargs)``.

Usage::

    from src.cli.plugin_integration import bind_plugin_commands, unbind_plugin_commands
    bind_plugin_commands(root, runtime)    # after runtime.load_all()
    unbind_plugin_commands(root, runtime)  # before reload
"""
from __future__ import annotations

import logging
from typing import Any, List, Set

import typer

from src.core.plugin_runtime import PluginRuntime

logger = logging.getLogger(__name__)

# module-level tracking of bound plugin ids (guards against double-register)
_bound: Set[str] = set()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def bind_plugin_commands(root: typer.Typer, runtime: PluginRuntime) -> None:
    """Register every loaded plugin as a sub-app under *root*.

    Each plugin gets its own Typer sub-app named after the plugin id.
    Idempotent — already-bound plugin ids are silently skipped.
    """
    for loaded in runtime.iter_loaded():
        pid = loaded.plugin_id
        if pid in _bound:
            continue

        _register_plugin_app(root, loaded)
        _bound.add(pid)
        logger.debug("Bound plugin %s (%d commands)", pid, len(loaded.commands))


def unbind_plugin_commands(root: typer.Typer, runtime: PluginRuntime) -> None:
    """Remove previously bound plugin sub-apps from *root*."""
    for pid in list(_bound):
        _unregister_plugin_app(root, pid)
        _bound.discard(pid)
        logger.debug("Unbound plugin %s", pid)


def bound_plugin_ids() -> Set[str]:
    """Return the set of plugin ids currently bound to any root app."""
    return set(_bound)


# ---------------------------------------------------------------------------
# Wire / Un-wire
# ---------------------------------------------------------------------------


def _register_plugin_app(root: typer.Typer, loaded: Any) -> None:
    """Create a sub-app for *loaded* and add it to *root*."""
    pid = loaded.plugin_id
    manifest = loaded.manifest
    plugin_app = typer.Typer(
        name=pid,
        help=getattr(manifest, "description", "") or getattr(manifest, "name", pid) or pid,
        no_args_is_help=True,
    )

    if not loaded.commands:
        plugin_app.command("help")(_noop_help(pid))
    else:
        _wire_sdk_commands(plugin_app, loaded.commands)

    root.add_typer(plugin_app, name=pid)


def _unregister_plugin_app(root: typer.Typer, pid: str) -> None:
    """Remove sub-app named *pid* from *root*."""
    # Typer adds sub-apps to registered_groups list — filter them out
    groups: List[Any] = getattr(root, "registered_groups", [])
    root.registered_groups = [g for g in groups if getattr(g, "name", None) != pid]


def _noop_help(pid: str):
    def _cmd():
        return f"No commands registered for {pid}."
    _cmd.__name__ = "help"
    _cmd.__doc__ = "Show this message"
    return _cmd


# ---------------------------------------------------------------------------
# SDK command wiring
# ---------------------------------------------------------------------------


def _wire_sdk_commands(plugin_app: typer.Typer, commands: list) -> None:
    """Attach each SDK command as a Typer command on *plugin_app*.

    SDK command interface::
        cmd.name        → str  (command name)
        cmd.description → str  (help text)
        cmd.handler     → Callable(**kwargs) → Any
    """
    for sdk_cmd in commands:
        cmd_name = getattr(sdk_cmd, "name", None) or str(sdk_cmd)
        cmd_desc = getattr(sdk_cmd, "description", "") or ""
        cmd_handler = getattr(sdk_cmd, "handler", None)

        if cmd_handler is None:
            logger.warning("Skipping SDK command %s: no handler", cmd_name)
            continue

        def _make_handler(handler, name: str):
            def _handler():
                return handler()
            _handler.__name__ = name
            _handler.__doc__ = cmd_desc
            return _handler

        plugin_app.command(
            cmd_name,
            help=cmd_desc,
        )(_make_handler(cmd_handler, cmd_name))
