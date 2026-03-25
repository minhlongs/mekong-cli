"""Copy trading — Elite tier customers auto-copy top strategies.

Flow:
  1. Customer selects strategy portfolio (market-maker, mean-reversion, etc.)
  2. Sets max capital allocation
  3. Automatic trade execution via customer's Polymarket API key
  4. Real-time P&L tracking per copier
  5. One-click pause/resume

This is the highest-value feature for Elite tier ($499/month).
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CopyStatus(Enum):
    """Copy trading subscription status."""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class StrategyProfile:
    """A copyable strategy profile."""
    strategy_id: str
    name: str
    description: str
    author_id: str
    win_rate: float = 0.0
    total_trades: int = 0
    total_pnl_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    copiers: int = 0
    is_public: bool = True


@dataclass
class CopySubscription:
    """A customer's copy trading subscription."""
    subscription_id: str
    copier_user_id: str
    strategy_id: str
    max_capital: float
    allocated_capital: float
    status: CopyStatus
    pnl: float = 0.0
    trades_copied: int = 0
    created_at: str = ""
    paused_at: Optional[str] = None


@dataclass
class CopiedTrade:
    """A trade executed by copy trading."""
    trade_id: str
    subscription_id: str
    original_trade_id: str
    market_id: str
    direction: str
    size_usd: float
    entry_price: float
    pnl: Optional[float] = None
    timestamp: str = ""


class CopyTradingEngine:
    """Manages copy trading subscriptions and trade replication."""

    def __init__(self, db_path: str = "data/algo-trade.db") -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create copy trading tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_profiles (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    author_id TEXT NOT NULL,
                    win_rate REAL DEFAULT 0,
                    total_trades INTEGER DEFAULT 0,
                    total_pnl_pct REAL DEFAULT 0,
                    sharpe_ratio REAL DEFAULT 0,
                    max_drawdown REAL DEFAULT 0,
                    copiers INTEGER DEFAULT 0,
                    is_public INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS copy_subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    copier_user_id TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    max_capital REAL NOT NULL,
                    allocated_capital REAL DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    pnl REAL DEFAULT 0,
                    trades_copied INTEGER DEFAULT 0,
                    created_at TEXT,
                    paused_at TEXT,
                    FOREIGN KEY (strategy_id) REFERENCES strategy_profiles(strategy_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS copied_trades (
                    trade_id TEXT PRIMARY KEY,
                    subscription_id TEXT NOT NULL,
                    original_trade_id TEXT,
                    market_id TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    size_usd REAL NOT NULL,
                    entry_price REAL,
                    pnl REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES copy_subscriptions(subscription_id)
                )
            """)

    # --- Strategy Profiles ---

    def register_strategy(
        self,
        name: str,
        description: str,
        author_id: str,
    ) -> StrategyProfile:
        """Register a new copyable strategy."""
        strategy_id = f"strat-{uuid.uuid4().hex[:8]}"
        profile = StrategyProfile(
            strategy_id=strategy_id,
            name=name,
            description=description,
            author_id=author_id,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO strategy_profiles
                   (strategy_id, name, description, author_id)
                   VALUES (?, ?, ?, ?)""",
                (strategy_id, name, description, author_id),
            )
        return profile

    def list_strategies(self, public_only: bool = True) -> list[StrategyProfile]:
        """List available strategies for copying."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM strategy_profiles"
            if public_only:
                query += " WHERE is_public = 1"
            query += " ORDER BY copiers DESC"
            rows = conn.execute(query).fetchall()

        return [
            StrategyProfile(
                strategy_id=r["strategy_id"],
                name=r["name"],
                description=r["description"],
                author_id=r["author_id"],
                win_rate=r["win_rate"],
                total_trades=r["total_trades"],
                total_pnl_pct=r["total_pnl_pct"],
                sharpe_ratio=r["sharpe_ratio"],
                max_drawdown=r["max_drawdown"],
                copiers=r["copiers"],
                is_public=bool(r["is_public"]),
            )
            for r in rows
        ]

    def get_strategy(self, strategy_id: str) -> Optional[StrategyProfile]:
        """Get strategy by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM strategy_profiles WHERE strategy_id = ?",
                (strategy_id,),
            ).fetchone()

        if row is None:
            return None
        return StrategyProfile(
            strategy_id=row["strategy_id"],
            name=row["name"],
            description=row["description"],
            author_id=row["author_id"],
            win_rate=row["win_rate"],
            total_trades=row["total_trades"],
            total_pnl_pct=row["total_pnl_pct"],
            sharpe_ratio=row["sharpe_ratio"],
            max_drawdown=row["max_drawdown"],
            copiers=row["copiers"],
        )

    def update_strategy_stats(
        self,
        strategy_id: str,
        win_rate: float,
        total_trades: int,
        total_pnl_pct: float,
        sharpe_ratio: float = 0.0,
        max_drawdown: float = 0.0,
    ) -> None:
        """Update strategy performance stats."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE strategy_profiles
                   SET win_rate = ?, total_trades = ?, total_pnl_pct = ?,
                       sharpe_ratio = ?, max_drawdown = ?
                   WHERE strategy_id = ?""",
                (win_rate, total_trades, total_pnl_pct,
                 sharpe_ratio, max_drawdown, strategy_id),
            )

    # --- Copy Subscriptions ---

    def subscribe(
        self,
        copier_user_id: str,
        strategy_id: str,
        max_capital: float,
    ) -> Optional[CopySubscription]:
        """Subscribe to copy a strategy."""
        strategy = self.get_strategy(strategy_id)
        if strategy is None:
            return None

        sub_id = f"copy-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        sub = CopySubscription(
            subscription_id=sub_id,
            copier_user_id=copier_user_id,
            strategy_id=strategy_id,
            max_capital=max_capital,
            allocated_capital=0.0,
            status=CopyStatus.ACTIVE,
            created_at=now,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO copy_subscriptions
                   (subscription_id, copier_user_id, strategy_id,
                    max_capital, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sub_id, copier_user_id, strategy_id,
                 max_capital, "active", now),
            )
            conn.execute(
                "UPDATE strategy_profiles SET copiers = copiers + 1 WHERE strategy_id = ?",
                (strategy_id,),
            )

        logger.info("Copy subscription: %s → %s ($%.2f)", copier_user_id, strategy_id, max_capital)
        return sub

    def pause(self, subscription_id: str) -> bool:
        """Pause copy trading."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE copy_subscriptions SET status = 'paused', paused_at = ? WHERE subscription_id = ?",
                (now, subscription_id),
            )
            return cursor.rowcount > 0

    def resume(self, subscription_id: str) -> bool:
        """Resume copy trading."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE copy_subscriptions SET status = 'active', paused_at = NULL WHERE subscription_id = ?",
                (subscription_id,),
            )
            return cursor.rowcount > 0

    def stop(self, subscription_id: str) -> bool:
        """Stop copy trading permanently."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT strategy_id FROM copy_subscriptions WHERE subscription_id = ?",
                (subscription_id,),
            ).fetchone()
            cursor = conn.execute(
                "UPDATE copy_subscriptions SET status = 'stopped' WHERE subscription_id = ?",
                (subscription_id,),
            )
            if row:
                conn.execute(
                    "UPDATE strategy_profiles SET copiers = MAX(0, copiers - 1) WHERE strategy_id = ?",
                    (row[0],),
                )
            return cursor.rowcount > 0

    def get_subscription(self, subscription_id: str) -> Optional[CopySubscription]:
        """Get a copy subscription."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM copy_subscriptions WHERE subscription_id = ?",
                (subscription_id,),
            ).fetchone()

        if row is None:
            return None
        return CopySubscription(
            subscription_id=row["subscription_id"],
            copier_user_id=row["copier_user_id"],
            strategy_id=row["strategy_id"],
            max_capital=row["max_capital"],
            allocated_capital=row["allocated_capital"],
            status=CopyStatus(row["status"]),
            pnl=row["pnl"],
            trades_copied=row["trades_copied"],
            created_at=row["created_at"],
            paused_at=row["paused_at"],
        )

    def get_user_subscriptions(self, user_id: str) -> list[CopySubscription]:
        """Get all copy subscriptions for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM copy_subscriptions WHERE copier_user_id = ?",
                (user_id,),
            ).fetchall()

        return [
            CopySubscription(
                subscription_id=r["subscription_id"],
                copier_user_id=r["copier_user_id"],
                strategy_id=r["strategy_id"],
                max_capital=r["max_capital"],
                allocated_capital=r["allocated_capital"],
                status=CopyStatus(r["status"]),
                pnl=r["pnl"],
                trades_copied=r["trades_copied"],
            )
            for r in rows
        ]

    # --- Trade Replication ---

    def replicate_trade(
        self,
        subscription_id: str,
        original_trade_id: str,
        market_id: str,
        direction: str,
        size_usd: float,
        entry_price: float,
    ) -> Optional[CopiedTrade]:
        """Replicate a trade for a copy subscriber."""
        sub = self.get_subscription(subscription_id)
        if sub is None or sub.status != CopyStatus.ACTIVE:
            return None

        # Check capital limit
        if sub.allocated_capital + size_usd > sub.max_capital:
            size_usd = sub.max_capital - sub.allocated_capital
            if size_usd <= 0:
                return None

        trade_id = f"ct-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        trade = CopiedTrade(
            trade_id=trade_id,
            subscription_id=subscription_id,
            original_trade_id=original_trade_id,
            market_id=market_id,
            direction=direction,
            size_usd=size_usd,
            entry_price=entry_price,
            timestamp=now,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO copied_trades
                   (trade_id, subscription_id, original_trade_id,
                    market_id, direction, size_usd, entry_price, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (trade_id, subscription_id, original_trade_id,
                 market_id, direction, size_usd, entry_price, now),
            )
            conn.execute(
                """UPDATE copy_subscriptions
                   SET allocated_capital = allocated_capital + ?,
                       trades_copied = trades_copied + 1
                   WHERE subscription_id = ?""",
                (size_usd, subscription_id),
            )

        return trade

    def resolve_copied_trade(self, trade_id: str, pnl: float) -> bool:
        """Resolve a copied trade with P&L."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT subscription_id, size_usd FROM copied_trades WHERE trade_id = ?",
                (trade_id,),
            ).fetchone()
            if row is None:
                return False

            conn.execute(
                "UPDATE copied_trades SET pnl = ? WHERE trade_id = ?",
                (pnl, trade_id),
            )
            conn.execute(
                """UPDATE copy_subscriptions
                   SET pnl = pnl + ?,
                       allocated_capital = MAX(0, allocated_capital - ?)
                   WHERE subscription_id = ?""",
                (pnl, row[1], row[0]),
            )
        return True
