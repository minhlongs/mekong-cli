"""Prediction executor — bridges prediction signals to order execution.

Pipeline: PredictionLoop → RiskManager → KellyPositionSizer →
          LiveModeGuard → ClobClient → OrderManager → PositionTracker
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from src.polymarket.clob_client import ClobClient, OrderRequest, OrderSide
from src.polymarket.kelly_position_sizer import KellyPositionSizer
from src.polymarket.live_mode_guard import GuardConfig, LiveModeGuard
from src.polymarket.order_manager import OrderManager
from src.polymarket.position_tracker import PositionTracker
from src.polymarket.risk_manager import RiskManager
from src.polymarket.types import (
    OrderStatus,
    Signal,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a prediction signal."""
    signal: Signal
    order_id: Optional[str] = None
    status: str = "skipped"
    reason: str = ""
    pnl: Optional[float] = None


class PredictionExecutor:
    """Executes trading signals through the full pipeline.

    Receives ranked signals from PredictionLoop, applies risk checks,
    sizes positions, and executes via ClobClient.
    """

    def __init__(
        self,
        risk_manager: RiskManager,
        sizer: KellyPositionSizer,
        clob_client: ClobClient,
        order_manager: OrderManager,
        position_tracker: PositionTracker,
        guard_config: Optional[GuardConfig] = None,
        on_trade: Optional[Callable[[ExecutionResult], None]] = None,
    ) -> None:
        self.risk_manager = risk_manager
        self.sizer = sizer
        self.clob_client = clob_client
        self.order_manager = order_manager
        self.position_tracker = position_tracker
        self.guard = LiveModeGuard(risk_manager, guard_config)
        self.on_trade = on_trade

    def execute_signal(self, signal: Signal) -> ExecutionResult:
        """Execute a single trading signal through the full pipeline.

        Steps:
        1. Size position via Kelly criterion
        2. Risk check via RiskManager
        3. Safety check via LiveModeGuard (for live trades)
        4. Place order via ClobClient
        5. Track order via OrderManager
        6. Update position via PositionTracker
        """
        # 1. Size the signal
        sized = self.sizer.size_signal(
            signal.prediction,
            self.position_tracker.current_capital,
        )
        signal.kelly_fraction = sized.kelly_fraction
        signal.position_size_usd = sized.position_size_usd

        if signal.kelly_fraction <= 0:
            return ExecutionResult(
                signal=signal,
                status="skipped",
                reason="Kelly fraction is zero — no edge",
            )

        # 2. Risk check
        risk_check = self.risk_manager.check_trade(signal)
        if not risk_check.allowed:
            return ExecutionResult(
                signal=signal,
                status="blocked",
                reason=risk_check.reason,
            )

        # 3. Live mode guard (for non-paper trades)
        if not self.clob_client.paper_mode:
            guard_check = self.guard.check(signal)
            if not guard_check.allowed:
                return ExecutionResult(
                    signal=signal,
                    status="blocked",
                    reason=guard_check.reason,
                )

        # 4. Place order
        order_request = OrderRequest(
            market_id=signal.market_id,
            side=OrderSide.BUY,
            direction=signal.prediction.direction,
            size_usd=signal.position_size_usd,
            price=signal.prediction.market_price,
            is_paper=self.clob_client.paper_mode,
        )

        order_response = self.clob_client.place_order(order_request)

        if not order_response.is_success:
            self.risk_manager.record_api_error()
            return ExecutionResult(
                signal=signal,
                order_id=order_response.order_id,
                status="failed",
                reason=order_response.error or "Order rejected",
            )

        # 5. Track order
        self.order_manager.track_order(order_response)

        # 6. Update position tracker
        if order_response.status == OrderStatus.FILLED:
            self.position_tracker.open_position(
                market_id=signal.market_id,
                direction=signal.prediction.direction,
                size_usd=signal.position_size_usd,
                entry_price=order_response.price,
            )

        result = ExecutionResult(
            signal=signal,
            order_id=order_response.order_id,
            status="executed",
            reason=f"Filled @ {order_response.price:.4f}",
        )

        if self.on_trade:
            self.on_trade(result)

        logger.info(
            "Executed: %s %s $%.2f @ %.4f (kelly=%.3f)",
            signal.prediction.direction.value,
            signal.market_id[:8],
            signal.position_size_usd,
            order_response.price,
            signal.kelly_fraction,
        )
        return result

    def execute_batch(self, signals: list[Signal]) -> list[ExecutionResult]:
        """Execute a batch of signals in priority order."""
        results: list[ExecutionResult] = []
        for signal in signals:
            result = self.execute_signal(signal)
            results.append(result)
            # Stop if circuit breaker tripped mid-batch
            if result.status == "blocked" and "circuit" in result.reason.lower():
                logger.warning("Circuit breaker tripped — stopping batch")
                break
        return results

    def resolve_position(self, market_id: str, outcome: float) -> Optional[float]:
        """Resolve a position when the market settles.

        Returns P&L or None if no position found.
        """
        pnl = self.position_tracker.close_position(market_id, outcome)
        if pnl is not None:
            self.risk_manager.record_trade_result(pnl)
            self.risk_manager.update_capital(self.position_tracker.current_capital)
        return pnl
