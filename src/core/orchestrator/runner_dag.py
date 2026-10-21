# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""DAG parallel execution routines for RecipeOrchestrator."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..dag_scheduler import DAGScheduler, validate_dag
from ..execution_history import EventKind, ExecutionEvent
from ..parser import Recipe, RecipeStep
from ..workflow_state import WorkflowState, WorkflowStatus
from .models import OrchestrationResult, OrchestrationStatus, StepResult

if TYPE_CHECKING:
    from ..executor import RecipeExecutor
    from .runner import RecipeOrchestrator


def run_dag_workflow(
    orchestrator: RecipeOrchestrator,
    recipe: Recipe,
    executor: RecipeExecutor,
    dag: DAGScheduler,
    result: OrchestrationResult,
    workflow_id: str,
    wf_state: WorkflowState,
) -> OrchestrationResult:
    """Run steps in DAG parallel mode."""
    cycle_err = validate_dag(recipe.steps)
    if cycle_err:
        result.status = OrchestrationStatus.FAILED
        result.errors.append(cycle_err)
        orchestrator._display_report(result)
        return result

    orchestrator.console.print("[dim]DAG mode: parallel execution enabled[/dim]")

    def _dag_executor(step: RecipeStep) -> StepResult:
        return orchestrator._execute_and_verify_step(executor, step, workflow_id, wf_state)

    def _on_dag_complete(order: int, dag_result: Any) -> None:
        if dag_result.success:
            result.completed_steps += 1
            orchestrator.console.print(f"[green]✓[/green] Step {order} passed")
        else:
            result.failed_steps += 1
            orchestrator.console.print(f"[red]✗[/red] Step {order} failed")

    dag_results = dag.execute_all(_dag_executor, _on_dag_complete)

    for order in sorted(dag_results):
        dr = dag_results[order]
        if dr.result:
            result.step_results.append(dr.result)
        if not dr.success:
            result.status = OrchestrationStatus.PARTIAL
        if dr.error:
            result.errors.append(f"Step {order}: {dr.error}")

    for cancelled_order in dag.cancelled_steps:
        result.errors.append(
            f"Step {cancelled_order}: cancelled (upstream failure)"
        )

    if result.failed_steps == 0 and not dag.cancelled_steps:
        result.status = OrchestrationStatus.SUCCESS
        wf_state.transition(WorkflowStatus.COMPLETED)
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.WORKFLOW_COMPLETED,
                workflow_id,
                data={"success_rate": result.success_rate},
            )
        )
    else:
        wf_state.transition(WorkflowStatus.FAILED)
        orchestrator.history.append(
            ExecutionEvent.create(
                EventKind.WORKFLOW_FAILED,
                workflow_id,
                data={"errors": result.errors[:5]},
            )
        )

    orchestrator.history.persist(workflow_id)
    orchestrator._display_report(result)
    return result


__all__ = ["run_dag_workflow"]
