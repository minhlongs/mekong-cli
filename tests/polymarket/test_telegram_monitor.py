"""Tests for TelegramMonitor — message formatting, config, disabled mode."""

from unittest.mock import patch


from src.polymarket.telegram_monitor import TelegramConfig, TelegramMonitor


class TestTelegramConfig:
    """Test Telegram configuration."""

    def test_disabled_without_token(self) -> None:
        config = TelegramConfig()
        assert config.enabled is False

    def test_enabled_with_both(self) -> None:
        config = TelegramConfig(bot_token="tok", chat_id="123", enabled=True)
        assert config.enabled is True

    def test_from_env_disabled(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            config = TelegramConfig.from_env()
            assert config.enabled is False

    def test_from_env_enabled(self) -> None:
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_CHAT_ID": "12345",
        }):
            config = TelegramConfig.from_env()
            assert config.enabled is True


class TestDisabledMode:
    """Test monitor when disabled."""

    def test_send_returns_false(self) -> None:
        monitor = TelegramMonitor(TelegramConfig())
        assert monitor.send_message("test") is False

    def test_alert_trade_disabled(self) -> None:
        monitor = TelegramMonitor(TelegramConfig())
        result = monitor.alert_trade("YES", "m1", 10.0, 0.55, 0.15)
        assert result is False

    def test_alert_circuit_breaker_disabled(self) -> None:
        monitor = TelegramMonitor(TelegramConfig())
        assert monitor.alert_circuit_breaker("test") is False

    def test_is_enabled_property(self) -> None:
        disabled = TelegramMonitor(TelegramConfig())
        assert disabled.is_enabled is False
        enabled = TelegramMonitor(TelegramConfig(bot_token="t", chat_id="c", enabled=True))
        assert enabled.is_enabled is True


class TestMessageFormatting:
    """Test message formatting (without actually sending)."""

    def test_alert_trade_format(self) -> None:
        config = TelegramConfig(bot_token="tok", chat_id="123", enabled=True)
        monitor = TelegramMonitor(config)
        with patch.object(monitor, "send_message", return_value=True) as mock_send:
            monitor.alert_trade("YES", "market123", 50.0, 0.55, 0.15, is_paper=True)
            msg = mock_send.call_args[0][0]
            assert "PAPER" in msg
            assert "YES" in msg
            assert "50.00" in msg

    def test_alert_daily_summary_format(self) -> None:
        config = TelegramConfig(bot_token="tok", chat_id="123", enabled=True)
        monitor = TelegramMonitor(config)
        with patch.object(monitor, "send_message", return_value=True) as mock_send:
            monitor.alert_daily_summary(
                date="2024-01-15", trades=10, pnl=25.50,
                win_rate=0.60, brier=0.18, capital=225.50,
            )
            msg = mock_send.call_args[0][0]
            assert "2024-01-15" in msg
            assert "25.50" in msg
            assert "60%" in msg

    def test_alert_calibration_drift_format(self) -> None:
        config = TelegramConfig(bot_token="tok", chat_id="123", enabled=True)
        monitor = TelegramMonitor(config)
        with patch.object(monitor, "send_message", return_value=True) as mock_send:
            monitor.alert_calibration_drift(brier=0.35, threshold=0.30)
            msg = mock_send.call_args[0][0]
            assert "0.3500" in msg
            assert "CalibrationTuner" in msg

    def test_send_status_format(self) -> None:
        config = TelegramConfig(bot_token="tok", chat_id="123", enabled=True)
        monitor = TelegramMonitor(config)
        with patch.object(monitor, "send_message", return_value=True) as mock_send:
            monitor.send_status(
                capital=500.0, pnl=25.0, open_positions=3,
                tier_level=2, circuit_breaker="closed",
            )
            msg = mock_send.call_args[0][0]
            assert "500.00" in msg
            assert "closed" in msg
