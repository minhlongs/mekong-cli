# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Workflow State Machine."""

from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ROLLED_BACK = "rolled_back"
    SUSPENDED = "suspended"


class StepStatus(str, Enum):
    SCHEDULED = "scheduled"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    ROLLING_BACK = "rolling_back"


_WORKFLOW_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.PENDING: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
    WorkflowStatus.RUNNING: {
        WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED,
        WorkflowStatus.TIMED_OUT, WorkflowStatus.ROLLED_BACK, WorkflowStatus.SUSPENDED,
    },
    WorkflowStatus.SUSPENDED: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
    WorkflowStatus.FAILED: {WorkflowStatus.RUNNING, WorkflowStatus.ROLLED_BACK},
    WorkflowStatus.TIMED_OUT: {WorkflowStatus.RUNNING},
    WorkflowStatus.COMPLETED: set(),
    WorkflowStatus.CANCELLED: set(),
    WorkflowStatus.ROLLED_BACK: set(),
}

_STEP_TRANSITIONS: dict[StepStatus, set[StepStatus]] = {
    StepStatus.SCHEDULED: {StepStatus.STARTED, StepStatus.SKIPPED},
    StepStatus.STARTED: {StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.RETRYING},
    StepStatus.RETRYING: {StepStatus.STARTED},
    StepStatus.FAILED: {StepStatus.RETRYING, StepStatus.ROLLING_BACK},
    StepStatus.COMPLETED: {StepStatus.ROLLING_BACK},
    StepStatus.ROLLING_BACK: {StepStatus.SKIPPED},
    StepStatus.SKIPPED: set(),
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


@dataclass
class StepState:
    order: int
    status: StepStatus = StepStatus.SCHEDULED
    attempt: int = 0
    last_heartbeat: float = 0.0
    error: str = ""

    def transition(self, new_status: StepStatus) -> None:
        if new_status not in _STEP_TRANSITIONS.get(self.status, set()):
            raise InvalidTransitionError(f"Step {self.order}: {self.status.value} → {new_status.value} not allowed")
        self.status = new_status


@dataclass
class WorkflowState:
    """Deterministic state machine for a workflow execution."""

    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: dict[int, StepState] = field(default_factory=dict)
    current_step: int = 0

    def transition(self, new_status: WorkflowStatus) -> None:
        if new_status not in _WORKFLOW_TRANSITIONS.get(self.status, set()):
            raise InvalidTransitionError(f"Workflow {self.workflow_id}: {self.status.value} → {new_status.value} not allowed")
        self.status = new_status

    def register_steps(self, step_count: int) -> None:
        for i in range(1, step_count + 1):
            self.steps[i] = StepState(order=i)

    def step_transition(self, step_order: int, new_status: StepStatus) -> None:
        step = self.steps[step_order]
        step.transition(new_status)
        if new_status == StepStatus.STARTED:
            self.current_step = step_order
        elif new_status == StepStatus.RETRYING:
            step.attempt += 1

    def get_completed_steps(self) -> list[int]:
        return [order for order, step in self.steps.items() if step.status == StepStatus.COMPLETED]

    def get_failed_steps(self) -> list[int]:
        return [order for order, step in self.steps.items() if step.status == StepStatus.FAILED]

    @property
    def is_terminal(self) -> bool:
        return self.status in {WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED, WorkflowStatus.ROLLED_BACK}

    @property
    def progress(self) -> float:
        return (len(self.get_completed_steps()) / len(self.steps)) * 100.0 if self.steps else 0.0


__all__ = ["InvalidTransitionError", "StepState", "StepStatus", "WorkflowState", "WorkflowStatus"]
