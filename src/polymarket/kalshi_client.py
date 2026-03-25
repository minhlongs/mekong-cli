"""Kalshi client — multi-market expansion to Kalshi event contracts.

Reuses the same PredictionLoop pipeline (model-agnostic).
Enables cross-market arbitrage between Polymarket and Kalshi.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.polymarket.types import Market

logger = logging.getLogger(__name__)


@dataclass
class KalshiMarket:
    """A Kalshi event contract."""
    event_ticker: str
    title: str
    category: str
    yes_price: float
    no_price: float
    volume: float
    end_date: datetime
    status: str = "active"

    def to_market(self) -> Market:
        """Convert to unified Market type for pipeline."""
        return Market(
            market_id=f"kalshi:{self.event_ticker}",
            question=self.title,
            outcomes=["Yes", "No"],
            volume_24h=self.volume,
            end_date=self.end_date,
            yes_price=self.yes_price,
            no_price=self.no_price,
            category=self.category,
        )


@dataclass
class ArbitrageOpportunity:
    """Cross-market arbitrage between Polymarket and Kalshi."""
    polymarket_id: str
    kalshi_ticker: str
    question: str
    poly_yes_price: float
    kalshi_yes_price: float
    spread: float
    direction: str  # "buy_poly_sell_kalshi" or "buy_kalshi_sell_poly"
    expected_profit_pct: float

    @property
    def is_profitable(self) -> bool:
        """Check if spread exceeds transaction costs (~2%)."""
        return self.expected_profit_pct > 0.02


class KalshiClient:
    """Client for Kalshi event contracts API.

    Paper mode simulates responses; live mode requires API keys.
    """

    def __init__(
        self,
        api_key: str = "",
        paper_mode: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("KALSHI_API_KEY", "")
        self.paper_mode = paper_mode

        if not paper_mode and not self.api_key:
            raise ValueError("KALSHI_API_KEY required for live Kalshi trading")

    def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
    ) -> list[KalshiMarket]:
        """Fetch active Kalshi markets.

        In paper mode, returns empty list (no mock data).
        In live mode, calls Kalshi API.
        """
        if self.paper_mode:
            return []

        # TODO: Wire to Kalshi REST API when ready
        logger.info("Kalshi API not yet wired")
        return []

    def get_market(self, event_ticker: str) -> Optional[KalshiMarket]:
        """Fetch a specific Kalshi market."""
        if self.paper_mode:
            return None
        return None

    def to_unified_markets(self, kalshi_markets: list[KalshiMarket]) -> list[Market]:
        """Convert Kalshi markets to unified Market type for the pipeline."""
        return [km.to_market() for km in kalshi_markets]


class CrossMarketArbitrage:
    """Detect and execute cross-market arbitrage opportunities."""

    def __init__(
        self,
        min_spread: float = 0.03,  # 3% minimum spread
    ) -> None:
        self.min_spread = min_spread

    def find_opportunities(
        self,
        poly_markets: list[Market],
        kalshi_markets: list[KalshiMarket],
    ) -> list[ArbitrageOpportunity]:
        """Find arbitrage opportunities between Polymarket and Kalshi.

        Matches markets by question similarity and compares prices.
        """
        opportunities: list[ArbitrageOpportunity] = []

        # Build lookup by normalized question
        kalshi_by_question: dict[str, KalshiMarket] = {}
        for km in kalshi_markets:
            key = km.title.lower().strip()
            kalshi_by_question[key] = km

        for pm in poly_markets:
            key = pm.question.lower().strip()
            km = kalshi_by_question.get(key)
            if km is None:
                continue

            spread = abs(pm.yes_price - km.yes_price)
            if spread < self.min_spread:
                continue

            if pm.yes_price < km.yes_price:
                direction = "buy_poly_sell_kalshi"
                profit = km.yes_price - pm.yes_price
            else:
                direction = "buy_kalshi_sell_poly"
                profit = pm.yes_price - km.yes_price

            opp = ArbitrageOpportunity(
                polymarket_id=pm.market_id,
                kalshi_ticker=km.event_ticker,
                question=pm.question,
                poly_yes_price=pm.yes_price,
                kalshi_yes_price=km.yes_price,
                spread=spread,
                direction=direction,
                expected_profit_pct=profit,
            )
            opportunities.append(opp)

        # Sort by profit descending
        opportunities.sort(key=lambda o: o.expected_profit_pct, reverse=True)
        return opportunities
