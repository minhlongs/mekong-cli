# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MekongCoreRuntime Protocol — Buzz Adapter. Provider-agnostic: goal->plan->delegate->execute->observe->verify->repair->remember->commit. No Buzz/MCP hardcoding."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.protocols import Plan, PlanStatus, Step
from src.core.memory_separation import MemoryTier

logger = logging.getLogger(__name__)


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

# Canonical MekongCoreRuntime Protocol lives in src.core.protocols
# This module only defines the concrete MekongCoreRuntimeImpl + supporting types.

_DEFAULT_CRITERIA = Criteria(checks=[CheckSpec(kind="exit_code", params={"expected": 0})])
_MAX_REPAIR_ATTEMPTS = 3


class MekongCoreRuntimeImpl:
    def __init__(self, *, dispatcher, tool_registry, memory_store=None, memory_separation=None, billing=None, telemetry=None, llm_router=None, capability_bus=None, agent_id="default", governance=None, max_cost_usd: float | None = None) -> None:
        self._dispatcher = dispatcher
        self._tool_registry = tool_registry
        self._memory_store = memory_store or self._default_memory_store()
        self._memory_separation = memory_separation or self._default_memory_separation()
        self._billing = billing
        self._telemetry = telemetry or self._default_telemetry()
        self._llm_router = llm_router or self._default_llm_router()
        self._capability_bus = capability_bus
        self._agent_id = agent_id
        self._destroyed = False
        self._governance = governance
        self._repair_count: int = 0
        self._mission_id: str | None = None
        self._mission_tracer: Any | None = None
        # AUTONOMY_GAPS #6 — cost guard: hard ceiling on cumulative spend.
        self._max_cost_usd: float | None = max_cost_usd
        self._spent_cost_usd: float = 0.0

    def _default_memory_store(self):
        from src.core.memory_store_adapter import MemoryStoreAdapter
        return MemoryStoreAdapter()

    def _default_telemetry(self):
        from src.core.telemetry_sink_adapter import TelemetrySinkAdapter
        return TelemetrySinkAdapter()

    def _default_llm_router(self):
        from src.core.llm_router_adapter import LLMRouterAdapter
        return LLMRouterAdapter()

    def _default_memory_separation(self):
        from src.core.memory_separation import MemorySeparation
        return MemorySeparation()

    def start_mission(self, goal: str, tracer: Any = None, mission_id: str | None = None) -> str:
        """Start a new mission with optional tracer correlation.

        Clears any SESSION-tier memory left over from a prior run so each
        mission starts with a clean short-term context. When ``mission_id`` is
        supplied (e.g. from an external payload), the tracer is told to use it
        so step/finish calls land on the same record the caller expects.
        """
        self._mission_id = mission_id or f"mission_{uuid.uuid4().hex[:8]}"
        try:
            self._memory_separation.flush_session()
        except Exception:
            pass
        # AUTONOMY_GAPS #6 — cost ceiling is per-mission, not per-process.
        self._spent_cost_usd = 0.0
        if tracer is not None:
            self._mission_tracer = tracer
            try:
                # Let the tracer own the correlation ID so step/finish calls
                # land on the same record it created.
                tracer_mission_id = tracer.start_mission(
                    goal, {"mission_id": self._mission_id}
                )
                if tracer_mission_id:
                    self._mission_id = tracer_mission_id
            except Exception:
                pass
        logger.info("Mission started: %s goal=%s", self._mission_id, goal)
        return self._mission_id

    def run(self, goal_text: str) -> Result:
        start = time.monotonic()
        ctx = Context(principal=self._agent_id, session_id=uuid.uuid4().hex[:16])
        g = self.goal(goal_text, ctx)
        return self._run_goal(g, start)

    def run_from_payload(self, payload: dict[str, Any]) -> Result:
        """Execute a goal parsed from an external payload (e.g. Buzz webhook).

        Wraps :class:`BuzzAdapter` so the runtime can accept structured goals
        with a callback URL and a pre-assigned mission id, without Buzz
        hardcoding leaking into the core loop.
        """
        from src.core.buzz_adapter import BuzzAdapter

        parsed = BuzzAdapter().receive_goal(payload)
        goal_text = parsed["text"]
        mission_id = parsed.get("mission_id")
        start = time.monotonic()
        ctx = Context(
            principal=self._agent_id,
            session_id=uuid.uuid4().hex[:16],
            metadata={"mission_id": mission_id, "callback_url": parsed.get("callback_url")},
        )
        g = self.goal(goal_text, ctx)
        if self._mission_id is None:
            self.start_mission(goal_text, tracer=self._mission_tracer, mission_id=mission_id)
        return self._run_goal(g, start)

    def _run_goal(self, goal: Goal, start: float) -> Result:
        p = self.plan(goal)
        tasks = self.delegate(p)
        logger.info("Loop: goal=%s steps=%d tasks=%d", goal.id, len(p.steps), len(tasks))
        results: list[Result] = []
        for task in tasks:
            results.append(self._run_task_loop(task, goal.criteria))
        merged = self._merge_results(results)
        obs = self.observe(merged)
        entry = self.remember(obs)
        commit_rec = self.commit(merged)
        self._finish_mission(merged)
        logger.info("Done in %.1fms commit=%s mem=%s", (time.monotonic() - start) * 1000, commit_rec.id, entry.key)
        return merged

    def goal(self, intent: str, context: Context) -> Goal:
        return Goal(id=f"goal-{uuid.uuid4().hex[:12]}", intent=intent, context=context, criteria=_DEFAULT_CRITERIA, priority=0)

    def plan(self, goal: Goal) -> Plan:
        step = Step(id="step-0", description=goal.intent, params={"goal_id": goal.id})
        return Plan(id=f"plan-{uuid.uuid4().hex[:12]}", goal=goal.id, steps=[step], status=PlanStatus.IN_PROGRESS)

    def delegate(self, plan: Plan) -> list[Task]:
        agent = AgentId(name=self._agent_id)
        return [Task(id=f"task-{uuid.uuid4().hex[:8]}", step=s, agent=agent, params=s.params) for s in plan.steps]

    def execute(self, task: Task) -> Result:
        """Execute a task with safety gates: governance, cost check, retry limit."""
        tool_name = task.params.get("tool")
        meta: dict[str, Any] = {"agent": task.agent.name}

        # Gate 1: Repair retry limit
        if self._repair_count >= 3:
            return Result(
                task_id=task.id,
                output=None,
                error="Max repair retries (3) exceeded",
                metadata=meta,
            )

        # Gate 2: Governance classification
        if self._governance is not None:
            try:
                from src.core.governance import ActionClass, Governance
                if isinstance(self._governance, Governance):
                    goal_text = task.params.get("description", task.step.description if hasattr(task.step, 'description') else "")
                    decision = self._governance.classify(goal_text)
                    if decision.action_class == ActionClass.FORBIDDEN:
                        self._record_audit(goal_text, decision, "blocked")
                        meta["gate_blocked"] = True
                        return Result(
                            task_id=task.id,
                            output=None,
                            error=f"Action forbidden: {decision.reason}",
                            metadata=meta,
                        )
                    if decision.action_class == ActionClass.REVIEW_REQUIRED:
                        if not self._governance.request_approval(goal_text, decision):
                            self._record_audit(goal_text, decision, "rejected")
                            meta["gate_blocked"] = True
                            return Result(
                                task_id=task.id,
                                output=None,
                                error=f"Action requires human approval: {decision.reason}",
                                metadata=meta,
                            )
                        self._record_audit(goal_text, decision, "approved")
            except ImportError:
                pass

        # Gate 3: Cost estimate (best-effort — warn but don't block)
        if self._llm_router is not None and hasattr(self._llm_router, "estimate_cost"):
            try:
                goal_text = task.params.get("description", task.step.description if hasattr(task.step, 'description') else "")
                tokens_est = max(len(str(goal_text)) // 4, 100)
                cost = self._llm_router.estimate_cost("default", tokens_est)
                meta["estimated_cost"] = cost
            except Exception:
                pass

        # Gate 3.5: Cost limit enforcement (AUTONOMY_GAPS #6)
        guard = self._check_cost_guard(meta.get("estimated_cost"))
        if guard is not None:
            meta["gate_blocked"] = True
            return Result(task_id=task.id, output=None, error=guard, metadata=meta)

        try:
            if tool_name and hasattr(self._tool_registry, "execute"):
                output = self._tool_registry.execute(tool_name, task.params)
            elif hasattr(self._dispatcher, "dispatch"):
                output = self._dispatcher.dispatch(task, task.agent)
            else:
                output = {"status": "noop", "task_id": task.id}
            if self._governance is not None and hasattr(self._governance, "record_audit"):
                try:
                    from src.core.governance import AuditEntry
                    self._governance.record_audit(
                        AuditEntry(goal=goal_text, action_class="safe", approved=True, result="executed")
                    )
                except Exception:
                    pass
            return Result(task_id=task.id, output=output, metadata=meta)
        except Exception as exc:
            logger.error("Execute failed task=%s: %s", task.id, exc)
            return Result(task_id=task.id, error=str(exc), metadata=meta)

    def observe(self, result: Result) -> Observation:
        metrics: dict[str, Any] = {"has_error": result.error is not None}
        # AUTONOMY_GAPS #11: cost is estimated in execute() but was discarded.
        # Propagate it into the observation so it lands in telemetry + memory.
        estimated = result.metadata.get("estimated_cost")
        if estimated is not None:
            metrics["estimated_cost"] = estimated
        self._telemetry.emit({
            "event_type": "task_completed",
            "metric": 1.0,
            "estimated_cost": estimated,
            "mission_id": self._mission_id,
        })
        se: list[SideEffect] = []
        if result.error:
            se.append(SideEffect(kind="error", target=result.task_id, data={"error": result.error}))
        return Observation(result=result, metrics=metrics, side_effects=se)

    def verify(self, observation: Observation, criteria: Criteria) -> Verification:
        checks: list[CheckResult] = []
        failures: list[str] = []
        for spec in criteria.checks:
            passed = self._evaluate_check(spec, observation)
            detail = "ok" if passed else f"check {spec.kind} failed"
            checks.append(CheckResult(check=spec, passed=passed, detail=detail))
            if not passed:
                failures.append(detail)
        return Verification(passed=len(failures) == 0, checks=checks, failures=failures)

    def repair(self, verification: Verification) -> RepairAction:
        """Attempt to repair a failed result. Abort after 3 retries."""
        if self._repair_count >= 3:
            return RepairAction(strategy=RepairStrategy.ESCALATE)
        self._repair_count += 1
        if verification.failures:
            has_error = any("error" in f.lower() for f in verification.failures)
            return RepairAction(strategy=RepairStrategy.RETRY if has_error else RepairStrategy.FALLBACK)
        return RepairAction(strategy=RepairStrategy.RETRY)

    def remember(self, observation: Observation) -> MemoryEntry:
        key = f"obs-{observation.result.task_id}"
        value = {"task_id": observation.result.task_id, "error": observation.result.error, "metrics": observation.metrics}
        entry = MemoryEntry(key=key, value=value, scope=Scope.SESSION)
        # AUTONOMY_GAPS #8 — ScopedMemoryStore is the single canonical owner.
        # The fallback path previously wrote to a second backend; it now
        # routes through the canonical owner instead.
        try:
            self._memory_separation.store(
                key,
                json.dumps(value).encode("utf-8"),
                tier=MemoryTier.SESSION,
            )
        except Exception:
            self._memory_separation.store_raw(key, json.dumps(value).encode("utf-8"))
        return entry

    def flush_session(self) -> int:
        """Clear all SESSION-tier memory. Returns count deleted."""
        try:
            return self._memory_separation.flush_session()
        except Exception:
            return 0

    def commit(self, result: Result) -> CommitRecord:
        record = CommitRecord(id=f"commit-{uuid.uuid4().hex[:12]}", result=result)
        if result.error is None and hasattr(self._billing, "record_usage"):
            try:
                self._billing.record_usage(self._agent_id, 0, "default", "run")
                if hasattr(self._billing, "check_quota"):
                    self._billing.check_quota(self._agent_id)
            except Exception as exc:
                logger.warning("Billing record_usage failed: %s", exc)
        self._telemetry.emit({"event_type": "run_completed", "task_id": result.task_id, "error": result.error, "mission_id": self._mission_id})
        return record

    def _run_task_loop(self, task: Task, criteria: Criteria) -> Result:
        attempts = 0
        result = self.execute(task)
        while attempts < _MAX_REPAIR_ATTEMPTS:
            obs = self.observe(result)
            verification = self.verify(obs, criteria)
            self._trace_step(task, result, verification)
            # Gate verdicts (governance block, cost ceiling) are deterministic
            # policy decisions, not transient failures — retrying cannot change
            # the outcome and would mask the real reason under a retry-limit
            # error, so surface them immediately.
            if verification.passed or result.metadata.get("gate_blocked", False):
                return result
            attempts += 1
            logger.warning("Verify failed task=%s attempt=%d: %s", task.id, attempts, verification.failures)
            action = self.repair(verification)
            if action.strategy in (RepairStrategy.ESCALATE, RepairStrategy.ROLLBACK):
                logger.error("Repair %s task=%s", action.strategy.value, task.id)
                return result
            result = self.execute(task)
        logger.error("Max repair attempts exceeded task=%s", task.id)
        return result

    def _check_cost_guard(self, cost_estimate: Any) -> str | None:
        """Return an error string when the cost ceiling would be breached.

        Returns None when execution may proceed. Never raises — a broken
        cost estimate must not break the loop.
        """
        if self._max_cost_usd is None:
            return None
        try:
            amount = float(cost_estimate.get("cost_usd", 0.0)) if isinstance(cost_estimate, dict) else 0.0
        except Exception:
            amount = 0.0
        projected = self._spent_cost_usd + amount
        if projected > self._max_cost_usd:
            return (
                f"Cost ceiling exceeded: ${projected:.4f} > ${self._max_cost_usd:.4f} "
                f"(spent ${self._spent_cost_usd:.4f}, estimated ${amount:.4f})"
            )
        self._spent_cost_usd = projected
        return None

    def _record_audit(self, goal_text: str, decision: Any, outcome: str) -> None:
        """Push a governance audit entry. Best-effort — never breaks the loop."""
        if self._governance is None or not hasattr(self._governance, "record_audit"):
            return
        try:
            from src.core.governance import AuditEntry
            self._governance.record_audit(
                AuditEntry(
                    goal=goal_text,
                    action_class=decision.action_class.value,
                    approved=outcome in ("approved", "executed"),
                    result=outcome,
                )
            )
        except Exception:
            pass

    def _trace_step(self, task: Task, result: Result, verification: Verification) -> None:
        """Push a step record into the mission tracer when one is attached."""
        if self._mission_tracer is None or self._mission_id is None:
            return
        try:
            self._mission_tracer.log_step(
                self._mission_id,
                task.id,
                {
                    "output": result.output,
                    "error": result.error,
                    "passed": verification.passed,
                    "failures": verification.failures,
                },
            )
        except Exception:
            # Tracing must never break the runtime loop.
            pass

    def _finish_mission(self, result: Result) -> None:
        """Close the mission trace with the final outcome."""
        if self._mission_tracer is None or self._mission_id is None:
            return
        try:
            outcome = "success" if result.error is None else "failed"
            self._mission_tracer.end_mission(self._mission_id, outcome)
        except Exception:
            pass

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

    def health(self) -> dict[str, Any]:
        """Return runtime health status."""
        try:
            llm_ok = self._llm_router.health() if self._llm_router else {"status": "not_set"}
            return {
                "status": "ok",
                "agent_id": self._agent_id,
                "destroyed": self._destroyed,
                "llm_router": llm_ok,
                "has_billing": self._billing is not None,
                "has_capability_bus": self._capability_bus is not None,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def destroy(self) -> dict[str, Any]:
        """Tear down runtime, release resources."""
        self._destroyed = True
        self._memory_store = None
        self._memory_separation = None
        self._telemetry = None
        self._llm_router = None
        self._capability_bus = None
        self._billing = None
        self._mission_id = None
        self._mission_tracer = None
        return {"status": "destroyed", "agent_id": self._agent_id}