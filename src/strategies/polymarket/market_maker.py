"""Market maker strategy for Polymarket — provide liquidity around fair value."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.polymarket.types import Market, Prediction, TradeDirection

logger = logging.getLogger(__name__)


@dataclass
class MarketMakerConfig:
    """Market maker strategy configuration."""
    spread_width: float = 0.03      # 3% spread around fair value
    min_edge: float = 0.05          # 5% minimum edge
    max_inventory: float = 0.10     # 10% max capital per market
    rebalance_threshold: float = 0.02  # Rebalance when edge shifts 2%


class MarketMakerStrategy:
    """Provide liquidity by placing orders around AI fair value.

    Strategy:
    1. Estimate fair value via ensemble
    2. Place YES order at fair_value - spread/2
    3. Place NO order at fair_value + spread/2
    4. Profit from spread when both sides fill
    """

    def __init__(self, config: Optional[MarketMakerConfig] = None) -> None:
        self.config = config or MarketMakerConfig()

    def generate_signals(
        self, market: Market, prediction: Prediction
    ) -> list[dict[str, object]]:
        """Generate market making signals for a market."""
        if prediction.edge < self.config.min_edge:
            return []

        fair_value = prediction.predicted_probability
        half_spread = self.config.spread_width / 2

        signals: list[dict[str, object]] = []

        # Buy YES below fair value
        yes_price = fair_value - half_spread
        if yes_price > 0.01 and yes_price < market.yes_price:
            signals.append({
                "direction": TradeDirection.YES,
                "price": yes_price,
                "edge": market.yes_price - yes_price,
                "strategy": "market_maker",
            })

        # Buy NO above fair value (YES price perspective)
        no_price = fair_value + half_spread
        if no_price < 0.99 and no_price > market.yes_price:
            signals.append({
                "direction": TradeDirection.NO,
                "price": 1.0 - no_price,
                "edge": no_price - market.yes_price,
                "strategy": "market_maker",
            })

        return signals
