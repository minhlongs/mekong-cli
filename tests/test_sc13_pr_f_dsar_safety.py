"""Adversarial regression suite for exact-identity tenant-scoped DSAR safety and financial legal-hold retention."""
from __future__ import annotations

from decimal import Decimal
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3
import time
import unicodedata
from unittest.mock import patch

import pytest

from src.opc.dsar_identity import normalize_phone_vn, parse_dsar_subject
from src.opc.models import BusinessProfile
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.privacy_guard import PilotPrivacyGuard

_APPROVAL_SECRET = "sc13-dsar-approval-secret-2026"
_VIETQR_SECRET = "sc13-dsar-vietqr-secret-2026"


def _profile() -> BusinessProfile:
    return BusinessProfile(
        business_name="CTY TNHH MEKONG DSAR TEST",
        owner_name="Nguyễn Quốc Minh",
        currency="VND",
        language="vi",
        locale="vi-VN",
        timezone="Asia/Ho_Chi_Minh",
        services={"tu_van_ai": Decimal("2000000")},
        payment_terms="Chuyển khoản VietQR",
        preferences={"bank_id": "VCB", "account_no": "1020304050"},
    )


def _event(event_id: str, sender_id: str, sender_name: str, message_text: str = "Cần báo giá gói tu_van_ai 3 giờ") -> ZaloWebhookEvent:
    now = int(time.time())
    return ZaloWebhookEvent(
        event_id=event_id,
        oa_id="oa_dsar_01",
        sender_id=sender_id,
        sender_name=sender_name,
        message_text=message_text,
        requested_services=["tu_van_ai"],
        estimated_hours=3,
        project_title=f"Báo giá {sender_name}",
        timestamp=now,
        last_user_interaction_ts=now,
    )


def _settle_vietqr(wf: PilotAWorkflow, card, memo: str, bank_tx_id: str) -> None:
    raw = json.dumps({
        "bank_tx_id": bank_tx_id,
        "amount_vnd": card.total_amount_vnd,
        "memo": memo,
        "bank_id": "VCB",
    }).encode("utf-8")
    sig = hmac.new(_VIETQR_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    wf.reconcile_payment_and_export_draft(card, raw, sig, _VIETQR_SECRET)


def test_similar_vietnamese_names_and_three_char_substring_never_cross_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "tenant_vn.db"
    wf = PilotAWorkflow(db_path=db_path, profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    # 1. Two subjects with similar Vietnamese names (NFC vs NFD diacritics)
    name_a_nfc = unicodedata.normalize("NFC", "Nguyễn Văn An")
    name_b_nfd = unicodedata.normalize("NFD", "Nguyễn Văn Anh")
    sub_a = "84901112233"
    sub_b = "84909998877"
    wf.privacy_guard.record_subject_consent(sub_a)
    wf.privacy_guard.record_subject_consent(sub_b)

    card_a = wf.handle_webhook(_event("evt_vn_a", sub_a, name_a_nfc, "Cần báo giá gói tu_van_ai 3 giờ mã 111 cho Nguyễn Văn An"))
    card_b = wf.handle_webhook(_event("evt_vn_b", sub_b, name_b_nfd, "Cần báo giá gói tu_van_ai 3 giờ mã 111 cho Nguyễn Văn Anh"))
    _settle_vietqr(wf, card_a, f"OPC {card_a.run_id} NGUYEN VAN AN {sub_a} 111", "FT_VN_A")
    _settle_vietqr(wf, card_b, f"OPC {card_b.run_id} NGUYEN VAN ANH {sub_b} 111", "FT_VN_B")

    # 2. A 3-char substring ("111", "Anh") embedded in both transactions must be rejected
    for short_or_ambig in ("111", "Anh", "min", "Nguyễn Văn An", "Nguyen Van An"):
        with pytest.raises(ValueError, match="Invalid subject_id"):
            wf.privacy_guard.erase_subject_under_72h(short_or_ambig)

    # Both subjects remain completely intact after rejected requests
    assert wf.state.get_run(card_a.run_id) is not None
    assert wf.state.get_run(card_b.run_id) is not None

    # 3. Exact subject match using alternative VN phone format (+84 901 112 233) erases ONLY subject A
    dsar_a = wf.privacy_guard.erase_subject_under_72h("+84 901 112 233")
    assert dsar_a["status"] == "COMPLETED"
    assert dsar_a["matched_subject_kind"] == "phone"
    assert dsar_a["matched_run_ids"] == [card_a.run_id]

    # 4. Subject A's run erased; Subject B's run & financial record 100% untouched
    assert wf.state.get_run(card_a.run_id) is None
    assert wf.state.get_run(card_b.run_id) is not None

    # 9. Financial record for Subject A preserved under legal hold with PII redacted; Subject B's memo intact
    vqr_db = tmp_path / "tenant_vn_vietqr.db"
    with sqlite3.connect(str(vqr_db)) as vconn:
        tx_a = vconn.execute("SELECT memo FROM transactions WHERE bank_tx_id = 'FT_VN_A'").fetchone()
        tx_b = vconn.execute("SELECT memo FROM transactions WHERE bank_tx_id = 'FT_VN_B'").fetchone()
    assert tx_a is not None and sub_a not in tx_a[0] and "NGUYEN VAN AN" not in tx_a[0]
    assert tx_b is not None and sub_b in tx_b[0] and "NGUYEN VAN ANH" in tx_b[0]
    assert dsar_a["financial_legal_hold_preserved"] is True
    assert dsar_a["retention_policy_status"] == "PENDING_COUNSEL_DETERMINATION"
    assert dsar_a["legal_review_required"] is True


def test_same_sender_id_across_tenants_isolated(tmp_path: Path) -> None:
    # 5. Same sender_id across two isolated tenants
    shared_sender = "zalo_shared_user_42"
    wf_a = PilotAWorkflow(db_path=tmp_path / "tenant_a.db", profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    wf_b = PilotAWorkflow(db_path=tmp_path / "tenant_b.db", profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    wf_a.privacy_guard.record_subject_consent(shared_sender)
    wf_b.privacy_guard.record_subject_consent(shared_sender)

    card_a = wf_a.handle_webhook(_event("evt_ta_1", shared_sender, "Lê Minh Tuấn"))
    card_b = wf_b.handle_webhook(_event("evt_tb_1", shared_sender, "Lê Minh Tuấn"))

    res_a = wf_a.privacy_guard.erase_subject_under_72h(shared_sender)
    assert res_a["matched_run_ids"] == [card_a.run_id]
    assert wf_a.state.get_run(card_a.run_id) is None
    assert wf_b.state.get_run(card_b.run_id) is not None


def test_missing_malformed_wildcard_and_underscore_subject_ids(tmp_path: Path) -> None:
    guard = PilotPrivacyGuard(tmp_path / "priv.db", opc_db_path=tmp_path / "opc.db")
    # 6 & 7 & 8. Missing, malformed, SQL wildcard %, control chars, short, ambiguous name-only
    for bad in ("", "   ", "%", "%%", "_", "___", "abc", "123", "zalo%admin", "user\x00id", "Trần Thị Hoa", "Hoa", "bad@email"):
        with pytest.raises(ValueError, match="Invalid subject_id"):
            guard.erase_subject_under_72h(bad)

    # Valid underscore machine ID (e.g. zalo_user_01) must NOT act as SQL wildcard matching zaloXuserX01
    wf = PilotAWorkflow(db_path=tmp_path / "wild.db", profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    wf.privacy_guard.record_subject_consent("zalo_user_01")
    wf.privacy_guard.record_subject_consent("zaloXuserX01")
    c_under = wf.handle_webhook(_event("evt_w1", "zalo_user_01", "User Underscore"))
    c_other = wf.handle_webhook(_event("evt_w2", "zaloXuserX01", "User Other"))

    res = wf.privacy_guard.erase_subject_under_72h("zalo_user_01")
    assert res["matched_run_ids"] == [c_under.run_id]
    assert wf.state.get_run(c_under.run_id) is None
    assert wf.state.get_run(c_other.run_id) is not None


def test_exact_email_matching_retry_interruption_and_audit_consistency(tmp_path: Path) -> None:
    db_path = tmp_path / "tenant_retry.db"
    wf = PilotAWorkflow(db_path=db_path, profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    wf.privacy_guard.record_subject_consent("84905556677")
    card = wf.handle_webhook(_event("evt_em_1", "84905556677", "Phạm Thu Hà"))
    # Attach verified client_email in proposal_input_json to test case-normalized exact email matching
    with sqlite3.connect(str(db_path)) as conn:
        raw = json.loads(conn.execute("SELECT proposal_input_json FROM opc_runs WHERE run_id = ?", (card.run_id,)).fetchone()[0])
        raw["client_email"] = "Thu.Ha@Example.VN"
        conn.execute("UPDATE opc_runs SET proposal_input_json = ? WHERE run_id = ?", (json.dumps(raw), card.run_id))
        conn.commit()

    # 11. Interrupted operation leaves run intact; subsequent retry completes cleanly
    with patch("src.opc.privacy_guard.json_blob_matches_subject", side_effect=RuntimeError("simulated mid-operation interruption")):
        with pytest.raises(RuntimeError, match="simulated mid-operation interruption"):
            wf.privacy_guard.erase_subject_under_72h("thu.ha@example.vn")
    assert wf.state.get_run(card.run_id) is not None

    # 10. Retry completes and second retry is idempotent (0 additional mutations)
    res1 = wf.privacy_guard.erase_subject_under_72h("THU.HA@EXAMPLE.VN")
    assert res1["status"] == "COMPLETED"
    assert res1["matched_subject_kind"] == "email"
    assert res1["matched_run_ids"] == [card.run_id]
    assert wf.state.get_run(card.run_id) is None

    res2 = wf.privacy_guard.erase_subject_under_72h("thu.ha@example.vn")
    assert res2["opc_rows_erased"] == 0
    assert res2["matched_run_ids"] == []

    # 12. Audit consistency: PRAGMA foreign_key_check clean and dsar_requests recorded
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    with sqlite3.connect(str(wf.privacy_guard.engine.db_path)) as pconn:
        statuses = [r[0] for r in pconn.execute("SELECT status FROM dsar_requests").fetchall()]
    assert "COMPLETED" in statuses

    # Verify phone normalization helper across VN formats
    assert normalize_phone_vn("0901 112 233") == "84901112233"
    assert normalize_phone_vn("+84-901-112-233") == "84901112233"
    assert parse_dsar_subject("0901.112.233").normalized == "84901112233"


def test_channel_prefix_pii_free_errors_tenant_zalo_isolation_and_consent_variants(tmp_path: Path) -> None:
    """Channel prefixes strip cleanly, errors never echo raw PII, shared zalo.db is untouched, and consent variants erase."""
    # Channel prefix stripping & explicit subject_type validation
    assert parse_dsar_subject("phone:+84 901 112 233").normalized == "84901112233"
    assert parse_dsar_subject("email:An.Nguyen@Example.VN").normalized == "an.nguyen@example.vn"
    assert parse_dsar_subject("zalo:usr_778899").normalized == "usr_778899"
    with pytest.raises(ValueError) as exc_info:
        parse_dsar_subject("0901112233", subject_type="email")
    assert "0901112233" not in str(exc_info.value)
    with pytest.raises(ValueError):
        parse_dsar_subject("usr_778899", subject_type="invalid_type")

    # Shared sibling zalo.db must NEVER be mutated by a tenant-scoped PilotPrivacyGuard DSAR
    shared_zalo = tmp_path / "zalo.db"
    with sqlite3.connect(str(shared_zalo)) as zconn:
        zconn.execute("CREATE TABLE followers (user_id TEXT PRIMARY KEY, phone TEXT, name TEXT)")
        zconn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, user_id TEXT, body TEXT)")
        zconn.execute("INSERT INTO followers VALUES ('84901112233', '84901112233', 'Other Tenant User')")
        zconn.execute("INSERT INTO messages VALUES (1, '84901112233', 'other tenant msg')")
        zconn.commit()

    db_path = tmp_path / "tenant_iso.db"
    wf = PilotAWorkflow(db_path=db_path, profile=_profile(), approval_secret=_APPROVAL_SECRET, enforce_consent=True)
    wf.privacy_guard.record_subject_consent("+84 901 112 233")
    res = wf.privacy_guard.erase_subject_under_72h("0901.112.233")
    assert res["consent_rows_erased"] >= 1
    assert res["status"] == "COMPLETED"
    with sqlite3.connect(str(wf.privacy_guard.engine.db_path)) as pconn:
        assert pconn.execute("SELECT COUNT(*) FROM consent_log").fetchone()[0] == 0
    # Shared zalo.db remains completely untouched
    with sqlite3.connect(str(shared_zalo)) as zconn:
        assert zconn.execute("SELECT COUNT(*) FROM followers").fetchone()[0] == 1
        assert zconn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1

