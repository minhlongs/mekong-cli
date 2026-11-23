"""SC11 PR-A Regression Suite: S11-01 (Approval), S11-02 (Quota), S11-03 (CORS), S11-04 (Isolation), S11-05 (VAT)."""
from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.opc.accounting_draft import (
    build_accounting_draft_export,
    compute_vnd_vat_breakdown,
)
from src.opc.models import BusinessProfile
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.privacy_guard import HaltForHumanError
from src.opc.verifier import MIN_EXTRACTION_CONFIDENCE


def _profile(rate_a: str = "600000", rate_b: str = "400000") -> BusinessProfile:
    return BusinessProfile(
        business_name="CONG TY TNHH MEKONG SC11",
        owner_name="Nguyen Thi Mai",
        language="vi",
        locale="vi_VN",
        timezone="Asia/Ho_Chi_Minh",
        currency="VND",
        services={"tu_van_ai": Decimal(rate_a), "tich_hop_vietqr": Decimal(rate_b)},
        payment_terms="Thanh toan 100% qua VietQR Napas 247",
        jurisdiction="VN",
        preferences={"bank_id": "MB", "account_no": "0988889999"},
    )


def _event(
    event_id: str,
    message_text: str = "Nhờ báo giá gói tư vấn AI và tích hợp VietQR 10 giờ.",
    *,
    extraction_confidence: float | None = None,
    hours: int = 10,
) -> ZaloWebhookEvent:
    now_ts = 1_760_000_000
    return ZaloWebhookEvent(
        event_id=event_id,
        oa_id="oa_sc11",
        sender_id="84909123456",
        sender_name="Công ty TNHH Kiểm Thử SC11",
        message_text=message_text,
        timestamp=now_ts,
        last_user_interaction_ts=now_ts - 600,
        requested_services=("tu_van_ai", "tich_hop_vietqr"),
        estimated_hours=hours,
        project_title="Dự Án SC11",
        currency="VND",
        language="vi",
        extraction_confidence=extraction_confidence,
    )


# ---------------------------------------------------------------------------
# S11-01: Approval fail-closed on low_confidence_halt & missing confidence
# ---------------------------------------------------------------------------
def test_s11_01_low_confidence_halt_and_missing_confidence_fail_closed(tmp_path: Path) -> None:
    """Ambiguous message (router_mode=low_confidence_halt) with omitted or high extraction_confidence must halt."""
    wf = PilotAWorkflow(
        db_path=tmp_path / "s11_01.db",
        profile=_profile(),
        handoff_on_low_confidence=True,
    )
    ambiguous_no_conf = _event(
        "evt_s11_01_missing",
        message_text="Chào shop, mình muốn hỏi thêm thông tin.",
        extraction_confidence=None,
    )
    with pytest.raises(HaltForHumanError) as exc_info:
        wf.handle_webhook(ambiguous_no_conf)
    assert exc_info.value.code == "HALT_LOW_CONFIDENCE"
    assert wf.usage.quota_guard.get_period_usage("default", "2025-10") == 0

    # Even if caller passes extraction_confidence=1.0, router low_confidence_halt must fail closed
    ambiguous_high_conf = _event(
        "evt_s11_01_high",
        message_text="Chào shop, mình muốn hỏi thêm thông tin.",
        extraction_confidence=1.0,
    )
    with pytest.raises(HaltForHumanError):
        wf.handle_webhook(ambiguous_high_conf)

    # handle_webhook_or_handoff converts HaltForHumanError into HANDOFF_ZALO_OA_MANAGER with 0 dispatches
    handoff = wf.handle_webhook_or_handoff(ambiguous_no_conf)
    assert isinstance(handoff, dict)
    assert handoff["status"] == "HANDOFF_ZALO_OA_MANAGER"
    assert handoff["reason_code"] == "HALT_LOW_CONFIDENCE"
    assert len(wf.zalo_connector.dispatched) == 0


def test_s11_01_high_confidence_with_omitted_field_uses_router_confidence(tmp_path: Path) -> None:
    """When extraction_confidence is None and deterministic router matches services+hours (>=0.85), workflow proceeds."""
    wf = PilotAWorkflow(db_path=tmp_path / "s11_01_ok.db", profile=_profile())
    card = wf.handle_webhook(_event("evt_s11_01_ok", extraction_confidence=None))
    assert card.run_id.startswith("run_")
    assert MIN_EXTRACTION_CONFIDENCE <= 0.95


# ---------------------------------------------------------------------------
# S11-02: Quota deduplication cannot release an already-committed slot
# ---------------------------------------------------------------------------
def test_s11_02_duplicate_event_cannot_release_committed_quota_slot_or_mint_second_run(tmp_path: Path) -> None:
    """Replaying event_id returns the original run idempotently; failing replay never deletes the committed slot."""
    wf = PilotAWorkflow(db_path=tmp_path / "s11_02.db", profile=_profile(), workflow_quota_limit=1)
    first_event = _event("evt_s11_02_dup")
    card_1 = wf.handle_webhook(first_event)
    assert wf.usage.quota_guard.get_period_usage("default", "2025-10") == 1

    # Replay identical event_id -> idempotent return of same run_id, quota stays 1
    card_2 = wf.handle_webhook(first_event)
    assert card_2.run_id == card_1.run_id
    assert wf.usage.quota_guard.get_period_usage("default", "2025-10") == 1

    # Replay same event_id with low confidence -> halts BEFORE quota touch, committed slot stays 1
    bad_replay = dataclasses.replace(first_event, extraction_confidence=0.40)
    with pytest.raises(HaltForHumanError):
        wf.handle_webhook(bad_replay)
    assert wf.usage.quota_guard.get_period_usage("default", "2025-10") == 1

    # Direct release_workflow_slot on a committed slot must return False and preserve the row
    assert wf.usage.quota_guard.release_workflow_slot("default", "evt_s11_02_dup", "2025-10") is False
    assert wf.usage.quota_guard.get_period_usage("default", "2025-10") == 1


# ---------------------------------------------------------------------------
# S11-03: CORS preflight allows X-Checkout-Secret & X-Card-Sig for allowed origins
# ---------------------------------------------------------------------------
def test_s11_03_cors_preflight_allows_checkout_secret_and_card_sig_and_rejects_unknown_origin() -> None:
    """OPTIONS preflight for localhost:3000 allows X-Checkout-Secret and X-Card-Sig; untrusted origin is rejected."""
    from src.gateway import app

    client = TestClient(app)
    for header_name, path in (
        ("X-Checkout-Secret", "/v1/checkout/status"),
        ("X-Card-Sig", "/v1/opc/pilot-a/decide"),
    ):
        resp = client.options(
            path,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET" if "status" in path else "POST",
                "Access-Control-Request-Headers": header_name,
            },
        )
        assert resp.status_code == 200, resp.text
        allowed = resp.headers.get("access-control-allow-headers", "").lower()
        assert header_name.lower() in allowed

    bad_origin = client.options(
        "/v1/checkout/status",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Checkout-Secret",
        },
    )
    assert "access-control-allow-origin" not in {k.lower() for k in bad_origin.headers}


# ---------------------------------------------------------------------------
# S11-04: Environment isolation after test_scoped_credential_vault
# ---------------------------------------------------------------------------
def test_s11_04_conftest_env_vars_preserved_across_vault_tests() -> None:
    """MEKONG_RAAS_DB and MEKONG_ALLOW_UNSIGNED_IPN set by tests/conftest.py remain intact."""
    assert os.environ.get("MEKONG_RAAS_DB"), "MEKONG_RAAS_DB leaked/cleared by prior test"
    assert os.environ.get("MEKONG_ALLOW_UNSIGNED_IPN") == "1"


# ---------------------------------------------------------------------------
# S11-05: End-to-end VAT-inclusive VietQR == settled == AccountingDraft total
#         + ROUND_HALF_UP (no int truncation)
# ---------------------------------------------------------------------------
def test_s11_05_vat_rounding_half_up_and_vietqr_matches_accounting_draft_total(tmp_path: Path) -> None:
    """Quote, VietQR EMVCo, bank settlement, and AccountingDraft total must all equal subtotal + ROUND_HALF_UP(VAT)."""
    # 1. Verify ROUND_HALF_UP on fractional VAT: 125_007 * 8% = 10_000.56 -> rounds to 10_001 (not truncated 10_000)
    sub, vat, total = compute_vnd_vat_breakdown(Decimal("125007"), 8)
    assert sub == 125_007
    assert vat == 10_001
    assert total == 135_008

    # 2. Verify full Pilot A workflow: 5h * 100,007 + 5h * 50,000 = 750,035 subtotal
    #    8% VAT = 60,002.80 -> ROUND_HALF_UP = 60,003 -> gross = 810,038 VND
    wf = PilotAWorkflow(
        db_path=tmp_path / "s11_05.db",
        profile=_profile(rate_a="100007", rate_b="50000"),
        vat_rate_pct=8,
    )
    card = wf.handle_webhook(_event("evt_s11_05_vat", hours=10))
    assert card.subtotal_vnd == 750_035
    assert card.vat_rate_pct == 8
    assert card.vat_amount_vnd == 60_003
    assert card.total_amount_vnd == 810_038
    assert f"5406{810038}" in card.vietqr_emvco

    secret = "sc11-vietqr-test-secret-2026"
    raw = json.dumps({
        "bank_tx_id": "NAPAS-SC11-VAT-01",
        "amount_vnd": 810_038,
        "memo": f"Thanh toan OPC {card.run_id}",
    }).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    recon, draft = wf.reconcile_payment_and_export_draft(card, raw, sig, secret)
    assert recon["amount_vnd"] == 810_038
    assert draft.subtotal_vnd == 750_035
    assert draft.vat_amount_vnd == 60_003
    assert draft.total_amount_vnd == 810_038
    assert draft.total_amount_vnd == card.total_amount_vnd == recon["amount_vnd"]

    # 3. Attempting to export with a mismatched settled_amount_vnd must fail closed
    with pytest.raises(ValueError, match="does not match"):
        build_accounting_draft_export(
            card.run_id, card.client_name, card.line_items, card.subtotal_vnd,
            vat_rate_pct=8, bank_tx_id="NAPAS-SC11-VAT-01", settled_amount_vnd=750_035,
        )
