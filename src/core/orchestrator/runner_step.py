# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Step execution and verification routines for RecipeOrchestrator."""

from __future__ import annotations

import time
from typing import Optional, TYPE_CHECKING

from ..parser import RecipeStep
from ..workflow_state import WorkflowState
from .models import StepResult

if TYPE_CHECKING:
    from ..executor import RecipeExecutor
    from .runner import RecipeOrchestrator


def execute_and_verify_step(
    orchestrator: RecipeOrchestrator,
    executor: RecipeExecutor,
    step: RecipeStep,
    workflow_id: str = "",
    wf_state: Optional[WorkflowState] = None,
) -> StepResult:
    """Execute single step and verify results, with optional LLM self-healing and constitutional review."""
    step_start = time.time()
    self_healed = False
    step_review = None

    if orchestrator.constitution:
        step_review = orchestrator._review_step_constitution(step, workflow_id)
        if step_review.blocked and orchestrator.constitutional_mode == "enforce":
            orchestrator.console.print(f"[bold red]🚫 Step {step.order} blocked by Constitutional AI[/bold red]")
            from ..verifier import ExecutionResult, VerificationReport

            blocked_result = ExecutionResult(exit_code=1, stderr=f"Constitutional violation: {step_review.summary}")
            verification = VerificationReport(
                passed=False,
                errors=[f"Constitutional AI: {r.reason}" for r in step_review.principle_results if not r.passed],
            )
            return StepResult(
                step=step,
                execution=blocked_result,
                verification=verification,
                self_healed=False,
                constitutional_score=step_review.overall_score if step_review else None,
                constitutional_review={
                    "overall_score": step_review.overall_score,
                    "blocked": step_review.blocked,
                    "principles": [
                        {"principle": r.principle.value, "score": r.score, "passed": r.passed}
                        for r in step_review.principle_results
                    ],
                }
                if step_review
                else None,
            )

    execution_result = executor.execute_step(step)
    step_type = step.params.get("type", "shell") if step.params else "shell"
    if (
        step_type == "shell"
        and execution_result.exit_code != 0
        and orchestrator.retry_policy.is_retryable(execution_result.stderr or "", execution_result.exit_code)
        and orchestrator.planner.llm_client
        and hasattr(orchestrator.planner.llm_client, "generate")
    ):
        execution_result, self_healed = orchestrator._self_heal_step(step, execution_result, workflow_id, executor)

    criteria = step.params.get("verification", {})
    verification_report = orchestrator.verifier.verify(execution_result, criteria)

    duration = time.time() - step_start
    orchestrator.telemetry.record_step(
        step_order=step.order,
        title=step.title,
        duration=duration,
        exit_code=execution_result.exit_code,
        self_healed=self_healed,
        agent=step.agent,
    )

    return StepResult(
        step=step,
        execution=execution_result,
        verification=verification_report,
        self_healed=self_healed,
        constitutional_score=step_review.overall_score if step_review else None,
        constitutional_review={
            "overall_score": step_review.overall_score,
            "blocked": step_review.blocked,
            "passed": step_review.passed,
            "principles": [
                {
                    "principle": r.principle.value,
                    "score": r.score,
                    "passed": r.passed,
                    "reason": r.reason,
                }
                for r in step_review.principle_results
            ],
        }
        if step_review
        else None,
    )


__all__ = ["execute_and_verify_step"]
