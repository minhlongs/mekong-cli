"""Typed models for persistent autonomous goals."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _now() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GoalStatus(str, Enum):
    CREATED = "created"
    PLANNED = "planned"
    RUNNING = "running"
    VERIFYING = "verifying"
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class AgentRole(str, Enum):
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    INFRA = "infra"
    QA = "qa"
    SECURITY = "security"
    DOCS = "docs"
    QUANT = "quant"
    REVIEWER = "reviewer"


@dataclass
class AcceptanceCriterion:
    id: str
    description: str
    satisfied: bool = False
    evidence: str = ""


@dataclass
class Goal:
    id: str
    title: str
    status: GoalStatus = GoalStatus.CREATED
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    retry_limit: int = 3
    stop_conditions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalTask:
    id: str
    goal_id: str
    title: str
    description: str
    role: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3
    command: str | None = None
    result_summary: str = ""
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)


class TaskGraph:
    def __init__(self, goal_id: str, tasks: list[GoalTask]) -> None:
        self.goal_id = goal_id
        self.tasks = tasks

    @staticmethod
    def _is_terminal(status: TaskStatus) -> bool:
        return status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
            TaskStatus.SKIPPED,
        )

    def _get_task(self, task_id: str) -> GoalTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def ready_tasks(self) -> list[GoalTask]:
        completed = {task.id for task in self.tasks if task.status == TaskStatus.COMPLETED}
        return [
            task
            for task in self.tasks
            if task.status == TaskStatus.PENDING
            and all(dep in completed for dep in task.depends_on)
        ]


@dataclass
class Checkpoint:
    id: str
    goal_id: str
    task_id: str | None
    label: str
    state: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_now)


@dataclass
class VerificationRun:
    id: str
    goal_id: str
    profile: str
    passed: bool
    results: list[dict[str, Any]]
    created_at: float = field(default_factory=_now)
