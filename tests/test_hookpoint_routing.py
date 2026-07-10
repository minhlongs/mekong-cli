"""Tests for HookpointRouter (src/cli/hookpoint_routing.py)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock
from enum import Enum
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Build proper SDK mock mirrors before importing anything that depends on them


class HookPoint(str, Enum):
    BEFORE_CLI_START = "before_cli_start"
    AFTER_CLI_START = "after_cli_start"
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
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
    """Mirror of SDK HookRegistry for testing."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = {}

    def initialize(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    def register(self, point, handler, priority=50) -> None:
        key = point.value if hasattr(point, "value") else str(point)
        self._hooks.setdefault(key, []).append(Hook(point=point, handler=handler, priority=priority))

    def get_hooks(self, point) -> list[Hook]:
        key = point.value if hasattr(point, "value") else str(point)
        return sorted(self._hooks.get(key, []), key=lambda h: h.priority)

    def execute(self, point, context) -> None:
        for hook in self.get_hooks(point):
            hook.handler(context)

    def clear(self) -> None:
        self._hooks = {}


# Install mocks in sys.modules so hookpoint_routing.py can import them
import types as _types  # noqa: E402

_sdk_hooks_mod = _types.ModuleType("packages.mekong_plugin_sdk.hooks")
_sdk_hooks_mod.HookPoint = HookPoint
_sdk_hooks_mod.HookContext = HookContext
_sdk_hooks_mod.Hook = Hook
_sdk_hooks_mod.HookRegistry = HookRegistry

_sdk_pkg = _types.ModuleType("packages.mekong_plugin_sdk")
_sdk_pkg.hooks = _sdk_hooks_mod

sys.modules.setdefault("packages.mekong_plugin_sdk", _sdk_pkg)
sys.modules.setdefault("packages.mekong_plugin_sdk.hooks", _sdk_hooks_mod)

from src.core.plugin_runtime import PluginRuntime, LoadedPlugin  # noqa: E402
from src.cli.hookpoint_routing import HookpointRouter  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_runtime(hooks_per_plugin):
    """Create a PluginRuntime with mocked loaded plugins.

    hooks_per_plugin: dict[plugin_id, list[Hook]]
    """
    runtime = MagicMock(spec=PluginRuntime)
    runtime.iter_loaded = lambda: [
        LoadedPlugin(
            plugin_id=pid,
            manifest=None,
            instance=None,
            hooks=hooks,
            source="test",
        )
        for pid, hooks in hooks_per_plugin.items()
    ]
    return runtime


def _make_hook(point, handler, priority=500):
    return Hook(point=point, handler=handler, priority=priority)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHookpointRouterInit:
    def test_empty_plugins_no_hooks(self):
        """Router with no plugins has no hooks for any point."""
        runtime = _make_runtime({})
        router = HookpointRouter(runtime)
        assert not router.has_hooks(HookPoint.AFTER_COMMAND)
        assert not router.has_hooks(HookPoint.BEFORE_COMMAND)

    def test_single_plugin_single_hook(self):
        """Router collects a single hook from a single plugin."""
        handler = MagicMock()
        hooks = [_make_hook(HookPoint.AFTER_COMMAND, handler)]
        runtime = _make_runtime({"com.test.plugin": hooks})
        router = HookpointRouter(runtime)
        assert router.has_hooks(HookPoint.AFTER_COMMAND)
        assert not router.has_hooks(HookPoint.BEFORE_COMMAND)

    def test_multiple_plugins_multiple_points(self):
        """Router collects hooks across multiple plugins and points."""
        h1 = MagicMock()
        h2 = MagicMock()
        hooks_by_plugin = {
            "com.test.a": [_make_hook(HookPoint.BEFORE_COMMAND, h1)],
            "com.test.b": [_make_hook(HookPoint.AFTER_COMMAND, h2)],
        }
        runtime = _make_runtime(hooks_by_plugin)
        router = HookpointRouter(runtime)
        assert router.has_hooks(HookPoint.BEFORE_COMMAND)
        assert router.has_hooks(HookPoint.AFTER_COMMAND)


class TestHookpointRouterFire:
    def test_fire_calls_handler(self):
        """fire() invokes registered handlers."""
        handler = MagicMock()
        hooks = [_make_hook(HookPoint.AFTER_COMMAND, handler)]
        runtime = _make_runtime({"p": hooks})
        router = HookpointRouter(runtime)
        ctx = HookContext(plugin_id="p", command_name="test")
        router.fire(HookPoint.AFTER_COMMAND, ctx)
        handler.assert_called_once_with(ctx)

    def test_fire_multiple_handlers_priority_order(self):
        """Handlers fire in priority order (lower first)."""
        order = []

        def make_handler(name):
            def handler(ctx):
                order.append(name)
            return handler

        hooks = [
            _make_hook(HookPoint.AFTER_COMMAND, make_handler("high"), priority=100),
            _make_hook(HookPoint.AFTER_COMMAND, make_handler("low"), priority=10),
        ]
        runtime = _make_runtime({"p": hooks})
        router = HookpointRouter(runtime)
        ctx = HookContext(plugin_id="p")
        router.fire(HookPoint.AFTER_COMMAND, ctx)
        assert order == ["low", "high"]

    def test_fire_no_hooks_returns_empty(self):
        """fire() on a point with no hooks returns empty list."""
        runtime = _make_runtime({})
        router = HookpointRouter(runtime)
        ctx = HookContext(plugin_id="*")
        result = router.fire(HookPoint.BEFORE_COMMAND, ctx)
        assert result == []

    def test_fire_safe_swallows_exceptions(self):
        """fire_safe() catches handler exceptions and logs them."""
        def bad_handler(ctx):
            raise RuntimeError("boom")

        hooks = [_make_hook(HookPoint.AFTER_COMMAND, bad_handler)]
        runtime = _make_runtime({"p": hooks})
        router = HookpointRouter(runtime)
        ctx = HookContext(plugin_id="p")
        # Should not raise
        router.fire_safe(HookPoint.AFTER_COMMAND, ctx)


class TestHookpointRouterEdgeCases:
    def test_get_hooks_returns_list(self):
        """get_hooks() returns the registered Hook objects."""
        handler = MagicMock()
        hooks = [_make_hook(HookPoint.BEFORE_COMMAND, handler, priority=10)]
        runtime = _make_runtime({"p": hooks})
        router = HookpointRouter(runtime)
        result = router.get_hooks(HookPoint.BEFORE_COMMAND)
        assert len(result) == 1
        assert result[0].priority == 10

    def test_empty_hook_list_on_plugin(self):
        """Plugin with empty hooks list contributes nothing."""
        runtime = _make_runtime({"p": []})
        router = HookpointRouter(runtime)
        assert not router.has_hooks(HookPoint.AFTER_COMMAND)
