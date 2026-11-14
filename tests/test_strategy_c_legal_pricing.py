"""Strategy C Legal & Pricing Suite: Polar Decommission on /v1/pricing/vn,
Section 10.3 VN SME Outcome-Priced Tiers, and Decree 52/2024 Fourth-Door IPN Guard.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.api.vn_pricing_routes import router as vn_pricing_router
from src.opc.quota import VN_SME_TIER_WORKFLOW_QUOTAS, WorkflowQuotaGuard
from src.raas import nowpayments_webhook_handler as handler_mod
from src.raas.checkout_router import (
    COMMERCIAL_TIERS,
    VN_SME_COMMITMENT_PRICING,
    VN_SME_WORKFLOW_TIERS,
    router as checkout_router,
)
from src.raas.credit_account_repository import CreditAccountRepository
from src.raas.nowpayments_router import router as nowpayments_router
from src.raas.revenue_router import router as revenue_router
from src.raas.tenant import TenantStore

REPO_ROOT = Path(__file__).resolve().parent.parent


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(vn_pricing_router)
    app.include_router(checkout_router)
    app.include_router(revenue_router)
    app.include_router(nowpayments_router)
    return TestClient(app)


def test_vn_pricing_route_has_zero_polar_and_exposes_section_10_3_tiers() -> None:
    """GET /v1/pricing/vn strips all Polar/USD billing references and exposes Section 10.3 SME tiers."""
    client = _build_client()
    res = client.get("/v1/pricing/vn")
    assert res.status_code == 200
    raw_text = json.dumps(res.json(), ensure_ascii=False).lower()
    assert "polar" not in raw_text
    assert "usd" not in raw_text

    body = res.json()
    assert body["currency_display"] == "VND"
    assert body["currency_billing"] == "VND"
    assert body["allowed_rails"] == ["vietqr"]
    assert {"starter_vn", "growth_vn", "pro_vn"}.issubset(body["tiers"].keys())
    assert len(body["services"]) >= 5

    sme = {item["tier"]: item for item in body["vn_sme_workflow_tiers"]}
    assert set(sme.keys()) == {"starter", "pilot_a", "growth", "agency"}
    assert sme["starter"]["price_vnd"] == 790_000 and sme["starter"]["commitment_6m_vnd"] == 690_000
    assert sme["starter"]["verified_workflows_per_month"] == 300 and sme["starter"]["rails"] == ["vietqr"]
    assert sme["pilot_a"]["price_vnd"] == 990_000 and sme["pilot_a"]["verified_workflows_per_month"] == 500
    assert sme["growth"]["price_vnd"] == 1_990_000 and sme["growth"]["commitment_6m_vnd"] == 1_690_000
    assert sme["growth"]["verified_workflows_per_month"] == 1_000 and sme["growth"]["rails"] == ["vietqr"]
    assert sme["agency"]["price_vnd"] == 4_900_000 and sme["agency"]["setup_fee_vnd"] == 5_000_000
    assert sme["agency"]["verified_workflows_per_month"] == 3_500 and sme["agency"]["rails"] == ["vietqr"]

    for sub_route in ("/v1/pricing/vn/services", "/v1/pricing/vn/tier/starter_vn", "/v1/pricing/vn/tier/growth", "/v1/pricing/paid"):
        sub_res = client.get(sub_route)
        assert sub_res.status_code == 200
        assert "polar" not in json.dumps(sub_res.json(), ensure_ascii=False).lower()


def test_section_10_3_quotas_and_commercial_tier_preservation(tmp_path: Path) -> None:
    """VN_SME_WORKFLOW_TIERS, VN_SME_TIER_WORKFLOW_QUOTAS, and /v1/pricing align without altering COMMERCIAL_TIERS."""
    assert COMMERCIAL_TIERS == {
        "basic": {"usd": 199, "vnd": 4_975_000, "mcu": 1_500},
        "premium": {"usd": 399, "vnd": 9_975_000, "mcu": 4_000},
        "enterprise": {"usd": 799, "vnd": 19_975_000, "mcu": 10_000},
        "master": {"usd": 4999, "vnd": 124_975_000, "mcu": 100_000},
    }
    assert VN_SME_TIER_WORKFLOW_QUOTAS == {"starter": 300, "pilot_a": 500, "growth": 1_000, "agency": 3_500}
    assert VN_SME_WORKFLOW_TIERS["growth"]["workflows"] == 1_000
    assert VN_SME_WORKFLOW_TIERS["agency"]["workflows"] == 3_500
    assert VN_SME_COMMITMENT_PRICING["starter"]["commitment_6m_vnd"] == 690_000
    assert VN_SME_COMMITMENT_PRICING["growth"]["commitment_6m_vnd"] == 1_690_000
    assert VN_SME_COMMITMENT_PRICING["agency"]["setup_fee_vnd"] == 5_000_000

    guard = WorkflowQuotaGuard(tmp_path / "quota_s103.db")
    assert guard.reserve_workflow_slot("t_growth", "wf_1", "2026-11", 1_760_000_000, tier="growth").limit_count == 1_000
    assert guard.reserve_workflow_slot("t_agency", "wf_1", "2026-11", 1_760_000_000, tier="agency").limit_count == 3_500

    pricing = _build_client().get("/v1/pricing").json()
    by_tier = {item["tier"]: item for item in pricing["vn_sme_workflow_tiers"]}
    assert by_tier["starter"]["commitment_6m_vnd"] == 690_000
    assert by_tier["growth"]["commitment_6m_vnd"] == 1_690_000
    assert by_tier["agency"]["setup_fee_vnd"] == 5_000_000


def test_decree_52_2024_fourth_door_blocks_vn_nowpayments_ipn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /webhooks/nowpayments returns HTTP 403 and grants 0 credits on all VN jurisdiction signals."""
    tenants_db = tmp_path / "tenants.db"
    monkeypatch.setenv("MEKONG_RAAS_DB", str(tenants_db))
    t_store = TenantStore(tenants_db)
    vn_tenant = t_store.create_tenant("doanhnghiep_vn")
    vn_hyph = t_store.create_tenant("shop-hanoi")
    sg_tenant = t_store.create_tenant("overseas_sg")
    with closing(t_store._connect()) as conn:
        conn.execute("UPDATE tenants SET jurisdiction = 'SG' WHERE id = ?", (sg_tenant.id,))
        conn.commit()

    repo = CreditAccountRepository(tmp_path / "credits.db")
    for ws in ("ws_explicit", "VN", "vn_shop", vn_tenant.id, "doanhnghiep_vn", "shop", "shop-hanoi", "mk", "ws_vnd", "ws_pilot", "overseas_sg"):
        repo.create_account(ws)

    client = _build_client()
    blocked_payloads = [
        {"payment_id": "p_vn_jur", "payment_status": "finished", "order_id": "ws_explicit-pro-monthly", "jurisdiction": "VN", "price_currency": "usd"},
        {"payment_id": "p_vn_cty", "payment_status": "finished", "order_id": "ws_explicit-pro-monthly", "country": "vn", "price_currency": "usd"},
        {"payment_id": "p_vn_pfx1", "payment_status": "finished", "order_id": "VN-acme-pro", "price_currency": "usd"},
        {"payment_id": "p_vn_pfx2", "payment_status": "finished", "order_id": "vn_shop-starter-monthly", "price_currency": "usd"},
        {"payment_id": "p_vn_tid", "payment_status": "finished", "order_id": f"{vn_tenant.id}-pro-monthly", "price_currency": "usd"},
        {"payment_id": "p_vn_tnm", "payment_status": "finished", "order_id": "doanhnghiep_vn-pro-monthly", "price_currency": "usd"},
        {"payment_id": "p_vn_hyp", "payment_status": "finished", "order_id": f"{vn_hyph.name}-pro-monthly", "price_currency": "usd"},
        {"payment_id": "p_mk_unattr", "payment_status": "finished", "order_id": "mk-a1b2c3d4e5f6", "price_currency": "usd"},
        {"payment_id": "p_mk_spoof_cty", "payment_status": "finished", "order_id": "mk-a1b2c3d4e5f6", "country": "US", "jurisdiction": "SG", "price_currency": "usd"},
        {"payment_id": "p_vnd_cur", "payment_status": "finished", "order_id": "ws_vnd-pro-monthly", "price_currency": "vnd"},
        {"payment_id": "p_pilot_a", "payment_status": "finished", "order_id": "ws_pilot-pilot_a-monthly", "price_currency": "usd"},
    ]

    with patch.object(handler_mod, "CreditAccountRepository", return_value=repo), patch.object(handler_mod, "_log_payment"):
        for item in blocked_payloads:
            resp = client.post("/webhooks/nowpayments", content=json.dumps(item))
            assert resp.status_code == 403, f"Expected 403 for {item['payment_id']}, got {resp.status_code}"
            assert resp.json() == {
                "status": "error",
                "detail": "rail_not_permitted_for_jurisdiction",
                "jurisdiction": "VN",
                "allowed_rails": ["vietqr"],
            }

        for ws in ("ws_explicit", "VN", "vn_shop", vn_tenant.id, "doanhnghiep_vn", "shop", "shop-hanoi", "mk", "ws_vnd", "ws_pilot"):
            assert repo.get_balance(ws) == 0

        # Registered SG tenant + mk-* order attributed to registered SG tenant grant credits to overseas_sg (never "mk")
        sg_resp = client.post(
            "/webhooks/nowpayments",
            content=json.dumps({"payment_id": "p_sg_ok", "payment_status": "finished", "order_id": "mk-a1b2c3d4e5f6", "tenant_id": "overseas_sg", "price_currency": "usd"}),
        )
        assert sg_resp.status_code == 200 and sg_resp.json() == {"status": "ok", "action": "credits_granted"}
        assert repo.get_balance("overseas_sg") > 0 and repo.get_balance("mk") == 0


def test_quota_and_legal_pricing_loc_ceilings() -> None:
    """Enforce <= 185 LOC ceiling on quota and Strategy C/E test suites."""
    for rel in (
        "src/opc/quota.py",
        "tests/test_strategy_e_billing_reconcile.py",
        "tests/test_strategy_c_legal_pricing.py",
    ):
        loc = len((REPO_ROOT / rel).read_text(encoding="utf-8").splitlines())
        assert loc <= 185, f"{rel} exceeds 185 LOC ceiling ({loc} LOC)"
