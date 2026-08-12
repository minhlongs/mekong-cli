"""Mekong CLI 7 — Analytics module (4 KPI board).

MRR · active products · conversion · cost/build — 4 góc nhìn platform.
"""

from __future__ import annotations

import time
from typing import Any

from .finance import Finance
from .opc_loop import MetricsStore, OpcLoop, RevenueLedger


class Analytics:
    def __init__(self) -> None:
        self.finance = Finance()
        self.revenue = RevenueLedger()
        self.metrics = MetricsStore()
        self.loop = OpcLoop()

    def board(self) -> dict[str, Any]:
        # 1. MRR
        mrr = self.finance.mrr()
        # 2. active products (không bị kill)
        active = len(self.loop.state.active_products)
        # 3. conversion = closes / leads (từ sales module — n/a nếu chưa có)
        leads = len([s for _, s in __import__("src.mk7.core.opc_loop", fromlist=["SignalInbox"])()
                     .SignalInbox().list() if s["kind"] == "lead"]) if False else 0
        # đọc trực tiếp từ signal inbox
        from .opc_loop import SignalInbox

        sig_leads = len([s for _, s in SignalInbox().list() if s["kind"] == "lead"])
        closes = len(self.revenue.data)
        conversion = round(closes / sig_leads, 2) if sig_leads else None
        # 4. cost/build = tổng cost / tổng build hours
        total_cost = sum(self.finance.costs.total_for(p) for p in
                         self.loop.state.active_products)
        total_hours = sum(self.finance.costs.hours_for(p) for p in
                          self.loop.state.active_products)
        cost_per_hour = round(total_cost / total_hours, 2) if total_hours else None
        # 5. A2: spend thật từ LLM (spend.jsonl) — không còn n/a
        from .spend import burn_rate

        spend_24h = burn_rate(24)
        spend_7d = burn_rate(24 * 7)
        if cost_per_hour is None and spend_24h > 0:
            cost_per_hour = round(spend_24h / 24, 2)  # $/h vận hành thật từ spend

        # per-product rows
        rows = []
        for p in self.loop.state.active_products:
            m = self.metrics.get(p)
            rev = self.revenue.total_for(p)
            cost = self.finance.costs.total_for(p)
            rows.append({
                "product": p, "revenue": rev, "cost": cost,
                "profit": round(rev - cost, 2),
                "cycles": m.get("cycles", 0),
                "kill_risk": m.get("zero_revenue_streak", 0),
            })

        return {
            "kpi": {
                "mrr": mrr,
                "active_products": active,
                "conversion": conversion,
                "cost_per_build_hour": cost_per_hour,
                "spend_24h": spend_24h,
                "spend_7d": spend_7d,
            },
            "products": rows,
        }
