"""
Unit tests for ImprovementEngine — covers uncovered branches from 35% baseline.

Targets:
- _load / _save
- analyze_and_generate_tasks (happy + no-failure paths)
- _analyze_failure_patterns
- _create_improvement_task (priority tiers: CRITICAL, HIGH, MEDIUM, LOW)
- _analyze_tech_debt (triggered + not triggered)
- get_recommendations (low success rate + high duration)
- get_improvements (filtered / unfiltered)
- mark_completed (found + not found)
- get_stats / _count_by_priority / _count_by_category
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.daemon.improvement_engine import (
    ImprovementEngine,
    ImprovementTask,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(
    id: str = "task-001",
    title: str = "Fix stuff",
    priority: str = "HIGH",
    category: str = "reliability",
    status: str = "pending",
) -> ImprovementTask:
    return ImprovementTask(
        id=id,
        title=title,
        description="desc",
        priority=priority,
        category=category,
        source_analysis="test",
        status=status,
    )


def _mock_journal(missions=None, summary=None):
    journal = MagicMock()
    journal.get_missions.return_value = missions or []
    journal.get_summary.return_value = summary or {
        "success_rate": 95.0,
        "avg_duration_ms": 1000,
    }
    return journal


def _mock_pattern_library():
    return MagicMock()


# ---------------------------------------------------------------------------
# ImprovementTask.to_dict
# ---------------------------------------------------------------------------

class TestImprovementTask:
    def test_to_dict_roundtrip(self):
        task = _make_task()
        d = task.to_dict()
        assert d["id"] == "task-001"
        assert d["title"] == "Fix stuff"
        assert d["priority"] == "HIGH"
        assert d["category"] == "reliability"
        assert d["status"] == "pending"
        assert "created_at" in d
        assert "metadata" in d


# ---------------------------------------------------------------------------
# ImprovementEngine._load
# ---------------------------------------------------------------------------

class TestImprovementEngineLoad:
    def test_load_no_file(self, tmp_path):
        """No improvements file → empty list."""
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", tmp_path / "improvements.json"):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
        assert engine._improvements == []

    def test_load_valid_file(self, tmp_path):
        """Valid JSON → loads improvements into list."""
        imp_file = tmp_path / "improvements.json"
        task_dict = _make_task().to_dict()
        imp_file.write_text(json.dumps({"improvements": [task_dict]}))

        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
        assert len(engine._improvements) == 1
        assert engine._improvements[0].id == "task-001"

    def test_load_invalid_json(self, tmp_path):
        """Corrupt JSON → warning logged, empty list."""
        imp_file = tmp_path / "improvements.json"
        imp_file.write_text("NOT_JSON{{{")

        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
        assert engine._improvements == []

    def test_load_missing_key(self, tmp_path):
        """Missing required key → KeyError caught, empty list."""
        imp_file = tmp_path / "improvements.json"
        # Missing "id" key
        imp_file.write_text(json.dumps({"improvements": [{"title": "X"}]}))

        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
        assert engine._improvements == []


# ---------------------------------------------------------------------------
# ImprovementEngine._save
# ---------------------------------------------------------------------------

class TestImprovementEngineSave:
    def test_save_writes_json(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
            engine._improvements.append(_make_task())
            engine._save()

        data = json.loads(imp_file.read_text())
        assert "improvements" in data
        assert len(data["improvements"]) == 1
        assert "last_updated" in data


# ---------------------------------------------------------------------------
# _create_improvement_task — priority tiers
# ---------------------------------------------------------------------------

class TestCreateImprovementTask:
    def _engine(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            return ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )

    def test_priority_critical(self, tmp_path):
        engine = self._engine(tmp_path)
        task = engine._create_improvement_task("api", 10, ["err1"])
        assert task.priority == "CRITICAL"

    def test_priority_high(self, tmp_path):
        engine = self._engine(tmp_path)
        task = engine._create_improvement_task("api", 5, ["err1"])
        assert task.priority == "HIGH"

    def test_priority_medium(self, tmp_path):
        engine = self._engine(tmp_path)
        task = engine._create_improvement_task("api", 3, ["err1"])
        assert task.priority == "MEDIUM"

    def test_priority_low(self, tmp_path):
        """failure_count < 3 → LOW (edge: 2)."""
        engine = self._engine(tmp_path)
        task = engine._create_improvement_task("api", 2, [])
        assert task.priority == "LOW"

    def test_task_fields(self, tmp_path):
        engine = self._engine(tmp_path)
        errors = ["err A", "err B"]
        task = engine._create_improvement_task("auth", 5, errors)
        assert "auth" in task.title
        assert task.category == "reliability"
        assert task.metadata["failure_count"] == 5
        assert task.metadata["common_errors"] == errors

    def test_description_truncates_to_5_errors(self, tmp_path):
        engine = self._engine(tmp_path)
        errors = [f"error {i}" for i in range(10)]
        task = engine._create_improvement_task("svc", 6, errors)
        # At most 5 errors in description bullets
        bullet_lines = [line for line in task.description.splitlines() if line.startswith("- ")]
        assert len(bullet_lines) <= 5


# ---------------------------------------------------------------------------
# _analyze_tech_debt
# ---------------------------------------------------------------------------

class TestAnalyzeTechDebt:
    def test_no_tech_debt(self, tmp_path):
        missions = [{"description": "normal task"} for _ in range(10)]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
        result = engine._analyze_tech_debt()
        assert result is None

    def test_tech_debt_triggered(self, tmp_path):
        missions = [{"description": "TODO: fix this hack workaround"} for _ in range(6)]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
        result = engine._analyze_tech_debt()
        assert result is not None
        assert result.category == "tech_debt"
        assert result.priority == "MEDIUM"

    def test_tech_debt_exact_threshold(self, tmp_path):
        """Exactly 5 missions with 'hack' keyword → triggered (>= 5 check in source).
        Note: indicators 'hack'/'temporary'/'workaround' are lowercase so they match
        .lower() desc; 'TODO'/'FIXME' are uppercase and do NOT match (source quirk).
        """
        missions = [{"description": "this is a hack"} for _ in range(5)]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
            result = engine._analyze_tech_debt()
        assert result is not None


# ---------------------------------------------------------------------------
# analyze_and_generate_tasks
# ---------------------------------------------------------------------------

class TestAnalyzeAndGenerateTasks:
    def _engine_with_failed_missions(self, tmp_path, num_failures=5, capability="api"):
        now_iso = datetime.now().isoformat()
        missions = [
            {
                "status": "failed",
                "capability": capability,
                "created_at": now_iso,
                "error": f"error {i}",
            }
            for i in range(num_failures)
        ]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            return ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library()), imp_file

    def test_generates_tasks_for_repeated_failures(self, tmp_path):
        engine, _ = self._engine_with_failed_missions(tmp_path, num_failures=5)
        tasks = engine.analyze_and_generate_tasks(min_failures=3)
        assert len(tasks) >= 1
        assert any(t.category == "reliability" for t in tasks)

    def test_no_tasks_when_below_threshold(self, tmp_path):
        engine, _ = self._engine_with_failed_missions(tmp_path, num_failures=2)
        tasks = engine.analyze_and_generate_tasks(min_failures=3)
        # Only tech debt task possible; no reliability task
        for t in tasks:
            assert t.category != "reliability" or t.category == "tech_debt"

    def test_saves_to_disk(self, tmp_path):
        now_iso = datetime.now().isoformat()
        missions = [
            {"status": "failed", "capability": "api", "created_at": now_iso, "error": "err"}
            for _ in range(5)
        ]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        # Keep patch active through the method call so _save writes to tmp path
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
            engine.analyze_and_generate_tasks(min_failures=3)
        assert imp_file.exists()

    def test_deduplication_of_errors(self, tmp_path):
        """Same error repeated → only one entry in common_errors."""
        now_iso = datetime.now().isoformat()
        missions = [
            {"status": "failed", "capability": "net", "created_at": now_iso, "error": "timeout"}
            for _ in range(5)
        ]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
        tasks = engine.analyze_and_generate_tasks(min_failures=3)
        assert len(tasks) >= 1
        net_task = next((t for t in tasks if "net" in t.title), None)
        assert net_task is not None
        assert net_task.metadata["common_errors"].count("timeout") == 1

    def test_old_failures_excluded_by_cutoff(self, tmp_path):
        """Failures older than lookback_days should be ignored."""
        old_iso = "2020-01-01T00:00:00"
        missions = [
            {"status": "failed", "capability": "api", "created_at": old_iso, "error": "err"}
            for _ in range(10)
        ]
        journal = _mock_journal(missions=missions)
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())
        tasks = engine.analyze_and_generate_tasks(min_failures=3, lookback_days=7)
        reliability_tasks = [t for t in tasks if t.category == "reliability"]
        assert len(reliability_tasks) == 0


# ---------------------------------------------------------------------------
# get_recommendations
# ---------------------------------------------------------------------------

class TestGetRecommendations:
    def _engine(self, tmp_path, success_rate, avg_duration_ms):
        journal = _mock_journal(summary={
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration_ms,
        })
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            return ImprovementEngine(journal=journal, pattern_library=_mock_pattern_library())

    def test_low_success_rate_recommends_reliability(self, tmp_path):
        engine = self._engine(tmp_path, success_rate=70.0, avg_duration_ms=1000)
        recs = engine.get_recommendations()
        categories = [r.category for r in recs]
        assert "reliability" in categories

    def test_high_success_rate_no_reliability_rec(self, tmp_path):
        engine = self._engine(tmp_path, success_rate=95.0, avg_duration_ms=1000)
        recs = engine.get_recommendations()
        categories = [r.category for r in recs]
        assert "reliability" not in categories

    def test_high_duration_recommends_performance(self, tmp_path):
        engine = self._engine(tmp_path, success_rate=95.0, avg_duration_ms=400000)
        recs = engine.get_recommendations()
        categories = [r.category for r in recs]
        assert "performance" in categories

    def test_low_duration_no_performance_rec(self, tmp_path):
        engine = self._engine(tmp_path, success_rate=95.0, avg_duration_ms=5000)
        recs = engine.get_recommendations()
        categories = [r.category for r in recs]
        assert "performance" not in categories

    def test_both_issues_returns_two_recs(self, tmp_path):
        engine = self._engine(tmp_path, success_rate=50.0, avg_duration_ms=600000)
        recs = engine.get_recommendations()
        assert len(recs) == 2

    def test_exact_success_threshold(self, tmp_path):
        """Exactly 80 → no reliability rec (not < 80)."""
        engine = self._engine(tmp_path, success_rate=80.0, avg_duration_ms=1000)
        recs = engine.get_recommendations()
        assert "reliability" not in [r.category for r in recs]

    def test_exact_duration_threshold(self, tmp_path):
        """Exactly 300000ms → no performance rec (not > 300000)."""
        engine = self._engine(tmp_path, success_rate=95.0, avg_duration_ms=300000)
        recs = engine.get_recommendations()
        assert "performance" not in [r.category for r in recs]


# ---------------------------------------------------------------------------
# get_improvements / mark_completed
# ---------------------------------------------------------------------------

class TestGetImprovementsAndMarkCompleted:
    def _engine(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(
                journal=_mock_journal(),
                pattern_library=_mock_pattern_library(),
            )
        engine._improvements = [
            _make_task("t1", status="pending"),
            _make_task("t2", status="completed"),
            _make_task("t3", status="pending"),
        ]
        return engine

    def test_get_improvements_no_filter(self, tmp_path):
        engine = self._engine(tmp_path)
        result = engine.get_improvements()
        assert len(result) == 3

    def test_get_improvements_pending_filter(self, tmp_path):
        engine = self._engine(tmp_path)
        result = engine.get_improvements(status="pending")
        assert len(result) == 2

    def test_get_improvements_completed_filter(self, tmp_path):
        engine = self._engine(tmp_path)
        result = engine.get_improvements(status="completed")
        assert len(result) == 1

    def test_mark_completed_success(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=_mock_journal(), pattern_library=_mock_pattern_library())
        engine._improvements = [_make_task("t1", status="pending")]
        result = engine.mark_completed("t1")
        assert result is True
        assert engine._improvements[0].status == "completed"

    def test_mark_completed_not_found(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=_mock_journal(), pattern_library=_mock_pattern_library())
        engine._improvements = [_make_task("t1")]
        result = engine.mark_completed("nonexistent-id")
        assert result is False


# ---------------------------------------------------------------------------
# get_stats / _count_by_priority / _count_by_category
# ---------------------------------------------------------------------------

class TestGetStats:
    def _engine_with_tasks(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=_mock_journal(), pattern_library=_mock_pattern_library())
        engine._improvements = [
            _make_task("t1", priority="CRITICAL", category="reliability", status="pending"),
            _make_task("t2", priority="HIGH", category="reliability", status="completed"),
            _make_task("t3", priority="MEDIUM", category="tech_debt", status="pending"),
        ]
        return engine

    def test_get_stats_counts(self, tmp_path):
        engine = self._engine_with_tasks(tmp_path)
        stats = engine.get_stats()
        assert stats["total_improvements"] == 3
        assert stats["pending"] == 2
        assert stats["completed"] == 1

    def test_get_stats_by_priority(self, tmp_path):
        engine = self._engine_with_tasks(tmp_path)
        stats = engine.get_stats()
        assert stats["by_priority"]["CRITICAL"] == 1
        assert stats["by_priority"]["HIGH"] == 1
        assert stats["by_priority"]["MEDIUM"] == 1

    def test_get_stats_by_category(self, tmp_path):
        engine = self._engine_with_tasks(tmp_path)
        stats = engine.get_stats()
        assert stats["by_category"]["reliability"] == 2
        assert stats["by_category"]["tech_debt"] == 1

    def test_get_stats_empty(self, tmp_path):
        imp_file = tmp_path / "improvements.json"
        with patch("src.daemon.improvement_engine.IMPROVEMENTS_FILE", imp_file):
            engine = ImprovementEngine(journal=_mock_journal(), pattern_library=_mock_pattern_library())
        stats = engine.get_stats()
        assert stats["total_improvements"] == 0
        assert stats["pending"] == 0
        assert stats["completed"] == 0
        assert stats["by_priority"] == {}
        assert stats["by_category"] == {}
