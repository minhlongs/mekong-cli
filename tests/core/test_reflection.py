# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Mekong Reflection Engine (src/core/reflection.py).

All tests are hermetic and deterministic: event bus, filesystem persistence,
and LLM clients are mocked or scoped to tmp_path to achieve 100% statement
and branch coverage without side effects.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.event_bus import EventType
from src.core.reflection import (
    ConfidenceCalibrator,
    ReflectionEngine,
    ReflectionReport,
    StrategyRecord,
)


# ===========================================================================
# Dataclass & StrategyRecord Tests
# ===========================================================================


class TestReflectionReport:
    def test_default_values(self):
        r = ReflectionReport(goal="test", status="success")
        assert r.goal == "test"
        assert r.status == "success"
        assert r.duration_ms == 0.0
        assert r.strengths == []
        assert r.weaknesses == []
        assert r.alternative_approach == ""
        assert r.confidence_adjustment == 0.0
        assert r.lesson_learned == ""
        assert r.should_change_strategy is False
        assert isinstance(r.timestamp, float)

    def test_fields_settable(self):
        r = ReflectionReport(
            goal="deploy",
            status="failed",
            duration_ms=1250.0,
            strengths=["fast"],
            weaknesses=["crash"],
            alternative_approach="use fallback",
            confidence_adjustment=-0.5,
            lesson_learned="check health before deploy",
            should_change_strategy=True,
            timestamp=1234567.0,
        )
        assert r.duration_ms == 1250.0
        assert r.weaknesses == ["crash"]
        assert r.alternative_approach == "use fallback"
        assert r.confidence_adjustment == -0.5
        assert r.lesson_learned == "check health before deploy"
        assert r.should_change_strategy is True
        assert r.timestamp == 1234567.0


class TestStrategyRecord:
    def test_default_values(self):
        s = StrategyRecord(strategy_name="fast_deploy")
        assert s.strategy_name == "fast_deploy"
        assert s.uses == 0
        assert s.successes == 0
        assert s.failures == 0
        assert s.avg_duration_ms == 0.0
        assert s.success_rate == 0.0

    def test_success_rate_calculation(self):
        s = StrategyRecord(
            strategy_name="robust_deploy",
            uses=10,
            successes=8,
            failures=2,
            avg_duration_ms=250.0,
        )
        assert s.success_rate == 0.8


# ===========================================================================
# ConfidenceCalibrator Tests
# ===========================================================================


class TestConfidenceCalibrator:
    def test_empty_calibration_error(self):
        cal = ConfidenceCalibrator()
        assert cal.get_calibration_error() == 0.5
        assert cal.prediction_count == 0

    def test_record_and_max_history_clamping(self):
        cal = ConfidenceCalibrator()
        for i in range(150):
            cal.record(0.8, i % 2 == 0)
        assert cal.prediction_count == 100

    def test_calibration_error_with_data(self):
        cal = ConfidenceCalibrator()
        # Predictions across different buckets: 0.1 (bucket 0), 0.3 (bucket 1), 0.5 (bucket 2), 0.7 (bucket 3), 0.95 (bucket 4)
        cal.record(0.1, False)
        cal.record(0.3, True)
        cal.record(0.5, True)
        cal.record(0.7, True)
        cal.record(0.95, True)
        cal.record(1.0, True)  # bucket 4 clamping
        error = cal.get_calibration_error()
        assert 0.0 <= error <= 1.0

    def test_calibration_error_total_count_zero_fallback(self):
        cal = ConfidenceCalibrator()

        class FakePredList(list):
            def __len__(self):
                return 10

        cal._predictions = FakePredList()
        assert cal.get_calibration_error() == 0.5

    def test_get_adjusted_confidence_less_than_10_predictions(self):
        cal = ConfidenceCalibrator()
        for _ in range(5):
            cal.record(0.9, True)
        # Should return raw confidence untouched when prediction count < 10
        assert cal.get_adjusted_confidence(0.75) == 0.75

    def test_get_adjusted_confidence_overconfident_reduction(self):
        cal = ConfidenceCalibrator()
        # 15 predictions with 0.95 predicted but all failing (overconfident)
        for _ in range(15):
            cal.record(0.95, False)
        adjusted = cal.get_adjusted_confidence(0.9)
        assert adjusted < 0.9

    def test_get_adjusted_confidence_underconfident_increase(self):
        cal = ConfidenceCalibrator()
        # 15 predictions with 0.1 predicted but all succeeding (underconfident)
        for _ in range(15):
            cal.record(0.1, True)
        adjusted = cal.get_adjusted_confidence(0.2)
        assert adjusted > 0.2

    def test_get_adjusted_confidence_clamping_bounds(self):
        cal = ConfidenceCalibrator()
        # Extreme overconfidence -> should not go below 0.05
        for _ in range(25):
            cal.record(1.0, False)
        assert cal.get_adjusted_confidence(0.1) == 0.05

        # Extreme underconfidence -> should not exceed 0.99
        cal2 = ConfidenceCalibrator()
        for _ in range(25):
            cal2.record(0.0, True)
        assert cal2.get_adjusted_confidence(0.95) == 0.99


# ===========================================================================
# ReflectionEngine Initialization & Persistence
# ===========================================================================


class TestReflectionEngineInitAndPersist:
    def test_init_defaults(self):
        engine = ReflectionEngine()
        assert engine.llm_client is None
        assert isinstance(engine.calibrator, ConfidenceCalibrator)
        assert engine._reflections == []
        assert engine._strategies == {}

    def test_init_with_llm(self):
        fake_llm = MagicMock()
        engine = ReflectionEngine(llm_client=fake_llm)
        assert engine.llm_client is fake_llm

    def test_persist_writes_jsonl(self, tmp_path):
        engine = ReflectionEngine()
        log_file = tmp_path / "reflections.jsonl"
        with patch("src.core.reflection.REFLECTION_PERSIST_PATH", str(log_file)):
            report = ReflectionReport(goal="test_goal", status="success")
            engine._persist(report)
            assert log_file.exists()
            content = log_file.read_text(encoding="utf-8")
            assert "test_goal" in content

    def test_persist_handles_exception(self):
        engine = ReflectionEngine()
        with patch("pathlib.Path.mkdir", side_effect=OSError("permission denied")):
            report = ReflectionReport(goal="test_goal", status="success")
            # Should catch and not raise
            engine._persist(report)


# ===========================================================================
# ReflectionEngine Rule-based & LLM Reflection
# ===========================================================================


class TestReflectionEngineReflect:
    @pytest.fixture(autouse=True)
    def setup_engine(self, tmp_path):
        self.tmp_path = tmp_path
        self.engine = ReflectionEngine()
        # Avoid writing to user's real home directory
        self.persist_patch = patch(
            "src.core.reflection.REFLECTION_PERSIST_PATH",
            str(tmp_path / "log.jsonl"),
        )
        self.persist_patch.start()
        yield
        self.persist_patch.stop()

    def test_reflect_success_fast_execution(self):
        with patch("src.core.reflection.get_event_bus") as mock_bus:
            report = self.engine.reflect(
                goal="build app",
                status="success",
                duration_ms=3000.0,
                predicted_confidence=0.85,
            )
            assert report.status == "success"
            assert report.confidence_adjustment == 0.05
            assert "Task completed successfully" in report.strengths
            assert "Fast execution time" in report.strengths
            mock_bus.return_value.emit.assert_called_once_with(
                EventType.AUTONOMOUS_CYCLE,
                {
                    "event": "reflection_complete",
                    "goal": "build app",
                    "status": "success",
                    "should_change_strategy": False,
                    "lesson": "",
                },
            )

    def test_reflect_success_slow_execution(self):
        report = self.engine.reflect(
            goal="train model",
            status="success",
            duration_ms=10000.0,
        )
        assert "Task completed successfully" in report.strengths
        assert "Fast execution time" not in report.strengths

    def test_reflect_failure_single(self):
        report = self.engine.reflect(
            goal="deploy container",
            status="failed",
            error="connection timeout",
        )
        assert report.status == "failed"
        assert report.confidence_adjustment == -0.1
        assert any("connection timeout" in w for w in report.weaknesses)
        assert report.should_change_strategy is False

    def test_reflect_failure_empty_error_fallback(self):
        report = self.engine.reflect(
            goal="deploy container",
            status="failed",
            error="",
        )
        assert any("unknown error" in w for w in report.weaknesses)

    def test_reflect_repeated_failures_triggers_strategy_change(self):
        # 2 prior failures with the same goal
        self.engine.reflect("deploy container", "failed", error="err 1")
        self.engine.reflect("deploy container", "failed", error="err 2")

        # 3rd failure
        report = self.engine.reflect("deploy container", "failed", error="err 3")
        assert report.should_change_strategy is True
        assert report.confidence_adjustment == -0.2
        assert any("Repeated failure (3 times)" in w for w in report.weaknesses)

    def test_reflect_max_reflections_truncation(self):
        self.engine.MAX_REFLECTIONS = 5
        for i in range(10):
            self.engine.reflect(f"goal-{i}", "success")
        assert len(self.engine._reflections) == 5
        assert self.engine._reflections[-1].goal == "goal-9"

    def test_reflect_with_llm_success(self):
        fake_llm = MagicMock()
        fake_llm.generate_json.return_value = {
            "strengths": ["Clear specification", "Fast execution time"],
            "weaknesses": ["Minor memory spike"],
            "alternative_approach": "Use streaming processing",
            "lesson_learned": "Always buffer outputs",
            "confidence_adjustment": "0.15",
            "should_change_strategy": True,
        }
        self.engine.llm_client = fake_llm

        report = self.engine.reflect(
            goal="stream events",
            status="success",
            duration_ms=2000.0,
        )
        assert "Clear specification" in report.strengths
        assert "Minor memory spike" in report.weaknesses
        assert report.alternative_approach == "Use streaming processing"
        assert report.lesson_learned == "Always buffer outputs"
        assert report.confidence_adjustment == 0.15
        assert report.should_change_strategy is True
        # Deduplication check
        assert report.strengths.count("Fast execution time") == 1

    def test_reflect_with_llm_exception_caught(self):
        fake_llm = MagicMock()
        # Invalid float for confidence_adjustment to trigger except block in reflect()
        fake_llm.generate_json.return_value = {
            "confidence_adjustment": "not-a-float",
        }
        self.engine.llm_client = fake_llm

        report = self.engine.reflect("process batch", "success")
        assert report.status == "success"
        assert "Task completed successfully" in report.strengths

    def test_reflect_confidence_adjustment_clamping(self):
        fake_llm = MagicMock()
        fake_llm.generate_json.return_value = {
            "confidence_adjustment": 2.5,  # Out of range
        }
        self.engine.llm_client = fake_llm

        report = self.engine.reflect("task", "success")
        assert report.confidence_adjustment == 1.0

    def test_reflect_with_llm_without_optional_fields(self):
        fake_llm = MagicMock()
        fake_llm.generate_json.return_value = {
            "strengths": ["Clear spec"],
        }
        self.engine.llm_client = fake_llm
        report = self.engine.reflect("task", "success")
        assert report.confidence_adjustment == 0.05
        assert report.should_change_strategy is False

    def test_reflect_llm_client_without_generate_json(self):
        self.engine.llm_client = object()
        report = self.engine.reflect("task", "success")
        assert report.status == "success"


# ===========================================================================
# LLM Reflect Direct Tests
# ===========================================================================


class TestLLMReflectDirect:
    def test_llm_reflect_no_llm_client(self):
        engine = ReflectionEngine(llm_client=None)
        assert engine._llm_reflect("goal", "success", 100.0, "") == {}

    def test_llm_reflect_with_previous_reflections_and_empty_error(self):
        engine = ReflectionEngine()
        engine._reflections.append(ReflectionReport(
            goal="prev 1", status="failed", lesson_learned="watch bounds",
        ))
        engine._reflections.append(ReflectionReport(
            goal="prev 2", status="success", lesson_learned="",  # fallback to 'no lesson'
        ))

        fake_llm = MagicMock()
        fake_llm.generate_json.return_value = {"strengths": ["good"]}
        engine.llm_client = fake_llm

        res = engine._llm_reflect("curr", "success", 50.0, error="")
        assert res == {"strengths": ["good"]}

        prompt_arg = fake_llm.generate_json.call_args[0][0]
        assert "Error: none" in prompt_arg
        assert "watch bounds" in prompt_arg
        assert "no lesson" in prompt_arg

    def test_llm_reflect_exception_returns_empty_dict(self):
        fake_llm = MagicMock()
        fake_llm.generate_json.side_effect = ValueError("bad json")
        engine = ReflectionEngine(llm_client=fake_llm)
        assert engine._llm_reflect("curr", "success", 50.0, "err") == {}

    def test_llm_reflect_non_dict_returns_empty_dict(self):
        fake_llm = MagicMock()
        fake_llm.generate_json.return_value = "string instead of dict"
        engine = ReflectionEngine(llm_client=fake_llm)
        assert engine._llm_reflect("curr", "success", 50.0, "err") == {}


# ===========================================================================
# Strategy Suggestion, Recent & Stats Tests
# ===========================================================================


class TestStrategySuggestionAndStats:
    def test_strategy_suggestion_no_prior_data(self):
        engine = ReflectionEngine()
        assert engine.get_strategy_suggestion("unknown task") == "No prior data. Using default strategy."

    def test_strategy_suggestion_all_successes(self):
        engine = ReflectionEngine()
        engine._reflections.append(ReflectionReport(goal="optimize query", status="success"))
        msg = engine.get_strategy_suggestion("optimize query")
        assert msg == "Previous attempts all succeeded. Continue current approach."

    def test_strategy_suggestion_failures_exceed_successes_with_alternative(self):
        engine = ReflectionEngine()
        engine._reflections.extend([
            ReflectionReport(goal="sync db", status="failed", alternative_approach="use cdc"),
            ReflectionReport(goal="sync db", status="failed", alternative_approach="use async replication"),
            ReflectionReport(goal="sync db", status="success"),
        ])
        msg = engine.get_strategy_suggestion("sync db")
        assert "Try: use async replication" in msg

    def test_strategy_suggestion_failures_exceed_successes_without_alternative(self):
        engine = ReflectionEngine()
        engine._reflections.extend([
            ReflectionReport(goal="sync db", status="failed", alternative_approach=""),
            ReflectionReport(goal="sync db", status="failed", alternative_approach=""),
        ])
        msg = engine.get_strategy_suggestion("sync db")
        assert msg == "Previous approach unreliable. Consider a different strategy."

    def test_strategy_suggestion_mixed_results(self):
        engine = ReflectionEngine()
        engine._reflections.extend([
            ReflectionReport(goal="sync db", status="success"),
            ReflectionReport(goal="sync db", status="success"),
            ReflectionReport(goal="sync db", status="failed"),
        ])
        msg = engine.get_strategy_suggestion("sync db")
        assert msg == "Mixed results. Current approach works but may need refinement."

    def test_get_recent(self):
        engine = ReflectionEngine()
        for i in range(10):
            engine._reflections.append(ReflectionReport(goal=f"g{i}", status="success"))
        recent = engine.get_recent(limit=3)
        assert len(recent) == 3
        assert recent[-1].goal == "g9"

    def test_get_stats_empty(self):
        engine = ReflectionEngine()
        stats = engine.get_stats()
        assert stats["total_reflections"] == 0
        assert stats["calibration_error"] == 0.5
        assert stats["strategy_changes_suggested"] == 0

    def test_get_stats_populated(self):
        engine = ReflectionEngine()
        engine._reflections.extend([
            ReflectionReport(
                goal="g1", status="success", confidence_adjustment=0.1,
                lesson_learned="lesson 1", should_change_strategy=False,
            ),
            ReflectionReport(
                goal="g2", status="failed", confidence_adjustment=-0.2,
                lesson_learned="lesson 2", should_change_strategy=True,
            ),
            ReflectionReport(
                goal="g3", status="success", confidence_adjustment=0.0,
                lesson_learned="", should_change_strategy=False,
            ),
        ])
        engine.calibrator.record(0.8, True)

        stats = engine.get_stats()
        assert stats["total_reflections"] == 3
        assert stats["prediction_count"] == 1
        assert stats["strategy_changes_suggested"] == 1
        assert pytest.approx(stats["avg_confidence_adjustment"], 0.001) == -0.1 / 3
        assert stats["lessons_learned"] == ["lesson 1", "lesson 2"]
