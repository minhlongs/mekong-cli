"""Tests for OrderManager — tracking, fills, cancellations, persistence."""

import os
import sqlite3
import tempfile

import pytest

from src.polymarket.clob_client import OrderResponse, OrderSide
from src.polymarket.order_manager import OrderManager
from src.polymarket.types import OrderStatus, TradeDirection


def _make_response(
    order_id: str = "ord-001",
    status: OrderStatus = OrderStatus.FILLED,
) -> OrderResponse:
    return OrderResponse(
        order_id=order_id,
        market_id="m1",
        side=OrderSide.BUY,
        direction=TradeDirection.YES,
        size_usd=10.0,
        price=0.55,
        status=status,
    )


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


class TestTrackOrder:
    """Test order tracking."""

    def test_track_filled_order(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        resp = _make_response(status=OrderStatus.FILLED)
        order = mgr.track_order(resp)
        assert order.status == OrderStatus.FILLED
        assert order.filled_at is not None
        assert len(mgr.filled_orders) == 1
        assert len(mgr.open_orders) == 0

    def test_track_pending_order(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        resp = _make_response(order_id="pending-1", status=OrderStatus.PENDING)
        order = mgr.track_order(resp)
        assert order.status == OrderStatus.PENDING
        assert len(mgr.open_orders) == 1
        assert "pending-1" in mgr.open_orders


class TestMarkFilled:
    """Test marking open orders as filled."""

    def test_mark_filled_moves_to_filled(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="p1", status=OrderStatus.PENDING))
        filled = mgr.mark_filled("p1", fill_price=0.60)
        assert filled is not None
        assert filled.status == OrderStatus.FILLED
        assert filled.price == 0.60
        assert len(mgr.open_orders) == 0
        assert len(mgr.filled_orders) == 1

    def test_mark_filled_nonexistent(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        assert mgr.mark_filled("nonexistent", 0.50) is None


class TestMarkCancelled:
    """Test cancelling orders."""

    def test_cancel_open_order(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="c1", status=OrderStatus.PENDING))
        cancelled = mgr.mark_cancelled("c1")
        assert cancelled is not None
        assert cancelled.status == OrderStatus.CANCELLED
        assert len(mgr.open_orders) == 0

    def test_cancel_nonexistent(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        assert mgr.mark_cancelled("nonexistent") is None


class TestResolveOrder:
    """Test order resolution with P&L."""

    def test_resolve_yes_win(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="r1", status=OrderStatus.FILLED))
        resolved = mgr.resolve_order("r1", outcome=1.0)
        assert resolved is not None
        assert resolved.pnl is not None
        assert resolved.pnl > 0  # Bought YES at 0.55, outcome=1.0

    def test_resolve_yes_lose(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="r2", status=OrderStatus.FILLED))
        resolved = mgr.resolve_order("r2", outcome=0.0)
        assert resolved is not None
        assert resolved.pnl < 0  # Bought YES at 0.55, outcome=0.0

    def test_total_pnl(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="t1", status=OrderStatus.FILLED))
        mgr.track_order(_make_response(order_id="t2", status=OrderStatus.FILLED))
        mgr.resolve_order("t1", outcome=1.0)
        mgr.resolve_order("t2", outcome=0.0)
        pnl = mgr.get_total_pnl()
        # t1 wins, t2 loses — net should be calculable
        assert isinstance(pnl, float)


class TestPersistence:
    """Test SQLite persistence."""

    def test_order_persisted(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="persist-1"))
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT * FROM orders").fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "persist-1"

    def test_open_exposure(self, db_path: str) -> None:
        mgr = OrderManager(db_path)
        mgr.track_order(_make_response(order_id="e1", status=OrderStatus.PENDING))
        mgr.track_order(_make_response(order_id="e2", status=OrderStatus.PENDING))
        assert mgr.get_open_exposure() == 20.0
