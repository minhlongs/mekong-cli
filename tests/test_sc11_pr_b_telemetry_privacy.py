"""SC11 PR-B regression tests: S11-06 (usage lineage), S11-07 (token/cost honesty), S11-08 (payment telemetry), S11-09 (DSAR accounting retention), S11-10 (VN PDPL 91/2025/QH15 legal accuracy)."""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.gateway import app
from src.opc.models import BusinessProfile
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.privacy_guard import ConsentRequiredError
from src.opc.selective_router import SelectiveRouter
from src.opc.tenant_provisioner import provision_isolated_tenant

_SECRET = "sc11_pr_b_test_approval_secret_32bytes"
_VIETQR_SECRET = "sc11_pr_b_vietqr_webhook_secret_32b"


def _profile() -> BusinessProfile:
    return BusinessProfile(
        business_name="Mekong Agency",
        owner_name="Lan Anh",
        currency="VND",
        language="vi",
        locale="vi-VN",
        timezone="Asia/Ho_Chi_Minh",
        services={"tu_van_ai": Decimal("1000000")},
        payment_terms="Chuyển khoản VietQR",
        preferences={"bank_id": "MB", "account_no": "0988889999"},
    )


def _event(event_id: str, sender_id: str = "84901234567", message_text: str = "Cần báo giá gói tu_van_ai 3 giờ") -> ZaloWebhookEvent:
    now = int(time.time())
    return ZaloWebhookEvent(
        event_id=event_id,
        oa_id="oa_sc11_test",
        sender_id=sender_id,
        sender_name="Minh Khoa",
        message_text=message_text,
        timestamp=now,
        last_user_interaction_ts=now - 30,
        requested_services=("tu_van_ai",),
        estimated_hours=3,
        project_title="Tư vấn AI Pilot",
    )


def test_s11_06_and_s11_07_usage_lineage_and_honest_tokens(tmp_path: Path) -> None:
    """S11-06 & S11-07: Router LLM usage rebinds from rt_<event_id> to run_id; offline_rules logs 0 LLM tokens; unknown LLM cost surfaces UNKNOWN."""
    db_path = tmp_path / "tenant_lineage.db"
    wf = PilotAWorkflow(db_path=db_path, profile=_profile(), approval_secret=_SECRET)

    # Case 1: Local LLM returns provider usage with tokens + explicit cost -> rebound to run_id
    wf.router = SelectiveRouter(
        usage_ledger=wf.usage,
        local_endpoint="http://127.0.0.1:11434/v1/chat/completions",
        local_model="qwen3-8b-local",
        local_transport=lambda *_a: (
            200,
            json.dumps({
                "confidence": 0.93,
                "extracted": {"requested_services": ["tu_van_ai"], "estimated_hours": 3},
                "usage": {"total_tokens": 410, "cost": "1250.00"},
            }).encode("utf-8"),
        ),
    )
    ev1 = _event("evt_s11_06_paid_llm", message_text="Mình muốn hỏi thêm về dịch vụ bên bạn cho dự án mới")
    card1 = wf.handle_webhook(ev1)

    # Zero orphaned rt_<event_id> records remain
    assert wf.usage.get_run_records(f"rt_{ev1.event_id}") == []
    records1 = wf.usage.get_run_records(card1.run_id)
    assert any(r.model == "qwen3-8b-local" and r.tokens == 410 for r in records1)
    offline_recs = [r for r in records1 if r.model == "offline_rules"]
    assert len(offline_recs) == 1 and offline_recs[0].tokens == 0

    agg1 = wf.usage.aggregate_run_costs(card1.run_id)
    assert agg1["total_tokens"] == 410
    assert agg1["known_amounts"]["VND"] == "1250.00"
    assert agg1["has_unknown_costs"] is False

    # Case 2: Local LLM omits cost -> UsageStage.UNKNOWN rebound to run_id, cost_status must NOT fabricate 0.0
    wf.router = SelectiveRouter(
        usage_ledger=wf.usage,
        local_endpoint="http://127.0.0.1:11434/v1/chat/completions",
        local_model="qwen3-8b-local",
        local_transport=lambda *_a: (
            200,
            json.dumps({
                "confidence": 0.91,
                "extracted": {"requested_services": ["tu_van_ai"], "estimated_hours": 3},
                "usage": {"total_tokens": 320},
            }).encode("utf-8"),
        ),
    )
    ev2 = _event("evt_s11_07_unk_cost", message_text="Nhờ tư vấn thêm giải pháp triển khai cho doanh nghiệp")
    card2 = wf.handle_webhook(ev2)

    assert wf.usage.get_run_records(f"rt_{ev2.event_id}") == []
    agg2 = wf.usage.aggregate_run_costs(card2.run_id)
    assert agg2["total_tokens"] == 320
    assert agg2["has_unknown_costs"] is True
    acct2 = wf.usage.summarize_cost_accounting(card2.run_id)
    assert acct2.actual_cost is None
    assert acct2.cost_status == "UNKNOWN"


def test_s11_08_workflow_payment_telemetry_on_runs_and_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """S11-08: opc_runs and GET /runs/{run_id} track unpaid -> settled payment_state, bank_tx_id, paid_amount_vnd, paid_at."""
    tenants_dir = tmp_path / "tenants"
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(tenants_dir))
    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", _SECRET)
    monkeypatch.setenv("VIETQR_WEBHOOK_SECRET", _VIETQR_SECRET)
    prov = provision_isolated_tenant(tenants_dir, "tenant_s11_08", "Mekong Agency", "Lan Anh", sme_tier="pilot_a")

    client = TestClient(app)
    hdr = {"X-API-Key": prov.tenant_api_key}
    now = int(time.time())
    resp = client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={
            "event_id": "evt_s11_08_pay",
            "sender_id": "84905551234",
            "sender_name": "Hữu Nghĩa",
            "message_text": "Báo giá gói tu_van_ai 2 giờ",
            "timestamp": now,
            "last_user_interaction_ts": now - 10,
            "requested_services": ["tu_van_ai"],
            "estimated_hours": 2,
            "project_title": "Audit AI",
            "tenant_id": "tenant_s11_08",
            "extraction_confidence": 0.96,
        },
        headers=hdr,
    )
    assert resp.status_code == 200
    body = resp.json()
    run_id = body["run_id"]
    amount_vnd = int(body["total_amount_vnd"])

    # Before payment: unpaid
    pre = client.get(f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_s11_08", headers=hdr)
    assert pre.status_code == 200
    pre_data = pre.json()
    assert pre_data["payment_state"] == "unpaid"
    assert pre_data["paid_amount_vnd"] == 0
    assert pre_data["bank_tx_id"] == ""
    assert pre_data["paid_at"] is None
    assert "cost_accounting" in pre_data

    # Settle via signed VietQR webhook
    raw_wh = json.dumps({
        "bank_tx_id": "FT261119S1108",
        "amount_vnd": amount_vnd,
        "memo": f"OPC {run_id}",
        "bank_id": "MB",
    }).encode("utf-8")
    sig = hmac.new(_VIETQR_SECRET.encode("utf-8"), raw_wh, hashlib.sha256).hexdigest()
    wh_resp = client.post(
        f"/v1/opc/pilot-a/webhook/vietqr?run_id={run_id}&tenant_id=tenant_s11_08",
        content=raw_wh,
        headers={"Content-Type": "application/json", "X-VietQR-Signature": sig},
    )
    assert wh_resp.status_code == 200

    # After payment: settled on GET /runs/{run_id}
    post = client.get(f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_s11_08", headers=hdr)
    assert post.status_code == 200
    post_data = post.json()
    assert post_data["payment_state"] == "settled"
    assert post_data["paid_amount_vnd"] == amount_vnd
    assert post_data["bank_tx_id"] == "FT261119S1108"
    assert isinstance(post_data["paid_at"], int) and post_data["paid_at"] > 0


def test_s11_09_and_s11_10_dsar_retains_accounting_ledger_and_pdpl_2025_text(tmp_path: Path) -> None:
    """S11-09 & S11-10: DSAR erasure removes OPC PII, preserves VietQR financial ledger (redacting PII in memo), and cites VN PDPL 91/2025/QH15."""
    db_path = tmp_path / "tenant_privacy.db"
    wf = PilotAWorkflow(db_path=db_path, profile=_profile(), approval_secret=_SECRET, enforce_consent=True)
    sub = "84908887766"

    # S11-10: Missing consent error cites Law 91/2025/QH15
    with pytest.raises(ConsentRequiredError, match="91/2025/QH15"):
        wf.privacy_guard.require_consent(sub)

    consent_rec = wf.privacy_guard.record_subject_consent(sub)
    assert "91/2025/QH15" in str(consent_rec.get("legal_basis", ""))

    # Create run and settle VietQR payment (with subject phone embedded in bank memo)
    ev = _event("evt_s11_09_dsar", sender_id=sub)
    card = wf.handle_webhook(ev)
    raw_wh = json.dumps({
        "bank_tx_id": "FT261119DSAR01",
        "amount_vnd": card.total_amount_vnd,
        "memo": f"OPC {card.run_id} {sub}",
        "bank_id": "MB",
    }).encode("utf-8")
    sig = hmac.new(_VIETQR_SECRET.encode("utf-8"), raw_wh, hashlib.sha256).hexdigest()
    wf.reconcile_payment_and_export_draft(card, raw_wh, sig, _VIETQR_SECRET)

    # Execute DSAR erasure
    dsar = wf.privacy_guard.erase_subject_under_72h(sub)
    assert dsar["status"] == "COMPLETED"
    assert wf.state.get_run(card.run_id) is None
    assert dsar["vietqr_financial_records_retained"] >= 1
    assert "88/2015/QH13" in dsar["financial_retention_basis"]
    assert "91/2025/QH15" in dsar["legal_framework"]
    assert dsar["legal_review_required"] is True

    # Financial transaction row MUST still exist in vietqr DB, with PII redacted from memo
    vqr_db = tmp_path / "tenant_privacy_vietqr.db"
    with sqlite3.connect(str(vqr_db)) as vconn:
        row = vconn.execute(
            "SELECT bank_tx_id, amount_vnd, memo FROM transactions WHERE bank_tx_id = ?",
            ("FT261119DSAR01",),
        ).fetchone()
    assert row is not None
    assert row[0] == "FT261119DSAR01"
    assert int(row[1]) == card.total_amount_vnd
    assert sub not in str(row[2])
    assert "[REDACTED_DSAR]" in str(row[2])
