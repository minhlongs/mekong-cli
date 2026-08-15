"""Funding rate arbitrage — delta-neutral carry trades across CEX/DEX.

Layer 2 revenue stream with separate risk budget:
  1. Monitor funding rates across exchanges
  2. Detect profitable delta-neutral carry trades
  3. Automated execution via CCXT
  4. Separate risk budget from prediction trading
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FundingRate:
    """Funding rate snapshot from an exchange."""
    exchange: str
    symbol: str
    rate: float  # Annualized rate
    next_funding_time: datetime
    timestamp: datetime

    @property
    def rate_8h(self) -> float:
        """8-hour funding rate."""
        return self.rate / (365 * 3)


@dataclass
class CarryTrade:
    """A delta-neutral carry trade opportunity."""
    long_exchange: str
    short_exchange: str
    symbol: str
    long_rate: float
    short_rate: float
    spread: float
    annualized_yield: float
    size_usd: float = 0.0

    @property
    def is_profitable(self) -> bool:
        """Check if carry trade exceeds minimum yield (5% APY)."""
        return self.annualized_yield > 0.05


@dataclass
class ArbConfig:
    """Funding rate arbitrage configuration."""
    min_annualized_yield: float = 0.05  # 5% minimum
    max_position_usd: float = 1000.0
    risk_budget_pct: float = 0.20  # 20% of capital for arb
    exchanges: list[str] = None

    def __post_init__(self) -> None:
        if self.exchanges is None:
            self.exchanges = ["binance", "bybit", "okx"]


class FundingRateMonitor:
    """Monitor funding rates across exchanges for carry opportunities."""

    def __init__(self, config: Optional[ArbConfig] = None) -> None:
        self.config = config or ArbConfig()
        self._rates: dict[str, list[FundingRate]] = {}

    def update_rates(self, rates: list[FundingRate]) -> None:
        """Update funding rate cache."""
        for rate in rates:
            key = rate.symbol
            if key not in self._rates:
                self._rates[key] = []
            self._rates[key].append(rate)

    def find_carry_trades(self) -> list[CarryTrade]:
        """Find profitable delta-neutral carry trade opportunities.

        Strategy: Go long on exchange with negative funding (earn),
        short on exchange with positive funding (earn).
        """
        trades: list[CarryTrade] = []

        for symbol, rates in self._rates.items():
            if len(rates) < 2:
                continue

            # Sort by rate
            sorted_rates = sorted(rates, key=lambda r: r.rate)
            lowest = sorted_rates[0]   # Most negative = best to go long
            highest = sorted_rates[-1]  # Most positive = best to go short

            spread = highest.rate - lowest.rate
            if spread < self.config.min_annualized_yield:
                continue

            trade = CarryTrade(
                long_exchange=lowest.exchange,
                short_exchange=highest.exchange,
                symbol=symbol,
                long_rate=lowest.rate,
                short_rate=highest.rate,
                spread=spread,
                annualized_yield=spread,
            )
            trades.append(trade)

        trades.sort(key=lambda t: t.annualized_yield, reverse=True)
        return trades

    def get_rates_for_symbol(self, symbol: str) -> list[FundingRate]:
        """Get all funding rates for a symbol."""
        return self._rates.get(symbol, [])

    def clear_rates(self) -> None:
        """Clear rate cache."""
        self._rates.clear()

    @property
    def monitored_symbols(self) -> list[str]:
        """Symbols currently being monitored."""
        return list(self._rates.keys())


class FundingRateArbitrage:
    """Execute funding rate arbitrage with risk management."""

    def __init__(
        self,
        capital: float,
        config: Optional[ArbConfig] = None,
    ) -> None:
        self.capital = capital
        self.config = config or ArbConfig()
        self.monitor = FundingRateMonitor(self.config)
        self.open_trades: list[CarryTrade] = []
        self.total_pnl: float = 0.0

    @property
    def risk_budget(self) -> float:
        """Available capital for arbitrage."""
        return self.capital * self.config.risk_budget_pct

    @property
    def allocated(self) -> float:
        """Capital currently allocated to arb trades."""
        return sum(t.size_usd for t in self.open_trades)

    @property
    def available(self) -> float:
        """Available arb capital."""
        return max(0, self.risk_budget - self.allocated)

    def evaluate_trades(self) -> list[CarryTrade]:
        """Find and size carry trades within risk budget."""
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
        """Open a carry trade (paper mode)."""
        if trade.size_usd > self.available:
            return False
        self.open_trades.append(trade)
        logger.info(
            "Arb opened: %s long@%s short@%s $%.2f yield=%.1f%%",
            trade.symbol, trade.long_exchange, trade.short_exchange,
            trade.size_usd, trade.annualized_yield * 100,
        )
        return True

    def close_trade(self, symbol: str, pnl: float) -> bool:
        """Close a carry trade and realize P&L."""
        for i, trade in enumerate(self.open_trades):
            if trade.symbol == symbol:
                self.open_trades.pop(i)
                self.total_pnl += pnl
                return True
        return False
