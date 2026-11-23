"""Adversarial regression suite for persisted jurisdiction authority and multi-currency Decimal accounting."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sqlite3
import time

from fastapi.testclient import TestClient
import pytest

from src.gateway import app
from src.opc.currency_accounting import FxQuote
from src.opc.models import UsageRecord, UsageStage
from src.opc.usage import UsageLedger
from src.raas.nowpayments_checkout import create_invoice, create_payment
from src.raas.tenant import TenantStore


@pytest.fixture()
def raas_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "raas_tenants.db"
    monkeypatch.setenv("MEKONG_RAAS_DB", str(db_path))
    monkeypatch.setenv("MEKONG_JURISDICTION_ADMIN_SECRET", "sc13-jurisdiction-admin-secret-2026")
    store = TenantStore(db_path)
    vn_tenant = store.create_tenant("vn-sme-alpha")
    sg_tenant = store.create_tenant("sg-corp-beta")
    store.update_jurisdiction_admin(
        sg_tenant.id, "SG", actor_id="compliance_officer_01", evidence_ref="ACRA-SG-2026-009"
    )
    return TestClient(app), db_path, store, vn_tenant, sg_tenant


def test_persisted_vn_jurisdiction_cannot_be_spoofed_by_request(raas_env) -> None:
    client, _, _, vn_tenant, _ = raas_env

    # 1. Persisted VN, request US -> 403 (client input never overrides persisted VN)
    r_spoof = client.post(
        "/v1/checkout",
        json={
            "tier": "ENTERPRISE",
            "rail": "nowpayments",
            "email": "cfo@vn-sme.vn",
            "org_id": vn_tenant.id,
            "jurisdiction": "US",
        },
    )
    assert r_spoof.status_code == 403
    assert r_spoof.json()["detail"]["jurisdiction"] == "VN"
    assert r_spoof.json()["detail"]["allowed_rails"] == ["vietqr"]

    # 2. Persisted VN, request missing jurisdiction -> 403 on crypto, 200 on vietqr
    r_missing = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "nowpayments", "email": "cfo@vn-sme.vn", "org_id": vn_tenant.id},
    )
    assert r_missing.status_code == 403
    r_missing_vqr = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "vietqr", "email": "cfo@vn-sme.vn", "org_id": vn_tenant.id},
        headers={"X-API-Key": vn_tenant.api_key},
    )
    assert r_missing_vqr.status_code == 200 and r_missing_vqr.json()["rail"] == "vietqr"

    # 3. Persisted VN, request VN -> 403 on crypto, 200 on vietqr
    r_vn_crypto = client.post(
        "/v1/checkout",
        json={
            "tier": "BASIC",
            "rail": "nowpayments",
            "email": "cfo@vn-sme.vn",
            "org_id": vn_tenant.id,
            "jurisdiction": "VN",
        },
        headers={"X-API-Key": vn_tenant.api_key},
    )
    assert r_vn_crypto.status_code == 403
    r_vn_vqr = client.post(
        "/v1/checkout",
        json={
            "tier": "BASIC",
            "rail": "vietqr",
            "email": "cfo@vn-sme.vn",
            "org_id": vn_tenant.id,
            "jurisdiction": "VN",
        },
        headers={"X-API-Key": vn_tenant.api_key},
    )
    assert r_vn_vqr.status_code == 200


def test_unverified_tenant_cross_tenant_checkout_and_backend_crypto_restriction(raas_env) -> None:
    client, _, _, vn_tenant, sg_tenant = raas_env

    # 4. Unverified tenant claiming US fails closed to VN -> 403 on crypto
    r_unverified = client.post(
        "/v1/checkout",
        json={
            "tier": "BASIC",
            "rail": "nowpayments",
            "email": "ghost@unverified.example",
            "org_id": "nonexistent-org-999",
            "jurisdiction": "US",
        },
    )
    assert r_unverified.status_code == 403
    assert r_unverified.json()["detail"]["jurisdiction"] == "VN"

    # 5. Cross-tenant checkout blocked when caller presents another tenant's API key
    r_cross = client.post(
        "/v1/checkout",
        json={
            "tier": "BASIC",
            "rail": "nowpayments",
            "email": "attacker@vn-sme.vn",
            "org_id": sg_tenant.id,
        },
        headers={"X-API-Key": vn_tenant.api_key},
    )
    assert r_cross.status_code == 403
    assert r_cross.json()["detail"]["error"] == "cross_tenant_checkout_forbidden"

    # 6. Restricted crypto payment rail enforced at backend service boundary too
    with pytest.raises(ValueError, match="crypto rail is not permitted"):
        create_invoice("basic", order_id="ord_vn_1", jurisdiction="VN")
    with pytest.raises(ValueError, match="crypto rail is not permitted"):
        create_payment("basic", order_id="ord_vn_2", jurisdiction="")


def test_admin_jurisdiction_workflow_persistence_restart_and_migration_rollback(raas_env) -> None:
    client, db_path, store, vn_tenant, _ = raas_env

    # Missing/wrong admin secret rejected (401)
    r_no_auth = client.post(
        f"/v1/admin/tenants/{vn_tenant.id}/jurisdiction",
        json={"jurisdiction": "SG", "actor_id": "admin_1", "evidence_ref": "KYC-123"},
    )
    assert r_no_auth.status_code == 401

    # Missing evidence rejected (422)
    r_no_ev = client.post(
        f"/v1/admin/tenants/{vn_tenant.id}/jurisdiction",
        json={"jurisdiction": "SG", "actor_id": "admin_1", "evidence_ref": "   "},
        headers={"X-Admin-Secret": "sc13-jurisdiction-admin-secret-2026"},
    )
    assert r_no_ev.status_code == 422

    # Valid admin update persists across TenantStore restart
    r_ok = client.post(
        f"/v1/admin/tenants/{vn_tenant.id}/jurisdiction",
        json={"jurisdiction": "SG", "actor_id": "compliance_lead", "evidence_ref": "ACRA-2026-888"},
        headers={"X-Admin-Secret": "sc13-jurisdiction-admin-secret-2026"},
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["old_jurisdiction"] == "VN"
    assert r_ok.json()["new_jurisdiction"] == "SG"

    restarted_store = TenantStore(db_path)
    assert restarted_store.get_persisted_jurisdiction(vn_tenant.id) == "SG"

    # Local migration & rollback for tenant_jurisdiction_audit
    restarted_store.rollback_jurisdiction_audit_schema()
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tenant_jurisdiction_audit'").fetchone() is None
    assert restarted_store.get_persisted_jurisdiction(vn_tenant.id) == "SG"
    restarted_store.ensure_jurisdiction_audit_schema()


def test_multicurrency_accounting_fx_provenance_dedup_legacy_and_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "usage_sc13.db"
    ledger = UsageLedger(db_path)
    now = int(time.time())

    # 7. Mixed USD/VND usage + 10. Mixed measured/estimated usage
    assert ledger.record_usage(
        UsageRecord("ev_usd_act", "run_mix", 1, UsageStage.ACTUAL, "openai", "gpt-4o-mini", 500, "0", "0.1250", "USD", "tenant", "provider_billed", now)
    ) is True
    assert ledger.record_usage(
        UsageRecord("ev_vnd_act", "run_mix", 1, UsageStage.ACTUAL, "vietqr", "napas247", 0, "0", "5000", "VND", "tenant", "provider_billed", now + 1)
    ) is True
    assert ledger.record_usage(
        UsageRecord("ev_usd_est", "run_mix", 1, UsageStage.ESTIMATED, "openai", "gpt-4o-mini", 200, "0", "0.0500", "USD", "tenant", "estimated", now + 2)
    ) is True

    # 11. Duplicate cost event is idempotently ignored
    assert ledger.record_usage(
        UsageRecord("ev_usd_act", "run_mix", 1, UsageStage.ACTUAL, "openai", "gpt-4o-mini", 500, "0", "0.1250", "USD", "tenant", "provider_billed", now)
    ) is False

    # Without FX: never produces a fictitious scalar sum
    sep = ledger.summarize_currency_aware_costs("run_mix", now=now + 10)
    assert sep.status == "SEPARATED_BY_CURRENCY"
    assert sep.has_mixed_currencies is True
    assert sep.measured_by_currency == {"USD": Decimal("0.1250"), "VND": Decimal("5000")}
    assert sep.estimated_by_currency == {"USD": Decimal("0.0500")}
    assert sep.converted_measured_total is None

    # CostAccounting refuses to collapse mixed currencies into a single float
    ca_mix = ledger.summarize_cost_accounting("run_mix")
    assert ca_mix.actual_cost is None

    # 8. Missing FX rate fails closed
    miss_fx = ledger.summarize_currency_aware_costs("run_mix", target_currency="VND", fx_quotes=[], now=now + 10)
    assert miss_fx.status == "INCOMPLETE_MISSING_DATA"
    assert miss_fx.has_stale_or_missing_fx is True
    assert miss_fx.converted_measured_total is None

    # 9. Stale FX rate fails closed
    stale_quote = FxQuote("USD", "VND", Decimal("25000"), "vietcombank_daily", timestamp=now - 100_000, max_age_seconds=3600)
    stale_fx = ledger.summarize_currency_aware_costs("run_mix", target_currency="VND", fx_quotes=[stale_quote], now=now + 10)
    assert stale_fx.status == "INCOMPLETE_MISSING_DATA"
    assert stale_fx.has_stale_or_missing_fx is True
    assert stale_fx.converted_measured_total is None

    # Verified fresh FX converts accurately using Decimal while preserving original amounts
    fresh_quote = FxQuote("USD", "VND", Decimal("25000"), "vietcombank_daily", timestamp=now, max_age_seconds=86400)
    conv = ledger.summarize_currency_aware_costs("run_mix", target_currency="VND", fx_quotes=[fresh_quote], now=now + 10)
    assert conv.status == "COMPLETE_CONVERTED"
    assert conv.converted_measured_total == Decimal("8125.0000")  # 0.1250 * 25000 + 5000
    assert conv.converted_estimated_total == Decimal("1250.0000")  # 0.0500 * 25000
    assert conv.measured_by_currency == {"USD": Decimal("0.1250"), "VND": Decimal("5000")}

    # 12. Per-currency reserve_budget + retry/cache-hit isolation (USD limit not polluted by VND rows)
    assert ledger.reserve_budget("res_usd_1", "run_mix", "0.50", "USD", "tenant", now + 20, hard_limit="1.00") is True
    assert ledger.reserve_budget("res_usd_1", "run_mix", "0.50", "USD", "tenant", now + 21, hard_limit="1.00") is False  # duplicate event_id

    # 13. Legacy rows missing currency fail closed and never coerce to zero
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO opc_usage_events VALUES (?, ?, 1, 'actual', 'legacy', 'v1', 100, '0', '10.00', '', 'tenant', 'legacy', ?)",
            ("ev_legacy_noccy", "run_legacy", now),
        )
        conn.commit()
    leg = ledger.summarize_currency_aware_costs("run_legacy", now=now + 10)
    assert leg.status == "INCOMPLETE_MISSING_DATA"
    assert leg.has_missing_currency is True
    assert ledger.summarize_cost_accounting("run_legacy").actual_cost is None

    # 14. Database restart preserves all usage rows and exact Decimal totals
    restarted_ledger = UsageLedger(db_path)
    after_restart = restarted_ledger.summarize_currency_aware_costs("run_mix", target_currency="VND", fx_quotes=[fresh_quote], now=now + 30)
    assert after_restart.converted_measured_total == Decimal("8125.0000")

    # 15. NaN/unverified FX quotes, invalid target_currency, and negative/invalid reserve_budget fail closed
    nan_quote = FxQuote("USD", "VND", Decimal("NaN"), "bad_feed", timestamp=now, max_age_seconds=86400)
    unverified_quote = FxQuote("USD", "VND", Decimal("25000"), "untrusted", timestamp=now, max_age_seconds=86400, confidence="estimated")
    bad_fx = restarted_ledger.summarize_currency_aware_costs("run_mix", target_currency="VND", fx_quotes=[nan_quote, unverified_quote], now=now + 10)
    assert bad_fx.status == "INCOMPLETE_MISSING_DATA" and bad_fx.converted_measured_total is None

    bad_target = restarted_ledger.summarize_currency_aware_costs("run_mix", target_currency="??", fx_quotes=[fresh_quote], now=now + 10)
    assert bad_target.status == "INCOMPLETE_MISSING_DATA" and bad_target.has_stale_or_missing_fx is True

    assert restarted_ledger.reserve_budget("res_neg", "run_mix", "-5.00", "USD", "tenant", now + 31, hard_limit="1.00") is False
    assert restarted_ledger.reserve_budget("res_bad_ccy", "run_mix", "0.10", "", "tenant", now + 32, hard_limit="1.00") is False
    assert restarted_ledger.reserve_budget("res_lower_ccy", "run_mix", "0.10", " usd ", "tenant", now + 33, hard_limit="1.00") is True


def test_unauthenticated_sg_hijack_email_fallback_and_duplicate_name_ambiguity_blocked(raas_env) -> None:
    """Unauthenticated callers cannot hijack an SG tenant via org_id or email; duplicate names fail closed."""
    client, _db_path, store, _vn_tenant, sg_tenant = raas_env

    # Unauthenticated nowpayments targeting an existing SG tenant fails closed to VN (403, no 200 oracle)
    r_unauth_crypto = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "nowpayments", "email": "attacker@vn.vn", "org_id": sg_tenant.id},
    )
    assert r_unauth_crypto.status_code == 403
    assert r_unauth_crypto.json()["detail"]["jurisdiction"] == "VN"

    # Unauthenticated vietqr targeting an existing tenant requires tenant API key (401)
    r_unauth_vqr = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "vietqr", "email": "attacker@vn.vn", "org_id": sg_tenant.id},
    )
    assert r_unauth_vqr.status_code == 401

    # Foreign req.email matching an SG tenant's name never unlocks nowpayments
    sg_email_tenant = store.create_tenant("cfo@sg-corp.sg")
    store.update_jurisdiction_admin(sg_email_tenant.id, "SG", actor_id="compliance_admin", evidence_ref="ACRA-SG-9")
    r_email_hijack = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "nowpayments", "email": "cfo@sg-corp.sg", "org_id": "attacker-vn-org"},
    )
    assert r_email_hijack.status_code == 403
    assert r_email_hijack.json()["detail"]["jurisdiction"] == "VN"

    # Authenticated SG tenant succeeds on nowpayments
    r_auth_sg = client.post(
        "/v1/checkout",
        json={"tier": "BASIC", "rail": "nowpayments", "email": "cfo@sg-corp.sg", "org_id": sg_email_tenant.id},
        headers={"X-API-Key": sg_email_tenant.api_key},
    )
    assert r_auth_sg.status_code == 200 and r_auth_sg.json()["rail"] == "nowpayments"

    # Ambiguous duplicate tenant names fail closed
    t1 = store.create_tenant("dup-corp")
    t2 = store.create_tenant("dup-corp")
    store.update_jurisdiction_admin(t2.id, "SG", actor_id="compliance_admin", evidence_ref="ACRA-DUP-2")
    assert store.get_persisted_jurisdiction("dup-corp") is None
    assert store.get_persisted_jurisdiction(t1.id) == "VN"
    assert store.get_persisted_jurisdiction(t2.id) == "SG"
    with pytest.raises(ValueError, match="Ambiguous tenant name"):
        store.update_jurisdiction_admin("dup-corp", "US", actor_id="compliance_admin", evidence_ref="EV-DUP")

