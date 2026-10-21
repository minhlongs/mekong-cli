# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Violation Tracker — ROIaaS Phase 6

Tracks quota exceeded events and license violations for analytics dashboard.
Stores to PostgreSQL violation_events table for reporting and enforcement.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional

from src.db.database import DatabaseConnection, get_database
from src.db.repository import LicenseRepository, get_repository
from src.raas.violation_tracker_models import (
    ViolationEvent,
    fetch_violation_summary,
)


class ViolationTracker:
    """Track and store license/quota violations for analytics."""

    def __init__(
        self,
        repository: Optional[LicenseRepository] = None,
        db: Optional[DatabaseConnection] = None,
    ) -> None:
        self._repo = repository or get_repository()
        self._db = db or get_database()

    async def record_violation(self, violation: ViolationEvent) -> Dict[str, Any]:
        """Record a violation event to PostgreSQL."""
        query = """
            INSERT INTO violation_events (
                key_id, tier, violation_type, command,
                daily_used, daily_limit, monthly_used, monthly_limit,
                retry_after_seconds, metadata, occurred_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            ) RETURNING id, created_at
        """
        metadata_json = json.dumps(violation.metadata or {})
        result = await self._db.fetch_one(
            query,
            (
                violation.key_id,
                violation.tier,
                violation.violation_type,
                violation.command,
                violation.daily_used,
                violation.daily_limit,
                violation.monthly_used,
                violation.monthly_limit,
                violation.retry_after_seconds,
                metadata_json,
                datetime.now(timezone.utc),
            ),
        )
        return dict(result) if result else {}

    async def get_violations_by_key(
        self,
        key_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """Get violation history for a specific key."""
        if not isinstance(days, int) or days < 0 or days > 365:
            raise ValueError("days must be an integer between 0 and 365")

        query = f"""
            SELECT * FROM violation_events
            WHERE key_id = $1
              AND occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
            ORDER BY occurred_at DESC
            LIMIT $2
        """
        results = await self._db.fetch_all(query, (key_id, limit))
        return [dict(row) for row in results]

    async def get_violation_summary(
        self,
        key_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get violation summary for analytics dashboard."""
        return await fetch_violation_summary(self._db, key_id, days=days)

    async def get_all_violations(
        self,
        days: int = 7,
        limit: int = 500,
    ) -> list[Dict[str, Any]]:
        """Get all recent violations for admin dashboard."""
        query = f"""
            SELECT * FROM violation_events
            WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
            ORDER BY occurred_at DESC
            LIMIT $1
        """
        results = await self._db.fetch_all(query, (limit,))
        return [dict(row) for row in results]


_tracker: Optional[ViolationTracker] = None


def get_tracker() -> ViolationTracker:
    """Get global violation tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ViolationTracker()
    return _tracker


async def record_violation(violation: ViolationEvent) -> Dict[str, Any]:
    """Record a violation event."""
    return await get_tracker().record_violation(violation)


__all__ = [
    "ViolationTracker",
    "ViolationEvent",
    "get_tracker",
    "record_violation",
]
