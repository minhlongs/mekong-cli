# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Violation event model and summary query helper for ViolationTracker."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.db.database import DatabaseConnection


@dataclass
class ViolationEvent:
    """Represents a quota/license violation event."""

    key_id: str
    tier: str
    violation_type: str
    command: str
    daily_used: int = 0
    daily_limit: int = 0
    monthly_used: int = 0
    monthly_limit: int = 0
    retry_after_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


async def fetch_violation_summary(
    db: DatabaseConnection,
    key_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """Query violation summary statistics from PostgreSQL."""
    if not isinstance(days, int) or days < 0 or days > 365:
        raise ValueError("days must be an integer between 0 and 365")

    type_query = f"""
        SELECT violation_type, COUNT(*) as count
        FROM violation_events
        WHERE key_id = $1
          AND occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
        GROUP BY violation_type
    """
    type_results = await db.fetch_all(type_query, (key_id,))
    violations_by_type = {row["violation_type"]: row["count"] for row in type_results}

    total_query = f"""
        SELECT COUNT(*) as total
        FROM violation_events
        WHERE key_id = $1
          AND occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
    """
    total_result = await db.fetch_one(total_query, (key_id,))
    total = total_result["total"] if total_result else 0

    last_query = """
        SELECT * FROM violation_events
        WHERE key_id = $1
        ORDER BY occurred_at DESC
        LIMIT 1
    """
    last_result = await db.fetch_one(last_query, (key_id,))
    last_violation = dict(last_result) if last_result else None

    return {
        "key_id": key_id,
        "total_violations": total,
        "violations_by_type": violations_by_type,
        "last_violation": last_violation,
        "period_days": days,
    }
