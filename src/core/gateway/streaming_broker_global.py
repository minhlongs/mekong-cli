# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Global singleton management for MissionStreamingBroker."""

from __future__ import annotations

import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .streaming_broker import MissionStreamingBroker

_GLOBAL_BROKER: Optional[MissionStreamingBroker] = None
_BROKER_LOCK = threading.Lock()


def get_mission_streaming_broker() -> MissionStreamingBroker:
    """Retrieve or initialize the global MissionStreamingBroker singleton."""
    global _GLOBAL_BROKER
    with _BROKER_LOCK:
        if _GLOBAL_BROKER is None:
            from .streaming_broker import MissionStreamingBroker
            _GLOBAL_BROKER = MissionStreamingBroker()
        return _GLOBAL_BROKER


def set_mission_streaming_broker(broker: MissionStreamingBroker) -> None:
    """Override the global MissionStreamingBroker singleton."""
    global _GLOBAL_BROKER
    with _BROKER_LOCK:
        _GLOBAL_BROKER = broker


def get_mission_broker() -> MissionStreamingBroker:
    """Alias for get_mission_streaming_broker."""
    return get_mission_streaming_broker()


__all__ = [
    "get_mission_broker",
    "get_mission_streaming_broker",
    "set_mission_streaming_broker",
]
