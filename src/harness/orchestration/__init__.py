# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI — C1 Agent Orchestration: Supervisor + Result Aggregation.

A goal spawns a supervisor that decomposes into sub-tasks, delegates each
sub-task to a specialised agent via AgentFactory, and merges/ranks results.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from src.core.retry import ExponentialBackoff, call_with_retry
from src.harness.agents.base import AgentBase, Result, Task, TaskStatus
from src.harness.agents.factory import AgentFactory, get_factory
from src.harness.orchestration.models import (
    ChildTask,
    SupervisorConfig,
    SwarmResult,
    build_swarm_aggregation,
    rank_child_outputs,
)
from src.harness.orchestration.role_matcher import (
    _ROLE_CANONICAL,
    _ROLE_KEYWORDS,
    _match_agent_id,
    decompose_goal,
)

logger = logging.getLogger(__name__)


class SupervisorAgent(AgentBase):
    """Decomposes a goal into child tasks, delegates to agents, aggregates."""

    def __init__(
        self,
        name: str = "supervisor",
        config: SupervisorConfig | None = None,
        factory: AgentFactory | None = None,
    ) -> None:
        super().__init__(name=name)
        self.config = config or SupervisorConfig()
        self._factory = factory or get_factory()
        self._backoff = ExponentialBackoff(
            initial=self.config.initial_retry_delay,
            max_delay=self.config.max_retry_delay,
            factor=self.config.retry_backoff_factor,
        )
        self._lock = threading.Lock()

    def plan(self, input_data: str) -> list[Task]:
        """Break *input_data* (goal) into child Task objects."""
        return [
            Task(
                id=c.id,
                description=c.description,
                input={"agent_id": c.agent_id, "child_input": c.input},
            )
            for c in self._decompose(input_data)
        ]

    def execute(self, task: Task) -> Result:
        """Delegate one child task to the appropriate agent (with retry)."""
        agent_id = task.input.get("agent_id", "ceo")
        child_input = task.input.get("child_input", {})

        def _invoke() -> Result:
            agent = self._factory.create(agent_id)
            results = agent.run(child_input.get("goal", task.description))
            if results:
                last = results[-1]
                return Result(
                    task_id=task.id,
                    success=last.success,
                    output=last.output,
                    error=last.error,
                )
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error="agent returned no results",
            )

        success, result_or_exc, stats = call_with_retry(
            _invoke,
            max_attempts=self.config.max_retries + 1,
            backoff=self._backoff,
            on_retry=lambda attempt, delay: logger.info(
                "Retry %d for %s in %.1fs", attempt, task.id, delay
            ),
        )
        with self._lock:
            if success:
                return result_or_exc  # type: ignore[return-value]
            error_msg = str(result_or_exc)
            logger.warning(
                "Child task %s failed after %d attempts: %s",
                task.id,
                stats.attempts,
                error_msg,
            )
            return Result(task_id=task.id, success=False, output=None, error=error_msg)

    def verify(self, result: Result) -> bool:
        """Accept any non-error result; retry on exception strings."""
        return result.success and "exception" not in (result.error or "").lower()

    def run(self, input_data: str) -> list[Result]:  # type: ignore[override]
        """Run the supervisor, return per-child results (not self-tasks)."""
        children = self._decompose(input_data)
        self.tasks = self.plan(input_data)
        raw_results = [self._run_child(c) for c in children]
        return self._aggregate(input_data, children, raw_results)

    def _decompose(self, goal: str) -> list[ChildTask]:
        return decompose_goal(goal, self._factory)

    def _run_child(self, child: ChildTask) -> Result:
        task = Task(
            id=child.id,
            description=child.description,
            input={"agent_id": child.agent_id, "child_input": child.input},
        )
        child.attempts += 1
        result = self.execute(task)
        child.result = result
        child.status = TaskStatus.SUCCESS if result.success else TaskStatus.FAILED
        return result

    def _aggregate(
        self, goal: str, children: list[ChildTask], results: list[Result]
    ) -> list[Result]:
        self._last_swarm, agg, self.tasks = build_swarm_aggregation(
            goal, self.name, children, self._rank_outputs(children)
        )
        return [agg]

    def _rank_outputs(self, children: list[ChildTask]) -> list[dict[str, Any]]:
        return rank_child_outputs(children)

    @property
    def last_swarm(self) -> SwarmResult | None:
        return getattr(self, "_last_swarm", None)


def run_swarm(
    goal: str,
    *,
    max_retries: int = 3,
    parallel: bool = False,
    max_workers: int = 3,
) -> SwarmResult:
    """One-shot: assemble supervisor and run on *goal*."""
    sup = SupervisorAgent(
        name=f"swarm-{id(goal) & 0xFFFF:04x}",
        config=SupervisorConfig(
            max_retries=max_retries, parallel=parallel, max_workers=max_workers
        ),
    )
    sup.run(goal)
    if sup.last_swarm is None:
        raise RuntimeError("Supervisor did not produce a swarm result")
    return sup.last_swarm


__all__ = [
    "ChildTask",
    "SwarmResult",
    "SupervisorAgent",
    "SupervisorConfig",
    "_ROLE_CANONICAL",
    "_ROLE_KEYWORDS",
    "_match_agent_id",
    "run_swarm",
]
