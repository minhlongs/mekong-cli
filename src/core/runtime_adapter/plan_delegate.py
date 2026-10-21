"""Planning, delegation, context, and agent resolution mixin."""

from __future__ import annotations

import uuid
from typing import Any

from src.core.protocols import Plan, PlanStatus, Step

from .intent import _classify_intent
from .models import _DEFAULT_CRITERIA, AgentId, Context, Goal, Task


class PlanDelegateMixin:
    """Mixin implementing goal, context, plan, delegate, and agent resolution."""

    _RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    _RISK_NAMES = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}

    _ROLE_AGENT_MAP = {
        "architect": "planner",
        "backend": "cto",
        "infra": "coo",
        "qa": "cto",
        "security": "cso",
        "docs": "cmo",
        "reviewer": "planner",
    }

    def _resolve_agent_meta(self, agent_name: str):
        """Resolve the acting agent's AgentMeta from the registry."""
        if not agent_name:
            return None
        registry = self._agent_registry
        if registry is None:
            try:
                from src.core.agent_registry import get_registry

                registry = get_registry()
            except Exception:
                return None
        try:
            return registry.get_meta_obj(agent_name)
        except Exception:
            return None

    def _effective_risk(self, agent_risk: str, capability_risk: str) -> str:
        """Return the higher of the agent's and capability's risk levels."""
        agent_r = self._RISK_ORDER.get((agent_risk or "").upper())
        cap_r = self._RISK_ORDER.get((capability_risk or "").upper())
        if agent_r is None or cap_r is None:
            return "CRITICAL"
        return self._RISK_NAMES[max(agent_r, cap_r)]

    def goal(self, intent: str, context: Context | None = None) -> Goal:
        if context is None:
            context = Context(
                principal=self._agent_id,
                session_id=uuid.uuid4().hex[:16],
                metadata={"mission_id": self._mission_id},
            )
        return Goal(
            id=f"goal-{uuid.uuid4().hex[:12]}",
            intent=intent,
            context=context,
            criteria=_DEFAULT_CRITERIA,
            priority=0,
        )

    def context(self, goal: Any = None) -> dict[str, Any]:
        """Extract or construct context metadata for the given goal."""
        if goal is None:
            return {
                "principal": self._agent_id,
                "session_id": uuid.uuid4().hex[:16],
                "mission_id": self._mission_id,
                "metadata": {},
            }
        if hasattr(goal, "context"):
            ctx = getattr(goal, "context")
            if isinstance(ctx, dict):
                return dict(ctx)
            if hasattr(ctx, "to_dict") and callable(ctx.to_dict):
                data = ctx.to_dict()
                if "mission_id" not in data:
                    data["mission_id"] = self._mission_id
                return data
            if hasattr(ctx, "principal") and hasattr(ctx, "session_id"):
                return {
                    "principal": ctx.principal,
                    "session_id": ctx.session_id,
                    "metadata": getattr(ctx, "metadata", {}),
                    "mission_id": self._mission_id,
                }
        if isinstance(goal, dict):
            ctx_val = goal.get("context")
            if isinstance(ctx_val, dict):
                return dict(ctx_val)
            return {
                "principal": self._agent_id,
                "session_id": uuid.uuid4().hex[:16],
                "mission_id": goal.get("mission_id", self._mission_id),
                "metadata": goal.get("metadata", {}),
            }
        return {
            "principal": self._agent_id,
            "session_id": uuid.uuid4().hex[:16],
            "mission_id": self._mission_id,
            "metadata": {},
        }

    def _resolve_agent_name(self, intent: str) -> str:
        classified = _classify_intent(intent)
        return classified or self._agent_id

    def _audit_unknown_agent(self, agent_name: str, intent: str) -> None:
        if self._governance is None or not hasattr(self._governance, "record_audit"):
            return
        try:
            from src.core.governance import ActionClass, AuditEntry

            self._governance.record_audit(
                AuditEntry(
                    goal=intent,
                    action_class=ActionClass.SAFE.value,
                    approved=False,
                    result=f"unknown_agent:{agent_name}",
                )
            )
        except Exception:
            pass

    def plan(self, goal: Any, context: Any = None) -> Plan:
        if isinstance(goal, str):
            goal = self.goal(goal, context=context)
        elif isinstance(goal, dict):
            intent = goal.get("intent") or goal.get("goal") or goal.get("text", "")
            goal = self.goal(intent, context=context)
        agent_name = self._resolve_agent_name(goal.intent)
        if agent_name in ("cto", "cmo", "coo", "cfo", "cso", "planner"):
            if self._goal_engine is None:
                from src.core.adapters.goal_engine_adapter import make_goal_engine_adapter

                self._goal_engine = make_goal_engine_adapter()
            multi_step_plan = self._goal_engine.decompose(goal.intent)
            multi_step_plan.id = f"plan-{uuid.uuid4().hex[:12]}"
            multi_step_plan.goal = goal.id
            multi_step_plan.status = PlanStatus.PENDING
            return multi_step_plan
        step = Step(id="step-0", description=goal.intent, params={"goal_id": goal.id, "agent": agent_name})
        return Plan(id=f"plan-{uuid.uuid4().hex[:12]}", goal=goal.id, steps=[step], status=PlanStatus.IN_PROGRESS)

    def delegate(self, plan: Plan) -> list[Task]:
        """Build tasks with explicit agent assignment."""
        from src.core.agent_registry import get_registry

        registry = get_registry()
        tasks: list[Task] = []
        for step in plan.steps:
            role = step.params.get("role")
            if role and role in self._ROLE_AGENT_MAP:
                agent_name = self._ROLE_AGENT_MAP[role]
            else:
                agent_name = step.params.get("agent") or self._agent_id
            if registry.get_meta_obj(agent_name) is None:
                self._audit_unknown_agent(agent_name, step.description)
            tasks.append(
                Task(
                    id=f"task-{uuid.uuid4().hex[:8]}",
                    step=step,
                    agent=AgentId(name=agent_name),
                    params=dict(step.params),
                )
            )
        return tasks
