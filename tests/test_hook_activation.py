"""Tests for HookCommandWrapper — E4e hook system activation.

Verifies that BEFORE_COMMAND / AFTER_COMMAND hooks fire around
Typer command dispatch, and that hook failures never crash commands.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import click
import typer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Build proper SDK mock mirrors before importing anything that depends on them
# ---------------------------------------------------------------------------

from enum import Enum
from dataclasses import dataclass


class HookPoint(str, Enum):
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    BEFORE_CLI_START = "before_cli_start"
    AFTER_CLI_START = "after_cli_start"
    BEFORE_PLAN = "before_plan"
    AFTER_PLAN = "after_plan"
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    BEFORE_VERIFY = "before_verify"
    AFTER_VERIFY = "after_verify"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class HookContext:
    plugin_id: str
    command_name: str | None = None
    data: dict | None = None


@dataclass
class Hook:
    point: HookPoint
    handler: any
    priority: int = 50


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = {}

    def initialize(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    def register(self, point, handler, priority=50) -> None:
        key = point.value if hasattr(point, "value") else str(point)
        self._hooks.setdefault(key, []).append(
            Hook(point=point, handler=handler, priority=priority)
        )

    def get_hooks(self, point) -> list[Hook]:
        key = point.value if hasattr(point, "value") else str(point)
        return sorted(self._hooks.get(key, []), key=lambda h: h.priority)

    def execute(self, point, context) -> None:
        for hook in self.get_hooks(point):
            hook.handler(context)

    def clear(self) -> None:
        self._hooks = {}


import types as _types

_sdk_hooks_mod = _types.ModuleType("packages.mekong_plugin_sdk.hooks")
_sdk_hooks_mod.HookPoint = HookPoint
_sdk_hooks_mod.HookContext = HookContext
_sdk_hooks_mod.Hook = Hook
_sdk_hooks_mod.HookRegistry = HookRegistry

_sdk_pkg = _types.ModuleType("packages.mekong_plugin_sdk")
_sdk_pkg.hooks = _sdk_hooks_mod

# Provide plugin submodule so test_plugin_binding mock detection does not skip
_plugin_mod = _types.ModuleType("packages.mekong_plugin_sdk.plugin")
_plugin_mod.create_plugin = None  # placeholder
_sdk_pkg.plugin = _plugin_mod

sys.modules.setdefault("packages", _types.ModuleType("packages"))
sys.modules["packages.mekong_plugin_sdk"] = _sdk_pkg
sys.modules["packages.mekong_plugin_sdk.hooks"] = _sdk_hooks_mod

from src.cli.hook_activation import HookCommandWrapper  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_router() -> MagicMock:
    """Return a mock HookpointRouter with controllable has_hooks / fire_safe."""
    router = MagicMock()
    router.has_hooks.return_value = False
    router.fire_safe.return_value = None
    return router


def _make_app() -> typer.Typer:
    """Create a fresh Typer app with no prior callback installed."""
    app = typer.Typer()
    if hasattr(app, "_hook_wrapper_installed"):
        delattr(app, "_hook_wrapper_installed")
    return app


def _invoke_callback(app: typer.Typer, command_name: str = "test-cmd") -> None:
    """Invoke the Typer registered callback with a fake Click context."""
    cb_info = app.registered_callback
    assert cb_info is not None, "No callback registered on app"
    fake_cmd = click.Command(command_name)
    ctx = click.Context(fake_cmd, info_name=command_name)
    ctx.args = []
    ctx.invoked_subcommand = command_name
    cb_info.callback(ctx)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHookCommandWrapperInstall:
    def test_install_sets_callback(self):
        """install() should add a callback to the Typer app."""
        router = _make_router()
        router.has_hooks.return_value = True
        app = _make_app()

        wrapper = HookCommandWrapper(router)
        wrapper.install(app)

        assert getattr(app, "_hook_wrapper_installed", False) is True

    def test_install_is_idempotent(self):
        """Calling install() twice should not install two callbacks."""
        router = _make_router()
        router.has_hooks.return_value = True
        app = _make_app()

        wrapper = HookCommandWrapper(router)
        wrapper.install(app)
        wrapper.install(app)  # second call

        assert getattr(app, "_hook_wrapper_installed", False) is True

    def test_install_with_none_router(self):
        """install() should handle None router gracefully."""
        app = _make_app()
        wrapper = HookCommandWrapper(None)
        wrapper.install(app)
        assert getattr(app, "_hook_wrapper_installed", False) is True


class TestHookCommandWrapperFireBefore:
    def test_fires_before_when_hooks_exist(self):
        """fire_safe(BEFORE_COMMAND) is called when has_hooks returns True."""
        router = _make_router()
        router.has_hooks.return_value = True
        app = _make_app()

        wrapper = HookCommandWrapper(router)
        wrapper.install(app)

        _invoke_callback(app, "my-command")

        router.fire_safe.assert_called()

    def test_skips_before_when_no_hooks(self):
        """When no BEFORE_COMMAND hooks, fire_safe is NOT called."""
        router = _make_router()
        router.has_hooks.return_value = False
        app = _make_app()

        wrapper = HookCommandWrapper(router)
        wrapper.install(app)

        _invoke_callback(app, "my-command")

        # No hooks registered — fire_safe should not be called
        router.fire_safe.assert_not_called()
