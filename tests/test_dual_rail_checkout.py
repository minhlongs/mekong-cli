"""Tests for Dual-Rail Checkout (VietQR + NOWPayments) & Polar.sh decommission."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.raas_license_verifier import verify_license_key
from src.raas.checkout_router import router as checkout_router
from src.raas.revenue_router import router as revenue_router

app = FastAPI()
app.include_router(checkout_router)
app.include_router(revenue_router)
client = TestClient(app)


def test_get_pricing_tiers() -> None:
    res = client.get("/v1/pricing")
    assert res.status_code == 200
    data = res.json()
    tier_names = [t["tier"].upper() for t in data["tiers"]]
    assert "BASIC" in tier_names
    assert "PREMIUM" in tier_names
    assert "ENTERPRISE" in tier_names
    assert "MASTER" in tier_names
    assert "vietqr" in data["allowed_rails"]
    assert "nowpayments" in data["allowed_rails"]


def test_create_checkout_vietqr() -> None:
    payload = {
        "tier": "PREMIUM",
        "rail": "vietqr",
        "email": "founder@mekong.ai",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tier"].upper() == "PREMIUM"
    assert data["rail"] == "vietqr"
    assert data["amount_usd"] == 399
    assert data["amount_vnd"] == 9975000
    assert "order_id" in data
    assert data["checkout_url"] != ""


def test_create_checkout_nowpayments() -> None:
    payload = {
        "tier": "ENTERPRISE",
        "rail": "nowpayments",
        "email": "builder@mekong.ai",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tier"].upper() == "ENTERPRISE"
    assert data["rail"] == "nowpayments"
    assert data["amount_usd"] == 799
    assert "order_id" in data


def test_checkout_status_and_license_provisioning() -> None:
    # 1. Pending status
    res = client.get("/v1/checkout/status?order_id=ord-pending-123")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending"
    assert data["license_key"] is None

    # 2. Simulated paid status returns a valid HMAC-SHA256 RAAS_LICENSE_KEY
    res_paid = client.get("/v1/checkout/status?order_id=ord-paid-789&simulate_paid=true")
    assert res_paid.status_code == 200
    data_paid = res_paid.json()
    assert data_paid["status"] == "paid"
    assert data_paid["license_key"] is not None

    key = data_paid["license_key"]
    verified = verify_license_key(key)
    assert verified.valid is True
    assert verified.tier.value == "PREMIUM"


def test_activate_license_and_check_status() -> None:
    # Get a real signed key
    res_paid = client.get("/v1/checkout/status?order_id=ord-paid-999&simulate_paid=true")
    key = res_paid.json()["license_key"]

    # Activate
    act_res = client.post("/v1/license/activate", json={"license_key": key})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["valid"] is True
    assert act_data["tier"] == "PREMIUM"

    # Query status
    stat_res = client.get("/v1/license/status")
    assert stat_res.status_code == 200
    stat_data = stat_res.json()
    assert "valid" in stat_data
    assert "tier" in stat_data


def test_polar_webhook_is_decommissioned_http_410() -> None:
    res = client.post("/webhook/polar", json={"event": "order.created"})
    assert res.status_code == 410
    data = res.json()
    detail = data["detail"]
    assert detail["error"] == "polar_rail_decommissioned"
    assert "vietqr" in detail["allowed_rails"]
    assert "nowpayments" in detail["allowed_rails"]
