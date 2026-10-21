# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credit system for RaaS tenant billing.

Manages credit balances and transactions using SQLite with
atomic operations to prevent race conditions.
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import uuid

from src.raas.credits_models import (
    DB_PATH,
    MISSION_COSTS,
    CreditAccount,
    CreditStoreOperationsMixin,
    CreditTransaction,
)


class CreditStore(CreditStoreOperationsMixin):
    """SQLite-backed credit store with atomic operations.

    Uses WAL mode and EXCLUSIVE transactions to ensure balance
    consistency under concurrent access.
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        """Initialize the store, creating DB directory and tables if needed."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Return a configured SQLite connection with WAL mode and busy timeout."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they do not already exist."""
        try:
            with self._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS credit_accounts (
                        tenant_id TEXT PRIMARY KEY,
                        balance INTEGER NOT NULL DEFAULT 0,
                        total_earned INTEGER NOT NULL DEFAULT 0,
                        total_spent INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        reason TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        idempotency_key TEXT
                    );
                    """
                )
                try:
                    conn.execute(
                        "ALTER TABLE credit_transactions ADD COLUMN idempotency_key TEXT"
                    )
                except sqlite3.OperationalError:
                    pass
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "idx_credit_transactions_idempotency_key "
                    "ON credit_transactions(idempotency_key) "
                    "WHERE idempotency_key IS NOT NULL"
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore: failed to initialize DB: {exc}") from exc

    @staticmethod
    def _now_iso() -> str:
        """Return current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def _record_transaction(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        amount: int,
        reason: str,
        idempotency_key: str | None = None,
    ) -> None:
        """Insert a transaction row (must be called within an open connection)."""
        conn.execute(
            "INSERT INTO credit_transactions "
            "(id, tenant_id, amount, reason, timestamp, idempotency_key) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                tenant_id,
                amount,
                reason,
                self._now_iso(),
                idempotency_key,
            ),
        )

    def get_balance(self, tenant_id: str) -> int:
        """Return the current credit balance for a tenant (0 if no account)."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE tenant_id = ?",
                    (tenant_id,),
                ).fetchone()
                return int(row["balance"]) if row else 0
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.get_balance failed: {exc}") from exc

    def get_transaction(self, idempotency_key: str) -> CreditTransaction | None:
        """Return the transaction for a given idempotency key, or None."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT id, tenant_id, amount, reason, timestamp, idempotency_key "
                    "FROM credit_transactions WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if row is None:
                    return None
                return CreditTransaction(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    amount=row["amount"],
                    reason=row["reason"],
                    timestamp=row["timestamp"],
                    idempotency_key=row["idempotency_key"],
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.get_transaction failed: {exc}") from exc


__all__ = [
    "CreditAccount",
    "CreditStore",
    "CreditTransaction",
    "DB_PATH",
    "MISSION_COSTS",
]
