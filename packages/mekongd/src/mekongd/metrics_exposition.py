"""Prometheus text-format exposition for mekongd.

Extracted from proxy.py to keep the FastAPI app file focused on routing.
Hand-formatted output (no prometheus_client dep) — see observability doc for
the metric families and their semantics.
"""

from __future__ import annotations

from pathlib import Path

from mekongd.config import MekongdConfig
from mekongd.stats import (
    aggregate_signals,
    aggregate_stats,
    today_cloud_spent_usd,
)


def build_metrics_body(cfg: MekongdConfig) -> str:
    """Aggregate from SQLite + config → Prometheus exposition text."""
    db_path: Path = cfg.stats_db_path
    s = aggregate_stats(db_path)
    lines = [
        "# HELP mekongd_requests_total Total /v1/messages requests by destination",
        "# TYPE mekongd_requests_total counter",
        f'mekongd_requests_total{{destination="local"}} {s.local_requests}',
        f'mekongd_requests_total{{destination="cloud"}} {s.cloud_requests}',
        "# HELP mekongd_tokens_in_total Total input tokens accepted",
        "# TYPE mekongd_tokens_in_total counter",
        f"mekongd_tokens_in_total {s.total_tokens_in}",
        "# HELP mekongd_tokens_out_total Total output tokens produced",
        "# TYPE mekongd_tokens_out_total counter",
        f"mekongd_tokens_out_total {s.total_tokens_out}",
        "# HELP mekongd_cost_saved_usd_total Estimated USD saved by local routing",
        "# TYPE mekongd_cost_saved_usd_total counter",
        f"mekongd_cost_saved_usd_total {s.total_cost_saved_usd:.6f}",
        "# HELP mekongd_local_ratio Share of requests routed to local runtime (0..1)",
        "# TYPE mekongd_local_ratio gauge",
        f"mekongd_local_ratio {s.local_pct / 100:.6f}",
        "# HELP mekongd_cloud_spent_usd_today Cloud routing cost (USD) since UTC midnight",
        "# TYPE mekongd_cloud_spent_usd_today gauge",
        f"mekongd_cloud_spent_usd_today {today_cloud_spent_usd(db_path):.6f}",
        "# HELP mekongd_cloud_daily_budget_usd Configured daily cap (0 = no enforcement)",
        "# TYPE mekongd_cloud_daily_budget_usd gauge",
        f"mekongd_cloud_daily_budget_usd {cfg.cloud_daily_budget_usd or 0:.6f}",
    ]

    sigs = aggregate_signals(db_path)
    good, bad = sigs.get("good", 0), sigs.get("bad", 0)
    total = good + bad
    ratio = good / total if total else 0.0
    lines.extend(
        [
            "# HELP mekongd_signals_total Operator feedback signals by kind (Pillar 3)",
            "# TYPE mekongd_signals_total counter",
            f'mekongd_signals_total{{kind="good"}} {good}',
            f'mekongd_signals_total{{kind="bad"}} {bad}',
            "# HELP mekongd_signals_ratio Share of good signals (0..1, 0 when no signals)",
            "# TYPE mekongd_signals_ratio gauge",
            f"mekongd_signals_ratio {ratio:.6f}",
        ]
    )
    return "\n".join(lines) + "\n"
