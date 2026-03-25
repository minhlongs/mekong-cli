"""Tests for PositionTracker — open/close, P&L, drawdown, portfolio state."""

import pytest

from src.polymarket.position_tracker import PositionTracker
from src.polymarket.types import TradeDirection


class TestOpenClose:
    """Test opening and closing positions."""

    def test_open_position(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        pos = tracker.open_position("m1", TradeDirection.YES, 50.0, 0.55)
        assert pos.market_id == "m1"
        assert pos.size_usd == 50.0
        assert tracker.open_position_count == 1

    def test_close_position_win(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.55)
        pnl = tracker.close_position("m1", exit_price=1.0)
        assert pnl is not None
        assert pnl > 0  # Bought YES at 0.55, resolved at 1.0
        assert tracker.open_position_count == 0
        assert tracker.trade_count == 1
        assert tracker.win_count == 1

    def test_close_position_loss(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.55)
        pnl = tracker.close_position("m1", exit_price=0.0)
        assert pnl is not None
        assert pnl < 0
        assert tracker.win_count == 0

    def test_close_no_direction(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.NO, 50.0, 0.55)
        pnl = tracker.close_position("m1", exit_price=0.0)
        assert pnl is not None
        assert pnl > 0  # Bought NO at 0.55, outcome=0.0 → win

    def test_close_nonexistent(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        assert tracker.close_position("nonexistent", 1.0) is None


class TestCapital:
    """Test capital tracking."""

    def test_initial_capital(self) -> None:
        tracker = PositionTracker(initial_capital=200.0)
        assert tracker.current_capital == 200.0

    def test_capital_after_win(self) -> None:
        tracker = PositionTracker(initial_capital=200.0)
        tracker.open_position("m1", TradeDirection.YES, 20.0, 0.50)
        tracker.close_position("m1", exit_price=1.0)
        assert tracker.current_capital > 200.0

    def test_capital_after_loss(self) -> None:
        tracker = PositionTracker(initial_capital=200.0)
        tracker.open_position("m1", TradeDirection.YES, 20.0, 0.50)
        tracker.close_position("m1", exit_price=0.0)
        assert tracker.current_capital < 200.0


class TestDrawdown:
    """Test max drawdown tracking."""

    def test_no_drawdown_initially(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        assert tracker.max_drawdown == 0.0

    def test_drawdown_after_loss(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.YES, 100.0, 0.50)
        tracker.close_position("m1", exit_price=0.0)
        assert tracker.max_drawdown > 0.0

    def test_peak_tracks_high_water(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        # Win → new peak
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.50)
        tracker.close_position("m1", exit_price=1.0)
        assert tracker.peak_capital > 1000.0
        # Loss → drawdown from peak
        tracker.open_position("m2", TradeDirection.YES, 50.0, 0.50)
        tracker.close_position("m2", exit_price=0.0)
        assert tracker.max_drawdown > 0.0


class TestWinRate:
    """Test win rate calculation."""

    def test_zero_trades(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        assert tracker.win_rate == 0.0

    def test_all_wins(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        for i in range(3):
            tracker.open_position(f"m{i}", TradeDirection.YES, 10.0, 0.50)
            tracker.close_position(f"m{i}", exit_price=1.0)
        assert tracker.win_rate == 1.0

    def test_mixed_results(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        # 2 wins
        tracker.open_position("w1", TradeDirection.YES, 10.0, 0.50)
        tracker.close_position("w1", exit_price=1.0)
        tracker.open_position("w2", TradeDirection.YES, 10.0, 0.50)
        tracker.close_position("w2", exit_price=1.0)
        # 1 loss
        tracker.open_position("l1", TradeDirection.YES, 10.0, 0.50)
        tracker.close_position("l1", exit_price=0.0)
        assert abs(tracker.win_rate - 2 / 3) < 1e-10


class TestUnrealizedPnL:
    """Test unrealized P&L."""

    def test_unrealized_updates(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.50)
        tracker.update_prices({"m1": 0.70})
        assert tracker.unrealized_pnl > 0

    def test_total_pnl_combines(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        # Realized win
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.50)
        tracker.close_position("m1", exit_price=1.0)
        # Unrealized position
        tracker.open_position("m2", TradeDirection.YES, 50.0, 0.50)
        tracker.update_prices({"m2": 0.60})
        assert tracker.total_pnl == tracker.realized_pnl + tracker.unrealized_pnl


class TestPortfolioState:
    """Test portfolio state snapshot."""

    def test_snapshot(self) -> None:
        tracker = PositionTracker(initial_capital=200.0)
        state = tracker.get_portfolio_state()
        assert state.capital == 200.0
        assert state.total_trades == 0
        assert state.total_pnl == 0.0

    def test_open_exposure(self) -> None:
        tracker = PositionTracker(initial_capital=1000.0)
        tracker.open_position("m1", TradeDirection.YES, 50.0, 0.50)
        tracker.open_position("m2", TradeDirection.NO, 30.0, 0.60)
        assert tracker.open_exposure == 80.0
