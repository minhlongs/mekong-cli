"""Plugin usage metering — track plugin invocations against MCU budget."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UsageEvent:
    """Single plugin usage event."""
    plugin_id: str
    user_id: str
    event_type: str = "invoke"
    mcu_cost: int = 1
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PluginUsageMeter:
    """In-memory usage tracker for plugin invocations.

    Production: replace with D1/KV persistence.
    """

    def __init__(self) -> None:
        self._events: list[UsageEvent] = []

    def record(self, event: UsageEvent) -> None:
        self._events.append(event)
        logger.debug("meter.record: plugin=%s user=%s cost=%d", event.plugin_id, event.user_id, event.mcu_cost)

    def total_mcu_for(self, plugin_id: str, user_id: str) -> int:
        return sum(e.mcu_cost for e in self._events if e.plugin_id == plugin_id and e.user_id == user_id)

    def events_for(self, plugin_id: str, user_id: str) -> list[UsageEvent]:
        return [e for e in self._events if e.plugin_id == plugin_id and e.user_id == user_id]

    def clear(self) -> None:
        self._events.clear()


# Global singleton
usage_meter = PluginUsageMeter()
