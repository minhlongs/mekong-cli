# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Full recipe execution pipeline (DAG, sequential, state tracking)."""

from __future__ import annotations

import uuid
from typing import Callable, Optional, TYPE_CHECKING

from ..dag_scheduler import DAGScheduler
from ..execution_history import EventKind, ExecutionEvent
from ..executor import RecipeExecutor
from ..parser import Recipe
from ..workflow_state import WorkflowState, WorkflowStatus
from .models import OrchestrationResult, OrchestrationStatus

if TYPE_CHECKING:
    from .runner import RecipeOrchestrator


def execute_recipe_pipeline(
    orchestrator: RecipeOrchestrator,
    recipe: Recipe,
    progress_callback: Optional[Callable[..., None]] = None,
) -> OrchestrationResult:
    """Execute existing recipe with verification (EXECUTE -> VERIFY)."""
    workflow_id = uuid.uuid4().hex[:12]
    result = OrchestrationResult(
        status=OrchestrationStatus.SUCCESS,
        recipe=recipe,
        total_steps=len(recipe.steps),
    )

    wf_state = WorkflowState(workflow_id=workflow_id)
    wf_state.register_steps(len(recipe.steps))
    wf_state.transition(WorkflowStatus.RUNNING)

    orchestrator.history.append(
        ExecutionEvent.create(
            EventKind.WORKFLOW_STARTED,
            workflow_id,
            data={"recipe": recipe.name, "steps": len(recipe.steps)},
        )
    )

    orchestrator.console.print("\n[bold yellow]⚙️ PHASE 2: EXECUTION & VERIFICATION[/bold yellow]")
    executor = RecipeExecutor(recipe)

    dag = DAGScheduler(recipe.steps)
    if dag.has_dependencies():
        return orchestrator._run_dag(recipe, executor, dag, result, workflow_id, wf_state)

    orchestrator._run_sequential(recipe, executor, result, workflow_id, wf_state, progress_callback)
    orchestrator._finalize_workflow(result, workflow_id, wf_state)
    orchestrator.history.persist(workflow_id)
    orchestrator._display_report(result)
    return result


__all__ = ["execute_recipe_pipeline"]
