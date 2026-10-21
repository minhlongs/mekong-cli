# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dashboard Service — ROIaaS Phase 5."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from cachetools import TTLCache

from src.analytics.dashboard_export import DashboardExportMixin
from src.db.database import DatabaseConnection
from src.db.queries.analytics_queries import AnalyticsQueries
from src.telemetry.rate_limit_metrics import RateLimitMetricsEmitter


@dataclass
class DashboardMetrics:
    """Dashboard metrics container."""
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    weekly_usage: List[Dict[str, Any]] = field(default_factory=list)
    monthly_usage: List[Dict[str, Any]] = field(default_factory=list)
    active_licenses: Dict[str, Any] = field(default_factory=dict)
    top_endpoints: List[Dict[str, Any]] = field(default_factory=list)
    revenue: Dict[str, Any] = field(default_factory=dict)
    tier_distribution: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = ""
    rate_limit_violations: List[Dict[str, Any]] = field(default_factory=list)
    quota_usage_by_tenant: List[Dict[str, Any]] = field(default_factory=list)
    violations_summary: Dict[str, Any] = field(default_factory=dict)
    license_health: Dict[str, Any] = field(default_factory=dict)
    renewal_prompts: List[Dict[str, Any]] = field(default_factory=list)
    rate_limit_events: List[Dict[str, Any]] = field(default_factory=list)


class DashboardService(DashboardExportMixin):
    """Analytics dashboard service."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._cache_ttl: int = 300
        self._queries = AnalyticsQueries(db or DatabaseConnection())
        self._rate_limit_emitter = RateLimitMetricsEmitter(db or DatabaseConnection())
        self._cache: TTLCache = TTLCache(maxsize=100, ttl=self._cache_ttl)

    def _get_cached(self, key: str) -> Optional[DashboardMetrics]:
        return self._cache.get(key)  # type: ignore

    def _set_cache(self, key: str, data: DashboardMetrics) -> None:
        self._cache[key] = data

    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        if pattern:
            for key in list(self._cache.keys()):
                if key.startswith(pattern):
                    del self._cache[key]
        else:
            self._cache.clear()

    async def get_metrics(
        self, range_days: int = 30, license_key: Optional[str] = None,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
    ) -> DashboardMetrics:
        cache_key = f"metrics_{range_days}_{license_key}_{start_date}_{end_date}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if start_date and end_date:
            f_start, f_end = start_date, end_date
        else:
            f_end = datetime.now().strftime('%Y-%m-%d')
            f_start = (datetime.now() - timedelta(days=range_days)).strftime('%Y-%m-%d')

        daily_usage = await self._queries.get_daily_usage(f_start, f_end)
        weekly_usage = await self._queries.get_weekly_usage()
        monthly_usage = await self._queries.get_monthly_usage()
        active_licenses = await self._queries.get_active_licenses()
        top_endpoints = await self._queries.get_top_endpoints(limit=10)
        revenue = await self._queries.get_revenue_summary()
        tier_dist = await self._queries.get_license_tier_distribution()

        violations_summary = await self._rate_limit_emitter.get_violations_summary(hours=24)
        top_violated = await self._rate_limit_emitter.get_top_violated_tenants(limit=10, hours=24)
        events_by_tier = await self._rate_limit_emitter.get_events_by_tier(hours=24)

        license_health = await self._queries.get_license_health_summary()
        renewal_prompts = await self._queries.get_expired_licenses_for_renewal(days=7)
        recent_rate_events = await self._rate_limit_emitter.get_recent_events(limit=50)

        metrics = DashboardMetrics(
            api_calls=self._format_chart_data(daily_usage, 'daily'),
            weekly_usage=self._format_chart_data(weekly_usage, 'weekly'),
            monthly_usage=self._format_chart_data(monthly_usage, 'monthly'),
            active_licenses={'total': len(active_licenses), 'licenses': active_licenses[:20]},
            top_endpoints=top_endpoints, revenue=revenue, tier_distribution=tier_dist,
            last_updated=datetime.now().isoformat(), rate_limit_violations=top_violated,
            quota_usage_by_tenant=events_by_tier, violations_summary=violations_summary,
            license_health=license_health, renewal_prompts=renewal_prompts,
            rate_limit_events=recent_rate_events,
        )
        self._set_cache(cache_key, metrics)
        return metrics

    def _format_chart_data(self, data: List[Dict[str, Any]], granularity: str = 'daily') -> List[Dict[str, Any]]:
        return [
            {
                'date': row.get('date', row.get('week_start', row.get('month', ''))),
                'calls': int(row.get('calls', 0)),
                'unique_licenses': int(row.get('unique_licenses', 0)),
            }
            for row in data
        ]

    def calculate_growth_rate(self, current: float, previous: float) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)
