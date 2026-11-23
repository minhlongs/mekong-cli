"""Honest usage and economics ledger tracking estimated, reserved, actual, and unknown stages."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.opc.currency_accounting import FxQuote, MultiCurrencyCostSummary, summarize_multicurrency_records
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
        raw_ccy = (record.currency or "").strip()
        stored_ccy = raw_ccy.upper() if (len(raw_ccy) == 3 and raw_ccy.isascii() and raw_ccy.isalpha()) else raw_ccy
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
                        record.amount, stored_ccy, record.payer, record.pricing_source,
                        record.created_at,
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def rebind_run_id(self, source_run_id: str, target_run_id: str) -> int:
        """Re-associate pre-run usage events (e.g., rt_<event_id>) with the minted workflow run_id."""
        with self._get_connection() as conn:
            cur = conn.execute("UPDATE opc_usage_events SET run_id = ? WHERE run_id = ?", (target_run_id, source_run_id))
            return max(0, cur.rowcount)

    def reserve_budget(
        self, event_id: str, run_id: str, max_budget_amount: str, currency: str,
        payer: str, now: int, hard_limit: str | None = None,
    ) -> bool:
        """Atomically reserve budget for an action in an IMMEDIATE transaction."""
        norm_ccy = (currency or "").strip().upper()
        if len(norm_ccy) != 3 or not norm_ccy.isascii() or not norm_ccy.isalpha():
            return False
        try:
            req_amt = Decimal(str(max_budget_amount).strip())
            lim_amt = Decimal(str(hard_limit).strip()) if hard_limit is not None else None
        except Exception:
            return False
        if not req_amt.is_finite() or req_amt < Decimal("0") or (lim_amt is not None and (not lim_amt.is_finite() or lim_amt < Decimal("0"))):
            return False
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if lim_amt is not None:
                    cur = conn.execute(
                        "SELECT amount FROM opc_usage_events WHERE run_id = ? AND UPPER(TRIM(currency)) = ? AND stage IN ('reserved', 'actual')",
                        (run_id, norm_ccy),
                    )
                    spent = sum(Decimal(r["amount"]) for r in cur.fetchall() if r["amount"] is not None)
                    if spent + req_amt > lim_amt:
                        conn.rollback()
                        return False
                conn.execute(
                    "INSERT INTO opc_usage_events (event_id, run_id, attempt, stage, provider, model, tokens, tool_fee, amount, currency, payer, pricing_source, created_at) "
                    "VALUES (?, ?, 1, 'reserved', 'pre_dispatch_guard', 'budget_lock', 0, '0', ?, ?, ?, 'policy_cap', ?)",
                    (event_id, run_id, str(req_amt), norm_ccy, payer, now),
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

    def summarize_currency_aware_costs(
        self, run_id: str, *, target_currency: str | None = None,
        fx_quotes: tuple[FxQuote, ...] | list[FxQuote] | None = None, now: int | None = None,
    ) -> MultiCurrencyCostSummary:
        """Aggregate run costs with strict Decimal currency separation and optional verified FX conversion."""
        return summarize_multicurrency_records(self.get_run_records(run_id), target_currency=target_currency, fx_quotes=fx_quotes, now=now)

    def aggregate_run_costs(self, run_id: str) -> dict[str, Any]:
        """Aggregate costs by currency and stage. Unknown or missing-currency rows are surfaced explicitly."""
        records = self.get_run_records(run_id)
        summary = summarize_multicurrency_records(records)
        known: dict[str, Decimal] = {}
        for bucket in (summary.measured_by_currency, summary.estimated_by_currency):
            for ccy, amt in bucket.items():
                known[ccy] = known.get(ccy, Decimal("0")) + amt
        return {
            "run_id": run_id,
            "total_tokens": sum(r.tokens for r in records if r.tokens),
            "known_amounts": {k: str(v) for k, v in sorted(known.items())},
            "measured_by_currency": {k: str(v) for k, v in sorted(summary.measured_by_currency.items())},
            "estimated_by_currency": {k: str(v) for k, v in sorted(summary.estimated_by_currency.items())},
            "has_unknown_costs": summary.has_unknown_costs or summary.has_missing_currency,
            "has_missing_currency": summary.has_missing_currency,
            "has_mixed_currencies": summary.has_mixed_currencies,
            "accounting_status": summary.status,
            "event_count": len(records),
        }

    def summarize_cost_accounting(self, run_id: str) -> CostAccounting:
        """Build CostAccounting without mixing currencies or fabricating 0.0 when cost/currency is missing."""
        records = self.get_run_records(run_id)
        summary = summarize_multicurrency_records(records)
        m_tok = sum(r.tokens for r in records if r.stage == UsageStage.ACTUAL and r.tokens is not None)
        e_tok = sum(r.tokens for r in records if r.stage != UsageStage.ACTUAL and r.tokens is not None)
        has_m_tok = any(r.stage == UsageStage.ACTUAL and r.tokens is not None for r in records)
        has_e_tok = any(r.stage != UsageStage.ACTUAL and r.tokens is not None for r in records)
        clean = not summary.has_unknown_costs and not summary.has_missing_currency and not summary.has_mixed_currencies
        act_scalar = float(next(iter(summary.measured_by_currency.values()))) if (clean and len(summary.measured_by_currency) == 1) else None
        est_scalar = float(next(iter(summary.estimated_by_currency.values()))) if (clean and len(summary.estimated_by_currency) == 1) else None
        return CostAccounting.build(
            measured_tokens=m_tok if has_m_tok else None,
            estimated_tokens=e_tok if has_e_tok else None,
            actual_cost=act_scalar,
            estimated_cost=est_scalar,
        )
