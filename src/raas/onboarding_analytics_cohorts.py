# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Time-to-complete and cohort analysis mixin for OnboardingAnalytics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List

from src.raas.onboarding_analytics_models import CohortData, TimeToComplete

logger = logging.getLogger(__name__)


class OnboardingAnalyticsCohortsMixin:
    """Time-to-complete and cohort analysis methods for OnboardingAnalytics."""

    _store: Any
    _funnel_steps: List[str]

    def get_avg_time_to_complete(self, days: int = 30) -> List[TimeToComplete]:
        """Calculate average time from signup to each step completion."""
        try:
            with self._store._connect() as conn:
                cutoff = (
                    datetime.now(timezone.utc) - timedelta(days=days)
                ).isoformat()
                time_metrics: List[TimeToComplete] = []

                for step_idx, step_name in enumerate(self._funnel_steps):
                    if step_idx == 0:
                        continue

                    rows = conn.execute(
                        """
                        SELECT e1.user_id, e1.created_at as signup_time, e2.created_at as step_time
                        FROM onboarding_events e1
                        JOIN onboarding_events e2 ON e1.user_id = e2.user_id
                        WHERE e1.event_type = 'signup_started' AND e2.event_type = ? AND e1.created_at >= ?
                        ORDER BY e2.created_at
                        """,
                        (step_name, cutoff),
                    ).fetchall()

                    if not rows:
                        continue

                    hours_list: List[float] = []
                    for row in rows:
                        try:
                            s = datetime.fromisoformat(row["signup_time"])
                            e = datetime.fromisoformat(row["step_time"])
                            h = (e - s).total_seconds() / 3600
                            if h >= 0:
                                hours_list.append(h)
                        except (ValueError, TypeError):
                            continue

                    if hours_list:
                        hours_list.sort()
                        n = len(hours_list)
                        time_metrics.append(
                            TimeToComplete(
                                step_name=step_name,
                                avg_hours=round(sum(hours_list) / n, 2),
                                median_hours=round(hours_list[n // 2], 2),
                                min_hours=round(min(hours_list), 2),
                                max_hours=round(max(hours_list), 2),
                                sample_count=n,
                            )
                        )
                return time_metrics
        except Exception as e:
            logger.error(f"Failed to calculate time-to-complete: {e}")
            return []

    def get_cohort_data(
        self, period: str = "daily", days: int = 30
    ) -> List[CohortData]:
        """Perform cohort analysis by period."""
        try:
            with self._store._connect() as conn:
                cutoff = (
                    datetime.now(timezone.utc) - timedelta(days=days)
                ).isoformat()
                rows = conn.execute(
                    "SELECT user_id, created_at FROM onboarding_events WHERE event_type = 'signup_started' AND created_at >= ? ORDER BY created_at",
                    (cutoff,),
                ).fetchall()

                if not rows:
                    return []

                cohorts: Dict[str, List[str]] = {}
                for row in rows:
                    dt = datetime.fromisoformat(row["created_at"])
                    fmt = (
                        "%Y-W%W"
                        if period == "weekly"
                        else ("%Y-%m" if period == "monthly" else "%Y-%m-%d")
                    )
                    k = dt.strftime(fmt)
                    cohorts.setdefault(k, []).append(row["user_id"])

                return [
                    self._build_cohort_data(conn, k, list(set(uids)), period)
                    for k, uids in sorted(cohorts.items())
                ]
        except Exception as e:
            logger.error(f"Failed to build cohort data: {e}")
            return []

    def _build_cohort_data(
        self, conn: Any, period_key: str, user_ids: List[str], period_type: str
    ) -> CohortData:
        """Build cohort data for a specific period."""
        if not user_ids:
            return CohortData(
                period=period_key,
                period_type=period_type,
                users_started=0,
                users_completed=0,
                conversion_rate=0.0,
                avg_time_to_complete_hours=0.0,
            )

        placeholders = ",".join("?" * len(user_ids))
        users_by_step: Dict[str, int] = {}
        for step in self._funnel_steps:
            row = conn.execute(
                f"SELECT COUNT(DISTINCT user_id) as cnt FROM onboarding_events WHERE event_type = ? AND user_id IN ({placeholders})",
                [step] + user_ids,
            ).fetchone()
            users_by_step[step] = row["cnt"] if row else 0

        started = users_by_step.get("signup_started", 0)
        completed = users_by_step.get("first_mission_completed", 0)
        c_rate = (completed / started * 100) if started > 0 else 0.0
        avg_time = self._calculate_cohort_avg_time(conn, user_ids)

        return CohortData(
            period=period_key,
            period_type=period_type,
            users_started=started,
            users_completed=completed,
            conversion_rate=round(c_rate, 2),
            avg_time_to_complete_hours=round(avg_time, 2),
            users_by_step=users_by_step,
        )

    def _calculate_cohort_avg_time(self, conn: Any, user_ids: List[str]) -> float:
        """Calculate average time to complete for a cohort."""
        if not user_ids:
            return 0.0

        placeholders = ",".join("?" * len(user_ids))
        rows = conn.execute(
            f"""
            SELECT e1.created_at as signup_time, e2.created_at as complete_time
            FROM onboarding_events e1
            JOIN onboarding_events e2 ON e1.user_id = e2.user_id
            WHERE e1.event_type = 'signup_started' AND e2.event_type = 'first_mission_completed' AND e1.user_id IN ({placeholders})
            """,
            user_ids,
        ).fetchall()

        hours: List[float] = []
        for row in rows:
            try:
                s = datetime.fromisoformat(row["signup_time"])
                e = datetime.fromisoformat(row["complete_time"])
                d = (e - s).total_seconds() / 3600
                if d >= 0:
                    hours.append(d)
            except (ValueError, TypeError):
                continue
        return (sum(hours) / len(hours)) if hours else 0.0
