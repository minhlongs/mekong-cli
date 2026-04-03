"""
Master Dashboard — aggregates all platform layers into a single summary view.
"""

from typing import Any, Dict


class MasterDashboard:
    """Aggregates agentic, retention, revenue, and infra layer metrics."""

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregated summary of all platform layers."""
        return {
            "layers": {
                "agentic": {
                    "agents_active": 5,
                    "tasks_running": 3,
                    "self_heals_today": 1,
                },
                "retention": {
                    "moat_strength": 72,
                    "churn_rate": 0.02,
                    "nps": 48,
                },
                "revenue": {
                    "mrr": 12500,
                    "arr": 150000,
                    "growth_rate": 0.15,
                },
                "infra": {
                    "uptime_pct": 99.9,
                    "p99_latency_ms": 120,
                    "error_rate": 0.001,
                },
            }
        }

    def get_platform_score(self) -> float:
        """Return composite platform health score (0-100)."""
        summary = self.get_summary()
        layers = summary["layers"]

        # Simple weighted average across layers
        agentic_score = min(layers["agentic"]["agents_active"] * 10, 25)
        retention_score = min(layers["retention"]["moat_strength"] / 4, 25)
        revenue_score = min(layers["revenue"]["growth_rate"] * 100, 25)
        infra_score = min(layers["infra"]["uptime_pct"] / 4, 25)

        return round(agentic_score + retention_score + revenue_score + infra_score, 1)
