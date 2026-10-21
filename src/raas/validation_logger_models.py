# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Validation Logger Models & Query Helpers — ROIaaS Phase 6e

Dataclass and SQL aggregation helpers for license validation logging.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.db.database import DatabaseConnection


@dataclass
class ValidationLog:
    """Represents a license validation attempt.

    Attributes:
        key_id: License key ID being validated
        result: Validation result (success, failed, offline_grace, revoked, expired)
        command: Command that triggered the validation
        duration_ms: Validation duration in milliseconds
        error_type: Type of error if failed (format_error, network_error, quota_exceeded, etc.)
        offline_mode: True if validation used offline cache
        grace_period_remaining: Seconds remaining in grace period (if offline mode)
        ip_address: Client IP address (if available)
        user_agent: Client user agent (if available)
        metadata: Additional context
    """

    key_id: str
    result: str  # success, failed, offline_grace, revoked, expired
    command: str
    duration_ms: float = 0.0
    error_type: Optional[str] = None
    offline_mode: bool = False
    grace_period_remaining: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


async def fetch_validation_stats(
    db: DatabaseConnection, key_id: str, days: int = 30
) -> Dict[str, Any]:
    """Compute validation statistics for analytics dashboard."""
    if not isinstance(days, int) or days < 0 or days > 365:
        raise ValueError("days must be an integer between 0 and 365")

    total_query = f"""
        SELECT COUNT(*) as total
        FROM license_validation_logs
        WHERE key_id = $1
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
    """
    total_result = await db.fetch_one(total_query, (key_id,))
    total = total_result["total"] if total_result else 0

    success_query = f"""
        SELECT COUNT(*) as success_count
        FROM license_validation_logs
        WHERE key_id = $1
          AND result = 'success'
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
    """
    success_result = await db.fetch_one(success_query, (key_id,))
    success_count = success_result["success_count"] if success_result else 0
    success_rate = (success_count / total * 100) if total > 0 else 0

    offline_query = f"""
        SELECT COUNT(*) as offline_count
        FROM license_validation_logs
        WHERE key_id = $1
          AND offline_mode = true
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
    """
    offline_result = await db.fetch_one(offline_query, (key_id,))
    offline_count = offline_result["offline_count"] if offline_result else 0

    result_query = f"""
        SELECT result, COUNT(*) as count
        FROM license_validation_logs
        WHERE key_id = $1
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
        GROUP BY result
        ORDER BY count DESC
    """
    result_results = await db.fetch_all(result_query, (key_id,))
    by_result = {row["result"]: row["count"] for row in result_results}

    error_query = f"""
        SELECT error_type, COUNT(*) as count
        FROM license_validation_logs
        WHERE key_id = $1
          AND error_type IS NOT NULL
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
        GROUP BY error_type
        ORDER BY count DESC
    """
    error_results = await db.fetch_all(error_query, (key_id,))
    by_error = {row["error_type"]: row["count"] for row in error_results}

    last_query = """
        SELECT * FROM license_validation_logs
        WHERE key_id = $1
        ORDER BY validated_at DESC
        LIMIT 1
    """
    last_result = await db.fetch_one(last_query, (key_id,))
    last_validation = dict(last_result) if last_result else None

    avg_duration_query = f"""
        SELECT AVG(duration_ms) as avg_duration
        FROM license_validation_logs
        WHERE key_id = $1
          AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
    """
    avg_result = await db.fetch_one(avg_duration_query, (key_id,))
    avg_duration = avg_result["avg_duration"] if avg_result else 0

    return {
        "key_id": key_id,
        "total_validations": total,
        "success_count": success_count,
        "success_rate": round(success_rate, 2),
        "offline_count": offline_count,
        "offline_percentage": round((offline_count / total * 100) if total > 0 else 0, 2),
        "by_result": by_result,
        "by_error": by_error,
        "last_validation": last_validation,
        "avg_duration_ms": round(avg_duration, 2),
        "period_days": days,
    }
