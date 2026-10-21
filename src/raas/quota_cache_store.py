# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite-backed QuotaCache storage implementation."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
from typing import Optional

from src.raas.quota_cache_models import (
    _DDL,
    DB_PATH,
    DEFAULT_TTL_SECONDS,
    GRACE_PERIOD_SECONDS,
    QuotaState,
    _row_to_quota_state,
)


def _resolve_db_path(db_path: Optional[Path]) -> Path:
    if db_path is not None:
        return db_path
    mod = sys.modules.get("src.raas.quota_cache")
    return getattr(mod, "DB_PATH", DB_PATH) if mod else DB_PATH


class QuotaCache:
    """SQLite-backed quota state cache with TTL and schema migration."""

    def __init__(self, db_path: Optional[Path] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.db_path = _resolve_db_path(db_path)
        self.ttl_seconds = ttl_seconds
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(quota_cache)").fetchall()}
        cols = {
            "grace_period_remaining": "INTEGER DEFAULT 86400",
            "last_online_validation": "TEXT",
            "is_offline_mode": "BOOLEAN DEFAULT 0",
            "last_reset_date": "TEXT",
        }
        for col_name, col_def in cols.items():
            if col_name not in existing:
                try:
                    conn.execute(f"ALTER TABLE quota_cache ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass

    def _init_db(self) -> None:
        try:
            with closing(self._connect()) as conn:
                conn.executescript(_DDL)
                self._migrate_schema(conn)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"QuotaCache: DB init failed: {exc}") from exc

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _iso(dt: datetime) -> str:
        return dt.isoformat()

    def get(self, key_id: str) -> Optional[QuotaState]:
        try:
            with closing(self._connect()) as conn:
                row = conn.execute(
                    "SELECT * FROM quota_cache WHERE key_id = ? AND expires_at > ?",
                    (key_id, self._iso(self._now())),
                ).fetchone()
                if not row:
                    return None
                state = _row_to_quota_state(row, full=True)
                today = self._now().strftime("%Y-%m-%d")
                if state.last_reset_date and state.last_reset_date != today:
                    state.daily_used = 0
                    state.last_reset_date = today
                    self.set(
                        key_id=key_id, daily_used=0, daily_limit=state.daily_limit,
                        tier=state.tier, status=state.status, expires_at_ts=state.expires_at_ts,
                        monthly_used=state.monthly_used, monthly_limit=state.monthly_limit,
                        grace_period_remaining=state.grace_period_remaining,
                        last_online_validation=state.last_online_validation,
                        is_offline_mode=state.is_offline_mode,
                    )
                return state
        except sqlite3.Error as exc:
            raise RuntimeError(f"QuotaCache.get failed: {exc}") from exc

    def set(
        self, key_id: str, daily_used: int, daily_limit: int, tier: str = "free",
        status: str = "active", expires_at_ts: int = 0, monthly_used: int = 0, monthly_limit: int = 0,
        grace_period_remaining: int = GRACE_PERIOD_SECONDS, last_online_validation: str = "",
        is_offline_mode: bool = False, last_reset_date: Optional[str] = None,
    ) -> QuotaState:
        now = self._now()
        expires = now + timedelta(seconds=self.ttl_seconds)
        state = QuotaState(
            key_id=key_id, daily_used=daily_used, daily_limit=daily_limit,
            tier=tier, status=status, expires_at_ts=expires_at_ts,
            monthly_used=monthly_used, monthly_limit=monthly_limit,
            cached_at=self._iso(now), expires_at=self._iso(expires),
            grace_period_remaining=grace_period_remaining,
            last_online_validation=last_online_validation or self._iso(now),
            is_offline_mode=is_offline_mode,
            last_reset_date=last_reset_date or now.strftime("%Y-%m-%d"),
        )
        try:
            with closing(self._connect()) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO quota_cache "
                    "(key_id, daily_used, daily_limit, tier, status, expires_at_ts, "
                    "monthly_used, monthly_limit, cached_at, expires_at, "
                    "grace_period_remaining, last_online_validation, is_offline_mode, last_reset_date) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        key_id, daily_used, daily_limit, tier, status, expires_at_ts,
                        monthly_used, monthly_limit, state.cached_at, state.expires_at,
                        state.grace_period_remaining, state.last_online_validation,
                        state.is_offline_mode, state.last_reset_date,
                    ),
                )
                conn.commit()
            return state
        except sqlite3.Error as exc:
            raise RuntimeError(f"QuotaCache.set failed: {exc}") from exc

    def _delete_where(self, label: str, query: str, params: tuple = ()) -> int:
        try:
            with closing(self._connect()) as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as exc:
            raise RuntimeError(f"QuotaCache.{label} failed: {exc}") from exc

    def invalidate(self, key_id: str) -> bool:
        return self._delete_where("invalidate", "DELETE FROM quota_cache WHERE key_id = ?", (key_id,)) > 0

    def clear(self) -> int:
        return self._delete_where("clear", "DELETE FROM quota_cache WHERE expires_at <= ?", (self._iso(self._now()),))

    def clear_all(self) -> int:
        return self._delete_where("clear_all", "DELETE FROM quota_cache")

    def get_all(self) -> list[QuotaState]:
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute("SELECT * FROM quota_cache WHERE expires_at > ?", (self._iso(self._now()),)).fetchall()
                return [_row_to_quota_state(r, full=False) for r in rows]
        except sqlite3.Error as exc:
            raise RuntimeError(f"QuotaCache.get_all failed: {exc}") from exc

