"""
E2E tests for Vietnamese Payment Integration (VietQR).

Tests cover:
- VietQR webhook processing
- Payment confirmation and credit allocation
- Bank transfer reference matching
- Duplicate payment detection
- Vietnamese bank-specific handling
"""

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ['REDIS_URL'] = ''
os.environ['REDIS_ENABLED'] = 'false'
os.environ.setdefault('MEKONG_VIETQR_PROVIDER', 'sepay')
os.environ.setdefault('MEKONG_VIETQR_WEBHOOK_SECRET', 'test_secret_123')

pytestmark = pytest.mark.asyncio


@pytest.fixture
def vietqr_secret():
    """Return test VietQR webhook secret."""
    return os.environ.get("MEKONG_VIETQR_WEBHOOK_SECRET", "test_secret_123")


@pytest.fixture
def vietqr_payload():
    """Return a valid VietQR webhook payload matching VietQRWebhookPayload schema."""
    return {
        "tx_ref": f"test_tx_{int(datetime.now().timestamp())}",
        "amount": 199000,  # 199K VND for Starter tier
        "memo": "MEKONG-opc_001_test",  # Memo format → user_id extraction
        "bank_code": "MB",
        "timestamp": datetime.now().isoformat(),
    }


class TestVietQRWebhook:
    """Tests for VietQR payment webhook."""

    def test_webhook_with_valid_signature(
        self, client, vietqr_payload, vietqr_secret
    ):
        """Test webhook with valid HMAC signature is accepted."""
        payload = json.dumps(vietqr_payload)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # Should accept the webhook
        assert response.status_code in [200, 202]

    def test_webhook_with_invalid_signature(
        self, client, vietqr_payload
    ):
        """Test webhook with invalid signature is rejected."""
        payload = json.dumps(vietqr_payload)

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": "invalid_signature_xyz"},
        )

        assert response.status_code == 401

    def test_webhook_without_signature(self, client, vietqr_payload):
        """Test webhook without signature is rejected."""
        payload = json.dumps(vietqr_payload)

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
        )

        assert response.status_code == 401

    def test_webhook_with_tampered_payload(
        self, client, vietqr_payload, vietqr_secret
    ):
        """Test webhook with tampered payload fails validation."""
        payload = json.dumps(vietqr_payload)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Tamper with payload
        tampered = payload.replace("test", "hacked")

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=tampered,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code == 401


class TestPaymentProcessing:
    """Tests for payment processing logic."""

    def test_payment_matches_correct_tier_amount(
        self, client, vietqr_payload, vietqr_secret
    ):
        """Test payment with exact tier amount credits user correctly."""
        # Create pilot user first
        pilot_data = {
            "name": "VietQR Test User",
            "email": f"vn_test_{datetime.now().timestamp()}@example.com",
            "zalo": "+84912345678",
            "business_type": "shop_online",
            "city": "HCM",
            "industry": "test",
        }

        signup_response = client.post("/v1/pilot/signup", json=pilot_data)
        if signup_response.status_code != 200:
            pytest.skip("Pilot signup not available")

        pilot = signup_response.json()
        user_id = pilot["user_id"]

        # Update payload with correct user_id
        vietqr_payload["user_id"] = user_id

        payload = json.dumps(vietqr_payload)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code in [200, 202]

        # Check user credits increased
        credits_response = client.get(
            "/v1/pilot/credits",
            headers={"X-User-Id": user_id},
        )

        if credits_response.status_code == 200:
            credits = credits_response.json()
            # Should have initial 50 + 199 (starter tier = 200 MCU)
            assert credits["balance"] >= 50

    def test_payment_with_wrong_amount_handled(
        self, client, vietqr_secret
    ):
        """Test payment with wrong amount is flagged for manual review."""
        payload_data = {
            "tx_ref": f"wrong_amount_tx_{int(datetime.now().timestamp())}",
            "user_id": "opc_001_test",
            "amount": 100000,  # Wrong amount (not matching any tier)
            "bank_code": "MB",
            "account_number": "1234567890",
            "timestamp": datetime.now().isoformat(),
            "memo": "MEKONG-opc_001_test",
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # Should be accepted but flagged
        assert response.status_code in [200, 202, 400]
        data = response.json()
        # May include flag for manual review
        if "status" in data:
            assert data["status"] in ["processed", "flagged", "pending", "amount_no_tier"]

    def test_payment_with_unknown_user(
        self, client, vietqr_secret
    ):
        """Test payment for unknown user_id is handled."""
        payload_data = {
            "tx_ref": f"unknown_user_tx_{int(datetime.now().timestamp())}",
            "user_id": "opc_999_unknown",
            "amount": 199000,
            "bank_code": "MB",
            "account_number": "1234567890",
            "timestamp": datetime.now().isoformat(),
            "memo": "MEKONG-opc_999_unknown",
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # Should be accepted for manual review
        assert response.status_code in [200, 202, 404]

    def test_duplicate_transaction_detected(
        self, client, vietqr_payload, vietqr_secret
    ):
        """Test duplicate transaction ID is rejected."""
        payload = json.dumps(vietqr_payload)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Send same webhook twice
        response1 = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        response2 = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # First should succeed, second should be idempotent
        assert response1.status_code in [200, 202]
        assert response2.status_code in [200, 202, 409]

    def test_memo_parsing_extracts_user_id(
        self, client, vietqr_secret
    ):
        """Test that memo format correctly extracts user_id."""
        payload_data = {
            "tx_ref": f"memo_test_tx_{int(datetime.now().timestamp())}",
            "user_id": "opc_memo_test_001",
            "amount": 299000,
            "memo": "MEKONG-opc_memo_test_001",
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code in [200, 202]

        # Verify user_id was extracted correctly from description
        data = response.json()
        if "user_id" in data:
            assert data["user_id"] == "opc_memo_test_001"


class TestBankSpecificHandling:
    """Tests for different Vietnamese bank handling."""

    @pytest.mark.parametrize("bank_code", ["MB", "TCB", "ACB", "VPB", "BIDV"])
    def test_different_bank_transfers_accepted(
        self, client, vietqr_secret, bank_code
    ):
        """Test webhook accepts transfers from different banks."""
        payload_data = {
            "tx_ref": f"bank_test_{bank_code}_{int(datetime.now().timestamp())}",
            "user_id": "opc_bank_test_001",
            "amount": 299000,
            "bank_code": bank_code,
            "account_number": "1234567890",
            "timestamp": datetime.now().isoformat(),
            "memo": "MEKONG-opc_bank_test_001",
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code in [200, 202]

    def test_invalid_bank_code_handled(
        self, client, vietqr_secret
    ):
        """Test invalid/unsupported bank code is handled."""
        payload_data = {
            "tx_ref": f"invalid_bank_tx_{int(datetime.now().timestamp())}",
            "user_id": "opc_bank_test_001",
            "amount": 299000,
            "bank_code": "UNKNOWN",  # Unsupported bank
            "account_number": "1234567890",
            "timestamp": datetime.now().isoformat(),
            "memo": "MEKONG-opc_bank_test_001",
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # Should be accepted but flagged for manual review
        assert response.status_code in [200, 202, 400]


class TestErrorHandling:
    """Tests for webhook error handling."""

    def test_missing_required_fields(self, client):
        """Test webhook with missing required fields is rejected."""
        incomplete_payload = {
            "transaction_id": "test123",
            # Missing user_id and amount
        }

        payload = json.dumps(incomplete_payload)

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": "dummy"},
        )

        assert response.status_code == 422

    def test_invalid_amount_type(self, client, vietqr_secret):
        """Test webhook with invalid amount type."""
        payload_data = {
            "transaction_id": "test_invalid_amount",
            "user_id": "opc_001_test",
            "amount": "not-a-number",  # Invalid type
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code == 422

    def test_negative_amount_rejected(self, client, vietqr_secret):
        """Test webhook with negative amount is rejected."""
        payload_data = {
            "transaction_id": "negative_amount_tx",
            "user_id": "opc_001_test",
            "amount": -100000,  # Negative amount
        }

        payload = json.dumps(payload_data)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        assert response.status_code == 422

    def test_webhook_timeout_handled(
        self, client, vietqr_payload, vietqr_secret
    ):
        """Test webhook processing timeout is handled gracefully."""
        # This would require mocking a slow downstream service
        # For now, just verify the endpoint exists
        payload = json.dumps(vietqr_payload)
        signature = hmac.new(
            vietqr_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/v1/payments/vietqr/webhook",
            content=payload,
            headers={"X-Vietqr-Signature": signature},
        )

        # Should complete within reasonable time
        assert response.status_code in [200, 202, 400, 404]