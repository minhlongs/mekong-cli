# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MekongCoreRuntime Protocol — Buzz Adapter. Provider-agnostic: goal->plan->delegate->execute->observe->verify->repair->remember->commit. No Buzz/MCP hardcoding."""

from __future__ import annotations

import time
import uuid
from typing import Any

from src.core.dag_scheduler import DAGScheduler, _get_order
from src.core.memory_separation import MemoryTier
from src.core.protocols import GoalEngine, Plan, PlanStatus, Step
from src.core.runtime_adapter.adapter_base import AdapterBaseMixin
from src.core.runtime_adapter.execution import ExecutionMixin, _enforce_capability_gates
from src.core.runtime_adapter.intent import (
    _INTENT_AGENT_KEYWORDS,
    _classify_intent,
    _criteria_to_verifier_dict,
    _ExecResultLike,
    _plan_has_dependencies,
    _report_to_verification,
    _topological_task_order,
)
from src.core.runtime_adapter.models import (
    _DEFAULT_CRITERIA,
    _MAX_REPAIR_ATTEMPTS,
    AgentId,
    CheckResult,
    CheckSpec,
    CommitRecord,
    Context,
    Criteria,
    Goal,
    MemoryEntry,
    Observation,
    RepairAction,
    RepairStrategy,
    Result,
    Scope,
    SideEffect,
    Task,
    Verification,
)
from src.core.runtime_adapter.plan_delegate import PlanDelegateMixin
from src.core.runtime_adapter.repair_memory import RepairMemoryMixin
from src.core.runtime_adapter.telemetry_health import TelemetryHealthMixin


class MekongCoreRuntimeImpl(
    AdapterBaseMixin,
    PlanDelegateMixin,
    ExecutionMixin,
    RepairMemoryMixin,
    TelemetryHealthMixin,
):
    """Concrete runtime: goal->plan->delegate->execute->observe->verify->repair->remember->commit."""

    def run_from_payload(self, payload: dict[str, Any]) -> Result:
        """Execute a goal parsed from an external payload (e.g. Buzz webhook)."""
        from src.core.buzz_adapter import BuzzAdapter

        parsed = BuzzAdapter().receive_goal(payload)
        goal_text = parsed["text"]
        mission_id = parsed.get("mission_id")
        start = time.monotonic()
        ctx = Context(
            principal=self._agent_id,
            session_id=uuid.uuid4().hex[:16],
            metadata={
                "mission_id": mission_id,
                "callback_url": parsed.get("callback_url"),
            },
        )
        g = self.goal(goal_text, ctx)
        if self._mission_id is None:
            self.start_mission(
                goal_text, tracer=self._mission_tracer, mission_id=mission_id
            )
        return self._run_goal(g, start)


__all__ = [
    "AgentId",
    "CheckResult",
    "CheckSpec",
    "CommitRecord",
    "Context",
    "Criteria",
    "DAGScheduler",
    "Goal",
    "GoalEngine",
    "MekongCoreRuntimeImpl",
    "MemoryEntry",
    "MemoryTier",
    "Observation",
    "Plan",
    "PlanStatus",
    "RepairAction",
    "RepairStrategy",
    "Result",
    "Scope",
    "SideEffect",
    "Step",
    "Task",
    "Verification",
    "_DEFAULT_CRITERIA",
    "_ExecResultLike",
    "_INTENT_AGENT_KEYWORDS",
    "_MAX_REPAIR_ATTEMPTS",
    "_classify_intent",
    "_criteria_to_verifier_dict",
    "_enforce_capability_gates",
    "_get_order",
    "_plan_has_dependencies",
    "_report_to_verification",
    "_topological_task_order",
]
