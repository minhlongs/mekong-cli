# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Strategy marketplace — Pro/Elite users create, backtest, and publish strategies."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from src.polymarket.marketplace_models import (
    CREATOR_REVENUE_SHARE,
    PLATFORM_REVENUE_SHARE,
    BacktestResult,
    StrategyListing,
    StrategyReview,
    init_marketplace_db,
)

logger = logging.getLogger(__name__)


class StrategyMarketplace:
    """Marketplace for custom trading strategies."""

    def __init__(self, db_path: str = "data/algo-trade.db") -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        init_marketplace_db(self.db_path)

    def create_listing(
        self, strategy_id: str, creator_id: str, name: str,
        description: str, category: str = "general", price_monthly: float = 0.0,
    ) -> StrategyListing:
        listing_id = f"mkt-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        listing = StrategyListing(
            listing_id=listing_id, strategy_id=strategy_id, creator_id=creator_id,
            name=name, description=description, category=category,
            price_monthly=price_monthly, created_at=now,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO marketplace_listings
                   (listing_id, strategy_id, creator_id, name, description, category, price_monthly, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (listing_id, strategy_id, creator_id, name, description, category, price_monthly, now),
            )
        return listing

    def publish_listing(self, listing_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT l.strategy_id FROM marketplace_listings l
                   JOIN backtest_results b ON l.strategy_id = b.strategy_id
                   WHERE l.listing_id = ? AND b.passed = 1""",
                (listing_id,),
            ).fetchone()
            if row is None:
                logger.warning("Cannot publish %s: no passing backtest", listing_id)
                return False
            conn.execute("UPDATE marketplace_listings SET published = 1 WHERE listing_id = ?", (listing_id,))
        return True

    def list_published(self, category: Optional[str] = None) -> list[StrategyListing]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                rows = conn.execute(
                    "SELECT * FROM marketplace_listings WHERE published = 1 AND category = ? ORDER BY subscribers DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM marketplace_listings WHERE published = 1 ORDER BY subscribers DESC").fetchall()
        return [self._row_to_listing(r) for r in rows]

    def get_listing(self, listing_id: str) -> Optional[StrategyListing]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM marketplace_listings WHERE listing_id = ?", (listing_id,)).fetchone()
        return self._row_to_listing(row) if row else None

    def subscribe_to_listing(self, listing_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE marketplace_listings SET subscribers = subscribers + 1 WHERE listing_id = ?", (listing_id,))
            return cursor.rowcount > 0

    def save_backtest(self, result: BacktestResult) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO backtest_results
                   (strategy_id, period_days, total_trades, win_rate, total_pnl_pct, sharpe_ratio, max_drawdown, brier_score, passed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (result.strategy_id, result.period_days, result.total_trades, result.win_rate,
                 result.total_pnl_pct, result.sharpe_ratio, result.max_drawdown, result.brier_score, 1 if result.passed else 0),
            )

    def get_backtests(self, strategy_id: str) -> list[BacktestResult]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM backtest_results WHERE strategy_id = ? ORDER BY created_at DESC", (strategy_id,)).fetchall()
        return [
            BacktestResult(
                strategy_id=r["strategy_id"], period_days=r["period_days"], total_trades=r["total_trades"],
                win_rate=r["win_rate"], total_pnl_pct=r["total_pnl_pct"], sharpe_ratio=r["sharpe_ratio"],
                max_drawdown=r["max_drawdown"], brier_score=r["brier_score"], passed=bool(r["passed"]),
            )
            for r in rows
        ]

    def add_review(self, listing_id: str, reviewer_id: str, rating: int, comment: str) -> Optional[StrategyReview]:
        if not 1 <= rating <= 5:
            return None
        review_id = f"rev-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        review = StrategyReview(review_id=review_id, listing_id=listing_id, reviewer_id=reviewer_id, rating=rating, comment=comment, created_at=now)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO strategy_reviews (review_id, listing_id, reviewer_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (review_id, listing_id, reviewer_id, rating, comment, now),
            )
            avg = conn.execute("SELECT AVG(rating), COUNT(*) FROM strategy_reviews WHERE listing_id = ?", (listing_id,)).fetchone()
            conn.execute("UPDATE marketplace_listings SET rating = ?, reviews = ? WHERE listing_id = ?", (avg[0] or 0, avg[1] or 0, listing_id))
        return review

    def get_reviews(self, listing_id: str) -> list[StrategyReview]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM strategy_reviews WHERE listing_id = ? ORDER BY created_at DESC", (listing_id,)).fetchall()
        return [
            StrategyReview(
                review_id=r["review_id"], listing_id=r["listing_id"], reviewer_id=r["reviewer_id"],
                rating=r["rating"], comment=r["comment"], created_at=r["created_at"],
            )
            for r in rows
        ]

    def calculate_revenue(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT price_monthly, subscribers FROM marketplace_listings WHERE published = 1").fetchall()
        total = sum(price * subs for price, subs in rows)
        return {
            "total_mrr": total, "creator_share": total * CREATOR_REVENUE_SHARE,
            "platform_share": total * PLATFORM_REVENUE_SHARE, "active_listings": len(rows),
        }

    @staticmethod
    def _row_to_listing(row: sqlite3.Row) -> StrategyListing:
        return StrategyListing(
            listing_id=row["listing_id"], strategy_id=row["strategy_id"], creator_id=row["creator_id"],
            name=row["name"], description=row["description"], category=row["category"],
            price_monthly=row["price_monthly"], subscribers=row["subscribers"], rating=row["rating"],
            reviews=row["reviews"], published=bool(row["published"]), created_at=row["created_at"],
        )


__all__ = [
    "BacktestResult", "CREATOR_REVENUE_SHARE", "PLATFORM_REVENUE_SHARE",
    "StrategyListing", "StrategyMarketplace", "StrategyReview", "init_marketplace_db",
]
