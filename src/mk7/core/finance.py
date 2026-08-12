"""Mekong CLI 7 — Finance module (OPC Platform).

Cost tracking → profit/MRR. Human-confirmed like revenue (bắt buộc `by`).
MRR = subscription revenue trong 30 ngày gần nhất.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .opc_loop import OPC_DIR, _load, _save

DEFAULT_RATE_USD_HOUR = 50.0


@dataclass
class CostEntry:
    product: str
    hours: float
    rate_usd_hour: float = DEFAULT_RATE_USD_HOUR
    tooling_usd: float = 0.0
    by: str = ""
    ts: float = field(default_factory=time.time)

    @property
    def labor_usd(self) -> float:
        return round(self.hours * self.rate_usd_hour, 2)

    @property
    def total_usd(self) -> float:
        return round(self.labor_usd + self.tooling_usd, 2)


class FinanceStore:
    def __init__(self) -> None:
        self.costs: list[dict[str, Any]] = _load("costs.json", [])

    def record(self, product: str, hours: float, rate: float = DEFAULT_RATE_USD_HOUR,
               tooling: float = 0.0, by: str = "") -> CostEntry:
        if not by:
            raise ValueError("cost requires human confirmation (by)")
        entry = CostEntry(product=product, hours=hours, rate_usd_hour=rate,
                          tooling_usd=tooling, by=by)
        self.costs.append({
            "product": product, "hours": hours, "rate_usd_hour": rate,
            "tooling_usd": tooling, "by": by, "ts": entry.ts,
        })
        _save("costs.json", self.costs)
        return entry

    def total_for(self, product: str, since: float = 0) -> float:
        return round(sum(
            e["hours"] * e["rate_usd_hour"] + e["tooling_usd"]
            for e in self.costs if e["product"] == product and e["ts"] >= since
        ), 2)

    def hours_for(self, product: str, since: float = 0) -> float:
        return round(sum(
            e["hours"] for e in self.costs
            if e["product"] == product and e["ts"] >= since
        ), 2)


class Finance:
    """Finance module: profit + MRR per product."""

    def __init__(self) -> None:
        from .opc_loop import RevenueLedger

        self.costs = FinanceStore()
        self.revenue = RevenueLedger()

    def profit(self, product: str, since: float = 0) -> float:
        return round(self.revenue.total_for(product, since) - self.costs.total_for(product, since), 2)

    def mrr(self, product: str | None = None) -> float:
        """MRR = subscription revenue trong 30 ngày gần nhất."""
        since = time.time() - 30 * 86400
        total = 0.0
        for e in self.revenue.data:
            if e["kind"] != "subscription" or e["ts"] < since:
                continue
            if product and e["product"] != product:
                continue
            total += e["amount"]
        return round(total, 2)

    def summary(self, product: str | None = None) -> dict[str, Any]:
        products = [product] if product else sorted({
            e["product"] for e in self.revenue.data
        } | {e["product"] for e in self.costs.costs})
        out: dict[str, Any] = {"mrr_total": self.mrr(), "products": {}}
        for p in products:
            rev = self.revenue.total_for(p)
            cost = self.costs.total_for(p)
            out["products"][p] = {
                "revenue": rev, "cost": cost, "profit": round(rev - cost, 2),
                "hours": self.costs.hours_for(p), "mrr": self.mrr(p),
            }
        return out
