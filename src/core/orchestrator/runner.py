# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RecipeOrchestrator — main Plan -> Execute -> Verify coordinator.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING


from ..dag_scheduler import DAGScheduler
from ..executor import RecipeExecutor  # noqa: F401 — re-export for test patching
from ..parser import Recipe, RecipeStep  # noqa: F401
from ..planner import PlanningContext
from ..retry_policy import RetryPolicy
from ..workflow_state import WorkflowState
from .display import display_report, format_status
from .models import OrchestrationResult, OrchestrationStatus, StepResult
from .rollback import handle_failure
from .runner_bmad import post_execution_agi, run_bmad_workflow
from .runner_constitutional import (
    record_constitutional_metric,
    review_plan_constitution,
    review_step_constitution,
)
from .runner_dag import run_dag_workflow
from .runner_goal import execute_goal_workflow, record_memory, try_nlu_shortcut
from .runner_init import init_orchestrator
from .runner_recipe import execute_recipe_pipeline
from .runner_self_heal import self_heal_step
from .runner_sequential import finalize_workflow, run_sequential_workflow
from .runner_step import execute_and_verify_step

if TYPE_CHECKING:
    from src.providers.llm.client import LLMClient
    from ..constitution import Constitution, ConstitutionalReview as ConReview


class RecipeOrchestrator:
    """Coordinates Plan -> Execute -> Verify workflow."""

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        strict_verification: bool = True,
        enable_rollback: bool = True,
        use_swarm: bool = False,
        retry_policy: Optional[RetryPolicy] = None,
        constitution: Optional["Constitution"] = None,
        constitutional_mode: str = "audit",
    ) -> None:
        init_orchestrator(
            self,
            llm_client=llm_client,
            strict_verification=strict_verification,
            enable_rollback=enable_rollback,
            use_swarm=use_swarm,
            retry_policy=retry_policy,
            constitution=constitution,
            constitutional_mode=constitutional_mode,
        )

    def run_from_goal(
        self,
        goal: str,
        context: Optional[PlanningContext] = None,
        progress_callback: Optional[Callable[..., None]] = None,
    ) -> OrchestrationResult:
        """Execute complete workflow from high-level goal (PLAN -> EXECUTE -> VERIFY)."""
        return execute_goal_workflow(self, goal, context, progress_callback)

    def run_from_recipe(
        self,
        recipe: Recipe,
        progress_callback: Optional[Callable[..., None]] = None,
    ) -> OrchestrationResult:
        """Execute existing recipe with verification (EXECUTE -> VERIFY)."""
        return execute_recipe_pipeline(self, recipe, progress_callback)

    def run_bmad_workflow(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """Execute a BMAD workflow by ID."""
        return run_bmad_workflow(self, workflow_id, context)

    def _try_nlu_shortcut(
        self,
        goal: str,
        progress_callback: Optional[Callable[..., None]],
        goal_start_time: float,
        world_before: Optional[Any],
    ) -> Optional[OrchestrationResult]:
        return try_nlu_shortcut(self, goal, progress_callback, goal_start_time, world_before)

    def _record_memory(self, goal: str, result: OrchestrationResult, duration_ms: float) -> None:
        record_memory(self, goal, result, duration_ms)

    def _post_execution_agi(
        self,
        goal: str,
        status: str,
        duration_ms: float,
        world_before: Optional[Any],
        errors: List[str],
    ) -> None:
        post_execution_agi(self, goal, status, duration_ms, world_before, errors)

    def _run_dag(
        self,
        recipe: Recipe,
        executor: RecipeExecutor,
        dag: DAGScheduler,
        result: OrchestrationResult,
        workflow_id: str,
        wf_state: WorkflowState,
    ) -> OrchestrationResult:
        return run_dag_workflow(self, recipe, executor, dag, result, workflow_id, wf_state)

    def _run_sequential(
        self,
        recipe: Recipe,
        executor: RecipeExecutor,
        result: OrchestrationResult,
        workflow_id: str,
        wf_state: WorkflowState,
        progress_callback: Optional[Callable[..., None]],
    ) -> None:
        run_sequential_workflow(self, recipe, executor, result, workflow_id, wf_state, progress_callback)

    def _finalize_workflow(
        self, result: OrchestrationResult, workflow_id: str, wf_state: WorkflowState
    ) -> None:
        finalize_workflow(self, result, workflow_id, wf_state)

    def _execute_and_verify_step(
        self,
        executor: RecipeExecutor,
        step: RecipeStep,
        workflow_id: str = "",
        wf_state: Optional[WorkflowState] = None,
    ) -> StepResult:
        return execute_and_verify_step(self, executor, step, workflow_id, wf_state)

    def _self_heal_step(
        self, step: RecipeStep, execution_result: Any, workflow_id: str, executor: RecipeExecutor
    ) -> tuple:
        return self_heal_step(self, step, execution_result, workflow_id, executor)

    def _review_plan_constitution(self, recipe: Recipe, goal: str) -> "ConReview":
        return review_plan_constitution(self, recipe, goal)

    def _review_step_constitution(self, step: RecipeStep, workflow_id: str = "") -> "ConReview":
        return review_step_constitution(self, step, workflow_id)

    def _record_constitutional_metric(
        self, phase: str, score: float, recipe_name: Optional[str] = None, step_order: Optional[int] = None
    ) -> None:
        record_constitutional_metric(self, phase, score, recipe_name, step_order)

    def _display_report(self, result: OrchestrationResult) -> None:
        display_report(result, self.console)

    def _format_status(self, status: OrchestrationStatus) -> str:
        return format_status(status)

    def _handle_failure(self, result: OrchestrationResult, failed_step: RecipeStep) -> None:
        handle_failure(result, failed_step, self.enable_rollback, self.console)


__all__ = ["RecipeExecutor", "RecipeOrchestrator"]
