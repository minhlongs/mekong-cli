"""
Vibe Coding Factory — Lineage Tracker.

Records command execution chains across factory layers and provides
forward/backward tracing for session history stored as JSON.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LINEAGE_DIR = Path.home() / ".mekong" / "lineage"


def _ensure_lineage_dir() -> None:
    """Create lineage storage directory if it does not exist."""
    _LINEAGE_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    """Return the JSON file path for a given session."""
    return _LINEAGE_DIR / f"{session_id}.json"


def _load_session(session_id: str) -> dict:
    """Load session data from disk, returning empty structure if missing."""
    path = _session_path(session_id)
    if not path.exists():
        return {"session_id": session_id, "steps": []}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load lineage session %s: %s", session_id, exc)
        return {"session_id": session_id, "steps": []}


def _save_session(session_id: str, data: dict) -> None:
    """Persist session data to disk."""
    _ensure_lineage_dir()
    path = _session_path(session_id)
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        logger.error("Failed to save lineage session %s: %s", session_id, exc)


class LineageTracker:
    """
    Tracks and traces command execution chains across factory layers.

    Each step records the layer, command, timestamp, and optional parent
    command that triggered it. Steps are persisted per session as JSON
    under ~/.mekong/lineage/{session_id}.json.
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id: str = session_id or str(uuid.uuid4())

    def record(
        self,
        layer: str,
        command: str,
        output_summary: str,
        triggered_by: Optional[str] = None,
    ) -> str:
        """
        Append a command execution step to the session lineage.

        Args:
            layer: Factory layer name (founder, business, product, engineering, ops).
            command: The command that was executed.
            output_summary: Brief summary of the command output.
            triggered_by: Command ID of the parent step, if cascade-triggered.

        Returns:
            The generated step ID.
        """
        step_id = str(uuid.uuid4())[:8]
        session = _load_session(self.session_id)
        session["steps"].append(
            {
                "id": step_id,
                "layer": layer,
                "command": command,
                "output_summary": output_summary,
                "triggered_by": triggered_by,
                "timestamp": time.time(),
            }
        )
        _save_session(self.session_id, session)
        logger.debug("Recorded step %s: %s/%s", step_id, layer, command)
        return step_id

    def trace_forward(self, command_id: str) -> list[dict]:
        """
        Return all steps triggered (directly or indirectly) by command_id.

        Args:
            command_id: The step ID to trace forward from.

        Returns:
            Ordered list of descendant step dicts.
        """
        session = _load_session(self.session_id)
        steps = session.get("steps", [])
        return [s for s in steps if s.get("triggered_by") == command_id]

    def trace_backward(self, command_id: str) -> list[dict]:
        """
        Return the ancestor chain leading to command_id.

        Args:
            command_id: The step ID to trace backward from.

        Returns:
            Ordered list of ancestor step dicts (oldest first).
        """
        session = _load_session(self.session_id)
        steps_by_id = {s["id"]: s for s in session.get("steps", [])}

        ancestors: list[dict] = []
        current_id: Optional[str] = command_id
        while current_id:
            step = steps_by_id.get(current_id)
            if step is None:
                break
            ancestors.append(step)
            current_id = step.get("triggered_by")

        ancestors.reverse()
        return ancestors

    def get_session(self) -> dict:
        """Return the full session lineage data."""
        return _load_session(self.session_id)
