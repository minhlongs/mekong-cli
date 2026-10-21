# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data structures and database schema for strategy marketplace."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

# Revenue share: 70% creator, 30% platform
CREATOR_REVENUE_SHARE = 0.70
PLATFORM_REVENUE_SHARE = 0.30


@dataclass
class StrategyListing:
    """A strategy listed on the marketplace."""
    listing_id: str
    strategy_id: str
    creator_id: str
    name: str
    description: str
    category: str
    price_monthly: float
    subscribers: int = 0
    rating: float = 0.0
    reviews: int = 0
    published: bool = False
    created_at: str = ""

    @property
    def creator_revenue(self) -> float:
        """Monthly revenue for creator."""
        return self.price_monthly * self.subscribers * CREATOR_REVENUE_SHARE

    @property
    def platform_revenue(self) -> float:
        """Monthly revenue for platform."""
        return self.price_monthly * self.subscribers * PLATFORM_REVENUE_SHARE


@dataclass
class BacktestResult:
    """Result of backtesting a strategy."""
    strategy_id: str
    period_days: int
    total_trades: int
    win_rate: float
    total_pnl_pct: float
    sharpe_ratio: float
    max_drawdown: float
    brier_score: float
    passed: bool = False

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.period_days}d: "
            f"trades={self.total_trades} win={self.win_rate:.0%} "
            f"pnl={self.total_pnl_pct:+.1f}% sharpe={self.sharpe_ratio:.2f}"
        )


@dataclass
class StrategyReview:
    """A user review of a marketplace strategy."""
    review_id: str
    listing_id: str
    reviewer_id: str
    rating: int  # 1-5
    comment: str
    created_at: str = ""


def init_marketplace_db(db_path: str) -> None:
    """Create marketplace tables if they do not exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_listings (
                listing_id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                price_monthly REAL DEFAULT 0,
                subscribers INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                reviews INTEGER DEFAULT 0,
                published INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_reviews (
                review_id TEXT PRIMARY KEY,
                listing_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES marketplace_listings(listing_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                period_days INTEGER,
                total_trades INTEGER,
                win_rate REAL,
                total_pnl_pct REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                brier_score REAL,
                passed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
