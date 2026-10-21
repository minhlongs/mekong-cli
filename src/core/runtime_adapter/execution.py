"""Task execution and safety gate enforcement for MekongCoreRuntimeImpl."""

from __future__ import annotations

import logging
from typing import Any

from .models import Result, Task

logger = logging.getLogger(__name__)


def _enforce_capability_gates(
    runtime: Any,
    task: Task,
    capability_id: str,
    meta: dict[str, Any],
) -> tuple[Result | None, tuple[str, float] | None]:
    """Enforce capability-based governance and AgentMeta policy gates."""
    agent_spend_delta: tuple[str, float] | None = None
    try:
        from src.core.governance import ActionClass, Governance

        if isinstance(runtime._governance, Governance):
            cap = runtime._capability_bus.get(capability_id)
            if cap is not None:
                agent_name = task.agent.name if task.agent else None
                agent_meta = runtime._resolve_agent_meta(agent_name) if agent_name else None

                if agent_meta is not None:
                    effective_risk = runtime._effective_risk(agent_meta.risk_level, cap.risk_level)
                else:
                    effective_risk = cap.risk_level if cap.risk_level in runtime._RISK_ORDER else "CRITICAL"

                decision = runtime._governance.classify_risk(effective_risk)

                if decision.action_class == ActionClass.FORBIDDEN:
                    runtime._record_audit(capability_id, decision, "blocked")
                    meta["gate_blocked"] = True
                    return Result(task_id=task.id, output=None, error=f"Capability forbidden: {decision.reason}", metadata=meta), None

                if agent_meta is not None and agent_meta.allowed_tools:
                    allowed = agent_meta.allowed_tools
                    if "*" not in allowed and capability_id not in allowed:
                        meta["gate_blocked"] = True
                        return Result(
                            task_id=task.id,
                            output=None,
                            error=f"Capability '{capability_id}' not allowed for agent '{agent_name}' (allowed_tools: {allowed})",
                            metadata=meta,
                        ), None

                if agent_meta is not None and agent_meta.max_budget is not None:
                    cap_cost = float(cap.cost or 0.0)
                    agent_key = agent_name or "unknown"
                    current_spent = runtime._agent_spend.get(agent_key, 0.0)
                    projected = current_spent + cap_cost
                    if projected > agent_meta.max_budget:
                        meta["gate_blocked"] = True
                        return Result(
                            task_id=task.id,
                            output=None,
                            error=f"Agent budget exceeded: ${projected:.4f} > ${agent_meta.max_budget:.4f} (spent ${current_spent:.4f}, capability cost ${cap_cost:.4f})",
                            metadata=meta,
                        ), None
                    agent_spend_delta = (agent_key, cap_cost)

                if agent_meta is not None and agent_meta.max_iterations is not None:
                    if runtime._repair_count >= agent_meta.max_iterations:
                        meta["gate_blocked"] = True
                        return Result(
                            task_id=task.id,
                            output=None,
                            error=f"Agent iteration cap exceeded: {runtime._repair_count} >= {agent_meta.max_iterations}",
                            metadata=meta,
                        ), None

                if agent_meta is not None and agent_meta.approval_policy == "DENY":
                    runtime._record_audit(capability_id, decision, "rejected")
                    meta["gate_blocked"] = True
                    return Result(
                        task_id=task.id,
                        output=None,
                        error=f"Agent approval policy DENY: capability '{capability_id}' denied",
                        metadata=meta,
                    ), None

                if decision.action_class == ActionClass.REVIEW_REQUIRED:
                    if not runtime._governance.request_approval(capability_id, decision):
                        runtime._record_audit(capability_id, decision, "rejected")
                        meta["gate_blocked"] = True
                        return Result(
                            task_id=task.id,
                            output=None,
                            error=f"Capability requires human approval: {decision.reason}",
                            metadata=meta,
                        ), None
                    runtime._record_audit(capability_id, decision, "approved")
    except ImportError:
        pass
    return None, agent_spend_delta


class ExecutionMixin:
    """Mixin implementing execute() and safety gates for MekongCoreRuntimeImpl."""

    def execute(self, task: Task) -> Result:
        """Execute a task with safety gates: governance, cost check, retry limit."""
        tool_name = task.params.get("tool")
        capability_id = task.params.get("capability_id")
        goal_text = task.params.get("description", getattr(task.step, "description", ""))
        meta: dict[str, Any] = {"agent": task.agent.name}

        if self._repair_count >= 3:
            return Result(task_id=task.id, output=None, error="Max repair retries (3) exceeded", metadata=meta)

        if self._governance is not None:
            try:
                from src.core.governance import ActionClass, Governance

                if isinstance(self._governance, Governance):
                    goal_text = task.params.get("description", task.step.description if hasattr(task.step, "description") else "")
                    decision = self._governance.classify(goal_text)
                    if decision.action_class == ActionClass.FORBIDDEN:
                        self._record_audit(goal_text, decision, "blocked")
                        meta["gate_blocked"] = True
                        return Result(task_id=task.id, output=None, error=f"Action forbidden: {decision.reason}", metadata=meta)
                    if decision.action_class == ActionClass.REVIEW_REQUIRED:
                        if not self._governance.request_approval(goal_text, decision):
                            self._record_audit(goal_text, decision, "rejected")
                            meta["gate_blocked"] = True
                            return Result(task_id=task.id, output=None, error=f"Action requires human approval: {decision.reason}", metadata=meta)
                        self._record_audit(goal_text, decision, "approved")
            except ImportError:
                pass

        agent_spend_delta: tuple[str, float] | None = None
        if capability_id and self._capability_bus is not None and self._governance is not None:
            blocked_res, agent_spend_delta = _enforce_capability_gates(self, task, capability_id, meta)
            if blocked_res is not None:
                return blocked_res

        if self._llm_router is not None and hasattr(self._llm_router, "estimate_cost"):
            try:
                goal_text = task.params.get("description", task.step.description if hasattr(task.step, "description") else "")
                tokens_est = max(len(str(goal_text)) // 4, 100)
                meta["estimated_cost"] = self._llm_router.estimate_cost("default", tokens_est)
            except Exception:
                pass

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

                    self._governance.record_audit(AuditEntry(goal=goal_text, action_class="safe", approved=True, result="executed"))
                except Exception:
                    pass
            if agent_spend_delta is not None:
                agent_key, cap_cost = agent_spend_delta
                self._agent_spend[agent_key] = self._agent_spend.get(agent_key, 0.0) + cap_cost
            dispatch_error: str | None = None
            if isinstance(output, dict):
                err_val = output.get("error")
                dispatch_error = str(err_val) if err_val else None
            return Result(task_id=task.id, output=output, error=dispatch_error, metadata=meta)
        except Exception as exc:
            logger.error("Execute failed task=%s: %s", task.id, exc)
            return Result(task_id=task.id, error=str(exc), metadata=meta)
