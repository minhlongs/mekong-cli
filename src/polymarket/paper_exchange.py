"""Paper exchange — simulate trade fills for paper trading."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from src.polymarket.types import (
    OrderStatus,
    PortfolioState,
    Signal,
    Trade,
    TradeDirection,
)

logger = logging.getLogger(__name__)


class PaperExchange:
    """Simulated exchange for paper trading.

    Fills orders instantly at market price. Tracks portfolio state.
    """

    def __init__(self, initial_capital: float = 200.0) -> None:
        self.portfolio = PortfolioState(capital=initial_capital)
        self.trade_history: list[Trade] = []

    def execute_signal(self, signal: Signal) -> Trade:
        """Execute a paper trade from a signal."""
        trade = Trade(
            trade_id=str(uuid.uuid4())[:8],
            market_id=signal.market_id,
            direction=signal.prediction.direction,
            size_usd=signal.position_size_usd,
            entry_price=signal.prediction.market_price,
            status=OrderStatus.FILLED,
            is_paper=True,
        )
        self.portfolio.open_positions.append(trade)
        self.portfolio.total_trades += 1
        self.trade_history.append(trade)
        logger.info(
            "Paper trade: %s %s $%.2f @ %.3f (edge: %.1f%%)",
            trade.direction.value,
            trade.market_id[:8],
            trade.size_usd,
            trade.entry_price,
            signal.prediction.edge * 100,
        )
        return trade

    def resolve_trade(
        self, trade_id: str, outcome: float
    ) -> Optional[Trade]:
        """Resolve a paper trade with the actual outcome (0 or 1)."""
        for trade in self.portfolio.open_positions:
            if trade.trade_id == trade_id:
                trade.exit_price = outcome
                if trade.direction == TradeDirection.YES:
                    trade.pnl = (outcome - trade.entry_price) * trade.size_usd
                else:
                    trade.pnl = (trade.entry_price - outcome) * trade.size_usd

                trade.status = OrderStatus.FILLED
                self.portfolio.total_pnl += trade.pnl or 0.0
                self.portfolio.daily_pnl += trade.pnl or 0.0
                if trade.pnl and trade.pnl > 0:
                    self.portfolio.winning_trades += 1

                self.portfolio.open_positions.remove(trade)
                logger.info(
                    "Resolved: %s P&L=$%.2f (total=$%.2f)",
                    trade.trade_id, trade.pnl, self.portfolio.total_pnl,
                )
                return trade
        return None

    def get_portfolio(self) -> PortfolioState:
        """Return current portfolio state."""
        return self.portfolio

    @property
    def total_pnl(self) -> float:
        return self.portfolio.total_pnl

    @property
    def win_rate(self) -> float:
        return self.portfolio.win_rate

    @property
    def open_position_count(self) -> int:
        return len(self.portfolio.open_positions)
