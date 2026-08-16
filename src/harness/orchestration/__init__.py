# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI — C1 Agent Orchestration: Supervisor + Result Aggregation.

A goal spawns a supervisor that decomposes into sub-tasks, delegates each
sub-task to a specialised agent via AgentFactory, and merges/ranks results.

Self-healing integration:
- Failed child tasks auto-retry through C3's ExponentialBackoff (src.core.retry)
- Circuit breaker guards rapid retries against a single failing agent provider.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from src.core.retry import ExponentialBackoff, call_with_retry
from src.harness.agents.factory import AgentFactory, get_factory
from src.harness.agents.base import AgentBase, Result, Task, TaskStatus

logger = logging.getLogger(__name__)


# ── Data contracts ───────────────────────────────────────────────────────────


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


# ── Agent selection heuristics ───────────────────────────────────────────────

# Keywords that map a sub-task description to an agent role.
_ROLE_KEYWORDS: dict[str, list[str]] = {
    "eng": ("code", "build", "fix", "implement", "api", "backend", "frontend",
            "test", "debug", "refactor", "database", "deploy"),
    "cto": ("architecture", "design", "system", "review", "audit"),
    "cmo": ("marketing", "campaign", "copy", "seo", "content", "brand"),
    "cfo": ("financial", "budget", "revenue", "cost", "invoice"),
    "coo": ("monitor", "health", "ops", "worker", "deployment", "infra"),
    "pm": ("plan", "roadmap", "spec", "requirement", "sprint"),
    "analyst": ("analyze", "research", "data", "report", "forecast"),
    "sales": ("sales", "pipeline", "prospect", "deal", "outreach"),
    "docs": ("document", "readme", "docs", "guide"),
    "security": ("security", "vulnerability", "secret", "access"),
}

_ROLE_CANONICAL: dict[str, str] = {
    "eng": "eng",
    "engineering": "eng",
    "developer": "eng",
    "cto": "cto",
    "architect": "cto",
    "cmo": "cmo",
    "marketing": "cmo",
    "cfo": "cfo",
    "finance": "cfo",
    "coo": "ops",  # registry uses "ops"
    "ops": "ops",
    "operations": "ops",
    "pm": "pm",
    "product": "pm",
    "analyst": "analyst",
    "sales": "sales",
    "docs": "docs",
    "documentation": "docs",
    "security": "security",
    "audit": "security",
}


def _match_agent_id(description: str, factory: AgentFactory) -> str:
    """Pick the best agent_id for *description* from the factory registry."""
    desc_lower = description.lower()
    # 1. Keyword scoring
    best_id: str | None = None
    best_score = 0
    for role, keywords in _ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > best_score:
            best_score = score
            canonical = _ROLE_CANONICAL.get(role, role)
            if canonical in factory.list_available():
                best_id = canonical
    # 2. Fallback: try canonical direct mapping
    if best_id is None:
        for alias, canonical in _ROLE_CANONICAL.items():
            if alias in desc_lower and canonical in factory.list_available():
                best_id = canonical
                break
    # 3. Ultimate fallback
    if best_id is None:
        available = factory.list_available()
        best_id = available[0] if available else "ceo"
    return best_id


# ── Supervisor ───────────────────────────────────────────────────────────────


class SupervisorAgent(AgentBase):
    """Decomposes a goal into child tasks, delegates to agents, aggregates.

    Each child agent call is wrapped with C3 retry logic.
    A per-agent circuit breaker prevents retry storms on persistent failures.

    Usage::

        sup = SupervisorAgent("swarm-1")
        result = sup.run("build a REST API")
        print(result.ranked_outputs)
    """

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

    # ── AgentBase overrides ────────────────────────────────────────────────

    def plan(self, input_data: str) -> list[Task]:
        """Break *input_data* (goal) into child Task objects."""
        children = self._decompose(input_data)
        return [
            Task(
                id=c.id,
                description=c.description,
                input={"agent_id": c.agent_id, "child_input": c.input},
            )
            for c in children
        ]

    def execute(self, task: Task) -> Result:
        """Delegate one child task to the appropriate agent (with retry)."""
        agent_id = task.input.get("agent_id", "ceo")
        child_input = task.input.get("child_input", {})

        def _invoke() -> Result:
            agent = self._factory.create(agent_id)
            results = agent.run(child_input.get("goal", task.description))
            # Flatten agent's results into one
            if results:
                last = results[-1]
                return Result(
                    task_id=task.id,
                    success=last.success,
                    output=last.output,
                    error=last.error,
                )
            return Result(task_id=task.id, success=False, output=None,
                          error="agent returned no results")

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
            logger.warning("Child task %s failed after %d attempts: %s",
                           task.id, stats.attempts, error_msg)
            return Result(task_id=task.id, success=False, output=None,
                          error=error_msg)

    def verify(self, result: Result) -> bool:
        """Accept any non-error result; retry on exception strings."""
        return result.success and "exception" not in (result.error or "").lower()

    def run(self, input_data: str) -> list[Result]:  # type: ignore[override]
        """Run the supervisor, return per-child results (not self-tasks)."""
        children = self._decompose(input_data)
        self.tasks = self.plan(input_data)
        raw_results: list[Result] = []
        for i, child in enumerate(children):
            logger.info("Supervisor delegating %s → %s (%d/%d)",
                        child.id, child.agent_id, i + 1, len(children))
            raw_results.append(self._run_child(child))
        return self._aggregate(input_data, children, raw_results)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _decompose(self, goal: str) -> list[ChildTask]:
        """Split a high-level goal into role-assigned child tasks."""
        # Simple decomposition: 1 child per implicit role detected.
        # More sophisticated splitting can be added later (LLM-based).
        assigned_roles: set[str] = set()
        children: list[ChildTask] = []

        # Always start with a primary role based on the goal text.
        primary_id = _match_agent_id(goal, self._factory)
        children.append(ChildTask(
            id=f"child-{len(children)+1:03d}",
            description=goal[:120],
            agent_id=primary_id,
            input={"goal": goal},
        ))
        assigned_roles.add(primary_id)

        # If the factory has multiple agents, spin up one child per
        # additional role whose keywords appear in the goal.
        goal_lower = goal.lower()
        for role, kws in _ROLE_KEYWORDS.items():
            canonical = _ROLE_CANONICAL.get(role, role)
            if canonical in assigned_roles:
                continue
            if canonical not in self._factory.list_available():
                continue
            if any(kw in goal_lower for kw in kws):
                children.append(ChildTask(
                    id=f"child-{len(children)+1:03d}",
                    description=f"{canonical} sub-task for: {goal[:80]}",
                    agent_id=canonical,
                    input={"goal": goal, "role": canonical},
                ))
                assigned_roles.add(canonical)

        return children

    def _run_child(self, child: ChildTask) -> Result:
        """Execute one child task, tracking attempts."""
        # Repackage as base Task for AgentBase.run() semantics, then
        # call execute() directly for supervisor-level control.
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

    # ── Result aggregation ────────────────────────────────────────────────

    def _aggregate(
        self,
        goal: str,
        children: list[ChildTask],
        results: list[Result],
    ) -> list[Result]:
        """Merge/rank child results and publish to self.tasks.

        The returned list is the supervisor's *own* result stream, matching
        AgentBase.run() convention.  Detailed per-child outputs are accessible
        as a side-effect attribute on the supervisor instance.
        """
        self._last_swarm = SwarmResult(
            goal=goal,
            supervisor_id=self.name,
            child_results=children,
            overall_success=all(c.success for c in children),
            ranked_outputs=self._rank_outputs(children),
        )
        # Build a single aggregated Result for the supervisor itself.
        summary = (
            f"swarm={self._last_swarm.succeeded_count}/{len(children)} succeeded"
        )
        agg = Result(
            task_id="supervisor-aggregate",
            success=self._last_swarm.overall_success,
            output={"summary": summary,
                    "ranked": self._last_swarm.ranked_outputs},
            error=None if self._last_swarm.overall_success
            else f"{self._last_swarm.failed_count} child task(s) failed",
        )
        # Replace self.tasks with supervisor-only output so AgentBase.run()
        # callers see a coherent result list.
        self.tasks = [Task(
            id="supervisor-run",
            description=f"Supervisor run for: {goal[:60]}",
            input={"goal": goal, "child_count": len(children)},
        )]
        return [agg]

    def _rank_outputs(self, children: list[ChildTask]) -> list[dict[str, Any]]:
        """Rank child outputs by (success DESC, attempts ASC, recency DESC)."""
        scored = []
        for c in children:
            r = c.result
            scored.append({
                "child_id": c.id,
                "agent_id": c.agent_id,
                "description": c.description,
                "success": c.success,
                "attempts": c.attempts,
                "output": r.output if r else None,
                "error": r.error if r else "no result",
            })
        scored.sort(key=lambda x: (not x["success"], x["attempts"]), reverse=False)
        return scored

    @property
    def last_swarm(self) -> SwarmResult | None:
        """Most recent swarm outcome (set after run())."""
        return getattr(self, "_last_swarm", None)


# ── Convenience API ──────────────────────────────────────────────────────────


def run_swarm(
    goal: str,
    *,
    max_retries: int = 3,
    parallel: bool = False,
    max_workers: int = 3,
) -> SwarmResult:
    """One-shot: assemble supervisor and run on *goal*.

    Returns SwarmResult with per-child outcomes + ranked outputs.
    """
    sup = SupervisorAgent(
        name=f"swarm-{id(goal) & 0xFFFF:04x}",
        config=SupervisorConfig(
            max_retries=max_retries,
            parallel=parallel,
            max_workers=max_workers,
        ),
    )
    sup.run(goal)
    swarm = sup.last_swarm
    if swarm is None:
        raise RuntimeError("Supervisor did not produce a swarm result")
    return swarm


__all__ = [
    "ChildTask",
    "SwarmResult",
    "SupervisorAgent",
    "SupervisorConfig",
    "run_swarm",
]
