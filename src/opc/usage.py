"""Honest usage and economics ledger tracking estimated, reserved, actual, and unknown stages."""
from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.opc.models import UsageRecord, UsageStage


class UsageLedger:
    """Truthful cost tracking ledger. Never coerces unknown costs to zero."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opc_usage_events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens INTEGER,
                    tool_fee TEXT,
                    amount TEXT,
                    currency TEXT NOT NULL,
                    payer TEXT NOT NULL,
                    pricing_source TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )

    def record_usage(self, record: UsageRecord) -> bool:
        """Insert a usage record. Returns False if event_id already exists (idempotent)."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO opc_usage_events (
                        event_id, run_id, attempt, stage, provider, model,
                        tokens, tool_fee, amount, currency, payer, pricing_source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.event_id, record.run_id, record.attempt, record.stage.value,
                        record.provider, record.model, record.tokens, record.tool_fee,
                        record.amount, record.currency, record.payer, record.pricing_source,
                        record.created_at,
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def reserve_budget(
        self, event_id: str, run_id: str, max_budget_amount: str, currency: str,
        payer: str, now: int, hard_limit: str | None = None,
    ) -> bool:
        """Atomically reserve budget for an action in an IMMEDIATE transaction."""
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if hard_limit is not None:
                    cur = conn.execute(
                        "SELECT amount FROM opc_usage_events WHERE run_id = ? AND stage IN ('reserved', 'actual')",
                        (run_id,),
                    )
                    spent = sum(Decimal(r["amount"]) for r in cur.fetchall() if r["amount"] is not None)
                    if spent + Decimal(max_budget_amount) > Decimal(hard_limit):
                        conn.rollback()
                        return False
                conn.execute(
                    """
                    INSERT INTO opc_usage_events (
                        event_id, run_id, attempt, stage, provider, model,
                        tokens, tool_fee, amount, currency, payer, pricing_source, created_at
                    ) VALUES (?, ?, 1, 'reserved', 'pre_dispatch_guard', 'budget_lock', 0, '0', ?, ?, ?, 'policy_cap', ?)
                    """,
                    (event_id, run_id, max_budget_amount, currency, payer, now),
                )
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def get_run_records(self, run_id: str) -> list[UsageRecord]:
        """Fetch all usage records for a run."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM opc_usage_events WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
            return [
                UsageRecord(
                    event_id=row["event_id"], run_id=row["run_id"], attempt=row["attempt"],
                    stage=UsageStage(row["stage"]), provider=row["provider"], model=row["model"],
                    tokens=row["tokens"], tool_fee=row["tool_fee"], amount=row["amount"],
                    currency=row["currency"], payer=row["payer"], pricing_source=row["pricing_source"],
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def aggregate_run_costs(self, run_id: str) -> dict[str, Any]:
        """Aggregate costs by stage. Unknown costs explicitly surfaced, never defaulted to zero."""
        records = self.get_run_records(run_id)
        totals: dict[str, Decimal] = {}
        has_unknown = False
        total_tokens = 0

        for r in records:
            if r.tokens:
                total_tokens += r.tokens
            if r.stage == UsageStage.UNKNOWN or r.amount is None:
                has_unknown = True
                continue
            curr = r.currency
            amt = Decimal(r.amount)
            totals[curr] = totals.get(curr, Decimal("0.0")) + amt

        return {
            "run_id": run_id,
            "total_tokens": total_tokens,
            "known_amounts": {k: str(v) for k, v in totals.items()},
            "has_unknown_costs": has_unknown,
            "event_count": len(records),
        }
