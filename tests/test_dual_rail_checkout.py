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
    assert data["jurisdiction"] == "VN"


def test_get_pricing_does_not_advertise_crypto_rail_to_vietnam() -> None:
    # An unidentified caller is treated as Vietnamese and must not be offered
    # the crypto rail it would then ask for and be refused.
    res = client.get("/v1/pricing")
    data = res.json()
    assert "nowpayments" not in data["allowed_rails"]
    for tier in data["tiers"]:
        assert tier["rails"] == ["vietqr"]


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
        "jurisdiction": "SG",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tier"].upper() == "ENTERPRISE"
    assert data["rail"] == "nowpayments"
    assert data["amount_usd"] == 799
    assert "order_id" in data


def test_vn_org_cannot_select_crypto_rail() -> None:
    """A Vietnamese licensee must not be able to settle on the USDT rail."""
    payload = {
        "tier": "PREMIUM",
        "rail": "nowpayments",
        "email": "ceo@doanhnghiep.vn",
        "org_id": "VN-acme",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["error"] == "rail_not_permitted_for_jurisdiction"
    assert detail["jurisdiction"] == "VN"
    assert detail["allowed_rails"] == ["vietqr"]


def test_unknown_jurisdiction_fails_closed() -> None:
    """An unresolvable organisation is denied the crypto rail, not granted it."""
    payload = {
        "tier": "BASIC",
        "rail": "nowpayments",
        "email": "unknown@example.com",
        "org_id": "mystery-org",
        "jurisdiction": "",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["error"] == "rail_not_permitted_for_jurisdiction"
    assert detail["allowed_rails"] == ["vietqr"]


def test_non_vn_org_must_declare_jurisdiction_to_keep_crypto_rail() -> None:
    """Overseas customers keep the crypto rail, but only by declaring it.

    An org label is not proof of nationality, so ``SG-overseas`` alone is not
    enough — the request has to state its jurisdiction. Denying an overseas
    buyer who declares a non-VN jurisdiction would break their legitimate
    purchase, so the gate stays open for them.
    """
    payload = {
        "tier": "BASIC",
        "rail": "nowpayments",
        "email": "ops@example.sg",
        "org_id": "SG-overseas",
        "jurisdiction": "SG",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 200
    assert res.json()["rail"] == "nowpayments"


def test_org_prefix_alone_is_not_proof_of_jurisdiction() -> None:
    """An undeclared ``SG-`` label fails closed rather than granting the rail.

    The prefix is a naming convenience, not a nationality declaration. Reading
    it as one would let any customer unlock the crypto rail by naming their org
    ``SG-anything``, which defeats the gate entirely.
    """
    payload = {
        "tier": "BASIC",
        "rail": "nowpayments",
        "email": "ops@example.sg",
        "org_id": "SG-overseas",
    }
    res = client.post("/v1/checkout", json=payload)
    assert res.status_code == 403
    assert res.json()["detail"]["allowed_rails"] == ["vietqr"]


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
    from src.raas.credits import CreditStore
    from src.raas.tenant import TenantStore

    # Get a real signed key
    res_paid = client.get("/v1/checkout/status?order_id=ord-paid-999&simulate_paid=true")
    key = res_paid.json()["license_key"]
    tenant_name = res_paid.json()["tenant_id"]

    # Activate first time
    act_res = client.post("/v1/license/activate", json={"license_key": key})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["valid"] is True
    assert act_data["tier"] == "PREMIUM"

    tenant = TenantStore().find_by_email(tenant_name)
    assert tenant is not None
    bal_first = CreditStore().get_balance(tenant.id)

    # Activate second time with the exact same license key — must be idempotent (no credit inflation)
    act_res_2 = client.post("/v1/license/activate", json={"license_key": key})
    assert act_res_2.status_code == 200
    bal_second = CreditStore().get_balance(tenant.id)
    assert bal_second == bal_first

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
    assert detail["allowed_rails"] == ["vietqr"]


def test_nowpayments_create_payment_rejects_vn_and_undeclared_jurisdiction() -> None:
    import pytest

    from src.raas.nowpayments_checkout import create_payment

    with pytest.raises(ValueError, match="not permitted for jurisdiction 'VN'"):
        create_payment("pro", "ORD-VN-1")
    with pytest.raises(ValueError, match="not permitted for jurisdiction 'VN'"):
        create_payment("pro", "ORD-VN-2", jurisdiction="VN")

