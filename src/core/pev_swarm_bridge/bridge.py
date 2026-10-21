"""Unified PEVSwarmBridge orchestrator class."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .bridge_exec import execute_task_impl
from .bridge_mission import run_mission_impl
from .bridge_plan import plan_impl
from .bridge_queries import get_mission_status_impl, get_task_impl, update_task_status_impl
from .bridge_verify import (
    find_latest_checkpoint,
    select_independent_verifier,
    verify_task_impl,
)
from .checkpoint_store import CheckpointStore
from .models import PevPlan, PevTask, TaskStatus
from .plan_heuristics_ext import build_subagent_payload_impl, decompose_goal_impl


class PEVSwarmBridge:
    """Unified bridge orchestrating Plan -> Execute -> Verify cycles."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        if db_path is None:
            db_path = self.project_root / ".mekong" / "pev_checkpoints.db"
        self.store = CheckpointStore(db_path)

    def plan(self, goal: str, mission_id: Optional[str] = None) -> PevPlan:
        """Decompose a high-level goal into structured tasks with subagent assignments."""
        return plan_impl(self, goal, mission_id=mission_id)

    def _decompose_goal(self, goal: str, mission_id: str, timestamp: str) -> list[PevTask]:
        """Heuristically decompose goal into structured DAG tasks with 25-subagent roles."""
        return decompose_goal_impl(goal, mission_id, timestamp, self.project_root)

    def _build_subagent_payload(
        self,
        role: str,
        task_desc: str,
        context_budget: int,
        allowed_tools: list[str],
    ) -> dict[str, Any]:
        """Construct Antigravity define_subagent, invoke_subagent, and context payload."""
        return build_subagent_payload_impl(
            role=role,
            task_desc=task_desc,
            context_budget=context_budget,
            allowed_tools=allowed_tools,
            project_root=self.project_root,
        )

    def execute_task(
        self,
        mission_id: str,
        task_id: str,
        dry_run: bool = False,
        files: Optional[list[str | Path]] = None,
    ) -> dict[str, Any]:
        """Execute or preview an individual task within a mission."""
        return execute_task_impl(self, mission_id, task_id, dry_run=dry_run, files=files)

    def verify_task(
        self,
        mission_id: str,
        task_id: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Dispatch independent verifier subagent with read-only tools to evaluate deliverables."""
        return verify_task_impl(self, mission_id, task_id, dry_run=dry_run)

    def _select_independent_verifier(self, worker_role: str) -> str:
        """Enforce Rule of Independence: verifier role must be distinct from worker."""
        return select_independent_verifier(worker_role)

    def _find_latest_checkpoint(
        self,
        mission_id: str,
        task_id: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Query the latest checkpoint matching criteria."""
        return find_latest_checkpoint(self, mission_id, task_id=task_id, phase=phase)

    def run_mission(
        self,
        goal: str,
        max_cycles: int = 3,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Execute full PEV cycle: Plan -> Execute -> Verify with auto-rollback."""
        return run_mission_impl(self, goal, max_cycles=max_cycles, dry_run=dry_run)

    def get_mission_status(self, mission_id: str) -> dict[str, Any]:
        """Query high-level status, tasks, checkpoints, and verification runs for a mission."""
        return get_mission_status_impl(self, mission_id)

    def get_task(self, task_id: str) -> Optional[PevTask]:
        """Fetch task from SQLite store."""
        return get_task_impl(self, task_id)

    def _update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status in SQLite store."""
        update_task_status_impl(self, task_id, status)
