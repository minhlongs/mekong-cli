"""Execute phase implementation for PEVSwarmBridge."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .constants import _utc_now_iso
from .models import TaskStatus

if TYPE_CHECKING:
    from .bridge import PEVSwarmBridge


def execute_task_impl(
    bridge: "PEVSwarmBridge",
    mission_id: str,
    task_id: str,
    dry_run: bool = False,
    files: Optional[list[str | Path]] = None,
) -> dict[str, Any]:
    """Execute or preview an individual task within a mission."""
    task = bridge.get_task(task_id)
    if not task:
        return {"ok": False, "error": f"Task {task_id} not found in database"}

    if task.depends_on:
        with bridge.store._connect() as conn:
            placeholders = ",".join("?" for _ in task.depends_on)
            rows = conn.execute(
                f"SELECT task_id, status FROM tasks WHERE task_id IN ({placeholders})",
                task.depends_on,
            ).fetchall()
            statuses = {r["task_id"]: r["status"] for r in rows}
            unmet = [
                dep
                for dep in task.depends_on
                if statuses.get(dep) != TaskStatus.COMPLETED.value
            ]
            if unmet:
                bridge._update_task_status(task_id, TaskStatus.BLOCKED)
                return {
                    "ok": False,
                    "status": TaskStatus.BLOCKED.value,
                    "error": f"Prerequisite tasks not completed: {unmet}",
                }

    worker_payload = bridge._build_subagent_payload(
        role=task.role,
        task_desc=f"{task.title}: {task.description}",
        context_budget=task.context_budget,
        allowed_tools=task.allowed_tools,
    )

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "mission_id": mission_id,
            "task_id": task_id,
            "title": task.title,
            "role": task.role,
            "context_budget": task.context_budget,
            "allowed_tools": task.allowed_tools,
            "payload": worker_payload,
        }

    snapshot_files: list[str | Path] = []
    if files:
        snapshot_files.extend(files)
    if task.verification_criteria.file_exists:
        for fe in task.verification_criteria.file_exists:
            fp = (bridge.project_root / fe).resolve()
            if fp.is_file():
                snapshot_files.append(fp)

    pre_cp_id = bridge.store.capture_checkpoint(
        mission_id=mission_id,
        label=f"Pre-execute: {task.title}",
        task_id=task_id,
        phase="pre_execute",
        files=snapshot_files if snapshot_files else None,
        project_root=bridge.project_root,
    )

    bridge._update_task_status(task_id, TaskStatus.RUNNING)

    now = _utc_now_iso()
    summary = f"Executed {task.title} by role {task.role} at {now}"

    with bridge.store._connect() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = ?, result_summary = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (TaskStatus.COMPLETED.value, summary, now, task_id),
        )
        conn.commit()

    post_cp_id = bridge.store.capture_checkpoint(
        mission_id=mission_id,
        label=f"Post-execute: {task.title}",
        task_id=task_id,
        phase="post_execute",
        project_root=bridge.project_root,
    )

    return {
        "ok": True,
        "mission_id": mission_id,
        "task_id": task_id,
        "status": TaskStatus.COMPLETED.value,
        "role": task.role,
        "context_budget": task.context_budget,
        "pre_checkpoint_id": pre_cp_id,
        "post_checkpoint_id": post_cp_id,
        "subagent_payload": worker_payload,
    }
