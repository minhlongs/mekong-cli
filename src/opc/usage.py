"""Honest usage and economics ledger tracking estimated, reserved, actual, and unknown stages."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.opc.models import CostAccounting, UsageRecord, UsageStage
from src.opc.quota import QuotaReservationResult, WorkflowQuotaGuard


class UsageLedger:
    """Truthful cost tracking ledger. Never coerces unknown costs to zero."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.quota_guard = WorkflowQuotaGuard(self.db_path)

    def reserve_workflow_quota(
        self, tenant_id: str, workflow_id: str, period_ym: str, now: int,
        limit_override: int | None = None, tier: str = "pilot_a",
    ) -> QuotaReservationResult:
        return self.quota_guard.reserve_workflow_slot(tenant_id, workflow_id, period_ym, now, limit_override, tier)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS opc_usage_events ("
                "event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, attempt INTEGER NOT NULL, "
                "stage TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, tokens INTEGER, "
                "tool_fee TEXT, amount TEXT, currency TEXT NOT NULL, payer TEXT NOT NULL, "
                "pricing_source TEXT NOT NULL, created_at INTEGER NOT NULL);"
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
            totals[curr] = totals.get(curr, Decimal("0.0")) + Decimal(r.amount)
        return {
            "run_id": run_id, "total_tokens": total_tokens,
            "known_amounts": {k: str(v) for k, v in totals.items()},
            "has_unknown_costs": has_unknown, "event_count": len(records),
        }

    def summarize_cost_accounting(self, run_id: str) -> CostAccounting:
        """Build CostAccounting for run_id without fabricating 0.0 when cost is unknown."""
        records = self.get_run_records(run_id)
        m_tok, e_tok, has_m_tok, has_e_tok = 0, 0, False, False
        act_sum, est_sum, has_act, has_est, has_unk = Decimal("0"), Decimal("0"), False, False, False
        for r in records:
            if r.stage == UsageStage.ACTUAL:
                if r.tokens is not None:
                    m_tok, has_m_tok = m_tok + r.tokens, True
                if r.amount is not None:
                    act_sum, has_act = act_sum + Decimal(r.amount), True
                else:
                    has_unk = True
            elif r.stage in (UsageStage.ESTIMATED, UsageStage.RESERVED):
                if r.tokens is not None:
                    e_tok, has_e_tok = e_tok + r.tokens, True
                if r.amount is not None:
                    est_sum, has_est = est_sum + Decimal(r.amount), True
            elif r.stage == UsageStage.UNKNOWN:
                has_unk = True
                if r.tokens is not None:
                    e_tok, has_e_tok = e_tok + r.tokens, True
        return CostAccounting.build(
            measured_tokens=m_tok if has_m_tok else None,
            estimated_tokens=e_tok if has_e_tok else None,
            actual_cost=float(act_sum) if (has_act and not has_unk) else None,
            estimated_cost=float(est_sum) if (has_est and not has_unk) else None,
        )
