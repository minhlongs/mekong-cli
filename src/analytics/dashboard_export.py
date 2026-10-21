# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dashboard Service Data Export Mixin."""

import csv
import io
import json
from typing import Any, Dict, List, Optional, Tuple

from src.db.queries.analytics_queries import AnalyticsQueries


class DashboardExportMixin:
    """Mixin for CSV and JSON analytics data exports."""

    _queries: AnalyticsQueries

    def _format_chart_data(self, data: List[Dict[str, Any]], granularity: str = 'daily') -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def export_to_csv(self, date_range: Tuple[str, str], license_key: Optional[str] = None) -> str:
        start_date, end_date = date_range
        daily_data = await self._queries.get_daily_usage(start_date, end_date)
        if license_key:
            daily_data = [d for d in daily_data if d.get('key_id') == license_key]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['date', 'api_calls', 'unique_licenses'])
        for row in daily_data:
            writer.writerow([row.get('date', ''), row.get('calls', 0), row.get('unique_licenses', 0)])
        return output.getvalue()

    async def export_to_json(self, date_range: Tuple[str, str], license_key: Optional[str] = None) -> str:
        from datetime import datetime
        start_date, end_date = date_range
        daily = await self._queries.get_daily_usage(start_date, end_date)
        weekly = await self._queries.get_weekly_usage()
        monthly = await self._queries.get_monthly_usage()
        active = await self._queries.get_active_licenses()
        revenue = await self._queries.get_revenue_summary()
        tiers = await self._queries.get_license_tier_distribution()

        if license_key:
            daily = [d for d in daily if d.get('key_id') == license_key]
            active = [a for a in active if a.get('key_id') == license_key]

        export_data = {
            'exported_at': datetime.now().isoformat(),
            'date_range': {'start': start_date, 'end': end_date},
            'filters': {'license_key': license_key},
            'usage': {
                'daily': self._format_chart_data(daily, 'daily'),
                'weekly': self._format_chart_data(weekly, 'weekly'),
                'monthly': self._format_chart_data(monthly, 'monthly'),
            },
            'licenses': {'active_count': len(active), 'tier_distribution': tiers},
            'revenue': revenue,
        }
        return json.dumps(export_data, indent=2)
