"""Core types for the CashClaw prediction trading system."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class TradeDirection(enum.Enum):
    """Direction of a prediction trade."""
    YES = "YES"
    NO = "NO"


class OrderStatus(enum.Enum):
    """Status of an order."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class CircuitBreakerState(enum.Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Trading halted
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class Market:
    """A prediction market opportunity."""
    market_id: str
    question: str
    outcomes: list[str]
    volume_24h: float
    end_date: datetime
    yes_price: float
    no_price: float
    category: str = ""
    slug: str = ""

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return abs(self.yes_price + self.no_price - 1.0)

    @property
    def days_to_resolution(self) -> float:
        """Days until market resolves."""
        delta = self.end_date - datetime.utcnow()
        return max(0.0, delta.total_seconds() / 86400)


@dataclass
class Prediction:
    """AI prediction for a market."""
    market_id: str
    question: str
    predicted_probability: float
    market_price: float
    edge: float
    confidence: float
    model_used: str
    ensemble_agreement: float
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def direction(self) -> TradeDirection:
        """Recommended trade direction based on edge."""
        if self.predicted_probability > self.market_price:
            return TradeDirection.YES
        return TradeDirection.NO


@dataclass
class Signal:
    """Ranked trading signal from prediction pipeline."""
    prediction: Prediction
    kelly_fraction: float
    position_size_usd: float
    expected_value: float
    rank: int = 0

    @property
    def market_id(self) -> str:
        return self.prediction.market_id


@dataclass
class Trade:
    """A completed or pending trade."""
    trade_id: str
    market_id: str
    direction: TradeDirection
    size_usd: float
    entry_price: float
    status: OrderStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    is_paper: bool = True

    @property
    def is_resolved(self) -> bool:
        return self.exit_price is not None


@dataclass
class PortfolioState:
    """Current portfolio snapshot."""
    capital: float
    open_positions: list[Trade] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    @property
    def capital_with_pnl(self) -> float:
        return self.capital + self.total_pnl


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    allowed: bool
    reason: str
    max_position_size: float = 0.0


@dataclass
class DailyReport:
    """Daily performance metrics."""
    date: str
    total_trades: int
    winning_trades: int
    pnl: float
    brier_score: float
    win_rate: float
    avg_edge: float
    sharpe_ratio: float
    max_drawdown: float
    calibration_ok: bool
