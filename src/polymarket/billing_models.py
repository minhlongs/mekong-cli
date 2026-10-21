# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing database and subscription models for CashClaw."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """A customer subscription record."""
    subscription_id: str
    user_id: str
    email: str
    tier: str
    api_key: str
    active: bool
    created_at: str
    expires_at: Optional[str] = None
    grace_until: Optional[str] = None


class BillingDB:
    """SQLite-backed subscription store."""

    def __init__(self, db_path: str = "data/algo-trade.db") -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _ensure_tables(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'starter',
                    api_key TEXT UNIQUE NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT,
                    expires_at TEXT,
                    grace_until TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS billing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    subscription_id TEXT,
                    payload TEXT,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def provision_subscription(self, subscription_id: str, user_id: str, email: str, tier: str) -> Subscription:
        api_key = f"ck_{uuid.uuid4().hex}"
        sub = Subscription(
            subscription_id=subscription_id, user_id=user_id, email=email,
            tier=tier, api_key=api_key, active=True, created_at=datetime.utcnow().isoformat(),
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO subscriptions
                   (subscription_id, user_id, email, tier, api_key, active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (sub.subscription_id, sub.user_id, sub.email, sub.tier, sub.api_key, sub.created_at),
            )
        logger.info("Provisioned subscription %s tier=%s email=%s", subscription_id, tier, email)
        return sub

    def update_tier(self, subscription_id: str, new_tier: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("UPDATE subscriptions SET tier = ? WHERE subscription_id = ?", (new_tier, subscription_id))
            return cursor.rowcount > 0

    def cancel_subscription(self, subscription_id: str, grace_days: int = 7) -> bool:
        grace_until = (datetime.utcnow() + timedelta(days=grace_days)).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE subscriptions SET active = 0, grace_until = ? WHERE subscription_id = ?",
                (grace_until, subscription_id),
            )
            return cursor.rowcount > 0

    def get_by_api_key(self, api_key: str) -> Optional[Subscription]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM subscriptions WHERE api_key = ?", (api_key,)).fetchone()
        return self._row_to_sub(row) if row else None

    def get_by_subscription_id(self, subscription_id: str) -> Optional[Subscription]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM subscriptions WHERE subscription_id = ?", (subscription_id,)).fetchone()
        return self._row_to_sub(row) if row else None

    def log_event(self, event_type: str, subscription_id: str, payload: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO billing_events (event_type, subscription_id, payload) VALUES (?, ?, ?)",
                (event_type, subscription_id, payload),
            )

    def count_active(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute("SELECT tier, COUNT(*) FROM subscriptions WHERE active = 1 GROUP BY tier").fetchall()
        return {tier: count for tier, count in rows}

    @staticmethod
    def _row_to_sub(row: sqlite3.Row) -> Subscription:
        return Subscription(
            subscription_id=row["subscription_id"], user_id=row["user_id"],
            email=row["email"], tier=row["tier"], api_key=row["api_key"],
            active=bool(row["active"]), created_at=row["created_at"],
            expires_at=row["expires_at"], grace_until=row["grace_until"],
        )
