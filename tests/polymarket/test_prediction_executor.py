"""Tests for PredictionExecutor — full pipeline from signal to execution."""

import os
import tempfile

import pytest

from src.polymarket.clob_client import ClobClient
from src.polymarket.kelly_position_sizer import KellyPositionSizer
from src.polymarket.live_mode_guard import GuardConfig
from src.polymarket.order_manager import OrderManager
from src.polymarket.position_tracker import PositionTracker
from src.polymarket.prediction_executor import PredictionExecutor
from src.polymarket.risk_manager import RiskManager
from src.polymarket.types import Prediction, Signal, TradeDirection


def _make_signal(
    edge: float = 0.15,
    predicted_prob: float = 0.70,
    market_price: float = 0.55,
) -> Signal:
    pred = Prediction(
        market_id="m1",
        question="Will event happen?",
        predicted_probability=predicted_prob,
        market_price=market_price,
        edge=edge,
        confidence=0.8,
        model_used="test",
        ensemble_agreement=0.9,
    )
    return Signal(
        prediction=pred,
        kelly_fraction=0.0,
        position_size_usd=0.0,
        expected_value=edge * 10,
    )


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def executor(db_path):
    return PredictionExecutor(
        risk_manager=RiskManager(capital=1000.0),
        sizer=KellyPositionSizer(),
        clob_client=ClobClient(paper_mode=True),
        order_manager=OrderManager(db_path),
        position_tracker=PositionTracker(initial_capital=1000.0),
        guard_config=GuardConfig(paper_trading=True, db_path=db_path),
    )


class TestExecuteSignal:
    """Test single signal execution."""

    def test_successful_execution(self, executor: PredictionExecutor) -> None:
        result = executor.execute_signal(_make_signal())
        assert result.status == "executed"
        assert result.order_id is not None
        assert "filled" in result.reason.lower() or "paper" in result.order_id.lower()

    def test_no_edge_skipped(self, executor: PredictionExecutor) -> None:
        result = executor.execute_signal(_make_signal(edge=0.0, predicted_prob=0.55, market_price=0.55))
        assert result.status == "skipped"
        assert "zero" in result.reason.lower() or "edge" in result.reason.lower()

    def test_position_tracked(self, executor: PredictionExecutor) -> None:
        executor.execute_signal(_make_signal())
        assert executor.position_tracker.open_position_count == 1

    def test_on_trade_callback(self, db_path: str) -> None:
        received = []
        ex = PredictionExecutor(
            risk_manager=RiskManager(capital=1000.0),
            sizer=KellyPositionSizer(),
            clob_client=ClobClient(paper_mode=True),
            order_manager=OrderManager(db_path),
            position_tracker=PositionTracker(initial_capital=1000.0),
            guard_config=GuardConfig(paper_trading=True, db_path=db_path),
            on_trade=lambda r: received.append(r),
        )
        ex.execute_signal(_make_signal())
        assert len(received) == 1


class TestExecuteBatch:
    """Test batch execution."""

    def test_batch_executes_multiple(self, executor: PredictionExecutor) -> None:
        signals = [
            _make_signal(edge=0.15),
            _make_signal(edge=0.10),
        ]
        # Use different market IDs
        signals[0].prediction.market_id = "m1"
        signals[1].prediction.market_id = "m2"
        results = executor.execute_batch(signals)
        executed = [r for r in results if r.status == "executed"]
        assert len(executed) == 2

    def test_batch_stops_on_circuit_breaker(self, db_path: str) -> None:
        rm = RiskManager(capital=1000.0)
        rm.record_trade_result(-60.0)  # Trip daily loss
        ex = PredictionExecutor(
            risk_manager=rm,
            sizer=KellyPositionSizer(),
            clob_client=ClobClient(paper_mode=True),
            order_manager=OrderManager(db_path),
            position_tracker=PositionTracker(initial_capital=1000.0),
            guard_config=GuardConfig(paper_trading=True, db_path=db_path),
        )
        results = ex.execute_batch([_make_signal(), _make_signal()])
        blocked = [r for r in results if r.status == "blocked"]
        assert len(blocked) >= 1


class TestResolvePosition:
    """Test position resolution."""

    def test_resolve_win(self, executor: PredictionExecutor) -> None:
        executor.execute_signal(_make_signal())
        pnl = executor.resolve_position("m1", outcome=1.0)
        assert pnl is not None
        assert pnl > 0

    def test_resolve_updates_capital(self, executor: PredictionExecutor) -> None:
        initial = executor.position_tracker.current_capital
        executor.execute_signal(_make_signal())
        executor.resolve_position("m1", outcome=1.0)
        assert executor.position_tracker.current_capital > initial

    def test_resolve_nonexistent(self, executor: PredictionExecutor) -> None:
        pnl = executor.resolve_position("nonexistent", outcome=1.0)
        assert pnl is None
