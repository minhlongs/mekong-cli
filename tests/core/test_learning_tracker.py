"""Tests for src/core/learning_tracker.py"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open


# ---------------------------------------------------------------------------
# Helpers — patch heavy imports before the module loads
# ---------------------------------------------------------------------------

def _make_tracker(tmp_path: Path, memory_mock: MagicMock | None = None):
    """Return a LearningHistoryTracker with all I/O mocked."""
    if memory_mock is None:
        memory_mock = MagicMock()
        memory_mock.connect.return_value = None
        memory_mock.add.return_value = None
        memory_mock.search.return_value = []
        memory_mock.get_all.return_value = []

    with (
        patch(
            "src.core.learning_tracker.get_memory_facade",
            return_value=memory_mock,
        ),
    ):
        from src.core.learning_tracker import LearningHistoryTracker

        tracker = LearningHistoryTracker(agent_id="test:agent")
        # Override storage path to tmp_path so tests don't write to home
        tracker.local_storage_path = tmp_path / "learning_history"
        tracker.local_storage_path.mkdir(parents=True, exist_ok=True)
        tracker.local_history_file = (
            tracker.local_storage_path / "test_agent.json"
        )
        return tracker, memory_mock


# ---------------------------------------------------------------------------
# _save_to_local_storage / _load_from_local_storage
# ---------------------------------------------------------------------------


class TestLocalStorage:
    def test_save_creates_file(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        data = {"type": "learning_event", "event_id": "abc", "topic": "python"}
        tracker._save_to_local_storage(data)
        assert tracker.local_history_file.exists()
        loaded = json.loads(tracker.local_history_file.read_text())
        assert len(loaded) == 1
        assert loaded[0]["topic"] == "python"

    def test_save_appends_and_caps_at_500(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        # Pre-populate 501 records
        initial = [{"n": i} for i in range(501)]
        tracker.local_history_file.write_text(json.dumps(initial))
        tracker._save_to_local_storage({"n": 999})
        loaded = json.loads(tracker.local_history_file.read_text())
        assert len(loaded) == 500
        # The oldest entry (index 1 of original 501) is dropped
        assert loaded[-1]["n"] == 999

    def test_load_returns_empty_when_no_file(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        result = tracker._load_from_local_storage()
        assert result == []

    def test_load_returns_data_when_file_exists(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        records = [{"type": "learning_event", "event_id": "x"}]
        tracker.local_history_file.write_text(json.dumps(records))
        result = tracker._load_from_local_storage()
        assert result == records

    def test_load_returns_empty_on_corrupt_json(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        tracker.local_history_file.write_text("not-json{{")
        result = tracker._load_from_local_storage()
        assert result == []


# ---------------------------------------------------------------------------
# log_learning_event
# ---------------------------------------------------------------------------


class TestLogLearningEvent:
    def test_returns_uuid_string(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        event_id = tracker.log_learning_event(
            topic="python",
            content="learned decorators",
            outcome="success",
            performance_score=0.9,
        )
        # Should be a valid UUID string
        uuid.UUID(event_id)  # raises if not valid

    def test_saves_to_local_storage(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        tracker.log_learning_event(
            topic="rust",
            content="ownership",
            outcome="ok",
            performance_score=0.8,
        )
        records = json.loads(tracker.local_history_file.read_text())
        assert len(records) == 1
        assert records[0]["topic"] == "rust"
        assert records[0]["type"] == "learning_event"

    def test_calls_memory_add(self, tmp_path):
        tracker, mem = _make_tracker(tmp_path)
        tracker.log_learning_event(
            topic="go",
            content="goroutines",
            outcome="ok",
            performance_score=0.7,
        )
        mem.add.assert_called_once()
        call_kwargs = mem.add.call_args[1]
        assert "goroutines" in call_kwargs["content"]

    def test_includes_metadata_when_provided(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        tracker.log_learning_event(
            topic="sql",
            content="indexes",
            outcome="ok",
            performance_score=0.6,
            metadata={"source": "book"},
        )
        records = json.loads(tracker.local_history_file.read_text())
        assert records[0].get("metadata") == {"source": "book"}

    def test_no_metadata_key_when_none(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        tracker.log_learning_event("topic", "content", "ok", 0.5)
        records = json.loads(tracker.local_history_file.read_text())
        assert "metadata" not in records[0]


# ---------------------------------------------------------------------------
# get_learning_events_by_topic
# ---------------------------------------------------------------------------


class TestGetLearningEventsByTopic:
    def _make_event(self, topic, score, event_id=None):
        return {
            "type": "learning_event",
            "event_id": event_id or str(uuid.uuid4()),
            "topic": topic,
            "performance_score": score,
            "timestamp": "2026-01-01T00:00:00",
        }

    def test_returns_events_from_local_storage(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [self._make_event("python", 0.9), self._make_event("python", 0.7)]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_learning_events_by_topic("python")
        assert len(result) == 2

    def test_filters_by_topic_case_insensitive(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            self._make_event("Python", 0.9),
            self._make_event("rust", 0.8),
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_learning_events_by_topic("python")
        assert all("python" in e["topic"].lower() for e in result)
        assert len(result) == 1

    def test_deduplicates_memory_and_local(self, tmp_path):
        shared_id = str(uuid.uuid4())
        event = self._make_event("go", 0.8, event_id=shared_id)

        mem = MagicMock()
        mem.connect.return_value = None
        mem.add.return_value = None
        # Memory returns the same event
        mem.search.return_value = [{"memory": json.dumps(event)}]
        mem.get_all.return_value = []

        tracker, _ = _make_tracker(tmp_path, memory_mock=mem)
        # Local storage also has same event
        tracker.local_history_file.write_text(json.dumps([event]))
        result = tracker.get_learning_events_by_topic("go")
        assert len(result) == 1  # not 2

    def test_respects_limit(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [self._make_event("python", 0.5) for _ in range(20)]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_learning_events_by_topic("python", limit=5)
        assert len(result) <= 5

    def test_sorted_newest_first(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {**self._make_event("ts", 0.9), "timestamp": "2026-01-01T00:00:00"},
            {**self._make_event("ts", 0.8), "timestamp": "2026-01-02T00:00:00"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_learning_events_by_topic("ts")
        assert result[0]["timestamp"] > result[1]["timestamp"]


# ---------------------------------------------------------------------------
# identify_knowledge_gaps
# ---------------------------------------------------------------------------


class TestIdentifyKnowledgeGaps:
    def _write_events(self, tracker, events):
        tracker.local_history_file.write_text(json.dumps(events))

    def test_returns_gaps_below_threshold(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "hard-topic",
             "performance_score": 0.2, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "2", "topic": "hard-topic",
             "performance_score": 0.3, "timestamp": "2026-01-02"},
        ]
        self._write_events(tracker, events)
        gaps = tracker.identify_knowledge_gaps(min_performance_threshold=0.6)
        topics = [g["topic"] for g in gaps]
        assert "hard-topic" in topics

    def test_no_gap_for_high_performers(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "easy",
             "performance_score": 0.9, "timestamp": "2026-01-01"},
        ]
        self._write_events(tracker, events)
        gaps = tracker.identify_knowledge_gaps()
        assert not any(g["topic"] == "easy" for g in gaps)

    def test_gap_severity_high(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": str(i), "topic": "terrible",
             "performance_score": 0.1, "timestamp": f"2026-01-0{i+1}"}
            for i in range(5)
        ]
        self._write_events(tracker, events)
        gaps = tracker.identify_knowledge_gaps()
        gap = next(g for g in gaps if g["topic"] == "terrible")
        assert gap["gap_severity"] == "HIGH"

    def test_gap_severity_medium(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": str(i), "topic": "medium-topic",
             "performance_score": 0.4, "timestamp": f"2026-01-0{i+1}"}
            for i in range(5)
        ]
        self._write_events(tracker, events)
        gaps = tracker.identify_knowledge_gaps()
        gap = next(g for g in gaps if g["topic"] == "medium-topic")
        assert gap["gap_severity"] == "MEDIUM"

    def test_sorted_worst_first(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "a", "topic": "bad",
             "performance_score": 0.1, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "b", "topic": "mediocre",
             "performance_score": 0.4, "timestamp": "2026-01-01"},
        ]
        self._write_events(tracker, events)
        gaps = tracker.identify_knowledge_gaps()
        assert gaps[0]["average_performance"] <= gaps[-1]["average_performance"]


# ---------------------------------------------------------------------------
# get_learning_progression
# ---------------------------------------------------------------------------


class TestGetLearningProgression:
    def test_sorted_oldest_first(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "python",
             "performance_score": 0.5, "timestamp": "2026-01-03"},
            {"type": "learning_event", "event_id": "2", "topic": "python",
             "performance_score": 0.7, "timestamp": "2026-01-01"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_learning_progression("python")
        assert result[0]["timestamp"] <= result[-1]["timestamp"]


# ---------------------------------------------------------------------------
# get_improvement_patterns
# ---------------------------------------------------------------------------


class TestGetImprovementPatterns:
    def test_requires_at_least_two_events_per_topic(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "lonely",
             "performance_score": 0.5, "timestamp": "2026-01-01"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        patterns = tracker.get_improvement_patterns()
        assert not any(p["topic"] == "lonely" for p in patterns)

    def test_detects_consistent_improvement(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "improving",
             "performance_score": 0.2, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "2", "topic": "improving",
             "performance_score": 0.55, "timestamp": "2026-01-02"},
            {"type": "learning_event", "event_id": "3", "topic": "improving",
             "performance_score": 0.9, "timestamp": "2026-01-03"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        patterns = tracker.get_improvement_patterns()
        p = next(x for x in patterns if x["topic"] == "improving")
        assert p["trend"] == "CONSISTENT_IMPROVEMENT"
        assert p["significant_improvement"] is True

    def test_detects_regression(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "declining",
             "performance_score": 0.9, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "2", "topic": "declining",
             "performance_score": 0.5, "timestamp": "2026-01-02"},
            {"type": "learning_event", "event_id": "3", "topic": "declining",
             "performance_score": 0.2, "timestamp": "2026-01-03"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        patterns = tracker.get_improvement_patterns()
        p = next(x for x in patterns if x["topic"] == "declining")
        assert p["trend"] == "REGRESSION"

    def test_sorted_most_improved_first(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "winner",
             "performance_score": 0.1, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "2", "topic": "winner",
             "performance_score": 0.95, "timestamp": "2026-01-02"},
            {"type": "learning_event", "event_id": "3", "topic": "loser",
             "performance_score": 0.9, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "4", "topic": "loser",
             "performance_score": 0.5, "timestamp": "2026-01-02"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        patterns = tracker.get_improvement_patterns()
        assert patterns[0]["improvement"] >= patterns[-1]["improvement"]


# ---------------------------------------------------------------------------
# get_performance_trends
# ---------------------------------------------------------------------------


class TestGetPerformanceTrends:
    def test_empty_returns_insufficient_data(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        result = tracker.get_performance_trends()
        assert result["total_learning_events"] == 0
        assert result["trend_direction"] == "INSUFFICIENT_DATA"

    def test_computes_average_performance(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": "1", "topic": "x",
             "performance_score": 0.6, "timestamp": "2026-01-01"},
            {"type": "learning_event", "event_id": "2", "topic": "x",
             "performance_score": 0.8, "timestamp": "2026-01-02"},
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_performance_trends()
        assert abs(result["average_performance"] - 0.7) < 1e-9

    def test_trend_improving(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        # First half low, second half high
        events = []
        for i in range(4):
            events.append({
                "type": "learning_event", "event_id": str(i), "topic": "t",
                "performance_score": 0.1, "timestamp": f"2026-01-0{i+1}",
            })
        for i in range(4, 8):
            events.append({
                "type": "learning_event", "event_id": str(i), "topic": "t",
                "performance_score": 0.9, "timestamp": f"2026-01-{i+10}",
            })
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_performance_trends()
        assert result["trend_direction"] == "IMPROVING"

    def test_trend_declining(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = []
        for i in range(4):
            events.append({
                "type": "learning_event", "event_id": str(i), "topic": "t",
                "performance_score": 0.9, "timestamp": f"2026-01-0{i+1}",
            })
        for i in range(4, 8):
            events.append({
                "type": "learning_event", "event_id": str(i), "topic": "t",
                "performance_score": 0.1, "timestamp": f"2026-01-{i+10}",
            })
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_performance_trends()
        assert result["trend_direction"] == "DECLINING"

    def test_performance_chart_capped_at_20(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = [
            {"type": "learning_event", "event_id": str(i), "topic": "t",
             "performance_score": 0.5, "timestamp": f"2026-01-{i+100}"}
            for i in range(30)
        ]
        tracker.local_history_file.write_text(json.dumps(events))
        result = tracker.get_performance_trends()
        assert len(result["performance_chart"]) <= 20


# ---------------------------------------------------------------------------
# _get_most_common_topics
# ---------------------------------------------------------------------------


class TestGetMostCommonTopics:
    def test_returns_top5(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = []
        for topic in ["a", "b", "c", "d", "e", "f"]:
            for _ in range(3):
                events.append({"topic": topic, "type": "learning_event"})
        result = tracker._get_most_common_topics(events)
        assert len(result) <= 5

    def test_sorted_by_count_desc(self, tmp_path):
        tracker, _ = _make_tracker(tmp_path)
        events = (
            [{"topic": "popular", "type": "learning_event"}] * 10
            + [{"topic": "rare", "type": "learning_event"}] * 2
        )
        result = tracker._get_most_common_topics(events)
        assert result[0]["topic"] == "popular"
        assert result[0]["count"] == 10


# ---------------------------------------------------------------------------
# LearningAnalyticsDashboard
# ---------------------------------------------------------------------------


class TestLearningAnalyticsDashboard:
    def _make_dashboard(self, tmp_path, subdir="lh"):
        with patch("src.core.learning_tracker.get_memory_facade") as mock_gm:
            mem = MagicMock()
            mem.connect.return_value = None
            mem.add.return_value = None
            mem.search.return_value = []
            mem.get_all.return_value = []
            mock_gm.return_value = mem

            from src.core.learning_tracker import LearningAnalyticsDashboard

            dashboard = LearningAnalyticsDashboard("test:dash")
            storage = tmp_path / subdir
            storage.mkdir(parents=True, exist_ok=True)
            dashboard.tracker.local_storage_path = storage
            dashboard.tracker.local_history_file = storage / "test_dash.json"
            # Add a couple of events so get_performance_trends includes most_common_topics
            events = [
                {"type": "learning_event", "event_id": "1", "topic": "python",
                 "performance_score": 0.8, "timestamp": "2026-01-01"},
                {"type": "learning_event", "event_id": "2", "topic": "python",
                 "performance_score": 0.9, "timestamp": "2026-01-02"},
            ]
            dashboard.tracker.local_history_file.write_text(__import__("json").dumps(events))
            return dashboard

    def test_generate_learning_report_structure(self, tmp_path):
        dashboard = self._make_dashboard(tmp_path, "lh1")
        report = dashboard.generate_learning_report()
        assert "agent_id" in report
        assert "performance_trends" in report
        assert "knowledge_gaps" in report
        assert "improvement_patterns" in report
        assert "summary" in report

    def test_generate_summary_fields(self, tmp_path):
        dashboard = self._make_dashboard(tmp_path, "lh2")
        summary = dashboard._generate_summary()
        required = [
            "total_events", "overall_performance", "trend_direction",
            "critical_gaps_count", "improved_topics_count", "most_studied_topics",
        ]
        for key in required:
            assert key in summary


# ---------------------------------------------------------------------------
# create_learning_tracker convenience function
# ---------------------------------------------------------------------------


class TestCreateLearningTracker:
    def test_returns_tracker_instance(self):
        with patch("src.core.learning_tracker.get_memory_facade") as mock_gm:
            mem = MagicMock()
            mem.connect.return_value = None
            mock_gm.return_value = mem

            from src.core.learning_tracker import (
                create_learning_tracker,
                LearningHistoryTracker,
            )

            tracker = create_learning_tracker("test:factory")
            assert isinstance(tracker, LearningHistoryTracker)
            assert tracker.agent_id == "test:factory"
