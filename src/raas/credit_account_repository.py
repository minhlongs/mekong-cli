# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credit account repository for workspace-level billing (SQLite version)."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Optional

from src.raas.credit_account_repository_models import (
    _DB_PATH,
    _DDL,
    CreditAccount,
    CreditAccountLedgerMixin,
    CreditTransaction,
)

logger = logging.getLogger(__name__)


class CreditAccountRepository(CreditAccountLedgerMixin):
    """SQLite repository for workspace credit accounts."""

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Open WAL-mode connection."""
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        try:
            with self._connect() as conn:
                conn.executescript(_DDL)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialize credit DB: {exc}") from exc

    @staticmethod
    def _now_iso() -> str:
        """Return current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def create_account(self, workspace_id: str) -> CreditAccount:
        """Create a new credit account for a workspace."""
        now = self._now_iso()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO credit_accounts (workspace_id, balance, total_earned, total_spent, created_at, updated_at)
                    VALUES (?, 0, 0, 0, ?, ?)
                    ON CONFLICT(workspace_id) DO NOTHING
                    """,
                    (workspace_id, now, now),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to create credit account: {exc}") from exc

        return CreditAccount(
            workspace_id=workspace_id,
            balance=0,
            total_earned=0,
            total_spent=0,
            created_at=now,
            updated_at=now,
        )

    def get_balance(self, workspace_id: str) -> int:
        """Return the current credit balance for a workspace."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE workspace_id = ?",
                    (workspace_id,),
                ).fetchone()
                return int(row["balance"]) if row else 0
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to get balance: {exc}") from exc

    def get_account(self, workspace_id: str) -> Optional[CreditAccount]:
        """Get full account details for a workspace."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM credit_accounts WHERE workspace_id = ?",
                    (workspace_id,),
                ).fetchone()
                if not row:
                    return None
                return CreditAccount(
                    workspace_id=row["workspace_id"],
                    balance=int(row["balance"]),
                    total_earned=int(row["total_earned"]),
                    total_spent=int(row["total_spent"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to get account: {exc}") from exc

    def mark_event_processed(
        self, event_id: str, event_type: str, workspace_id: str
    ) -> bool:
        """Mark a webhook event as processed for idempotency."""
        now = self._now_iso()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO processed_events (event_id, event_type, workspace_id, processed_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (event_id, event_type, workspace_id, now),
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def is_event_processed(self, event_id: str) -> bool:
        """Check if an event has already been processed."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM processed_events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
                return row is not None
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to check event: {exc}") from exc


__all__ = [
    "CreditAccount",
    "CreditAccountRepository",
    "CreditTransaction",
    "_DB_PATH",
]
