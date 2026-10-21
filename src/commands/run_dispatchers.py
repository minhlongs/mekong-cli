# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dispatchers for `mekong run` command."""

from __future__ import annotations


class _NullDispatcher:
    """Minimal dispatcher stub — runtime falls back gracefully when no dispatch()."""

    def dispatch(self, task, agent=None):  # noqa: ANN001, ANN202
        raise NotImplementedError("No dispatcher configured")


class _RegistryDispatcher:
    """Dispatcher backed by the AgentRegistry (core agent stack).

    Resolves ``task.agent`` (an ``AgentId``) to a registered ``AgentBase``
    subclass via ``AgentRegistry.get_meta_obj`` and spawns it through
    ``AgentBase.run()``. Unknown agents raise ``NotImplementedError`` — the
    same graceful failure path the null dispatcher used, so the runtime's
    execute() catches it and surfaces a terminal error instead of crashing.
    """

    def __init__(self) -> None:
        from src.core.agent_registry import get_registry

        self._registry = get_registry()

    def dispatch(self, task, agent=None):  # noqa: ANN001, ANN202
        agent_name = getattr(agent, "name", None) or self._fallback_agent_name(task)
        meta = self._registry.get_meta_obj(agent_name)
        if meta is None:
            raise NotImplementedError(f"No dispatcher configured for agent '{agent_name}'")
        try:
            agent_instance = meta.cls(name=agent_name)
        except TypeError as exc:
            raise NotImplementedError(f"Cannot instantiate agent '{agent_name}': {exc}") from exc
        # The runtime's Task wraps a Step (task.step.description); the frozen
        # test passes a bare Step directly. Resolve either shape.
        goal_text = getattr(task, "description", None)
        if goal_text is None:
            step = getattr(task, "step", task)
            goal_text = getattr(step, "description", "") or ""
        results = agent_instance.run(goal_text)
        if not results:
            return {"status": "noop", "task_id": task.id}
        final = results[-1]
        return {
            "status": "success" if final.success else "failed",
            "task_id": task.id,
            "output": final.output,
            "error": final.error,
            "agent": agent_name,
        }

    @staticmethod
    def _fallback_agent_name(task) -> str:
        """Best-effort agent name when ``task.agent`` is missing."""
        params = getattr(task, "params", None) or {}
        return params.get("agent") or "default"
