"""Public signals API — free tier signal endpoint + performance transparency.

Endpoints:
  GET /public/signals      — 1 top signal (no auth, 10 req/min per IP)
  GET /public/performance  — anonymized live P&L dashboard data
  GET /public/calibration  — Brier score + calibration curve data
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public (Free Tier)"])

DB_PATH = os.getenv("DATABASE_PATH", "data/algo-trade.db")

# In-memory rate limit store
_ip_requests: dict[str, list[float]] = defaultdict(list)


def _check_ip_rate_limit(client_ip: str, max_per_min: int = 10) -> None:
    """Rate limit by IP address."""
    now = time.time()
    requests = _ip_requests[client_ip]
    requests[:] = [t for t in requests if t > now - 60]
    if len(requests) >= max_per_min:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: {max_per_min} requests per minute",
            headers={"Retry-After": "60"},
        )
    requests.append(now)


@router.get("/signals")
async def public_signal(request: Request) -> dict:
    """Free tier: 1 top AI signal with reasoning. No auth required.

    Designed to drive upgrades: shows signal quality, gates quantity.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip)

    # Get latest signal from database
    signal = _get_latest_signal()

    return {
        "signal": signal,
        "tier": "free",
        "signals_shown": 1,
        "upgrade_cta": "Get 20 signals/day with CashClaw Pro ($149/mo)",
        "pricing_url": "https://cashclaw.io/pricing",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/performance")
async def public_performance(request: Request) -> dict:
    """Public performance dashboard data — anonymized, live.

    Transparency builds trust → drives signups.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip, max_per_min=30)

    perf = _get_performance_summary()
    return {
        "performance": perf,
        "note": "Amounts anonymized. Percentages are real.",
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/calibration")
async def public_calibration(request: Request) -> dict:
    """Public calibration data — Brier score + calibration curve.

    Shows prediction quality to potential customers.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip, max_per_min=30)

    calibration = _get_calibration_data()
    return {
        "calibration": calibration,
        "updated_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_latest_signal() -> Optional[dict]:
    """Get the latest prediction signal from the database."""
    if not Path(DB_PATH).exists():
        return None

    try:
        with sqlite3.connect(DB_PATH) as conn:
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
            "market_id": row["market_id"][:8] + "...",  # Truncate for privacy
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


def _get_performance_summary() -> dict:
    """Get anonymized performance summary."""
    if not Path(DB_PATH).exists():
        return _empty_performance()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Total stats
            total = conn.execute(
                "SELECT COUNT(*) FROM ai_decisions WHERE resolved = 1"
            ).fetchone()[0]

            if total == 0:
                return _empty_performance()

            # Win rate
            wins = conn.execute(
                "SELECT COUNT(*) FROM ai_decisions WHERE resolved = 1 AND pnl > 0"
            ).fetchone()[0]

            # Brier score
            rows = conn.execute(
                "SELECT predicted_probability, actual_outcome FROM ai_decisions WHERE resolved = 1"
            ).fetchall()
            brier = sum((p - a) ** 2 for p, a in rows) / len(rows) if rows else 1.0

            # Weekly breakdown
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
        return _empty_performance()


def _get_calibration_data() -> dict:
    """Get calibration curve data (binned predictions vs actuals)."""
    if not Path(DB_PATH).exists():
        return {"bins": [], "brier_score": None, "sample_size": 0}

    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT predicted_probability, actual_outcome FROM ai_decisions WHERE resolved = 1"
            ).fetchall()

        if not rows:
            return {"bins": [], "brier_score": None, "sample_size": 0}

        # Bin predictions into 10 buckets
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

        return {
            "bins": calibration_bins,
            "brier_score": round(brier, 4),
            "sample_size": len(rows),
        }
    except Exception:
        logger.exception("Error fetching calibration data")
        return {"bins": [], "brier_score": None, "sample_size": 0}


def _empty_performance() -> dict:
    """Return empty performance summary."""
    return {
        "total_trades": 0,
        "win_rate": 0,
        "brier_score": None,
        "weeks": [],
    }
