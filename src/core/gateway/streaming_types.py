# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stream event types, models, subscriber queue and mission control primitives."""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class StreamEventType(str, Enum):
    """Typed stream events emitted across the autonomous agent lifecycle."""

    PLAN_CREATED = "plan_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CHECKPOINT_CAPTURED = "checkpoint_captured"
    MISSION_COMPLETED = "mission_completed"
    COMMAND_ACK = "command_ack"
    ERROR = "error"
    PING = "ping"
    HEARTBEAT = "heartbeat"


class ControlCommand(str, Enum):
    """Client duplex control commands."""

    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"


@dataclass
class StreamEvent:
    """Canonical event model for mission execution streaming."""

    event_id: str
    mission_id: str
    event_type: StreamEventType | str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        evt_type_val = (
            self.event_type.value
            if isinstance(self.event_type, Enum)
            else str(self.event_type)
        )
        return {
            "event_id": self.event_id,
            "mission_id": self.mission_id,
            "event_type": evt_type_val,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    def to_sse_frame(self) -> str:
        payload = json.dumps(self.to_dict())
        evt_type_val = (
            self.event_type.value
            if isinstance(self.event_type, Enum)
            else str(self.event_type)
        )
        return f"id: {self.event_id}\nevent: {evt_type_val}\ndata: {payload}\n\n"

    def to_sse(self) -> str:
        return self.to_sse_frame()


class EventSubscriber:
    """Thread-safe subscriber queue isolating client consumers from publisher."""

    def __init__(
        self,
        subscriber_id: str,
        mission_id: str = "",
        max_buffer: int = 1000,
    ) -> None:
        self.subscriber_id = subscriber_id
        self.mission_id = mission_id
        self.queue: queue.Queue[StreamEvent] = queue.Queue(maxsize=max_buffer)
        self.created_at = time.time()

    def push(self, event: StreamEvent) -> bool:
        try:
            self.queue.put_nowait(event)
            return True
        except queue.Full:
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(event)
                return True
            except (queue.Empty, queue.Full):
                return False

    def put(self, event: StreamEvent) -> bool:
        return self.push(event)

    def get(self, timeout: float = 1.0) -> StreamEvent:
        return self.queue.get(timeout=timeout)

    def __hash__(self) -> int:
        return hash(self.subscriber_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventSubscriber):
            return self.subscriber_id == other.subscriber_id
        return False


class MissionControl:
    """Thread-safe mission control state (pause/resume/cancel)."""

    def __init__(self, mission_id: str) -> None:
        self.mission_id = mission_id
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancelled = False
        self._lock = threading.Lock()

    def pause(self) -> None:
        with self._lock:
            self._pause_event.clear()

    def resume(self) -> None:
        with self._lock:
            self._pause_event.set()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            self._pause_event.set()

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def is_cancelled(self) -> bool:
        return self._cancelled

    def wait_if_paused(self, timeout: Optional[float] = None) -> bool:
        return self._pause_event.wait(timeout=timeout)


__all__ = [
    "ControlCommand",
    "EventSubscriber",
    "MissionControl",
    "StreamEvent",
    "StreamEventType",
]
