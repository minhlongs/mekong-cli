# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Audit Export Module — ROIaaS Phase 7

Export compliance audit logs to CSV, JSON, and PDF formats.
Query violation_events, rate_limit_events, and validation_logs tables.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from src.db.database import DatabaseConnection, get_database
from src.raas.audit_export_renderers import (
    AuditExportRenderersMixin,
    ExportFilter,
    ExportFormat,
)

logger = logging.getLogger(__name__)


class AuditExporter(AuditExportRenderersMixin):
    """Export audit logs to various formats for compliance reporting."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        """Initialize exporter with database connection."""
        self._db = db or get_database()

    def _validate_filters(self, filters: ExportFilter) -> None:
        """Validate filter inputs to prevent SQL injection."""
        if filters.license_key:
            if not re.match(r"^[a-zA-Z0-9_-]{1,255}$", filters.license_key):
                raise ValueError(
                    "license_key must contain only alphanumeric characters, "
                    "hyphens, and underscores (max 255 chars)"
                )

        if filters.tenant_id:
            if not re.match(r"^[a-zA-Z0-9_-]{1,255}$", filters.tenant_id):
                raise ValueError(
                    "tenant_id must contain only alphanumeric characters, "
                    "hyphens, and underscores (max 255 chars)"
                )

        if filters.limit < 1 or filters.limit > 100000:
            raise ValueError("limit must be between 1 and 100000")

        if filters.date_from > filters.date_to:
            raise ValueError("date_from must be before or equal to date_to")

    async def query_events(
        self, filters: ExportFilter
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Query audit events based on filters."""
        self._validate_filters(filters)

        events: Dict[str, List[Dict[str, Any]]] = {
            "violation_events": [],
            "rate_limit_events": [],
            "validation_logs": [],
        }

        where_clauses: List[str] = []
        params_base: List[Any] = []
        param_idx = 1

        if filters.license_key or filters.tenant_id:
            key_id = filters.license_key or filters.tenant_id
            where_clauses.append(f"key_id = ${param_idx}")
            params_base.append(key_id)
            param_idx += 1

        date_from = filters.date_from.isoformat()
        date_to = filters.date_to.isoformat()

        violation_query = f"""
            SELECT * FROM violation_events
            WHERE {' AND '.join(where_clauses)}
              AND occurred_at >= ${param_idx}
              AND occurred_at <= ${param_idx + 1}
            ORDER BY occurred_at DESC
            LIMIT ${param_idx + 2}
        """
        params = tuple(params_base) + (date_from, date_to, filters.limit)
        results = await self._db.fetch_all(violation_query, params)
        events["violation_events"] = [dict(row) for row in results]

        has_key = bool(filters.license_key or filters.tenant_id)
        rate_query = f"""
            SELECT * FROM rate_limit_events
            WHERE tenant_id = ${1 if has_key else -1}
              AND created_at >= ${2 if has_key else 1}
              AND created_at <= ${3 if has_key else 2}
            ORDER BY created_at DESC
            LIMIT ${4 if has_key else 3}
        """
        rate_params = (
            params_base + [date_from, date_to, filters.limit]
            if params_base
            else [date_from, date_to, filters.limit]
        )
        if not has_key:
            rate_query = """
                SELECT * FROM rate_limit_events
                WHERE created_at >= $1 AND created_at <= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
        rate_results = await self._db.fetch_all(rate_query, tuple(rate_params))
        events["rate_limit_events"] = [dict(row) for row in rate_results]

        validation_query = f"""
            SELECT * FROM license_validation_logs
            WHERE {' AND '.join(where_clauses)}
              AND validated_at >= ${param_idx}
              AND validated_at <= ${param_idx + 1}
            ORDER BY validated_at DESC
            LIMIT ${param_idx + 2}
        """
        validation_params = tuple(params_base) + (date_from, date_to, filters.limit)
        validation_results = await self._db.fetch_all(
            validation_query, validation_params
        )
        events["validation_logs"] = [dict(row) for row in validation_results]

        return events


__all__ = [
    "AuditExporter",
    "ExportFilter",
    "ExportFormat",
]
