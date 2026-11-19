"""Regression & rehearsal tests for SC11 PR-C runtime hardening (RT-01 through RT-06)."""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src.api.pilot_a_routes import _pilot_base_dir
from src.core.ops_engine import OpsEngine
from src.gateway import app
from src.opc.dr_backup import (
    PilotAKillSwitchError,
    backup_tenant_directory,
    restore_tenant_directory,
)
from src.opc.models import BusinessProfile
from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent
from src.opc.tenant_provisioner import provision_isolated_tenant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SECRET = "sc11_pr_c_secret_key_for_testing_32b"
_VIETQR_SECRET = "sc11_pr_c_vietqr_secret_for_testing"


def _profile() -> BusinessProfile:
    return BusinessProfile(
        business_name="Mekong Agency",
        owner_name="Lan Anh",
        locale="vi-VN",
        timezone="Asia/Ho_Chi_Minh",
        currency="VND",
        language="vi",
        services={"tu_van_ai": Decimal("1000000")},
        payment_terms="50% deposit",
    )


def test_rt01_to_rt04_docker_compose_and_dockerfile_hardening(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RT-01..RT-04: loopback bind, persistent /data tenant DB dir, engine/ copied, and MEKONG_ENV=production."""
    compose = yaml.safe_load((_REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    # RT-01: Neither mekong-ide nor raas may expose bare 0.0.0.0 ports
    for svc_name, port in (("mekong-ide", "3000:3000"), ("raas", "8000:8000")):
        ports = [str(p) for p in services[svc_name]["ports"]]
        assert port not in ports, f"{svc_name} exposes unrestricted port {port}"
        assert any("127.0.0.1" in p and p.endswith(port) for p in ports), f"{svc_name} missing loopback bind: {ports}"

    # RT-02 & RT-04: raas mounts /data, sets MEKONG_PILOT_A_DB_DIR=/data/pilot_a_tenants and MEKONG_ENV=production
    raas_env = [str(e) for e in services["raas"]["environment"]]
    assert "MEKONG_ENV=production" in raas_env
    assert "NODE_ENV=production" not in raas_env
    assert "MEKONG_PILOT_A_DB_DIR=/data/pilot_a_tenants" in raas_env
    assert any(":/data" in str(v) for v in services["raas"]["volumes"])

    # Verify runtime _pilot_base_dir honors MEKONG_PILOT_A_DB_DIR
    custom_dir = tmp_path / "persisted_tenants"
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(custom_dir))
    assert _pilot_base_dir() == custom_dir.resolve()

    # RT-03: Dockerfile copies engine/ alongside src/ and sets MEKONG_PILOT_A_DB_DIR
    dockerfile = (_REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY engine/ ./engine/" in dockerfile
    assert "COPY src/ ./src/" in dockerfile
    assert "MEKONG_PILOT_A_DB_DIR=/data/pilot_a_tenants" in dockerfile
    from engine.license.license_gate_middleware import EngineLicenseGateMiddleware
    assert EngineLicenseGateMiddleware is not None


def test_rt05_pilot_a_kill_switch_stops_intake_and_inflight_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RT-05: Kill switch halts both new webhook intake and in-flight approve dispatch, while allowing safe reject."""
    tenants_dir = tmp_path / "tenants"
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(tenants_dir))
    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", _SECRET)
    prov = provision_isolated_tenant(tenants_dir, "tenant_rt05", "Mekong Agency", "Lan Anh", sme_tier="pilot_a")
    client = TestClient(app)
    hdr = {"X-API-Key": prov.tenant_api_key}

    # 1. Create an in-flight run while kill switch is OFF
    monkeypatch.delenv("MEKONG_PILOT_A_KILL_SWITCH", raising=False)
    now = int(time.time())
    r_ok = client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        headers=hdr,
        json={
            "tenant_id": "tenant_rt05",
            "event_id": "evt_rt05_inflight",
            "sender_id": "zalo_rt05_u1",
            "sender_name": "Minh Khoa",
            "message_text": "Báo giá tư vấn AI 2 giờ",
            "requested_services": ["zalo_oa_lead_to_quote"],
            "estimated_hours": 2,
            "project_title": "AI Setup",
            "extraction_confidence": 0.96,
            "timestamp": now,
            "last_user_interaction_ts": now - 60,
        },
    )
    assert r_ok.status_code == 200
    body_ok = r_ok.json()
    run_id = body_ok["run_id"]
    action_digest = body_ok["action_digest"]

    # 2. Activate kill switch -> new intake must fail-closed with 503
    monkeypatch.setenv("MEKONG_PILOT_A_KILL_SWITCH", "1")
    monkeypatch.setenv("MEKONG_PILOT_A_KILL_SWITCH_REASON", "Incident SEV1 stop")
    r_blocked_intake = client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        headers=hdr,
        json={
            "tenant_id": "tenant_rt05",
            "event_id": "evt_rt05_blocked",
            "sender_id": "zalo_rt05_u2",
            "sender_name": "Lan",
            "message_text": "Báo giá mới",
            "requested_services": ["zalo_oa_lead_to_quote"],
            "estimated_hours": 1,
            "project_title": "Blocked",
            "extraction_confidence": 0.96,
            "timestamp": now,
            "last_user_interaction_ts": now - 30,
        },
    )
    assert r_blocked_intake.status_code == 503
    assert r_blocked_intake.json()["detail"]["error"] == "PILOT_A_KILL_SWITCH_ACTIVE"
    assert r_blocked_intake.json()["detail"]["stage"] == "intake"

    # 3. In-flight run approve dispatch must ALSO be blocked with 503
    r_blocked_dispatch = client.post(
        "/v1/opc/pilot-a/decide",
        headers=hdr,
        json={"tenant_id": "tenant_rt05", "run_id": run_id, "decision": "approve", "action_digest": action_digest},
    )
    assert r_blocked_dispatch.status_code == 503
    assert r_blocked_dispatch.json()["detail"]["error"] == "PILOT_A_KILL_SWITCH_ACTIVE"
    assert r_blocked_dispatch.json()["detail"]["stage"] == "dispatch"

    # 4. Safe wind-down via decision='reject' remains allowed
    r_reject = client.post(
        "/v1/opc/pilot-a/decide",
        headers=hdr,
        json={"tenant_id": "tenant_rt05", "run_id": run_id, "decision": "reject", "action_digest": action_digest},
    )
    assert r_reject.status_code == 200

    # 5. Direct PilotAWorkflow methods also enforce kill switch
    wf = PilotAWorkflow(tmp_path / "direct_rt05.db", _profile(), approval_secret=_SECRET, enforce_consent=False)
    ev = ZaloWebhookEvent("evt_direct", "oa1", "u1", "Anh", "Báo giá tư vấn AI 2 giờ", now, now - 10, ("tu_van_ai",), 2, "AI")
    with pytest.raises(PilotAKillSwitchError):
        wf.handle_webhook(ev)
    monkeypatch.delenv("MEKONG_PILOT_A_KILL_SWITCH", raising=False)
    card = wf.handle_webhook(ev)
    monkeypatch.setenv("MEKONG_PILOT_A_KILL_SWITCH", "true")
    with pytest.raises(PilotAKillSwitchError):
        wf.approve_and_send(card)


def test_rt06_dr_online_backup_and_isolated_restore_rehearsal(tmp_path: Path) -> None:
    """RT-06: WAL-consistent SQLite backup, SHA-256 verification, tamper detection, and full isolated restore."""
    live_dir = tmp_path / "live_tenants"
    prov = provision_isolated_tenant(live_dir, "tenant_rt06", "Mekong Agency", "Lan Anh", sme_tier="pilot_a")
    db_path = live_dir / "tenant_rt06.db"
    wf = PilotAWorkflow(db_path, _profile(), approval_secret=_SECRET, tenant_id="tenant_rt06", enforce_consent=True)
    wf.privacy_guard.record_subject_consent("zalo_rt06_u1")
    now = int(time.time())
    card = wf.handle_webhook(
        ZaloWebhookEvent(
            "evt_rt06_1", "oa1", "zalo_rt06_u1", "Minh Khoa",
            "Báo giá tư vấn AI 2 giờ", now, now - 30, ("tu_van_ai",), 2, "DR Rehearsal",
        )
    )
    raw_wh = json.dumps({
        "bank_tx_id": "FT261119DR06",
        "amount_vnd": card.total_amount_vnd,
        "memo": f"OPC {card.run_id}",
        "bank_id": "MB",
    }).encode("utf-8")
    sig = hmac.new(_VIETQR_SECRET.encode("utf-8"), raw_wh, hashlib.sha256).hexdigest()
    wf.reconcile_payment_and_export_draft(card, raw_wh, sig, _VIETQR_SECRET)

    # Execute DR backup + restore rehearsal through OpsEngine
    ops = OpsEngine(project_root=tmp_path)
    rehearsal_dir = tmp_path / "dr_rehearsal"
    res = ops.dr_rehearse_backup_restore(live_dir, rehearsal_dir)
    assert res["ok"] is True
    assert "tenant_rt06.db" in res["restore"]["databases_restored"]
    assert "tenant_rt06_vietqr.db" in res["restore"]["databases_restored"]
    assert "tenant_rt06_privacy.db" in res["restore"]["databases_restored"]
    assert "tenant_rt06.tenant.json" in res["restore"]["configs_restored"]
    assert all(v.lower() == "ok" for v in res["restore"]["integrity_checks"].values())

    # Verify restored data integrity against original run, payment settlement, and VietQR ledger
    restored_dir = rehearsal_dir / "restore"
    restored_wf = PilotAWorkflow(restored_dir / "tenant_rt06.db", _profile(), approval_secret=_SECRET, tenant_id="tenant_rt06")
    restored_run = restored_wf.state.get_run(card.run_id)
    assert restored_run is not None
    assert restored_run["payment_state"] == "settled"
    assert restored_run["bank_tx_id"] == "FT261119DR06"
    assert restored_run["paid_amount_vnd"] == card.total_amount_vnd
    restored_wf.privacy_guard.require_consent("zalo_rt06_u1")
    with sqlite3.connect(str(restored_dir / "tenant_rt06_vietqr.db")) as vconn:
        tx = vconn.execute("SELECT bank_tx_id, amount_vnd FROM transactions WHERE matched_order_id = ?", (card.run_id,)).fetchone()
    assert tx == ("FT261119DR06", card.total_amount_vnd)
    assert (restored_dir / "tenant_rt06.tenant.json").is_file()
    assert prov.tenant_id == "tenant_rt06"

    # Tamper detection: corrupting a backed-up DB file must fail SHA-256 verification on restore
    tampered_backup = tmp_path / "tampered_backup"
    backup_tenant_directory(live_dir, tampered_backup)
    (tampered_backup / "tenant_rt06.db").write_bytes(b"corrupted-bytes")
    with pytest.raises(ValueError, match="SHA-256 checksum mismatch"):
        restore_tenant_directory(tampered_backup, tmp_path / "tampered_restore")
