# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Fair-use rate limiter for RaaS tenants.

Implements a sliding window rate limiter backed by SQLite.
Daily = last 24 hours, monthly = last 30 days.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Optional
import uuid

from src.raas.credit_rate_limiter_models import (
    _DDL,
    DB_PATH,
    OVERAGE_TIERS,
    TIER_LIMITS,
    OverageConfig,
    RateLimitStatus,
    get_overage_config,
)


class CreditRateLimiter:
    """Sliding-window rate limiter persisted in SQLite."""

    def __init__(
        self,
        db_path: Path = DB_PATH,
        daily_limit: int = TIER_LIMITS["free"]["daily"],
        monthly_limit: int = TIER_LIMITS["free"]["monthly"],
    ) -> None:
        self.db_path = db_path
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_DDL)
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditRateLimiter: DB init failed: {exc}") from exc

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _iso(dt: datetime) -> str:
        return dt.isoformat()

    def _sum_credits(self, conn: sqlite3.Connection, tenant_id: str, since: datetime) -> int:
        row = conn.execute(
            "SELECT COALESCE(SUM(credits_used), 0) AS total FROM rate_limit_events "
            "WHERE tenant_id = ? AND timestamp >= ?",
            (tenant_id, self._iso(since)),
        ).fetchone()
        return int(row["total"])

    def _oldest_timestamp_in_window(
        self, conn: sqlite3.Connection, tenant_id: str, since: datetime
    ) -> Optional[datetime]:
        row = conn.execute(
            "SELECT MIN(timestamp) AS oldest FROM rate_limit_events "
            "WHERE tenant_id = ? AND timestamp >= ?",
            (tenant_id, self._iso(since)),
        ).fetchone()
        if row and row["oldest"]:
            return datetime.fromisoformat(row["oldest"])
        return None

    def check_limit(self, tenant_id: str) -> RateLimitStatus:
        """Check whether *tenant_id* is within their rate limits."""
        now = self._now()
        daily_since = now - timedelta(hours=24)
        monthly_since = now - timedelta(days=30)

        try:
            with self._connect() as conn:
                daily_used = self._sum_credits(conn, tenant_id, daily_since)
                monthly_used = self._sum_credits(conn, tenant_id, monthly_since)

                daily_exceeded = self.daily_limit > 0 and daily_used >= self.daily_limit
                monthly_exceeded = self.monthly_limit > 0 and monthly_used >= self.monthly_limit

                if daily_exceeded or monthly_exceeded:
                    window_since = daily_since if daily_exceeded else monthly_since
                    window_hours = 24 if daily_exceeded else 24 * 30
                    oldest = self._oldest_timestamp_in_window(conn, tenant_id, window_since)
                    retry_after: Optional[int] = None
                    if oldest is not None:
                        expires_at = oldest + timedelta(hours=window_hours)
                        retry_after = max(0, int((expires_at - now).total_seconds()))

                    return RateLimitStatus(
                        allowed=False,
                        daily_used=daily_used,
                        daily_limit=self.daily_limit,
                        monthly_used=monthly_used,
                        monthly_limit=self.monthly_limit,
                        retry_after_seconds=retry_after,
                    )

                return RateLimitStatus(
                    allowed=True,
                    daily_used=daily_used,
                    daily_limit=self.daily_limit,
                    monthly_used=monthly_used,
                    monthly_limit=self.monthly_limit,
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditRateLimiter.check_limit failed: {exc}") from exc

    def record_request(self, tenant_id: str, credits_used: int) -> None:
        """Log a request event into the sliding window."""
        if credits_used <= 0:
            raise ValueError("credits_used must be positive")
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO rate_limit_events (id, tenant_id, credits_used, timestamp) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), tenant_id, credits_used, self._iso(self._now())),
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditRateLimiter.record_request failed: {exc}") from exc

    def get_limits(self, tenant_id: str) -> dict:
        """Return current usage versus configured limits for *tenant_id*."""
        now = self._now()
        try:
            with self._connect() as conn:
                daily_used = self._sum_credits(conn, tenant_id, now - timedelta(hours=24))
                monthly_used = self._sum_credits(conn, tenant_id, now - timedelta(days=30))
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditRateLimiter.get_limits failed: {exc}") from exc

        return {
            "daily_used": daily_used,
            "daily_limit": self.daily_limit,
            "daily_remaining": max(0, self.daily_limit - daily_used) if self.daily_limit > 0 else None,
            "monthly_used": monthly_used,
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": max(0, self.monthly_limit - monthly_used) if self.monthly_limit > 0 else None,
        }


__all__ = [
    "DB_PATH", "TIER_LIMITS", "OverageConfig", "OVERAGE_TIERS",
    "get_overage_config", "_DDL", "RateLimitStatus", "CreditRateLimiter",
]
