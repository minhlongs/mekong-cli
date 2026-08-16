# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stub: execution history for PEV orchestrator."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

class EventKind(Enum):
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_FAIL = "step_fail"
    VERIFY_PASS = "verify_pass"
    VERIFY_FAIL = "verify_fail"

@dataclass
class ExecutionEvent:
    kind: EventKind
    step_index: int
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class ExecutionHistory:
    events: List[ExecutionEvent] = field(default_factory=list)
    goal_id: Optional[str] = None

    def record(self, event: ExecutionEvent) -> None:
        self.events.append(event)

    def get_events(self) -> List[ExecutionEvent]:
        return list(self.events)
