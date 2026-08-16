# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hookpoint routing — fires registered plugin hooks at CLI lifecycle points.

Collects Hook objects from PluginRuntime._loaded, groups by HookPoint,
and provides fire() / fire_safe() dispatch methods.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from packages.mekong_plugin_sdk.hooks import HookPoint, HookContext

from src.core.plugin_runtime import PluginRuntime

logger = logging.getLogger(__name__)


class HookpointRouter:
    """Routes hook execution to registered plugin handlers.

    Groups hooks from all loaded plugins by their HookPoint and dispatches
    via HookRegistry.execute() in priority order.

    Usage::

        router = HookpointRouter(runtime)
        router.fire(HookPoint.AFTER_COMMAND, HookContext(plugin_id="*", ...))
    """

    def __init__(self, runtime: PluginRuntime) -> None:
        """Collect hooks from all loaded plugins and build per-point registries.

        Args:
            runtime: PluginRuntime with plugins already loaded.
        """
        self._runtime = runtime
        self._registries: Dict[HookPoint, Any] = {}  # HookPoint -> HookRegistry
        self._build_registries()

    def _build_registries(self) -> None:
        """Group hooks from all loaded plugins by HookPoint.

        Creates one HookRegistry per HookPoint. Each plugin's hooks are
        registered into the matching registry.
        """
        from packages.mekong_plugin_sdk.hooks import HookRegistry

        # Initialize one registry per point
        for point in HookPoint:
            self._registries[point] = HookRegistry()

        # Register each plugin's hooks into the matching registry
        for loaded in self._runtime.iter_loaded():
            for hook in loaded.hooks:
                registry = self._registries.get(hook.point)
                if registry is not None:
                    registry.register(hook.point, hook.handler, hook.priority)

    def fire(self, point: HookPoint, context: HookContext) -> List[Exception]:
        """Execute all handlers registered for *point*.

        Calls HookRegistry.execute() for each plugin's registry. Exceptions
        propagate — the caller is responsible for handling them.

        Args:
            point: HookPoint to fire.
            context: HookContext to pass to all handlers.

        Returns:
            List of exceptions raised by handlers (empty = all succeeded).
        """
        errors: List[Exception] = []
        registry = self._registries.get(point)
        if registry is None:
            return errors
        try:
            registry.execute(point, context)
        except Exception as exc:
            errors.append(exc)
        return errors

    def fire_safe(self, point: HookPoint, context: HookContext) -> None:
        """Execute all handlers for *point*, swallowing exceptions.

        Same as fire() but catches and logs all exceptions. Never raises.

        Args:
            point: HookPoint to fire.
            context: HookContext to pass to all handlers.
        """
        try:
            self.fire(point, context)
        except Exception as exc:
            logger.warning("Hook handler error at %s: %s", point.value, exc)

    def get_hooks(self, point: HookPoint) -> List[Any]:
        """Return registered hooks for a point (sorted by priority)."""
        registry = self._registries.get(point)
        if registry is None:
            return []
        return registry.get_hooks(point)

    def has_hooks(self, point: HookPoint) -> bool:
        """True if at least one handler is registered for *point*."""
        return bool(self.get_hooks(point))
