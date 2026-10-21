# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and operations mixin for RaaS CreditStore."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3

DB_PATH = Path(
    os.environ.get("MEKONG_RAAS_DB")
    or Path.home() / ".mekong" / "raas" / "tenants.db"
)

MISSION_COSTS: dict[str, int] = {"simple": 1, "standard": 3, "complex": 5}


@dataclass
class CreditAccount:
    tenant_id: str
    balance: int
    total_earned: int
    total_spent: int


@dataclass
class CreditTransaction:
    id: str
    tenant_id: str
    amount: int
    reason: str
    timestamp: str
    idempotency_key: str | None = None


class CreditStoreOperationsMixin:
    """Atomic credit mutation and history methods for CreditStore."""

    def add_credits(
        self,
        tenant_id: str,
        amount: int,
        reason: str,
        idempotency_key: str | None = None,
    ) -> int:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        try:
            conn = self._connect()  # type: ignore[attr-defined]
            try:
                conn.execute("BEGIN EXCLUSIVE")
                if idempotency_key is not None:
                    existing = conn.execute(
                        "SELECT id FROM credit_transactions WHERE idempotency_key = ?", (idempotency_key,)
                    ).fetchone()
                    if existing:
                        row = conn.execute(
                            "SELECT balance FROM credit_accounts WHERE tenant_id = ?", (tenant_id,)
                        ).fetchone()
                        conn.execute("COMMIT")
                        return int(row["balance"]) if row else 0

                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE tenant_id = ?", (tenant_id,)
                ).fetchone()
                current = int(row["balance"]) if row else 0
                new_balance = current + amount
                if row:
                    conn.execute(
                        "UPDATE credit_accounts SET balance = ?, total_earned = total_earned + ? WHERE tenant_id = ?",
                        (new_balance, amount, tenant_id),
                    )
                else:
                    conn.execute(
                        "INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent) VALUES (?, ?, ?, 0)",
                        (tenant_id, new_balance, amount),
                    )
                self._record_transaction(conn, tenant_id, amount, reason)  # type: ignore[attr-defined]
                conn.execute("COMMIT")
                return new_balance
            except Exception:
                conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.add_credits failed: {exc}") from exc

    def deduct(
        self,
        tenant_id: str,
        amount: int,
        reason: str,
        idempotency_key: str | None = None,
    ) -> bool:
        if amount <= 0:
            raise ValueError("Deduction amount must be positive")
        try:
            conn = self._connect()  # type: ignore[attr-defined]
            try:
                conn.execute("BEGIN EXCLUSIVE")
                if idempotency_key is not None:
                    existing = conn.execute(
                        "SELECT id FROM credit_transactions WHERE idempotency_key = ?", (idempotency_key,)
                    ).fetchone()
                    if existing is not None:
                        conn.execute("ROLLBACK")
                        return True

                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE tenant_id = ?", (tenant_id,)
                ).fetchone()
                current = int(row["balance"]) if row else 0
                if current < amount:
                    conn.execute("ROLLBACK")
                    return False

                new_balance = current - amount
                if row:
                    conn.execute(
                        "UPDATE credit_accounts SET balance = ?, total_spent = total_spent + ? WHERE tenant_id = ?",
                        (new_balance, amount, tenant_id),
                    )
                else:
                    conn.execute(
                        "INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent) VALUES (?, ?, 0, ?)",
                        (tenant_id, new_balance, amount),
                    )
                self._record_transaction(conn, tenant_id, -amount, reason, idempotency_key)  # type: ignore[attr-defined]
                conn.execute("COMMIT")
                return True
            except sqlite3.Error:
                conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.deduct failed: {exc}") from exc

    def add(self, tenant_id: str, amount: int, reason: str) -> int:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        try:
            with self._connect() as conn:  # type: ignore[attr-defined]
                conn.execute(
                    "INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent) "
                    "VALUES (?, ?, ?, 0) ON CONFLICT(tenant_id) DO UPDATE SET "
                    "balance = balance + excluded.balance, total_earned = total_earned + excluded.total_earned",
                    (tenant_id, amount, amount),
                )
                self._record_transaction(conn, tenant_id, amount, reason)  # type: ignore[attr-defined]
                row = conn.execute(
                    "SELECT balance FROM credit_accounts WHERE tenant_id = ?", (tenant_id,)
                ).fetchone()
                return int(row["balance"])
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.add failed: {exc}") from exc

    def get_history(self, tenant_id: str, limit: int = 50) -> list[CreditTransaction]:
        try:
            with self._connect() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    "SELECT id, tenant_id, amount, reason, timestamp, idempotency_key "
                    "FROM credit_transactions WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (tenant_id, limit),
                ).fetchall()
                return [
                    CreditTransaction(
                        id=r["id"], tenant_id=r["tenant_id"], amount=r["amount"],
                        reason=r["reason"], timestamp=r["timestamp"], idempotency_key=r["idempotency_key"],
                    )
                    for r in rows
                ]
        except sqlite3.Error as exc:
            raise RuntimeError(f"CreditStore.get_history failed: {exc}") from exc
