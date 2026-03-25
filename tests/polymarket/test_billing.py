"""Tests for CashClaw billing — Polar.sh webhooks, subscriptions, tiers."""

import json
import os
import sqlite3
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.polymarket.billing import BillingDB, router, verify_polar_signature


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def billing_db(db_path):
    return BillingDB(db_path)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestBillingDB:
    """Test subscription database operations."""

    def test_provision_subscription(self, billing_db: BillingDB) -> None:
        sub = billing_db.provision_subscription(
            subscription_id="sub_001",
            user_id="user_001",
            email="test@example.com",
            tier="pro",
        )
        assert sub.subscription_id == "sub_001"
        assert sub.tier == "pro"
        assert sub.api_key.startswith("ck_")
        assert sub.active is True

    def test_get_by_api_key(self, billing_db: BillingDB) -> None:
        sub = billing_db.provision_subscription(
            subscription_id="sub_002",
            user_id="user_002",
            email="test2@example.com",
            tier="starter",
        )
        found = billing_db.get_by_api_key(sub.api_key)
        assert found is not None
        assert found.email == "test2@example.com"

    def test_get_by_api_key_not_found(self, billing_db: BillingDB) -> None:
        assert billing_db.get_by_api_key("nonexistent") is None

    def test_update_tier(self, billing_db: BillingDB) -> None:
        billing_db.provision_subscription(
            subscription_id="sub_003",
            user_id="user_003",
            email="test3@example.com",
            tier="starter",
        )
        result = billing_db.update_tier("sub_003", "elite")
        assert result is True

        sub = billing_db.get_by_subscription_id("sub_003")
        assert sub.tier == "elite"

    def test_cancel_subscription(self, billing_db: BillingDB) -> None:
        billing_db.provision_subscription(
            subscription_id="sub_004",
            user_id="user_004",
            email="test4@example.com",
            tier="pro",
        )
        result = billing_db.cancel_subscription("sub_004", grace_days=7)
        assert result is True

        sub = billing_db.get_by_subscription_id("sub_004")
        assert sub.active is False
        assert sub.grace_until is not None

    def test_count_active(self, billing_db: BillingDB) -> None:
        billing_db.provision_subscription("s1", "u1", "a@b.com", "starter")
        billing_db.provision_subscription("s2", "u2", "c@d.com", "starter")
        billing_db.provision_subscription("s3", "u3", "e@f.com", "pro")

        counts = billing_db.count_active()
        assert counts["starter"] == 2
        assert counts["pro"] == 1

    def test_log_event(self, billing_db: BillingDB) -> None:
        billing_db.log_event("subscription.created", "sub_001", '{"test": true}')
        with sqlite3.connect(billing_db.db_path) as conn:
            rows = conn.execute("SELECT * FROM billing_events").fetchall()
            assert len(rows) == 1


class TestWebhookSignature:
    """Test webhook signature verification."""

    def test_no_secret_allows(self) -> None:
        # When POLAR_WEBHOOK_SECRET not set, allow in dev mode
        assert verify_polar_signature(b"payload", "") is True

    def test_empty_signature_allowed_dev(self) -> None:
        assert verify_polar_signature(b"test", "") is True


class TestWebhookEndpoint:
    """Test Polar.sh webhook handling."""

    def test_subscription_created(self, client: TestClient) -> None:
        payload = {
            "type": "subscription.created",
            "data": {
                "object": {
                    "id": "sub_new",
                    "customer_id": "cust_001",
                    "customer_email": "new@example.com",
                    "product_id": "prod_starter",
                }
            },
        }
        resp = client.post(
            "/webhooks/polar",
            json=payload,
            headers={"X-Polar-Signature": ""},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "provisioned"
        assert data["tier"] == "starter"
        assert "api_key" in data

    def test_subscription_updated(self, client: TestClient) -> None:
        # First create
        client.post(
            "/webhooks/polar",
            json={
                "type": "subscription.created",
                "data": {"object": {
                    "id": "sub_upd", "customer_id": "c1",
                    "customer_email": "u@e.com", "product_id": "prod_starter",
                }},
            },
            headers={"X-Polar-Signature": ""},
        )
        # Then update
        resp = client.post(
            "/webhooks/polar",
            json={
                "type": "subscription.updated",
                "data": {"object": {"id": "sub_upd", "product_id": "prod_pro"}},
            },
            headers={"X-Polar-Signature": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["tier"] == "pro"

    def test_subscription_cancelled(self, client: TestClient) -> None:
        client.post(
            "/webhooks/polar",
            json={
                "type": "subscription.created",
                "data": {"object": {
                    "id": "sub_can", "customer_id": "c2",
                    "customer_email": "c@e.com", "product_id": "prod_starter",
                }},
            },
            headers={"X-Polar-Signature": ""},
        )
        resp = client.post(
            "/webhooks/polar",
            json={
                "type": "subscription.cancelled",
                "data": {"object": {"id": "sub_can"}},
            },
            headers={"X-Polar-Signature": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["grace_days"] == 7

    def test_payment_failed(self, client: TestClient) -> None:
        resp = client.post(
            "/webhooks/polar",
            json={
                "type": "payment.failed",
                "data": {"object": {"subscription_id": "sub_fail"}},
            },
            headers={"X-Polar-Signature": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["retry_days"] == 3

    def test_unknown_event_ignored(self, client: TestClient) -> None:
        resp = client.post(
            "/webhooks/polar",
            json={"type": "unknown.event", "data": {"object": {}}},
            headers={"X-Polar-Signature": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_invalid_json(self, client: TestClient) -> None:
        resp = client.post(
            "/webhooks/polar",
            content="not json",
            headers={"X-Polar-Signature": "", "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
