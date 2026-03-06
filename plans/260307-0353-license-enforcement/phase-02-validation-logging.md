---
title: "Phase 2: Validation Logging"
description: "Log all validation attempts for analytics dashboard"
status: pending
priority: P2
effort: 1.5h
---

# Phase 2: Validation Logging Implementation

## Objective

Track tất cả validation attempts (thành công và thất bại) để phân tích usage patterns và phát hiện abuse.

## Database Schema

**New Table:** `license_validation_logs`

```sql
CREATE TABLE IF NOT EXISTS license_validation_logs (
    id              SERIAL PRIMARY KEY,
    key_id          VARCHAR(255),
    tier            VARCHAR(50),
    command         VARCHAR(100),
    result          VARCHAR(20),     -- 'allowed', 'blocked', 'offline_grace'
    validation_type VARCHAR(50),     -- 'remote', 'local', 'cache', 'offline_grace'
    error_code      VARCHAR(100),
    duration_ms     INTEGER,
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB,
    validated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_validation_logs_key_id ON license_validation_logs(key_id);
CREATE INDEX idx_validation_logs_validated_at ON license_validation_logs(validated_at);
CREATE INDEX idx_validation_logs_result ON license_validation_logs(result);
```

## New File: src/raas/validation_logger.py

```python
"""
Validation Logger — ROIaaS Phase 6e

Logs all license validation attempts for analytics.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
import time

from src.db.database import get_database, DatabaseConnection


@dataclass
class ValidationLog:
    """Validation attempt log entry."""
    key_id: Optional[str]
    command: str
    result: str  # 'allowed', 'blocked', 'offline_grace'
    validation_type: str  # 'remote', 'local', 'cache', 'offline_grace'
    tier: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: int = 0
    metadata: Optional[Dict[str, Any]] = None


class ValidationLogger:
    """Log validation attempts for analytics."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()
        self._async_mode = True

    async def log_validation(
        self,
        log: ValidationLog,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log a validation attempt.

        Args:
            log: ValidationLog dataclass
            ip_address: Client IP (optional)
            user_agent: User agent string (optional)

        Returns:
            Created log record
        """
        query = """
            INSERT INTO license_validation_logs (
                key_id, tier, command, result, validation_type,
                error_code, duration_ms, ip_address, user_agent,
                metadata, validated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            ) RETURNING id, validated_at
        """

        metadata_json = json.dumps(log.metadata or {})

        result = await self._db.fetch_one(
            query,
            (
                log.key_id,
                log.tier,
                log.command,
                log.result,
                log.validation_type,
                log.error_code,
                log.duration_ms,
                ip_address,
                user_agent,
                metadata_json,
                datetime.now(timezone.utc),
            )
        )

        return dict(result) if result else {}

    def log_validation_sync(
        self,
        log: ValidationLog,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Synchronous wrapper for fire-and-forget logging.
        Does not block CLI execution.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule without awaiting
                asyncio.ensure_future(self.log_validation(log, ip_address, user_agent))
            else:
                loop.run_until_complete(self.log_validation(log, ip_address, user_agent))
        except Exception:
            # Never fail on logging
            pass

    async def get_validation_history(
        self,
        key_id: str,
        days: int = 30,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """Get validation history for a key."""
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
        self,
        key_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get validation statistics for analytics."""
        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE result = 'allowed') as allowed,
                COUNT(*) FILTER (WHERE result = 'blocked') as blocked,
                COUNT(*) FILTER (WHERE result = 'offline_grace') as offline_grace,
                COUNT(*) FILTER (WHERE validation_type = 'remote') as remote,
                COUNT(*) FILTER (WHERE validation_type = 'local') as local,
                AVG(duration_ms) as avg_duration_ms
            FROM license_validation_logs
            WHERE key_id = $1
              AND validated_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
        """

        result = await self._db.fetch_one(query, (key_id,))
        return dict(result) if result else {}


# Singleton
_logger: Optional[ValidationLogger] = None


def get_logger() -> ValidationLogger:
    """Get global validation logger instance."""
    global _logger
    if _logger is None:
        _logger = ValidationLogger()
    return _logger


def log_validation(
    key_id: Optional[str],
    command: str,
    result: str,
    validation_type: str,
    tier: Optional[str] = None,
    error_code: Optional[str] = None,
    duration_ms: int = 0,
) -> None:
    """Log validation attempt (fire-and-forget)."""
    log = ValidationLog(
        key_id=key_id,
        command=command,
        result=result,
        validation_type=validation_type,
        tier=tier,
        error_code=error_code,
        duration_ms=duration_ms,
    )
    get_logger().log_validation_sync(log)


__all__ = [
    "ValidationLogger",
    "ValidationLog",
    "get_logger",
    "log_validation",
]
```

## Integration with RaasLicenseGate

**File:** `src/lib/raas_gate.py`

```python
def check(self, command: str) -> Tuple[bool, Optional[str]]:
    start_time = time.time()
    validation_type = "unknown"
    error_code = None
    result = "blocked"

    try:
        # ... existing validation logic ...

        # At each validation path, log:

        # Remote success
        validation_type = "remote"
        result = "allowed"

        # Local fallback
        validation_type = "local"
        result = "allowed"

        # Offline grace
        validation_type = "offline_grace"
        result = "offline_grace"

        # Blocked
        result = "blocked"
        error_code = "quota_exceeded"

    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        log_validation(
            key_id=self._key_id,
            command=command,
            result=result,
            validation_type=validation_type,
            tier=self._license_tier,
            error_code=error_code,
            duration_ms=duration_ms,
        )
```

## Implementation Steps

1. [ ] Create database migration for `license_validation_logs` table
2. [ ] Create `src/raas/validation_logger.py`
3. [ ] Integrate logging into `RaasLicenseGate.check()`
4. [ ] Add async logging to avoid blocking CLI
5. [ ] Create analytics queries for dashboard

## Output Files

- New: `src/raas/validation_logger.py`
- New: `src/db/migrations/create_validation_logs_table.sql`
- Modified: `src/lib/raas_gate.py`

## Success Criteria

- [ ] Tất cả validation attempts được log
- [ ] Logging không làm chậm CLI (< 10ms overhead)
- [ ] Async logging không block execution
- [ ] Analytics queries available cho dashboard
