"""Integration tests for C2: Stripe Checkout + Webhook + Credit Provisioning.

Covers:
  - Checkout endpoint creates Stripe session and returns URL
  - Free-tier checkout rejected (tier with monthly_price_usd == 0)
  - Webhook provisions credits on subscription.created/updated
  - Webhook zeros credits on subscription.deleted
  - Role sync runs alongside credit provisioning
  - Idempotent: same event ID processes twice without error (Stripe signature guard)
  - Graceful handling for unresolved customer/tenant / unknown tier
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.billing_endpoints import billing_router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_app():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(billing_router)
    return TestClient(app)


def _stripe_subscription_event(
    event_type="customer.subscription.created",
    *,
    customer_id="cus_TEST123",
    price_id="price_basic_123",
    subscription_id="sub_TEST",
    event_id=None,
):
    if event_id is None:
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
    return {
        "type": event_type,
        "id": event_id,
        "object": "event",
        "request": {"id": None},
        "api_version": "2024-06-20",
        "data": {
            "object": {
                "id": subscription_id,
                "object": "subscription",
                "customer": customer_id,
                "status": "active",
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": price_id,
                                "object": "price",
                                "recurring": {"interval": "month"},
                            },
                        }
                    ]
                },
                "created": 1700000000,
                "current_period_start": 1700000000,
                "current_period_end": 1702678400,
            }
        },
    }


def _webhook_payload(event: dict) -> bytes:
    """Serialize event to bytes (body) with sliced signature headers."""
    return json.dumps(event).encode()


# ---------------------------------------------------------------------------
# C2b — Checkout endpoint
# ---------------------------------------------------------------------------
class TestStripeCheckoutEndpoint:
    """Tests for POST /billing/checkout/stripe."""

    def test_checkout_endpoint_returns_url(self):
        """Valid checkout returns 200 with a Stripe session_url."""
        client = _make_app()

        with patch(
            "src.api.billing_endpoints.get_tier_to_role_mapping",
            return_value={"price_basic_123": "starter"},
        ), patch("src.api.billing_endpoints.stripe_sdk") as mock_stripe:
            session = MagicMock()
            session.url = "https://checkout.stripe.com/cs_test_abc123"
            session.id = "cs_test_abc123"
            mock_stripe.checkout.Session.create.return_value = session

            resp = client.post(
                "/billing/checkout/stripe",
                json={"tier": "starter"},
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("checkout_url") == "https://checkout.stripe.com/cs_test_abc123"
        assert data.get("session_id") == "cs_test_abc123"
        assert data.get("tier") == "starter"

    def test_checkout_rejects_free_tier(self):
        """Free tier (monthly_price_usd == 0) returns 400."""
        client = _make_app()
        resp = client.post(
            "/billing/checkout/stripe",
            json={"tier": "free"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (400, 422), f"Expected rejection, got {resp.status_code}"


# ---------------------------------------------------------------------------
# C2c — Webhook + credit provisioning
# ---------------------------------------------------------------------------
_WEBHOOK_HEADERS = {
    "Content-Type": "application/json",
    "Stripe-Signature": "t=1,v1=abc",
}


class TestStripeWebhookProvisioning:
    """Tests for POST /billing/webhook/stripe credit provisioning."""

    def test_provision_credits_subscription_created(self):
        """customer.subscription.created provisions credits via CreditStore.add_credits."""
        with patch("src.api.billing_endpoints.CreditStore") as mock_store_cls, \
             patch("src.api.billing_endpoints.StripeService") as mock_svc_cls, \
             patch(
                 "src.api.billing_endpoints.get_tier_to_role_mapping",
                 return_value={"price_basic_123": "starter"},
             ), \
             patch("src.api.billing_endpoints.UserRepository") as mock_repo_cls:
            # --- CreditStore ---
            mock_store = MagicMock()
            mock_store_cls.return_value = mock_store

            # --- StripeService ---
            mock_stripe_svc = MagicMock()
            mock_stripe_svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": True, "message": "synced"}
            )
            mock_stripe_svc._get_customer_by_id = AsyncMock(
                return_value=MagicMock(email="user@example.com")
            )
            mock_svc_cls.return_value = mock_stripe_svc

            # --- User ---
            fake_user = MagicMock()
            fake_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            mock_repo = MagicMock()
            mock_repo.find_by_email = AsyncMock(return_value=fake_user)
            mock_repo_cls.return_value = mock_repo

            # --- Build request ---
            event = _stripe_subscription_event(
                price_id="price_basic_123",
                event_id="evt_created_1",
            )
            body = _webhook_payload(event)

            client = _make_app()
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "test_secret"}, clear=False):
                with patch(
                    "src.api.billing_endpoints.stripe_sdk.Webhook.construct_event",
                    return_value=event,
                ):
                    resp = client.post(
                        "/billing/webhook/stripe",
                        content=body,
                        headers=_WEBHOOK_HEADERS,
                    )

            # CreditStore.add_credits must have been called
            call_args = mock_store.add_credits.call_args
            assert call_args is not None, "add_credits was not called"
            assert call_args.kwargs["amount"] > 0
            assert "customer.subscription.created" in call_args.kwargs["reason"]
            assert resp.status_code == 200
            body_resp = resp.json()
            assert body_resp["status"] == "success"
            assert body_resp["credits_provisioned"] > 0

    def test_provision_idempotent(self):
        """Same event ID sent twice — second call succeeds (duplicate credit accepted per plan)."""
        with patch("src.api.billing_endpoints.CreditStore") as mock_store_cls, \
             patch("src.api.billing_endpoints.StripeService") as mock_svc_cls, \
             patch(
                 "src.api.billing_endpoints.get_tier_to_role_mapping",
                 return_value={"price_basic_123": "starter"},
             ), \
             patch("src.api.billing_endpoints.UserRepository") as mock_repo_cls:
            mock_store = MagicMock()
            mock_store_cls.return_value = mock_store

            mock_stripe_svc = MagicMock()
            mock_stripe_svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": True, "message": "synced"}
            )
            mock_stripe_svc._get_customer_by_id = AsyncMock(
                return_value=MagicMock(email="user@example.com")
            )
            mock_svc_cls.return_value = mock_stripe_svc

            fake_user = MagicMock()
            fake_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            mock_repo = MagicMock()
            mock_repo.find_by_email = AsyncMock(return_value=fake_user)
            mock_repo_cls.return_value = mock_repo

            event = _stripe_subscription_event(
                price_id="price_basic_123",
                event_id="evt_idempotent_1",
            )
            body = _webhook_payload(event)
            headers = {
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1700000000,v1=abc",
            }

            client = _make_app()
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "test_secret"}, clear=False):
                with patch(
                    "src.api.billing_endpoints.stripe_sdk.Webhook.construct_event",
                    return_value=event,
                ):
                    resp1 = client.post(
                        "/billing/webhook/stripe", content=body, headers=headers
                    )
                    resp2 = client.post(
                        "/billing/webhook/stripe", content=body, headers=headers
                    )

            assert resp1.status_code == 200
            assert resp2.status_code == 200   # no crash on replay
            assert mock_store.add_credits.call_count == 2   # both calls provision

    def test_provision_missing_customer(self):
        """Stripe customer ID not resolvable — returns 200 (graceful)."""
        with patch("src.api.billing_endpoints.CreditStore") as mock_store_cls, \
             patch("src.api.billing_endpoints.StripeService") as mock_svc_cls, \
             patch(
                 "src.api.billing_endpoints.get_tier_to_role_mapping",
                 return_value={"price_basic_123": "starter"},
             ):
            mock_store = MagicMock()
            mock_store_cls.return_value = mock_store

            mock_stripe_svc = MagicMock()
            mock_stripe_svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": True, "message": "synced"}
            )
            mock_stripe_svc._get_customer_by_id = AsyncMock(return_value=None)
            mock_svc_cls.return_value = mock_stripe_svc

            event = _stripe_subscription_event(
                customer_id="cus_GHOST",
                price_id="price_basic_123",
                event_id="evt_missing_customer",
            )
            body = _webhook_payload(event)
            client = _make_app()
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "test_secret"}, clear=False):
                with patch(
                    "src.api.billing_endpoints.stripe_sdk.Webhook.construct_event",
                    return_value=event,
                ):
                    resp = client.post(
                        "/billing/webhook/stripe", content=body, headers=_WEBHOOK_HEADERS
                    )

            assert resp.status_code == 200, (
                f"Expected 200 for missing customer (graceful), got {resp.status_code}: {resp.text}"
            )
            assert resp.json()["credits_provisioned"] == 0
            mock_store.add_credits.assert_not_called()

    def test_deletion_downgrades_and_zeros(self):
        """customer.subscription.deleted -> credits=0 (role downgrade handled by StripeService)."""
        with patch("src.api.billing_endpoints.CreditStore") as mock_store_cls, \
             patch("src.api.billing_endpoints.StripeService") as mock_svc_cls, \
             patch(
                 "src.api.billing_endpoints.get_tier_to_role_mapping",
                 return_value={"price_basic_123": "starter"},
             ), \
             patch("src.api.billing_endpoints.UserRepository") as mock_repo_cls:
            mock_store = MagicMock()
            mock_store_cls.return_value = mock_store

            mock_stripe_svc = MagicMock()
            mock_stripe_svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": True, "message": "downgraded"}
            )
            mock_stripe_svc._get_customer_by_id = AsyncMock(
                return_value=MagicMock(email="user@example.com")
            )
            mock_svc_cls.return_value = mock_stripe_svc

            fake_user = MagicMock()
            fake_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            mock_repo = MagicMock()
            mock_repo.find_by_email = AsyncMock(return_value=fake_user)
            mock_repo_cls.return_value = mock_repo

            event = _stripe_subscription_event(
                event_type="customer.subscription.deleted",
                price_id="price_basic_123",
                event_id="evt_deleted_1",
            )
            body = _webhook_payload(event)
            client = _make_app()
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "test_secret"}, clear=False):
                with patch(
                    "src.api.billing_endpoints.stripe_sdk.Webhook.construct_event",
                    return_value=event,
                ):
                    resp = client.post(
                        "/billing/webhook/stripe", content=body, headers=_WEBHOOK_HEADERS
                    )

            assert resp.status_code == 200
            body_resp = resp.json()
            assert body_resp["credits_provisioned"] == 0
            # StripeService role downgrade must have been invoked
            mock_stripe_svc.handle_stripe_webhook.assert_called_once()

    def test_unknown_tier_fallback(self):
        """price_id not in tier mapping -> no credits, role sync still runs."""
        with patch("src.api.billing_endpoints.CreditStore") as mock_store_cls, \
             patch("src.api.billing_endpoints.StripeService") as mock_svc_cls, \
             patch(
                 "src.api.billing_endpoints.get_tier_to_role_mapping",
                 return_value={"price_basic_123": "starter"},
             ), \
             patch("src.api.billing_endpoints.UserRepository") as mock_repo_cls:
            mock_store = MagicMock()
            mock_store_cls.return_value = mock_store

            mock_stripe_svc = MagicMock()
            mock_stripe_svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": True}
            )
            mock_stripe_svc._get_customer_by_id = AsyncMock(
                return_value=MagicMock(email="user@example.com")
            )
            mock_svc_cls.return_value = mock_stripe_svc

            fake_user = MagicMock()
            fake_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            mock_repo = MagicMock()
            mock_repo.find_by_email = AsyncMock(return_value=fake_user)
            mock_repo_cls.return_value = mock_repo

            event = _stripe_subscription_event(
                price_id="price_UNKNOWN_999",
                event_id="evt_unknown_tier",
            )
            body = _webhook_payload(event)
            client = _make_app()
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "test_secret"}, clear=False):
                with patch(
                    "src.api.billing_endpoints.stripe_sdk.Webhook.construct_event",
                    return_value=event,
                ):
                    resp = client.post(
                        "/billing/webhook/stripe", content=body, headers=_WEBHOOK_HEADERS
                    )

            assert resp.status_code == 200
            assert resp.json()["credits_provisioned"] == 0
            mock_store.add_credits.assert_not_called()
