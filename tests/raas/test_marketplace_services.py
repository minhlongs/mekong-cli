"""Tests for marketplace backend services (Phase 4)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from src.raas.marketplace.payout import (
    MINIMUM_PAYOUT_CENTS,
    calculate_payout,
    is_payout_eligible,
    monthly_settlement_report,
)
from src.raas.marketplace.license import verify_license_key, verify_purchase
from src.raas.marketplace.metering import PluginUsageMeter, UsageEvent


class TestCalculatePayout:
    def test_split_sums_to_gross(self):
        result = calculate_payout(1000)
        assert result["developer_share_cents"] + result["platform_share_cents"] == 1000

    def test_zero_gross(self):
        result = calculate_payout(0)
        assert result["developer_share_cents"] == 0
        assert result["platform_share_cents"] == 0

    def test_returns_structure(self):
        result = calculate_payout(1500)
        assert "gross_cents" in result
        assert "split" in result


class TestPayoutEligibility:
    def test_below_threshold(self):
        assert is_payout_eligible(4999) is False

    def test_at_threshold(self):
        assert is_payout_eligible(5000) is True

    def test_above_threshold(self):
        assert is_payout_eligible(25000) is True


class TestMonthlySettlement:
    def test_sums_transactions(self):
        txs = [
            {"amount_cents": 5000, "plugin_id": "com.example.plugin"},
            {"amount_cents": 5000, "plugin_id": "com.example.plugin"},
        ]
        report = monthly_settlement_report("com.example.plugin", txs)
        assert report["gross_cents"] == 10000
        assert report["eligible_for_payout"] is True

    def test_no_transactions_zero(self):
        report = monthly_settlement_report("com.example.plugin", [])
        assert report["gross_cents"] == 0
        assert report["eligible_for_payout"] is False


class TestVerifyLicenseKey:
    def test_valid_key_format(self):
        import hashlib
        import hmac
        import os

        secret = "test-secret"
        plugin_id = "com.example.plugin"
        user_id = "user-123"
        payload = f"{plugin_id}:{user_id}".encode()
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()[:32]
        license_key = f"lp_{expected}"
        os.environ["MEKONG_LICENSE_SECRET"] = secret
        result = verify_license_key(license_key, plugin_id, user_id)
        assert result["valid"] is True
        assert result["plugin_id"] == plugin_id

    def test_invalid_key_rejected(self):
        import pytest

        with pytest.raises(Exception):
            verify_license_key("lp_fakekey", "com.example.plugin", "user-1")

    def test_missing_prefix_rejected(self):
        import pytest

        with pytest.raises(Exception):
            verify_license_key("no-prefix", "com.example.plugin", "user-1")


class TestVerifyPurchase:
    def test_valid_purchase(self):
        result = verify_purchase("pur_abc123", "com.example.plugin", 500)
        assert result["verified"] is True
        assert result["purchase_id"] == "pur_abc123"

    def test_invalid_purchase_id(self):
        result = verify_purchase("bad-id", "com.example.plugin", 500)
        assert result["verified"] is False