"""Supreme Command #08 Adversarial Multi-Tenant Isolation, Auth, Sandbox Gate & Card Leakage Suite."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.api.pilot_a_card_view import render_mobile_approval_card_html
from src.gateway import app
from src.opc.tenant_provisioner import ProvisionedTenantResult, provision_isolated_tenant

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def tenant_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sc08_tenants"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture()
def sc08_client(tenant_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(tenant_dir))
    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", "sc08-pilot-a-approval-secret-2026-prod")
    monkeypatch.setenv("VIETQR_WEBHOOK_SECRET", "sc08-vietqr-hmac-secret-2026-prod")
    monkeypatch.setenv("ZALO_OA_SECRET_KEY", "sc08-zalo-oa-mac-secret-2026-prod")
    monkeypatch.setenv("MEKONG_ENV", "development")
    monkeypatch.delenv("MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK", raising=False)
    monkeypatch.delenv("MEKONG_PUBLIC_GATEWAY", raising=False)
    return TestClient(app)


def _provision_pair(tenant_dir: Path) -> tuple[ProvisionedTenantResult, ProvisionedTenantResult]:
    alpha = provision_isolated_tenant(
        tenant_dir, "tenant_alpha", "CTY TNHH ALPHA MEKONG", "Nguyễn Văn Alpha",
        sme_tier="pilot_a", bank_id="VCB", account_no="1111222233",
    )
    bravo = provision_isolated_tenant(
        tenant_dir, "tenant_bravo", "CTY TNHH BRAVO CỬU LONG", "Trần Thị Bravo",
        sme_tier="pilot_a", bank_id="ACB", account_no="8888999900",
    )
    return alpha, bravo


def _create_run(client: TestClient, tenant_id: str, api_key: str, event_id: str, hours: int = 10) -> dict[str, object]:
    resp = client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={
            "event_id": event_id,
            "oa_id": f"oa_{tenant_id}",
            "sender_id": "84909111222",
            "sender_name": f"Khách Hàng {tenant_id}",
            "message_text": f"Nhờ shop báo giá tư vấn AI và tích hợp VietQR {hours} giờ.",
            "requested_services": ["tu_van_ai", "tich_hop_vietqr"],
            "estimated_hours": hours,
            "project_title": f"Dự án riêng {tenant_id}",
            "tenant_id": tenant_id,
        },
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


def test_cross_tenant_api_key_and_card_sig_isolation(sc08_client: TestClient, tenant_dir: Path) -> None:
    """Controls 1 & 2: Tenant Alpha API key, Bearer token, and card_sig cannot access or mutate Tenant Bravo."""
    alpha, bravo = _provision_pair(tenant_dir)
    alpha_run = _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_alpha_1")
    bravo_run = _create_run(sc08_client, "tenant_bravo", bravo.tenant_api_key, "evt_bravo_1")

    a_run_id = str(alpha_run["run_id"])
    a_sig = str(alpha_run["card_sig"])
    b_run_id = str(bravo_run["run_id"])
    b_digest = str(bravo_run["action_digest"])

    for alpha_hdr in (
        {"X-API-Key": alpha.tenant_api_key},
        {"Authorization": f"Bearer {alpha.tenant_api_key}"},
    ):
        # Alpha key against Bravo run, card, decide, draft-export, and webhook must return 401 with zero Bravo leakage
        r_runs = sc08_client.get(f"/v1/opc/pilot-a/runs/{b_run_id}?tenant_id=tenant_bravo", headers=alpha_hdr)
        assert r_runs.status_code == 401 and "BRAVO" not in r_runs.text and b_digest not in r_runs.text

        r_nonexist = sc08_client.get("/v1/opc/pilot-a/runs/run_does_not_exist?tenant_id=tenant_bravo", headers=alpha_hdr)
        assert r_nonexist.status_code == 401

        r_card = sc08_client.get(f"/v1/opc/pilot-a/card/{b_run_id}?tenant_id=tenant_bravo", headers=alpha_hdr)
        assert r_card.status_code == 401 and "BRAVO" not in r_card.text

        r_dec = sc08_client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": b_run_id, "tenant_id": "tenant_bravo", "decision": "approve", "action_digest": b_digest},
            headers=alpha_hdr,
        )
        assert r_dec.status_code == 401

        r_exp = sc08_client.get(f"/v1/opc/pilot-a/draft-export/{b_run_id}?fmt=json&tenant_id=tenant_bravo", headers=alpha_hdr)
        assert r_exp.status_code == 401 and "BRAVO" not in r_exp.text

        r_wh = sc08_client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_cross_key",
                "sender_id": "84909000111",
                "sender_name": "Cross Tenant Probe",
                "message_text": "Báo giá 2 giờ",
                "tenant_id": "tenant_bravo",
            },
            headers=alpha_hdr,
        )
        assert r_wh.status_code == 401

    # Alpha's card_sig cannot read, approve, or export on Tenant Bravo (401 on Bravo run, 404 on Alpha run_id)
    assert sc08_client.get(f"/v1/opc/pilot-a/runs/{b_run_id}?tenant_id=tenant_bravo&sig={a_sig}").status_code == 401
    assert sc08_client.get(f"/v1/opc/pilot-a/runs/{a_run_id}?tenant_id=tenant_bravo&sig={a_sig}").status_code == 404
    assert sc08_client.get(f"/v1/opc/pilot-a/card/{b_run_id}?tenant_id=tenant_bravo", headers={"X-Card-Sig": a_sig}).status_code == 401
    assert sc08_client.get(f"/v1/opc/pilot-a/draft-export/{b_run_id}?fmt=csv&tenant_id=tenant_bravo", headers={"X-Card-Sig": a_sig}).status_code == 401
    assert sc08_client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": b_run_id, "tenant_id": "tenant_bravo", "decision": "approve", "action_digest": b_digest, "card_sig": a_sig},
    ).status_code == 401

    # Verify Bravo's run was never mutated
    b_check = sc08_client.get(
        f"/v1/opc/pilot-a/runs/{b_run_id}?tenant_id=tenant_bravo",
        headers={"X-API-Key": bravo.tenant_api_key},
    )
    assert b_check.status_code == 200 and b_check.json()["status"] == "pending_approval"


def test_quota_exhaustion_isolation_and_sme_tier_escalation_blocked(
    sc08_client: TestClient, tenant_dir: Path
) -> None:
    """Control 3: Exhausting Tenant Alpha quota never impacts Tenant Bravo and cannot be reset via sme_tier."""
    alpha, bravo = _provision_pair(tenant_dir)
    # Tighten Tenant Alpha's provisioned monthly quota to 1 in its isolated config
    alpha_cfg_path = Path(alpha.config_path)
    cfg_data = json.loads(alpha_cfg_path.read_text(encoding="utf-8"))
    cfg_data["monthly_workflow_quota"] = 1
    cfg_data["sme_tier"] = "starter"
    alpha_cfg_path.write_text(json.dumps(cfg_data), encoding="utf-8")

    # 1st workflow on Alpha succeeds
    _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_q_alpha_1")

    # 2nd workflow on Alpha fails 429, even when Alpha attempts to escalate sme_tier="agency"
    r_over = sc08_client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={
            "event_id": "evt_q_alpha_2",
            "sender_id": "84909111222",
            "sender_name": "Alpha Over Quota",
            "message_text": "Báo giá thêm gói tư vấn AI 5 giờ.",
            "tenant_id": "tenant_alpha",
            "sme_tier": "agency",
        },
        headers={"X-API-Key": alpha.tenant_api_key},
    )
    assert r_over.status_code == 429 and r_over.json()["detail"]["error"] == "workflow_quota_exceeded"

    # Unauthenticated caller attempting sme_tier override is forbidden (403)
    r_unauth_tier = sc08_client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={
            "event_id": "evt_q_alpha_3",
            "sender_id": "84909111222",
            "sender_name": "Attacker Tier Override",
            "message_text": "Báo giá tư vấn AI.",
            "tenant_id": "tenant_alpha",
            "sme_tier": "agency",
        },
    )
    assert r_unauth_tier.status_code == 403
    assert r_unauth_tier.json()["detail"]["error"] == "privileged_webhook_fields_forbidden"

    # Tenant Bravo quota remains completely unaffected
    bravo_ok = _create_run(sc08_client, "tenant_bravo", bravo.tenant_api_key, "evt_q_bravo_1")
    assert bravo_ok["status"] == "INTERRUPT_AUTHORIZE"


def test_vietqr_cross_tenant_and_cross_order_bank_tx_replay_blocked(
    sc08_client: TestClient, tenant_dir: Path
) -> None:
    """Control 4: VietQR webhook cannot cross-settle another tenant or settle two runs with one bank_tx_id."""
    alpha, bravo = _provision_pair(tenant_dir)
    a_run1 = _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_vqr_a1", hours=10)
    a_run2 = _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_vqr_a2", hours=10)
    b_run1 = _create_run(sc08_client, "tenant_bravo", bravo.tenant_api_key, "evt_vqr_b1", hours=10)

    a_id1, a_id2, b_id1 = str(a_run1["run_id"]), str(a_run2["run_id"]), str(b_run1["run_id"])
    secret = b"sc08-vietqr-hmac-secret-2026-prod"

    def _sign_vqr(payload_obj: dict[str, object]) -> tuple[bytes, dict[str, str]]:
        raw = json.dumps(payload_obj).encode("utf-8")
        sig = hmac.new(secret, raw, hashlib.sha256).hexdigest()
        return raw, {"Content-Type": "application/json", "X-VietQR-Signature": sig}

    raw_a1, hdr_a1 = _sign_vqr({"bank_tx_id": "NAPAS-SC08-001", "amount_vnd": 5_400_000, "memo": f"Thanh toan OPC {a_id1}"})

    # Replaying Alpha's run_id against Tenant Bravo fails 404; replaying Alpha's memo against Bravo's run_id fails 403
    assert sc08_client.post(f"/v1/opc/pilot-a/webhook/vietqr?run_id={a_id1}&tenant_id=tenant_bravo", content=raw_a1, headers=hdr_a1).status_code == 404
    assert sc08_client.post(f"/v1/opc/pilot-a/webhook/vietqr?run_id={b_id1}&tenant_id=tenant_bravo", content=raw_a1, headers=hdr_a1).status_code == 403

    # Unprovisioned tenant on /webhook/vietqr fails closed (403) without creating SQLite files
    assert sc08_client.post(f"/v1/opc/pilot-a/webhook/vietqr?run_id={a_id1}&tenant_id=unprov_vqr", content=raw_a1, headers=hdr_a1).status_code == 403
    assert not (tenant_dir / "unprov_vqr.db").exists()

    # Legitimate settlement on Alpha run 1 succeeds
    ok1 = sc08_client.post(f"/v1/opc/pilot-a/webhook/vietqr?run_id={a_id1}&tenant_id=tenant_alpha", content=raw_a1, headers=hdr_a1)
    assert ok1.status_code == 200 and ok1.json()["reconciliation"]["bank_tx_id"] == "NAPAS-SC08-001"

    # Reusing the same bank_tx_id to settle Alpha run 2 fails closed (403)
    raw_a2, hdr_a2 = _sign_vqr({"bank_tx_id": "NAPAS-SC08-001", "amount_vnd": 5_400_000, "memo": f"Thanh toan OPC {a_id2}"})
    replay_a2 = sc08_client.post(f"/v1/opc/pilot-a/webhook/vietqr?run_id={a_id2}&tenant_id=tenant_alpha", content=raw_a2, headers=hdr_a2)
    assert replay_a2.status_code == 403 and "replay blocked" in replay_a2.json()["detail"]["message"]


def test_dev_sandbox_webhook_opt_in_gate_and_privileged_fields_forbidden(
    sc08_client: TestClient, tenant_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control 5: Unauthenticated Zalo webhook fails 401 by default; sandbox flag never works in prod/public or with consent/rates."""
    monkeypatch.delenv("ZALO_OA_SECRET_KEY", raising=False)
    monkeypatch.setenv("MEKONG_ENV", "development")

    base_payload = {
        "event_id": "evt_sbx_1",
        "sender_id": "84909777888",
        "sender_name": "Khách Dev Sandbox",
        "message_text": "Báo giá tư vấn AI 4 giờ.",
        "tenant_id": "dev_sbx_tenant",
        "connector": "zalo_oa_sandbox",
    }

    # Without MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK=1 -> rejected 401 even in development with ZALO_OA_SECRET_KEY unset
    r_default_closed = sc08_client.post("/v1/opc/pilot-a/webhook/zalo", json=base_payload)
    assert r_default_closed.status_code == 401
    assert r_default_closed.json()["detail"]["error"] == "missing_zalo_webhook_secret"
    assert not (tenant_dir / "dev_sbx_tenant.db").exists()

    # Enable explicit local dev sandbox flag
    monkeypatch.setenv("MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK", "1")

    # Even in dev sandbox, unauthenticated grant_consent and service_rates_vnd MUST fail 403
    assert sc08_client.post("/v1/opc/pilot-a/webhook/zalo", json={**base_payload, "grant_consent": True}).status_code == 403
    assert sc08_client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={**base_payload, "service_rates_vnd": {"tu_van_ai": 1}},
    ).status_code == 403

    # Clean dev sandbox payload succeeds in local development and never leaks card_sig
    r_sbx_ok = sc08_client.post("/v1/opc/pilot-a/webhook/zalo", json=base_payload)
    assert r_sbx_ok.status_code == 200
    assert "card_sig" not in r_sbx_ok.json() and "sig=" not in r_sbx_ok.json()["card_url"]

    # Even with MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK=1, public/staging/production environments reject 401
    for env_override in ("production", "staging", "public"):
        monkeypatch.setenv("MEKONG_ENV", env_override)
        r_prod = sc08_client.post("/v1/opc/pilot-a/webhook/zalo", json={**base_payload, "tenant_id": f"sbx_{env_override}", "event_id": f"e_{env_override}"})
        assert r_prod.status_code == 401
        assert not (tenant_dir / f"sbx_{env_override}.db").exists()

    monkeypatch.setenv("MEKONG_ENV", "development")
    monkeypatch.setenv("MEKONG_PUBLIC_GATEWAY", "1")
    r_pub_gw = sc08_client.post("/v1/opc/pilot-a/webhook/zalo", json={**base_payload, "tenant_id": "sbx_pub_gw", "event_id": "e_pub_gw"})
    assert r_pub_gw.status_code == 401
    assert not (tenant_dir / "sbx_pub_gw.db").exists()

    # Stale MAC (> 300s old) is rejected 401 before touching tenant DBs; fresh MAC against unprovisioned tenant fails 403
    monkeypatch.delenv("MEKONG_PUBLIC_GATEWAY", raising=False)
    monkeypatch.delenv("MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK", raising=False)
    monkeypatch.setenv("ZALO_OA_SECRET_KEY", "sc08-zalo-oa-mac-secret-2026-prod")
    stale_ts = int(time.time()) - 900
    raw_stale = json.dumps({
        "event_id": "evt_mac_stale",
        "sender_id": "84909777888",
        "sender_name": "Stale MAC",
        "message_text": "Báo giá tư vấn AI 2 giờ.",
        "timestamp": stale_ts,
        "last_user_interaction_ts": stale_ts - 100,
        "app_id": "app_sc08",
        "tenant_id": "unprov_mac_tenant",
    }).encode("utf-8")
    stale_mac = hashlib.sha256(
        b"app_sc08" + raw_stale + str(stale_ts).encode("utf-8") + b"sc08-zalo-oa-mac-secret-2026-prod"
    ).hexdigest()
    assert (
        sc08_client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            content=raw_stale,
            headers={"Content-Type": "application/json", "X-ZEvent-Mac": stale_mac},
        ).status_code
        == 401
    )

    fresh_ts = int(time.time())
    raw_unprov = json.dumps({
        "event_id": "evt_mac_unprov",
        "sender_id": "84909777888",
        "sender_name": "Unprovisioned MAC",
        "message_text": "Báo giá tư vấn AI 2 giờ.",
        "timestamp": fresh_ts,
        "last_user_interaction_ts": fresh_ts - 100,
        "app_id": "app_sc08",
        "tenant_id": "unprov_mac_tenant",
    }).encode("utf-8")
    mac = hashlib.sha256(
        b"app_sc08" + raw_unprov + str(fresh_ts).encode("utf-8") + b"sc08-zalo-oa-mac-secret-2026-prod"
    ).hexdigest()
    r_unprov_mac = sc08_client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        content=raw_unprov,
        headers={"Content-Type": "application/json", "X-ZEvent-Mac": mac},
    )
    assert r_unprov_mac.status_code == 403 and not (tenant_dir / "unprov_mac_tenant.db").exists()


def test_signed_card_url_leakage_headers_csp_history_scrub_and_x_card_sig(
    sc08_client: TestClient, tenant_dir: Path
) -> None:
    """Control 6: Verify no-store, Referrer-Policy, strict CSP, history.replaceState, X-Card-Sig header, and <15KB size."""
    alpha, _ = _provision_pair(tenant_dir)
    created = _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_card_sec_1")
    run_id = str(created["run_id"])
    digest = str(created["action_digest"])
    card_sig = str(created["card_sig"])

    # Verify card HTML via X-Card-Sig header (without ?sig= in URL)
    r_card = sc08_client.get(f"/v1/opc/pilot-a/card/{run_id}?tenant_id=tenant_alpha", headers={"X-Card-Sig": card_sig})
    assert r_card.status_code == 200
    assert len(r_card.text.encode("utf-8")) < 15_000
    assert r_card.headers["cache-control"] == "no-store, no-cache, must-revalidate, private"
    assert r_card.headers["pragma"] == "no-cache"
    assert r_card.headers["referrer-policy"] == "no-referrer"
    assert r_card.headers["x-content-type-options"] == "nosniff"
    assert r_card.headers["content-security-policy"] == (
        "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    )
    assert "<meta name='referrer' content='no-referrer'>" in r_card.text
    assert "u.searchParams.delete('sig')" in r_card.text and "window.history.replaceState" in r_card.text
    assert "'X-Card-Sig':CFG.sig" in r_card.text and "dlDraft('csv')" in r_card.text
    # Ensure no anchor href leaks ?sig= or &sig=
    assert "&amp;sig=" not in r_card.text and "?sig=" not in r_card.text

    # Forged X-Card-Sig header is rejected even if a valid ?sig= query parameter is present
    r_forged_hdr = sc08_client.get(
        f"/v1/opc/pilot-a/card/{run_id}?tenant_id=tenant_alpha&sig={card_sig}",
        headers={"X-Card-Sig": "0" * 64},
    )
    assert r_forged_hdr.status_code == 401

    # Authenticated X-API-Key calls with untrusted ?sig=spoofed_attacker_sig NEVER echo spoofed sig in card_url or HTML
    r_run_spoof = sc08_client.get(
        f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_alpha&sig=spoofed_attacker_sig",
        headers={"X-API-Key": alpha.tenant_api_key},
    )
    assert r_run_spoof.status_code == 200 and "spoofed_attacker_sig" not in r_run_spoof.text
    assert f"sig={card_sig}" in r_run_spoof.json()["card_url"]
    r_card_spoof = sc08_client.get(
        f"/v1/opc/pilot-a/card/{run_id}?tenant_id=tenant_alpha&sig=spoofed_attacker_sig",
        headers={"X-API-Key": alpha.tenant_api_key},
    )
    assert r_card_spoof.status_code == 200 and "spoofed_attacker_sig" not in r_card_spoof.text

    # Verify /runs, /draft-export, and /decide all accept X-Card-Sig header and return no-store/no-referrer headers
    r_run = sc08_client.get(f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_alpha", headers={"X-Card-Sig": card_sig})
    assert r_run.status_code == 200 and r_run.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in r_run.headers["cache-control"]

    r_exp = sc08_client.get(f"/v1/opc/pilot-a/draft-export/{run_id}?fmt=csv&tenant_id=tenant_alpha", headers={"X-Card-Sig": card_sig})
    assert r_exp.status_code == 200 and r_exp.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in r_exp.headers["cache-control"]

    r_dec = sc08_client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": run_id, "tenant_id": "tenant_alpha", "decision": "approve", "action_digest": digest},
        headers={"X-Card-Sig": card_sig},
    )
    assert r_dec.status_code == 200 and r_dec.json()["status"] == "completed"
    assert r_dec.headers["referrer-policy"] == "no-referrer" and "no-store" in r_dec.headers["cache-control"]

    # Worst-case UTF-8 Vietnamese payload stays strictly < 15,000 bytes
    worst_html = render_mobile_approval_card_html(
        run_id="run_" + "x" * 60,
        status="pending_approval",
        client_name="Công ty Cổ phần Xuất Nhập Khẩu Nông Sản Đồng Bằng Sông Cửu Long " * 3,
        project_title="Triển khai hệ thống tự động hóa báo giá Zalo OA & đối soát VietQR toàn diện " * 3,
        customer_notes="Khách yêu cầu tư vấn chi tiết tích hợp đa chi nhánh tại Cần Thơ, Đồng Tháp, An Giang. " * 10,
        line_items=[
            {"service": f"Hạng mục dịch vụ chuyên sâu số {i}", "hours": 12, "rate": 1_250_000, "subtotal": 15_000_000}
            for i in range(16)
        ],
        citations=[
            {"field_name": f"requested_service_{i}", "source_quote": "Trích dẫn nguyên văn yêu cầu báo giá của khách hàng từ Zalo OA", "start_char": 0, "end_char": 62}
            for i in range(6)
        ],
        total_amount_vnd=240_000_000,
        action_digest="f" * 64,
        vietqr_memo="OPC run_worst_case_check",
        window_remaining_hours=47.5,
        tenant_id="tenant_alpha",
        card_sig="a" * 64,
    )
    assert len(worst_html.encode("utf-8")) < 15_000


def test_ghost_unprovisioned_tenant_probes_never_create_sqlite_files(
    sc08_client: TestClient, tenant_dir: Path
) -> None:
    """Control 7: Probing /runs, /card, /decide, /draft-export, or /webhook/vietqr for ghost tenant creates 0 files."""
    ghost = "ghost_unprovisioned"
    assert sc08_client.get(f"/v1/opc/pilot-a/runs/nonexistent?tenant_id={ghost}").status_code == 401
    assert sc08_client.get(f"/v1/opc/pilot-a/runs/nonexistent?tenant_id={ghost}&sig={'a' * 64}").status_code == 404
    assert sc08_client.get(f"/v1/opc/pilot-a/card/nonexistent?tenant_id={ghost}&sig={'a' * 64}").status_code == 404
    assert sc08_client.get(f"/v1/opc/pilot-a/draft-export/nonexistent?tenant_id={ghost}&sig={'a' * 64}").status_code == 404
    assert sc08_client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": "nonexistent", "tenant_id": ghost, "decision": "approve", "action_digest": "b" * 64, "card_sig": "a" * 64},
    ).status_code == 404
    assert sc08_client.post(
        f"/v1/opc/pilot-a/webhook/vietqr?run_id=nonexistent&tenant_id={ghost}",
        content=b"{}",
        headers={"Content-Type": "application/json", "X-VietQR-Signature": "c" * 64},
    ).status_code == 403

    created_files = list(tenant_dir.glob(f"{ghost}*"))
    assert created_files == [], f"Unexpected ghost tenant files created: {created_files}"


def test_missing_approval_secret_outside_pytest_fails_closed_zero_side_effects(
    sc08_client: TestClient, tenant_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control 8: Missing MEKONG_APPROVAL_SECRET outside pytest fails closed (503) with zero external side effects."""
    alpha, _ = _provision_pair(tenant_dir)
    created = _create_run(sc08_client, "tenant_alpha", alpha.tenant_api_key, "evt_pre_secret_drop")
    run_id = str(created["run_id"])
    digest = str(created["action_digest"])

    # Simulate runtime outside pytest with MEKONG_APPROVAL_SECRET missing
    monkeypatch.delenv("MEKONG_APPROVAL_SECRET", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    with patch("src.opc.connectors.zalo_http._stdlib_http_post") as mock_http:
        r_wh = sc08_client.post(
            "/v1/opc/pilot-a/webhook/zalo",
            json={
                "event_id": "evt_no_secret",
                "sender_id": "84909111222",
                "sender_name": "No Secret Caller",
                "message_text": "Báo giá tư vấn AI 2 giờ.",
                "tenant_id": "tenant_alpha",
            },
            headers={"X-API-Key": alpha.tenant_api_key},
        )
        assert r_wh.status_code == 503

        r_run = sc08_client.get(
            f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_alpha",
            headers={"X-API-Key": alpha.tenant_api_key},
        )
        assert r_run.status_code == 503

        r_card = sc08_client.get(
            f"/v1/opc/pilot-a/card/{run_id}?tenant_id=tenant_alpha",
            headers={"X-API-Key": alpha.tenant_api_key},
        )
        assert r_card.status_code == 503

        r_dec = sc08_client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": run_id, "tenant_id": "tenant_alpha", "decision": "approve", "action_digest": digest},
            headers={"X-API-Key": alpha.tenant_api_key},
        )
        assert r_dec.status_code == 503
        assert mock_http.call_count == 0

    # Also verify in an isolated non-pytest Python subprocess
    sub_code = (
        "from fastapi.testclient import TestClient\n"
        "from src.gateway import app\n"
        "c = TestClient(app)\n"
        f"r = c.get('/v1/opc/pilot-a/runs/{run_id}?tenant_id=tenant_alpha', headers={{'X-API-Key': {alpha.tenant_api_key!r}}})\n"
        "assert r.status_code == 503, r.status_code\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", sub_code],
        cwd=REPO_ROOT,
        env={
            "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
            "PYTHONPATH": str(REPO_ROOT),
            "MEKONG_PILOT_A_DB_DIR": str(tenant_dir),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
