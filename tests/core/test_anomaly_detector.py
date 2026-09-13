# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Mekong Usage Anomaly Detection (src/core/anomaly_detector.py).

All tests are hermetic and deterministic: filesystem persistence is scoped
to pytest tmp_path to achieve 100% statement and branch coverage without side effects.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.anomaly_detector import (
    Anomaly,
    AnomalyCategory,
    AnomalyType,
    BaselineStats,
    UsageAnomalyDetector,
    get_detector,
    reset_detector,
)
from src.core.usage_metering import (
    UsageEvent,
    UsageEventType,
    UsageMetering,
    get_metering,
    reset_metering,
)


# ===========================================================================
# BaselineStats Tests
# ===========================================================================


class TestBaselineStats:
    """Test BaselineStats dataclass."""

    def test_create_baseline(self) -> None:
        """Test creating a baseline with defaults."""
        baseline = BaselineStats(metric="api_calls:requests")
        assert baseline.metric == "api_calls:requests"
        assert baseline.mean == 0.0
        assert baseline.std_dev == 0.0
        assert baseline.sample_count == 0
        assert baseline.window_days == 7
        assert isinstance(baseline.last_updated, float)
        assert baseline.samples == []

    def test_to_dict(self) -> None:
        """Test baseline serialization."""
        baseline = BaselineStats(
            metric="test",
            mean=10.5,
            std_dev=2.3,
            sample_count=5,
            window_days=14,
            last_updated=123456789.0,
            samples=[10.0, 11.0],
        )
        data = baseline.to_dict()
        assert data["metric"] == "test"
        assert data["mean"] == 10.5
        assert data["std_dev"] == 2.3
        assert data["sample_count"] == 5
        assert data["window_days"] == 14
        assert data["last_updated"] == 123456789.0
        assert data["samples"] == [10.0, 11.0]

    def test_from_dict_full(self) -> None:
        """Test baseline deserialization with full data."""
        data = {
            "metric": "test_metric",
            "mean": 15.0,
            "std_dev": 3.0,
            "sample_count": 10,
            "window_days": 7,
            "last_updated": 1234567890.0,
            "samples": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
        baseline = BaselineStats.from_dict(data)
        assert baseline.metric == "test_metric"
        assert baseline.mean == 15.0
        assert baseline.std_dev == 3.0
        assert baseline.sample_count == 10
        assert baseline.samples == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_from_dict_empty_defaults(self) -> None:
        """Test baseline deserialization with empty dict."""
        baseline = BaselineStats.from_dict({})
        assert baseline.metric == ""
        assert baseline.mean == 0.0
        assert baseline.std_dev == 0.0
        assert baseline.sample_count == 0
        assert baseline.window_days == 7
        assert isinstance(baseline.last_updated, float)
        assert baseline.samples == []


# ===========================================================================
# Anomaly Tests
# ===========================================================================


class TestAnomaly:
    """Test Anomaly dataclass."""

    def test_create_anomaly(self) -> None:
        """Test creating an anomaly."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            category=AnomalyCategory.API_CALLS,
            metric="api_calls:requests",
            current_value=100.0,
            baseline_mean=50.0,
            baseline_std_dev=10.0,
            z_score=5.0,
            severity="high",
        )
        assert anomaly.anomaly_type == AnomalyType.SPIKE
        assert anomaly.category == AnomalyCategory.API_CALLS
        assert anomaly.metric == "api_calls:requests"
        assert anomaly.current_value == 100.0
        assert anomaly.baseline_mean == 50.0
        assert anomaly.baseline_std_dev == 10.0
        assert anomaly.z_score == 5.0
        assert anomaly.severity == "high"
        assert isinstance(anomaly.timestamp, float)
        assert anomaly.details == {}

    def test_to_dict(self) -> None:
        """Test anomaly serialization."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.DROP,
            category=AnomalyCategory.AGENT_SPAWNS,
            metric="agent_spawns:spawns",
            current_value=5.0,
            baseline_mean=50.0,
            baseline_std_dev=10.0,
            z_score=-4.5123,
            severity="high",
            timestamp=1234567.0,
            details={"key": "val"},
        )
        data = anomaly.to_dict()
        assert data["anomaly_type"] == "drop"
        assert data["category"] == "agent_spawns"
        assert data["metric"] == "agent_spawns:spawns"
        assert data["current_value"] == 5.0
        assert data["baseline_mean"] == 50.0
        assert data["baseline_std_dev"] == 10.0
        assert data["z_score"] == -4.51
        assert data["severity"] == "high"
        assert data["timestamp"] == 1234567.0
        assert data["details"] == {"key": "val"}

    def test_to_event_data(self) -> None:
        """Test formatting for usage:anomaly_detected event."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            category=AnomalyCategory.API_CALLS,
            metric="api_calls:requests",
            current_value=120.555,
            baseline_mean=50.123,
            baseline_std_dev=10.456,
            z_score=6.738,
            severity="critical",
        )
        event_data = anomaly.to_event_data()
        assert event_data["type"] == "spike"
        assert event_data["category"] == "api_calls"
        assert event_data["metric"] == "api_calls:requests"
        assert event_data["current"] == 120.555
        assert event_data["baseline_mean"] == 50.12
        assert event_data["baseline_std"] == 10.46
        assert event_data["z_score"] == 6.74
        assert event_data["severity"] == "critical"
        assert "Sudden increase detected" in event_data["message"]

    def test_generate_message_all_types(self) -> None:
        """Test human-readable message generation for all anomaly types."""
        spike = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            category=AnomalyCategory.API_CALLS,
            metric="api_calls:requests",
            current_value=100.0,
            baseline_mean=50.0,
            baseline_std_dev=10.0,
            z_score=5.0,
            severity="critical",
        )
        assert "Sudden increase detected" in spike._generate_message()

        drop = Anomaly(
            anomaly_type=AnomalyType.DROP,
            category=AnomalyCategory.LLM_CALLS,
            metric="llm_calls:rate",
            current_value=1.0,
            baseline_mean=50.0,
            baseline_std_dev=10.0,
            z_score=-4.9,
            severity="high",
        )
        assert "Sudden drop detected" in drop._generate_message()

        pattern = Anomaly(
            anomaly_type=AnomalyType.PATTERN_BREAK,
            category=AnomalyCategory.MODEL_USAGE,
            metric="model_usage:gpt4",
            current_value=50.0,
            baseline_mean=50.0,
            baseline_std_dev=10.0,
            z_score=0.0,
            severity="low",
        )
        assert "Pattern change detected" in pattern._generate_message()

        # Fallback for unknown type
        custom = Anomaly(
            anomaly_type="unknown_type",  # type: ignore[arg-type]
            category=AnomalyCategory.TOKEN_USAGE,
            metric="token_usage:tokens",
            current_value=10.0,
            baseline_mean=10.0,
            baseline_std_dev=1.0,
            z_score=0.0,
            severity="low",
        )
        assert "Anomaly: token_usage:tokens" in custom._generate_message()


# ===========================================================================
# UsageAnomalyDetector Tests
# ===========================================================================


class TestUsageAnomalyDetector:
    """Test UsageAnomalyDetector class."""

    @pytest.fixture
    def detector(self, tmp_path: Path) -> UsageAnomalyDetector:
        """Create detector with temp baseline file."""
        baseline_file = tmp_path / "test_baseline.json"
        return UsageAnomalyDetector(baseline_file=str(baseline_file))

    def test_load_baselines_file_not_found(self, tmp_path: Path) -> None:
        """Test initializing detector when file does not exist."""
        non_existent = tmp_path / "missing.json"
        d = UsageAnomalyDetector(baseline_file=str(non_existent))
        assert d.get_all_baselines() == {}

    def test_load_baselines_invalid_json(self, tmp_path: Path) -> None:
        """Test handling malformed JSON on load."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("invalid-json{", encoding="utf-8")
        d = UsageAnomalyDetector(baseline_file=str(bad_file))
        assert d.get_all_baselines() == {}

    def test_load_baselines_key_error(self, tmp_path: Path) -> None:
        """Test handling JSON with bad format causing KeyError/TypeError."""
        bad_file = tmp_path / "keyerr.json"
        # baselines is a list instead of dict, calling .items() triggers AttributeError/KeyError
        with patch.object(BaselineStats, "from_dict", side_effect=KeyError("corrupted")):
            bad_file.write_text('{"baselines": {"metric1": {}}}', encoding="utf-8")
            d = UsageAnomalyDetector(baseline_file=str(bad_file))
            assert d.get_all_baselines() == {}

    def test_record_metric_and_rolling_window_trimming(self, detector: UsageAnomalyDetector) -> None:
        """Test recording metrics and trimming when exceeding MAX_SAMPLES (168)."""
        # Record 175 samples
        for i in range(175):
            detector.record_metric(AnomalyCategory.API_CALLS, "requests", float(i))

        baseline = detector.get_baseline(AnomalyCategory.API_CALLS, "requests")
        assert baseline is not None
        assert baseline.sample_count == 168
        assert len(baseline.samples) == 168
        # The earliest samples should have been trimmed off
        assert baseline.samples[0] == 7.0
        assert baseline.samples[-1] == 174.0

    def test_record_metric_with_string_category(self, detector: UsageAnomalyDetector) -> None:
        """Test recording metric using a string category."""
        detector.record_metric("custom_category", "ops", 42.0)
        baseline = detector.get_baseline("custom_category", "ops")
        assert baseline is not None
        assert baseline.metric == "custom_category:ops"
        assert baseline.sample_count == 1
        assert baseline.samples == [42.0]

    def test_recalculate_stats_edge_cases(self, detector: UsageAnomalyDetector) -> None:
        """Test _recalculate_stats on empty list, 1 element, and normal list."""
        b_empty = BaselineStats(metric="test:empty", samples=[])
        detector._recalculate_stats(b_empty)
        assert b_empty.mean == 0.0
        assert b_empty.std_dev == 0.0

        b_single = BaselineStats(metric="test:single", samples=[42.0])
        detector._recalculate_stats(b_single)
        assert b_single.mean == 42.0
        assert b_single.std_dev == 0.0

        b_multi = BaselineStats(metric="test:multi", samples=[10.0, 20.0, 30.0])
        detector._recalculate_stats(b_multi)
        assert b_multi.mean == 20.0
        assert b_multi.std_dev == 10.0

    def test_no_anomaly_when_metric_untracked(self, detector: UsageAnomalyDetector) -> None:
        """Test detect_anomaly returns None when metric has not been recorded."""
        assert detector.detect_anomaly("api_calls", "non_existent", 100.0) is None

    def test_no_anomaly_with_few_samples(self, detector: UsageAnomalyDetector) -> None:
        """Test no anomaly detected with insufficient samples (< MIN_SAMPLES=3)."""
        detector.record_metric(AnomalyCategory.API_CALLS, "requests", 10.0)
        detector.record_metric(AnomalyCategory.API_CALLS, "requests", 12.0)

        anomaly = detector.detect_anomaly(AnomalyCategory.API_CALLS, "requests", 100.0)
        assert anomaly is None

    def test_no_anomaly_within_threshold(self, detector: UsageAnomalyDetector) -> None:
        """Test no anomaly when value is within Z_SCORE_THRESHOLD (3.0)."""
        for value in [10, 15, 12, 18, 11, 14, 10, 16, 13, 17]:
            detector.record_metric(AnomalyCategory.API_CALLS, "requests", float(value))

        anomaly = detector.detect_anomaly(AnomalyCategory.API_CALLS, "requests", 14.0)
        assert anomaly is None

    def test_spike_anomaly_detection(self, detector: UsageAnomalyDetector) -> None:
        """Test detection of spike anomaly (>3σ above mean)."""
        for _ in range(20):
            detector.record_metric(AnomalyCategory.API_CALLS, "requests", 10.0)

        detector.record_metric(AnomalyCategory.API_CALLS, "requests", 100.0)

        anomaly = detector.detect_anomaly(AnomalyCategory.API_CALLS, "requests", 100.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.SPIKE
        assert anomaly.z_score > 3.0
        assert anomaly.severity in ["low", "medium", "high", "critical"]
        assert anomaly.details["sample_count"] == 21
        assert anomaly.details["window_days"] == 7

    def test_drop_anomaly_detection(self, detector: UsageAnomalyDetector) -> None:
        """Test detection of drop anomaly (>3σ below mean)."""
        for _ in range(20):
            detector.record_metric(AnomalyCategory.AGENT_SPAWNS, "spawns", 100.0)

        detector.record_metric(AnomalyCategory.AGENT_SPAWNS, "spawns", 10.0)

        anomaly = detector.detect_anomaly(AnomalyCategory.AGENT_SPAWNS, "spawns", 10.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.DROP
        assert anomaly.z_score < -3.0

    def test_determine_anomaly_type_direct(self, detector: UsageAnomalyDetector) -> None:
        """Test _determine_anomaly_type for spike, drop, and pattern break."""
        assert detector._determine_anomaly_type(3.5) == AnomalyType.SPIKE
        assert detector._determine_anomaly_type(-3.5) == AnomalyType.DROP
        assert detector._determine_anomaly_type(0.0) == AnomalyType.PATTERN_BREAK

    def test_detect_anomaly_with_string_category_and_pattern_break(
        self, detector: UsageAnomalyDetector
    ) -> None:
        """Test detect_anomaly using string category and pattern break with lowered threshold."""
        for _ in range(5):
            detector.record_metric("api_calls", "reqs", 10.0)

        # Temporarily lower Z_SCORE_THRESHOLD to -1 so z_score=0 is detected
        with patch.object(detector, "Z_SCORE_THRESHOLD", -1.0):
            anomaly = detector.detect_anomaly("api_calls", "reqs", 10.0)
            assert anomaly is not None
            assert anomaly.category == AnomalyCategory.API_CALLS
            assert anomaly.anomaly_type == AnomalyType.PATTERN_BREAK

    def test_z_score_calculation(self, detector: UsageAnomalyDetector) -> None:
        """Test Z-score calculation with normal and zero std dev."""
        assert detector._calculate_z_score(15.0, 10.0, 2.5) == 2.0
        assert detector._calculate_z_score(15.0, 10.0, 0.0) == 0.0

    def test_severity_calculation(self, detector: UsageAnomalyDetector) -> None:
        """Test severity level calculation across all bands."""
        assert detector._calculate_severity(5.5) == "critical"
        assert detector._calculate_severity(5.0) == "critical"
        assert detector._calculate_severity(4.5) == "high"
        assert detector._calculate_severity(4.0) == "high"
        assert detector._calculate_severity(3.7) == "medium"
        assert detector._calculate_severity(3.5) == "medium"
        assert detector._calculate_severity(3.2) == "low"
        assert detector._calculate_severity(1.0) == "low"

    def test_baseline_persistence(self, detector: UsageAnomalyDetector, tmp_path: Path) -> None:
        """Test baseline persistence and reloading."""
        detector.record_metric("api_calls", "requests", 50.0)
        detector._save_baselines()

        baseline_file = tmp_path / "test_baseline.json"
        new_detector = UsageAnomalyDetector(baseline_file=str(baseline_file))

        baseline = new_detector.get_baseline("api_calls", "requests")
        assert baseline is not None
        assert baseline.sample_count == 1
        assert baseline.samples == [50.0]

    def test_reset_baseline(self, detector: UsageAnomalyDetector) -> None:
        """Test resetting single baseline."""
        detector.record_metric(AnomalyCategory.API_CALLS, "requests", 10.0)
        assert detector.get_baseline(AnomalyCategory.API_CALLS, "requests") is not None

        detector.reset_baseline(AnomalyCategory.API_CALLS, "requests")
        assert detector.get_baseline(AnomalyCategory.API_CALLS, "requests") is None

        # Resetting non-existent key should not raise
        detector.reset_baseline("non", "existent")

    def test_reset_all_baselines_with_and_without_file(
        self, detector: UsageAnomalyDetector, tmp_path: Path
    ) -> None:
        """Test reset_all_baselines unlinks file when present and clears memory."""
        detector.record_metric(AnomalyCategory.API_CALLS, "requests", 10.0)
        detector._save_baselines()
        baseline_file = tmp_path / "test_baseline.json"
        assert baseline_file.exists()

        detector.reset_all_baselines()
        assert not baseline_file.exists()
        assert detector.get_all_baselines() == {}

        # Running again when file is already unlinked
        detector.reset_all_baselines()
        assert detector.get_all_baselines() == {}


# ===========================================================================
# UsageMetering Tests
# ===========================================================================


class TestUsageMetering:
    """Test UsageMetering integration class."""

    @pytest.fixture
    def metering(self, tmp_path: Path) -> UsageMetering:
        """Create metering with temp baseline file."""
        baseline_file = tmp_path / "test_metering_baseline.json"
        return UsageMetering(baseline_file=str(baseline_file))

    def test_record_api_call(self, metering: UsageMetering) -> None:
        """Test recording API calls."""
        metering.record_api_call("chat/completions", "POST", 200)
        summary = metering.get_usage_summary()
        assert summary["api_calls"] == 1

    def test_record_agent_spawn(self, metering: UsageMetering) -> None:
        """Test recording agent spawns."""
        metering.record_agent_spawn("planner", "qwen3.5-plus", 2.5)
        summary = metering.get_usage_summary()
        assert summary["agent_spawns"] == 1

    def test_record_model_usage(self, metering: UsageMetering) -> None:
        """Test recording model usage."""
        metering.record_model_usage("qwen3.5-plus", 1000, 500, 0.002)
        detector = metering.get_detector()
        baseline = detector.get_baseline("model_usage", "qwen3.5-plus")
        assert baseline is not None

    def test_record_llm_call(self, metering: UsageMetering) -> None:
        """Test recording LLM calls."""
        metering.record_llm_call("qwen3.5-plus", 1000, 500, 1.5)
        summary = metering.get_usage_summary()
        assert summary["llm_calls"] == 1

    def test_record_token_usage(self, metering: UsageMetering) -> None:
        """Test recording token usage."""
        metering.record_token_usage("qwen3.5-plus", 1000, 500)
        detector = metering.get_detector()
        baseline = detector.get_baseline("token_usage", "qwen3.5-plus")
        assert baseline is not None

    def test_event_subscription(self, metering: UsageMetering) -> None:
        """Test subscribing to usage events."""
        received_events: list[UsageEvent] = []

        def handler(event: UsageEvent) -> None:
            received_events.append(event)

        metering.subscribe(UsageEventType.API_CALL, handler)
        metering.record_api_call("test", "GET", 200)

        assert len(received_events) == 1
        assert received_events[0].event_type == UsageEventType.API_CALL

    def test_reset_counters(self, metering: UsageMetering) -> None:
        """Test resetting counters."""
        metering.record_api_call("test", "POST", 200)
        metering.record_agent_spawn("test", "model", 1.0)
        metering.record_llm_call("model", 100, 50, 0.5)

        metering.reset_counters()

        summary = metering.get_usage_summary()
        assert summary["api_calls"] == 0
        assert summary["agent_spawns"] == 0
        assert summary["llm_calls"] == 0


# ===========================================================================
# Singletons Tests
# ===========================================================================


class TestSingletons:
    """Test singleton getters and resetters."""

    def teardown_method(self) -> None:
        """Reset singletons after each test."""
        reset_detector()
        reset_metering()

    def test_get_detector_singleton(self) -> None:
        """Test detector singleton creation and retrieval."""
        reset_detector()
        d1 = get_detector()
        d2 = get_detector()
        assert d1 is d2
        reset_detector()

    def test_get_metering_singleton(self) -> None:
        """Test metering singleton creation and retrieval."""
        reset_metering()
        m1 = get_metering()
        m2 = get_metering()
        assert m1 is m2
        reset_metering()
