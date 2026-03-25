"""Tests for RiskManager — circuit breakers, daily limits, position caps."""

import time


from src.polymarket.risk_manager import RiskConfig, RiskManager
from src.polymarket.types import CircuitBreakerState, Prediction, Signal


def _make_signal(position_usd: float = 10.0) -> Signal:
    """Create a test signal."""
    pred = Prediction(
        market_id="m1", question="Test",
        predicted_probability=0.70, market_price=0.55,
        edge=0.15, confidence=0.8,
        model_used="test", ensemble_agreement=0.9,
    )
    return Signal(
        prediction=pred,
        kelly_fraction=0.05,
        position_size_usd=position_usd,
        expected_value=1.5,
    )


class TestDailyLossLimit:
    """Test 5% daily loss limit."""

    def test_trade_allowed_within_limit(self) -> None:
        rm = RiskManager(capital=1000.0)
        result = rm.check_trade(_make_signal())
        assert result.allowed is True

    def test_trade_blocked_after_daily_loss(self) -> None:
        rm = RiskManager(capital=1000.0)
        # Simulate losses exceeding 5% of $1000 = $50
        rm.record_trade_result(-60.0)
        result = rm.check_trade(_make_signal())
        assert result.allowed is False
        assert "loss limit" in result.reason.lower()

    def test_daily_loss_resets(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.state.daily_pnl = -60.0
        # Force a new day
        rm.state.date = "2024-01-01"
        result = rm.check_trade(_make_signal())
        assert result.allowed is True


class TestConsecutiveLosses:
    """Test circuit breaker on consecutive losses."""

    def test_three_consecutive_losses_pauses(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.record_trade_result(-5.0)
        rm.record_trade_result(-5.0)
        rm.record_trade_result(-5.0)
        result = rm.check_trade(_make_signal())
        assert result.allowed is False
        assert "consecutive" in result.reason.lower()

    def test_win_resets_consecutive(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.record_trade_result(-5.0)
        rm.record_trade_result(-5.0)
        rm.record_trade_result(10.0)  # Win resets counter
        result = rm.check_trade(_make_signal())
        assert result.allowed is True

    def test_two_losses_still_allowed(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.record_trade_result(-5.0)
        rm.record_trade_result(-5.0)
        result = rm.check_trade(_make_signal())
        assert result.allowed is True


class TestPositionCap:
    """Test position size cap at 10% of capital."""

    def test_oversized_position_rejected(self) -> None:
        rm = RiskManager(capital=1000.0)
        signal = _make_signal(position_usd=150.0)  # 15% of capital
        result = rm.check_trade(signal)
        assert result.allowed is False
        assert "10%" in result.reason

    def test_exact_cap_allowed(self) -> None:
        rm = RiskManager(capital=1000.0)
        signal = _make_signal(position_usd=100.0)
        result = rm.check_trade(signal)
        assert result.allowed is True

    def test_small_position_allowed(self) -> None:
        rm = RiskManager(capital=1000.0)
        signal = _make_signal(position_usd=10.0)
        result = rm.check_trade(signal)
        assert result.allowed is True


class TestCalibrationDrift:
    """Test Brier score circuit breaker."""

    def test_high_brier_halts_trading(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.update_brier(0.35)  # Above 0.30 threshold
        result = rm.check_trade(_make_signal())
        assert result.allowed is False
        assert "calibration" in result.reason.lower()

    def test_good_brier_allows_trading(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.update_brier(0.18)
        result = rm.check_trade(_make_signal())
        assert result.allowed is True


class TestCircuitBreaker:
    """Test circuit breaker states."""

    def test_initial_state_closed(self) -> None:
        rm = RiskManager(capital=1000.0)
        assert rm.state.circuit_breaker == CircuitBreakerState.CLOSED

    def test_force_resume(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm._trip_circuit_breaker("test")
        assert rm.state.circuit_breaker == CircuitBreakerState.OPEN
        rm.force_resume()
        assert rm.state.circuit_breaker == CircuitBreakerState.CLOSED

    def test_auto_resume_after_cooldown(self) -> None:
        rm = RiskManager(capital=1000.0)
        # Trip with 0.01s cooldown
        rm._trip_circuit_breaker("test", auto_resume_sec=0.01)
        time.sleep(0.02)
        result = rm.check_trade(_make_signal())
        assert result.allowed is True

    def test_calibration_no_auto_resume(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.update_brier(0.35)
        rm.check_trade(_make_signal())
        # Even after long wait, calibration halt doesn't auto-resume
        rm.state.paused_until = time.time() - 100
        result = rm.check_trade(_make_signal())
        assert result.allowed is False


class TestApiErrorStorm:
    """Test API error storm detection."""

    def test_many_errors_halts(self) -> None:
        config = RiskConfig(max_api_errors_per_min=3)
        rm = RiskManager(capital=1000.0, config=config)
        rm.record_api_error()
        rm.record_api_error()
        rm.record_api_error()
        result = rm.check_trade(_make_signal())
        assert result.allowed is False
        assert "api" in result.reason.lower()

    def test_few_errors_allowed(self) -> None:
        rm = RiskManager(capital=1000.0)
        rm.record_api_error()
        rm.record_api_error()
        result = rm.check_trade(_make_signal())
        assert result.allowed is True
