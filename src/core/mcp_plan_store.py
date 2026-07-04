"""Mekong MCP Plan Store — JSON-backed plan persistence with goal decomposition."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path.home() / ".mekong"
_DEFAULT_PATH = _DEFAULT_DIR / "mcp_plans.json"

PLAN_STATUSES = ("active", "completed")


class McpPlan:
    """A plan with decomposed tasks."""

    def __init__(
        self,
        plan_id: str,
        goal: str,
        tasks: list[dict[str, str]] | None = None,
        status: str = "active",
        created_at: str | None = None,
        completed_at: str | None = None,
    ) -> None:
        self.plan_id = plan_id
        self.goal = goal
        self.tasks = tasks or []
        self.status = status if status in PLAN_STATUSES else "active"
        self.created_at = created_at or _now()
        self.completed_at = completed_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "tasks": self.tasks,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "McpPlan":
        plan_id = d.get("plan_id", "")
        goal = d.get("goal", "")
        if not plan_id or not goal:
            raise ValueError(f"Missing plan_id or goal in plan data: {d}")
        return cls(
            plan_id=plan_id,
            goal=goal,
            tasks=d.get("tasks", []),
            status=d.get("status", "active"),
            created_at=d.get("created_at"),
            completed_at=d.get("completed_at"),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    return uuid.uuid4().hex[:12]


def _decompose_goal(goal: str) -> list[dict[str, str]]:
    """Split a goal description into logical sub-tasks.

    Uses simple heuristics: splits on bullet points, numbered lists,
    semicolons, or natural conjunction patterns.
    """
    goal = goal.strip()
    if not goal:
        return []

    lines = [line.strip() for line in goal.replace("\r", "").split("\n") if line.strip()]
    segments: list[str] = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            segments.append(stripped[2:])
        elif stripped[0].isdigit() and ". " in stripped[:4]:
            segments.append(stripped.split(". ", 1)[1])
        else:
            segments.append(stripped)

    if len(segments) <= 1:
        parts = goal.split(";")
        segments = [s.strip() for s in parts if s.strip()]

    if len(segments) <= 1:
        for conj in (" and then ", " then ", " followed by ", " afterwards "):
            if conj in goal:
                segments = [s.strip() for s in goal.split(conj)]
                break

    if len(segments) <= 1:
        segments = [goal]

    tasks = []
    for i, seg in enumerate(segments):
        tasks.append({
            "id": f"task-{i + 1}",
            "description": seg,
            "status": "todo",
        })
    return tasks


class McpPlanStore:
    """Thread-safe JSON-backed plan store for MCP tools."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else _DEFAULT_PATH
        self._lock = threading.Lock()
        self._plans: dict[str, McpPlan] = {}
        self._loaded = False
        self._dirty = False

    def create(self, goal: str) -> McpPlan:
        tasks = _decompose_goal(goal)
        plan = McpPlan(plan_id=_generate_id(), goal=goal, tasks=tasks)
        with self._lock:
            self._load()
            self._plans[plan.plan_id] = plan
            self._dirty = True
            self._save()
        return plan

    def get(self, plan_id: str) -> McpPlan | None:
        with self._lock:
            self._load()
            return self._plans.get(plan_id)

    def list(self, status: str = "") -> list[McpPlan]:
        with self._lock:
            self._load()
            plans = list(self._plans.values())
        if status:
            plans = [p for p in plans if p.status == status]
        return sorted(plans, key=lambda p: p.created_at, reverse=True)

    def complete(self, plan_id: str) -> McpPlan | None:
        with self._lock:
            self._load()
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            plan.status = "completed"
            plan.completed_at = _now()
            for t in plan.tasks:
                if t["status"] == "todo":
                    t["status"] = "done"
            self._dirty = True
            self._save()
        return plan

    def update_task_status(
        self, plan_id: str, task_id: str, status: str
    ) -> McpPlan | None:
        with self._lock:
            self._load()
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            for t in plan.tasks:
                if t["id"] == task_id:
                    t["status"] = status
                    t["updated_at"] = _now()
                    self._dirty = True
                    self._save()
                    return plan
        return None

    def delete(self, plan_id: str) -> bool:
        with self._lock:
            self._load()
            if plan_id not in self._plans:
                return False
            del self._plans[plan_id]
            self._dirty = True
            self._save()
        return True

    def stats(self) -> dict[str, int]:
        with self._lock:
            self._load()
            counts: dict[str, int] = {"total": len(self._plans)}
            for p in self._plans.values():
                counts[p.status] = counts.get(p.status, 0) + 1
        for s in PLAN_STATUSES:
            counts.setdefault(s, 0)
        return counts

    def _load(self) -> None:
        if self._loaded:
            return
        self._plans = {}
        try:
            if self._path.exists():
                raw = self._path.read_text(encoding="utf-8").strip()
                if raw:
                    data = json.loads(raw)
                    if isinstance(data, list):
                        for item in data:
                            try:
                                plan = McpPlan.from_dict(item)
                            except (KeyError, TypeError, ValueError) as exc:
                                logger.warning("Skipping malformed plan item: %s", exc)
                                continue
                            self._plans[plan.plan_id] = plan
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load MCP plans from %s: %s", self._path, exc)
        self._loaded = True

    def _save(self) -> None:
        if not self._dirty:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = [p.to_dict() for p in self._plans.values()]
            self._path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            self._dirty = False
        except OSError as exc:
            logger.warning("Failed to save MCP plans to %s: %s", self._path, exc)


_store: McpPlanStore | None = None


def get_plan_store(path: str | Path | None = None) -> McpPlanStore:
    global _store
    if _store is None:
        _store = McpPlanStore(path=path)
    return _store
