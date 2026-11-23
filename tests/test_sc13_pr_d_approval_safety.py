"""Adversarial regression suite for single-use persisted ApprovalTokens and expiring/revocable signed cards."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import time
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.api.pilot_a_approval_tokens import (
    derive_dispatch_idempotency_key,
    ensure_card_revocations_schema,
    rollback_card_revocations_schema,
)
from src.gateway import app
from src.opc.state import StateStore
from src.opc.tenant_provisioner import provision_isolated_tenant


@pytest.fixture()
def client_and_tenant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_root = tmp_path / "pilot_tenants"
    monkeypatch.setenv("MEKONG_PILOT_A_DB_DIR", str(db_root))
    monkeypatch.setenv("MEKONG_APPROVAL_SECRET", "sc13-approval-safety-hmac-secret-2026")
    monkeypatch.setenv("VIETQR_WEBHOOK_SECRET", "sc13-vietqr-webhook-secret-2026")
    monkeypatch.setenv("ZALO_OA_SECRET_KEY", "sc13-zalo-oa-mac-secret-2026")
    monkeypatch.setenv("MEKONG_CARD_SIG_TTL_SECONDS", "600")
    prov = provision_isolated_tenant(
        db_root, "t_alpha", "CTY ALPHA", "Nguyễn Văn An",
        sme_tier="pilot_a", bank_id="VCB", account_no="1122334455",
    )
    prov_b = provision_isolated_tenant(
        db_root, "t_beta", "CTY BETA", "Trần Thị Bình",
        sme_tier="pilot_a", bank_id="VCB", account_no="5566778899",
    )
    return TestClient(app), db_root, prov, prov_b


def _create_intake(client: TestClient, tenant_id: str, api_key: str, event_id: str) -> dict:
    r = client.post(
        "/v1/opc/pilot-a/webhook/zalo",
        json={
            "event_id": event_id,
            "oa_id": "oa_test_01",
            "sender_id": "84901112233",
            "sender_name": "Khách Hàng Thử Nghiệm",
            "message_text": "Cần báo giá gói tư vấn AI 5 giờ",
            "requested_services": ["tu_van_ai"],
            "estimated_hours": 5,
            "project_title": "Báo giá tư vấn AI",
            "tenant_id": tenant_id,
            "grant_consent": True,
        },
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_valid_first_approval_consumes_persisted_intake_token_and_rejects_reuse(client_and_tenant) -> None:
    client, db_root, prov, _ = client_and_tenant
    intake = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_valid_1")
    run_id = intake["run_id"]
    tok_id = intake["approval_token_id"]
    digest = intake["action_digest"]

    # First approval consumes the exact persisted intake token (no new token minted)
    r1 = client.post(
        "/v1/opc/pilot-a/decide",
        json={
            "run_id": run_id,
            "tenant_id": "t_alpha",
            "decision": "approve",
            "action_digest": digest,
            "approval_token_id": tok_id,
            "idempotency_key": "attacker-forged-idem-key",
        },
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "completed"
    assert r1.json()["approval_token_id"] == tok_id

    # Verify DB: exactly 1 approval row (consumed=1) and server-derived idempotency key used
    state = StateStore(db_root / "t_alpha.db")
    stored_tok = state.get_approval(tok_id)
    assert stored_tok is not None and stored_tok.consumed is True
    expected_idem = derive_dispatch_idempotency_key("t_alpha", run_id, digest)
    assert state.get_action_status(expected_idem) == "completed"
    assert state.get_action_status("attacker-forged-idem-key") is None

    # Explicit reuse of the same approval_token_id is rejected (409)
    r_reuse = client.post(
        "/v1/opc/pilot-a/decide",
        json={
            "run_id": run_id,
            "tenant_id": "t_alpha",
            "decision": "approve",
            "action_digest": digest,
            "approval_token_id": tok_id,
        },
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_reuse.status_code == 409


def test_concurrent_token_reuse_executes_at_most_once(client_and_tenant) -> None:
    client, db_root, prov, _ = client_and_tenant
    intake = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_conc_1")
    payload = {
        "run_id": intake["run_id"],
        "tenant_id": "t_alpha",
        "decision": "approve",
        "action_digest": intake["action_digest"],
        "approval_token_id": intake["approval_token_id"],
    }
    headers = {"X-API-Key": prov.tenant_api_key}

    def _call() -> int:
        return client.post("/v1/opc/pilot-a/decide", json=payload, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        codes = list(pool.map(lambda _: _call(), range(4)))
    assert codes.count(200) == 1
    assert all(c in (200, 409) for c in codes)

    state = StateStore(db_root / "t_alpha.db")
    with state._get_connection() as conn:  # noqa: SLF001
        action_rows = conn.execute("SELECT COUNT(*) FROM opc_actions WHERE run_id = ?", (intake["run_id"],)).fetchone()[0]
    assert action_rows == 1


def test_cross_tenant_and_cross_run_tokens_rejected(client_and_tenant) -> None:
    client, _, prov_a, prov_b = client_and_tenant
    intake_a1 = _create_intake(client, "t_alpha", prov_a.tenant_api_key, "evt_xt_a1")
    intake_a2 = _create_intake(client, "t_alpha", prov_a.tenant_api_key, "evt_xt_a2")
    intake_b1 = _create_intake(client, "t_beta", prov_b.tenant_api_key, "evt_xt_b1")

    # Token from tenant B presented against tenant A's run -> 409
    r_xt = client.post(
        "/v1/opc/pilot-a/decide",
        json={
            "run_id": intake_a1["run_id"],
            "tenant_id": "t_alpha",
            "decision": "approve",
            "action_digest": intake_a1["action_digest"],
            "approval_token_id": intake_b1["approval_token_id"],
        },
        headers={"X-API-Key": prov_a.tenant_api_key},
    )
    assert r_xt.status_code == 409

    # Card sig from tenant B presented against tenant A -> 401
    r_xt_sig = client.post(
        "/v1/opc/pilot-a/decide",
        json={
            "run_id": intake_a1["run_id"],
            "tenant_id": "t_alpha",
            "decision": "approve",
            "action_digest": intake_a1["action_digest"],
            "card_sig": intake_b1["card_sig"],
        },
    )
    assert r_xt_sig.status_code == 401

    # Token from run A2 presented against run A1 -> 409
    r_xr = client.post(
        "/v1/opc/pilot-a/decide",
        json={
            "run_id": intake_a1["run_id"],
            "tenant_id": "t_alpha",
            "decision": "approve",
            "action_digest": intake_a1["action_digest"],
            "approval_token_id": intake_a2["approval_token_id"],
        },
        headers={"X-API-Key": prov_a.tenant_api_key},
    )
    assert r_xr.status_code == 409


def test_payload_amount_and_recipient_tampering_after_approval_blocked(client_and_tenant) -> None:
    client, db_root, prov, _ = client_and_tenant
    state = StateStore(db_root / "t_alpha.db")

    for field, mutator in (
        ("content", lambda d: d.__setitem__("content", "TAMPERED CONTENT")),
        ("amount", lambda d: d["parameters"].__setitem__("amount_vnd", 999_999_999)),
        ("recipient", lambda d: d.__setitem__("recipient", "zalo:attacker_999")),
    ):
        intake = _create_intake(client, "t_alpha", prov.tenant_api_key, f"evt_tamper_{field}")
        run_id = intake["run_id"]
        with state._get_connection() as conn:  # noqa: SLF001
            raw = conn.execute("SELECT action_payload_json FROM opc_runs WHERE run_id = ?", (run_id,)).fetchone()[0]
            payload_dict = json.loads(raw)
            mutator(payload_dict)
            conn.execute(
                "UPDATE opc_runs SET action_payload_json = ? WHERE run_id = ?",
                (json.dumps(payload_dict, sort_keys=True), run_id),
            )
        # Presenting original digest fails TOCTOU check; presenting recomputed digest still fails persisted token digest check
        r_orig = client.post(
            "/v1/opc/pilot-a/decide",
            json={
                "run_id": run_id,
                "tenant_id": "t_alpha",
                "decision": "approve",
                "action_digest": intake["action_digest"],
            },
            headers={"X-API-Key": prov.tenant_api_key},
        )
        assert r_orig.status_code == 409

        run_view = client.get(f"/v1/opc/pilot-a/runs/{run_id}?tenant_id=t_alpha", headers={"X-API-Key": prov.tenant_api_key}).json()
        r_recomp = client.post(
            "/v1/opc/pilot-a/decide",
            json={
                "run_id": run_id,
                "tenant_id": "t_alpha",
                "decision": "approve",
                "action_digest": run_view["action_digest"],
            },
            headers={"X-API-Key": prov.tenant_api_key},
        )
        assert r_recomp.status_code == 409


def test_expired_revoked_forged_and_unauthenticated_requests_fail_closed(client_and_tenant) -> None:
    client, db_root, prov, _ = client_and_tenant
    state = StateStore(db_root / "t_alpha.db")

    # 1. Expired approval token + expired signed card URL
    intake_exp = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_expired_1")
    with state._get_connection() as conn:  # noqa: SLF001
        conn.execute("UPDATE opc_approvals SET expires_at = 1 WHERE run_id = ?", (intake_exp["run_id"],))
    r_exp = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_exp["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_exp["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_exp.status_code == 409
    future_now = int(intake_exp["card_sig_expires_at"]) + 60
    with patch("src.api.pilot_a_routes.time.time", return_value=future_now):
        r_card_exp = client.get(f"/v1/opc/pilot-a/card/{intake_exp['run_id']}?tenant_id=t_alpha&sig={intake_exp['card_sig']}")
        assert r_card_exp.status_code == 401 and r_card_exp.json()["detail"]["error"] == "card_sig_expired"

    # 2. Revoked approval token & revoked signed card URL
    intake_rev = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_revoked_1")
    r_revoke = client.post(
        "/v1/opc/pilot-a/revoke",
        json={"run_id": intake_rev["run_id"], "tenant_id": "t_alpha", "reason": "owner_cancelled"},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_revoke.status_code == 200 and r_revoke.json()["revoked_approvals"] == 1
    assert client.get(f"/v1/opc/pilot-a/card/{intake_rev['run_id']}?tenant_id=t_alpha&sig={intake_rev['card_sig']}").status_code == 401
    r_dec_rev = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_rev["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_rev["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_dec_rev.status_code == 409

    # 3. Forged token HMAC signature in DB + forged card signature + missing owner authentication
    intake_forg = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_forged_1")
    assert client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_forg["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_forg["action_digest"]},
    ).status_code == 401
    assert client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_forg["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_forg["action_digest"], "card_sig": "v2.9999999999." + "a" * 64},
    ).status_code == 401
    with state._get_connection() as conn:  # noqa: SLF001
        conn.execute("UPDATE opc_approvals SET signature = ? WHERE run_id = ?", ("f" * 64, intake_forg["run_id"]))
    r_forged = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_forg["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_forg["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_forged.status_code == 409


def test_crash_recovery_retry_after_ack_unavailable_store_and_migration_rollback(client_and_tenant) -> None:
    client, db_root, prov, _ = client_and_tenant
    state = StateStore(db_root / "t_alpha.db")

    # 1. Crash before consumption: persisted token remains unconsumed; retry succeeds once
    intake_pre = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_crash_pre")
    with patch("src.opc.engine.OPCEngine.execute_approved_action", side_effect=RuntimeError("simulated crash before consumption")):
        with pytest.raises(RuntimeError):
            client.post(
                "/v1/opc/pilot-a/decide",
                json={"run_id": intake_pre["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_pre["action_digest"]},
                headers={"X-API-Key": prov.tenant_api_key},
            )
    assert state.get_approval(intake_pre["approval_token_id"]).consumed is False
    r_recover = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_pre["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_pre["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_recover.status_code == 200 and r_recover.json()["status"] == "completed"

    # 2. Crash after consumption (token consumed=1, run still pending): fail-closed, never mints new token or double-dispatches
    intake_post = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_crash_post")
    assert state.consume_approval_atomic(intake_post["approval_token_id"], intake_post["action_digest"], int(time.time())) is True
    r_post = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_post["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_post["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_post.status_code == 409

    # 3. Retry after dispatch acknowledgement (completed run, card retry without explicit token_id deduplicates cleanly)
    r_retry_ack = client.post(
        "/v1/opc/pilot-a/decide",
        json={"run_id": intake_pre["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_pre["action_digest"]},
        headers={"X-API-Key": prov.tenant_api_key},
    )
    assert r_retry_ack.status_code == 200 and r_retry_ack.json()["side_effect_deduplicated"] is True

    # 4. Missing / unavailable state store fails closed (503)
    with patch("src.opc.state.StateStore.get_run", side_effect=sqlite3.OperationalError("database is locked")):
        r_unavail = client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": intake_pre["run_id"], "tenant_id": "t_alpha", "decision": "approve", "action_digest": intake_pre["action_digest"]},
            headers={"X-API-Key": prov.tenant_api_key},
        )
        assert r_unavail.status_code == 503 and r_unavail.json()["detail"]["error"] == "state_store_unavailable"

    # 5. Local schema migration & rollback evidence for opc_card_revocations
    ensure_card_revocations_schema(state)
    with state._get_connection() as conn:  # noqa: SLF001
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opc_card_revocations'").fetchone() is not None
    rollback_card_revocations_schema(state)
    with state._get_connection() as conn:  # noqa: SLF001
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opc_card_revocations'").fetchone() is None
    assert state.get_run(intake_pre["run_id"]) is not None


def test_card_sig_read_never_extends_expiry_and_write_error_returns_503(client_and_tenant) -> None:
    """Card-sig authenticated GETs must echo presented token without extending expiry; DB write errors return 503."""
    client, _db_root, prov, _prov_b = client_and_tenant
    intake = _create_intake(client, "t_alpha", prov.tenant_api_key, "evt_card_ttl")
    orig_sig = intake["card_sig"]
    orig_exp = int(orig_sig.split(".")[1])

    # Calling GET /runs/{run_id} and GET /card/{run_id} with only X-Card-Sig must not extend exp
    with patch("src.api.pilot_a_routes.time.time", return_value=orig_exp - 10):
        r_run = client.get(
            f"/v1/opc/pilot-a/runs/{intake['run_id']}",
            params={"tenant_id": "t_alpha"},
            headers={"X-Card-Sig": orig_sig},
        )
        assert r_run.status_code == 200
        assert r_run.json()["card_sig"] == orig_sig
        assert r_run.json()["card_sig_expires_at"] == orig_exp

        r_card = client.get(
            f"/v1/opc/pilot-a/card/{intake['run_id']}",
            params={"tenant_id": "t_alpha"},
            headers={"X-Card-Sig": orig_sig},
        )
        assert r_card.status_code == 200
        assert orig_sig in r_card.text

    # DB write error on reject returns 503 fail-closed
    with patch("src.opc.state.StateStore.save_run", side_effect=sqlite3.OperationalError("disk full")):
        r_err = client.post(
            "/v1/opc/pilot-a/decide",
            json={"run_id": intake["run_id"], "tenant_id": "t_alpha", "decision": "reject", "action_digest": intake["action_digest"]},
            headers={"X-API-Key": prov.tenant_api_key},
        )
        assert r_err.status_code == 503 and r_err.json()["detail"]["error"] == "state_store_unavailable"

