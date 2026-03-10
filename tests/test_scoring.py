"""Tests for AGI Score Calculator — transparent scoring formula."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.scoring import (
    AGI_SUBSYSTEMS,
    AGIScoreBreakdown,
    BenchmarkResult,
    calculate_agi_score,
    score_label,
)
from src.core.telemetry_models import SubsystemHealth, SubsystemHealthReport


class TestBenchmarkResult:
    def test_default_values(self) -> None:
        b = BenchmarkResult()
        assert b.total_tasks == 0
        assert b.successful_tasks == 0
        assert b.quality_scores == []

    def test_custom_values(self) -> None:
        b = BenchmarkResult(total_tasks=10, successful_tasks=8)
        assert b.total_tasks == 10
        assert b.successful_tasks == 8


class TestCalculateAGIScore:
    def test_zero_benchmark(self) -> None:
        score = calculate_agi_score(BenchmarkResult())
        assert score.total_score == 0.0
        assert score.task_success_rate == 0.0

    def test_perfect_score(self) -> None:
        b = BenchmarkResult(
            total_tasks=10,
            successful_tasks=10,
            self_healed_tasks=0,
            recipes_reused=5,
            total_recipe_opportunities=5,
            quality_scores=[1.0] * 10,
        )
        report = SubsystemHealthReport()
        for name in AGI_SUBSYSTEMS:
            h = SubsystemHealth(subsystem=name, activation_count=1)
            report.add_subsystem(h)

        score = calculate_agi_score(b, report)
        assert score.task_success_rate == 1.0
        assert score.recipe_reuse_rate == 1.0
        assert score.avg_quality_score == 1.0
        assert score.subsystem_coverage == 1.0
        # self_healing_rate=0 (no failures to heal) → 80/100 = 0.80
        assert score.total_score == pytest.approx(0.80, abs=0.01)

    def test_partial_score(self) -> None:
        b = BenchmarkResult(
            total_tasks=10,
            successful_tasks=7,
            self_healed_tasks=2,
            recipes_reused=3,
            total_recipe_opportunities=10,
            quality_scores=[0.8, 0.7, 0.9],
        )
        score = calculate_agi_score(b)
        assert 0.0 < score.task_success_rate < 1.0
        assert 0.0 < score.self_healing_rate < 1.0
        assert 0.0 < score.total_score < 1.0

    def test_self_healing_rate(self) -> None:
        b = BenchmarkResult(
            total_tasks=10,
            successful_tasks=8,
            self_healed_tasks=2,
        )
        score = calculate_agi_score(b)
        # healable = (10-8) + 2 = 4, healed = 2
        assert score.self_healing_rate == pytest.approx(0.5)

    def test_no_health_report(self) -> None:
        b = BenchmarkResult(total_tasks=5, successful_tasks=5)
        score = calculate_agi_score(b, health_report=None)
        assert score.subsystem_coverage == 0.0

    def test_weights_sum_to_100(self) -> None:
        s = AGIScoreBreakdown()
        total = (
            s.WEIGHT_SUCCESS
            + s.WEIGHT_HEALING
            + s.WEIGHT_REUSE
            + s.WEIGHT_QUALITY
            + s.WEIGHT_COVERAGE
        )
        assert total == 100


class TestScoreLabel:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.96, "Exceptional"),
            (0.90, "Strong"),
            (0.75, "Competent"),
            (0.55, "Developing"),
            (0.30, "Nascent"),
            (0.0, "Nascent"),
        ],
    )
    def test_labels(self, score: float, expected: str) -> None:
        assert score_label(score) == expected


class TestAGIScoreBreakdownSerialization:
    def test_to_dict(self) -> None:
        b = BenchmarkResult(
            total_tasks=10,
            successful_tasks=9,
            quality_scores=[0.85],
        )
        score = calculate_agi_score(b)
        data = score.to_dict()

        assert "total_score" in data
        assert "dimensions" in data
        assert "task_success_rate" in data["dimensions"]
        assert data["dimensions"]["task_success_rate"]["weight"] == 40


class TestAGISubsystems:
    def test_subsystem_count(self) -> None:
        assert len(AGI_SUBSYSTEMS) == 9

    def test_known_subsystems(self) -> None:
        assert "memory" in AGI_SUBSYSTEMS
        assert "self_healing" in AGI_SUBSYSTEMS
        assert "planning" in AGI_SUBSYSTEMS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
