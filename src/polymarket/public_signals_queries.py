# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data queries and analytics for public trading signals."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_latest_signal(db_path: str) -> Optional[dict]:
    """Get the latest prediction signal from the database."""
    if not Path(db_path).exists():
        return None

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT market_id, question, predicted_probability,
                          market_price, edge, direction, confidence,
                          model_used, timestamp
                   FROM ai_decisions
                   ORDER BY timestamp DESC
                   LIMIT 1"""
            ).fetchone()

        if row is None:
            return None

        return {
            "market_id": row["market_id"][:8] + "...",
            "question": row["question"],
            "direction": row["direction"],
            "predicted_probability": round(row["predicted_probability"], 3),
            "market_price": round(row["market_price"], 3),
            "edge": round(row["edge"], 3),
            "confidence": round(row["confidence"], 3),
            "model": row["model_used"],
        }
    except Exception:
        logger.exception("Error fetching latest signal")
        return None


def get_performance_summary(db_path: str) -> dict:
    """Get anonymized performance summary."""
    if not Path(db_path).exists():
        return empty_performance()

    try:
        with sqlite3.connect(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM ai_decisions WHERE resolved = 1").fetchone()[0]
            if total == 0:
                return empty_performance()

            wins = conn.execute("SELECT COUNT(*) FROM ai_decisions WHERE resolved = 1 AND pnl > 0").fetchone()[0]
            rows = conn.execute("SELECT predicted_probability, actual_outcome FROM ai_decisions WHERE resolved = 1").fetchall()
            brier = sum((p - a) ** 2 for p, a in rows) / len(rows) if rows else 1.0

            weekly = conn.execute(
                """SELECT strftime('%Y-W%W', timestamp) as week,
                          COUNT(*) as trades,
                          SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
                   FROM ai_decisions
                   WHERE resolved = 1
                   GROUP BY week
                   ORDER BY week DESC
                   LIMIT 8"""
            ).fetchall()

        return {
            "total_trades": total,
            "win_rate": round(wins / total, 3) if total > 0 else 0,
            "brier_score": round(brier, 4),
            "weeks": [
                {
                    "week": w[0],
                    "trades": w[1],
                    "win_rate": round(w[2] / w[1], 3) if w[1] > 0 else 0,
                }
                for w in weekly
            ],
        }
    except Exception:
        logger.exception("Error fetching performance")
        return empty_performance()


def get_calibration_data(db_path: str) -> dict:
    """Get calibration curve data (binned predictions vs actuals)."""
    if not Path(db_path).exists():
        return {"bins": [], "brier_score": None, "sample_size": 0}

    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT predicted_probability, actual_outcome FROM ai_decisions WHERE resolved = 1").fetchall()

        if not rows:
            return {"bins": [], "brier_score": None, "sample_size": 0}

        bins: dict[int, list[tuple[float, float]]] = {i: [] for i in range(10)}
        for pred, actual in rows:
            bucket = min(int(pred * 10), 9)
            bins[bucket].append((pred, actual))

        calibration_bins = []
        for i in range(10):
            bucket_data = bins[i]
            if bucket_data:
                avg_pred = sum(p for p, _ in bucket_data) / len(bucket_data)
                avg_actual = sum(a for _, a in bucket_data) / len(bucket_data)
                calibration_bins.append({
                    "bin": f"{i * 10}-{(i + 1) * 10}%",
                    "avg_predicted": round(avg_pred, 3),
                    "avg_actual": round(avg_actual, 3),
                    "count": len(bucket_data),
                })

        brier = sum((p - a) ** 2 for p, a in rows) / len(rows)
        return {"bins": calibration_bins, "brier_score": round(brier, 4), "sample_size": len(rows)}
    except Exception:
        logger.exception("Error fetching calibration data")
        return {"bins": [], "brier_score": None, "sample_size": 0}


def empty_performance() -> dict:
    """Return empty performance summary."""
    return {"total_trades": 0, "win_rate": 0, "brier_score": None, "weeks": []}
