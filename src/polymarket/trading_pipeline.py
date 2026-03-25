"""Trading pipeline — orchestrates the full prediction-to-execution flow.

Connects all components:
  MarketScanner → PredictionLoop → PredictionExecutor → Telegram alerts
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from src.polymarket.capital_tiers import get_current_tier, get_progress_report
from src.polymarket.clob_client import ClobClient
from src.polymarket.kelly_position_sizer import KellyPositionSizer
from src.polymarket.live_mode_guard import GuardConfig
from src.polymarket.market_scanner import MarketScanner, ScannerFilters
from src.polymarket.order_manager import OrderManager
from src.polymarket.position_tracker import PositionTracker
from src.polymarket.prediction_executor import ExecutionResult, PredictionExecutor
from src.polymarket.prediction_loop import (
    DecisionLogger,
    EnsembleEstimator,
    LoopConfig,
    PredictionLoop,
    TemperatureScaler,
)
from src.polymarket.risk_manager import RiskConfig, RiskManager
from src.polymarket.telegram_monitor import TelegramMonitor
from src.polymarket.types import Market

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Full pipeline configuration."""
    initial_capital: float = 200.0
    paper_trading: bool = True
    cycle_interval_sec: float = 60.0
    ensemble_n: int = 3
    db_path: str = "data/algo-trade.db"
    enable_telegram: bool = False


class TradingPipeline:
    """Full prediction-to-execution trading pipeline.

    Lifecycle:
    1. Scanner filters markets
    2. PredictionLoop estimates probabilities
    3. PredictionExecutor sizes + executes trades
    4. TelegramMonitor sends alerts
    5. RiskManager enforces safety
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()

        # Core components
        self.scanner = MarketScanner(ScannerFilters())
        self.estimator = EnsembleEstimator(n_votes=self.config.ensemble_n)
        self.scaler = TemperatureScaler()
        self.decision_logger = DecisionLogger(self.config.db_path)

        self.risk_manager = RiskManager(
            capital=self.config.initial_capital,
            config=RiskConfig(paper_trading=self.config.paper_trading),
        )
        self.sizer = KellyPositionSizer()
        self.clob_client = ClobClient(paper_mode=self.config.paper_trading)
        self.order_manager = OrderManager(self.config.db_path)
        self.position_tracker = PositionTracker(self.config.initial_capital)

        self.executor = PredictionExecutor(
            risk_manager=self.risk_manager,
            sizer=self.sizer,
            clob_client=self.clob_client,
            order_manager=self.order_manager,
            position_tracker=self.position_tracker,
            guard_config=GuardConfig(
                paper_trading=self.config.paper_trading,
                db_path=self.config.db_path,
            ),
            on_trade=self._on_trade,
        )

        self.telegram = TelegramMonitor()
        self.loop = PredictionLoop(
            scanner=self.scanner,
            estimator=self.estimator,
            scaler=self.scaler,
            logger_db=self.decision_logger,
            config=LoopConfig(
                cycle_interval_sec=self.config.cycle_interval_sec,
                ensemble_n=self.config.ensemble_n,
                db_path=self.config.db_path,
                paper_trading=self.config.paper_trading,
            ),
        )

        self._running = False
        self.cycle_count = 0

    def run_cycle(self, markets: list[Market]) -> list[ExecutionResult]:
        """Run one full prediction-to-execution cycle."""
        # 1. Prediction loop: scan → estimate → rank
        signals = self.loop.run_cycle(markets)

        # 2. Execute signals
        results = self.executor.execute_batch(signals)

        self.cycle_count += 1
        executed = [r for r in results if r.status == "executed"]
        blocked = [r for r in results if r.status == "blocked"]

        logger.info(
            "Pipeline cycle %d: %d signals → %d executed, %d blocked",
            self.cycle_count, len(signals), len(executed), len(blocked),
        )
        return results

    def start(self, market_source: Callable[[], list[Market]]) -> None:
        """Start continuous trading pipeline."""
        self._running = True
        mode = "PAPER" if self.config.paper_trading else "LIVE"
        logger.info(
            "TradingPipeline started [%s] capital=$%.2f",
            mode, self.config.initial_capital,
        )

        while self._running:
            try:
                markets = market_source()
                self.run_cycle(markets)
                time.sleep(self.config.cycle_interval_sec)
            except KeyboardInterrupt:
                self.stop()
            except Exception:
                logger.exception("Pipeline cycle error")
                self.risk_manager.record_api_error()
                time.sleep(self.config.cycle_interval_sec)

    def stop(self) -> None:
        """Stop the trading pipeline."""
        self._running = False
        logger.info(
            "Pipeline stopped. Cycles=%d, P&L=$%.2f, Trades=%d",
            self.cycle_count,
            self.position_tracker.realized_pnl,
            self.position_tracker.trade_count,
        )

    def _on_trade(self, result: ExecutionResult) -> None:
        """Callback when a trade is executed."""
        if self.telegram.is_enabled:
            self.telegram.alert_trade(
                direction=result.signal.prediction.direction.value,
                market_id=result.signal.market_id,
                size_usd=result.signal.position_size_usd,
                price=result.signal.prediction.market_price,
                edge=result.signal.prediction.edge,
                is_paper=self.config.paper_trading,
            )

    def get_status(self) -> dict:
        """Get current pipeline status."""
        portfolio = self.position_tracker.get_portfolio_state()
        tier = get_current_tier(self.config.db_path)
        progress = get_progress_report(self.config.db_path)
        return {
            "mode": "PAPER" if self.config.paper_trading else "LIVE",
            "capital": self.position_tracker.current_capital,
            "realized_pnl": self.position_tracker.realized_pnl,
            "unrealized_pnl": self.position_tracker.unrealized_pnl,
            "total_pnl": self.position_tracker.total_pnl,
            "trade_count": self.position_tracker.trade_count,
            "win_rate": self.position_tracker.win_rate,
            "open_positions": self.position_tracker.open_position_count,
            "open_exposure": self.position_tracker.open_exposure,
            "max_drawdown": self.position_tracker.max_drawdown,
            "tier": tier.level,
            "tier_progress": {
                "days": progress.days_completed,
                "required_days": progress.tier.min_dry_run_days,
                "profitable_days": progress.profitable_days,
                "can_progress": progress.can_progress,
            },
            "circuit_breaker": self.risk_manager.state.circuit_breaker.value,
            "cycle_count": self.cycle_count,
        }
