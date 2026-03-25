"""Order manager — tracks open orders, fills, and cancellations."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.polymarket.clob_client import OrderResponse, OrderSide
from src.polymarket.types import OrderStatus, TradeDirection

logger = logging.getLogger(__name__)


@dataclass
class ManagedOrder:
    """An order tracked by the order manager."""
    order_id: str
    market_id: str
    side: OrderSide
    direction: TradeDirection
    size_usd: float
    price: float
    status: OrderStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    pnl: Optional[float] = None


class OrderManager:
    """Manages the lifecycle of orders from placement through resolution."""

    def __init__(self, db_path: str = "data/algo-trade.db") -> None:
        self.db_path = db_path
        self.open_orders: dict[str, ManagedOrder] = {}
        self.filled_orders: list[ManagedOrder] = []
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create orders table if not exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    market_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    size_usd REAL NOT NULL,
                    price REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT,
                    filled_at TEXT,
                    cancelled_at TEXT,
                    pnl REAL
                )
            """)

    def track_order(self, response: OrderResponse) -> ManagedOrder:
        """Start tracking an order from a CLOB response."""
        order = ManagedOrder(
            order_id=response.order_id,
            market_id=response.market_id,
            side=response.side,
            direction=response.direction,
            size_usd=response.size_usd,
            price=response.price,
            status=response.status,
            created_at=response.timestamp,
        )

        if response.status == OrderStatus.FILLED:
            order.filled_at = datetime.utcnow()
            self.filled_orders.append(order)
        elif response.status == OrderStatus.PENDING:
            self.open_orders[response.order_id] = order

        self._persist_order(order)
        logger.info(
            "Tracking order %s: %s %s $%.2f status=%s",
            order.order_id, order.direction.value,
            order.market_id[:8], order.size_usd, order.status.value,
        )
        return order

    def mark_filled(self, order_id: str, fill_price: float) -> Optional[ManagedOrder]:
        """Mark an open order as filled."""
        order = self.open_orders.pop(order_id, None)
        if order is None:
            logger.warning("Order %s not found in open orders", order_id)
            return None

        order.status = OrderStatus.FILLED
        order.filled_at = datetime.utcnow()
        order.price = fill_price
        self.filled_orders.append(order)
        self._persist_order(order)
        return order

    def mark_cancelled(self, order_id: str) -> Optional[ManagedOrder]:
        """Mark an open order as cancelled."""
        order = self.open_orders.pop(order_id, None)
        if order is None:
            return None

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        self._persist_order(order)
        return order

    def resolve_order(self, order_id: str, outcome: float) -> Optional[ManagedOrder]:
        """Resolve a filled order with the market outcome and calculate P&L."""
        for order in self.filled_orders:
            if order.order_id == order_id:
                if order.direction == TradeDirection.YES:
                    order.pnl = (outcome - order.price) * order.size_usd
                else:
                    order.pnl = (order.price - outcome) * order.size_usd
                self._persist_order(order)
                return order
        return None

    def get_open_orders(self) -> list[ManagedOrder]:
        """Return all open orders."""
        return list(self.open_orders.values())

    def get_filled_orders(self) -> list[ManagedOrder]:
        """Return all filled orders."""
        return list(self.filled_orders)

    def get_total_pnl(self) -> float:
        """Calculate total P&L from resolved orders."""
        return sum(o.pnl for o in self.filled_orders if o.pnl is not None)

    def get_open_exposure(self) -> float:
        """Total USD in open orders."""
        return sum(o.size_usd for o in self.open_orders.values())

    def _persist_order(self, order: ManagedOrder) -> None:
        """Persist order state to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO orders
                   (order_id, market_id, side, direction, size_usd, price,
                    status, created_at, filled_at, cancelled_at, pnl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order.order_id,
                    order.market_id,
                    order.side.value,
                    order.direction.value,
                    order.size_usd,
                    order.price,
                    order.status.value,
                    order.created_at.isoformat() if order.created_at else None,
                    order.filled_at.isoformat() if order.filled_at else None,
                    order.cancelled_at.isoformat() if order.cancelled_at else None,
                    order.pnl,
                ),
            )
