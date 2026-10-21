# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Improvement Engine — Generate improvement tasks from failure analysis.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .improvement_engine_models import (
    ImprovementRecommendation,
    ImprovementTask,
    build_failure_improvement_task,
    build_tech_debt_task,
    load_improvements_from_file,
)
from .learning_journal import LearningJournal
from .pattern_library import PatternLibrary

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
MEKONG_DIR = MEKONG_ROOT / ".mekong"
JOURNAL_DIR = MEKONG_DIR / "journal"
IMPROVEMENTS_FILE = JOURNAL_DIR / "improvements.json"

JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


class ImprovementEngine:
    """Analyzes failures and generates improvement tasks."""

    def __init__(
        self,
        journal: LearningJournal | None = None,
        pattern_library: PatternLibrary | None = None,
    ) -> None:
        self.journal = journal or LearningJournal()
        self.pattern_library = pattern_library or PatternLibrary()
        self._improvements: list[ImprovementTask] = []
        self._recommendations: list[ImprovementRecommendation] = []
        self._load()

    def _load(self) -> None:
        """Load improvements from disk."""
        self._improvements = load_improvements_from_file(IMPROVEMENTS_FILE)

    def _save(self) -> None:
        """Save improvements to disk."""
        data = {
            "improvements": [imp.to_dict() for imp in self._improvements],
            "last_updated": datetime.now().isoformat(),
        }
        IMPROVEMENTS_FILE.write_text(json.dumps(data, indent=2))

    def analyze_and_generate_tasks(
        self, lookback_days: int = 7, min_failures: int = 3
    ) -> list[ImprovementTask]:
        """Analyze recent failures and generate improvement tasks."""
        tasks = []
        failure_stats = self._analyze_failure_patterns(lookback_days)

        for category, stats in failure_stats.items():
            if stats["count"] >= min_failures:
                task = self._create_improvement_task(
                    category=category,
                    failure_count=stats["count"],
                    common_errors=stats["common_errors"],
                )
                tasks.append(task)
                self._improvements.append(task)

        tech_debt_task = self._analyze_tech_debt()
        if tech_debt_task:
            tasks.append(tech_debt_task)
            self._improvements.append(tech_debt_task)

        self._save()
        logger.info(f"[ImprovementEngine] Generated {len(tasks)} improvement tasks")
        return tasks

    def _analyze_failure_patterns(self, lookback_days: int) -> dict[str, Any]:
        """Analyze failure patterns from the journal."""
        cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()
        failed = [
            m
            for m in self.journal.get_missions(limit=1000)
            if m["status"] == "failed" and m.get("created_at", "") > cutoff
        ]

        stats: dict[str, dict] = {}
        for mission in failed:
            capability = mission.get("capability", "general")
            entry = stats.setdefault(capability, {"count": 0, "common_errors": []})
            entry["count"] += 1
            error = mission.get("error", "")
            if error and error not in entry["common_errors"]:
                entry["common_errors"].append(error[:100])
        return stats

    def _create_improvement_task(
        self, category: str, failure_count: int, common_errors: list[str]
    ) -> ImprovementTask:
        """Create an improvement task for a failure category."""
        return build_failure_improvement_task(category, failure_count, common_errors)

    def _analyze_tech_debt(self) -> ImprovementTask | None:
        """Analyze tech debt and create improvement task if needed."""
        return build_tech_debt_task(self.journal.get_missions(limit=500))

    def get_recommendations(self) -> list[ImprovementRecommendation]:
        """Get improvement recommendations based on analysis."""
        recommendations = []
        summary = self.journal.get_summary()

        if summary["success_rate"] < 80:
            recommendations.append(ImprovementRecommendation(
                category="reliability", description="Improve mission success rate",
                impact="high", effort="medium", details={"current_success_rate": summary["success_rate"]},
            ))
        if summary["avg_duration_ms"] > 300000:
            recommendations.append(ImprovementRecommendation(
                category="performance", description="Reduce mission execution time",
                impact="medium", effort="high", details={"avg_duration_ms": summary["avg_duration_ms"]},
            ))
        self._recommendations = recommendations
        return recommendations

    def get_improvements(self, status: str | None = None) -> list[dict]:
        """Get improvement tasks, optionally filtered by status."""
        improvements = [i for i in self._improvements if i.status == status] if status else self._improvements
        return [imp.to_dict() for imp in improvements]

    def mark_completed(self, improvement_id: str) -> bool:
        """Mark an improvement task as completed."""
        for imp in self._improvements:
            if imp.id == improvement_id:
                imp.status = "completed"
                self._save()
                logger.info(f"[ImprovementEngine] Marked {improvement_id} as completed")
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get improvement engine statistics."""
        return {
            "total_improvements": len(self._improvements),
            "pending": sum(1 for imp in self._improvements if imp.status == "pending"),
            "completed": sum(1 for imp in self._improvements if imp.status == "completed"),
            "by_priority": self._count_by_priority(),
            "by_category": self._count_by_category(),
        }

    def _count_by_priority(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for imp in self._improvements:
            counts[imp.priority] = counts.get(imp.priority, 0) + 1
        return counts

    def _count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for imp in self._improvements:
            counts[imp.category] = counts.get(imp.category, 0) + 1
        return counts
