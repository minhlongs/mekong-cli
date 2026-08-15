"""Capital tier progression system for risk-managed growth."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CapitalTier:
    """A capital tier with progression requirements."""
    level: int
    max_capital: float
    min_dry_run_days: int
    min_profitable_days: int


TIERS: list[CapitalTier] = [
    CapitalTier(level=1, max_capital=200, min_dry_run_days=14, min_profitable_days=10),
    CapitalTier(level=2, max_capital=500, min_dry_run_days=14, min_profitable_days=10),
    CapitalTier(level=3, max_capital=1000, min_dry_run_days=14, min_profitable_days=10),
    CapitalTier(level=4, max_capital=5000, min_dry_run_days=14, min_profitable_days=10),
]


@dataclass
class TierProgress:
    """Progress report for current tier."""
    tier: CapitalTier
    days_completed: int
    profitable_days: int
    total_pnl: float
    can_progress: bool
    next_tier: Optional[CapitalTier]


def get_current_tier(db_path: str) -> CapitalTier:
    """Determine current tier from trade history."""
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT date(timestamp)) FROM ai_decisions WHERE resolved = 1"
            ).fetchone()
            total_days = row[0] if row else 0

        # Progress through tiers based on days traded
        accumulated_days = 0
        for tier in TIERS:
            accumulated_days += tier.min_dry_run_days
            if total_days < accumulated_days:
                return tier
        return TIERS[-1]
    except Exception:
        return TIERS[0]


def can_progress_to_next_tier(db_path: str) -> bool:
    """Check if criteria met for next tier."""
    current = get_current_tier(db_path)
    if current.level >= len(TIERS):
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            # Count profitable days in current tier window
            rows = conn.execute(
                """SELECT date(timestamp) as day, SUM(pnl) as daily_pnl
                   FROM ai_decisions
                   WHERE resolved = 1
                   GROUP BY day
                   ORDER BY day DESC
                   LIMIT ?""",
                (current.min_dry_run_days,),
            ).fetchall()

        if len(rows) < current.min_dry_run_days:
            return False

        profitable_days = sum(1 for _, pnl in rows if pnl and pnl > 0)
        return profitable_days >= current.min_profitable_days
    except Exception:
        return False


def get_progress_report(db_path: str) -> TierProgress:
    """Get progress report for current tier."""
    current = get_current_tier(db_path)
    next_tier = None
    if current.level < len(TIERS):
        next_tier = TIERS[current.level]

    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                """SELECT date(timestamp) as day, SUM(pnl) as daily_pnl
                   FROM ai_decisions
                   WHERE resolved = 1
                   GROUP BY day
                   ORDER BY day DESC
                   LIMIT ?""",
                (current.min_dry_run_days,),
            ).fetchall()

        days_completed = len(rows)
        profitable_days = sum(1 for _, pnl in rows if pnl and pnl > 0)
        total_pnl = sum(pnl for _, pnl in rows if pnl)
    except Exception:
        days_completed = 0
        profitable_days = 0
        total_pnl = 0.0

    return TierProgress(
        tier=current,
        days_completed=days_completed,
        profitable_days=profitable_days,
        total_pnl=total_pnl,
        can_progress=can_progress_to_next_tier(db_path),
        next_tier=next_tier,
    )
