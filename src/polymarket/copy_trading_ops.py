# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Trade replication and strategy profile management for copy trading."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from src.polymarket.copy_trading_models import (
    CopiedTrade,
    CopyStatus,
    StrategyProfile,
)

logger = logging.getLogger(__name__)


class CopyTradingReplicatorMixin:
    """Methods for strategy management, subscriptions, and trade replication."""

    db_path: str

    def register_strategy(self, name: str, description: str, author_id: str) -> StrategyProfile:
        strategy_id = f"strat-{uuid.uuid4().hex[:8]}"
        profile = StrategyProfile(strategy_id=strategy_id, name=name, description=description, author_id=author_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO strategy_profiles (strategy_id, name, description, author_id) VALUES (?, ?, ?, ?)",
                (strategy_id, name, description, author_id),
            )
        return profile

    def list_strategies(self, public_only: bool = True) -> list[StrategyProfile]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM strategy_profiles"
            if public_only:
                query += " WHERE is_public = 1"
            query += " ORDER BY copiers DESC"
            rows = conn.execute(query).fetchall()

        return [
            StrategyProfile(
                strategy_id=r["strategy_id"], name=r["name"], description=r["description"],
                author_id=r["author_id"], win_rate=r["win_rate"], total_trades=r["total_trades"],
                total_pnl_pct=r["total_pnl_pct"], sharpe_ratio=r["sharpe_ratio"],
                max_drawdown=r["max_drawdown"], copiers=r["copiers"], is_public=bool(r["is_public"]),
            )
            for r in rows
        ]

    def get_strategy(self, strategy_id: str) -> Optional[StrategyProfile]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM strategy_profiles WHERE strategy_id = ?", (strategy_id,)).fetchone()
        if row is None:
            return None
        return StrategyProfile(
            strategy_id=row["strategy_id"], name=row["name"], description=row["description"],
            author_id=row["author_id"], win_rate=row["win_rate"], total_trades=row["total_trades"],
            total_pnl_pct=row["total_pnl_pct"], sharpe_ratio=row["sharpe_ratio"],
            max_drawdown=row["max_drawdown"], copiers=row["copiers"],
        )

    def update_strategy_stats(
        self, strategy_id: str, win_rate: float, total_trades: int, total_pnl_pct: float,
        sharpe_ratio: float = 0.0, max_drawdown: float = 0.0,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE strategy_profiles
                   SET win_rate = ?, total_trades = ?, total_pnl_pct = ?,
                       sharpe_ratio = ?, max_drawdown = ?
                   WHERE strategy_id = ?""",
                (win_rate, total_trades, total_pnl_pct, sharpe_ratio, max_drawdown, strategy_id),
            )

    def replicate_trade(
        self, subscription_id: str, original_trade_id: str, market_id: str,
        direction: str, size_usd: float, entry_price: float,
    ) -> Optional[CopiedTrade]:
        sub = self.get_subscription(subscription_id)  # type: ignore[attr-defined]
        if sub is None or sub.status != CopyStatus.ACTIVE:
            return None
        if sub.allocated_capital + size_usd > sub.max_capital:
            size_usd = sub.max_capital - sub.allocated_capital
            if size_usd <= 0:
                return None

        trade_id = f"ct-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        trade = CopiedTrade(
            trade_id=trade_id, subscription_id=subscription_id, original_trade_id=original_trade_id,
            market_id=market_id, direction=direction, size_usd=size_usd, entry_price=entry_price, timestamp=now,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO copied_trades
                   (trade_id, subscription_id, original_trade_id, market_id, direction, size_usd, entry_price, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (trade_id, subscription_id, original_trade_id, market_id, direction, size_usd, entry_price, now),
            )
            conn.execute(
                "UPDATE copy_subscriptions SET allocated_capital = allocated_capital + ?, trades_copied = trades_copied + 1 WHERE subscription_id = ?",
                (size_usd, subscription_id),
            )
        return trade

    def resolve_copied_trade(self, trade_id: str, pnl: float) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT subscription_id, size_usd FROM copied_trades WHERE trade_id = ?", (trade_id,)).fetchone()
            if row is None:
                return False
            conn.execute("UPDATE copied_trades SET pnl = ? WHERE trade_id = ?", (pnl, trade_id))
            conn.execute(
                "UPDATE copy_subscriptions SET pnl = pnl + ?, allocated_capital = MAX(0, allocated_capital - ?) WHERE subscription_id = ?",
                (pnl, row[1], row[0]),
            )
        return True
