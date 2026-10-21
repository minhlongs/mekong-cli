# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and verification helpers for PEV Orchestrator."""

from __future__ import annotations

from typing import Any

from src.core.memory_bridge import MemoryKind, MemoryRecord
from src.core.verifier import (
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from src.harness.pev.parser import Recipe, RecipeParser


def detect_recipe_intent(recipe: Recipe) -> str:
    """Detect intent for a parsed recipe using B3 unified NLU."""
    try:
        return RecipeParser.detect_intent(recipe)
    except Exception:
        return ""


class PipelineResult:
    """Outcome of a full PEV pipeline run."""

    def __init__(
        self,
        *,
        success: bool,
        pipeline_id: str,
        goal: str,
        steps_total: int,
        steps_passed: int,
        steps_failed: int,
        duration_ms: float,
        error: str | None,
        recipe: Recipe,
        verification_report: VerificationReport | None,
    ) -> None:
        self.success = success
        self.pipeline_id = pipeline_id
        self.goal = goal
        self.steps_total = steps_total
        self.steps_passed = steps_passed
        self.steps_failed = steps_failed
        self.duration_ms = duration_ms
        self.error = error
        self.recipe = recipe
        self.verification_report = verification_report


def build_summary_report(
    recipe: Recipe, passed: int, failed: int
) -> VerificationReport:
    """Build a top-level VerificationReport summarising whole-pipeline status."""
    report = VerificationReport(
        passed=(failed == 0),
        checks=[
            VerificationCheck(
                name="pipeline_summary",
                status=(
                    VerificationStatus.PASSED
                    if failed == 0
                    else VerificationStatus.FAILED
                ),
                message=(
                    f"{passed}/{len(recipe.steps)} steps passed, "
                    f"{failed} failed"
                ),
                expected=len(recipe.steps),
                actual=passed,
            )
        ],
        warnings=[],
        errors=[],
    )

    if failed > 0:
        report.errors.append(f"{failed} step(s) failed")

    return report


def record_pipeline_memory(
    memory_bridge: Any,
    pipeline_id: str,
    goal: str,
    passed: int,
    failed: int,
    steps_total: int,
    duration_ms: float,
    error: str | None,
) -> None:
    """Record episodic memory for a finished pipeline run."""
    try:
        memory_bridge.record(
            MemoryRecord(
                content=(
                    f"Pipeline {pipeline_id}: goal={goal!r}, "
                    f"result={'OK' if error is None and failed == 0 else 'FAIL'}, "
                    f"steps={passed}/{steps_total} passed, "
                    f"duration_ms={duration_ms:.1f}"
                ),
                kind=MemoryKind.EPISODIC,
                metadata={
                    "pipeline_id": pipeline_id,
                    "goal": goal,
                    "steps_total": steps_total,
                    "steps_passed": passed,
                    "steps_failed": failed,
                    "duration_ms": duration_ms,
                    "error": error,
                },
            )
        )
    except Exception:
        pass
