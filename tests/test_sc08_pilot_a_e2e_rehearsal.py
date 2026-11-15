"""Phase 5 Realistic E2E Readiness Rehearsal (Zero Live External Side Effects) & 15-Layer MEKONG-BENCH."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.gateway import app
from src.opc.accounting_draft import DRAFT_STATUS_PENDING_TVAN
from src.opc.connectors.zalo_http import verify_zalo_webhook_mac
from src.opc.mekong_bench import MekongBenchRunner, _bench_profile
from src.opc.models import UsageRecord, UsageStage
from src.opc.pilot_a import PilotAWorkflow
from src.opc.selective_router import SelectiveRouter
from src.opc.tenant_provisioner import provision_isolated_tenant
from src.opc.verifier import HaltForHumanError, verify_confidence_and_math

REPO_ROOT = Path(__file__).resolve().parent.parent
ZALO_SECRET = "sc08-e2e-zalo-oa-hmac-secret-2026"
VIETQR_SECRET = "sc08-e2e-vietqr-napas-secret-2026"
APPROVAL_SECRET = "sc08-e2e-owner-approval-secret-2026"


def _sign_zalo(app_id: str, raw_body: bytes, ts: int, secret: str = ZALO_SECRET) -> str:
    return hashlib.sha256(app_id.encode("utf-8") + raw_body + str(ts).encode("utf-8") + secret.encode("utf-8")).hexdigest()


def _sign_vietqr(raw_body: bytes, secret: str = VIETQR_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


@pytest.fixture()
def e2e_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    tenants_dir = tmp_path / "pilot_a_e2e_tenants"
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(tenants_dir))
    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", APPROVAL_SECRET)
    monkeypatch.setenv("VIETQR_WEBHOOK_SECRET", VIETQR_SECRET)
    monkeypatch.setenv("ZALO_OA_SECRET_KEY", ZALO_SECRET)
    monkeypatch.setenv("ZALO_OA_ACCESS_TOKEN", "synthetic-zalo-oa-token-no-live-calls")
    monkeypatch.setenv("MEKONG_ENV", "production")
    return TestClient(app), tenants_dir


def test_sc08_realistic_golden_e2e_workflow_and_metrics(e2e_env: tuple[TestClient, Path]) -> None:
    """Synthetic golden path:
    Zalo webhook -> intent extraction -> deterministic quote -> owner approval ->
    VietQR creation -> verified mock settlement -> DRAFT_PENDING_TVAN accounting draft -> audit event.
    Zero live network calls, zero unauthorized side effects.
    """
    client, tenants_dir = e2e_env
    prov = provision_isolated_tenant(
        tenants_dir,
        "sme_minhlong_01",
        "CÔNG TY TNHH NỘI THẤT MINH LONG",
        "Nguyễn Minh Tâm",
        sme_tier="pilot_a",
        bank_id="MB",
        account_no="0988889999",
    )
    owner_headers = {"X-API-Key": prov.tenant_api_key}
    dispatched_zalo: list[tuple[str, bytes]] = []

    def _mock_zalo_http(url: str, _headers: dict[str, str], body: bytes, _timeout: float = 8.0) -> tuple[int, bytes]:
        dispatched_zalo.append((url, body))
        return 200, b'{"error":0,"message":"Success","data":{"message_id":"msg_synth_001"}}'

    # Pre-record Decree 13 customer consent via owner-authenticated channel
    now_ts = 1_794_800_000
    with patch("src.opc.connectors.zalo_http._stdlib_http_post", side_effect=_mock_zalo_http), \
         patch("src.api.pilot_a_routes.time.time", return_value=now_ts):
        seed_res = client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_consent_001",
                "oa_id": "oa_minhlong_vn",
                "sender_id": "84909382910",
                "sender_name": "Công ty TNHH Sao Khuê",
                "message_text": "Đồng ý nhận báo giá gói tư vấn AI 2 giờ.",
                "timestamp": now_ts,
                "last_user_interaction_ts": now_ts - 120,
                "requested_services": ["tu_van_ai"],
                "estimated_hours": 2,
                "tenant_id": "sme_minhlong_01",
                "require_consent": True,
                "grant_consent": True,
            },
            headers=owner_headers,
        )
        assert seed_res.status_code == 200

        # 1. Signed external Zalo OA webhook -> intent/citation extraction -> deterministic quote + VietQR
        inbound_payload = {
            "event_id": "evt_golden_zalo_01",
            "oa_id": "oa_minhlong_vn",
            "app_id": "zalo_app_vn_01",
            "sender_id": "84909382910",
            "sender_name": "Công ty TNHH Sao Khuê",
            "message_text": "Shop báo giá gói tư vấn AI và tích hợp VietQR 10 giờ, sđt 0909382910, MST 0312345678 nhé.",
            "timestamp": now_ts + 10,
            "last_user_interaction_ts": now_ts - 60,
            "requested_services": ["tu_van_ai", "tich_hop_vietqr"],
            "estimated_hours": 10,
            "project_title": "Triển khai Báo giá Zalo OA & VietQR Napas 247",
            "connector": "zalo_oa",
            "require_consent": True,
            "tenant_id": "sme_minhlong_01",
        }
        raw_zalo = json.dumps(inbound_payload, ensure_ascii=False).encode("utf-8")
        mac = _sign_zalo("zalo_app_vn_01", raw_zalo, now_ts + 10)
        assert verify_zalo_webhook_mac("zalo_app_vn_01", raw_zalo, now_ts + 10, ZALO_SECRET, mac)

        t_quote_start = time.perf_counter()
        wh_res = client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            content=raw_zalo,
            headers={"Content-Type": "application/json", "X-ZEvent-Mac": mac},
        )
        quote_latency_ms = (time.perf_counter() - t_quote_start) * 1000.0
        assert wh_res.status_code == 200, wh_res.text
        assert quote_latency_ms < 500.0

        wh_body = wh_res.json()
        run_id = wh_body["run_id"]
        digest = wh_body["action_digest"]
        # External webhook caller never receives card_sig
        assert "card_sig" not in wh_body and "sig=" not in wh_body["card_url"]
        # PII redacted (phone & MST never persisted raw in notes)
        assert "0909382910" not in wh_body["redacted_notes"]
        assert "0312345678" not in wh_body["redacted_notes"]
        # Deterministic math: 5h * 600,000 + 5h * 400,000 = 5,000,000 VND
        assert wh_body["total_amount_vnd"] == 5_000_000
        assert wh_body["vietqr_emvco"].startswith("000201010212")
        assert wh_body["accounting_draft_status"] == DRAFT_STATUS_PENDING_TVAN
        assert len(dispatched_zalo) == 0  # Zero external messages sent prior to owner approval

        # 2. Owner inspects run & mobile approval card -> 1-tap owner approval
        run_info = client.get(f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=sme_minhlong_01", headers=owner_headers).json()
        card_sig = run_info["card_sig"]
        assert run_info["checkpoint_stage"] == "INTERRUPT_AUTHORIZE"
        assert run_info["economics"]["known_amounts"].get("VND") == "0.00"

        card_html = client.get(
            f"/v1/opc/pilot-a/card/{run_id}?tenant_id=sme_minhlong_01",
            headers={"X-Card-Sig": card_sig},
        )
        assert card_html.status_code == 200 and len(card_html.text.encode("utf-8")) < 15_000
        assert "no-store" in card_html.headers.get("cache-control", "")
        assert card_html.headers.get("referrer-policy") == "no-referrer"

        dec_res = client.post(
            "/v1/opc/pilot-a/decide",
            json={
                "run_id": run_id,
                "tenant_id": "sme_minhlong_01",
                "decision": "approve",
                "action_digest": digest,
                "card_sig": card_sig,
            },
            headers={"X-Card-Sig": card_sig},
        )
        assert dec_res.status_code == 200 and dec_res.json()["status"] == "completed"
        assert len(dispatched_zalo) == 1  # Exactly 1 synthetic Zalo dispatch after owner approval

        # 3. Verified mock bank VietQR settlement -> accounting draft -> audit trail verification
        vqr_body = json.dumps(
            {"bank_tx_id": "NAPAS-E2E-GOLD-01", "amount_vnd": 5_000_000, "memo": f"Thanh toan OPC {run_id}"}
        ).encode("utf-8")
        vqr_res = client.post(
            f"/v1/opc/pilot-a/webhook/vietqr?run_id={run_id}&tenant_id=sme_minhlong_01&vat_rate_pct=8&target_provider=misa_meinvoice",
            content=vqr_body,
            headers={"Content-Type": "application/json", "X-VietQR-Signature": _sign_vietqr(vqr_body)},
        )
        assert vqr_res.status_code == 200
        draft = vqr_res.json()["accounting_draft"]
        assert draft["invoice_status"] == DRAFT_STATUS_PENDING_TVAN
        assert draft["invoice_status"] != "ISSUED"
        assert draft["requires_tvan_signature"] is True and draft["legal_certified"] is False
        assert draft["subtotal_vnd"] == 5_000_000 and draft["vat_amount_vnd"] == 400_000 and draft["total_amount_vnd"] == 5_400_000
        assert draft["bank_tx_id"] == "NAPAS-E2E-GOLD-01"

        for fmt in ("json", "csv", "xml"):
            exp_res = client.get(
                f"/v1/opc/pilot-a/draft-export/{run_id}?fmt={fmt}&tenant_id=sme_minhlong_01",
                headers=owner_headers,
            )
            assert exp_res.status_code == 200
            assert DRAFT_STATUS_PENDING_TVAN in exp_res.text
            assert "NAPAS-E2E-GOLD-01" in exp_res.text

    # 4. Audit trail verification in tenant SQLite WAL DB
    with sqlite3.connect(prov.db_path) as conn:
        action_rows = conn.execute("SELECT status FROM opc_actions WHERE run_id = ?", (run_id,)).fetchall()
        approval_rows = conn.execute("SELECT consumed, decision FROM opc_approvals WHERE run_id = ?", (run_id,)).fetchall()
        cp_row = conn.execute("SELECT current_stage, interrupted FROM opc_graph_checkpoints WHERE thread_id = ?", (run_id,)).fetchone()
        usage_rows = conn.execute("SELECT stage, amount FROM opc_usage_events WHERE run_id = ?", (run_id,)).fetchall()
    assert len(action_rows) == 1 and action_rows[0][0] == "completed"
    assert any(r[0] == 1 and r[1] == "approve" for r in approval_rows)
    assert cp_row is not None and cp_row[0] == "COMPLETED" and cp_row[1] == 0
    assert len(usage_rows) >= 2


def test_sc08_all_14_adversarial_and_fault_injection_scenarios(
    e2e_env: tuple[TestClient, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercises all 14 mandatory fault/adversarial scenarios with 0 unauthorized actions,
    0 duplicate financial side effects, 0 cross-tenant leaks, 0 payload mismatches accepted,
    and 0 silent budget bypasses.
    """
    client, tenants_dir = e2e_env
    t_a = provision_isolated_tenant(tenants_dir, "tenant_e2e_a", "CTY ALPHA VN", "Chủ A", sme_tier="pilot_a")
    t_b = provision_isolated_tenant(tenants_dir, "tenant_e2e_b", "CTY BRAVO VN", "Chủ B", sme_tier="pilot_a")
    hdr_a = {"X-API-Key": t_a.tenant_api_key}
    hdr_b = {"X-API-Key": t_b.tenant_api_key}
    dispatches: list[str] = []

    def _mock_zalo_post(_url: str, _headers: dict[str, str], body: bytes, _timeout: float = 8.0) -> tuple[int, bytes]:
        dispatches.append(body.decode("utf-8", errors="ignore"))
        return 200, b'{"error":0,"message":"Success","data":{"message_id":"m_ok"}}'

    now_ts = 1_794_810_000
    with patch("src.opc.connectors.zalo_http._stdlib_http_post", side_effect=_mock_zalo_post), \
         patch("src.api.pilot_a_routes.time.time", return_value=now_ts):
        # Seed consent for sender_ok on tenant_e2e_a
        client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "seed_a",
                "sender_id": "84911000111",
                "sender_name": "Khách A",
                "message_text": "Đồng ý tư vấn AI 2 giờ",
                "timestamp": now_ts,
                "last_user_interaction_ts": now_ts - 100,
                "tenant_id": "tenant_e2e_a",
                "require_consent": True,
                "grant_consent": True,
            },
            headers=hdr_a,
        )

        # (2) Invalid MAC/HMAC signatures -> HTTP 401/403, 0 side effects
        bad_raw = json.dumps(
            {
                "event_id": "evt_bad_mac",
                "app_id": "app1",
                "sender_id": "84911000111",
                "sender_name": "Khách A",
                "message_text": "Tư vấn AI 4 giờ",
                "timestamp": now_ts,
                "connector": "zalo_oa",
                "tenant_id": "tenant_e2e_a",
            }
        ).encode("utf-8")
        assert client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            content=bad_raw,
            headers={"Content-Type": "application/json", "X-ZEvent-Mac": "0" * 64},
        ).status_code == 401

        # (5) Missing tenant credentials -> HTTP 401 across all owner endpoints
        assert client.get("/v1/opc/pilot-a/runs/run_any?tenant_id=tenant_e2e_a").status_code == 401
        assert client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": "run_any", "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": "a" * 64},
        ).status_code == 401

        # (1) Duplicate & out-of-order webhook events + (6) Concurrent decisions
        dup_body = {
            "event_id": "evt_dup_001",
            "app_id": "app1",
            "sender_id": "84911000111",
            "sender_name": "Khách A",
            "message_text": "Báo giá gói tư vấn AI 4 giờ",
            "timestamp": now_ts,
            "last_user_interaction_ts": now_ts - 200,
            "requested_services": ["tu_van_ai"],
            "estimated_hours": 4,
            "connector": "zalo_oa",
            "require_consent": True,
            "tenant_id": "tenant_e2e_a",
        }
        dup_raw = json.dumps(dup_body).encode("utf-8")
        dup_mac = _sign_zalo("app1", dup_raw, now_ts)
        r_d1 = client.post("/v1/opc/pilot-a/webhook/zalo", content=dup_raw, headers={"Content-Type": "application/json", "X-ZEvent-Mac": dup_mac})
        r_d2 = client.post("/v1/opc/pilot-a/webhook/zalo", content=dup_raw, headers={"Content-Type": "application/json", "X-ZEvent-Mac": dup_mac})
        assert r_d1.status_code == 200 and r_d2.status_code == 200
        # Quota guard deduplicates same event_id so duplicate webhook does not double-burn monthly quota
        with sqlite3.connect(t_a.db_path) as conn:
            q_cnt = conn.execute("SELECT COUNT(*) FROM opc_workflow_quota_reservations WHERE workflow_id = 'evt_dup_001'").fetchone()[0]
        assert q_cnt == 1

        run_a = r_d1.json()["run_id"]
        dig_a = r_d1.json()["action_digest"]

        # Out-of-order VietQR settlement BEFORE approval or with wrong amount/signature -> (9) Invalid/missing payment evidence
        assert client.post(
            f"/v1/opc/pilot-a/webhook/vietqr?run_id={run_a}&tenant_id=tenant_e2e_a",
            content=b'{"bank_tx_id":"TX-BADSIG","amount_vnd":2400000,"memo":"OPC ' + run_a.encode() + b'"}',
            headers={"Content-Type": "application/json", "X-VietQR-Signature": "deadbeef"},
        ).status_code == 403
        bad_amt_raw = json.dumps({"bank_tx_id": "TX-UNDER", "amount_vnd": 1_000_000, "memo": f"OPC {run_a}"}).encode("utf-8")
        assert client.post(
            f"/v1/opc/pilot-a/webhook/vietqr?run_id={run_a}&tenant_id=tenant_e2e_a",
            content=bad_amt_raw,
            headers={"Content-Type": "application/json", "X-VietQR-Signature": _sign_vietqr(bad_amt_raw)},
        ).status_code == 403
        # Draft export before verified payment records bank_tx_id="" (unsettled draft only)
        pre_exp = json.loads(client.get(f"/v1/opc/pilot-a/draft-export/{run_a}?fmt=json&tenant_id=tenant_e2e_a", headers=hdr_a).text)
        assert pre_exp["rows"][0]["MaGiaoDichVietQR"] == ""

        # (4) Price modification after approval (TOCTOU digest mismatch + DB tamper test)
        assert client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": run_a, "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": "f" * 64},
            headers=hdr_a,
        ).status_code == 409
        with sqlite3.connect(t_a.db_path) as conn:
            orig_payload_json = conn.execute("SELECT action_payload_json FROM opc_runs WHERE run_id = ?", (run_a,)).fetchone()[0]
            mutated = json.loads(orig_payload_json)
            mutated["parameters"]["amount_vnd"] = 99_000_000
            conn.execute("UPDATE opc_runs SET action_payload_json = ? WHERE run_id = ?", (json.dumps(mutated), run_a))
            conn.commit()
        # Owner tries to approve with original digest after DB price mutation -> 409 TOCTOU blocked!
        assert client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": run_a, "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": dig_a},
            headers=hdr_a,
        ).status_code == 409
        assert len(dispatches) == 0
        # Restore original payload for subsequent concurrency test
        with sqlite3.connect(t_a.db_path) as conn:
            conn.execute("UPDATE opc_runs SET action_payload_json = ? WHERE run_id = ?", (orig_payload_json, run_a))
            conn.commit()

        # (8) Multi-tenant isolation: Tenant B cannot read, card-view, approve, settle, or export Tenant A's run
        assert client.get(f"/v1/opc/pilot-a/runs/{run_a}?tenant_id=tenant_e2e_a", headers=hdr_b).status_code == 401
        assert client.get(f"/v1/opc/pilot-a/runs/{run_a}?tenant_id=tenant_e2e_b", headers=hdr_b).status_code == 404
        assert client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": run_a, "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": dig_a},
            headers=hdr_b,
        ).status_code == 401
        assert client.get(f"/v1/opc/pilot-a/draft-export/{run_a}?fmt=csv&tenant_id=tenant_e2e_a", headers=hdr_b).status_code == 401

        # (6) Concurrent 6-thread approval race -> exactly 1 Zalo message dispatched!
        def _concurrent_decide(_i: int) -> int:
            with TestClient(app) as local_c:
                r = local_c.post(
                    "/v1/opc/pilot-a/decide",
                    json={"run_id": run_a, "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": dig_a},
                    headers=hdr_a,
                )
                return r.status_code

        with ThreadPoolExecutor(max_workers=6) as pool:
            codes = list(pool.map(_concurrent_decide, range(6)))
        assert 200 in codes and all(c in (200, 409) for c in codes)
        assert len(dispatches) == 1  # Strictly 1 external dispatch across 6 concurrent threads!

        # (7) Database restart & recovery: fresh SQLite connections / fresh workflow instance preserve COMPLETED + dedup
        r_after_restart = client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": run_a, "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": dig_a},
            headers=hdr_a,
        )
        assert r_after_restart.status_code == 200 and r_after_restart.json()["side_effect_deduplicated"] is True
        assert len(dispatches) == 1

        # (3) Expired approval token -> rejected with 0 dispatches
        r_exp_in = client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_exp_tok",
                "sender_id": "84911000111",
                "sender_name": "Khách Hết Hạn",
                "message_text": "Tư vấn AI 2 giờ",
                "timestamp": now_ts,
                "last_user_interaction_ts": now_ts - 60,
                "requested_services": ["tu_van_ai"],
                "estimated_hours": 2,
                "tenant_id": "tenant_e2e_a",
            },
            headers=hdr_a,
        ).json()
        # Advance clock past 24h payload/token expiry (86400s) while testing expiry guard:
        # Note 48h Zalo window is 172800s, whereas payload expires_at is +86400s (24h)!
        with patch("src.api.pilot_a_routes.time.time", return_value=now_ts + 90_000):
            r_exp_dec = client.post(
                "/v1/opc/pilot-a/decide",
                json={"run_id": r_exp_in["run_id"], "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": r_exp_in["action_digest"]},
                headers=hdr_a,
            )
            assert r_exp_dec.status_code == 409 and len(dispatches) == 1

        # (11) Zalo 48-hour interaction-window policy violation -> HTTP 403 at intake AND at delayed decide
        assert client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_49h_old",
                "sender_id": "84911000111",
                "sender_name": "Khách Quá 48h",
                "message_text": "Tư vấn AI 2 giờ",
                "timestamp": now_ts,
                "last_user_interaction_ts": now_ts - (49 * 3600),
                "tenant_id": "tenant_e2e_a",
            },
            headers=hdr_a,
        ).status_code == 403
        with patch("src.api.pilot_a_routes.time.time", return_value=now_ts + (49 * 3600)):
            assert client.post(
                "/v1/opc/pilot-a/decide",
                json={"run_id": r_exp_in["run_id"], "tenant_id": "tenant_e2e_a", "decision": "approve", "action_digest": r_exp_in["action_digest"]},
                headers=hdr_a,
            ).status_code == 403

        # (10) Privacy consent required, withdrawal & <72h DSAR deletion across OPC + Checkpoint + VietQR DBs
        assert client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_no_consent",
                "sender_id": "84999888777",
                "sender_name": "Khách Chưa Đồng Ý",
                "message_text": "Tư vấn AI 2 giờ",
                "tenant_id": "tenant_e2e_a",
                "require_consent": True,
            },
            headers=hdr_a,
        ).status_code == 403
        wf_dsar = PilotAWorkflow(db_path=Path(t_a.db_path), profile=_bench_profile())
        wf_dsar.privacy_guard.withdraw_subject_consent("84911000111")
        assert wf_dsar.privacy_guard.has_active_consent("84911000111") is False
        dsar_out = wf_dsar.privacy_guard.erase_subject_under_72h("84911000111")
        assert dsar_out["statutory_deadline"]["deadline_days"] <= 3 and dsar_out["total_erased_combined"] >= 1
        assert dsar_out["status"] == "COMPLETED"

    # (12) AI hallucinated prices and tax calculations -> deterministic verifier halts for human
    with pytest.raises(HaltForHumanError) as exc_halluc:
        verify_confidence_and_math(
            [{"service": "tu_van_ai", "hours": 5, "rate": "600000", "subtotal": "9999999"}],
            declared_total="9999999",
            confidence=0.99,
            tax_rate=Decimal("0"),
        )
    assert exc_halluc.value.code == "MATH_MISMATCH_REQUIRES_HUMAN"
    with pytest.raises(HaltForHumanError):
        verify_confidence_and_math(
            [{"service": "tu_van_ai", "hours": 5, "rate": "600000", "subtotal": "3000000"}],
            declared_total="3000000",
            confidence=0.99,
            tax_rate=Decimal("-0.08"),
        )

    # (13) LLM timeout, unavailable provider, budget exhaustion & unknown cost events
    wf_rt = PilotAWorkflow(
        db_path=tmp_path / "router_faults.db",
        profile=_bench_profile(),
    )
    router_timeout = SelectiveRouter(
        wf_rt.usage,
        wf_rt.profile.services,
        local_endpoint="http://127.0.0.1:9/v1/chat/completions",
        local_transport=lambda *_a: (_ for _ in ()).throw(TimeoutError("local MLX timeout")),
        cloud_fallback_fn=None,
    )
    rt_halt = router_timeout.route("Câu hỏi mơ hồ không có dịch vụ hay giờ", run_id="run_llm_timeout")
    assert rt_halt.mode == "low_confidence_halt"

    router_unk = SelectiveRouter(
        wf_rt.usage,
        wf_rt.profile.services,
        local_endpoint="http://local-mlx/v1/chat/completions",
        local_transport=lambda *_a: (200, json.dumps({"confidence": 0.92, "extracted": {"requested_services": ["tu_van_ai"], "estimated_hours": 3}, "usage": {"total_tokens": 320}}).encode("utf-8")),
    )
    rt_unk_res = router_unk.route("Nhờ tư vấn riêng", run_id="run_unk_cost")
    assert rt_unk_res.unknown_cost is True
    agg_unk = wf_rt.usage.aggregate_run_costs("run_unk_cost")
    assert agg_unk["has_unknown_costs"] is True and "VND" not in agg_unk["known_amounts"]

    # Pre-execution budget ceiling blocks cloud fallback silently-never (raises PermissionError fail-closed)
    wf_rt.usage.record_usage(UsageRecord("u_full", "run_cap", 1, UsageStage.ACTUAL, "cloud", "m1", 100, "0", "100.00", "VND", "owner", "cap", now_ts))
    router_capped = SelectiveRouter(
        wf_rt.usage,
        wf_rt.profile.services,
        local_endpoint="",
        estimated_call_budget="50.00",
        hard_budget_limit="120.00",
        cloud_fallback_fn=lambda *_a: {"confidence": 0.95},
    )
    with pytest.raises(PermissionError, match="Budget reservation failed"):
        router_capped.route("Mơ hồ cần gọi cloud", run_id="run_cap")

    # (14) Absent encryption/approval secrets outside pytest -> fail closed with exit/error and 0 side effects
    sub_no_secret = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os\n"
                "os.environ.pop('PYTEST_CURRENT_TEST', None)\n"
                "os.environ.pop('MEKONG_APPROVAL_SECRET', None)\n"
                "from src.opc.approval import PayloadBoundApprovalEngine\n"
                "try:\n"
                "    PayloadBoundApprovalEngine()\n"
                "    raise SystemExit(2)\n"
                "except Exception as e:\n"
                "    assert 'MEKONG_APPROVAL_SECRET' in str(e)\n"
                "    raise SystemExit(0)\n"
            ),
        ],
        cwd=REPO_ROOT,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert sub_no_secret.returncode == 0


def test_sc08_mekong_bench_all_15_layers_and_latency_benchmark(tmp_path: Path) -> None:
    """Execute all 15 MEKONG-BENCH layers (0 missing layers) and record synthetic latency metrics."""
    runner = MekongBenchRunner()
    t0 = time.perf_counter()
    suite = runner.run_all(tmp_path / "bench15")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert suite.total_count == 15
    assert suite.passed_count == 15
    assert suite.pass_rate == 1.0
    layer_ids = [layer.layer_id for layer in suite.layers]
    assert layer_ids == [f"L{i}" for i in range(1, 16)]
    assert elapsed_ms < 10_000.0
