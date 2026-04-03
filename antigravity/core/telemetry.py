"""
Telemetry — lightweight event tracking with persistence.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryEvent:
    """A single tracked event."""

    category: str
    action: str
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Telemetry:
    """Track events and persist them across sessions."""

    _FILENAME = "telemetry.json"

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.storage_path = storage_path
        self.events: List[TelemetryEvent] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def track(
        self,
        category: str,
        action: str,
        duration_ms: float = 0.0,
    ) -> None:
        """Record an event."""
        event = TelemetryEvent(category=category, action=action, duration_ms=duration_ms)
        self.events.append(event)
        self._persist()

    def get_summary(self) -> Dict[str, Any]:
        """Return statistical aggregation over recorded events."""
        total = len(self.events)
        top_categories: Dict[str, int] = {}
        top_actions: Dict[str, int] = {}

        for evt in self.events:
            top_categories[evt.category] = top_categories.get(evt.category, 0) + 1
            top_actions[evt.action] = top_actions.get(evt.action, 0) + 1

        return {
            "volume": {"total_events": total},
            "top_categories": top_categories,
            "top_actions": top_actions,
        }

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _filepath(self) -> Optional[str]:
        if not self.storage_path:
            return None
        return os.path.join(self.storage_path, self._FILENAME)

    def _persist(self) -> None:
        path = self._filepath()
        if not path:
            return
        try:
            data = [e.to_dict() for e in self.events]
            with open(path, "w") as fh:
                json.dump(data, fh)
        except OSError:
            pass

    def _load(self) -> None:
        path = self._filepath()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path) as fh:
                raw = json.load(fh)
            for item in raw:
                self.events.append(TelemetryEvent(**item))
        except (OSError, json.JSONDecodeError, TypeError):
            pass
