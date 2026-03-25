"""Market scanner — filters Polymarket markets for DNA strategy criteria."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.polymarket.types import Market

logger = logging.getLogger(__name__)


@dataclass
class ScannerFilters:
    """Filter criteria for market scanning (DNA strategy)."""
    min_volume_24h: float = 1_000.0    # $1K minimum
    max_volume_24h: float = 100_000.0  # $100K max (long-tail, less arb-saturated)
    min_days_to_resolution: float = 7.0
    max_days_to_resolution: float = 30.0
    min_outcomes: int = 2
    exclude_price_markets: bool = True  # LLM has no edge on BTC price
    min_spread: float = 0.0
    max_spread: float = 0.10           # 10% max spread


# Keywords indicating price/numeric prediction markets (no LLM edge)
PRICE_MARKET_KEYWORDS: list[str] = [
    "price", "btc", "eth", "bitcoin", "ethereum", "above $",
    "below $", "stock", "nasdaq", "s&p", "dow jones",
    "interest rate", "cpi", "gdp", "inflation",
]


class MarketScanner:
    """Scans and filters Polymarket markets for tradeable opportunities."""

    def __init__(
        self,
        filters: Optional[ScannerFilters] = None,
        api_client: Optional[object] = None,
    ) -> None:
        self.filters = filters or ScannerFilters()
        self.api_client = api_client

    def scan(self, markets: list[Market]) -> list[Market]:
        """Apply all filters and return qualifying markets."""
        filtered = markets
        filtered = self._filter_volume(filtered)
        filtered = self._filter_resolution_window(filtered)
        filtered = self._filter_outcomes(filtered)
        filtered = self._filter_spread(filtered)
        if self.filters.exclude_price_markets:
            filtered = self._filter_price_markets(filtered)
        logger.info(
            "MarketScanner: %d/%d markets passed filters",
            len(filtered), len(markets),
        )
        return filtered

    def _filter_volume(self, markets: list[Market]) -> list[Market]:
        """Filter by 24h volume: $1K–$100K sweet spot."""
        return [
            m for m in markets
            if self.filters.min_volume_24h <= m.volume_24h <= self.filters.max_volume_24h
        ]

    def _filter_resolution_window(self, markets: list[Market]) -> list[Market]:
        """Filter by resolution window: 7–30 days."""
        return [
            m for m in markets
            if self.filters.min_days_to_resolution
            <= m.days_to_resolution
            <= self.filters.max_days_to_resolution
        ]

    def _filter_outcomes(self, markets: list[Market]) -> list[Market]:
        """Filter by minimum outcome count."""
        return [
            m for m in markets
            if len(m.outcomes) >= self.filters.min_outcomes
        ]

    def _filter_spread(self, markets: list[Market]) -> list[Market]:
        """Filter by bid-ask spread."""
        return [
            m for m in markets
            if m.spread <= self.filters.max_spread
        ]

    def _filter_price_markets(self, markets: list[Market]) -> list[Market]:
        """Exclude price/numeric markets where LLM has no edge."""
        result: list[Market] = []
        for m in markets:
            question_lower = m.question.lower()
            is_price = any(kw in question_lower for kw in PRICE_MARKET_KEYWORDS)
            if not is_price:
                result.append(m)
        return result

    @staticmethod
    def is_price_market(question: str) -> bool:
        """Check if a market question is about price prediction."""
        question_lower = question.lower()
        return any(kw in question_lower for kw in PRICE_MARKET_KEYWORDS)
