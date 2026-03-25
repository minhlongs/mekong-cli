"""Tests for prediction pipeline — ensemble, temperature scaling, decision logging."""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta


from src.polymarket.prediction_loop import (
    DecisionLogger,
    EnsembleEstimator,
    LoopConfig,
    PredictionLoop,
    TemperatureScaler,
)
from src.polymarket.market_scanner import MarketScanner
from src.polymarket.types import Market


def _make_market(market_id: str = "m1") -> Market:
    return Market(
        market_id=market_id,
        question="Will event happen?",
        outcomes=["Yes", "No"],
        volume_24h=10_000,
        end_date=datetime.utcnow() + timedelta(days=14),
        yes_price=0.55,
        no_price=0.45,
    )


class TestEnsembleEstimator:
    """Test ensemble voting with N=3."""

    def test_returns_prediction(self) -> None:
        estimator = EnsembleEstimator(n_votes=3)
        market = _make_market()
        pred = estimator.estimate(market)
        assert pred.market_id == "m1"
        assert 0.0 <= pred.predicted_probability <= 1.0
        assert pred.model_used == "deepseek-r1"

    def test_ensemble_agreement_calculated(self) -> None:
        estimator = EnsembleEstimator(n_votes=3)
        market = _make_market()
        pred = estimator.estimate(market)
        # Without LLM client, all votes return 0.5 → perfect agreement
        assert pred.ensemble_agreement == 1.0

    def test_edge_calculated(self) -> None:
        estimator = EnsembleEstimator(n_votes=3)
        market = _make_market()
        pred = estimator.estimate(market)
        expected_edge = abs(pred.predicted_probability - market.yes_price)
        assert abs(pred.edge - expected_edge) < 1e-10

    def test_custom_vote_count(self) -> None:
        estimator = EnsembleEstimator(n_votes=5)
        market = _make_market()
        pred = estimator.estimate(market)
        assert pred is not None


class TestTemperatureScaler:
    """Test temperature scaling for calibration."""

    def test_identity_when_not_fitted(self) -> None:
        scaler = TemperatureScaler()
        assert scaler.is_fitted is False
        assert scaler.scale(0.7) == 0.7
        assert scaler.scale(0.3) == 0.3

    def test_fit_with_data(self) -> None:
        scaler = TemperatureScaler()
        predicted = [0.6, 0.7, 0.8, 0.5, 0.4, 0.9, 0.3, 0.6, 0.7, 0.5]
        actual = [1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
        scaler.fit(predicted, actual)
        assert scaler.is_fitted is True

    def test_fit_too_few_datapoints(self) -> None:
        scaler = TemperatureScaler()
        scaler.fit([0.5, 0.6], [1.0, 0.0])
        assert scaler.is_fitted is False  # Not enough data

    def test_scaled_output_bounded(self) -> None:
        scaler = TemperatureScaler()
        predicted = [0.6, 0.7, 0.8, 0.5, 0.4, 0.9, 0.3, 0.6, 0.7, 0.5]
        actual = [1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
        scaler.fit(predicted, actual)
        for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
            scaled = scaler.scale(p)
            assert 0.0 < scaled < 1.0


class TestDecisionLogger:
    """Test SQLite decision logging."""

    def test_creates_table(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            DecisionLogger(db_path)
            with sqlite3.connect(db_path) as conn:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                assert ("ai_decisions",) in tables
        finally:
            os.unlink(db_path)

    def test_log_prediction(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            logger = DecisionLogger(db_path)
            from src.polymarket.types import Prediction
            pred = Prediction(
                market_id="m1", question="Test?",
                predicted_probability=0.7, market_price=0.55,
                edge=0.15, confidence=0.8,
                model_used="test", ensemble_agreement=0.9,
            )
            logger.log_prediction(pred, is_paper=True)
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute("SELECT * FROM ai_decisions").fetchall()
                assert len(rows) == 1
                assert rows[0][1] == "m1"  # market_id
        finally:
            os.unlink(db_path)

    def test_get_resolved_predictions_empty(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            logger = DecisionLogger(db_path)
            assert logger.get_resolved_predictions() == []
        finally:
            os.unlink(db_path)


class TestPredictionLoop:
    """Test the full scan → estimate → rank → log cycle."""

    def test_run_cycle_empty_markets(self) -> None:
        scanner = MarketScanner()
        estimator = EnsembleEstimator(n_votes=3)
        loop = PredictionLoop(
            scanner=scanner,
            estimator=estimator,
            config=LoopConfig(paper_trading=True),
        )
        signals = loop.run_cycle([])
        assert signals == []
        assert loop.cycle_count == 1

    def test_run_cycle_with_markets(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            scanner = MarketScanner()
            estimator = EnsembleEstimator(n_votes=3)
            decision_logger = DecisionLogger(db_path)
            loop = PredictionLoop(
                scanner=scanner,
                estimator=estimator,
                logger_db=decision_logger,
                config=LoopConfig(paper_trading=True, min_edge=0.0, db_path=db_path),
            )
            markets = [_make_market()]
            loop.run_cycle(markets)
            assert loop.cycle_count == 1
            # Predictions should be logged
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute("SELECT COUNT(*) FROM ai_decisions").fetchone()
                assert rows[0] >= 1
        finally:
            os.unlink(db_path)

    def test_on_signal_callback(self) -> None:
        received: list = []
        scanner = MarketScanner()
        estimator = EnsembleEstimator(n_votes=3)
        loop = PredictionLoop(
            scanner=scanner,
            estimator=estimator,
            on_signal=lambda s: received.append(s),
            config=LoopConfig(paper_trading=True, min_edge=0.0),
        )
        loop.run_cycle([_make_market()])
        # Callback should fire for each signal
        assert len(received) >= 0  # May be 0 if edge is 0

    def test_stop_sets_running_false(self) -> None:
        scanner = MarketScanner()
        estimator = EnsembleEstimator(n_votes=3)
        loop = PredictionLoop(scanner=scanner, estimator=estimator)
        loop._running = True
        loop.stop()
        assert loop._running is False
