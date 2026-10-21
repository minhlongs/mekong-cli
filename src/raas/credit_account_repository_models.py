# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and ledger operations mixin for CreditAccountRepository."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import uuid

_DB_PATH = Path.home() / ".mekong" / "raas" / "workspaces.db"

_DDL = """
CREATE TABLE IF NOT EXISTS credit_accounts (
    workspace_id  TEXT PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    balance       INTEGER NOT NULL DEFAULT 0,
    total_earned  INTEGER NOT NULL DEFAULT 0,
    total_spent   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS credit_transactions (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    amount       INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    metadata     TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS processed_events (
    event_id     TEXT PRIMARY KEY,
    event_type   TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    processed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_workspace ON credit_transactions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_workspace ON processed_events(workspace_id);
"""


@dataclass
class CreditAccount:
    workspace_id: str
    balance: int
    total_earned: int
    total_spent: int
    created_at: str = ""
    updated_at: str = ""


@dataclass
class CreditTransaction:
    id: str
    workspace_id: str
    amount: int
    reason: str
    timestamp: str
    metadata: str = "{}"


class CreditAccountLedgerMixin:
    """Ledger mutation and event idempotency methods for CreditAccountRepository."""

    def add_credits(
        self, workspace_id: str, amount: int, reason: str, metadata: dict | None = None
    ) -> int:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        now = self._now_iso()  # type: ignore[attr-defined]
        meta_json = str(metadata or {}).replace("'", '"')
        try:
            with self._connect() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    "INSERT INTO credit_accounts (workspace_id, balance, total_earned, total_spent, created_at, updated_at) "
                    "VALUES (?, ?, ?, 0, ?, ?) ON CONFLICT(workspace_id) DO UPDATE SET "
                    "balance = balance + excluded.balance, total_earned = total_earned + excluded.total_earned, updated_at = excluded.updated_at",
                    (workspace_id, amount, amount, now, now),
                )
                conn.execute(
                    "INSERT INTO credit_transactions (id, workspace_id, amount, reason, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), workspace_id, amount, reason, now, meta_json),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE workspace_id = ?", (workspace_id,)
                ).fetchone()
                return int(row["balance"])
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to add credits: {exc}") from exc

    def deduct_credits(
        self, workspace_id: str, amount: int, reason: str, metadata: dict | None = None
    ) -> bool:
        if amount <= 0:
            raise ValueError("Deduction amount must be positive")
        now = self._now_iso()  # type: ignore[attr-defined]
        meta_json = str(metadata or {}).replace("'", '"')
        try:
            conn = self._connect()  # type: ignore[attr-defined]
            try:
                conn.execute("BEGIN EXCLUSIVE")
                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE workspace_id = ?", (workspace_id,)
                ).fetchone()
                current = int(row["balance"]) if row else 0
                if current < amount:
                    conn.execute("ROLLBACK")
                    return False

                conn.execute(
                    "UPDATE credit_accounts SET balance = ?, total_spent = total_spent + ?, updated_at = ? WHERE workspace_id = ?",
                    (current - amount, amount, now, workspace_id),
                )
                conn.execute(
                    "INSERT INTO credit_transactions (id, workspace_id, amount, reason, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), workspace_id, -amount, reason, now, meta_json),
                )
                conn.execute("COMMIT")
                return True
            except sqlite3.Error:
                conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to deduct credits: {exc}") from exc

    def get_history(self, workspace_id: str, limit: int = 50) -> list[CreditTransaction]:
        try:
            with self._connect() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    "SELECT id, workspace_id, amount, reason, timestamp, metadata "
                    "FROM credit_transactions WHERE workspace_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (workspace_id, limit),
                ).fetchall()
                return [
                    CreditTransaction(
                        id=r["id"], workspace_id=r["workspace_id"], amount=r["amount"],
                        reason=r["reason"], timestamp=r["timestamp"], metadata=r["metadata"] or "{}",
                    )
                    for r in rows
                ]
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to get history: {exc}") from exc
