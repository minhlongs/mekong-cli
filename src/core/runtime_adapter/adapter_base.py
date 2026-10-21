"""Base initialization and mission loop for MekongCoreRuntimeImpl."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from src.core.protocols import GoalEngine

from .intent import _plan_has_dependencies
from .models import Context, Goal, Result

logger = logging.getLogger(__name__)


class AdapterBaseMixin:
    """Mixin implementing __init__, defaults, start_mission, run, and _run_goal."""

    def __init__(
        self,
        *,
        dispatcher,
        tool_registry,
        memory_store=None,
        memory_separation=None,
        billing=None,
        telemetry=None,
        llm_router=None,
        capability_bus=None,
        agent_id="default",
        governance=None,
        max_cost_usd: float | None = None,
        agent_registry=None,
        goal_engine: GoalEngine | None = None,
        verifier=None,
    ) -> None:
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
        self._max_cost_usd: float | None = max_cost_usd
        self._spent_cost_usd: float = 0.0
        self._agent_spend: dict[str, float] = {}
        self._agent_registry = agent_registry
        self._goal_engine = goal_engine
        if verifier is None:
            from src.core.verifier import RecipeVerifier

            verifier = RecipeVerifier(strict_mode=True)
        self._verifier = verifier
        self._session_keys: set[str] = set()

    def _default_memory_store(self):
        from src.core.memory_store_adapter import MemoryStoreAdapter

        return MemoryStoreAdapter()

    def _default_telemetry(self):
        from src.core.telemetry_emitter import TelemetryEmitter

        return TelemetryEmitter()

    def _default_llm_router(self):
        from src.core.llm_router_adapter import LLMRouterAdapter

        return LLMRouterAdapter()

    def _default_memory_separation(self):
        return None

    def start_mission(
        self, goal: str, tracer: Any = None, mission_id: str | None = None
    ) -> str:
        """Start a new mission with optional tracer correlation."""
        self._mission_id = mission_id or f"mission_{uuid.uuid4().hex[:8]}"
        try:
            self._flush_session_keys()
        except Exception:
            pass
        self._spent_cost_usd = 0.0
        self._agent_spend.clear()
        if tracer is not None:
            self._mission_tracer = tracer
            try:
                # ``mission_id`` rides in metadata; a tracer that honors the
                # correlation id echoes it back, and one that does not still
                # records the mission under its own (metadata-preserving) id.
                tracer.start_mission(goal, {"mission_id": self._mission_id})
            except Exception:
                pass
        if self._telemetry is not None and hasattr(self._telemetry, "emit_start"):
            self._telemetry.emit_start(self._mission_id, goal)
        logger.info("Mission started: %s goal=%s", self._mission_id, goal)
        return self._mission_id or ""

    def run(self, goal_text: str) -> Result:
        """Run the full lifecycle loop for a plain goal string."""
        if self._mission_id is None:
            self.start_mission(goal_text, tracer=self._mission_tracer)
        start = time.monotonic()
        ctx = Context(principal=self._agent_id, session_id=uuid.uuid4().hex[:16])
        g = self.goal(goal_text, ctx)
        return self._run_goal(g, start)

    def _run_goal(self, goal: Goal, start: float) -> Result:
        self._record_stage("goal", {"goal_id": goal.id, "intent": goal.intent})
        p = self.plan(goal)
        self._record_stage("plan", {"plan_id": p.id, "steps": len(p.steps)})
        tasks = self.delegate(p)
        self._record_stage("delegate", {"tasks": len(tasks)})
        logger.info(
            "Loop: goal=%s steps=%d tasks=%d", goal.id, len(p.steps), len(tasks)
        )
        has_deps = _plan_has_dependencies(p)
        results: list[Result] = []
        if has_deps:
            results = self._run_dag_tasks(tasks, goal.criteria)
        else:
            for task in tasks:
                results.append(self._run_task_loop(task, goal.criteria))
        merged = self._merge_results(results)
        obs = self.observe(merged)
        self._record_stage("observe", {"has_error": merged.error is not None})
        entry = self.remember(obs)
        self._record_stage("remember", {"memory_key": entry.key})
        commit_rec = self.commit(merged)
        self._record_stage("commit", {"commit_id": commit_rec.id})
        self._finish_mission(merged)
        self._record_stage(
            "finish",
            {"outcome": "success" if merged.error is None else "failed"},
        )
        logger.info(
            "Done in %.1fms commit=%s mem=%s",
            (time.monotonic() - start) * 1000,
            commit_rec.id,
            entry.key,
        )
        return merged
