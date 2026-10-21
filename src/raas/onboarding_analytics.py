# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Onboarding analytics engine for RaaS."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.raas.onboarding_analytics_cohorts import OnboardingAnalyticsCohortsMixin
from src.raas.onboarding_analytics_models import (
    _DB_PATH,
    CohortData,
    ConversionRate,
    DropOffPoint,
    TimeToComplete,
)
from src.raas.onboarding_funnel_store import OnboardingFunnelStore

logger = logging.getLogger(__name__)


class OnboardingAnalytics(OnboardingAnalyticsCohortsMixin):
    """Analytics engine for onboarding funnel analysis."""

    def __init__(self, store: Optional[OnboardingFunnelStore] = None) -> None:
        self._store = store or OnboardingFunnelStore(db_path=_DB_PATH)
        self._funnel_steps = OnboardingFunnelStore.FUNNEL_STEPS

    def get_conversion_rates(self, days: int = 30) -> List[ConversionRate]:
        """Calculate step-to-step conversion rates."""
        funnel_data = self._store.get_funnel_data(days=days)
        steps = funnel_data.steps
        if len(steps) < 2:
            return []

        rates: List[ConversionRate] = []
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            from_count = current_step.count
            to_count = next_step.count
            conversion_rate = (to_count / from_count * 100) if from_count > 0 else 0.0
            drop_off_count = from_count - to_count
            drop_off_rate = (drop_off_count / from_count * 100) if from_count > 0 else 0.0

            rates.append(
                ConversionRate(
                    from_step=current_step.step_name,
                    to_step=next_step.step_name,
                    from_count=from_count,
                    to_count=to_count,
                    conversion_rate=round(conversion_rate, 2),
                    drop_off_count=drop_off_count,
                    drop_off_rate=round(drop_off_rate, 2),
                )
            )

        logger.info(f"Calculated {len(rates)} conversion rates for last {days} days")
        return rates

    def get_drop_off_points(self, days: int = 30) -> List[DropOffPoint]:
        """Identify biggest drop-off points in the funnel."""
        funnel_data = self._store.get_funnel_data(days=days)
        steps = funnel_data.steps
        if len(steps) < 2:
            return []

        drop_offs: List[DropOffPoint] = []
        initial_count = steps[0].count if steps else 0

        for i, step in enumerate(steps):
            users_dropped = (step.count - steps[i + 1].count) if i < len(steps) - 1 else 0
            drop_off_rate = (users_dropped / initial_count * 100) if initial_count > 0 else 0.0
            severity = self._classify_drop_off_severity(drop_off_rate)

            if users_dropped > 0:
                drop_offs.append(
                    DropOffPoint(
                        step_name=step.step_name,
                        step_order=step.step_order,
                        users_reached=step.count,
                        users_dropped=users_dropped,
                        drop_off_rate=round(drop_off_rate, 2),
                        drop_off_severity=severity,
                    )
                )

        drop_offs.sort(key=lambda x: x.drop_off_rate, reverse=True)
        logger.info(f"Identified {len(drop_offs)} drop-off points for last {days} days")
        return drop_offs

    def _classify_drop_off_severity(self, drop_off_rate: float) -> str:
        """Classify drop-off severity based on rate."""
        if drop_off_rate >= 50:
            return "critical"
        if drop_off_rate >= 30:
            return "high"
        if drop_off_rate >= 15:
            return "medium"
        return "low"

    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get a comprehensive analytics summary."""
        conversion_rates = self.get_conversion_rates(days=days)
        drop_offs = self.get_drop_off_points(days=days)
        time_metrics = self.get_avg_time_to_complete(days=days)
        biggest_drop_off = drop_offs[0] if drop_offs else None

        return {
            "period_days": days,
            "conversion_rates": [
                {
                    "from": cr.from_step,
                    "to": cr.to_step,
                    "rate": cr.conversion_rate,
                    "drop_off_rate": cr.drop_off_rate,
                }
                for cr in conversion_rates
            ],
            "biggest_drop_off": (
                {
                    "step": biggest_drop_off.step_name,
                    "rate": biggest_drop_off.drop_off_rate,
                    "severity": biggest_drop_off.drop_off_severity,
                }
                if biggest_drop_off
                else None
            ),
            "critical_drop_offs": [
                {"step": d.step_name, "rate": d.drop_off_rate}
                for d in drop_offs
                if d.drop_off_severity in ("critical", "high")
            ],
            "avg_time_to_complete": [
                {
                    "step": t.step_name,
                    "avg_hours": t.avg_hours,
                    "median_hours": t.median_hours,
                }
                for t in time_metrics
            ],
        }


__all__ = [
    "CohortData",
    "ConversionRate",
    "DropOffPoint",
    "OnboardingAnalytics",
    "TimeToComplete",
    "_DB_PATH",
]
