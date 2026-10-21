# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Self-healing execution routines for failed shell steps."""

from __future__ import annotations

from typing import Any, Tuple, TYPE_CHECKING

from ..execution_history import EventKind, ExecutionEvent
from ..parser import RecipeStep

if TYPE_CHECKING:
    from ..executor import RecipeExecutor
    from .runner import RecipeOrchestrator


def self_heal_step(
    orchestrator: RecipeOrchestrator,
    step: RecipeStep,
    execution_result: Any,
    workflow_id: str,
    executor: RecipeExecutor,
) -> Tuple[Any, bool]:
    """Attempt LLM self-correction for a failed shell step. Returns (result, healed)."""
    command = step.description.strip()
    stderr = execution_result.stderr or ""
    orchestrator.console.print("[yellow]🔧 Attempting AI self-correction...[/yellow]")

    if workflow_id:
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.SELF_HEAL_ATTEMPTED,
                workflow_id,
                step.order,
                data={"error": stderr[:200]},
            )
        )

    try:
        orchestrator.telemetry.record_llm_call()
        prompt = (
            f"This shell command failed: `{command}`. "
            f"Error: `{stderr[:500]}`. "
            "Suggest a corrected command. "
            "Reply with ONLY the corrected command, no explanation."
        )
        corrected = orchestrator.planner.llm_client.generate(prompt).strip()

        if corrected and corrected != command:
            from ..parser import RecipeStep as _RS

            healed_step = _RS(
                order=step.order,
                title=f"{step.title} (healed)",
                description=corrected,
                agent=step.agent,
                params=step.params,
            )
            healed_result = executor.execute_step(healed_step)
            if healed_result.exit_code == 0:
                orchestrator.console.print("[green]✓ Self-healing succeeded[/green]")
                if workflow_id:
                    orchestrator.history.append(
                        ExecutionEvent.create(
                            EventKind.SELF_HEAL_SUCCEEDED,
                            workflow_id,
                            step.order,
                        )
                    )
                return healed_result, True
            else:
                orchestrator.telemetry.record_error(
                    f"Self-heal retry also failed for step {step.order}"
                )
    except Exception as e:
        orchestrator.telemetry.record_error(f"Self-heal error: {e}")

    return execution_result, False


__all__ = ["self_heal_step"]
