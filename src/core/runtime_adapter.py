# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MekongCoreRuntime Protocol — Buzz Adapter. Provider-agnostic: goal->plan->delegate->execute->observe->verify->repair->remember->commit. No Buzz/MCP hardcoding."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

class PlanStatus(str, Enum):
    PENDING, IN_PROGRESS, COMPLETED, FAILED = "pending", "in_progress", "completed", "failed"

class RepairStrategy(str, Enum):
    RETRY, FALLBACK, ESCALATE, ROLLBACK = "retry", "fallback", "escalate", "rollback"

class Scope(str, Enum):
    SESSION, ORG, GLOBAL = "session", "org", "global"

@dataclass(frozen=True)
class AgentId:
    name: str

@dataclass(frozen=True)
class CheckSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class SideEffect:
    kind: str
    target: str
    data: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class RepairAction:
    strategy: RepairStrategy = RepairStrategy.RETRY
    params: dict[str, Any] = field(default_factory=dict)

@dataclass
class Context:
    principal: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Criteria:
    checks: list[CheckSpec] = field(default_factory=list)

@dataclass
class Goal:
    id: str
    intent: str
    context: Context
    criteria: Criteria
    priority: int = 0

@dataclass
class Step:
    id: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)

@dataclass
class Plan:
    id: str
    goal_id: str
    steps: list[Step] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING

@dataclass
class Task:
    id: str
    step: Step
    agent: AgentId
    params: dict[str, Any] = field(default_factory=dict)

@dataclass
class Result:
    task_id: str
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CheckResult:
    check: CheckSpec
    passed: bool
    detail: str = ""

@dataclass
class Verification:
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

@dataclass
class Observation:
    result: Result
    metrics: dict[str, Any] = field(default_factory=dict)
    side_effects: list[SideEffect] = field(default_factory=list)

@dataclass
class MemoryEntry:
    key: str
    value: Any = None
    scope: Scope = Scope.SESSION
    timestamp: float = field(default_factory=time.time)

@dataclass
class CommitRecord:
    id: str
    result: Result
    memory_refs: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@runtime_checkable
class MekongCoreRuntime(Protocol):
    async def run(self, goal: str) -> Result: ...
    async def goal(self, intent: str, context: Context) -> Goal: ...
    async def plan(self, goal: Goal) -> Plan: ...
    async def delegate(self, plan: Plan) -> list[Task]: ...
    async def execute(self, task: Task) -> Result: ...
    async def observe(self, result: Result) -> Observation: ...
    async def verify(self, obs: Observation, criteria: Criteria) -> Verification: ...
    async def repair(self, verification: Verification) -> RepairAction: ...
    async def remember(self, observation: Observation) -> MemoryEntry: ...
    async def commit(self, result: Result) -> CommitRecord: ...

_DEFAULT_CRITERIA = Criteria(checks=[CheckSpec(kind="exit_code", params={"expected": 0})])
_MAX_REPAIR_ATTEMPTS = 3


class MekongCoreRuntimeImpl:
    def __init__(self, *, dispatcher, tool_registry, memory_store, billing, telemetry, agent_id="default") -> None:
        self._dispatcher = dispatcher
        self._tool_registry = tool_registry
        self._memory_store = memory_store
        self._billing = billing
        self._telemetry = telemetry
        self._agent_id = agent_id

    async def run(self, goal_text: str) -> Result:
        start = time.monotonic()
        ctx = Context(principal=self._agent_id, session_id=uuid.uuid4().hex[:16])
        g = await self.goal(goal_text, ctx)
        p = await self.plan(g)
        tasks = await self.delegate(p)
        logger.info("Loop: goal=%s steps=%d tasks=%d", g.id, len(p.steps), len(tasks))
        results: list[Result] = []
        for task in tasks:
            results.append(await self._run_task_loop(task, g.criteria))
        merged = self._merge_results(results)
        obs = await self.observe(merged)
        entry = await self.remember(obs)
        commit_rec = await self.commit(merged)
        logger.info("Done in %.1fms commit=%s mem=%s", (time.monotonic() - start) * 1000, commit_rec.id, entry.key)
        return merged

    async def goal(self, intent: str, context: Context) -> Goal:
        return Goal(id=f"goal-{uuid.uuid4().hex[:12]}", intent=intent, context=context, criteria=_DEFAULT_CRITERIA, priority=0)

    async def plan(self, goal: Goal) -> Plan:
        step = Step(id="step-0", description=goal.intent, params={"goal_id": goal.id})
        return Plan(id=f"plan-{uuid.uuid4().hex[:12]}", goal_id=goal.id, steps=[step], status=PlanStatus.IN_PROGRESS)

    async def delegate(self, plan: Plan) -> list[Task]:
        agent = AgentId(name=self._agent_id)
        return [Task(id=f"task-{uuid.uuid4().hex[:8]}", step=s, agent=agent, params=s.params) for s in plan.steps]

    async def execute(self, task: Task) -> Result:
        tool_name = task.params.get("tool")
        meta = {"agent": task.agent.name}
        try:
            if tool_name and hasattr(self._tool_registry, "execute"):
                output = await self._tool_registry.execute(tool_name, task.params)
            elif hasattr(self._dispatcher, "dispatch"):
                output = await self._dispatcher.dispatch(task, task.agent)
            else:
                output = {"status": "noop", "task_id": task.id}
            return Result(task_id=task.id, output=output, metadata=meta)
        except Exception as exc:
            logger.error("Execute failed task=%s: %s", task.id, exc)
            return Result(task_id=task.id, error=str(exc), metadata=meta)

    async def observe(self, result: Result) -> Observation:
        metrics: dict[str, Any] = {"has_error": result.error is not None}
        if hasattr(self._telemetry, "record_metric"):
            self._telemetry.record_metric("task_completed", 1.0)
        se: list[SideEffect] = []
        if result.error:
            se.append(SideEffect(kind="error", target=result.task_id, data={"error": result.error}))
        return Observation(result=result, metrics=metrics, side_effects=se)

    async def verify(self, observation: Observation, criteria: Criteria) -> Verification:
        checks: list[CheckResult] = []
        failures: list[str] = []
        for spec in criteria.checks:
            passed = self._evaluate_check(spec, observation)
            detail = "ok" if passed else f"check {spec.kind} failed"
            checks.append(CheckResult(check=spec, passed=passed, detail=detail))
            if not passed:
                failures.append(detail)
        return Verification(passed=len(failures) == 0, checks=checks, failures=failures)

    async def repair(self, verification: Verification) -> RepairAction:
        if verification.failures:
            has_error = any("error" in f.lower() for f in verification.failures)
            return RepairAction(strategy=RepairStrategy.RETRY if has_error else RepairStrategy.FALLBACK)
        return RepairAction(strategy=RepairStrategy.RETRY)

    async def remember(self, observation: Observation) -> MemoryEntry:
        key = f"obs-{observation.result.task_id}"
        value = {"task_id": observation.result.task_id, "error": observation.result.error, "metrics": observation.metrics}
        entry = MemoryEntry(key=key, value=value, scope=Scope.SESSION)
        if hasattr(self._memory_store, "append"):
            self._memory_store.append(value)
        return entry

    async def commit(self, result: Result) -> CommitRecord:
        record = CommitRecord(id=f"commit-{uuid.uuid4().hex[:12]}", result=result)
        if result.error is None and hasattr(self._billing, "deduct"):
            try:
                self._billing.deduct(self._agent_id, "standard")
            except Exception as exc:
                logger.warning("Billing deduct failed: %s", exc)
        if hasattr(self._telemetry, "record_event"):
            self._telemetry.record_event("run_completed", properties={"task_id": result.task_id, "error": result.error})
        return record

    async def _run_task_loop(self, task: Task, criteria: Criteria) -> Result:
        attempts = 0
        result = await self.execute(task)
        while attempts < _MAX_REPAIR_ATTEMPTS:
            obs = await self.observe(result)
            verification = await self.verify(obs, criteria)
            if verification.passed:
                return result
            attempts += 1
            logger.warning("Verify failed task=%s attempt=%d: %s", task.id, attempts, verification.failures)
            action = await self.repair(verification)
            if action.strategy in (RepairStrategy.ESCALATE, RepairStrategy.ROLLBACK):
                logger.error("Repair %s task=%s", action.strategy.value, task.id)
                return result
            result = await self.execute(task)
        logger.error("Max repair attempts exceeded task=%s", task.id)
        return result

    @staticmethod
    def _evaluate_check(spec: CheckSpec, observation: Observation) -> bool:
        if spec.kind == "exit_code":
            return observation.result.error is None
        if spec.kind == "output_pattern":
            pattern = spec.params.get("pattern", "")
            return pattern in str(observation.result.output) if pattern else True
        return True

    @staticmethod
    def _merge_results(results: list[Result]) -> Result:
        if len(results) == 1:
            return results[0]
        errors = [r.error for r in results if r.error]
        return Result(task_id="merged", output=[r.output for r in results], error="; ".join(errors) if errors else None, metadata={"task_count": len(results)})