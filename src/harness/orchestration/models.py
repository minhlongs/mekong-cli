# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data contracts for C1 Agent Orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.harness.agents.base import Result, Task, TaskStatus


@dataclass
class ChildTask:
    """One delegated sub-task inside a swarm run."""

    id: str
    description: str
    agent_id: str
    input: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Result | None = None
    attempts: int = 0

    @property
    def success(self) -> bool:
        return self.result is not None and self.result.success


@dataclass
class SwarmResult:
    """Aggregated outcome of a supervisor run."""

    goal: str
    supervisor_id: str
    child_results: list[ChildTask]
    overall_success: bool
    ranked_outputs: list[dict[str, Any]]

    @property
    def succeeded_count(self) -> int:
        return sum(1 for c in self.child_results if c.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.child_results if not c.success)


@dataclass
class SupervisorConfig:
    """Tunables for the supervisor run."""

    max_retries: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    retry_backoff_factor: float = 2.0
    parallel: bool = False
    max_workers: int = 3
    circuit_failure_threshold: int = 3
    circuit_recovery_timeout: float = 30.0


def rank_child_outputs(children: list[ChildTask]) -> list[dict[str, Any]]:
    """Rank child outputs by (success DESC, attempts ASC, recency DESC)."""
    scored = [
        {
            "child_id": c.id,
            "agent_id": c.agent_id,
            "description": c.description,
            "success": c.success,
            "attempts": c.attempts,
            "output": c.result.output if c.result else None,
            "error": c.result.error if c.result else "no result",
        }
        for c in children
    ]
    scored.sort(key=lambda x: (not x["success"], x["attempts"]))
    return scored


def build_swarm_aggregation(
    goal: str,
    supervisor_id: str,
    children: list[ChildTask],
    ranked_outputs: list[dict[str, Any]],
) -> tuple[SwarmResult, Result, list[Task]]:
    """Build SwarmResult, aggregate Result, and supervisor Task list."""
    swarm = SwarmResult(
        goal=goal,
        supervisor_id=supervisor_id,
        child_results=children,
        overall_success=all(c.success for c in children),
        ranked_outputs=ranked_outputs,
    )
    summary = f"swarm={swarm.succeeded_count}/{len(children)} succeeded"
    agg = Result(
        task_id="supervisor-aggregate",
        success=swarm.overall_success,
        output={"summary": summary, "ranked": swarm.ranked_outputs},
        error=None
        if swarm.overall_success
        else f"{swarm.failed_count} child task(s) failed",
    )
    tasks = [
        Task(
            id="supervisor-run",
            description=f"Supervisor run for: {goal[:60]}",
            input={"goal": goal, "child_count": len(children)},
        )
    ]
    return swarm, agg, tasks
