"""Strategy E Verification Suite (Part 1): Fail-Closed Approval, ZaloOAConnector,
Decree 13 PDPD Consent/<72h DSAR SQL-Safe Erasure, PII Redaction, and Math/NaN Halt.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from src.opc.approval import ApprovalSecurityError, PayloadBoundApprovalEngine
from src.opc.connectors.zalo_http import (
    ZaloOAConnector,
    ZaloTierPolicyError,
    ZaloWebhookMacError,
    verify_zalo_webhook_mac,
)
from src.opc.models import BusinessProfile, WorkflowStatus
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.privacy_guard import (
    ConsentRequiredError,
    HaltForHumanError,
    TenantIsolationError,
    compact_conversation_preserving_moim,
    redact_vietnamese_pii,
    verify_confidence_and_math,
)
from src.opc.quota import WorkflowQuotaExceededError

REPO_ROOT = Path(__file__).resolve().parent.parent


def _profile() -> BusinessProfile:
    return BusinessProfile(
        business_name="CONG TY TNHH MEKONG STRATEGY E", owner_name="Nguyen Thi Mai",
        language="vi", locale="vi_VN", timezone="Asia/Ho_Chi_Minh", currency="VND",
        services={"tu_van_ai": Decimal("600000"), "tich_hop_vietqr": Decimal("400000")},
        payment_terms="Thanh toan 100% qua VietQR Napas 247", jurisdiction="VN",
        preferences={"bank_id": "MB", "account_no": "0988889999"},
    )


def _event(
    event_id: str = "evt_se_01",
    message: str = "Chào shop, mình là Hùng (SĐT 0909 123 456, CCCD 079090001234, email hung@abc.vn), báo giá gói 10 giờ.",
    confidence: float = 0.96,
    sender_id: str = "84909123456",
) -> ZaloWebhookEvent:
    now_ts = 1_760_000_000
    return ZaloWebhookEvent(
        event_id=event_id, oa_id="oa_growth_01", sender_id=sender_id, sender_name="Công ty TNHH Hùng Phát",
        message_text=message, timestamp=now_ts, last_user_interaction_ts=now_ts - 900,
        requested_services=("tu_van_ai", "tich_hop_vietqr"), estimated_hours=10,
        project_title="Tự Động Hóa Zalo OA & VietQR", currency="VND", language="vi",
        extraction_confidence=confidence,
    )


def test_approval_secret_fails_closed_on_missing_or_short_env_and_explicit_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset or <16-byte MEKONG_APPROVAL_SECRET / explicit secret_key raises ApprovalSecurityError."""
    proc = subprocess.run(
        [sys.executable, "-c", "from src.opc.approval import PayloadBoundApprovalEngine; PayloadBoundApprovalEngine()"],
        cwd=REPO_ROOT, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode != 0 and "ApprovalSecurityError" in proc.stderr

    for bad_key in ("short-secret", "a", b"x", b"   "):
        with pytest.raises(ApprovalSecurityError):
            PayloadBoundApprovalEngine(secret_key=bad_key)  # type: ignore[arg-type]

    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", "short-12char")
    with pytest.raises(ApprovalSecurityError, match="at least 16 bytes"):
        PayloadBoundApprovalEngine()

    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", "valid-production-approval-secret-2026")
    assert PayloadBoundApprovalEngine().default_ttl == 3600


def test_zalo_oa_connector_tier_mac_non_dict_json_silent_error_and_timeout(tmp_path: Path) -> None:
    """ZaloOAConnector enforces Growth/Enterprise tier, mandatory MAC, non-dict/bool JSON safety, and timeout."""
    for blocked_tier in ("basic", "trial", "standard", "co_ban", "tieu_chuan"):
        with pytest.raises(ZaloTierPolicyError, match="not eligible"):
            ZaloOAConnector(access_token="tok_x", oa_tier=blocked_tier)

    raw_data = '{"event_name":"user_send_text"}'
    ts, app_id, oa_secret = 1_760_000_000, "app_99", "oa_secret_test_only"
    good_mac = hashlib.sha256(f"{app_id}{raw_data}{ts}{oa_secret}".encode("utf-8")).hexdigest()
    assert verify_zalo_webhook_mac(app_id, raw_data, ts, oa_secret, f"mac={good_mac}") is True

    captured: list[dict[str, str]] = []
    conn_ok = ZaloOAConnector(
        access_token="zalo_growth_tok", oa_tier="growth",
        transport=lambda _u, h, _b, _t: (captured.append(h) or 200, b'{"error":0,"message":"Success","data":{"message_id":"msg_zalo_001"}}'),
    )
    wf = PilotAWorkflow(db_path=tmp_path / "zalo_ok.db", profile=_profile(), zalo_connector=conn_ok)
    # Live ZaloOAConnector requires webhook MAC even if caller omits webhook_mac arg
    with pytest.raises(ZaloWebhookMacError):
        wf.handle_webhook(_event("evt_missing_mac"))
    card = wf.handle_webhook(_event("evt_good_mac"), webhook_mac=good_mac, oa_secret_key=oa_secret, app_id=app_id, raw_webhook_data=raw_data)
    sent = wf.approve_and_send(card, idempotency_key="idem_zalo_http_1")
    assert sent["status"] == "completed" and sent["result"]["record"]["message_id"] == "msg_zalo_001"
    assert captured[0]["X-Idempotency-Key"] == "idem_zalo_http_1"

    # Malformed shapes: non-dict JSON, bool error=false, and silent error=-213 all fail cleanly
    for bad_body in (b"[]", b"null", b'{"error":false}', b'{"error":-213,"message":"48h expired"}'):
        conn_bad = ZaloOAConnector(access_token="tok", oa_tier="enterprise", transport=lambda *_a, b=bad_body: (200, b))
        wf_b = PilotAWorkflow(db_path=tmp_path / "zalo_bad.db", profile=_profile(), zalo_connector=conn_bad, require_webhook_mac=False)
        c_b = wf_b.handle_webhook(_event(f"evt_{hashlib.md5(bad_body).hexdigest()[:6]}"))  # noqa: S324
        assert wf_b.approve_and_send(c_b)["status"] == "failed"

    def _timeout(*_a: object) -> tuple[int, bytes]:
        raise TimeoutError("gateway timeout")

    conn_to = ZaloOAConnector(access_token="tok", oa_tier="growth", transport=_timeout)
    wf_to = PilotAWorkflow(db_path=tmp_path / "zalo_to.db", profile=_profile(), zalo_connector=conn_to, require_webhook_mac=False)
    c_to = wf_to.handle_webhook(_event("evt_to"))
    assert wf_to.approve_and_send(c_to)["status"] == "reconciliation_required"
    run_to = wf_to.state.get_run(c_to.run_id)
    assert run_to is not None and run_to["status"] == WorkflowStatus.RECONCILIATION_REQUIRED


def test_decree13_dsar_wildcard_safety_fk_integrity_pii_nan_and_live_quota(tmp_path: Path) -> None:
    """DSAR blocks '%'/'_' wipes, preserves FK integrity, handles >20 consents, NaN/negative math, and live quota."""
    db_file = tmp_path / "pdpd.db"
    wf = PilotAWorkflow(db_path=db_file, profile=_profile(), enforce_consent=True, workflow_quota_limit=2)
    ev1 = _event("evt_c1", sender_id="84909123456")
    ev2 = _event("evt_c2", sender_id="84918887766")

    with pytest.raises(ConsentRequiredError):
        wf.handle_webhook(ev1)
    wf.privacy_guard.record_subject_consent(ev1.sender_id)
    wf.privacy_guard.record_subject_consent(ev2.sender_id)
    for idx in range(25):
        wf.privacy_guard.record_subject_consent(ev1.sender_id, purpose=f"other_purpose_{idx}")
    card1 = wf.handle_webhook(ev1)
    card2 = wf.handle_webhook(ev2)
    assert "<PII_PHONE_" in card1.redacted_notes and "0909 123 456" not in card1.redacted_notes
    # Live PilotAWorkflow enforces workflow_quota_limit=2 on 3rd distinct event
    with pytest.raises(WorkflowQuotaExceededError):
        wf.handle_webhook(_event("evt_c3_over_quota", sender_id="84909123456"))

    red = redact_vietnamese_pii("MST: 0101234567, CMND: 025678912, STK: 0988889999, SĐT +84 912-345-678")
    assert red.redacted_count == 4 and "0101234567" not in red.redacted_text and "<PII_BANK_ACC_" in red.redacted_text

    # Wildcard DSAR injection attempts must fail without touching card1 or card2
    for bad_sub in ("", "%", "_", "%%"):
        with pytest.raises(ValueError, match="Invalid subject_id"):
            wf.privacy_guard.erase_subject_under_72h(bad_sub)
    dsar = wf.privacy_guard.erase_subject_under_72h(ev1.sender_id)
    assert dsar["statutory_deadline"]["deadline_days"] == 3 and dsar["status"] == "COMPLETED"
    assert wf.state.get_run(card1.run_id) is None and wf.state.get_run(card2.run_id) is not None
    with sqlite3.connect(str(db_file)) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    # NaN / inf / negative math & tenant traversal + MOIM compaction
    for bad_conf in (0.80, float("nan"), float("inf"), 1.5):
        with pytest.raises(HaltForHumanError, match="HALT_FOR_HUMAN"):
            verify_confidence_and_math([{"hours": 1, "rate": "100", "subtotal": "100"}], "100", confidence=bad_conf)
    for neg_items, neg_tot in (([{"hours": -2, "rate": "100"}], "-200"), ([{"hours": 2, "rate": "100", "subtotal": "250"}], "250")):
        with pytest.raises(HaltForHumanError, match="MATH_MISMATCH_REQUIRES_HUMAN"):
            verify_confidence_and_math(neg_items, neg_tot)
    with pytest.raises(TenantIsolationError):
        PilotAWorkflow(db_path=tmp_path / "t.db", profile=_profile(), tenant_id="../bad")
    comp = compact_conversation_preserving_moim([f"t{i}" for i in range(20)], "[MOIM] rule", keep_recent=4)
    assert comp[0] == "[MOIM] rule" and len(comp) == 6 and json.dumps(comp) != ""
