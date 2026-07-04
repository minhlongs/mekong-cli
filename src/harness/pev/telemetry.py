"""Stub: telemetry collector for PEV orchestrator."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class TelemetryEvent:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

class TelemetryCollector:
    def __init__(self) -> None:
        self._events: List[TelemetryEvent] = []

    def record(self, name: str, **data: Any) -> None:
        self._events.append(TelemetryEvent(name=name, data=data))

    def get_events(self) -> List[TelemetryEvent]:
        return list(self._events)
