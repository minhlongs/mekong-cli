"""Adapters between goal lifecycle events and the legacy event bus."""

from __future__ import annotations

from typing import Any

from src.core.event_bus import EventType, get_event_bus


class GoalEventBusAdapter:
    """Emits goal-engine events through the existing in-process event bus."""

    def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        mapping = {
            "goal.started": EventType.GOAL_STARTED,
            "goal.completed": EventType.GOAL_COMPLETED,
            "task.started": EventType.STEP_STARTED,
            "task.completed": EventType.STEP_COMPLETED,
            "task.failed": EventType.STEP_FAILED,
            "memory.recorded": EventType.MEMORY_RECORDED,
        }
        event_type = mapping.get(event_name, EventType.AUTONOMOUS_CYCLE)
        get_event_bus().emit(event_type, {"event": event_name, **payload})
