"""
core/signals/evals/offline.py — Canned SQL queries against local signals.sqlite.

3 standard eval metrics (last 7 days by default):
  1. success_rate  — fraction of missions that succeeded
  2. p95_ms        — 95th-percentile duration in milliseconds
  3. avg_credits   — average credits consumed per mission

All queries accept optional agent_id filter and days window.
Returns typed dicts — safe for CLI table rendering and JSON export.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.core.signals.local_store import _get_db_path


@dataclass
class EvalResult:
    """Output of a single eval run."""

    agent_id: str
    window_days: int
    total_missions: int
    success_rate: float   # 0.0–1.0
    p95_ms: int
    avg_credits: float
    db_path: str

    def summary(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "window_days": self.window_days,
            "total_missions": self.total_missions,
            "success_rate_pct": round(self.success_rate * 100, 1),
            "p95_ms": self.p95_ms,
            "avg_credits": round(self.avg_credits, 2),
        }


def run_offline_eval(
    agent_id: str = "all",
    window_days: int = 7,
    db_path: Optional[Path] = None,
) -> EvalResult:
    """
    Run 3 canned eval queries for the given agent_id and time window.

    Args:
        agent_id:    Agent version slug to filter, or "all" for no filter.
        window_days: How many days back to query (default 7).
        db_path:     Override SQLite path (uses env/default if None).

    Returns:
        EvalResult with metrics, or zeroed result if DB missing/empty.
    """
    path = db_path or _get_db_path()
    agent_filter = agent_id if agent_id != "all" else None

    empty = EvalResult(
        agent_id=agent_id,
        window_days=window_days,
        total_missions=0,
        success_rate=0.0,
        p95_ms=0,
        avg_credits=0.0,
        db_path=str(path),
    )

    if not path.exists():
        return empty

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row

        # Date filter — SQLite stores ts as ISO-8601 text
        date_expr = f"datetime(ts) >= datetime('now', '-{window_days} days')"
        agent_expr = "agent_id = ?" if agent_filter else "1=1"
        params: list = [agent_filter] if agent_filter else []

        base_where = f"WHERE {date_expr} AND {agent_expr}"

        # Query 1: success rate + total
        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                AVG(CAST(success AS REAL)) AS success_rate,
                AVG(CAST(credits_used AS REAL)) AS avg_credits
            FROM missions
            {base_where}
            """,
            params,
        ).fetchone()

        if not row or row["total"] == 0:
            conn.close()
            return empty

        total = int(row["total"])
        success_rate = float(row["success_rate"] or 0.0)
        avg_credits = float(row["avg_credits"] or 0.0)

        # Query 2: p95 duration — SQLite has no built-in percentile; use ntile
        all_durations = [
            r[0]
            for r in conn.execute(
                f"SELECT duration_ms FROM missions {base_where} ORDER BY duration_ms",
                params,
            ).fetchall()
        ]

        p95_ms = 0
        if all_durations:
            idx = max(0, int(len(all_durations) * 0.95) - 1)
            p95_ms = all_durations[idx]

        conn.close()

        return EvalResult(
            agent_id=agent_id,
            window_days=window_days,
            total_missions=total,
            success_rate=success_rate,
            p95_ms=p95_ms,
            avg_credits=avg_credits,
            db_path=str(path),
        )

    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning("offline eval failed: %s", exc)
        return empty
