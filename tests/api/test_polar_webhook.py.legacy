"""
Unit tests for src/api/polar_webhook.py

Tests:
 - verify_webhook_signature (sig validation, timestamp checks)
 - process_subscription_created (tier detection, file I/O mocked)
 - process_subscription_cancelled (revocation logic, file I/O mocked)
 - process_order_created (trial key generation)
 - _is_event_duplicate (idempotency)
 - /api/v1/polar/webhook HTTP endpoint (all branches)
 - /api/v1/polar/test  health endpoint

External dependencies mocked:
 - hmac.new       (to control HMAC output)
 - Path.exists / open / json.load / json.dump (filesystem)
 - LicenseKeyGenerator.generate_key
 - datetime.now   (timestamp control)
"""

import json
import hmac as _hmac
import hashlib
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, mock_open


os.environ.setdefault("TESTING", "true")
os.environ.setdefault("AUTH_ENVIRONMENT", "dev")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECRET = "test-webhook-secret"


def _make_signature(payload: bytes, secret: str = _SECRET) -> str:
    """Produce a valid sha256= signature for the given payload and secret."""
    sig = _hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


# ---------------------------------------------------------------------------
# verify_webhook_signature
# ---------------------------------------------------------------------------

class TestVerifyWebhookSignature:
    """Pure-function signature verification logic."""

    def _run(self, payload, sig, timestamp=None, secret=_SECRET):
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", secret):
            from src.api.polar_webhook import verify_webhook_signature
            # Reload to pick up patched module-level var
            return verify_webhook_signature(payload, sig, timestamp)

    def test_valid_signature_returns_true(self):
        payload = b'{"type":"subscription.created"}'
        sig = _make_signature(payload)
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, sig) is True

    def test_wrong_signature_returns_false(self):
        payload = b'{"type":"subscription.created"}'
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, "sha256=deabeef") is False

    def test_missing_sha256_prefix_returns_false(self):
        payload = b'{"type":"order.created"}'
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, "invalidhex") is False

    def test_no_secret_configured_returns_true(self):
        """Dev mode: no secret → allow all (skip verification)."""
        payload = b'{"type":"order.created"}'
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, "sha256=anything") is True

    def test_fresh_timestamp_accepted(self):
        payload = b'{"type":"subscription.created"}'
        sig = _make_signature(payload)
        ts = _now_ts()
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, sig, timestamp=ts) is True

    def test_stale_timestamp_rejected(self):
        payload = b'{"type":"subscription.created"}'
        sig = _make_signature(payload)
        stale_ts = _now_ts() - 400  # 400s ago, > 300s tolerance
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            assert verify_webhook_signature(payload, sig, timestamp=stale_ts) is False

    def test_no_timestamp_skips_time_check(self):
        payload = b'{"type":"order.created"}'
        sig = _make_signature(payload)
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            from src.api.polar_webhook import verify_webhook_signature
            # timestamp=None → no time check, only sig check
            assert verify_webhook_signature(payload, sig, timestamp=None) is True

    def test_exception_during_verify_returns_false(self):
        """Any unexpected exception → return False."""
        payload = b"data"
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET), \
             patch("hmac.compare_digest", side_effect=Exception("explode")):
            from src.api.polar_webhook import verify_webhook_signature
            result = verify_webhook_signature(payload, _make_signature(payload))
        assert result is False


# ---------------------------------------------------------------------------
# process_subscription_created
# ---------------------------------------------------------------------------

class TestProcessSubscriptionCreated:
    """Tier detection and license generation."""

    def _event(self, product_name="Pro Plan", email="user@example.com", customer_id="cust-1", sub_id="sub-1"):
        return {
            "subscription": {
                "id": sub_id,
                "customer": {"id": customer_id, "email": email},
                "product": {"name": product_name},
            }
        }

    def _run(self, event_data, fake_key="raas-pro-ABCD-sig"):
        licenses_path = MagicMock()
        licenses_path.exists.return_value = False
        licenses_path.parent.mkdir = MagicMock()

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen, \
             patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("json.load", return_value={}), \
             patch("json.dump"):
            MockGen.return_value.generate_key.return_value = fake_key
            MockPath.return_value.__truediv__ = lambda self, other: licenses_path
            MockPath.home.return_value.__truediv__ = lambda self, other: MagicMock(
                exists=MagicMock(return_value=False),
                parent=MagicMock(mkdir=MagicMock()),
            )
            from src.api.polar_webhook import process_subscription_created
            return process_subscription_created(event_data)

    def test_happy_path_returns_license_key(self):
        result = self._run(self._event())
        assert result["status"] == "success"
        assert "license_key" in result
        assert "tier" in result
        assert "email" in result

    def test_enterprise_product_name_sets_starter_tier(self):
        """Source tier logic: only 'pro'/'growth'/'starter' keywords matched.
        'Enterprise Suite' has no matching keyword → defaults to 'starter'."""
        from src.api.polar_webhook import process_subscription_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen, \
             patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("json.load", return_value={}), \
             patch("json.dump"):
            MockGen.return_value.generate_key.return_value = "raas-starter-X-sig"
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path.parent = MagicMock()
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)

            result = process_subscription_created(self._event(product_name="Enterprise Suite"))
        assert result["tier"] == "starter"

    def test_trial_product_name_sets_starter_tier(self):
        """Source tier logic: 'Free Trial' has no matching keyword → defaults to 'starter'."""
        from src.api.polar_webhook import process_subscription_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen, \
             patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("json.load", return_value={}), \
             patch("json.dump"):
            MockGen.return_value.generate_key.return_value = "raas-starter-X-sig"
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path.parent = MagicMock()
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)

            result = process_subscription_created(self._event(product_name="Free Trial"))
        assert result["tier"] == "starter"

    def test_free_starter_product_name_sets_starter_tier(self):
        """Source tier logic: 'Free Starter' contains 'starter' keyword → tier 'starter'."""
        from src.api.polar_webhook import process_subscription_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen, \
             patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("json.load", return_value={}), \
             patch("json.dump"):
            MockGen.return_value.generate_key.return_value = "raas-starter-X-sig"
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path.parent = MagicMock()
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)

            result = process_subscription_created(self._event(product_name="Free Starter"))
        assert result["tier"] == "starter"

    def test_unknown_product_defaults_to_starter(self):
        """Source tier logic: unknown product name → defaults to 'starter'."""
        from src.api.polar_webhook import process_subscription_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen, \
             patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("json.load", return_value={}), \
             patch("json.dump"):
            MockGen.return_value.generate_key.return_value = "raas-starter-X-sig"
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path.parent = MagicMock()
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)

            result = process_subscription_created(self._event(product_name="Mekong Business"))
        assert result["tier"] == "starter"


# ---------------------------------------------------------------------------
# process_subscription_cancelled
# ---------------------------------------------------------------------------

class TestProcessSubscriptionCancelled:
    def _event(self, sub_id="sub-cancel-1"):
        return {"subscription": {"id": sub_id}}

    def test_matching_subscription_revoked(self):
        from src.api.polar_webhook import process_subscription_cancelled

        licenses = {
            "raas-pro-KEY123-sig": {
                "subscription_id": "sub-cancel-1",
                "customer_email": "a@b.com",
                "tier": "pro",
                "status": "active",
            }
        }
        revoked_list: list = []

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open()), \
             patch("json.load", side_effect=[revoked_list, licenses]), \
             patch("json.dump"):
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)
            result = process_subscription_cancelled(self._event())

        assert result["status"] == "success"
        assert result["revoked"] is True

    def test_no_matching_subscription_revoked_count_zero(self):
        from src.api.polar_webhook import process_subscription_cancelled

        licenses = {
            "raas-pro-KEY999-sig": {
                "subscription_id": "sub-OTHER",
                "tier": "pro",
                "status": "active",
            }
        }

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open()), \
             patch("json.load", side_effect=[[], licenses]), \
             patch("json.dump"):
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)
            result = process_subscription_cancelled(self._event("sub-cancel-NOMATCH"))

        assert result["status"] == "success"
        assert result["revoked_count"] == 0

    def test_empty_licenses_file_graceful(self):
        from src.api.polar_webhook import process_subscription_cancelled

        mock_path = MagicMock()
        mock_path.exists.return_value = True

        with patch("src.api.polar_webhook.Path") as MockPath, \
             patch("builtins.open", mock_open()), \
             patch("json.load", side_effect=[[], {}]), \
             patch("json.dump"):
            MockPath.home.return_value.__truediv__ = MagicMock(return_value=mock_path)
            result = process_subscription_cancelled(self._event())

        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# process_order_created
# ---------------------------------------------------------------------------

class TestProcessOrderCreated:
    def _event(self, email="buyer@example.com"):
        return {"order": {"customer": {"email": email}}}

    def test_generates_trial_license(self):
        from src.api.polar_webhook import process_order_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen:
            MockGen.return_value.generate_key.return_value = "raas-trial-XYZ-sig"
            result = process_order_created(self._event())

        assert result["status"] == "success"
        assert result["tier"] == "trial"
        assert result["license_key"] == "raas-trial-XYZ-sig"

    def test_calls_generate_key_with_30_days(self):
        from src.api.polar_webhook import process_order_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen:
            MockGen.return_value.generate_key.return_value = "raas-trial-ABC-sig"
            process_order_created(self._event("buyer@example.com"))

            _, kwargs = MockGen.return_value.generate_key.call_args
            assert kwargs.get("days") == 30 or (
                len(MockGen.return_value.generate_key.call_args[0]) >= 3
                and MockGen.return_value.generate_key.call_args[0][2] == 30
            )

    def test_email_included_in_result(self):
        from src.api.polar_webhook import process_order_created

        with patch("src.api.polar_webhook.LicenseKeyGenerator") as MockGen:
            MockGen.return_value.generate_key.return_value = "raas-trial-ZZZ-sig"
            result = process_order_created(self._event("custom@email.com"))

        assert result["email"] == "custom@email.com"


# ---------------------------------------------------------------------------
# _is_event_duplicate
# ---------------------------------------------------------------------------

class TestIsEventDuplicate:
    def setup_method(self):
        """Clear the in-memory idempotency store before each test."""
        import src.api.polar_webhook as mod
        mod._processed_events.clear()

    def test_first_call_not_duplicate(self):
        from src.api.polar_webhook import _is_event_duplicate
        assert _is_event_duplicate("evt-001") is False

    def test_second_call_is_duplicate(self):
        from src.api.polar_webhook import _is_event_duplicate
        _is_event_duplicate("evt-002")
        assert _is_event_duplicate("evt-002") is True

    def test_different_ids_not_duplicates(self):
        from src.api.polar_webhook import _is_event_duplicate
        assert _is_event_duplicate("evt-003") is False
        assert _is_event_duplicate("evt-004") is False


# ---------------------------------------------------------------------------
# HTTP endpoint tests — /api/v1/polar/webhook
# ---------------------------------------------------------------------------

@pytest.fixture()
def polar_client():
    """Build a minimal FastAPI app containing just the polar router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Ensure idempotency store is clean for each test
    import src.api.polar_webhook as mod
    mod._processed_events.clear()

    from src.api.polar_webhook import router
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def _post_webhook(client, payload: dict, secret=None, ts: int | None = None, extra_headers=None):
    """Helper to POST a JSON webhook with proper headers."""
    body = json.dumps(payload).encode()
    sig = _make_signature(body, secret or _SECRET) if secret else "sha256=invalid"

    headers = {"Content-Type": "application/json", "X-Polar-Signature": sig}
    if ts is not None:
        headers["X-Polar-Timestamp"] = str(ts)
    if extra_headers:
        headers.update(extra_headers)

    return client.post("/webhook/polar", content=body, headers=headers)


class TestWebhookEndpointSecurity:
    def test_wrong_content_type_returns_400(self, polar_client):
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            resp = polar_client.post(
                "/webhook/polar",
                content=b"{}",
                headers={"Content-Type": "text/plain", "X-Polar-Signature": "sha256=x"},
            )
        assert resp.status_code == 400

    def test_invalid_signature_returns_401(self, polar_client):
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            resp = polar_client.post(
                "/webhook/polar",
                content=b'{"type":"subscription.created"}',
                headers={
                    "Content-Type": "application/json",
                    "X-Polar-Signature": "sha256=deadbeef",
                },
            )
        assert resp.status_code == 401

    def test_stale_timestamp_returns_401(self, polar_client):
        payload = {"type": "subscription.created"}
        body = json.dumps(payload).encode()
        sig = _make_signature(body)
        stale_ts = _now_ts() - 400

        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            resp = polar_client.post(
                "/webhook/polar",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Polar-Signature": sig,
                    "X-Polar-Timestamp": str(stale_ts),
                },
            )
        assert resp.status_code == 401

    def test_invalid_json_returns_400(self, polar_client):
        body = b"not-json"
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            resp = polar_client.post(
                "/webhook/polar",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Polar-Signature": "sha256=anything",
                },
            )
        assert resp.status_code == 400


class TestWebhookEndpointRouting:
    def test_subscription_created_calls_handler(self, polar_client):
        payload = {
            "id": "evt-unique-1",
            "type": "subscription.created",
            "subscription": {
                "id": "sub-1",
                "customer": {"id": "cust-1", "email": "user@test.com"},
                "product": {"name": "Pro Plan"},
            },
        }
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None), \
             patch("src.api.polar_webhook.process_subscription_created") as mock_handler:
            mock_handler.return_value = {"status": "success", "license_key": "k", "tier": "pro", "email": "u@t.com"}
            resp = polar_client.post(
                "/webhook/polar",
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"},
            )

        assert resp.status_code == 200
        mock_handler.assert_called_once()

    def test_subscription_cancelled_calls_handler(self, polar_client):
        payload = {
            "id": "evt-unique-2",
            "type": "subscription.cancelled",
            "subscription": {"id": "sub-1"},
        }
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None), \
             patch("src.api.polar_webhook.process_subscription_cancelled") as mock_handler:
            mock_handler.return_value = {"status": "success", "revoked": True, "revoked_count": 1}
            resp = polar_client.post(
                "/webhook/polar",
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"},
            )

        assert resp.status_code == 200
        mock_handler.assert_called_once()

    def test_order_created_calls_handler(self, polar_client):
        payload = {
            "id": "evt-unique-3",
            "type": "order.created",
            "order": {"customer": {"email": "buyer@test.com"}},
        }
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None), \
             patch("src.api.polar_webhook.process_order_created") as mock_handler:
            mock_handler.return_value = {"status": "success", "license_key": "k", "tier": "trial", "email": "b@t.com"}
            resp = polar_client.post(
                "/webhook/polar",
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"},
            )

        assert resp.status_code == 200
        mock_handler.assert_called_once()

    def test_unknown_event_type_returns_ignored(self, polar_client):
        payload = {"id": "evt-unique-4", "type": "payment.refunded"}
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            resp = polar_client.post(
                "/webhook/polar",
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"},
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_duplicate_event_returns_duplicate_status(self, polar_client):
        payload = {"id": "evt-dup-1", "type": "order.created"}

        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            headers = {"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"}
            body = json.dumps(payload).encode()

            # First request
            polar_client.post("/webhook/polar", content=body, headers=headers)
            # Second request (same event_id)
            resp = polar_client.post("/webhook/polar", content=body, headers=headers)

        assert resp.json()["status"] == "duplicate"
        assert resp.json()["event_id"] == "evt-dup-1"

    def test_handler_exception_returns_500(self, polar_client):
        payload = {"id": "evt-unique-5", "type": "subscription.created"}
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None), \
             patch("src.api.polar_webhook.process_subscription_created", side_effect=RuntimeError("db fail")):
            resp = polar_client.post(
                "/webhook/polar",
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-Polar-Signature": "sha256=x"},
            )

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# /api/v1/polar/test — health check
# ---------------------------------------------------------------------------

class TestWebhookTestEndpoint:
    def test_returns_ok(self, polar_client):
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", _SECRET):
            resp = polar_client.get("/webhook/polar/test")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["secret_configured"] is True
        assert data["timestamp_tolerance"] == 300

    def test_no_secret_configured(self, polar_client):
        with patch("src.api.polar_webhook.POLAR_WEBHOOK_SECRET", None):
            resp = polar_client.get("/webhook/polar/test")

        assert resp.json()["secret_configured"] is False
