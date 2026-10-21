# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Analytics Queries — ROIaaS Phase 5

Query builders for dashboard metrics:
- API call volume (daily/weekly/monthly)
- Active license keys
- Top endpoints
- Revenue estimation
"""

from typing import List, Dict, Any, Optional

from src.db.database import DatabaseConnection
from src.seed.config.tiers import get_tier
from src.db.queries.analytics_license_queries import AnalyticsLicenseQueriesMixin


class AnalyticsQueries(AnalyticsLicenseQueriesMixin):
    """Analytics query builders for ROIaaS dashboard."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        """Initialize with database connection."""
        self._db = db or DatabaseConnection()

    async def get_daily_usage(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get API calls per day for date range."""
        query = """
            SELECT
                date::text,
                COALESCE(SUM(commands_count), 0) as calls,
                COUNT(DISTINCT key_id) as unique_licenses
            FROM usage_records
            WHERE date BETWEEN $1 AND $2
            GROUP BY date
            ORDER BY date ASC
        """
        return await self._db.fetch_all(query, (start_date, end_date))

    async def get_weekly_usage(self) -> List[Dict[str, Any]]:
        """Get API calls per week (last 12 weeks)."""
        query = """
            SELECT
                date_trunc('week', date)::date as week_start,
                COALESCE(SUM(commands_count), 0) as calls,
                COUNT(DISTINCT key_id) as unique_licenses
            FROM usage_records
            WHERE date >= CURRENT_DATE - INTERVAL '12 weeks'
            GROUP BY week_start
            ORDER BY week_start ASC
        """
        return await self._db.fetch_all(query)

    async def get_monthly_usage(self) -> List[Dict[str, Any]]:
        """Get API calls per month (last 12 months)."""
        query = """
            SELECT
                date_trunc('month', date)::date as month,
                COALESCE(SUM(commands_count), 0) as calls,
                COUNT(DISTINCT key_id) as unique_licenses
            FROM usage_records
            WHERE date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month ASC
        """
        return await self._db.fetch_all(query)

    async def get_active_licenses(self) -> List[Dict[str, Any]]:
        """Get all active license keys with usage data."""
        query = """
            SELECT
                l.license_key,
                l.tier,
                l.email,
                l.status,
                l.created_at,
                COALESCE(SUM(u.commands_count), 0) as total_commands,
                MAX(u.date) as last_active
            FROM licenses l
            LEFT JOIN usage_records u ON l.key_id = u.key_id
            WHERE l.status = 'active'
            GROUP BY l.id, l.license_key, l.tier, l.email, l.status, l.created_at
            ORDER BY total_commands DESC
        """
        return await self._db.fetch_all(query)

    async def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used endpoints."""
        query = """
            SELECT
                endpoint,
                COUNT(*) as calls,
                AVG(duration_ms) as avg_duration
            FROM api_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY endpoint
            ORDER BY calls DESC
            LIMIT $1
        """
        try:
            return await self._db.fetch_all(query, (limit,))
        except Exception:
            return []


__all__ = ["AnalyticsQueries", "get_tier"]
