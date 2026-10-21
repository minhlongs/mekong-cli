# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BuzzRuntimeAdapter — versioned in-process facade over MekongCoreRuntime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Callable
import uuid

from src.core.buzz_adapter import BuzzAdapter, BuzzConfigError

logger = logging.getLogger(__name__)
Approver = Callable[[str, str], bool]


@dataclass
class _Session:
    """In-process session bookkeeping."""
    session_id: str
    goal_hint: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "open"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_mission_id: str | None = None


class BuzzRuntimeAdapter:
    """Versioned v0.1 interface between Buzz and the core runtime."""

    INTERFACE_VERSION = "v0.1"

    def __init__(
        self, runtime: Any | None = None, tracer: Any | None = None,
        transport: Any | None = None, approver: Approver | None = None,
    ) -> None:
        self._runtime = runtime
        self._buzz = BuzzAdapter(transport=transport)
        self._tracer = tracer
        self._approver = approver
        self._sessions: dict[str, _Session] = {}

    @property
    def interface_version(self) -> str:
        return self.INTERFACE_VERSION

    def start_session(
        self, goal_hint: str = "", session_id: str | None = None, metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sid = session_id or f"session_{uuid.uuid4().hex[:8]}"
        if sid in self._sessions:
            raise ValueError(f"session already open: {sid}")
        self._sessions[sid] = _Session(session_id=sid, goal_hint=goal_hint, metadata=metadata or {})
        return self.session_info(sid)

    def stop_session(self, session_id: str) -> dict[str, Any]:
        record = self._sessions.get(session_id)
        if record is not None:
            record.status = "closed"
            return self.session_info(session_id)
        logger.info("stop_session ignored unknown session %s", session_id)
        return {"session_id": session_id, "status": "unknown", "interface_version": self.INTERFACE_VERSION}

    def session_info(self, session_id: str) -> dict[str, Any]:
        record = self._sessions.get(session_id)
        if record is None:
            return {"session_id": session_id, "status": "unknown", "interface_version": self.INTERFACE_VERSION}
        return {
            "interface_version": self.INTERFACE_VERSION, "session_id": record.session_id,
            "status": record.status, "goal_hint": record.goal_hint,
            "metadata": dict(record.metadata), "created_at": record.created_at,
            "last_mission_id": record.last_mission_id,
        }

    def assign_mission(self, payload: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
        """Run a mission from a Buzz-shaped payload through the core runtime.

        Every mission starts from a clean cancel flag, and a ``mission_id``
        supplied by the caller is honored so it can correlate the trace and
        poll status afterwards.
        """
        if self._runtime is None:
            raise BuzzConfigError("BuzzRuntimeAdapter has no runtime wired")
        parsed_callback = payload.get("callback_url")
        goal_text = payload.get("goal") or payload.get("text") or ""
        # Bound before the try so a crash mid-mission still reports the id
        # assigned by start_mission rather than silently dropping it.
        mission_id: str | None = payload.get("mission_id")
        try:
            if goal_text == "":
                raise BuzzConfigError("Buzz payload missing 'goal' field")
            self._reset_cancel_flag()
            self._runtime.start_mission(goal_text, tracer=self._tracer, mission_id=mission_id)
            result = self._runtime.run_from_payload(payload)
            mission_id = getattr(self._runtime, "_mission_id", None) or mission_id
            cancelled = bool(result.metadata.get("cancelled"))
            outcome = "completed" if result.error is None else ("cancelled" if cancelled else "failed")
            data: dict[str, Any] = {
                "output": result.output, "error": result.error,
                "task_id": result.task_id, "interface_version": self.INTERFACE_VERSION,
            }
            if cancelled:
                data["cancelled"] = True
        except Exception as exc:
            logger.error("Mission execution crashed: %s", exc)
            outcome = "failed"
            data = {"error": str(exc), "interface_version": self.INTERFACE_VERSION}
        if session_id and session_id in self._sessions:
            self._sessions[session_id].last_mission_id = mission_id
        self._buzz.send_update(outcome, data, callback_url=parsed_callback)
        return {"interface_version": self.INTERFACE_VERSION, "mission_id": mission_id, "status": outcome, "data": data, **data}

    def stream_event(self, event: str, data: dict[str, Any], callback_url: str | None = None) -> dict[str, Any]:
        return self._buzz.send_update(event, data, callback_url=callback_url)

    def request_approval(self, goal: str, reason: str = "") -> bool:
        if self._approver is None:
            logger.warning("Approval requested for '%s' but no approver wired — denied", goal)
            return False
        try:
            return bool(self._approver(goal, reason))
        except Exception as exc:
            logger.error("Approver raised for '%s': %s — denying", goal, exc)
            return False

    def cancel_mission(self) -> dict[str, Any]:
        """Request cooperative cancellation of the active mission.

        The latch is one-shot: ``assign_mission`` clears it at the start of
        the next mission, so a cancelled mission never poisons the missions
        that follow it on the same runtime.
        """
        if self._runtime is None:
            return {"cancelled": False, "reason": "no runtime"}
        setattr(self._runtime, "_cancel_requested", True)
        return {"cancelled": True, "mission_id": getattr(self._runtime, "_mission_id", None)}

    def _reset_cancel_flag(self) -> None:
        """Clear the cooperative cancel flag at the mission boundary.

        Done in ``assign_mission`` *before* ``start_mission`` so a cancel
        that raced the new mission's start cannot pre-cancel it.
        """
        if self._runtime is not None:
            setattr(self._runtime, "_cancel_requested", False)

    def get_status(self, mission_id: str | None = None) -> dict[str, Any]:
        if self._tracer is not None and mission_id is not None:
            record = self._tracer.get_mission(mission_id)
            if record is not None:
                return {
                    "interface_version": self.INTERFACE_VERSION, "mission_id": record.mission_id,
                    "status": record.status, "step_count": len(record.steps), "goal": record.goal,
                    "created_at": record.created_at, "completed_at": record.completed_at,
                }
        if mission_id is None and self._runtime is not None:
            active = getattr(self._runtime, "_mission_id", None)
            return {"interface_version": self.INTERFACE_VERSION, "mission_id": active, "status": "running" if active else "idle"}
        return {"interface_version": self.INTERFACE_VERSION, "mission_id": mission_id, "status": "unknown"}

    def get_artifacts(self, mission_id: str | None = None) -> list[dict[str, Any]]:
        if self._tracer is None or mission_id is None:
            return []
        record = self._tracer.get_mission(mission_id)
        if record is None:
            return []
        return [{"step": s.get("step"), "timestamp": s.get("timestamp"), "result": s.get("result")} for s in record.steps]


__all__ = ["BuzzRuntimeAdapter"]
