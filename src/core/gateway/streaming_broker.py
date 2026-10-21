# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mission event streaming broker and pub/sub registry."""

from __future__ import annotations

import collections
import threading
import time
from typing import Any, Optional

from .streaming_broker_cmd import handle_mission_command
from .streaming_broker_global import (
    get_mission_broker,
    get_mission_streaming_broker,
    set_mission_streaming_broker,
)
from .streaming_types import (
    EventSubscriber,
    MissionControl,
    StreamEvent,
    StreamEventType,
)


class MissionStreamingBroker:
    """Thread-safe in-memory pub/sub broker for real-time mission event streaming."""

    def __init__(self, history_limit: int = 500) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[str, set[EventSubscriber]] = {}
        self._history: dict[str, collections.deque[StreamEvent]] = {}
        self._controls: dict[str, MissionControl] = {}
        self._history_limit = history_limit
        self._seq = 0
        self._sub_seq = 0
        self._total_events_emitted = 0
        self._active_ws_connections = 0
        self._start_time = time.time()

    def publish(
        self,
        mission_id: str,
        event_type: str | StreamEventType,
        data: dict[str, Any],
    ) -> StreamEvent:
        if isinstance(event_type, str):
            try:
                typed_event: StreamEventType | str = StreamEventType(event_type.lower())
            except ValueError:
                typed_event = event_type
        else:
            typed_event = event_type

        with self._lock:
            self._seq += 1
            evt_id = f"evt_{int(time.time() * 1000)}_{self._seq}"
            event = StreamEvent(
                event_id=evt_id,
                mission_id=mission_id,
                event_type=typed_event,
                data=data,
                timestamp=time.time(),
            )

            if mission_id not in self._history:
                self._history[mission_id] = collections.deque(maxlen=self._history_limit)
            self._history[mission_id].append(event)
            self._total_events_emitted += 1

            subscribers = list(self._subscribers.get(mission_id, set()))

        for sub in subscribers:
            sub.push(event)

        return event

    def subscribe(
        self,
        mission_id: str,
        since_cursor: Optional[str] = None,
        subscriber_id: Optional[str] = None,
    ) -> EventSubscriber:
        with self._lock:
            self._sub_seq += 1
            sub_id = subscriber_id or f"sub_{int(time.time() * 1000)}_{self._sub_seq}_{id(self)}"
            subscriber = EventSubscriber(subscriber_id=sub_id, mission_id=mission_id)

            if mission_id not in self._subscribers:
                self._subscribers[mission_id] = set()
            self._subscribers[mission_id].add(subscriber)

            if since_cursor is not None:
                history = list(self._history.get(mission_id, []))
                cursor_idx = -1
                for idx, ev in enumerate(history):
                    if ev.event_id == since_cursor:
                        cursor_idx = idx
                        break
                replays = history[cursor_idx + 1 :] if cursor_idx != -1 else history
                for ev in replays:
                    subscriber.push(ev)

        return subscriber

    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        with self._lock:
            mission_id = subscriber.mission_id
            if mission_id in self._subscribers:
                self._subscribers[mission_id].discard(subscriber)
                if not self._subscribers[mission_id]:
                    del self._subscribers[mission_id]

            for subs in list(self._subscribers.values()):
                subs.discard(subscriber)

    def get_mission_control(self, mission_id: str) -> MissionControl:
        with self._lock:
            if mission_id not in self._controls:
                self._controls[mission_id] = MissionControl(mission_id)
            return self._controls[mission_id]

    def handle_command(
        self,
        mission_id: str,
        command: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return handle_mission_command(self, mission_id, command, payload)

    def get_history(self, mission_id: str, limit: int = 50) -> list[StreamEvent]:
        with self._lock:
            history = list(self._history.get(mission_id, []))
        if limit > 0 and len(history) > limit:
            return history[-limit:]
        return history

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            uptime = round(time.time() - self._start_time, 2)
            active_subscribers = sum(len(subs) for subs in self._subscribers.values())
            active_missions = len(self._subscribers)
            return {
                "status": "healthy",
                "uptime": uptime,
                "uptime_seconds": uptime,
                "active_missions": active_missions,
                "active_subscribers": active_subscribers,
                "total_events_emitted": self._total_events_emitted,
                "active_ws_connections": self._active_ws_connections,
            }

    def record_ws_connect(self) -> None:
        with self._lock:
            self._active_ws_connections += 1

    def record_ws_disconnect(self) -> None:
        with self._lock:
            self._active_ws_connections = max(0, self._active_ws_connections - 1)

    def reset(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._history.clear()
            self._controls.clear()
            self._seq = 0
            self._total_events_emitted = 0
            self._active_ws_connections = 0
            self._start_time = time.time()


__all__ = [
    "MissionStreamingBroker",
    "get_mission_broker",
    "get_mission_streaming_broker",
    "set_mission_streaming_broker",
]
