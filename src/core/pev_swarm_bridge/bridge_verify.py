"""Verify phase implementation and independent verifier selection for PEVSwarmBridge."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Optional
import uuid

from .bridge_verify_checks import evaluate_verification_criteria
from .constants import ROLE_CONTEXT_BUDGETS, ROLE_TOOL_ALLOWLISTS, _utc_now_iso
from .models import MissionStatus, TaskStatus

if TYPE_CHECKING:
    from .bridge import PEVSwarmBridge


def select_independent_verifier(worker_role: str) -> str:
    """Enforce Rule of Independence: verifier role must be distinct from worker."""
    if worker_role in ("eng", "fullstack-developer", "debugger", "code-simplifier"):
        return "tester"
    if worker_role in ("tester", "qa"):
        return "code-reviewer"
    if worker_role in ("pm", "planner", "project-manager"):
        return "cto"
    if worker_role in ("cto", "architect"):
        return "sun-tzu"
    if worker_role in ("cso", "sec"):
        return "code-reviewer"
    return "code-reviewer"


def find_latest_checkpoint(
    bridge: "PEVSwarmBridge",
    mission_id: str,
    task_id: Optional[str] = None,
    phase: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Query the latest checkpoint matching criteria."""
    with bridge.store._connect() as conn:
        query = "SELECT * FROM checkpoints WHERE mission_id = ?"
        params: list[Any] = [mission_id]
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if phase:
            query += " AND phase = ?"
            params.append(phase)
        query += " ORDER BY created_at DESC LIMIT 1"
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def verify_task_impl(
    bridge: "PEVSwarmBridge",
    mission_id: str,
    task_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Dispatch independent verifier subagent with read-only tools to evaluate deliverables."""
    task = bridge.get_task(task_id)
    if not task:
        return {"ok": False, "error": f"Task {task_id} not found in database"}

    verifier_role = bridge._select_independent_verifier(task.role)
    verifier_budget = ROLE_CONTEXT_BUDGETS.get(verifier_role, 16000)
    verifier_tools = [
        t
        for t in ROLE_TOOL_ALLOWLISTS.get(verifier_role, ["Read", "Bash", "Task"])
        if t not in ("Write", "Edit")
    ]

    checks, all_passed = evaluate_verification_criteria(
        task.verification_criteria, bridge.project_root, dry_run=dry_run
    )

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "mission_id": mission_id,
            "task_id": task_id,
            "verifier_role": verifier_role,
            "verifier_budget": verifier_budget,
            "allowed_tools": verifier_tools,
            "checks": checks,
            "passed": all_passed,
        }

    now = _utc_now_iso()
    run_id = f"vr_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    with bridge.store._connect() as conn:
        m_cur = conn.execute(
            "SELECT cycle FROM missions WHERE mission_id = ?", (mission_id,)
        ).fetchone()
        cycle = m_cur["cycle"] if m_cur else 1

        conn.execute(
            """
            INSERT INTO verification_runs (
                id, mission_id, task_id, cycle, verifier_role,
                passed, checks_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, mission_id, task_id, cycle, verifier_role, 1 if all_passed else 0, json.dumps(checks), now),
        )
        conn.commit()

    if all_passed:
        post_v_cp = bridge.store.capture_checkpoint(
            mission_id=mission_id,
            label=f"Post-verify passed: {task.title}",
            task_id=task_id,
            phase="post_verify",
            test_results=checks,
            project_root=bridge.project_root,
        )
        return {
            "ok": True,
            "passed": True,
            "verifier_role": verifier_role,
            "checks": checks,
            "post_checkpoint_id": post_v_cp,
        }

    new_attempts = task.attempts + 1
    with bridge.store._connect() as conn:
        conn.execute(
            "UPDATE tasks SET attempts = ?, updated_at = ? WHERE task_id = ?",
            (new_attempts, now, task_id),
        )
        conn.commit()

    pre_cp = bridge._find_latest_checkpoint(mission_id, task_id, phase="pre_execute")
    rollback_info = (
        bridge.store.rollback_to_checkpoint(pre_cp["checkpoint_id"], project_root=bridge.project_root)
        if pre_cp
        else None
    )

    if new_attempts < task.max_attempts:
        bridge._update_task_status(task_id, TaskStatus.PENDING)
        return {
            "ok": False,
            "passed": False,
            "rolled_back": bool(rollback_info and rollback_info.get("ok", False)),
            "attempts": new_attempts,
            "max_attempts": task.max_attempts,
            "rollback_checkpoint": pre_cp["checkpoint_id"] if pre_cp else None,
            "rollback_details": rollback_info,
            "checks": checks,
        }

    bridge._update_task_status(task_id, TaskStatus.FAILED)
    with bridge.store._connect() as conn:
        conn.execute(
            "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
            (MissionStatus.FAILED.value, now, mission_id),
        )
        conn.commit()

    return {
        "ok": False,
        "passed": False,
        "rolled_back": bool(rollback_info and rollback_info.get("ok", False)),
        "escalated": True,
        "attempts": new_attempts,
        "max_attempts": task.max_attempts,
        "error": "Verification failed: maximum repair attempts exceeded",
        "rollback_details": rollback_info,
        "checks": checks,
    }
