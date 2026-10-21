# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Validation Logger — ROIaaS Phase 6e

Logs all license validation attempts for analytics and audit trails.
Stores to PostgreSQL license_validation_logs table.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional

from src.db.database import DatabaseConnection, get_database
from src.db.repository import LicenseRepository, get_repository
from src.raas.validation_logger_models import ValidationLog, fetch_validation_stats


class ValidationLogger:
    """Log and retrieve license validation attempts for analytics."""

    def __init__(
        self,
        repository: Optional[LicenseRepository] = None,
        db: Optional[DatabaseConnection] = None,
    ) -> None:
        self._repo = repository or get_repository()
        self._db = db or get_database()

    async def log_validation(self, log: ValidationLog) -> Dict[str, Any]:
        """Log a validation attempt to PostgreSQL."""
        query = """
            INSERT INTO license_validation_logs (
                key_id, result, command, duration_ms, error_type,
                offline_mode, grace_period_remaining, ip_address,
                user_agent, metadata, validated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            ) RETURNING id, created_at
        """
        metadata_json = json.dumps(log.metadata or {})
        result = await self._db.fetch_one(
            query,
            (
                log.key_id,
                log.result,
                log.command,
                log.duration_ms,
                log.error_type,
                log.offline_mode,
                log.grace_period_remaining,
                log.ip_address,
                log.user_agent,
                metadata_json,
                datetime.now(timezone.utc),
            ),
        )
        return dict(result) if result else {}

    async def get_validations_by_key(
        self, key_id: str, days: int = 30, limit: int = 100
    ) -> list[Dict[str, Any]]:
        """Get validation history for a specific key."""
        if not isinstance(days, int) or days < 0 or days > 365:
            raise ValueError("days must be an integer between 0 and 365")

        query = f"""
            SELECT * FROM license_validation_logs
            WHERE key_id = $1
              AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
            ORDER BY validated_at DESC
            LIMIT $2
        """
        results = await self._db.fetch_all(query, (key_id, limit))
        return [dict(row) for row in results]

    async def get_validation_stats(
        self, key_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get validation statistics for analytics dashboard."""
        return await fetch_validation_stats(self._db, key_id, days)

    async def get_recent_validations(
        self, limit: int = 500, hours: int = 24
    ) -> list[Dict[str, Any]]:
        """Get recent validations across all keys for admin dashboard."""
        query = f"""
            SELECT * FROM license_validation_logs
            WHERE validated_at >= CURRENT_TIMESTAMP - INTERVAL '{hours} hours'
            ORDER BY validated_at DESC
            LIMIT $1
        """
        results = await self._db.fetch_all(query, (limit,))
        return [dict(row) for row in results]

    async def get_failed_validations(
        self, key_id: str, days: int = 7, limit: int = 50
    ) -> list[Dict[str, Any]]:
        """Get failed validations for a specific key."""
        query = f"""
            SELECT * FROM license_validation_logs
            WHERE key_id = $1
              AND result != 'success'
              AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
            ORDER BY validated_at DESC
            LIMIT $2
        """
        results = await self._db.fetch_all(query, (key_id, limit))
        return [dict(row) for row in results]


_logger: Optional[ValidationLogger] = None


def get_logger() -> ValidationLogger:
    """Get global validation logger instance."""
    global _logger
    if _logger is None:
        _logger = ValidationLogger()
    return _logger


async def log_validation(log: ValidationLog) -> Dict[str, Any]:
    """Log a validation attempt."""
    return await get_logger().log_validation(log)


async def get_validation_stats(key_id: str, days: int = 30) -> Dict[str, Any]:
    """Get validation statistics for a key."""
    return await get_logger().get_validation_stats(key_id, days)


__all__ = [
    "ValidationLogger",
    "ValidationLog",
    "get_logger",
    "log_validation",
    "get_validation_stats",
]
