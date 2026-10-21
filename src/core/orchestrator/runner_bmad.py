# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BMAD workflow execution and post-execution AGI bridge for RecipeOrchestrator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..parser import Recipe, RecipeStep
from .models import OrchestrationResult

if TYPE_CHECKING:
    from .runner import RecipeOrchestrator


def run_bmad_workflow(
    orchestrator: RecipeOrchestrator, workflow_id: str, context: Optional[Dict[str, Any]] = None
) -> OrchestrationResult:
    """Execute a BMAD workflow by ID."""
    if not orchestrator.bmad_loader:
        raise RuntimeError("BMAD loader not available")

    workflow = orchestrator.bmad_loader.get_workflow(workflow_id)
    if not workflow:
        raise ValueError(f"Workflow not found: {workflow_id}")

    step = RecipeStep(
        order=1,
        title=f"Execute {workflow.name}",
        description=f"# BMAD Workflow: {workflow_id}",
        params={"workflow_id": workflow_id, "context": context or {}},
    )
    recipe = Recipe(
        name=workflow.name,
        description=workflow.description,
        steps=[step],
        metadata={"agent_type": workflow.agent_type, "source": "bmad"},
    )
    return orchestrator.run_from_recipe(recipe)


def post_execution_agi(
    orchestrator: RecipeOrchestrator,
    goal: str,
    status: str,
    duration_ms: float,
    world_before: Optional[Any],
    errors: List[str],
) -> None:
    """Run post-execution AGI pipeline using current component references."""
    from .agi import AGIComponents as _A

    tmp = _A.__new__(_A)
    tmp.reflection = orchestrator._reflection
    tmp.world_model = orchestrator._world_model
    tmp.tool_registry = orchestrator._tool_registry
    tmp.collaboration = orchestrator._collaboration
    tmp.code_evolution = orchestrator._code_evolution
    tmp.vector_memory = orchestrator._vector_memory
    tmp.run_post_execution(goal, status, duration_ms, world_before, errors, orchestrator.console)


__all__ = ["post_execution_agi", "run_bmad_workflow"]
