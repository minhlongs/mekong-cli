"""Mekong CLI v3.1 - AGI Score Calculator.

Transparent scoring formula based on real benchmark results,
not self-reported metrics. Each dimension weighted explicitly.

Formula:
    agi_score = (
        task_success_rate * 40 +      # 40pts: Core delivery
        self_healing_rate * 20 +       # 20pts: Recovery ability
        recipe_reuse_rate * 15 +       # 15pts: Learning/memory
        avg_quality_score * 15 +       # 15pts: Output quality
        subsystem_coverage * 10        # 10pts: All 9 active
    ) / 100
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .telemetry_models import SubsystemHealthReport


# 9 AGI subsystems in the Mekong architecture
AGI_SUBSYSTEMS = [
    "memory",
    "reflection",
    "world_model",
    "planning",
    "execution",
    "self_healing",
    "learning",
    "event_bus",
    "telemetry",
]


@dataclass
class BenchmarkResult:
    """Raw benchmark results from test runs."""

    total_tasks: int = 0
    successful_tasks: int = 0
    self_healed_tasks: int = 0
    total_retries: int = 0
    recipes_reused: int = 0
    total_recipe_opportunities: int = 0
    quality_scores: list[float] = field(default_factory=list)


@dataclass
class AGIScoreBreakdown:
    """Detailed AGI score with per-dimension breakdown."""

    task_success_rate: float = 0.0
    self_healing_rate: float = 0.0
    recipe_reuse_rate: float = 0.0
    avg_quality_score: float = 0.0
    subsystem_coverage: float = 0.0
    total_score: float = 0.0

    # Weights (must sum to 100)
    WEIGHT_SUCCESS: int = 40
    WEIGHT_HEALING: int = 20
    WEIGHT_REUSE: int = 15
    WEIGHT_QUALITY: int = 15
    WEIGHT_COVERAGE: int = 10

    def to_dict(self) -> dict:
        """Serialize score breakdown."""
        return {
            "total_score": round(self.total_score, 2),
            "dimensions": {
                "task_success_rate": {
                    "value": round(self.task_success_rate, 4),
                    "weight": self.WEIGHT_SUCCESS,
                    "weighted": round(self.task_success_rate * self.WEIGHT_SUCCESS, 2),
                },
                "self_healing_rate": {
                    "value": round(self.self_healing_rate, 4),
                    "weight": self.WEIGHT_HEALING,
                    "weighted": round(self.self_healing_rate * self.WEIGHT_HEALING, 2),
                },
                "recipe_reuse_rate": {
                    "value": round(self.recipe_reuse_rate, 4),
                    "weight": self.WEIGHT_REUSE,
                    "weighted": round(self.recipe_reuse_rate * self.WEIGHT_REUSE, 2),
                },
                "avg_quality_score": {
                    "value": round(self.avg_quality_score, 4),
                    "weight": self.WEIGHT_QUALITY,
                    "weighted": round(self.avg_quality_score * self.WEIGHT_QUALITY, 2),
                },
                "subsystem_coverage": {
                    "value": round(self.subsystem_coverage, 4),
                    "weight": self.WEIGHT_COVERAGE,
                    "weighted": round(self.subsystem_coverage * self.WEIGHT_COVERAGE, 2),
                },
            },
        }


def calculate_agi_score(
    benchmark: BenchmarkResult,
    health_report: SubsystemHealthReport | None = None,
) -> AGIScoreBreakdown:
    """Calculate transparent AGI score from benchmark results.

    Args:
        benchmark: Raw benchmark results from test runs
        health_report: Optional subsystem health report

    Returns:
        AGIScoreBreakdown with per-dimension scores
    """
    score = AGIScoreBreakdown()

    # Dimension 1: Task success rate (0.0 - 1.0)
    if benchmark.total_tasks > 0:
        score.task_success_rate = benchmark.successful_tasks / benchmark.total_tasks

    # Dimension 2: Self-healing rate (0.0 - 1.0)
    failed_tasks = benchmark.total_tasks - benchmark.successful_tasks
    healable = failed_tasks + benchmark.self_healed_tasks
    if healable > 0:
        score.self_healing_rate = benchmark.self_healed_tasks / healable

    # Dimension 3: Recipe reuse rate (0.0 - 1.0)
    if benchmark.total_recipe_opportunities > 0:
        score.recipe_reuse_rate = (
            benchmark.recipes_reused / benchmark.total_recipe_opportunities
        )

    # Dimension 4: Average quality score (0.0 - 1.0)
    if benchmark.quality_scores:
        score.avg_quality_score = sum(benchmark.quality_scores) / len(
            benchmark.quality_scores
        )

    # Dimension 5: Subsystem coverage (0.0 - 1.0)
    if health_report:
        score.subsystem_coverage = health_report.coverage
    else:
        score.subsystem_coverage = 0.0

    # Calculate total weighted score
    score.total_score = (
        score.task_success_rate * score.WEIGHT_SUCCESS
        + score.self_healing_rate * score.WEIGHT_HEALING
        + score.recipe_reuse_rate * score.WEIGHT_REUSE
        + score.avg_quality_score * score.WEIGHT_QUALITY
        + score.subsystem_coverage * score.WEIGHT_COVERAGE
    ) / 100

    return score


def score_label(score: float) -> str:
    """Human-readable label for an AGI score.

    Args:
        score: AGI score (0.0 - 1.0)

    Returns:
        Label string
    """
    if score >= 0.95:
        return "Exceptional"
    if score >= 0.85:
        return "Strong"
    if score >= 0.70:
        return "Competent"
    if score >= 0.50:
        return "Developing"
    return "Nascent"


__all__ = [
    "AGI_SUBSYSTEMS",
    "AGIScoreBreakdown",
    "BenchmarkResult",
    "calculate_agi_score",
    "score_label",
]
