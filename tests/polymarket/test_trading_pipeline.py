"""Tests for TradingPipeline — full integration from scan to execute."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.polymarket.trading_pipeline import PipelineConfig, TradingPipeline
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


@pytest.fixture
def pipeline():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    config = PipelineConfig(
        initial_capital=200.0,
        paper_trading=True,
        db_path=db_path,
    )
    pipe = TradingPipeline(config)
    yield pipe
    os.unlink(db_path)


class TestPipelineCycle:
    """Test run_cycle integration."""

    def test_cycle_with_no_markets(self, pipeline: TradingPipeline) -> None:
        results = pipeline.run_cycle([])
        assert results == []
        assert pipeline.cycle_count == 1

    def test_cycle_with_markets(self, pipeline: TradingPipeline) -> None:
        results = pipeline.run_cycle([_make_market()])
        assert pipeline.cycle_count == 1
        # Results may be empty if no edge detected (mock estimator returns 0.5)
        assert isinstance(results, list)

    def test_multiple_cycles(self, pipeline: TradingPipeline) -> None:
        pipeline.run_cycle([])
        pipeline.run_cycle([])
        pipeline.run_cycle([])
        assert pipeline.cycle_count == 3


class TestPipelineStatus:
    """Test status reporting."""

    def test_initial_status(self, pipeline: TradingPipeline) -> None:
        status = pipeline.get_status()
        assert status["mode"] == "PAPER"
        assert status["capital"] == 200.0
        assert status["trade_count"] == 0
        assert status["circuit_breaker"] == "closed"

    def test_status_after_cycle(self, pipeline: TradingPipeline) -> None:
        pipeline.run_cycle([_make_market()])
        status = pipeline.get_status()
        assert status["cycle_count"] == 1
        assert "tier" in status
        assert "tier_progress" in status


class TestPipelineStop:
    """Test pipeline start/stop."""

    def test_stop(self, pipeline: TradingPipeline) -> None:
        pipeline._running = True
        pipeline.stop()
        assert pipeline._running is False


class TestPaperModeDefault:
    """Test paper_trading defaults."""

    def test_config_defaults_to_paper(self) -> None:
        config = PipelineConfig()
        assert config.paper_trading is True

    def test_pipeline_paper_mode(self, pipeline: TradingPipeline) -> None:
        assert pipeline.clob_client.paper_mode is True
        assert pipeline.config.paper_trading is True
