"""Tests for funding rate arbitrage — monitor, carry trades, risk budget."""

from datetime import datetime, timedelta

import pytest

from src.polymarket.funding_rate_arb import (
    ArbConfig,
    CarryTrade,
    FundingRate,
    FundingRateArbitrage,
    FundingRateMonitor,
)


def _make_rate(
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    rate: float = 0.10,
) -> FundingRate:
    return FundingRate(
        exchange=exchange,
        symbol=symbol,
        rate=rate,
        next_funding_time=datetime.utcnow() + timedelta(hours=8),
        timestamp=datetime.utcnow(),
    )


class TestFundingRateMonitor:
    def test_update_rates(self) -> None:
        monitor = FundingRateMonitor()
        monitor.update_rates([
            _make_rate("binance", "BTC/USDT", 0.10),
            _make_rate("bybit", "BTC/USDT", -0.05),
        ])
        assert "BTC/USDT" in monitor.monitored_symbols

    def test_find_carry_trades(self) -> None:
        monitor = FundingRateMonitor(ArbConfig(min_annualized_yield=0.05))
        monitor.update_rates([
            _make_rate("binance", "BTC/USDT", 0.15),
            _make_rate("bybit", "BTC/USDT", -0.05),
        ])
        trades = monitor.find_carry_trades()
        assert len(trades) == 1
        assert trades[0].long_exchange == "bybit"  # Lowest rate → go long
        assert trades[0].short_exchange == "binance"  # Highest rate → go short
        assert trades[0].annualized_yield == pytest.approx(0.20)

    def test_no_trades_small_spread(self) -> None:
        monitor = FundingRateMonitor(ArbConfig(min_annualized_yield=0.10))
        monitor.update_rates([
            _make_rate("binance", "BTC/USDT", 0.05),
            _make_rate("bybit", "BTC/USDT", 0.03),
        ])
        assert monitor.find_carry_trades() == []

    def test_clear_rates(self) -> None:
        monitor = FundingRateMonitor()
        monitor.update_rates([_make_rate()])
        monitor.clear_rates()
        assert monitor.monitored_symbols == []

    def test_8h_rate(self) -> None:
        rate = _make_rate(rate=0.365)  # ~0.0333% per 8h
        assert rate.rate_8h == pytest.approx(0.365 / (365 * 3), rel=0.01)


class TestFundingRateArbitrage:
    def test_risk_budget(self) -> None:
        arb = FundingRateArbitrage(capital=10_000, config=ArbConfig(risk_budget_pct=0.20))
        assert arb.risk_budget == 2_000

    def test_open_trade(self) -> None:
        arb = FundingRateArbitrage(capital=10_000)
        trade = CarryTrade(
            long_exchange="bybit", short_exchange="binance",
            symbol="BTC/USDT", long_rate=-0.05, short_rate=0.15,
            spread=0.20, annualized_yield=0.20, size_usd=500.0,
        )
        assert arb.open_trade(trade) is True
        assert arb.allocated == 500.0

    def test_close_trade(self) -> None:
        arb = FundingRateArbitrage(capital=10_000)
        trade = CarryTrade(
            long_exchange="bybit", short_exchange="binance",
            symbol="BTC/USDT", long_rate=-0.05, short_rate=0.15,
            spread=0.20, annualized_yield=0.20, size_usd=500.0,
        )
        arb.open_trade(trade)
        assert arb.close_trade("BTC/USDT", pnl=25.0)
        assert arb.total_pnl == 25.0
        assert arb.allocated == 0.0

    def test_exceeds_budget_rejected(self) -> None:
        arb = FundingRateArbitrage(capital=1_000, config=ArbConfig(risk_budget_pct=0.10))
        # Budget = $100
        trade = CarryTrade(
            long_exchange="a", short_exchange="b",
            symbol="X", long_rate=0, short_rate=0.1,
            spread=0.1, annualized_yield=0.1, size_usd=200.0,
        )
        assert arb.open_trade(trade) is False

    def test_evaluate_trades(self) -> None:
        arb = FundingRateArbitrage(capital=10_000)
        arb.monitor.update_rates([
            _make_rate("binance", "BTC/USDT", 0.15),
            _make_rate("bybit", "BTC/USDT", -0.05),
        ])
        sized = arb.evaluate_trades()
        assert len(sized) >= 1
        assert all(t.size_usd > 0 for t in sized)

    def test_carry_trade_is_profitable(self) -> None:
        trade = CarryTrade(
            long_exchange="a", short_exchange="b",
            symbol="X", long_rate=0, short_rate=0.1,
            spread=0.1, annualized_yield=0.10,
        )
        assert trade.is_profitable is True

        low = CarryTrade(
            long_exchange="a", short_exchange="b",
            symbol="X", long_rate=0, short_rate=0.01,
            spread=0.01, annualized_yield=0.01,
        )
        assert low.is_profitable is False
