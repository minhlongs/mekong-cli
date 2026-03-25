"""Tests for CashClaw SDK — tier gating, signal limits, init."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.polymarket.sdk import CashClaw, Tier, TierLimits, SDKSignal


class TestInit:
    """Test SDK initialization."""

    def test_init_with_key(self) -> None:
        client = CashClaw(api_key="test-key", tier="starter")
        assert client.api_key == "test-key"
        assert client.tier == Tier.STARTER

    def test_init_class_method(self) -> None:
        client = CashClaw.init(api_key="test-key", tier="pro")
        assert client.tier == Tier.PRO

    def test_init_no_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                CashClaw.init(api_key="")

    def test_init_from_env(self) -> None:
        with patch.dict(os.environ, {"CASHCLAW_API_KEY": "env-key"}):
            client = CashClaw.init()
            assert client.api_key == "env-key"

    def test_context_manager(self) -> None:
        with CashClaw(api_key="test", tier="starter") as client:
            assert client.api_key == "test"


class TestTierLimits:
    """Test tier feature gating."""

    def test_starter_limits(self) -> None:
        limits = TierLimits.for_tier(Tier.STARTER)
        assert limits.signals_per_day == 5
        assert limits.ensemble_n == 1
        assert limits.dark_edge is False
        assert limits.custom_strategies is False

    def test_pro_limits(self) -> None:
        limits = TierLimits.for_tier(Tier.PRO)
        assert limits.signals_per_day == 20
        assert limits.ensemble_n == 3
        assert limits.dark_edge is True

    def test_elite_limits(self) -> None:
        limits = TierLimits.for_tier(Tier.ELITE)
        assert limits.signals_per_day == 999
        assert limits.ensemble_n == 5
        assert limits.custom_strategies is True


class TestSignalLimit:
    """Test daily signal limit enforcement."""

    def test_remaining_signals_initial(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        assert client.remaining_signals == 5

    def test_signal_limit_decrements(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._signals_today = 3
        assert client.remaining_signals == 2

    def test_signal_limit_exceeded(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._signals_today = 5
        with pytest.raises(PermissionError, match="signal limit"):
            client._check_signal_limit()

    def test_signals_returns_empty_at_limit(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._signals_today = 5
        # Without HTTP client, returns empty
        assert client.signals() == []


class TestAPIFallback:
    """Test behavior when httpx is not available or server unreachable."""

    def test_scan_without_http(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._http = None
        result = client.scan()
        assert result == []

    def test_predict_without_http(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._http = None
        result = client.predict("m1")
        assert "error" in result

    def test_paper_status_without_http(self) -> None:
        client = CashClaw(api_key="test", tier="starter")
        client._http = None
        status = client.paper_status()
        assert status.running is False
