# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Copy trading — Elite tier customers auto-copy top strategies."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from src.polymarket.copy_trading_models import (
    CopiedTrade,
    CopyStatus,
    CopySubscription,
    StrategyProfile,
    init_copy_trading_db,
)
from src.polymarket.copy_trading_ops import CopyTradingReplicatorMixin

logger = logging.getLogger(__name__)


class CopyTradingEngine(CopyTradingReplicatorMixin):
    """Manages copy trading subscriptions and trade replication."""

    def __init__(self, db_path: str = "data/algo-trade.db") -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        init_copy_trading_db(self.db_path)

    def subscribe(
        self,
        copier_user_id: str,
        strategy_id: str,
        max_capital: float,
    ) -> Optional[CopySubscription]:
        strategy = self.get_strategy(strategy_id)
        if strategy is None:
            return None

        sub_id = f"copy-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        sub = CopySubscription(
            subscription_id=sub_id, copier_user_id=copier_user_id, strategy_id=strategy_id,
            max_capital=max_capital, allocated_capital=0.0, status=CopyStatus.ACTIVE, created_at=now,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO copy_subscriptions
                   (subscription_id, copier_user_id, strategy_id, max_capital, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sub_id, copier_user_id, strategy_id, max_capital, "active", now),
            )
            conn.execute("UPDATE strategy_profiles SET copiers = copiers + 1 WHERE strategy_id = ?", (strategy_id,))

        logger.info("Copy subscription: %s → %s ($%.2f)", copier_user_id, strategy_id, max_capital)
        return sub

    def pause(self, subscription_id: str) -> bool:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE copy_subscriptions SET status = 'paused', paused_at = ? WHERE subscription_id = ?",
                (now, subscription_id),
            )
            return cursor.rowcount > 0

    def resume(self, subscription_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE copy_subscriptions SET status = 'active', paused_at = NULL WHERE subscription_id = ?",
                (subscription_id,),
            )
            return cursor.rowcount > 0

    def stop(self, subscription_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT strategy_id FROM copy_subscriptions WHERE subscription_id = ?", (subscription_id,)).fetchone()
            cursor = conn.execute("UPDATE copy_subscriptions SET status = 'stopped' WHERE subscription_id = ?", (subscription_id,))
            if row:
                conn.execute("UPDATE strategy_profiles SET copiers = MAX(0, copiers - 1) WHERE strategy_id = ?", (row[0],))
            return cursor.rowcount > 0

    def get_subscription(self, subscription_id: str) -> Optional[CopySubscription]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM copy_subscriptions WHERE subscription_id = ?", (subscription_id,)).fetchone()
        if row is None:
            return None
        return CopySubscription(
            subscription_id=row["subscription_id"], copier_user_id=row["copier_user_id"],
            strategy_id=row["strategy_id"], max_capital=row["max_capital"],
            allocated_capital=row["allocated_capital"], status=CopyStatus(row["status"]),
            pnl=row["pnl"], trades_copied=row["trades_copied"],
            created_at=row["created_at"], paused_at=row["paused_at"],
        )

    def get_user_subscriptions(self, user_id: str) -> list[CopySubscription]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM copy_subscriptions WHERE copier_user_id = ?", (user_id,)).fetchall()
        return [
            CopySubscription(
                subscription_id=r["subscription_id"], copier_user_id=r["copier_user_id"],
                strategy_id=r["strategy_id"], max_capital=r["max_capital"],
                allocated_capital=r["allocated_capital"], status=CopyStatus(r["status"]),
                pnl=r["pnl"], trades_copied=r["trades_copied"],
            )
            for r in rows
        ]


__all__ = [
    "CopiedTrade", "CopyStatus", "CopySubscription", "CopyTradingEngine",
    "CopyTradingReplicatorMixin", "StrategyProfile", "init_copy_trading_db",
]
