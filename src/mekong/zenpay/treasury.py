"""Constitutional Treasury — records transactions, checks budgets, reports balances.

Uses the behaviour graph for immutable audit-trail persistence and the
constitution parser for budget limit resolution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import re

import yaml

from src.mekong.constitution.parser import parse_constitution
from src.mekong.graph.store import get_behaviors, open_db, record_behavior
from src.mekong.zenpay.types import BudgetConfig, Transaction, TreasuryBalance

_DEFAULT_DB = ".mekong/graph.db"
_PARTICLES_DIR = ".mekong/particles"


def _resolve_db(db_path: str | None) -> str:
    return db_path or _DEFAULT_DB


def _constitution_limits(particle_id: str) -> dict[str, float]:
    """Extract treasury budget limits from the particle's ZENOS.md constitution."""
    for candidate in [Path(_PARTICLES_DIR) / particle_id / "ZENOS.md", Path("ZENOS.md")]:
        if candidate.exists():
            break
    else:
        return {}
    try:
        constitution = parse_constitution(str(candidate))
    except (ValueError, FileNotFoundError):
        return {}
    limits: dict[str, float] = {}
    for article in constitution.articles:
        if article.category == "economics":
            for line in article.content.lower().split("\n"):
                m = re.search(r"(max\s*per\s*transaction|max\s*approval)\D*(\d+\.?\d*)", line)
                if m:
                    key = "max_per_transaction" if "per" in m.group(1) else "requires_approval_above"
                    limits[key] = max(limits.get(key, 0), float(m.group(2)))
    return limits


def _load_budget_config(particle_id: str) -> BudgetConfig | None:
    path = Path(_PARTICLES_DIR) / particle_id / "cashflow" / "budgets.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    # Merge constitution-based limits (higher of yaml vs constitution wins)
    cl = _constitution_limits(particle_id)
    return BudgetConfig(
        max_monthly_expense=raw.get("max_monthly_expense", 0.0),
        max_per_transaction=max(raw.get("max_per_transaction", 0.0), cl.get("max_per_transaction", 0.0)),
        requires_approval_above=max(
            raw.get("requires_approval_above", 0.0), cl.get("requires_approval_above", 0.0)
        ),
        allowed_categories=raw.get("allowed_categories", []),
    )


def _month_expenses(particle_id: str, db_path: str) -> float:
    conn = open_db(db_path)
    try:
        ms = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                """SELECT COALESCE(SUM(value), 0) FROM behaviors
                   WHERE source_id=? AND action='treasury:expense' AND timestamp>=?""",
                (particle_id, ms.strftime("%Y-%m-%dT%H:%M:%SZ")),
            ).fetchone()
            conn.commit()
            return float(row[0]) if row else 0.0
        except BaseException:
            conn.rollback()
            raise
    finally:
        conn.close()


def _check_limits(
    tx: Transaction,
    cfg: BudgetConfig | None,
    month_total: float,
) -> str:
    if cfg is None:
        return tx.constitutional_review
    status = tx.constitutional_review
    if cfg.max_per_transaction > 0 and tx.amount > cfg.max_per_transaction:
        status = "pending"
    if cfg.max_monthly_expense > 0 and (month_total + abs(tx.amount)) > cfg.max_monthly_expense:
        status = "pending"
    if cfg.requires_approval_above > 0 and tx.amount > cfg.requires_approval_above:
        status = "pending"
    if cfg.allowed_categories and tx.category not in cfg.allowed_categories:
        status = "pending"
    return status


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_transaction(
    tx: Transaction,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Record a treasury transaction with constitutional review.

    1. Load particle budget config, 2. check limits, 3. set review=pending if exceeded,
    4. persist as behaviour graph edge, 5. return ``{transaction_id, behavior_id, review_status}``.
    """
    resolved = _resolve_db(db_path)
    cfg = _load_budget_config(tx.particle_id)
    month_total = _month_expenses(tx.particle_id, resolved) if cfg and cfg.max_monthly_expense > 0 else 0.0
    review_status = _check_limits(tx, cfg, month_total)

    tx_id = tx.id or str(uuid.uuid4())
    conn = open_db(resolved)
    try:
        bid = record_behavior(
            conn=conn, source_id=tx.particle_id, target_id=tx.particle_id,
            action=f"treasury:{tx.tx_type}",
            payload={
                "transaction_id": tx_id, "tx_type": tx.tx_type,
                "amount": tx.amount, "currency": tx.currency,
                "description": tx.description, "category": tx.category,
                "constitutional_review": review_status,
                "counterparty": tx.counterparty, "evidence": tx.evidence,
            },
            value=tx.amount, timestamp=tx.timestamp or None,
        )
    finally:
        conn.close()

    return {"transaction_id": tx_id, "behavior_id": bid, "review_status": review_status}


def get_balance(
    particle_id: str,
    db_path: str | None = None,
) -> TreasuryBalance:
    """Aggregate all treasury behaviours for *particle_id* into a balance."""
    conn = open_db(_resolve_db(db_path))
    try:
        behaviors = get_behaviors(conn=conn, source_id=particle_id, limit=10_000)
    finally:
        conn.close()

    income = expense = 0.0
    count = 0
    for b in behaviors:
        if b.action == "treasury:income":
            income += b.value
            count += 1
        elif b.action == "treasury:expense":
            expense += b.value
            count += 1
        elif b.action == "treasury:transfer":
            count += 1

    return TreasuryBalance(
        particle_id=particle_id,
        total_income=income,
        total_expense=expense,
        net_balance=income - expense,
        transaction_count=count,
    )


def get_history(
    particle_id: str,
    limit: int = 20,
    db_path: str | None = None,
) -> list[Transaction]:
    """Return recent treasury transactions, newest first."""
    conn = open_db(_resolve_db(db_path))
    try:
        behaviors = get_behaviors(conn=conn, source_id=particle_id, limit=limit * 2)
    finally:
        conn.close()

    transactions: list[Transaction] = []
    for b in behaviors:
        if not b.action.startswith("treasury:"):
            continue
        p = b.payload
        tx_type = b.action.split(":", 1)[1]
        transactions.append(
            Transaction(
                id=p.get("transaction_id", str(b.id)),
                particle_id=b.source_id, tx_type=tx_type,
                amount=b.value, currency=p.get("currency", "USD"),
                description=p.get("description", ""),
                category=p.get("category", ""),
                constitutional_review=p.get("constitutional_review", "passed"),
                counterparty=p.get("counterparty"),
                timestamp=b.timestamp, evidence=p.get("evidence"),
            )
        )
        if len(transactions) >= limit:
            break

    return transactions


def check_budget(
    particle_id: str,
    amount: float,
    config: BudgetConfig | None = None,
    db_path: str | None = None,
) -> list[str]:
    """Check *amount* against budget rules and return warnings (empty = all clear)."""
    if config is None:
        config = _load_budget_config(particle_id)
    if config is None:
        return []

    warnings: list[str] = []

    if config.max_per_transaction > 0 and amount > config.max_per_transaction:
        warnings.append(
            f"Amount {amount} exceeds max per-transaction limit {config.max_per_transaction}"
        )

    if config.requires_approval_above > 0 and amount > config.requires_approval_above:
        warnings.append(
            f"Amount {amount} exceeds approval threshold "
            f"{config.requires_approval_above}; review required"
        )

    if config.max_monthly_expense > 0 and amount > 0:
        month_total = _month_expenses(particle_id, _resolve_db(db_path))
        if month_total + amount > config.max_monthly_expense:
            warnings.append(
                f"Adding {amount} would exceed monthly expense limit "
                f"{config.max_monthly_expense} (current: {month_total})"
            )

    return warnings
