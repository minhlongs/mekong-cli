"""Kelly criterion position sizer — half-Kelly with risk caps."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.polymarket.types import Prediction, Signal, TradeDirection

logger = logging.getLogger(__name__)


@dataclass
class SizerConfig:
    """Position sizing configuration."""
    use_half_kelly: bool = True
    max_position_pct: float = 0.10   # 10% of capital max per position
    min_edge: float = 0.02           # 2% minimum edge to size


class KellyPositionSizer:
    """Half-Kelly position sizing with capital caps.

    Kelly formula: f* = (p * b - q) / b
    Where:
        p = probability of winning
        q = 1 - p = probability of losing
        b = odds (payout ratio)

    Half-Kelly: f = f* / 2 (reduces variance)
    """

    def __init__(self, config: SizerConfig | None = None) -> None:
        self.config = config or SizerConfig()

    def calculate_kelly(self, prediction: Prediction) -> float:
        """Calculate Kelly fraction for a prediction.

        Returns fraction of capital to bet (0.0 to 1.0).
        """
        if prediction.edge <= 0:
            return 0.0

        if prediction.edge < self.config.min_edge:
            return 0.0

        p = prediction.predicted_probability
        if prediction.direction == TradeDirection.NO:
            p = 1.0 - p

        market_price = prediction.market_price
        if prediction.direction == TradeDirection.NO:
            market_price = 1.0 - market_price

        # Avoid division by zero
        if market_price <= 0 or market_price >= 1.0:
            return 0.0

        # Odds = payout ratio (binary market: 1/price - 1)
        b = (1.0 / market_price) - 1.0
        if b <= 0:
            return 0.0

        q = 1.0 - p

        # Full Kelly: f* = (p * b - q) / b
        full_kelly = (p * b - q) / b

        if full_kelly <= 0:
            return 0.0

        # Half-Kelly to reduce variance
        if self.config.use_half_kelly:
            fraction = full_kelly / 2.0
        else:
            fraction = full_kelly

        # Cap at max position percentage
        fraction = min(fraction, self.config.max_position_pct)

        return fraction

    def size_signal(self, prediction: Prediction, capital: float) -> Signal:
        """Create a sized signal from a prediction."""
        kelly = self.calculate_kelly(prediction)
        position_usd = kelly * capital

        # Cap at max position
        max_usd = capital * self.config.max_position_pct
        position_usd = min(position_usd, max_usd)

        return Signal(
            prediction=prediction,
            kelly_fraction=kelly,
            position_size_usd=position_usd,
            expected_value=prediction.edge * position_usd,
        )

    def size_signals(
        self, predictions: list[Prediction], capital: float
    ) -> list[Signal]:
        """Size multiple predictions and return ranked signals."""
        signals: list[Signal] = []
        for pred in predictions:
            signal = self.size_signal(pred, capital)
            if signal.kelly_fraction > 0:
                signals.append(signal)

        # Sort by expected value descending
        signals.sort(key=lambda s: s.expected_value, reverse=True)
        for rank, sig in enumerate(signals, 1):
            sig.rank = rank

        return signals
