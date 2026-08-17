# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Buzz Adapter — v0.1 integration between Buzz goals and MekongCoreRuntime.

Receives goal payloads from Buzz, parses them into runtime-compatible dicts,
and sends status updates back. No Buzz hardcoding — protocol-driven.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BuzzPayload:
    """Parsed representation of a Buzz webhook payload."""

    goal_text: str
    context: dict[str, Any] = field(default_factory=dict)
    callback_url: str | None = None
    mission_id: str | None = None


class BuzzAdapter:
    """Receives goals from Buzz and feeds them into MekongCoreRuntime."""

    def __init__(self, runtime: Any | None = None) -> None:
        self._runtime = runtime

    @property
    def runtime(self) -> Any:
        return self._runtime

    @runtime.setter
    def runtime(self, value: Any) -> None:
        self._runtime = value

    def receive_goal(self, payload: dict) -> dict:
        """Parse Buzz webhook payload into a Goal dict for runtime.run().

        Accepts either ``{"goal": "..."}`` or ``{"text": "..."}`` as the
        primary goal field.
        """
        bp = BuzzPayload(
            goal_text=payload.get("goal", payload.get("text", "")),
            context=payload.get("context", {}),
            callback_url=payload.get("callback_url"),
            mission_id=payload.get("mission_id"),
        )
        if not bp.goal_text:
            raise ValueError("Buzz payload missing 'goal' field")
        return {
            "text": bp.goal_text,
            "context": bp.context,
            "mission_id": bp.mission_id,
            "callback_url": bp.callback_url,
        }

    def send_update(self, status: str, data: dict) -> dict:
        """Build a status update dict destined for the Buzz callback URL."""
        return {"status": status, "data": data}

    def receive_feedback(self, feedback: dict) -> dict:
        """Parse feedback from Buzz for plan adaptation."""
        return feedback


__all__ = ["BuzzAdapter", "BuzzPayload"]
