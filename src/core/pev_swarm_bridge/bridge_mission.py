"""Swarm mission cycle runner for PEVSwarmBridge."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .constants import _utc_now_iso
from .models import MissionStatus, TaskStatus

if TYPE_CHECKING:
    from .bridge import PEVSwarmBridge

logger = logging.getLogger(__name__)


def run_mission_impl(
    bridge: "PEVSwarmBridge",
    goal: str,
    max_cycles: int = 3,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute full PEV cycle: Plan -> Execute -> Verify with auto-rollback."""
    plan = bridge.plan(goal)
    mid = plan.mission_id

    if dry_run:
        task_previews = []
        for t in plan.tasks:
            exec_prev = bridge.execute_task(mid, t.task_id, dry_run=True)
            veri_prev = bridge.verify_task(mid, t.task_id, dry_run=True)
            task_previews.append(
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "role": t.role,
                    "phase": t.phase.value,
                    "context_budget": t.context_budget,
                    "allowed_tools": t.allowed_tools,
                    "execution_preview": exec_prev,
                    "verification_preview": veri_prev,
                }
            )

        return {
            "ok": True,
            "dry_run": True,
            "mission_id": mid,
            "goal": goal,
            "total_tasks": len(plan.tasks),
            "tasks": task_previews,
            "subagent_assignments": plan.subagent_assignments,
        }

    now = _utc_now_iso()
    with bridge.store._connect() as conn:
        conn.execute(
            "UPDATE missions SET status = ?, max_cycles = ?, updated_at = ? WHERE mission_id = ?",
            (MissionStatus.EXECUTING.value, max_cycles, now, mid),
        )
        conn.commit()

    executed_tasks: list[dict[str, Any]] = []

    for task in plan.tasks:
        task_success = False
        while True:
            exec_result = bridge.execute_task(mid, task.task_id, dry_run=False)
            if not exec_result.get("ok"):
                return {
                    "ok": False,
                    "mission_id": mid,
                    "failed_stage": "execute",
                    "task_id": task.task_id,
                    "error": exec_result.get("error"),
                }

            verify_result = bridge.verify_task(mid, task.task_id, dry_run=False)
            if verify_result.get("passed"):
                task_success = True
                executed_tasks.append(
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "role": task.role,
                        "status": TaskStatus.COMPLETED.value,
                        "checks": verify_result.get("checks"),
                    }
                )
                break

            if verify_result.get("escalated"):
                return {
                    "ok": False,
                    "mission_id": mid,
                    "failed_stage": "verify",
                    "task_id": task.task_id,
                    "attempts": verify_result.get("attempts"),
                    "error": verify_result.get("error"),
                    "checks": verify_result.get("checks"),
                }

            logger.info(
                "Retrying task %s after rollback (attempt %s)",
                task.task_id,
                verify_result.get("attempts"),
            )

        if not task_success:
            break

    now_done = _utc_now_iso()
    with bridge.store._connect() as conn:
        conn.execute(
            "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
            (MissionStatus.COMPLETED.value, now_done, mid),
        )
        conn.commit()

    final_cp = bridge.store.capture_checkpoint(
        mission_id=mid,
        label="Mission completed",
        phase="mission_complete",
        project_root=bridge.project_root,
    )

    return {
        "ok": True,
        "mission_id": mid,
        "status": MissionStatus.COMPLETED.value,
        "goal": goal,
        "executed_tasks": executed_tasks,
        "final_checkpoint_id": final_cp,
    }
