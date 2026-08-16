# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
StepExecutor — executes and verifies individual recipe steps with optional self-healing.
"""

from typing import Any, List, Optional

from ..execution_history import ExecutionEvent, EventKind
from ..parser import RecipeStep
from .models import StepResult


class StepExecutor:
    """Executes and verifies individual recipe steps with optional self-healing."""

    def __init__(
        self,
        executor: Any,
        verifier: Any,
        llm_client: Optional[Any] = None,
        history: Optional[List[Any]] = None,
        telemetry: Optional[Any] = None,
    ) -> None:
        self.executor = executor
        self.verifier = verifier
        self.llm_client = llm_client
        self.history: List[Any] = history if history is not None else []
        self.telemetry = telemetry

    def execute_and_verify(
        self,
        step: RecipeStep,
        step_order: Optional[int] = None,
        workflow_id: str = "",
    ) -> StepResult:
        """Execute step, optionally self-heal on failure, then verify."""
        self_healed = False
        order = step_order if step_order is not None else step.order

        # Execute
        execution_result = self.executor.execute_step(step)

        # Self-healing: only for shell steps with an LLM client
        step_type = step.params.get("type", "shell") if step.params else "shell"
        if (
            step_type == "shell"
            and execution_result.exit_code != 0
            and self.llm_client is not None
            and hasattr(self.llm_client, "generate")
        ):
            command = step.description.strip()
            stderr = execution_result.stderr or ""

            # Optional: get strategy hint from reflection engine
            strategy_hint = ""
            reflection = getattr(self, "_reflection", None)
            if reflection is not None:
                try:
                    strategy_hint = reflection.get_strategy_suggestion(command) or ""
                except Exception:
                    pass

            # Append history event for self-heal attempt
            try:
                event = ExecutionEvent.create(
                    EventKind.SELF_HEAL_ATTEMPTED,
                    workflow_id or "local",
                    step.order,
                    data={"error": stderr[:200]},
                )
                self.history.append(event)
            except Exception:
                pass

            try:
                if self.telemetry:
                    self.telemetry.record_llm_call()

                prompt = (
                    f"This shell command failed: `{command}`. "
                    f"Error: `{stderr[:500]}`. "
                    + (f"Hint: {strategy_hint}. " if strategy_hint else "")
                    + "Suggest a corrected command. "
                    "Reply with ONLY the corrected command, no explanation."
                )
                corrected = self.llm_client.generate(prompt).strip()

                if corrected and corrected != command:
                    from ..parser import RecipeStep as _RS

                    healed_step = _RS(
                        order=step.order,
                        title=f"{step.title} (healed)",
                        description=corrected,
                        params=step.params,
                    )
                    healed_result = self.executor.execute_step(healed_step)
                    if healed_result.exit_code == 0:
                        self_healed = True
                        execution_result = healed_result
            except Exception:
                pass

        # Extract verification criteria
        criteria = step.params.get("verification", {}) if step.params else {}

        # Verify
        verification_report = self.verifier.verify(execution_result, criteria)

        # Record telemetry
        if self.telemetry:
            try:
                self.telemetry.record_step(
                    step_order=order,
                    title=step.title,
                    exit_code=execution_result.exit_code,
                    self_healed=self_healed,
                )
            except Exception:
                pass

        return StepResult(
            step=step,
            execution=execution_result,
            verification=verification_report,
            self_healed=self_healed,
        )


__all__ = ["StepExecutor"]
