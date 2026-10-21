# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and schema DDL for the Quota State Cache."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path.home() / ".mekong" / "raas" / "quota_cache.db"

DEFAULT_TTL_SECONDS = 300  # 5 minutes (cache TTL for normal operation)
GRACE_PERIOD_SECONDS = 86400  # 24 hours offline grace period

_DDL = """
CREATE TABLE IF NOT EXISTS quota_cache (
    key_id          TEXT PRIMARY KEY,
    daily_used      INTEGER NOT NULL,
    daily_limit     INTEGER NOT NULL,
    tier            TEXT NOT NULL,
    status          TEXT DEFAULT 'active',
    expires_at_ts   INTEGER DEFAULT 0,
    monthly_used    INTEGER DEFAULT 0,
    monthly_limit   INTEGER DEFAULT 0,
    cached_at       TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    grace_period_remaining INTEGER DEFAULT 86400,
    last_online_validation TEXT,
    is_offline_mode BOOLEAN DEFAULT FALSE,
    last_reset_date TEXT
);
CREATE INDEX IF NOT EXISTS idx_quota_cache_expires
    ON quota_cache (expires_at);
"""


@dataclass
class QuotaState:
    """Cached quota state for a key."""

    key_id: str
    daily_used: int
    daily_limit: int
    tier: str = "free"
    status: str = "active"  # active, revoked, expired
    expires_at_ts: int = 0  # 0 = never expires
    monthly_used: int = 0
    monthly_limit: int = 0
    cached_at: str = ""
    expires_at: str = ""
    grace_period_remaining: int = GRACE_PERIOD_SECONDS
    last_online_validation: str = ""
    is_offline_mode: bool = False
    last_reset_date: str = ""

    def __post_init__(self) -> None:
        if not self.cached_at:
            self.cached_at = datetime.now(timezone.utc).isoformat()
        if not self.expires_at:
            expires = datetime.now(timezone.utc) + timedelta(seconds=DEFAULT_TTL_SECONDS)
            self.expires_at = expires.isoformat()

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now(timezone.utc) >= expires

    def is_license_expired(self) -> bool:
        """Check if license itself is expired."""
        if self.expires_at_ts <= 0:
            return False
        now_ts = int(datetime.now(timezone.utc).timestamp())
        return now_ts >= self.expires_at_ts

    def is_revoked(self) -> bool:
        """Check if license is revoked."""
        return self.status == "revoked"

    def remaining_seconds(self) -> int:
        """Get seconds until cache expires."""
        expires = datetime.fromisoformat(self.expires_at)
        delta = expires - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))

    def usage_percentage(self) -> float:
        """Get usage as percentage of limit."""
        if self.daily_limit <= 0:
            return 0.0
        return (self.daily_used / self.daily_limit) * 100

    def remaining(self) -> int:
        """Get remaining commands."""
        if self.daily_limit <= 0:
            return -1
        return max(0, self.daily_limit - self.daily_used)

    def is_in_grace_period(self) -> bool:
        """Check if still within offline grace period."""
        if not self.last_online_validation:
            return False
        last_valid = datetime.fromisoformat(self.last_online_validation)
        now = datetime.now(timezone.utc)
        elapsed = (now - last_valid).total_seconds()
        return elapsed < self.grace_period_remaining

    def remaining_grace_seconds(self) -> int:
        """Get remaining seconds in grace period."""
        if not self.last_online_validation:
            return 0
        last_valid = datetime.fromisoformat(self.last_online_validation)
        now = datetime.now(timezone.utc)
        elapsed = (now - last_valid).total_seconds()
        return max(0, int(self.grace_period_remaining - elapsed))

    def remaining_grace_hours(self) -> float:
        """Get remaining grace period in hours (for display)."""
        return round(self.remaining_grace_seconds() / 3600, 1)


def _row_to_quota_state(row: sqlite3.Row, full: bool = True) -> QuotaState:
    keys = row.keys()
    if not full:
        return QuotaState(
            key_id=row["key_id"],
            daily_used=row["daily_used"],
            daily_limit=row["daily_limit"],
            tier=row["tier"],
            monthly_used=row["monthly_used"] if "monthly_used" in keys else 0,
            monthly_limit=row["monthly_limit"] if "monthly_limit" in keys else 0,
            cached_at=row["cached_at"],
            expires_at=row["expires_at"],
        )
    return QuotaState(
        key_id=row["key_id"],
        daily_used=row["daily_used"],
        daily_limit=row["daily_limit"],
        tier=row["tier"],
        status=row["status"] if "status" in keys else "active",
        expires_at_ts=row["expires_at_ts"] if "expires_at_ts" in keys else 0,
        monthly_used=row["monthly_used"] if "monthly_used" in keys else 0,
        monthly_limit=row["monthly_limit"] if "monthly_limit" in keys else 0,
        cached_at=row["cached_at"],
        expires_at=row["expires_at"],
        grace_period_remaining=(
            row["grace_period_remaining"]
            if "grace_period_remaining" in keys
            else GRACE_PERIOD_SECONDS
        ),
        last_online_validation=(
            row["last_online_validation"] if "last_online_validation" in keys else ""
        ),
        is_offline_mode=(
            bool(row["is_offline_mode"]) if "is_offline_mode" in keys else False
        ),
        last_reset_date=row["last_reset_date"] if "last_reset_date" in keys else "",
    )
