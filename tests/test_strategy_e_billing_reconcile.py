"""Strategy E Verification Suite (Part 2): Signed VietQR Cross-Order Replay Guard,
DRAFT_PENDING_TVAN Export, Parallel VN_SME_WORKFLOW_TIERS, and Atomic SQLite WAL Quota.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.opc.accounting_draft import DRAFT_STATUS_PENDING_TVAN, VietQrWebhookError
from src.opc.models import BusinessProfile
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.usage import UsageLedger
from src.raas.checkout_router import COMMERCIAL_TIERS, VN_SME_WORKFLOW_TIERS, router as checkout_router
from src.raas.revenue_router import router as revenue_router

REPO_ROOT = Path(__file__).resolve().parent.parent


def _profile() -> BusinessProfile:
    return BusinessProfile(
        business_name="CONG TY TNHH MEKONG BILLING", owner_name="Nguyen Thi Mai",
        language="vi", locale="vi_VN", timezone="Asia/Ho_Chi_Minh", currency="VND",
        services={"tu_van_ai": Decimal("600000"), "tich_hop_vietqr": Decimal("400000")},
        payment_terms="Thanh toan 100% qua VietQR Napas 247", jurisdiction="VN",
        preferences={"bank_id": "MB", "account_no": "0988889999"},
    )


def _event(event_id: str) -> ZaloWebhookEvent:
    now_ts = 1_760_000_000
    return ZaloWebhookEvent(
        event_id=event_id, oa_id="oa_growth_01", sender_id="84909123456",
        sender_name="Công ty TNHH Hùng Phát", message_text="Báo giá gói 10 giờ.",
        timestamp=now_ts, last_user_interaction_ts=now_ts - 900,
        requested_services=("tu_van_ai", "tich_hop_vietqr"), estimated_hours=10,
        project_title="Tự Động Hóa Zalo OA & VietQR", currency="VND", language="vi",
    )


def test_vietqr_reconciliation_blocks_cross_order_replay_and_exports_tvan_draft(tmp_path: Path) -> None:
    """Single VietQR transfer cannot reconcile two orders; malformed amounts fail closed; draft is DRAFT_PENDING_TVAN."""
    wf = PilotAWorkflow(db_path=tmp_path / "recon.db", profile=_profile())
    card_a = wf.handle_webhook(_event("evt_recon_a"))
    card_b = wf.handle_webhook(_event("evt_recon_b"))
    secret = "vietqr_napas_webhook_secret_test"

    def _sign(obj: object) -> tuple[bytes, str]:
        raw = json.dumps(obj).encode("utf-8")
        return raw, hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    # Reject bad signature, boolean amount_vnd, null/string amount, multi-run memo, and prefix collision
    for bad_obj in (
        {"bank_tx_id": "TX-BOOL", "amount_vnd": True, "memo": f"OPC {card_a.run_id}"},
        {"bank_tx_id": "TX-NULL", "amount_vnd": None, "memo": f"OPC {card_a.run_id}"},
        {"bank_tx_id": "TX-STR", "amount_vnd": "abc", "memo": f"OPC {card_a.run_id}"},
        {"bank_tx_id": "TX-TWO", "amount_vnd": card_a.total_amount_vnd, "memo": f"OPC {card_a.run_id} {card_b.run_id}"},
        {"bank_tx_id": "TX-PFX", "amount_vnd": card_a.total_amount_vnd, "memo": f"OPC {card_a.run_id}999"},
    ):
        raw_bad, sig_bad = _sign(bad_obj)
        with pytest.raises(VietQrWebhookError):
            wf.reconcile_payment_and_export_draft(card_a, raw_bad, sig_bad, secret)

    raw_ok, sig_ok = _sign({"bank_tx_id": "NAPAS-TX-01", "amount_vnd": card_a.total_amount_vnd, "memo": f"Thanh toan OPC {card_a.run_id}"})
    with pytest.raises(VietQrWebhookError, match="Invalid VietQR webhook"):
        wf.reconcile_payment_and_export_draft(card_a, raw_ok, "bad_sig", secret)

    recon1, draft = wf.reconcile_payment_and_export_draft(card_a, raw_ok, sig_ok, secret, vat_rate_pct=8)
    assert recon1["reconciled"] is True and recon1["is_duplicate"] is False
    assert draft.invoice_status == DRAFT_STATUS_PENDING_TVAN and draft.invoice_status != "ISSUED"
    assert draft.legal_certified is False and draft.requires_tvan_signature is True
    assert draft.subtotal_vnd == 5_000_000 and draft.vat_amount_vnd == 400_000 and draft.total_amount_vnd == 5_400_000

    # Same order replay -> idempotent duplicate; cross-order replay of same bank_tx_id -> blocked!
    recon2, _ = wf.reconcile_payment_and_export_draft(card_a, raw_ok, sig_ok, secret)
    assert recon2["is_duplicate"] is True
    raw_cross, sig_cross = _sign({"bank_tx_id": "NAPAS-TX-01", "amount_vnd": card_b.total_amount_vnd, "memo": f"Thanh toan OPC {card_b.run_id}"})
    with pytest.raises(VietQrWebhookError, match="Cross-order bank_tx_id replay blocked"):
        wf.reconcile_payment_and_export_draft(card_b, raw_cross, sig_cross, secret)

    # CLI pilot-a + CLI proposal graceful exit code 1 when MEKONG_APPROVAL_SECRET unset outside pytest
    cli_res = CliRunner().invoke(
        build_app(),
        ["opc", "pilot-a", "--db", str(tmp_path / "cli_se.db"), "--tenant-id", "sme_cantho_01", "--require-consent", "--grant-consent", "--export-draft", "--json"],
    )
    assert cli_res.exit_code == 0 and json.loads(cli_res.stdout)["accounting_draft"]["invoice_status"] == "DRAFT_PENDING_TVAN"
    prop_unauth = subprocess.run(
        [sys.executable, "-c", "from typer.testing import CliRunner; from src.cli.app_setup import build_app; r=CliRunner().invoke(build_app(), ['opc','proposal']); raise SystemExit(r.exit_code)"],
        cwd=REPO_ROOT, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO_ROOT)}, capture_output=True, text=True, check=False,
    )
    assert prop_unauth.returncode == 1


def test_parallel_vn_sme_workflow_tiers_status_mapping_and_atomic_quota(tmp_path: Path) -> None:
    """VN_SME_WORKFLOW_TIERS settles on vietqr only, resolves SME tier on status, and guards quota atomically."""
    assert tuple(COMMERCIAL_TIERS.keys()) == ("basic", "premium", "enterprise", "master")
    assert VN_SME_WORKFLOW_TIERS == {
        "starter": {"vnd": 790_000, "usd": 31, "workflows": 300},
        "pilot_a": {"vnd": 990_000, "usd": 39, "workflows": 500},
        "growth": {"vnd": 1_990_000, "usd": 78, "workflows": 1_500},
        "agency": {"vnd": 4_900_000, "usd": 195, "workflows": 5_000},
    }

    api = FastAPI()
    api.include_router(checkout_router)
    api.include_router(revenue_router)
    client = TestClient(api)

    pricing = client.get("/v1/pricing").json()
    sme_by_tier = {item["tier"]: item for item in pricing["vn_sme_workflow_tiers"]}
    assert len(pricing["tiers"]) == 4 and sme_by_tier["pilot_a"]["price_vnd"] == 990_000 and sme_by_tier["pilot_a"]["rails"] == ["vietqr"]

    co_ok = client.post("/v1/checkout", json={"tier": "pilot_a", "rail": "vietqr", "email": "chu_shop@mekong.vn"}).json()
    assert co_ok["tier"] == "pilot_a" and co_ok["amount_vnd"] == 990_000 and co_ok["workflow_quota"] == 500

    # Record paid 990k VietQR transaction and verify /v1/checkout/status resolves pilot_a (500 workflows, NOT PREMIUM)
    from src.core.vietqr_engine import VietQrEngine
    VietQrEngine().record_transaction(f"TX-{co_ok['order_id']}", 990_000, f"MEKONG {co_ok['order_id'][-6:]}", matched_order_id=co_ok["order_id"])
    st_paid = client.get(f"/v1/checkout/status?order_id={co_ok['order_id']}").json()
    assert st_paid["status"] == "paid" and st_paid["tier"] == "pilot_a" and st_paid["workflow_quota"] == 500

    co_crypto = client.post("/v1/checkout", json={"tier": "pilot_a", "rail": "nowpayments", "email": "chu_shop@mekong.vn", "jurisdiction": "SG"})
    assert co_crypto.status_code == 403

    usage = UsageLedger(tmp_path / "quota_atomic.db")
    with ThreadPoolExecutor(max_workers=6) as pool:
        burst = list(pool.map(lambda i: usage.reserve_workflow_quota("tenant_vn_01", f"wf_{i}", "2026-11", 1_760_000_000, limit_override=3), range(20)))
    assert sum(1 for r in burst if r.allowed) == 3 and sum(1 for r in burst if not r.allowed) == 17
    winner = next(r.workflow_id for r in burst if r.allowed)
    replay = usage.reserve_workflow_quota("tenant_vn_01", winner, "2026-11", 1_760_000_000, limit_override=3)
    assert replay.allowed is True and replay.deduplicated is True and usage.quota_guard.get_period_usage("tenant_vn_01", "2026-11") == 3
