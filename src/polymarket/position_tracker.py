"""Position tracker — monitors open positions and portfolio state."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.polymarket.types import PortfolioState, TradeDirection

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """An open position in a market."""
    market_id: str
    direction: TradeDirection
    size_usd: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    opened_at: datetime = field(default_factory=datetime.utcnow)

    def update_price(self, new_price: float) -> None:
        """Update current price and recalculate unrealized P&L."""
        self.current_price = new_price
        if self.direction == TradeDirection.YES:
            self.unrealized_pnl = (new_price - self.entry_price) * self.size_usd
        else:
            self.unrealized_pnl = (self.entry_price - new_price) * self.size_usd


class PositionTracker:
    """Tracks all open positions and portfolio metrics."""

    def __init__(self, initial_capital: float = 200.0) -> None:
        self.initial_capital = initial_capital
        self.realized_pnl: float = 0.0
        self.positions: dict[str, Position] = {}
        self.trade_count: int = 0
        self.win_count: int = 0
        self.peak_capital: float = initial_capital
        self.max_drawdown: float = 0.0
        self._daily_pnl: float = 0.0
        self._daily_date: str = datetime.utcnow().strftime("%Y-%m-%d")

    def open_position(
        self,
        market_id: str,
        direction: TradeDirection,
        size_usd: float,
        entry_price: float,
    ) -> Position:
        """Open a new position."""
        position = Position(
            market_id=market_id,
            direction=direction,
            size_usd=size_usd,
            entry_price=entry_price,
            current_price=entry_price,
        )
        self.positions[market_id] = position
        logger.info(
            "Opened position: %s %s $%.2f @ %.4f",
            direction.value, market_id[:8], size_usd, entry_price,
        )
        return position

    def close_position(self, market_id: str, exit_price: float) -> Optional[float]:
        """Close a position and realize P&L."""
        position = self.positions.pop(market_id, None)
        if position is None:
            logger.warning("No open position for %s", market_id)
            return None

        if position.direction == TradeDirection.YES:
            pnl = (exit_price - position.entry_price) * position.size_usd
        else:
            pnl = (position.entry_price - exit_price) * position.size_usd

        self.realized_pnl += pnl
        self.trade_count += 1
        if pnl > 0:
            self.win_count += 1

        # Track daily P&L
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._daily_date:
            self._daily_pnl = 0.0
            self._daily_date = today
        self._daily_pnl += pnl

        # Track drawdown
        current_capital = self.current_capital
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        dd = (self.peak_capital - current_capital) / self.peak_capital if self.peak_capital > 0 else 0.0
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        logger.info(
            "Closed position: %s P&L=$%.2f (total=$%.2f)",
            market_id[:8], pnl, self.realized_pnl,
        )
        return pnl

    def update_prices(self, price_updates: dict[str, float]) -> None:
        """Update current prices for all tracked positions."""
        for market_id, price in price_updates.items():
            if market_id in self.positions:
                self.positions[market_id].update_price(price)

    @property
    def current_capital(self) -> float:
        """Current capital = initial + realized P&L."""
        return self.initial_capital + self.realized_pnl

    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L across open positions."""
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def total_pnl(self) -> float:
        """Realized + unrealized P&L."""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def win_rate(self) -> float:
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count

    @property
    def open_exposure(self) -> float:
        """Total USD in open positions."""
        return sum(p.size_usd for p in self.positions.values())

    @property
    def daily_pnl(self) -> float:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._daily_date:
            return 0.0
        return self._daily_pnl

    def get_portfolio_state(self) -> PortfolioState:
        """Snapshot current portfolio state."""
        return PortfolioState(
            capital=self.current_capital,
            total_trades=self.trade_count,
            winning_trades=self.win_count,
            total_pnl=self.realized_pnl,
            daily_pnl=self.daily_pnl,
            max_drawdown=self.max_drawdown,
        )

    def get_position(self, market_id: str) -> Optional[Position]:
        return self.positions.get(market_id)

    @property
    def open_position_count(self) -> int:
        return len(self.positions)
