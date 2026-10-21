# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sequential execution and workflow finalization routines for RecipeOrchestrator."""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

from ..execution_history import EventKind, ExecutionEvent
from ..parser import Recipe
from ..workflow_state import StepStatus, WorkflowState, WorkflowStatus
from .models import OrchestrationResult, OrchestrationStatus

if TYPE_CHECKING:
    from ..executor import RecipeExecutor
    from .runner import RecipeOrchestrator


def run_sequential_workflow(
    orchestrator: RecipeOrchestrator,
    recipe: Recipe,
    executor: RecipeExecutor,
    result: OrchestrationResult,
    workflow_id: str,
    wf_state: WorkflowState,
    progress_callback: Optional[Callable[..., None]],
) -> None:
    """Run steps sequentially."""
    for step in recipe.steps:
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.STEP_SCHEDULED, workflow_id, step.order
            )
        )
        wf_state.step_transition(step.order, StepStatus.STARTED)

        step_result = orchestrator._execute_and_verify_step(
            executor, step, workflow_id, wf_state
        )
        result.step_results.append(step_result)

        if step_result.verification.passed:
            result.completed_steps += 1
            wf_state.step_transition(step.order, StepStatus.COMPLETED)
            orchestrator.history.append(
                ExecutionEvent.create(
                    EventKind.STEP_COMPLETED, workflow_id, step.order
                )
            )
            orchestrator.console.print(f"[green]✓[/green] Step {step.order} passed")
        else:
            result.failed_steps += 1
            result.status = OrchestrationStatus.FAILED
            wf_state.step_transition(step.order, StepStatus.FAILED)
            orchestrator.history.append(
                ExecutionEvent.create(
                    EventKind.STEP_FAILED,
                    workflow_id,
                    step.order,
                    data={"errors": step_result.verification.errors[:3]},
                )
            )
            orchestrator.console.print(f"[red]✗[/red] Step {step.order} failed")
            for error in step_result.verification.errors:
                result.errors.append(f"Step {step.order}: {error}")

        for warning in step_result.verification.warnings:
            result.warnings.append(f"Step {step.order}: {warning}")

        if progress_callback:
            progress_callback(step_result, result)

        if not step_result.verification.passed:
            if orchestrator.enable_rollback:
                orchestrator.history.append(
                    ExecutionEvent.create(
                        EventKind.ROLLBACK_STARTED, workflow_id, step.order
                    )
                )
                orchestrator._handle_failure(result, step)
                orchestrator.history.append(
                    ExecutionEvent.create(
                        EventKind.ROLLBACK_COMPLETED, workflow_id, step.order
                    )
                )
            else:
                result.status = OrchestrationStatus.PARTIAL
            break


def finalize_workflow(
    orchestrator: RecipeOrchestrator,
    result: OrchestrationResult,
    workflow_id: str,
    wf_state: WorkflowState,
) -> None:
    """Transition final workflow state and record history events."""
    if result.status == OrchestrationStatus.SUCCESS:
        wf_state.transition(WorkflowStatus.COMPLETED)
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.WORKFLOW_COMPLETED,
                workflow_id,
                data={"success_rate": result.success_rate},
            )
        )
    elif result.status == OrchestrationStatus.FAILED:
        wf_state.transition(WorkflowStatus.FAILED)
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.WORKFLOW_FAILED,
                workflow_id,
                data={"errors": result.errors[:5]},
            )
        )


__all__ = ["finalize_workflow", "run_sequential_workflow"]
