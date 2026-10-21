"""Plan phase implementation for PEVSwarmBridge."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Optional
import uuid

from .constants import _utc_now_iso
from .models import MissionStatus, PevPlan

if TYPE_CHECKING:
    from .bridge import PEVSwarmBridge


def plan_impl(
    bridge: "PEVSwarmBridge", goal: str, mission_id: Optional[str] = None
) -> PevPlan:
    """Decompose a high-level goal into structured tasks with subagent assignments."""
    clean_goal = (goal or "").strip()
    if not clean_goal:
        raise ValueError("Goal cannot be empty")

    mid = mission_id or f"m_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    now = _utc_now_iso()

    tasks = bridge._decompose_goal(clean_goal, mid, now)
    subagent_assignments: dict[str, dict[str, Any]] = {}

    for t in tasks:
        if t.role not in subagent_assignments:
            subagent_assignments[t.role] = bridge._build_subagent_payload(
                role=t.role,
                task_desc=f"Execute task: {t.title}. {t.description}",
                context_budget=t.context_budget,
                allowed_tools=t.allowed_tools,
            )

    pev_plan = PevPlan(
        goal=clean_goal,
        mission_id=mid,
        tasks=tasks,
        subagent_assignments=subagent_assignments,
        metadata={"created_at": now, "engine": "PEVSwarmBridge", "version": "1.0.0"},
    )

    with bridge.store._connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO missions (
                mission_id, goal, status, cycle, max_cycles, plan_json,
                created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mid,
                clean_goal,
                MissionStatus.CREATED.value,
                1,
                3,
                json.dumps(pev_plan.to_dict()),
                now,
                now,
                json.dumps({"total_tasks": len(tasks)}),
            ),
        )

        for t in tasks:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks (
                    task_id, mission_id, order_idx, title, description,
                    role, phase, status, depends_on, context_budget,
                    allowed_tools, verification_criteria, attempts,
                    max_attempts, result_summary, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t.task_id,
                    t.mission_id,
                    t.order_idx,
                    t.title,
                    t.description,
                    t.role,
                    t.phase.value,
                    t.status.value,
                    json.dumps(t.depends_on),
                    t.context_budget,
                    json.dumps(t.allowed_tools),
                    json.dumps(t.verification_criteria.to_dict()),
                    t.attempts,
                    t.max_attempts,
                    t.result_summary,
                    t.created_at,
                    t.updated_at,
                ),
            )
        conn.commit()

    return pev_plan
