"""Audit, telemetry tracing, cost guards, health, and teardown mixin."""

from __future__ import annotations

from typing import Any

from .models import CheckSpec, Observation, Result, Task, Verification


class TelemetryHealthMixin:
    """Mixin implementing cost guard, audit, tracing, health, and destroy."""

    def _check_cost_guard(self, cost_estimate: Any) -> str | None:
        """Return an error string when the cost ceiling would be breached."""
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

    def _record_stage(self, stage: str, metadata: dict[str, Any] | None = None) -> None:
        """Push a high-level lifecycle stage onto the attached mission tracer."""
        if self._mission_tracer is None:
            return
        try:
            recorder = getattr(self._mission_tracer, "record_stage", None)
            if recorder is not None:
                recorder(stage, metadata)
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
        return Result(
            task_id="merged",
            output=[r.output for r in results],
            error="; ".join(errors) if errors else None,
            metadata={"task_count": len(results)},
        )

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
