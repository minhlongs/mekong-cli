# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Goal workflow execution, planning, and NLU shortcut routines for RecipeOrchestrator."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, TYPE_CHECKING

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..memory_canonical import MemoryEntry
from ..planner import PlanningContext
from .models import OrchestrationResult

if TYPE_CHECKING:
    from .runner import RecipeOrchestrator


def try_nlu_shortcut(
    orchestrator: RecipeOrchestrator,
    goal: str,
    progress_callback: Optional[Callable[..., None]],
    goal_start_time: float,
    world_before: Optional[Any],
) -> Optional[OrchestrationResult]:
    """Try to match goal to a known recipe via NLU. Returns result or None."""
    intent_result = orchestrator.nlu.classify(goal)
    if not (intent_result.confidence > 0.7 and intent_result.suggested_recipe):
        return None

    from ..smart_router import SmartRouter

    router = SmartRouter(memory_store=orchestrator.memory)
    route = router.route(intent_result)
    if not (route.action == "recipe" and route.recipe_path):
        return None

    from pathlib import Path as _Path
    from ..parser import RecipeParser

    try:
        recipe = RecipeParser().parse(_Path(route.recipe_path))
        orchestrator.console.print(
            f"[green]NLU:[/green] Matched recipe '{route.recipe_name}'"
        )
        result = orchestrator.run_from_recipe(recipe, progress_callback=progress_callback)
        orchestrator.telemetry.finish_trace()
        duration_ms = (time.time() - goal_start_time) * 1000
        record_memory(orchestrator, goal, result, duration_ms)
        orchestrator._post_execution_agi(
            goal, result.status.value, duration_ms, world_before, result.errors
        )
        return result
    except Exception:
        return None


def record_memory(
    orchestrator: RecipeOrchestrator, goal: str, result: OrchestrationResult, duration_ms: float
) -> None:
    """Record execution outcome in persistent memory."""
    entry = MemoryEntry(
        goal=goal,
        status=result.status.value,
        duration_ms=duration_ms,
        error_summary="; ".join(result.errors[:3]) if result.errors else "",
        recipe_used=result.recipe.name if result.recipe else "",
    )
    orchestrator.memory.record(entry)


def execute_goal_workflow(
    orchestrator: RecipeOrchestrator,
    goal: str,
    context: Optional[PlanningContext] = None,
    progress_callback: Optional[Callable[..., None]] = None,
) -> OrchestrationResult:
    """Execute complete workflow from high-level goal (PLAN -> EXECUTE -> VERIFY)."""
    orchestrator.console.print(
        Panel(
            f"[bold]Goal:[/bold] {goal}",
            title="🎯 Mekong Orchestrator",
            border_style="cyan",
        )
    )

    goal_start_time = time.time()
    orchestrator.telemetry.start_trace(goal)

    # AGI pre-execution hints + world snapshot
    world_before = orchestrator._agi.print_pre_execution_hints(goal, orchestrator.console)

    # NLU Phase — try direct recipe match
    result = orchestrator._try_nlu_shortcut(
        goal, progress_callback, goal_start_time, world_before
    )
    if result is not None:
        return result

    # PHASE 1: PLAN
    orchestrator.console.print("\n[bold yellow]📋 PHASE 1: PLANNING[/bold yellow]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=orchestrator.console,
    ) as progress:
        task = progress.add_task("Generating execution plan...", total=None)
        recipe = orchestrator.planner.plan(goal, context)
        progress.update(task, completed=True)

    plan_issues = orchestrator.planner.validate_plan(recipe)
    if plan_issues:
        orchestrator.console.print("[yellow]⚠️ Plan validation warnings:[/yellow]")
        for issue in plan_issues:
            orchestrator.console.print(f" • {issue}")

    # Constitutional review of plan (PLAN hook)
    plan_constitutional_review = orchestrator._review_plan_constitution(recipe, goal)
    if plan_constitutional_review.blocked:
        orchestrator.console.print("[bold red]🚫 Plan blocked by Constitutional AI[/bold red]")
        orchestrator.console.print(f"Score: {plan_constitutional_review.overall_score:.2f}")
        for res in plan_constitutional_review.principle_results:
            if not res.passed:
                orchestrator.console.print(f" • {res.principle.value}: {res.reason}")
        if orchestrator.constitutional_mode == "enforce":
            raise ValueError(
                f"Plan failed constitutional review "
                f"(score={plan_constitutional_review.overall_score:.2f})"
            )
        else:
            orchestrator.console.print("[yellow]⚠️ Continuing in non-enforce mode[/yellow]")

    orchestrator.console.print(f"[green]✓[/green] Generated {len(recipe.steps)} steps")
    orchestrator._record_constitutional_metric(
        phase="plan",
        score=plan_constitutional_review.overall_score,
        recipe_name=recipe.name,
    )

    # PHASE 2 & 3: EXECUTE -> VERIFY
    result = orchestrator.run_from_recipe(recipe, progress_callback=progress_callback)

    # Attach plan constitutional score
    result.constitutional_plan_score = plan_constitutional_review.overall_score

    # Calculate average step constitutional score
    step_scores = [
        sr.constitutional_score
        for sr in result.step_results
        if sr.constitutional_score is not None
    ]
    if step_scores:
        result.constitutional_average_step_score = sum(step_scores) / len(step_scores)

    # Overall compliance (plan + average steps)
    if result.constitutional_plan_score and result.constitutional_average_step_score:
        combined = (
            result.constitutional_plan_score + result.constitutional_average_step_score
        ) / 2
        result.constitutional_compliant = combined >= 0.7

    orchestrator.telemetry.finish_trace()
    duration_ms = (time.time() - goal_start_time) * 1000
    orchestrator._record_memory(goal, result, duration_ms)
    orchestrator._post_execution_agi(
        goal, result.status.value, duration_ms, world_before, result.errors
    )

    return result


__all__ = ["execute_goal_workflow", "record_memory", "try_nlu_shortcut"]
