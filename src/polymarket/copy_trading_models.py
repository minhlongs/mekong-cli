# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data structures and database schema for copy trading."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


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


def init_copy_trading_db(db_path: str) -> None:
    """Create copy trading tables if they do not exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
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
