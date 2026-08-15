"""Live mode guard — safety checks before any live trade execution.

CRITICAL: This guard MUST be called before ClobClient.placeOrder().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.polymarket.capital_tiers import get_current_tier
from src.polymarket.risk_manager import RiskManager
from src.polymarket.types import RiskCheckResult, Signal

logger = logging.getLogger(__name__)


@dataclass
class GuardConfig:
    """Live mode guard configuration."""
    min_dry_run_days: int = 14
    db_path: str = "data/algo-trade.db"
    paper_trading: bool = True


class LiveModeGuard:
    """Safety guard for live trading. Checks all preconditions."""

    def __init__(
        self,
        risk_manager: RiskManager,
        config: GuardConfig | None = None,
    ) -> None:
        self.risk_manager = risk_manager
        self.config = config or GuardConfig()

    def check(self, signal: Signal) -> RiskCheckResult:
        """Run all safety checks before live trade execution.

        Returns allowed=True only if ALL checks pass.
        """
        # 1. Paper trading mode check
        if self.config.paper_trading:
            return RiskCheckResult(
                allowed=False,
                reason="Paper trading mode — live trades disabled",
            )

        # 2. Capital tier check
        tier = get_current_tier(self.config.db_path)
        if signal.position_size_usd > tier.max_capital * 0.10:
            return RiskCheckResult(
                allowed=False,
                reason=f"Position exceeds tier {tier.level} limit "
                       f"(max ${tier.max_capital * 0.10:.2f})",
            )

        # 3. Risk manager check (daily loss, circuit breaker, etc.)
        risk_result = self.risk_manager.check_trade(signal)
        if not risk_result.allowed:
            return risk_result

        logger.info(
            "LiveModeGuard: APPROVED trade %s $%.2f",
            signal.market_id[:8],
            signal.position_size_usd,
        )
        return RiskCheckResult(
            allowed=True,
            reason="All safety checks passed",
            max_position_size=risk_result.max_position_size,
        )
