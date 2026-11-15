"""Supreme Command #08 — Phase 2 (P0 Payment Integrity) Adversarial Test Matrix.

Covers:
1. Unknown/unregistered order_id (bank tx memo, simulate_paid=true, mk-paid-* prefix) -> 0 licenses, 401/None.
2. Unauthenticated GET /v1/checkout/status (missing/wrong secret, wrong tenant API key) -> 401, 0 leaks; owning tenant API key -> 200.
3. Partial 6-character order_id[-6:] tail collision -> rejected, 0 cross-order settlement.
4. Ambiguous memo containing two order IDs & wrong org tag -> rejected, 0 licenses.
5. Underpayment (expected - 1 VND, and 990,000 VND against enterprise 19,975,000 VND) -> pending, no tier inference or PREMIUM fallback.
6. Single bank_tx_id replay across two orders / two tenants -> at most 1 order settles, 0 duplicate funding.
7. Multi-worker / process restart simulation (>25 newer bank txs, starter / pilot_a / enterprise) -> exact tier/org preserved, identical license key.
8. High-concurrency race (ThreadPoolExecutor max_workers=8) on status + license activation -> 1 settlement, identical token, 1x credit grant.
9. MEKONG_ENV=production rejects simulate_paid=true (HTTP 403) even when PYTEST_CURRENT_TEST is set.
10. NOWPayments mk-* hosted invoice with customer_email only -> credits sg_tenant.id ("mk" == 0), replay idempotent, underpaid/missing payment_id rejected.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import hmac
import json
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.core.raas_license_verifier import sign_license_key, verify_license_key
from src.core.vietqr_engine import VietQrEngine
from src.raas import nowpayments_webhook_handler as handler_mod
from src.raas.checkout_router import router as checkout_router
from src.raas.credit_account_repository import CreditAccountRepository
from src.raas.credits import CreditStore
from src.raas.nowpayments_router import router as nowpayments_router
from src.raas.revenue_router import router as revenue_router
from src.raas.tenant import TenantStore


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(checkout_router)
    app.include_router(revenue_router)
    app.include_router(nowpayments_router)
    return TestClient(app)


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    vietqr_db = tmp_path / "vietqr.db"
    raas_db = tmp_path / "raas_tenants.db"
    credits_db = tmp_path / "workspaces_credits.db"
    monkeypatch.setenv("MEKONG_VIETQR_DB", str(vietqr_db))
    monkeypatch.setenv("MEKONG_RAAS_DB", str(raas_db))
    monkeypatch.setenv("MEKONG_ENV", "test")
    return {"vietqr_db": vietqr_db, "raas_db": raas_db, "credits_db": credits_db}


def test_1_unknown_order_never_mints_license(isolated_env: dict[str, Path]) -> None:
    """Unknown/unregistered order_id never settles or leaks a license, even with matching bank tx or simulate_paid."""
    client = _make_client()
    engine = VietQrEngine(db_path=isolated_env["vietqr_db"])

    ghost_order = "mk-deadbeefcafe1234"
    engine.record_transaction(
        bank_tx_id="TX-GHOST-1",
        amount_vnd=9_975_000,
        memo=f"MEKONG org-ghost {ghost_order}",
        matched_order_id=ghost_order,
    )

    for candidate in (ghost_order, "mk-paid-bypass999", "ord-unknown-001"):
        r1 = client.get(f"/v1/checkout/status?order_id={candidate}")
        assert r1.status_code == 401
        assert "license_key" not in r1.json()

        r2 = client.get(
            f"/v1/checkout/status?order_id={candidate}&simulate_paid=true",
            headers={"X-Checkout-Secret": "chk_forged_secret_value"},
        )
        assert r2.status_code == 401
        assert "license_key" not in r2.json()

        settled = engine.settle_checkout_order_atomic(
            order_id=candidate,
            license_signer=lambda org, tier: sign_license_key(tenant_id=org, tier=tier),
            allow_test_simulation=True,
        )
        assert settled is None


def test_2_checkout_status_caller_authorization_matrix(isolated_env: dict[str, Path]) -> None:
    """Paid order returns 401 on missing/wrong secret or wrong tenant API key; succeeds for secret or owning API key."""
    client = _make_client()
    t_store = TenantStore(isolated_env["raas_db"])
    owner_tenant = t_store.create_tenant("owner_sme_vn")
    attacker_tenant = t_store.create_tenant("attacker_sme_vn")

    co = client.post(
        "/v1/checkout",
        json={"tier": "pilot_a", "rail": "vietqr", "email": "owner@sme.vn", "org_id": owner_tenant.id},
    ).json()
    order_id = co["order_id"]
    secret = co["checkout_secret"]

    VietQrEngine().record_transaction(
        bank_tx_id="TX-AUTH-01",
        amount_vnd=990_000,
        memo=f"MEKONG {owner_tenant.id} {order_id}",
    )

    # Missing credentials -> 401
    r_none = client.get(f"/v1/checkout/status?order_id={order_id}")
    assert r_none.status_code == 401
    assert "MEKONG-RAAS-v1" not in r_none.text

    # Wrong X-Checkout-Secret -> 401
    r_bad_sec = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"X-Checkout-Secret": "chk_wrong_secret_token"},
    )
    assert r_bad_sec.status_code == 401
    assert "MEKONG-RAAS-v1" not in r_bad_sec.text

    # Wrong tenant's valid API key -> 401
    r_wrong_tenant = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"X-API-Key": attacker_tenant.api_key},
    )
    assert r_wrong_tenant.status_code == 401
    assert "MEKONG-RAAS-v1" not in r_wrong_tenant.text

    r_wrong_bearer = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"Authorization": f"Bearer {attacker_tenant.api_key}"},
    )
    assert r_wrong_bearer.status_code == 401

    # Valid X-Checkout-Secret -> 200
    r_sec_ok = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"X-Checkout-Secret": secret},
    )
    assert r_sec_ok.status_code == 200
    body_sec = r_sec_ok.json()
    assert body_sec["status"] == "paid"
    assert body_sec["license_key"] is not None
    assert body_sec["tenant_id"] == owner_tenant.id

    # Valid owning tenant X-API-Key and Bearer token -> 200 with identical license_key
    r_key_ok = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"X-API-Key": owner_tenant.api_key},
    )
    assert r_key_ok.status_code == 200
    assert r_key_ok.json()["license_key"] == body_sec["license_key"]

    r_bearer_ok = client.get(
        f"/v1/checkout/status?order_id={order_id}",
        headers={"Authorization": f"Bearer {owner_tenant.api_key}"},
    )
    assert r_bearer_ok.status_code == 200
    assert r_bearer_ok.json()["license_key"] == body_sec["license_key"]


def test_3_six_char_suffix_collision_rejected(isolated_env: dict[str, Path]) -> None:
    """Two orders sharing the same 6-char suffix cannot cross-settle or match a 6-char memo tail."""
    engine = VietQrEngine(db_path=isolated_env["vietqr_db"])
    sec_a, sec_b = "sec_alpha", "sec_beta"
    order_a = "mk-1111111111abcdef"
    order_b = "mk-2222222222abcdef"

    engine.create_checkout_order(
        order_id=order_a,
        org_id="org-alpha",
        expected_amount_vnd=990_000,
        display_tier="pilot_a",
        canonical_tier="BASIC",
        workflow_quota=500,
        checkout_secret_sha256=hashlib.sha256(sec_a.encode()).hexdigest(),
    )
    engine.create_checkout_order(
        order_id=order_b,
        org_id="org-beta",
        expected_amount_vnd=19_975_000,
        display_tier="ENTERPRISE",
        canonical_tier="ENTERPRISE",
        workflow_quota=None,
        checkout_secret_sha256=hashlib.sha256(sec_b.encode()).hexdigest(),
    )

    # Transfer with only 6-char suffix in memo -> settles NEITHER order
    engine.record_transaction(
        bank_tx_id="TX-TAIL-ONLY",
        amount_vnd=25_000_000,
        memo="MEKONG org-beta abcdef",
    )
    client = _make_client()
    st_a1 = client.get(f"/v1/checkout/status?order_id={order_a}", headers={"X-Checkout-Secret": sec_a}).json()
    st_b1 = client.get(f"/v1/checkout/status?order_id={order_b}", headers={"X-Checkout-Secret": sec_b}).json()
    assert st_a1["status"] == "pending" and st_a1["license_key"] is None
    assert st_b1["status"] == "pending" and st_b1["license_key"] is None

    # Transfer paying order_a exact memo -> settles order_a ONLY; order_b (sharing tail 'abcdef') stays pending
    engine.record_transaction(
        bank_tx_id="TX-EXACT-A",
        amount_vnd=25_000_000,
        memo=f"MEKONG org-alpha {order_a}",
    )
    st_b2 = client.get(f"/v1/checkout/status?order_id={order_b}", headers={"X-Checkout-Secret": sec_b}).json()
    assert st_b2["status"] == "pending" and st_b2["license_key"] is None

    st_a2 = client.get(f"/v1/checkout/status?order_id={order_a}", headers={"X-Checkout-Secret": sec_a}).json()
    assert st_a2["status"] == "paid" and st_a2["tier"] == "pilot_a"


def test_4_ambiguous_multi_order_memo_and_wrong_org_tag_rejected(isolated_env: dict[str, Path]) -> None:
    """Memos mentioning two order IDs or a mismatched tenant org tag settle 0 orders."""
    client = _make_client()
    co_a = client.post(
        "/v1/checkout",
        json={"tier": "starter", "rail": "vietqr", "email": "a@sme.vn", "org_id": "tenant-a"},
    ).json()
    co_b = client.post(
        "/v1/checkout",
        json={"tier": "starter", "rail": "vietqr", "email": "b@sme.vn", "org_id": "tenant-b"},
    ).json()

    engine = VietQrEngine()
    # Ambiguous memo containing both order IDs
    engine.record_transaction(
        bank_tx_id="TX-AMBIG-01",
        amount_vnd=2_000_000,
        memo=f"MEKONG tenant-a {co_a['order_id']} {co_b['order_id']}",
    )
    # Wrong org tag in MEKONG <org> <order_id> and ORG:<org>
    engine.record_transaction(
        bank_tx_id="TX-WRONG-ORG-1",
        amount_vnd=2_000_000,
        memo=f"MEKONG tenant-b {co_a['order_id']}",
    )
    engine.record_transaction(
        bank_tx_id="TX-WRONG-ORG-2",
        amount_vnd=2_000_000,
        memo=f"ORG:tenant-a {co_b['order_id']}",
    )

    st_a = client.get(
        f"/v1/checkout/status?order_id={co_a['order_id']}",
        headers={"X-Checkout-Secret": co_a["checkout_secret"]},
    ).json()
    st_b = client.get(
        f"/v1/checkout/status?order_id={co_b['order_id']}",
        headers={"X-Checkout-Secret": co_b["checkout_secret"]},
    ).json()
    assert st_a["status"] == "pending" and st_a["license_key"] is None
    assert st_b["status"] == "pending" and st_b["license_key"] is None


def test_5_underpayment_stays_pending_without_tier_inference_or_premium_fallback(
    isolated_env: dict[str, Path],
) -> None:
    """Underpaying by 1 VND or paying an SME tier amount against ENTERPRISE stays pending with None license."""
    client = _make_client()
    co_starter = client.post(
        "/v1/checkout",
        json={"tier": "starter", "rail": "vietqr", "email": "s@sme.vn", "org_id": "org-starter"},
    ).json()
    co_ent = client.post(
        "/v1/checkout",
        json={"tier": "ENTERPRISE", "rail": "vietqr", "email": "e@corp.vn", "org_id": "org-ent"},
    ).json()

    engine = VietQrEngine()
    # 789,999 VND against starter (expected 790,000 VND)
    engine.record_transaction(
        bank_tx_id="TX-UNDER-STARTER",
        amount_vnd=789_999,
        memo=f"MEKONG org-starter {co_starter['order_id']}",
        matched_order_id=co_starter["order_id"],
    )
    # 990,000 VND (pilot_a price) against enterprise (expected 19,975,000 VND)
    engine.record_transaction(
        bank_tx_id="TX-UNDER-ENT",
        amount_vnd=990_000,
        memo=f"MEKONG org-ent {co_ent['order_id']}",
        matched_order_id=co_ent["order_id"],
    )

    st_s = client.get(
        f"/v1/checkout/status?order_id={co_starter['order_id']}",
        headers={"X-Checkout-Secret": co_starter["checkout_secret"]},
    ).json()
    assert st_s["status"] == "pending"
    assert st_s["tier"] == "starter"
    assert st_s["license_key"] is None

    st_e = client.get(
        f"/v1/checkout/status?order_id={co_ent['order_id']}",
        headers={"X-Checkout-Secret": co_ent["checkout_secret"]},
    ).json()
    assert st_e["status"] == "pending"
    assert st_e["tier"] == "ENTERPRISE"
    assert st_e["license_key"] is None


def test_6_single_bank_tx_id_cannot_fund_two_orders_or_tenants(
    isolated_env: dict[str, Path],
) -> None:
    """A single bank_tx_id settles at most one order and rejects duplicate replay for another order/tenant."""
    client = _make_client()
    co_1 = client.post(
        "/v1/checkout",
        json={"tier": "pilot_a", "rail": "vietqr", "email": "t1@sme.vn", "org_id": "tenant-one"},
    ).json()
    co_2 = client.post(
        "/v1/checkout",
        json={"tier": "pilot_a", "rail": "vietqr", "email": "t2@sme.vn", "org_id": "tenant-two"},
    ).json()

    engine = VietQrEngine()
    rec1 = engine.record_transaction(
        bank_tx_id="NAPAS-UNIQUE-777",
        amount_vnd=990_000,
        memo=f"MEKONG tenant-one {co_1['order_id']}",
    )
    assert rec1["is_duplicate"] is False

    # Replay same bank_tx_id attempting to bind to co_2
    rec2 = engine.record_transaction(
        bank_tx_id="NAPAS-UNIQUE-777",
        amount_vnd=990_000,
        memo=f"MEKONG tenant-two {co_2['order_id']}",
        matched_order_id=co_2["order_id"],
    )
    assert rec2["is_duplicate"] is True

    st_1 = client.get(
        f"/v1/checkout/status?order_id={co_1['order_id']}",
        headers={"X-Checkout-Secret": co_1["checkout_secret"]},
    ).json()
    st_2 = client.get(
        f"/v1/checkout/status?order_id={co_2['order_id']}",
        headers={"X-Checkout-Secret": co_2["checkout_secret"]},
    ).json()
    assert st_1["status"] == "paid" and st_1["tenant_id"] == "tenant-one"
    assert st_2["status"] == "pending" and st_2["license_key"] is None


def test_7_multi_worker_restart_durability_and_over_20_tx_window(
    isolated_env: dict[str, Path],
) -> None:
    """Orders survive fresh worker instances and >25 newer bank txs; default org_id hashes email cleanly."""
    # Worker 1: create starter (default org), pilot_a (second default org), enterprise (explicit org)
    client_w1 = _make_client()
    co_s = client_w1.post(
        "/v1/checkout",
        json={"tier": "starter", "rail": "vietqr", "email": "alice@shop.vn"},
    ).json()
    co_p = client_w1.post(
        "/v1/checkout",
        json={"tier": "pilot_a", "rail": "vietqr", "email": "bob@shop.vn"},
    ).json()
    co_e = client_w1.post(
        "/v1/checkout",
        json={"tier": "ENTERPRISE", "rail": "vietqr", "email": "cto@corp.vn", "org_id": "corp-vn-hq"},
    ).json()

    del client_w1

    # Worker 2: fresh VietQrEngine instance records payments, followed by 30 unrelated transactions
    engine_w2 = VietQrEngine(db_path=isolated_env["vietqr_db"])
    ord_s = engine_w2.get_checkout_order(co_s["order_id"])
    ord_p = engine_w2.get_checkout_order(co_p["order_id"])
    assert ord_s is not None and ord_p is not None
    assert ord_s["org_id"].startswith("org-") and ord_p["org_id"].startswith("org-")
    assert ord_s["org_id"] != ord_p["org_id"]  # Never collide on shared "default"

    engine_w2.record_transaction("TX-W2-S", 790_000, f"MEKONG {ord_s['org_id']} {co_s['order_id']}")
    engine_w2.record_transaction("TX-W2-P", 990_000, f"MEKONG {ord_p['org_id']} {co_p['order_id']}")
    engine_w2.record_transaction("TX-W2-E", 19_975_000, f"MEKONG corp-vn-hq {co_e['order_id']}")
    for idx in range(30):
        engine_w2.record_transaction(f"TX-NOISE-{idx:02d}", 50_000, f"NOISE TRANSFER {idx}")
    del engine_w2

    # Worker 3: fresh FastAPI TestClient polls all 3 orders twice
    client_w3 = _make_client()
    st_s1 = client_w3.get(
        f"/v1/checkout/status?order_id={co_s['order_id']}",
        headers={"X-Checkout-Secret": co_s["checkout_secret"]},
    ).json()
    st_p1 = client_w3.get(
        f"/v1/checkout/status?order_id={co_p['order_id']}",
        headers={"X-Checkout-Secret": co_p["checkout_secret"]},
    ).json()
    st_e1 = client_w3.get(
        f"/v1/checkout/status?order_id={co_e['order_id']}",
        headers={"X-Checkout-Secret": co_e["checkout_secret"]},
    ).json()
    st_e2 = client_w3.get(
        f"/v1/checkout/status?order_id={co_e['order_id']}",
        headers={"X-Checkout-Secret": co_e["checkout_secret"]},
    ).json()

    assert st_s1["status"] == "paid" and st_s1["tier"] == "starter" and st_s1["workflow_quota"] == 300
    assert st_p1["status"] == "paid" and st_p1["tier"] == "pilot_a" and st_p1["workflow_quota"] == 500
    assert st_e1["status"] == "paid" and st_e1["tier"] == "ENTERPRISE" and st_e1["tenant_id"] == "corp-vn-hq"
    assert st_e1["license_key"] == st_e2["license_key"]

    ver_e = verify_license_key(st_e1["license_key"])
    assert ver_e.valid is True and ver_e.tier.value == "ENTERPRISE" and ver_e.tenant_id == "corp-vn-hq"


def test_8_high_concurrency_status_and_license_activation_race(
    isolated_env: dict[str, Path],
) -> None:
    """8 concurrent pollers + 8 concurrent activations yield 1 settlement, 1 license token, and 1x credits."""
    client = _make_client()
    co = client.post(
        "/v1/checkout",
        json={"tier": "ENTERPRISE", "rail": "vietqr", "email": "race@corp.vn", "org_id": "race-tenant-hq"},
    ).json()
    VietQrEngine().record_transaction(
        bank_tx_id="TX-RACE-888",
        amount_vnd=19_975_000,
        memo=f"MEKONG race-tenant-hq {co['order_id']}",
    )

    def _poll(_i: int) -> dict:
        r = client.get(
            f"/v1/checkout/status?order_id={co['order_id']}",
            headers={"X-Checkout-Secret": co["checkout_secret"]},
        )
        assert r.status_code == 200
        return r.json()

    with ThreadPoolExecutor(max_workers=8) as pool:
        poll_results = list(pool.map(_poll, range(16)))

    keys = {item["license_key"] for item in poll_results}
    assert len(keys) == 1
    license_key = next(iter(keys))
    assert license_key is not None

    def _activate(_i: int) -> dict:
        r = client.post("/v1/license/activate", json={"license_key": license_key})
        assert r.status_code == 200
        return r.json()

    with ThreadPoolExecutor(max_workers=8) as pool:
        act_results = list(pool.map(_activate, range(16)))

    assert all(item["valid"] is True and item["tenant_id"] == "race-tenant-hq" for item in act_results)
    store = CreditStore(isolated_env["raas_db"])
    assert store.get_balance("race-tenant-hq") == 10_000


def test_9_production_env_rejects_simulate_paid_even_under_pytest(
    isolated_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """MEKONG_ENV=production returns HTTP 403 on simulate_paid=true even when PYTEST_CURRENT_TEST is set."""
    monkeypatch.setenv("RAAS_LICENSE_SECRET", "prod-test-hmac-secret-sc08-2026")
    client = _make_client()
    co = client.post(
        "/v1/checkout",
        json={"tier": "PREMIUM", "rail": "vietqr", "email": "prod@mekong.vn", "org_id": "prod-org"},
    ).json()

    monkeypatch.setenv("MEKONG_ENV", "production")
    assert bool(isolated_env["vietqr_db"])

    r_sim = client.get(
        f"/v1/checkout/status?order_id={co['order_id']}&simulate_paid=true",
        headers={"X-Checkout-Secret": co["checkout_secret"]},
    )
    assert r_sim.status_code == 403
    assert r_sim.json()["detail"]["error"] == "simulation_forbidden_in_production"

    # Normal status check without simulate_paid still works and confirms order remained pending
    r_real = client.get(
        f"/v1/checkout/status?order_id={co['order_id']}",
        headers={"X-Checkout-Secret": co["checkout_secret"]},
    )
    assert r_real.status_code == 200
    assert r_real.json()["status"] == "pending"
    assert r_real.json()["license_key"] is None

    # Direct engine call with allow_test_simulation=True also stays pending in production
    direct = VietQrEngine().settle_checkout_order_atomic(
        order_id=co["order_id"],
        license_signer=lambda org, tier: sign_license_key(tenant_id=org, tier=tier),
        allow_test_simulation=True,
    )
    assert direct is not None and direct["payment_state"] == "pending" and direct["issued_license_key"] is None


def test_10_nowpayments_mk_email_attribution_and_replay_idempotency(
    isolated_env: dict[str, Path],
) -> None:
    """Overseas mk-* IPN with customer_email only credits sg_tenant.id (never 'mk') and blocks replays/underpayments."""
    t_store = TenantStore(isolated_env["raas_db"])
    sg_tenant = t_store.create_tenant("billing@overseas.sg")
    with closing(t_store._connect()) as conn:
        conn.execute("UPDATE tenants SET jurisdiction = 'SG' WHERE id = ?", (sg_tenant.id,))
        conn.commit()

    repo = CreditAccountRepository(isolated_env["credits_db"])
    repo.create_account("mk")
    repo.create_account(sg_tenant.id)

    client = _make_client()
    with patch("src.raas.nowpayments_checkout.create_invoice", return_value={"invoice_url": "https://np.example/inv/1"}):
        co = client.post(
            "/v1/checkout",
            json={
                "tier": "ENTERPRISE",
                "rail": "nowpayments",
                "email": "billing@overseas.sg",
                "org_id": sg_tenant.id,
                "jurisdiction": "SG",
            },
        ).json()

    with patch.object(handler_mod, "CreditAccountRepository", return_value=repo), patch.object(
        handler_mod, "_log_payment"
    ):
        # Missing payment_id -> rejected
        r_missing_pid = client.post(
            "/webhooks/nowpayments",
            content=json.dumps({
                "payment_status": "finished",
                "order_id": co["order_id"],
                "customer_email": "billing@overseas.sg",
                "price_amount": 799,
                "price_currency": "usd",
            }),
        )
        assert r_missing_pid.json() == {"status": "error", "detail": "missing_payment_id"}
        assert repo.get_balance(sg_tenant.id) == 0

        # Underpaid callback ($100 vs expected $799) -> rejected
        r_under = client.post(
            "/webhooks/nowpayments",
            content=json.dumps({
                "payment_id": "np_under_001",
                "payment_status": "finished",
                "order_id": co["order_id"],
                "customer_email": "billing@overseas.sg",
                "price_amount": 100,
                "price_currency": "usd",
            }),
        )
        assert r_under.json() == {"status": "error", "detail": "underpaid_invoice"}
        assert repo.get_balance(sg_tenant.id) == 0

        # Valid hosted invoice IPN with customer_email ONLY (no tenant_id) -> credits sg_tenant.id, NOT "mk"
        ipn_payload = json.dumps({
            "payment_id": "np_live_sg_9001",
            "payment_status": "finished",
            "order_id": co["order_id"],
            "order_description": "OpenClaw Enterprise — 10000 credits/mo",
            "customer_email": "billing@overseas.sg",
            "price_amount": 799,
            "price_currency": "usd",
        })
        r_ok = client.post("/webhooks/nowpayments", content=ipn_payload)
        assert r_ok.status_code == 200
        assert r_ok.json() == {"status": "ok", "action": "credits_granted"}
        assert repo.get_balance(sg_tenant.id) == 10_000
        assert repo.get_balance("mk") == 0

        # Duplicate replay (sequential + concurrent) with same payment_id -> 0 additional credits
        def _replay(_i: int) -> dict:
            return client.post("/webhooks/nowpayments", content=ipn_payload).json()

        with ThreadPoolExecutor(max_workers=6) as pool:
            replays = list(pool.map(_replay, range(6)))

        assert all(item == {"status": "ok", "action": "duplicate_ignored"} for item in replays)
        assert repo.get_balance(sg_tenant.id) == 10_000
        assert repo.get_balance("mk") == 0


def test_nowpayments_ipn_secret_required_master_tier_credits_and_deferred_license_retry(
    isolated_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adversarial #11: Unsigned IPN blocked without MEKONG_ALLOW_UNSIGNED_IPN=1, MASTER grants 100k, and license retry recovers."""
    store = TenantStore(isolated_env["raas_db"])
    sg_tenant = store.create_tenant("master@overseas.sg")
    with closing(store._connect()) as conn:
        conn.execute("UPDATE tenants SET jurisdiction = 'SG' WHERE id = ?", (sg_tenant.id,))
        conn.commit()
    repo = CreditAccountRepository(isolated_env["credits_db"])
    repo.create_account(sg_tenant.id)
    client = _make_client()

    with patch("src.raas.nowpayments_checkout.create_invoice", return_value={"invoice_url": "https://np.example/inv/m1"}):
        co = client.post(
            "/v1/checkout",
            json={
                "tier": "MASTER",
                "rail": "nowpayments",
                "email": "master@overseas.sg",
                "org_id": sg_tenant.id,
                "jurisdiction": "SG",
            },
        ).json()
    order_id = co["order_id"]

    with patch.object(handler_mod, "CreditAccountRepository", return_value=repo), patch.object(
        handler_mod, "_log_payment"
    ):
        # 1. Without NOWPAYMENTS_IPN_SECRET and without MEKONG_ALLOW_UNSIGNED_IPN=1 -> HTTP 503 across all envs
        monkeypatch.setattr(handler_mod, "IPN_SECRET", "")
        monkeypatch.delenv("NOWPAYMENTS_IPN_SECRET", raising=False)
        monkeypatch.delenv("MEKONG_ALLOW_UNSIGNED_IPN", raising=False)
        for env_name in ("staging", "production", "development"):
            monkeypatch.setenv("MEKONG_ENV", env_name)
            r_no_sec = client.post(
                "/webhooks/nowpayments",
                content=json.dumps({"payment_id": "np_unauth_1", "payment_status": "finished", "order_id": order_id}),
            )
            assert r_no_sec.status_code == 503
            assert r_no_sec.json()["detail"] == "ipn_secret_unconfigured"

        # 2. Signed IPN with omitted price_amount or non-USD currency rejected
        ipn_secret = "np_sc08_master_secret_2026"
        monkeypatch.setattr(handler_mod, "IPN_SECRET", ipn_secret)
        monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", ipn_secret)
        monkeypatch.setenv("MEKONG_ENV", "production")
        monkeypatch.delenv("RAAS_LICENSE_SECRET", raising=False)

        def _post_signed(body_dict: dict[str, object]):
            canonical = json.dumps(body_dict, sort_keys=True).encode("utf-8")
            sig = hmac.new(ipn_secret.encode("utf-8"), canonical, hashlib.sha512).hexdigest()
            return client.post("/webhooks/nowpayments", content=canonical, headers={"x-nowpayments-sig": sig})

        r_omit_price = _post_signed({
            "payment_id": "np_m_omit",
            "payment_status": "finished",
            "order_id": order_id,
            "customer_email": "master@overseas.sg",
        })
        assert r_omit_price.json()["detail"] == "missing_price_amount"
        assert repo.get_balance(sg_tenant.id) == 0

        r_bad_ccy = _post_signed({
            "payment_id": "np_m_eur",
            "payment_status": "finished",
            "order_id": order_id,
            "customer_email": "master@overseas.sg",
            "price_amount": 4999,
            "price_currency": "eur",
        })
        assert r_bad_ccy.json()["detail"] == "invalid_price_currency"
        assert repo.get_balance(sg_tenant.id) == 0

        # 3. Valid $4,999 MASTER IPN when order settlement transiently fails on Attempt 1:
        #    Attempt 1 grants 100,000 credits (NOT 1,500 starter fallback!) and returns HTTP 503 so NOWPayments retries license minting.
        valid_master_ipn: dict[str, object] = {
            "payment_id": "np_m_real_001",
            "payment_status": "finished",
            "order_id": order_id,
            "order_description": "OpenClaw Master — 100000 credits/mo",
            "customer_email": "master@overseas.sg",
            "price_amount": 4999,
            "price_currency": "usd",
        }
        with patch.object(handler_mod, "sign_license_key", side_effect=RuntimeError("transient_settlement_error")):
            r_retry_needed = _post_signed(valid_master_ipn)
        assert r_retry_needed.status_code == 503
        assert "transient_settlement_error" in r_retry_needed.json()["detail"]
        assert repo.get_balance(sg_tenant.id) == 100_000

        # 4. NOWPayments retries same payment_id -> 0 extra credits, order settles to paid with MASTER license!
        r_recovered = _post_signed(valid_master_ipn)
        assert r_recovered.status_code == 200
        assert r_recovered.json() == {"status": "ok", "action": "duplicate_ignored"}
        assert repo.get_balance(sg_tenant.id) == 100_000

        st = client.get(
            f"/v1/checkout/status?order_id={order_id}",
            headers={"X-Checkout-Secret": co["checkout_secret"]},
        )
        assert st.status_code == 200
        assert st.json()["status"] == "paid"
        assert st.json()["tier"] == "MASTER"
        verified_lic = verify_license_key(st.json()["license_key"])
        assert verified_lic.valid and verified_lic.tier is not None and verified_lic.tier.value == "MASTER"

