# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typed models for persistent autonomous goals, durable tickets, mandates, leases, and outbox."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


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


class ExecutionTruthStatus(str, Enum):
    """Canonical 12-state execution truth model preventing false-positive completion."""

    PLANNED = "PLANNED"
    SIMULATED = "SIMULATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RETRY_WAIT = "RETRY_WAIT"
    VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    UNAVAILABLE = "UNAVAILABLE"


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
    truth_status: ExecutionTruthStatus = ExecutionTruthStatus.PLANNED
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
    truth_status: ExecutionTruthStatus = ExecutionTruthStatus.PLANNED
    depends_on: list[str] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3
    command: str | None = None
    result_summary: str = ""
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    blocked_reason: str | None = None
    is_idempotent: bool = False
    side_effect_uncertain: bool = False
    mutates_workspace: bool = False
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)


# Alias for external contract compatibility
TaskRecord = GoalTask
GoalRecord = Goal


def compute_mandate_hash(
    *,
    ticket_id: str,
    source_id: str,
    event_id: str,
    requester: str,
    authorized_scope: str,
    workspace_id: str,
    mandate_version: int,
    policy_version: str,
    accepted_at: str,
    permitted_capabilities: tuple[str, ...],
    resource_boundaries: tuple[str, ...],
    risk_classification: str,
    cost_budget: float,
    retry_budget: int,
    verification_requirements: str,
    secret: str | None = None,
) -> str:
    """Compute deterministic HMAC-SHA256 digest over immutable mandate fields."""
    effective_secret = secret or os.environ.get(
        "MEKONG_MANDATE_HMAC_SECRET", "mekong-autonomous-mandate-v1"
    )
    payload = {
        "ticket_id": ticket_id,
        "source_id": source_id,
        "event_id": event_id,
        "requester": requester,
        "authorized_scope": authorized_scope,
        "workspace_id": workspace_id,
        "mandate_version": int(mandate_version),
        "policy_version": policy_version,
        "accepted_at": accepted_at,
        "permitted_capabilities": list(permitted_capabilities),
        "resource_boundaries": list(resource_boundaries),
        "risk_classification": risk_classification,
        "cost_budget": float(cost_budget),
        "retry_budget": int(retry_budget),
        "verification_requirements": verification_requirements,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        effective_secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()


@dataclass(frozen=True)
class ImmutableMandate:
    ticket_id: str
    source_id: str
    event_id: str
    requester: str
    authorized_scope: str
    workspace_id: str
    mandate_version: int
    policy_version: str
    accepted_at: str
    permitted_capabilities: tuple[str, ...]
    resource_boundaries: tuple[str, ...]
    risk_classification: str
    cost_budget: float
    retry_budget: int
    verification_requirements: str
    mandate_hash: str = ""

    def __post_init__(self) -> None:
        if not self.mandate_hash:
            computed = compute_mandate_hash(
                ticket_id=self.ticket_id,
                source_id=self.source_id,
                event_id=self.event_id,
                requester=self.requester,
                authorized_scope=self.authorized_scope,
                workspace_id=self.workspace_id,
                mandate_version=self.mandate_version,
                policy_version=self.policy_version,
                accepted_at=self.accepted_at,
                permitted_capabilities=tuple(self.permitted_capabilities),
                resource_boundaries=tuple(self.resource_boundaries),
                risk_classification=self.risk_classification,
                cost_budget=self.cost_budget,
                retry_budget=self.retry_budget,
                verification_requirements=self.verification_requirements,
            )
            object.__setattr__(self, "mandate_hash", computed)

    def verify_hash(self, secret: str | None = None) -> bool:
        expected = compute_mandate_hash(
            ticket_id=self.ticket_id,
            source_id=self.source_id,
            event_id=self.event_id,
            requester=self.requester,
            authorized_scope=self.authorized_scope,
            workspace_id=self.workspace_id,
            mandate_version=self.mandate_version,
            policy_version=self.policy_version,
            accepted_at=self.accepted_at,
            permitted_capabilities=tuple(self.permitted_capabilities),
            resource_boundaries=tuple(self.resource_boundaries),
            risk_classification=self.risk_classification,
            cost_budget=self.cost_budget,
            retry_budget=self.retry_budget,
            verification_requirements=self.verification_requirements,
            secret=secret,
        )
        return hmac.compare_digest(self.mandate_hash, expected)


@dataclass
class TicketRecord:
    ticket_id: str
    goal_id: str
    mandate: ImmutableMandate
    truth_status: ExecutionTruthStatus = ExecutionTruthStatus.PLANNED
    thread_id: str | None = None
    measured_tokens: int | None = None
    estimated_tokens: int | None = None
    actual_cost: float | None = None
    estimated_cost: float | None = None
    cost_status: str = "UNKNOWN"
    created_at: str = field(default_factory=lambda: str(_now()))
    updated_at: str = field(default_factory=lambda: str(_now()))


@dataclass
class WorkerLease:
    worker_id: str
    lane_kind: Literal["AUTONOMOUS", "OPERATOR_CONTROL"]
    ticket_id: str
    task_id: str
    lease_expires_at: float
    heartbeat_at: float
    attempt_no: int = 1
    is_idempotent: bool = False
    side_effect_uncertain: bool = False
    worktree_path: str | None = None


@dataclass
class OutboxEntry:
    outbox_id: str
    ticket_id: str
    source_id: str
    thread_id: str
    idempotency_key: str
    payload_json: str
    delivery_status: Literal["PENDING", "SENT", "FAILED_RETRYABLE", "DEAD_LETTER"] = "PENDING"
    attempts: int = 0
    max_attempts: int = 3
    next_retry_at: float = 0.0
    last_error: str | None = None
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

    def propagate_failures(self) -> list[GoalTask]:
        """Propagate upstream FAILED/BLOCKED/CANCELLED states to dependent tasks."""
        failed_or_blocked: dict[str, str] = {}
        for task in self.tasks:
            if task.status in (TaskStatus.FAILED, TaskStatus.BLOCKED) or task.truth_status in (
                ExecutionTruthStatus.EXECUTION_FAILED,
                ExecutionTruthStatus.VERIFICATION_FAILED,
                ExecutionTruthStatus.BLOCKED,
                ExecutionTruthStatus.CANCELLED,
                ExecutionTruthStatus.WAITING_APPROVAL,
            ):
                failed_or_blocked[task.id] = task.id

        changed: list[GoalTask] = []
        progress = True
        while progress:
            progress = False
            for task in self.tasks:
                if task.id in failed_or_blocked:
                    continue
                if task.status == TaskStatus.PENDING:
                    for dep_id in task.depends_on:
                        if dep_id in failed_or_blocked:
                            task.status = TaskStatus.BLOCKED
                            task.truth_status = ExecutionTruthStatus.BLOCKED
                            task.blocked_reason = f"upstream_task_failed:{dep_id}"
                            task.result_summary = f"Blocked due to upstream failure in {dep_id}"
                            task.updated_at = _now()
                            failed_or_blocked[task.id] = task.id
                            changed.append(task)
                            progress = True
                            break
        return changed

    def ready_tasks(self, allow_simulated: bool = True) -> list[GoalTask]:
        """Return PENDING tasks whose dependencies have genuinely succeeded."""
        self.propagate_failures()
        allowed_truth = {
            ExecutionTruthStatus.VERIFIED_SUCCESS,
            ExecutionTruthStatus.UNAVAILABLE,
        }
        if allow_simulated:
            allowed_truth.add(ExecutionTruthStatus.SIMULATED)
            allowed_truth.add(ExecutionTruthStatus.PLANNED)

        satisfied_ids = {
            task.id
            for task in self.tasks
            if task.status == TaskStatus.COMPLETED and task.truth_status in allowed_truth
        }
        return [
            task
            for task in self.tasks
            if task.status == TaskStatus.PENDING
            and all(dep in satisfied_ids for dep in task.depends_on)
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
