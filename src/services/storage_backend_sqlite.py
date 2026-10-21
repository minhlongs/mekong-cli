# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite storage backend for VN Pilot (WAL mode + thread-safe lock)."""
from __future__ import annotations

import json
import sqlite3
import threading

from src.services.sqlite_migrations import _db_path


class SqliteBackend:
    """sqlite3-based backend with WAL mode + threading.Lock.

    Raises RuntimeError at __init__ if pilot.db does not exist — fail-fast
    prevents accidental empty-DB writes in a misconfigured deployment.
    Run scripts/migrate-jsonl-to-sqlite.py first to create the DB.
    """

    def __init__(self) -> None:
        db = _db_path()
        if not db.exists():
            raise RuntimeError(
                f"SQLite DB missing at {db}; run scripts/migrate-jsonl-to-sqlite.py first"
            )
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.commit()

    def append_pilot(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO pilots
                  (user_id, org_id, name, zalo, business_type, city,
                   industry, source, onboarded_at, pilot_end_at, status, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("org_id", "default"),
                    record.get("name", ""),
                    record.get("zalo", ""),
                    record.get("business_type"),
                    record.get("city"),
                    record.get("industry"),
                    record.get("source"),
                    record.get("onboarded_at", ""),
                    record.get("pilot_end_at", ""),
                    record.get("status", "active"),
                    raw,
                ),
            )
            self._conn.commit()

    def load_pilots(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute("SELECT raw_payload FROM pilots").fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    def append_conversion(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO conversions
                  (user_id, org_id, tier, monthly_vnd, started_at,
                   recorded_at, bank_tx_ref, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("org_id", "default"),
                    record.get("tier", ""),
                    record.get("monthly_vnd", 0),
                    record.get("started_at", ""),
                    record.get("recorded_at", ""),
                    record.get("bank_tx_ref"),
                    raw,
                ),
            )
            self._conn.commit()

    def load_conversions(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute("SELECT raw_payload FROM conversions").fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    def append_response(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO poll_responses
                  (user_id, score, comment, iso_week, recorded_at, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("score", 0),
                    record.get("comment"),
                    record.get("iso_week", ""),
                    record.get("recorded_at", ""),
                    raw,
                ),
            )
            self._conn.commit()

    def load_responses(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute("SELECT raw_payload FROM poll_responses").fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    def append_subscription(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """INSERT OR IGNORE INTO subscriptions
                (user_id, org_id, tier, monthly_vnd, credits, status,
                 started_at, last_paid_at, next_due_at, bank_tx_ref,
                 renewal_count, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("org_id", "default"),
                    record.get("tier", ""),
                    record.get("monthly_vnd", 0),
                    record.get("credits", 0),
                    record.get("status", "active"),
                    record.get("started_at", ""),
                    record.get("last_paid_at", ""),
                    record.get("next_due_at", ""),
                    record.get("bank_tx_ref"),
                    record.get("renewal_count", 0),
                    raw,
                ),
            )
            self._conn.commit()

    def load_subscriptions(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute("SELECT raw_payload FROM subscriptions").fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    def get_credit_balance(self, user_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT balance FROM pilot_credits WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row["balance"]) if row else 0

    def add_credits(self, user_id: str, delta: int) -> int:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO pilot_credits (user_id, balance) VALUES (?, 0)",
                (user_id,),
            )
            self._conn.execute(
                "UPDATE pilot_credits SET balance = MAX(0, balance + ?) WHERE user_id = ?",
                (delta, user_id),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT balance FROM pilot_credits WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row["balance"]) if row else 0
