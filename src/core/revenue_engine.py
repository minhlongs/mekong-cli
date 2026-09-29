# Mekong CLI — Pure Standard-Library Revenue Operations Engine
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Revenue operations and financial intelligence engine for Mekong CLI.

Provides MRR/ARR waterfall metrics, multi-tier subscription lifecycle tracking,
transaction ledger recording, payment reconciliation, and multi-scenario forecasting.
Enforces strict standard-library-only execution with zero vendor SDKs.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

USD_TO_VND_RATE = 25400

TIER_CATALOG: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price_usd": 0.0,
        "price_vnd": 0,
        "credits": 50,
        "description": "Exploration & basic CLI tools",
    },
    "starter": {
        "name": "Starter",
        "price_usd": 49.0,
        "price_vnd": 1244600,
        "credits": 300,
        "description": "Solo founder / single agent workflow",
    },
    "growth": {
        "name": "Growth",
        "price_usd": 149.0,
        "price_vnd": 3784600,
        "credits": 1200,
        "description": "High-velocity team / multi-agent pipelines",
    },
    "scale": {
        "name": "Scale",
        "price_usd": 299.0,
        "price_vnd": 7594600,
        "credits": 3500,
        "description": "High-throughput autonomous swarm execution",
    },
    "pro": {
        "name": "Pro",
        "price_usd": 499.0,
        "price_vnd": 12674600,
        "credits": 7000,
        "description": "Full agency OS & unlimited background daemons",
    },
    "enterprise": {
        "name": "Enterprise",
        "price_usd": 999.0,
        "price_vnd": 25374600,
        "credits": 15000,
        "description": "Custom SLAs, dedicated on-prem & hybrid compute",
    },
}


class RevenueEngine:
    """Core Revenue Operations & Financial Intelligence Engine."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            base_dir = Path.cwd() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "revenue.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT,
                    amount REAL NOT NULL,
                    amount_usd REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    tier TEXT DEFAULT 'starter',
                    type TEXT DEFAULT 'subscription',
                    gateway TEXT DEFAULT 'stripe',
                    status TEXT DEFAULT 'succeeded',
                    created_at TEXT NOT NULL,
                    notes TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT,
                    tier TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    billing_cycle TEXT DEFAULT 'monthly',
                    status TEXT DEFAULT 'active',
                    started_at TEXT NOT NULL,
                    renewed_at TEXT,
                    cancelled_at TEXT,
                    notes TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reconciliations (
                    id TEXT PRIMARY KEY,
                    period TEXT NOT NULL,
                    total_expected REAL NOT NULL,
                    total_collected REAL NOT NULL,
                    discrepancy REAL NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    @staticmethod
    def get_tier_catalog(currency: str = "USD") -> Dict[str, Any]:
        """Return subscription tiers with pricing in USD or VND."""
        curr = currency.upper()
        catalog: Dict[str, Any] = {}
        for tier_key, info in TIER_CATALOG.items():
            if curr == "VND":
                price_str = f"{info['price_vnd']:,} VND"
                display_price = info["price_vnd"]
            else:
                price_str = f"${info['price_usd']:,.2f}"
                display_price = info["price_usd"]
            catalog[tier_key] = {
                "tier": tier_key,
                "name": info["name"],
                "price": display_price,
                "currency": curr,
                "price_formatted": price_str,
                "credits": info["credits"],
                "description": info["description"],
            }
        return catalog

    def record_transaction(
        self,
        customer_id: str,
        amount: float,
        customer_name: str = "",
        currency: str = "USD",
        tier: str = "starter",
        type: str = "subscription",
        gateway: str = "stripe",
        status: str = "succeeded",
        notes: str = "",
        auto_subscription: bool = True,
    ) -> Dict[str, Any]:
        """Record a transaction in the revenue ledger."""
        curr = currency.upper()
        if curr == "VND":
            amount_usd = round(amount / USD_TO_VND_RATE, 2)
        else:
            amount_usd = round(float(amount), 2)

        txn_id = f"txn_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        name = customer_name.strip() or f"Customer-{customer_id}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    id, customer_id, customer_name, amount, amount_usd,
                    currency, tier, type, gateway, status, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    txn_id,
                    customer_id,
                    name,
                    amount,
                    amount_usd,
                    curr,
                    tier,
                    type,
                    gateway,
                    status,
                    now,
                    notes,
                ),
            )
            conn.commit()

        # If it is a succeeded subscription transaction, optionally update or create subscription
        sub_id = None
        if auto_subscription and type == "subscription" and status == "succeeded":
            sub_res = self.create_or_renew_subscription(
                customer_id=customer_id,
                tier=tier,
                amount_usd=amount_usd,
                customer_name=name,
            )
            sub_id = sub_res.get("id")

        return {
            "id": txn_id,
            "customer_id": customer_id,
            "customer_name": name,
            "amount": amount,
            "amount_usd": amount_usd,
            "currency": curr,
            "tier": tier,
            "type": type,
            "gateway": gateway,
            "status": status,
            "created_at": now,
            "notes": notes,
            "subscription_id": sub_id,
        }

    def create_or_renew_subscription(
        self,
        customer_id: str,
        tier: str,
        amount_usd: Optional[float] = None,
        customer_name: str = "",
        billing_cycle: str = "monthly",
    ) -> Dict[str, Any]:
        """Create or update an active customer subscription."""
        if amount_usd is None:
            tier_info = TIER_CATALOG.get(tier.lower(), {})
            amount_usd = float(tier_info.get("price_usd", 49.0))

        now = datetime.now(timezone.utc).isoformat()
        name = customer_name.strip() or f"Customer-{customer_id}"

        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT id FROM subscriptions WHERE customer_id = ? AND status = 'active'",
                (customer_id,),
            )
            existing = cur.fetchone()
            if existing:
                sub_id = existing["id"]
                conn.execute(
                    """
                    UPDATE subscriptions
                    SET tier = ?, amount_usd = ?, renewed_at = ?, notes = ?
                    WHERE id = ?
                    """,
                    (tier, amount_usd, now, f"Renewed on {now}", sub_id),
                )
                conn.commit()
                return {
                    "id": sub_id,
                    "customer_id": customer_id,
                    "customer_name": name,
                    "tier": tier,
                    "amount_usd": amount_usd,
                    "status": "active",
                    "action": "renewed",
                    "renewed_at": now,
                }
            else:
                sub_id = f"sub_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO subscriptions (
                        id, customer_id, customer_name, tier, amount_usd,
                        billing_cycle, status, started_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    """,
                    (
                        sub_id,
                        customer_id,
                        name,
                        tier,
                        amount_usd,
                        billing_cycle,
                        now,
                        "Initial subscription creation",
                    ),
                )
                conn.commit()
                return {
                    "id": sub_id,
                    "customer_id": customer_id,
                    "customer_name": name,
                    "tier": tier,
                    "amount_usd": amount_usd,
                    "status": "active",
                    "action": "created",
                    "started_at": now,
                }

    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "Customer requested cancellation",
    ) -> Dict[str, Any]:
        """Cancel an active subscription."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM subscriptions WHERE id = ? OR customer_id = ?",
                (subscription_id, subscription_id),
            )
            row = cur.fetchone()
            if not row:
                return {
                    "success": False,
                    "error": f"Subscription {subscription_id} not found",
                }

            real_id = row["id"]
            conn.execute(
                """
                UPDATE subscriptions
                SET status = 'cancelled', cancelled_at = ?, notes = ?
                WHERE id = ?
                """,
                (now, reason, real_id),
            )
            conn.commit()

        return {
            "success": True,
            "id": real_id,
            "customer_id": row["customer_id"],
            "status": "cancelled",
            "cancelled_at": now,
            "reason": reason,
        }

    def list_subscriptions(
        self, status: str = "all"
    ) -> List[Dict[str, Any]]:
        """List subscriptions filtered by status."""
        query = "SELECT * FROM subscriptions"
        params: List[Any] = []
        if status.lower() != "all":
            query += " WHERE status = ?"
            params.append(status.lower())
        query += " ORDER BY started_at DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def list_transactions(
        self,
        customer_id: str = "",
        status: str = "all",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List recorded transactions in reverse chronological order."""
        conditions = []
        params: List[Any] = []
        if customer_id.strip():
            conditions.append("customer_id = ?")
            params.append(customer_id.strip())
        if status.lower() != "all":
            conditions.append("status = ?")
            params.append(status.lower())

        query = "SELECT * FROM transactions"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def get_metrics(self, period: str = "month") -> Dict[str, Any]:
        """Compute MRR, ARR, ARPU, LTV, MRR waterfall, and retention metrics."""
        with self._get_connection() as conn:
            # Active subscriptions
            sub_cur = conn.execute(
                "SELECT * FROM subscriptions WHERE status = 'active'"
            )
            active_subs = [dict(r) for r in sub_cur.fetchall()]

            # Cancelled subscriptions
            can_cur = conn.execute(
                "SELECT * FROM subscriptions WHERE status = 'cancelled'"
            )
            cancelled_subs = [dict(r) for r in can_cur.fetchall()]

            # All succeeded transactions
            txn_cur = conn.execute(
                "SELECT * FROM transactions WHERE status = 'succeeded'"
            )
            succeeded_txns = [dict(r) for r in txn_cur.fetchall()]

        # MRR calculation: sum amount_usd for active monthly subscriptions
        mrr = 0.0
        tier_breakdown: Dict[str, Dict[str, Any]] = {}
        for s in active_subs:
            amt = float(s["amount_usd"])
            if s.get("billing_cycle") == "annual":
                amt = round(amt / 12, 2)
            mrr += amt
            tier = s.get("tier", "unknown")
            if tier not in tier_breakdown:
                tier_breakdown[tier] = {"count": 0, "mrr": 0.0}
            tier_breakdown[tier]["count"] += 1
            tier_breakdown[tier]["mrr"] = round(
                tier_breakdown[tier]["mrr"] + amt, 2
            )

        mrr = round(mrr, 2)
        arr = round(mrr * 12, 2)

        # Total historical revenue
        total_revenue = round(
            sum(float(t["amount_usd"]) for t in succeeded_txns), 2
        )

        # Gateways breakdown
        gateway_breakdown: Dict[str, float] = {}
        for t in succeeded_txns:
            gw = t.get("gateway", "other")
            gateway_breakdown[gw] = round(
                gateway_breakdown.get(gw, 0.0) + float(t["amount_usd"]), 2
            )

        # Customer counts & ARPU
        paying_customers = len(set(s["customer_id"] for s in active_subs))
        arpu = round(mrr / paying_customers, 2) if paying_customers > 0 else 0.0

        # Churn rate calculation
        total_ever_subs = len(active_subs) + len(cancelled_subs)
        churn_rate_pct = (
            round((len(cancelled_subs) / total_ever_subs) * 100, 2)
            if total_ever_subs > 0
            else 0.0
        )

        # LTV calculation
        if churn_rate_pct > 0:
            ltv = round(arpu / (churn_rate_pct / 100), 2)
        else:
            ltv = round(arpu * 24, 2)  # 24-month horizon benchmark

        # MRR Waterfall calculation
        # New MRR: active subscriptions created recently
        new_mrr = round(sum(float(s["amount_usd"]) for s in active_subs), 2)
        churned_mrr = round(
            sum(float(s["amount_usd"]) for s in cancelled_subs), 2
        )
        expansion_mrr = 0.0
        for t in succeeded_txns:
            if t.get("type") in ("addon", "upgrade"):
                expansion_mrr += float(t["amount_usd"])
        expansion_mrr = round(expansion_mrr, 2)
        contraction_mrr = 0.0

        net_new_mrr = round(
            new_mrr + expansion_mrr - contraction_mrr - churned_mrr, 2
        )

        # Net Revenue Retention (NRR) estimate
        if new_mrr > 0:
            nrr_pct = round(
                ((new_mrr + expansion_mrr - churned_mrr) / new_mrr) * 100, 1
            )
        else:
            nrr_pct = 100.0

        return {
            "period": period,
            "currency": "USD",
            "mrr": mrr,
            "arr": arr,
            "total_revenue": total_revenue,
            "active_subscriptions": len(active_subs),
            "paying_customers": paying_customers,
            "arpu": arpu,
            "churn_rate_pct": churn_rate_pct,
            "ltv": ltv,
            "nrr_pct": nrr_pct,
            "mrr_waterfall": {
                "new_mrr": new_mrr,
                "expansion_mrr": expansion_mrr,
                "contraction_mrr": contraction_mrr,
                "churned_mrr": churned_mrr,
                "net_new_mrr": net_new_mrr,
            },
            "tier_breakdown": tier_breakdown,
            "gateway_breakdown": gateway_breakdown,
        }

    def reconcile_payments(self, auto_fix: bool = False) -> Dict[str, Any]:
        """Reconcile active subscriptions against collected transactions."""
        with self._get_connection() as conn:
            sub_cur = conn.execute(
                "SELECT * FROM subscriptions WHERE status = 'active'"
            )
            active_subs = [dict(r) for r in sub_cur.fetchall()]

            txn_cur = conn.execute(
                "SELECT * FROM transactions WHERE status = 'succeeded'"
            )
            succeeded_txns = [dict(r) for r in txn_cur.fetchall()]

        customer_txns: Dict[str, List[Dict[str, Any]]] = {}
        for t in succeeded_txns:
            cid = t["customer_id"]
            if cid not in customer_txns:
                customer_txns[cid] = []
            customer_txns[cid].append(t)

        discrepancies: List[Dict[str, Any]] = []
        total_expected = 0.0
        total_collected = 0.0

        for s in active_subs:
            cid = s["customer_id"]
            expected = float(s["amount_usd"])
            total_expected += expected

            txns = customer_txns.get(cid, [])
            collected = sum(float(t["amount_usd"]) for t in txns)
            total_collected += collected

            if not txns:
                discrepancy = {
                    "type": "unpaid_subscription",
                    "customer_id": cid,
                    "subscription_id": s["id"],
                    "expected": expected,
                    "collected": 0.0,
                    "difference": expected,
                    "message": f"Active subscription for {cid} has no recorded succeeded transactions",
                }
                discrepancies.append(discrepancy)
                if auto_fix:
                    # Update status to past_due
                    with self._get_connection() as conn:
                        conn.execute(
                            "UPDATE subscriptions SET status = 'past_due', notes = 'Auto-reconciliation flagged past_due' WHERE id = ?",
                            (s["id"],),
                        )
                        conn.commit()

        status = "reconciled" if not discrepancies else "discrepancy_detected"
        period_str = datetime.now(timezone.utc).strftime("%Y-%m")
        rec_id = f"rec_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        report = {
            "id": rec_id,
            "period": period_str,
            "status": status,
            "total_expected": round(total_expected, 2),
            "total_collected": round(total_collected, 2),
            "net_discrepancy": round(total_expected - total_collected, 2),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "auto_fix_applied": auto_fix,
            "timestamp": now,
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reconciliations (
                    id, period, total_expected, total_collected, discrepancy,
                    status, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    period_str,
                    round(total_expected, 2),
                    round(total_collected, 2),
                    round(total_expected - total_collected, 2),
                    status,
                    json.dumps(report),
                    now,
                ),
            )
            conn.commit()

        return report

    def forecast_revenue(
        self, months: int = 6, scenario: str = "base"
    ) -> Dict[str, Any]:
        """Project future MRR, ARR, and cumulative revenue over N months."""
        metrics = self.get_metrics()
        current_mrr = metrics["mrr"]
        if current_mrr <= 0:
            # Baseline benchmark if ledger is new
            current_mrr = 1500.0

        scenario_clean = scenario.lower().strip()
        if scenario_clean == "conservative":
            monthly_growth = 0.02
            monthly_churn = 0.04
        elif scenario_clean == "aggressive":
            monthly_growth = 0.18
            monthly_churn = 0.01
        else:
            scenario_clean = "base"
            monthly_growth = 0.08
            monthly_churn = 0.02

        net_growth_rate = monthly_growth - monthly_churn

        projections: List[Dict[str, Any]] = []
        projected_mrr = current_mrr
        cumulative_revenue = 0.0

        for m in range(1, months + 1):
            projected_mrr = round(projected_mrr * (1.0 + net_growth_rate), 2)
            projected_arr = round(projected_mrr * 12, 2)
            cumulative_revenue = round(cumulative_revenue + projected_mrr, 2)
            projections.append(
                {
                    "month": m,
                    "projected_mrr": projected_mrr,
                    "projected_arr": projected_arr,
                    "cumulative_revenue": cumulative_revenue,
                }
            )

        return {
            "scenario": scenario_clean,
            "horizon_months": months,
            "starting_mrr": current_mrr,
            "projected_ending_mrr": projected_mrr,
            "projected_ending_arr": round(projected_mrr * 12, 2),
            "total_forecasted_revenue": cumulative_revenue,
            "monthly_growth_rate_pct": round(monthly_growth * 100, 1),
            "monthly_churn_rate_pct": round(monthly_churn * 100, 1),
            "net_monthly_growth_pct": round(net_growth_rate * 100, 1),
            "monthly_projections": projections,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return engine operational status, database statistics, and key indicators."""
        with self._get_connection() as conn:
            txn_count = conn.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]
            sub_count = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
            ).fetchone()[0]
            rec_count = conn.execute(
                "SELECT COUNT(*) FROM reconciliations"
            ).fetchone()[0]

        metrics = self.get_metrics()
        return {
            "status": "HEALTHY",
            "db_path": str(self.db_path),
            "transactions_count": txn_count,
            "active_subscriptions": sub_count,
            "reconciliations_count": rec_count,
            "mrr": metrics["mrr"],
            "arr": metrics["arr"],
            "total_revenue": metrics["total_revenue"],
        }


_default_revenue_engine: Optional[RevenueEngine] = None


def get_revenue_engine(db_path: Optional[Path] = None) -> RevenueEngine:
    """Return the global RevenueEngine singleton or a newly initialized instance."""
    global _default_revenue_engine
    if db_path is not None:
        return RevenueEngine(db_path=db_path)
    if _default_revenue_engine is None:
        _default_revenue_engine = RevenueEngine()
    return _default_revenue_engine
