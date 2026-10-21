# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Constitutional AI review and metric hooks for RecipeOrchestrator."""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from ..constitution import ConstitutionalReview as ConReview
from ..parser import Recipe, RecipeStep

if TYPE_CHECKING:
    from .runner import RecipeOrchestrator


def review_plan_constitution(
    orchestrator: RecipeOrchestrator, recipe: Recipe, goal: str
) -> ConReview:
    """Constitutional review of entire plan (PLAN hook)."""
    context = {
        "goal": goal,
        "recipe_name": recipe.name,
        "step_count": len(recipe.steps),
    }

    parameters = {
        "action_type": "plan",
        "steps": [
            {
                "title": step.title,
                "type": step.params.get("type", "shell") if step.params else "shell",
                "agent": step.agent,
            }
            for step in recipe.steps
        ],
    }

    metadata = {
        "source": "orchestrator",
        "phase": "plan",
        "recipe": recipe.name,
    }

    return orchestrator.constitution.review(
        action="plan:review",
        context=context,
        parameters=parameters,
        metadata=metadata,
    )


def review_step_constitution(
    orchestrator: RecipeOrchestrator, step: RecipeStep, workflow_id: str = ""
) -> ConReview:
    """Constitutional review of single step (EXECUTE hook)."""
    context = {
        "workflow_id": workflow_id,
        "step_order": step.order,
        "step_title": step.title,
    }

    parameters = {
        "command": step.description.strip(),
        "type": step.params.get("type", "shell") if step.params else "shell",
        "agent": step.agent,
        "verification": step.params.get("verification", {}),
    }

    metadata = {
        "source": "orchestrator",
        "phase": "execute",
        "step": step.order,
    }

    return orchestrator.constitution.review(
        action="step:execute",
        context=context,
        parameters=parameters,
        metadata=metadata,
    )


def record_constitutional_metric(
    orchestrator: RecipeOrchestrator,
    phase: str,
    score: float,
    recipe_name: Optional[str] = None,
    step_order: Optional[int] = None,
) -> None:
    """Record constitutional score metric."""
    if hasattr(orchestrator.telemetry, "record_constitutional_score"):
        orchestrator.telemetry.record_constitutional_score(
            phase=phase,
            score=score,
            recipe=recipe_name,
            step=step_order,
        )
    else:
        logger = getattr(orchestrator, "logger", logging.getLogger("RecipeOrchestrator"))
        logger.info(
            f"Constitutional score [{phase}]: {score:.3f}",
            extra={"phase": phase, "score": score, "recipe": recipe_name, "step": step_order},
        )


__all__ = [
    "record_constitutional_metric",
    "review_plan_constitution",
    "review_step_constitution",
]
