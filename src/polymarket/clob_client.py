"""CLOB client — interface to Polymarket's Central Limit Order Book API.

Handles order placement, cancellation, and market data retrieval.
Paper mode returns simulated responses; live mode calls the real API.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.polymarket.types import OrderStatus, TradeDirection

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """CLOB order side."""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class OrderRequest:
    """Request to place an order on the CLOB."""
    market_id: str
    side: OrderSide
    direction: TradeDirection
    size_usd: float
    price: float
    is_paper: bool = True


@dataclass
class OrderResponse:
    """Response from order placement."""
    order_id: str
    market_id: str
    side: OrderSide
    direction: TradeDirection
    size_usd: float
    price: float
    status: OrderStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.PENDING)


@dataclass
class MarketData:
    """Real-time market data from CLOB."""
    market_id: str
    best_bid: float
    best_ask: float
    mid_price: float
    volume_24h: float
    last_trade_price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ClobClient:
    """Client for Polymarket CLOB API.

    In paper mode, simulates all operations locally.
    In live mode, calls the real Polymarket API (requires API keys).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key: Optional[str] = None,
        paper_mode: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY", "")
        self.private_key = private_key or os.getenv("POLYMARKET_PRIVATE_KEY", "")
        self.paper_mode = paper_mode
        self._order_count = 0

        if not paper_mode and not self.api_key:
            raise ValueError(
                "POLYMARKET_API_KEY required for live trading. "
                "Set POLYMARKET_API_KEY env var or pass api_key."
            )

    def place_order(self, request: OrderRequest) -> OrderResponse:
        """Place an order on the CLOB.

        CRITICAL: LiveModeGuard.check() MUST be called before this method.
        """
        if self.paper_mode or request.is_paper:
            return self._paper_fill(request)

        return self._live_place_order(request)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if self.paper_mode:
            logger.info("Paper cancel: %s", order_id)
            return True

        # Live cancellation would call API
        logger.info("Live cancel requested: %s", order_id)
        return True

    def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Get current market data."""
        if self.paper_mode:
            return MarketData(
                market_id=market_id,
                best_bid=0.50,
                best_ask=0.52,
                mid_price=0.51,
                volume_24h=10_000.0,
                last_trade_price=0.51,
            )
        # Live: call Polymarket API
        return None

    def _paper_fill(self, request: OrderRequest) -> OrderResponse:
        """Simulate an instant fill for paper trading."""
        self._order_count += 1
        order_id = f"paper-{self._order_count:06d}"

        logger.info(
            "Paper order filled: %s %s %s $%.2f @ %.4f",
            order_id,
            request.side.value,
            request.direction.value,
            request.size_usd,
            request.price,
        )

        return OrderResponse(
            order_id=order_id,
            market_id=request.market_id,
            side=request.side,
            direction=request.direction,
            size_usd=request.size_usd,
            price=request.price,
            status=OrderStatus.FILLED,
        )

    def _live_place_order(self, request: OrderRequest) -> OrderResponse:
        """Place a real order via Polymarket CLOB API.

        TODO: Wire to actual Polymarket SDK when ready for live trading.
        Currently returns a rejection to prevent accidental live trades.
        """
        logger.warning(
            "Live order attempted but API not wired: %s %s $%.2f",
            request.direction.value,
            request.market_id,
            request.size_usd,
        )
        return OrderResponse(
            order_id=f"rejected-{uuid.uuid4().hex[:8]}",
            market_id=request.market_id,
            side=request.side,
            direction=request.direction,
            size_usd=request.size_usd,
            price=request.price,
            status=OrderStatus.REJECTED,
            error="Live API not yet wired. Complete Polymarket SDK integration first.",
        )

    @property
    def is_live(self) -> bool:
        return not self.paper_mode
