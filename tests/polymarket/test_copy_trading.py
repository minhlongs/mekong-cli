"""Tests for copy trading — strategies, subscriptions, trade replication."""

import os
import tempfile

import pytest

from src.polymarket.copy_trading import CopyStatus, CopyTradingEngine


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def engine(db_path):
    return CopyTradingEngine(db_path)


class TestStrategyProfiles:
    def test_register_strategy(self, engine) -> None:
        s = engine.register_strategy("Mean Reversion", "Buy dips", "author_1")
        assert s.strategy_id.startswith("strat-")
        assert s.name == "Mean Reversion"

    def test_list_strategies(self, engine) -> None:
        engine.register_strategy("S1", "desc", "a1")
        engine.register_strategy("S2", "desc", "a2")
        strategies = engine.list_strategies()
        assert len(strategies) == 2

    def test_get_strategy(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        found = engine.get_strategy(s.strategy_id)
        assert found is not None
        assert found.name == "S1"

    def test_get_nonexistent(self, engine) -> None:
        assert engine.get_strategy("nonexistent") is None

    def test_update_stats(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        engine.update_strategy_stats(s.strategy_id, 0.65, 100, 12.5, 1.8, 0.05)
        updated = engine.get_strategy(s.strategy_id)
        assert updated.win_rate == 0.65
        assert updated.total_trades == 100


class TestCopySubscriptions:
    def test_subscribe(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("copier_1", s.strategy_id, max_capital=500.0)
        assert sub is not None
        assert sub.status == CopyStatus.ACTIVE
        assert sub.max_capital == 500.0

    def test_subscribe_invalid_strategy(self, engine) -> None:
        assert engine.subscribe("c1", "nonexistent", 500.0) is None

    def test_pause_resume(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 500.0)
        assert engine.pause(sub.subscription_id)
        paused = engine.get_subscription(sub.subscription_id)
        assert paused.status == CopyStatus.PAUSED
        assert engine.resume(sub.subscription_id)
        resumed = engine.get_subscription(sub.subscription_id)
        assert resumed.status == CopyStatus.ACTIVE

    def test_stop(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 500.0)
        assert engine.stop(sub.subscription_id)
        stopped = engine.get_subscription(sub.subscription_id)
        assert stopped.status == CopyStatus.STOPPED

    def test_copier_count_increments(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        engine.subscribe("c1", s.strategy_id, 500.0)
        engine.subscribe("c2", s.strategy_id, 300.0)
        updated = engine.get_strategy(s.strategy_id)
        assert updated.copiers == 2

    def test_get_user_subscriptions(self, engine) -> None:
        s1 = engine.register_strategy("S1", "desc", "a1")
        s2 = engine.register_strategy("S2", "desc", "a2")
        engine.subscribe("c1", s1.strategy_id, 500.0)
        engine.subscribe("c1", s2.strategy_id, 300.0)
        subs = engine.get_user_subscriptions("c1")
        assert len(subs) == 2


class TestTradeReplication:
    def test_replicate_trade(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 500.0)
        trade = engine.replicate_trade(
            sub.subscription_id, "orig_001", "m1", "YES", 50.0, 0.55
        )
        assert trade is not None
        assert trade.size_usd == 50.0
        updated = engine.get_subscription(sub.subscription_id)
        assert updated.trades_copied == 1
        assert updated.allocated_capital == 50.0

    def test_capital_limit_respected(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 100.0)
        engine.replicate_trade(sub.subscription_id, "o1", "m1", "YES", 80.0, 0.5)
        # Only 20 remaining
        trade = engine.replicate_trade(sub.subscription_id, "o2", "m2", "YES", 50.0, 0.5)
        assert trade is not None
        assert trade.size_usd == 20.0  # Capped to remaining

    def test_no_capital_returns_none(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 50.0)
        engine.replicate_trade(sub.subscription_id, "o1", "m1", "YES", 50.0, 0.5)
        result = engine.replicate_trade(sub.subscription_id, "o2", "m2", "YES", 10.0, 0.5)
        assert result is None

    def test_paused_blocks_replication(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 500.0)
        engine.pause(sub.subscription_id)
        result = engine.replicate_trade(sub.subscription_id, "o1", "m1", "YES", 50.0, 0.5)
        assert result is None

    def test_resolve_trade(self, engine) -> None:
        s = engine.register_strategy("S1", "desc", "a1")
        sub = engine.subscribe("c1", s.strategy_id, 500.0)
        trade = engine.replicate_trade(sub.subscription_id, "o1", "m1", "YES", 50.0, 0.55)
        assert engine.resolve_copied_trade(trade.trade_id, pnl=10.0)
        updated = engine.get_subscription(sub.subscription_id)
        assert updated.pnl == 10.0
