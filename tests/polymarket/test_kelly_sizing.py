"""Tests for Kelly position sizer — half-Kelly, caps, edge cases."""

import pytest

from src.polymarket.kelly_position_sizer import KellyPositionSizer, SizerConfig
from src.polymarket.types import Prediction, TradeDirection


def _make_prediction(
    predicted_prob: float = 0.70,
    market_price: float = 0.55,
) -> Prediction:
    """Create a test prediction."""
    edge = abs(predicted_prob - market_price)
    return Prediction(
        market_id="m1",
        question="Test market",
        predicted_probability=predicted_prob,
        market_price=market_price,
        edge=edge,
        confidence=0.8,
        model_used="test",
        ensemble_agreement=0.9,
    )


class TestHalfKellyCalculation:
    """Test half-Kelly formula correctness."""

    def test_positive_edge_returns_fraction(self) -> None:
        sizer = KellyPositionSizer()
        pred = _make_prediction(predicted_prob=0.70, market_price=0.55)
        kelly = sizer.calculate_kelly(pred)
        assert kelly > 0
        assert kelly <= 0.10  # capped at 10%

    def test_half_kelly_is_half_of_full(self) -> None:
        """Half-Kelly should be approximately half of full Kelly."""
        full_sizer = KellyPositionSizer(SizerConfig(use_half_kelly=False, max_position_pct=1.0))
        half_sizer = KellyPositionSizer(SizerConfig(use_half_kelly=True, max_position_pct=1.0))
        pred = _make_prediction(predicted_prob=0.70, market_price=0.55)
        full = full_sizer.calculate_kelly(pred)
        half = half_sizer.calculate_kelly(pred)
        assert abs(half - full / 2.0) < 1e-10

    def test_no_edge_returns_zero(self) -> None:
        sizer = KellyPositionSizer()
        pred = _make_prediction(predicted_prob=0.55, market_price=0.55)
        assert sizer.calculate_kelly(pred) == 0.0

    def test_negative_edge_returns_zero(self) -> None:
        """When predicted < market, edge is negative → no bet."""
        pred = Prediction(
            market_id="m1", question="Test",
            predicted_probability=0.40, market_price=0.55,
            edge=-0.15, confidence=0.5,
            model_used="test", ensemble_agreement=0.5,
        )
        sizer = KellyPositionSizer()
        assert sizer.calculate_kelly(pred) == 0.0

    def test_very_high_edge_capped(self) -> None:
        """Even with huge edge, position capped at 10%."""
        sizer = KellyPositionSizer()
        pred = _make_prediction(predicted_prob=0.95, market_price=0.10)
        kelly = sizer.calculate_kelly(pred)
        assert kelly <= 0.10


class TestPositionCap:
    """Test position never exceeds 10% of capital."""

    def test_position_usd_respects_cap(self) -> None:
        sizer = KellyPositionSizer()
        pred = _make_prediction(predicted_prob=0.95, market_price=0.10)
        signal = sizer.size_signal(pred, capital=1000.0)
        assert signal.position_size_usd <= 100.0  # 10% of $1000

    def test_small_capital_small_position(self) -> None:
        sizer = KellyPositionSizer()
        pred = _make_prediction(predicted_prob=0.70, market_price=0.55)
        signal = sizer.size_signal(pred, capital=200.0)
        assert signal.position_size_usd <= 20.0  # 10% of $200


class TestEdgeCases:
    """Test edge cases in Kelly calculation."""

    def test_edge_zero(self) -> None:
        pred = _make_prediction(predicted_prob=0.50, market_price=0.50)
        sizer = KellyPositionSizer()
        assert sizer.calculate_kelly(pred) == 0.0

    def test_edge_below_minimum(self) -> None:
        """Edge below 2% minimum should return 0."""
        pred = _make_prediction(predicted_prob=0.56, market_price=0.55)
        sizer = KellyPositionSizer()
        assert sizer.calculate_kelly(pred) == 0.0

    def test_market_price_zero(self) -> None:
        pred = _make_prediction(predicted_prob=0.50, market_price=0.0)
        sizer = KellyPositionSizer()
        assert sizer.calculate_kelly(pred) == 0.0

    def test_market_price_one(self) -> None:
        pred = _make_prediction(predicted_prob=0.50, market_price=1.0)
        sizer = KellyPositionSizer()
        assert sizer.calculate_kelly(pred) == 0.0


class TestMultipleSignals:
    """Test batch signal sizing."""

    def test_size_signals_ranked(self) -> None:
        sizer = KellyPositionSizer()
        predictions = [
            _make_prediction(predicted_prob=0.70, market_price=0.55),
            _make_prediction(predicted_prob=0.80, market_price=0.55),
            _make_prediction(predicted_prob=0.55, market_price=0.55),  # No edge
        ]
        signals = sizer.size_signals(predictions, capital=1000.0)
        # Should exclude no-edge prediction
        assert len(signals) == 2
        # Should be ranked by expected value
        assert signals[0].rank == 1
        assert signals[1].rank == 2
        assert signals[0].expected_value >= signals[1].expected_value

    def test_empty_predictions(self) -> None:
        sizer = KellyPositionSizer()
        assert sizer.size_signals([], capital=1000.0) == []
