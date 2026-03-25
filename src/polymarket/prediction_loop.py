"""Prediction loop — scan → estimate → rank → log cycle."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from src.polymarket.types import Market, Prediction, Signal

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/algo-trade.db"


@dataclass
class LoopConfig:
    """Configuration for the prediction loop."""
    cycle_interval_sec: float = 60.0
    min_edge: float = 0.05          # 5% minimum edge to signal
    max_signals_per_cycle: int = 10
    ensemble_n: int = 3             # Number of ensemble votes
    db_path: str = DEFAULT_DB_PATH
    paper_trading: bool = True


class EnsembleEstimator:
    """Ensemble prediction: N independent LLM calls, majority vote."""

    def __init__(
        self,
        llm_client: Optional[object] = None,
        n_votes: int = 3,
        model: str = "deepseek-r1",
    ) -> None:
        self.llm_client = llm_client
        self.n_votes = n_votes
        self.model = model

    def estimate(self, market: Market) -> Prediction:
        """Generate ensemble probability estimate for a market."""
        votes: list[float] = []
        for i in range(self.n_votes):
            prob = self._single_estimate(market, seed=i)
            votes.append(prob)

        avg_prob = sum(votes) / len(votes)
        agreement = 1.0 - (max(votes) - min(votes))
        edge = abs(avg_prob - market.yes_price)

        return Prediction(
            market_id=market.market_id,
            question=market.question,
            predicted_probability=avg_prob,
            market_price=market.yes_price,
            edge=edge,
            confidence=agreement,
            model_used=self.model,
            ensemble_agreement=agreement,
        )

    def _single_estimate(self, market: Market, seed: int = 0) -> float:
        """Single LLM probability estimate. Returns 0.5 if no client."""
        if self.llm_client is None:
            return 0.5
        # In production, call LLM with structured prompt
        # For now, return mock value for paper trading validation
        return 0.5


class TemperatureScaler:
    """Platt scaling for calibrated probabilities. Identity until fitted."""

    def __init__(self) -> None:
        self.a: float = 1.0  # Identity transform
        self.b: float = 0.0
        self.is_fitted: bool = False

    def scale(self, probability: float) -> float:
        """Apply temperature scaling. Identity if not fitted."""
        if not self.is_fitted:
            return probability
        import math
        logit = math.log(probability / (1.0 - probability + 1e-10))
        scaled_logit = self.a * logit + self.b
        return 1.0 / (1.0 + math.exp(-scaled_logit))

    def fit(self, predicted: list[float], actual: list[float]) -> None:
        """Fit scaling parameters from resolved predictions."""
        if len(predicted) < 10:
            logger.warning("Not enough data to fit scaler (%d < 10)", len(predicted))
            return
        # Simple grid search for a, b
        best_brier = float("inf")
        best_a, best_b = 1.0, 0.0
        for a in [x * 0.1 for x in range(5, 21)]:
            for b in [x * 0.1 for x in range(-10, 11)]:
                self.a, self.b = a, b
                self.is_fitted = True
                brier = sum(
                    (self.scale(p) - a_val) ** 2
                    for p, a_val in zip(predicted, actual)
                ) / len(predicted)
                if brier < best_brier:
                    best_brier = brier
                    best_a, best_b = a, b
        self.a, self.b = best_a, best_b
        self.is_fitted = True
        logger.info("TemperatureScaler fitted: a=%.2f, b=%.2f, brier=%.4f", best_a, best_b, best_brier)


class DecisionLogger:
    """Log AI decisions to SQLite for calibration tracking."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create ai_decisions table if not exists."""
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
        """Log a prediction to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO ai_decisions
                   (market_id, question, predicted_probability, market_price,
                    edge, direction, confidence, ensemble_agreement,
                    model_used, is_paper, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prediction.market_id,
                    prediction.question,
                    prediction.predicted_probability,
                    prediction.market_price,
                    prediction.edge,
                    prediction.direction.value,
                    prediction.confidence,
                    prediction.ensemble_agreement,
                    prediction.model_used,
                    1 if is_paper else 0,
                    prediction.timestamp.isoformat(),
                ),
            )

    def get_resolved_predictions(self) -> list[tuple[float, float]]:
        """Return (predicted, actual) pairs for calibration."""
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
        """Run one prediction cycle: scan → estimate → rank → log."""
        # 1. Scan (filter markets)
        from src.polymarket.market_scanner import MarketScanner
        if isinstance(self.scanner, MarketScanner):
            filtered = self.scanner.scan(markets)
        else:
            filtered = markets

        # 2. Estimate probabilities
        predictions: list[Prediction] = []
        for market in filtered:
            pred = self.estimator.estimate(market)
            # Apply temperature scaling
            pred.predicted_probability = self.scaler.scale(pred.predicted_probability)
            pred.edge = abs(pred.predicted_probability - pred.market_price)
            predictions.append(pred)

        # 3. Filter by minimum edge
        with_edge = [p for p in predictions if p.edge >= self.config.min_edge]

        # 4. Rank by edge (descending)
        with_edge.sort(key=lambda p: p.edge, reverse=True)
        top = with_edge[: self.config.max_signals_per_cycle]

        # 5. Create signals (position sizing happens in caller)
        signals: list[Signal] = []
        for rank, pred in enumerate(top, 1):
            signal = Signal(
                prediction=pred,
                kelly_fraction=0.0,  # Filled by position sizer
                position_size_usd=0.0,
                expected_value=pred.edge * pred.confidence,
                rank=rank,
            )
            signals.append(signal)

        # 6. Log decisions
        if self.decision_logger:
            for pred in predictions:
                self.decision_logger.log_prediction(
                    pred, is_paper=self.config.paper_trading
                )

        # 7. Notify callback
        if self.on_signal:
            for sig in signals:
                self.on_signal(sig)

        self.cycle_count += 1
        logger.info(
            "Cycle %d: %d markets → %d filtered → %d signals",
            self.cycle_count, len(markets), len(filtered), len(signals),
        )
        return signals

    def start(self, market_source: Callable[[], list[Market]]) -> None:
        """Start continuous prediction loop."""
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
        """Stop the prediction loop."""
        self._running = False
        logger.info("PredictionLoop stopped after %d cycles", self.cycle_count)
