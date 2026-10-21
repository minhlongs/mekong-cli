# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Control command handler logic for MissionStreamingBroker."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .streaming_types import ControlCommand, StreamEventType

if TYPE_CHECKING:
    from .streaming_broker import MissionStreamingBroker


def handle_mission_command(
    broker: MissionStreamingBroker,
    mission_id: str,
    command: str,
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Execute a mission control command and publish the acknowledgment."""
    cmd_clean = command.strip().lower()
    ctrl = broker.get_mission_control(mission_id)

    if cmd_clean == ControlCommand.PAUSE.value:
        ctrl.pause()
        status = "paused"
    elif cmd_clean == ControlCommand.RESUME.value:
        ctrl.resume()
        status = "resumed"
    elif cmd_clean == ControlCommand.CANCEL.value:
        ctrl.cancel()
        status = "cancelled"
    else:
        return {
            "ok": False,
            "error": f"Unknown or unsupported command '{command}'",
            "mission_id": mission_id,
        }

    ack_data = {
        "command": cmd_clean,
        "status": status,
        "mission_id": mission_id,
        "payload": payload or {},
    }
    broker.publish(mission_id, StreamEventType.COMMAND_ACK, ack_data)

    return {
        "ok": True,
        "command": cmd_clean,
        "status": status,
        "mission_id": mission_id,
        "payload": payload or {},
    }


__all__ = ["handle_mission_command"]
