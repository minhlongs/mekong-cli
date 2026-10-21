# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PEV Orchestrator -- goal to plan to exec to verify to memory loop.

Wires existing PEV components into a single end-to-end pipeline.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from src.core.memory_bridge import MemoryBridge, get_bridge
from src.core.planner import PlanningContext, RecipePlanner
from src.core.verifier import RecipeVerifier, VerificationReport
from src.harness.pev.executor import RecipeExecutor
from src.harness.pev.metrics_collector import get_pev_metrics
from src.harness.pev.orchestrator_models import (
    PipelineResult,
    build_summary_report,
    detect_recipe_intent,
    record_pipeline_memory,
)
from src.harness.pev.parser import Recipe, RecipeParser


def _detect_recipe_intent(recipe: "Recipe") -> str:
    """Detect intent for a parsed recipe using B3 unified NLU."""
    return detect_recipe_intent(recipe)


class PEVOrchestrator:
    """Coordinates the full Plan-Execute-Verify pipeline."""

    def __init__(self, memory: MemoryBridge | None = None) -> None:
        self.memory = memory
        self._parser = RecipeParser()
        self._planner = RecipePlanner()

    def run(self, recipe_or_goal: str | Path) -> PipelineResult:
        """Run a full PEV pipeline."""
        pipeline_id = uuid.uuid4().hex[:8]
        t0 = time.perf_counter()

        error: str | None = None
        goal = ""
        recipe: Recipe | None = None

        try:
            recipe = self._resolve_recipe(recipe_or_goal)
            goal = (recipe.title or recipe.name or str(recipe_or_goal)).strip()

            executor = RecipeExecutor(recipe)
            verifier = RecipeVerifier(strict_mode=True)

            metrics = get_pev_metrics()
            metrics.record_pipeline_start(pipeline_id)

            passed = 0
            failed = 0

            for step in recipe.steps:
                step_t0 = time.perf_counter()
                result = executor.execute_step(step)
                duration_ms = (time.perf_counter() - step_t0) * 1000

                metrics.record_step_result(
                    pipeline_id,
                    step.order,
                    success=result.exit_code == 0,
                    duration_ms=duration_ms,
                )

                criteria = (step.params or {}).get("verification", {})
                if criteria:
                    step_report = verifier.verify(result, criteria)
                    if step_report.passed:
                        passed += 1
                    else:
                        failed += 1
                else:
                    if result.exit_code == 0:
                        passed += 1
                    else:
                        failed += 1

            status = "completed" if failed == 0 else "failed"
            metrics.record_pipeline_end(pipeline_id, status)

        except Exception as exc:
            error = str(exc)
            passed = 0
            failed = 0

        duration_ms = (time.perf_counter() - t0) * 1000
        steps_total = len(recipe.steps) if recipe else 0

        verification_report: VerificationReport | None = None
        if recipe is not None:
            try:
                verification_report = self._build_summary_report(
                    recipe, passed, failed
                )
            except Exception:
                pass

        record_pipeline_memory(
            self.memory or get_bridge(),
            pipeline_id,
            goal,
            passed,
            failed,
            steps_total,
            duration_ms,
            error,
        )

        success = error is None and failed == 0 and recipe is not None

        return PipelineResult(
            success=success,
            pipeline_id=pipeline_id,
            goal=goal,
            steps_total=steps_total,
            steps_passed=passed,
            steps_failed=failed,
            duration_ms=duration_ms,
            error=error,
            recipe=(
                recipe
                if recipe is not None
                else Recipe(name=str(recipe_or_goal), title=str(recipe_or_goal))
            ),
            verification_report=verification_report,
        )

    def _resolve_recipe(self, recipe_or_goal: str | Path) -> Recipe:
        """Return a ``Recipe`` from a file path or decompose a goal string."""
        if isinstance(recipe_or_goal, Path) or (
            isinstance(recipe_or_goal, str)
            and (
                recipe_or_goal.endswith(".md")
                or Path(recipe_or_goal).suffix == ".md"
            )
            and Path(recipe_or_goal).exists()
        ):
            path = Path(recipe_or_goal)
            parsed = self._parser.parse(path)
            if not parsed.title:
                parsed.title = path.stem
            parsed.intent = _detect_recipe_intent(parsed)
            return parsed

        goal = str(recipe_or_goal)
        context = PlanningContext(goal=goal)
        return self._planner.plan(goal, context)

    def _build_summary_report(
        self, recipe: Recipe, passed: int, failed: int
    ) -> VerificationReport:
        """Build a top-level VerificationReport summarising whole-pipeline status."""
        return build_summary_report(recipe, passed, failed)
