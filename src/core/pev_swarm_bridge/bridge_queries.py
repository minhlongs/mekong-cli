"""Mission status and task database query helpers for PEVSwarmBridge."""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import TYPE_CHECKING, Any, Optional

from .constants import _utc_now_iso
from .models import PevTask, TaskStatus

if TYPE_CHECKING:
    from .bridge import PEVSwarmBridge

logger = logging.getLogger(__name__)


def get_mission_status_impl(bridge: "PEVSwarmBridge", mission_id: str) -> dict[str, Any]:
    """Query high-level status, tasks, checkpoints, and verification runs for a mission."""
    with bridge.store._connect() as conn:
        m_row = conn.execute(
            "SELECT * FROM missions WHERE mission_id = ?", (mission_id,)
        ).fetchone()
        if not m_row:
            return {"ok": False, "error": f"Mission {mission_id} not found"}

        t_rows = conn.execute(
            "SELECT * FROM tasks WHERE mission_id = ? ORDER BY order_idx ASC",
            (mission_id,),
        ).fetchall()

        v_rows = conn.execute(
            "SELECT * FROM verification_runs WHERE mission_id = ? ORDER BY created_at DESC",
            (mission_id,),
        ).fetchall()

        cp_rows = conn.execute(
            "SELECT checkpoint_id, phase, label, created_at FROM checkpoints "
            "WHERE mission_id = ? ORDER BY created_at DESC",
            (mission_id,),
        ).fetchall()

        tasks_list = []
        for tr in t_rows:
            tasks_list.append(
                {
                    "task_id": tr["task_id"],
                    "order_idx": tr["order_idx"],
                    "title": tr["title"],
                    "role": tr["role"],
                    "phase": tr["phase"],
                    "status": tr["status"],
                    "attempts": tr["attempts"],
                    "max_attempts": tr["max_attempts"],
                    "result_summary": tr["result_summary"],
                }
            )

        verification_list = []
        for vr in v_rows:
            try:
                checks = json.loads(vr["checks_json"]) if vr["checks_json"] else []
            except (json.JSONDecodeError, ValueError):
                checks = []
            verification_list.append(
                {
                    "id": vr["id"],
                    "task_id": vr["task_id"],
                    "cycle": vr["cycle"],
                    "verifier_role": vr["verifier_role"],
                    "passed": bool(vr["passed"]),
                    "checks": checks,
                    "created_at": vr["created_at"],
                }
            )

        checkpoints_list = [dict(cr) for cr in cp_rows]

        return {
            "ok": True,
            "mission_id": m_row["mission_id"],
            "goal": m_row["goal"],
            "status": m_row["status"],
            "cycle": m_row["cycle"],
            "max_cycles": m_row["max_cycles"],
            "created_at": m_row["created_at"],
            "updated_at": m_row["updated_at"],
            "tasks": tasks_list,
            "checkpoints": checkpoints_list,
            "verification_runs": verification_list,
        }


def get_task_impl(bridge: "PEVSwarmBridge", task_id: str) -> Optional[PevTask]:
    """Fetch task from SQLite store."""
    try:
        with bridge.store._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            try:
                data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
            except (json.JSONDecodeError, ValueError):
                data["depends_on"] = []
            try:
                data["allowed_tools"] = (
                    json.loads(data["allowed_tools"]) if data["allowed_tools"] else []
                )
            except (json.JSONDecodeError, ValueError):
                data["allowed_tools"] = []
            try:
                data["verification_criteria"] = (
                    json.loads(data["verification_criteria"])
                    if data["verification_criteria"]
                    else {}
                )
            except (json.JSONDecodeError, ValueError):
                data["verification_criteria"] = {}
            return PevTask.from_dict(data)
    except (sqlite3.Error, OSError, ValueError) as exc:
        logger.warning("Failed to load task %s: %s", task_id, exc)
        return None


def update_task_status_impl(bridge: "PEVSwarmBridge", task_id: str, status: TaskStatus) -> None:
    """Update task status in SQLite store."""
    now = _utc_now_iso()
    with bridge.store._connect() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
            (status.value, now, task_id),
        )
        conn.commit()
