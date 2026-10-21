# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Prediction loop — scan → estimate → rank → log cycle."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from src.polymarket.prediction_estimator import EnsembleEstimator, TemperatureScaler
from src.polymarket.types import Market, Prediction, Signal

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/algo-trade.db"


@dataclass
class LoopConfig:
    """Configuration for the prediction loop."""
    cycle_interval_sec: float = 60.0
    min_edge: float = 0.05
    max_signals_per_cycle: int = 10
    ensemble_n: int = 3
    db_path: str = DEFAULT_DB_PATH
    paper_trading: bool = True


class DecisionLogger:
    """Log AI decisions to SQLite for calibration tracking."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    question TEXT,
                    predicted_probability REAL,
                    market_price REAL,
                    edge REAL,
                    direction TEXT,
                    confidence REAL,
                    ensemble_agreement REAL,
                    model_used TEXT,
                    is_paper INTEGER DEFAULT 1,
                    resolved INTEGER DEFAULT 0,
                    actual_outcome REAL,
                    pnl REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def log_prediction(self, prediction: Prediction, is_paper: bool = True) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO ai_decisions
                   (market_id, question, predicted_probability, market_price,
                    edge, direction, confidence, ensemble_agreement,
                    model_used, is_paper, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prediction.market_id, prediction.question, prediction.predicted_probability,
                    prediction.market_price, prediction.edge, prediction.direction.value,
                    prediction.confidence, prediction.ensemble_agreement, prediction.model_used,
                    1 if is_paper else 0, prediction.timestamp.isoformat(),
                ),
            )

    def get_resolved_predictions(self) -> list[tuple[float, float]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT predicted_probability, actual_outcome FROM ai_decisions WHERE resolved = 1"
            ).fetchall()
        return [(r[0], r[1]) for r in rows]


class PredictionLoop:
    """Main scan → estimate → rank → log cycle."""

    def __init__(
        self,
        scanner: object,
        estimator: EnsembleEstimator,
        scaler: Optional[TemperatureScaler] = None,
        logger_db: Optional[DecisionLogger] = None,
        config: Optional[LoopConfig] = None,
        on_signal: Optional[Callable[[Signal], None]] = None,
    ) -> None:
        self.scanner = scanner
        self.estimator = estimator
        self.scaler = scaler or TemperatureScaler()
        self.decision_logger = logger_db
        self.config = config or LoopConfig()
        self.on_signal = on_signal
        self._running = False
        self.cycle_count = 0

    def run_cycle(self, markets: list[Market]) -> list[Signal]:
        from src.polymarket.market_scanner import MarketScanner
        filtered = self.scanner.scan(markets) if isinstance(self.scanner, MarketScanner) else markets

        predictions: list[Prediction] = []
        for market in filtered:
            pred = self.estimator.estimate(market)
            pred.predicted_probability = self.scaler.scale(pred.predicted_probability)
            pred.edge = abs(pred.predicted_probability - pred.market_price)
            predictions.append(pred)

        with_edge = [p for p in predictions if p.edge >= self.config.min_edge]
        with_edge.sort(key=lambda p: p.edge, reverse=True)
        top = with_edge[: self.config.max_signals_per_cycle]

        signals: list[Signal] = []
        for rank, pred in enumerate(top, 1):
            signal = Signal(
                prediction=pred,
                kelly_fraction=0.0,
                position_size_usd=0.0,
                expected_value=pred.edge * pred.confidence,
                rank=rank,
            )
            signals.append(signal)

        if self.decision_logger:
            for pred in predictions:
                self.decision_logger.log_prediction(pred, is_paper=self.config.paper_trading)

        if self.on_signal:
            for sig in signals:
                self.on_signal(sig)

        self.cycle_count += 1
        logger.info("Cycle %d: %d markets → %d filtered → %d signals", self.cycle_count, len(markets), len(filtered), len(signals))
        return signals

    def start(self, market_source: Callable[[], list[Market]]) -> None:
        self._running = True
        logger.info("PredictionLoop started (paper=%s)", self.config.paper_trading)
        while self._running:
            try:
                markets = market_source()
                self.run_cycle(markets)
                time.sleep(self.config.cycle_interval_sec)
            except KeyboardInterrupt:
                self.stop()
            except Exception:
                logger.exception("Error in prediction cycle")
                time.sleep(self.config.cycle_interval_sec)

    def stop(self) -> None:
        self._running = False
        logger.info("PredictionLoop stopped after %d cycles", self.cycle_count)


__all__ = [
    "DEFAULT_DB_PATH", "DecisionLogger", "EnsembleEstimator", "LoopConfig",
    "PredictionLoop", "TemperatureScaler",
]
