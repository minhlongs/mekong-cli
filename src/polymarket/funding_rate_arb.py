# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Funding rate arbitrage — capture perp-spot and cross-exchange funding spread."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ArbStrategy(Enum):
    CASH_AND_CARRY = "cash_and_carry"
    CROSS_EXCHANGE = "cross_exchange"
    PREDICTION_HEDGE = "prediction_hedge"


@dataclass
class FundingRate:
    exchange: str
    symbol: str
    rate: float
    next_funding_time: Any = None
    predicted_rate: Optional[float] = None
    annualized_pct: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.annualized_pct == 0.0 and self.rate != 0.0:
            self.annualized_pct = self.rate * 3 * 365 * 100

    @property
    def rate_8h(self) -> float:
        return self.rate / (365 * 3)


@dataclass
class CarryTrade:
    long_exchange: str
    short_exchange: str
    symbol: str
    long_rate: float
    short_rate: float
    net_funding_rate: float = 0.0
    annualized_yield: float = 0.0
    spread: float = 0.0
    size_usd: float = 0.0
    entry_basis: float = 0.0
    status: str = "pending"
    opened_at: str = ""

    def __post_init__(self) -> None:
        if not self.spread:
            self.spread = abs(self.short_rate - self.long_rate)
        if not self.annualized_yield:
            self.annualized_yield = self.spread

    @property
    def is_profitable(self) -> bool:
        return self.annualized_yield >= 0.05


@dataclass
class ArbConfig:
    min_annualized_yield: float = 0.15
    max_position_usd: float = 50.0
    max_basis_pct: float = 0.005
    rebalance_threshold_pct: float = 0.02
    risk_budget_pct: float = 0.20


class FundingRateMonitor:
    def __init__(self, config: Optional[ArbConfig] = None, exchanges: Optional[list[str]] = None) -> None:
        self.config = config or ArbConfig()
        self.exchanges = exchanges or ["hyperliquid", "dydx", "binance"]
        self._rates: dict[str, dict[str, FundingRate]] = {}

    @property
    def monitored_symbols(self) -> list[str]:
        return list(self._rates.keys())

    def clear_rates(self) -> None:
        self._rates.clear()

    def update_rate(self, exchange: str, symbol: str, rate: float, next_funding_time: Optional[float] = None) -> FundingRate:
        fr = FundingRate(exchange=exchange, symbol=symbol, rate=rate, next_funding_time=next_funding_time or (time.time() + 28800))
        self._rates.setdefault(symbol, {})[exchange] = fr
        return fr

    def update_rates(self, rates: list[FundingRate]) -> None:
        for r in rates:
            self._rates.setdefault(r.symbol, {})[r.exchange] = r

    def get_rate(self, symbol: str, exchange: str) -> Optional[FundingRate]:
        return self._rates.get(symbol, {}).get(exchange)

    def find_carry_trades(self, min_yield: Optional[float] = None) -> list[CarryTrade]:
        threshold = min_yield if min_yield is not None else self.config.min_annualized_yield
        opportunities: list[CarryTrade] = []
        for symbol, exchange_rates in self._rates.items():
            rates = list(exchange_rates.values())
            for i in range(len(rates)):
                for j in range(i + 1, len(rates)):
                    r1, r2 = rates[i], rates[j]
                    spread = abs(r1.rate - r2.rate)
                    if spread >= threshold:
                        long_ex, short_ex = (r1.exchange, r2.exchange) if r1.rate < r2.rate else (r2.exchange, r1.exchange)
                        opportunities.append(CarryTrade(
                            symbol=symbol, long_exchange=long_ex, short_exchange=short_ex,
                            long_rate=min(r1.rate, r2.rate), short_rate=max(r1.rate, r2.rate),
                            net_funding_rate=spread, spread=spread, annualized_yield=spread,
                        ))
        opportunities.sort(key=lambda t: t.annualized_yield, reverse=True)
        return opportunities


class FundingRateArbitrage:
    def __init__(self, capital: float = 200.0, config: Optional[ArbConfig] = None) -> None:
        self.capital = capital
        self.config = config or ArbConfig()
        self.monitor = FundingRateMonitor(config=self.config)
        self.open_trades: list[CarryTrade] = []
        self.total_pnl: float = 0.0

    @property
    def risk_budget(self) -> float:
        return self.capital * self.config.risk_budget_pct

    @property
    def allocated(self) -> float:
        return sum(t.size_usd for t in self.open_trades)

    @property
    def available(self) -> float:
        return max(0.0, self.risk_budget - self.allocated)

    def evaluate_trades(self) -> list[CarryTrade]:
        candidates = self.monitor.find_carry_trades()
        sized: list[CarryTrade] = []
        remaining = self.available
        max_per_trade = self.config.max_position_usd

        for trade in candidates:
            if remaining <= 0:
                break
            size = min(max_per_trade, remaining)
            trade.size_usd = size
            sized.append(trade)
            remaining -= size
        return sized

    def open_trade(self, trade: CarryTrade) -> bool:
        if trade.size_usd > self.available:
            return False
        self.open_trades.append(trade)
        return True

    def close_trade(self, symbol: str, pnl: float) -> bool:
        for i, trade in enumerate(self.open_trades):
            if trade.symbol == symbol:
                self.open_trades.pop(i)
                self.total_pnl += pnl
                return True
        return False


# Alias for backward compatibility
FundingRateArb = FundingRateArbitrage

__all__ = [
    "ArbConfig", "ArbStrategy", "CarryTrade", "FundingRate",
    "FundingRateArb", "FundingRateArbitrage", "FundingRateMonitor",
]
