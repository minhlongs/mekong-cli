"""Atomic SQLite WAL monthly workflow quota guard for VN SME outcome-priced tiers."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

VN_SME_TIER_WORKFLOW_QUOTAS: dict[str, int] = {
    "starter": 300,
    "pilot_a": 500,
    "growth": 1_500,
    "agency": 5_000,
}


class WorkflowQuotaExceededError(PermissionError):
    """Raised when a tenant exhausts its monthly verified workflow quota."""


@dataclass(frozen=True)
class QuotaReservationResult:
    """Outcome of an atomic SQLite WAL workflow quota reservation."""
    allowed: bool
    tenant_id: str
    period_ym: str
    workflow_id: str
    used_count: int
    limit_count: int
    deduplicated: bool = False


class WorkflowQuotaGuard:
    """Atomic BEGIN IMMEDIATE SQLite WAL workflow-count quota ledger (0% TOCTOU overrun)."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opc_workflow_quota_reservations (
                    tenant_id TEXT NOT NULL,
                    period_ym TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (tenant_id, period_ym, workflow_id)
                );
                """
            )

    def reserve_workflow_slot(
        self,
        tenant_id: str,
        workflow_id: str,
        period_ym: str,
        now: int,
        limit_override: int | None = None,
        tier: str = "pilot_a",
    ) -> QuotaReservationResult:
        """Atomically reserve 1 workflow slot under BEGIN IMMEDIATE lock."""
        norm_tier = tier.strip().lower()
        max_slots = int(limit_override) if limit_override is not None else VN_SME_TIER_WORKFLOW_QUOTAS.get(norm_tier, 500)
        clean_tenant = tenant_id.strip()
        clean_wf = workflow_id.strip()
        clean_ym = period_ym.strip()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    """
                    SELECT 1 FROM opc_workflow_quota_reservations
                    WHERE tenant_id = ? AND period_ym = ? AND workflow_id = ?
                    """,
                    (clean_tenant, clean_ym, clean_wf),
                ).fetchone()
                cur_count = int(
                    conn.execute(
                        "SELECT COUNT(*) FROM opc_workflow_quota_reservations WHERE tenant_id = ? AND period_ym = ?",
                        (clean_tenant, clean_ym),
                    ).fetchone()[0]
                )
                if existing is not None:
                    conn.execute("COMMIT")
                    return QuotaReservationResult(True, clean_tenant, clean_ym, clean_wf, cur_count, max_slots, True)
                if cur_count >= max_slots:
                    conn.execute("ROLLBACK")
                    return QuotaReservationResult(False, clean_tenant, clean_ym, clean_wf, cur_count, max_slots, False)
                conn.execute(
                    """
                    INSERT INTO opc_workflow_quota_reservations (tenant_id, period_ym, workflow_id, tier, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (clean_tenant, clean_ym, clean_wf, norm_tier, int(now)),
                )
                conn.execute("COMMIT")
                return QuotaReservationResult(True, clean_tenant, clean_ym, clean_wf, cur_count + 1, max_slots, False)
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def release_workflow_slot(self, tenant_id: str, workflow_id: str, period_ym: str) -> bool:
        """Release a reserved slot on cancellation/timeout before external side effects."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """
                DELETE FROM opc_workflow_quota_reservations
                WHERE tenant_id = ? AND period_ym = ? AND workflow_id = ?
                """,
                (tenant_id.strip(), period_ym.strip(), workflow_id.strip()),
            )
            conn.execute("COMMIT")
            return cur.rowcount > 0

    def get_period_usage(self, tenant_id: str, period_ym: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM opc_workflow_quota_reservations WHERE tenant_id = ? AND period_ym = ?",
                (tenant_id.strip(), period_ym.strip()),
            ).fetchone()
            return int(row[0]) if row else 0
