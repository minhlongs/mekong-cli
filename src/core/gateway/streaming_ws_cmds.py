# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""WebSocket client command dispatch and message handling."""

from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .streaming_broker import MissionStreamingBroker


def parse_client_command(payload: bytes | str) -> dict[str, Any]:
    """Parse raw bytes or string into a client command dict."""
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = payload
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("WebSocket payload must be a JSON object")
    return data


def process_client_message(
    payload: bytes | str,
    mission_id: str,
    broker: Optional[MissionStreamingBroker] = None,
) -> dict[str, Any]:
    """Process a client message and route it to the mission streaming broker."""
    if broker is None:
        from .streaming_broker import get_mission_streaming_broker
        broker = get_mission_streaming_broker()
    data = parse_client_command(payload)
    command = str(data.get("command", "")).strip().lower()
    sub_payload = data.get("payload")
    if sub_payload is not None and not isinstance(sub_payload, dict):
        sub_payload = {"value": sub_payload}
    return broker.handle_command(mission_id, command, sub_payload)


__all__ = ["parse_client_command", "process_client_message"]
