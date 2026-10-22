"""Unit & CLI tests for 25-Step Open-Core Public GitHub + SaaS Monetization (Phases 559-560)."""
from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from src.cli.commands.opencore_saas_restructuring_command import opencore_saas_app
from src.core.mcu_billing import MCUBilling
from src.core.opencore.phase_559_opencore_25_step_catalog import (
    TWENTY_FIVE_OPENCORE_STEPS,
    OpenCorePhase,
)
from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
    OpenCoreReadinessTelemetry,
    OpenCoreReadinessVerdict,
    OpenCoreSaasReadinessEngine,
)
from src.core.opencore.monetization_gate_probes import probe
from src.core.opencore.saas_immutable_audit_ledger import AuditLedger
from src.raas.payos_webhook_handler import PayOSWebhookHandler, PayOSWebhookPayload

REPO_ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_25_step_catalog_completeness() -> None:
    assert len(TWENTY_FIVE_OPENCORE_STEPS) == 25
    assert [s.step_number for s in TWENTY_FIVE_OPENCORE_STEPS] == list(range(1, 26))
    for phase in OpenCorePhase:
        assert len(OpenCoreSaasReadinessEngine.list_steps(phase)) == 5


def test_readiness_engine_verdicts() -> None:
    blocked = OpenCoreSaasReadinessEngine.evaluate(
        OpenCoreReadinessTelemetry(
            completed_step_Count=25, leaked_secrets_detected=1,
            private_dirs_exposed_in_git=False, jwt_license_gate_enforced=True,
            mcu_http402_billing_wired=True,
        )
    )
    assert blocked.verdict == OpenCoreReadinessVerdict.BLOCKED_SECRET_OR_BOUNDARY_LEAK
    assert blocked.safe_for_public_github_push is False

    incomplete = OpenCoreSaasReadinessEngine.evaluate(
        OpenCoreReadinessTelemetry(
            completed_step_Count=20, leaked_secrets_detected=0,
            private_dirs_exposed_in_git=False, jwt_license_gate_enforced=True,
            mcu_http402_billing_wired=False,
        )
    )
    assert incomplete.verdict == OpenCoreReadinessVerdict.MONETIZATION_GATE_INCOMPLETE
    assert incomplete.safe_for_public_github_push is True
    assert incomplete.saas_paywall_active is False

    ready = OpenCoreSaasReadinessEngine.evaluate(
        OpenCoreReadinessTelemetry(
            completed_step_Count=25, leaked_secrets_detected=0,
            private_dirs_exposed_in_git=False, jwt_license_gate_enforced=True,
            mcu_http402_billing_wired=True,
        )
    )
    assert ready.verdict == OpenCoreReadinessVerdict.PUBLIC_GITHUB_SAAS_READY
    assert ready.completion_pct == 100.0
    assert ready.safe_for_public_github_push is True
    assert ready.saas_paywall_active is True


def test_verify_filesystem_hygiene_real_repo_and_synthetic(tmp_path: Path) -> None:
    real_hygiene = OpenCoreSaasReadinessEngine.verify_filesystem_hygiene(REPO_ROOT)
    assert real_hygiene.is_clean is True, f"Missing hygiene items: {real_hygiene.missing_items}"
    assert real_hygiene.gitignore_valid is True
    assert real_hygiene.env_example_valid is True
    assert real_hygiene.license_mit_valid is True
    assert real_hygiene.contributing_cla_valid is True
    assert real_hygiene.apps_tracked_files_count == 0

    audit_report = OpenCoreSaasReadinessEngine.audit_repository(REPO_ROOT, completed_steps=25)
    probes = probe()
    gate_enforced = probes.jwt_license_gate_enforced and probes.mcu_http402_billing_wired
    if gate_enforced:
        assert audit_report.verdict == OpenCoreReadinessVerdict.PUBLIC_GITHUB_SAAS_READY
        assert audit_report.saas_paywall_active is True
    else:
        # The audit must agree with the probes, and the failure must be named.
        assert audit_report.verdict == OpenCoreReadinessVerdict.MONETIZATION_GATE_INCOMPLETE
        assert audit_report.safe_for_public_github_push is True
        assert audit_report.saas_paywall_active is False
        named = probes.gate_gaps + probes.billing_gaps
        assert named, "probe reported an incomplete gate without naming a gap"
        assert audit_report.monetization_gaps == tuple(named)

    (tmp_path / ".gitignore").write_text("apps/\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("OPENROUTER_API_KEY=sk-or-v1-leakedsecret\n", encoding="utf-8")
    bad_hygiene = OpenCoreSaasReadinessEngine.verify_filesystem_hygiene(tmp_path)
    assert bad_hygiene.is_clean is False
    assert bad_hygiene.gitignore_valid is False
    assert bad_hygiene.env_example_valid is False
    assert bad_hygiene.leaked_secrets_detected >= 1
    bad_report = OpenCoreSaasReadinessEngine.audit_repository(tmp_path)
    assert bad_report.verdict == OpenCoreReadinessVerdict.BLOCKED_SECRET_OR_BOUNDARY_LEAK


def test_payos_webhook_handler_signature_replay_and_mcu_credit(tmp_path: Path) -> None:
    checksum_key = "payos_test_checksum_secret_2026"
    billing = MCUBilling(db_path=str(tmp_path / "credits.db"))
    ledger = AuditLedger(ledger_file=tmp_path / "audit.jsonl")
    handler = PayOSWebhookHandler(
        checksum_key=checksum_key, mcu_billing=billing, audit_ledger=ledger, vnd_per_mcu=1000
    )

    payment_data = {
        "orderCode": 90210, "amount": 250000, "description": "Mekong Pro Topup",
        "accountNumber": "1903888999", "reference": "FT26290001",
        "transactionDateTime": "2026-10-17 14:30:00", "currency": "VND", "paymentLinkId": "plink_001",
    }
    valid_sig = PayOSWebhookHandler.compute_payos_signature(payment_data, checksum_key)

    res_ok = handler.process_webhook(
        PayOSWebhookPayload(
            code="00", desc="success", success=True,
            data=payment_data, signature=valid_sig, tenant_id="org_vietqr_01",
        )
    )
    assert res_ok.accepted is True
    assert res_ok.mcu_credited == 250
    assert res_ok.balance_after == 250
    assert billing.get_balance("org_vietqr_01") == 250
    assert len(res_ok.ledger_hash) == 64
    assert ledger.verify_integrity() is True

    res_replay = handler.process_webhook(
        PayOSWebhookPayload(
            code="00", desc="success", success=True,
            data=payment_data, signature=valid_sig, tenant_id="org_vietqr_01",
        )
    )
    assert res_replay.accepted is False
    assert res_replay.reason == "REPLAY_ORDER_DETECTED"
    assert billing.get_balance("org_vietqr_01") == 250

    forged_data = dict(payment_data, orderCode=90211)
    res_bad_sig = handler.process_webhook(
        PayOSWebhookPayload(
            code="00", desc="success", success=True,
            data=forged_data, signature="00" * 32, tenant_id="org_vietqr_01",
        )
    )
    assert res_bad_sig.accepted is False
    assert res_bad_sig.reason == "INVALID_PAYOS_SIGNATURE"


def test_modularized_loc_invariants() -> None:
    targets = [
        REPO_ROOT / "src/core/mcu_billing.py",
        REPO_ROOT / "src/core/mcu_billing_models.py",
        REPO_ROOT / "src/core/mcu_billing_store.py",
        REPO_ROOT / "src/raas/payos_webhook_handler.py",
        REPO_ROOT / "src/core/opencore/phase_560_opencore_saas_readiness_engine.py",
        REPO_ROOT / "src/cli/commands/opencore_saas_restructuring_command.py",
        *sorted((REPO_ROOT / "src/core/banking_engine").glob("*.py")),
    ]
    for path in targets:
        assert path.is_file(), f"Expected module missing: {path}"
        loc = sum(1 for _ in path.open("r", encoding="utf-8"))
        assert loc <= 195, f"{path.relative_to(REPO_ROOT)} exceeds 195 LOC ({loc} lines)"


def test_opencore_saas_cli_commands() -> None:
    res_steps = runner.invoke(opencore_saas_app, ["steps"])
    assert res_steps.exit_code == 0
    assert json.loads(res_steps.stdout)["total"] == 25

    res_audit = runner.invoke(
        opencore_saas_app, ["audit", "--verify-fs", "--repo-root", str(REPO_ROOT)]
    )
    assert res_audit.exit_code == 0
    reported = json.loads(res_audit.stdout)
    probes = probe()
    gate_enforced = probes.jwt_license_gate_enforced and probes.mcu_http402_billing_wired
    if gate_enforced:
        assert reported["verdict"] == "PUBLIC_GITHUB_SAAS_READY"
        assert reported["saas_paywall_active"] is True
    else:
        # The CLI must publish the same reasons the probes found, not a generic string.
        assert reported["verdict"] == "MONETIZATION_GATE_INCOMPLETE"
        gaps = probes.gate_gaps + probes.billing_gaps
        assert reported["monetization_gaps"] == list(gaps)
        assert all(gap in reported["rationale"] for gap in gaps)

    res_hygiene = runner.invoke(opencore_saas_app, ["hygiene", "--repo-root", str(REPO_ROOT)])
    assert res_hygiene.exit_code == 0
    assert json.loads(res_hygiene.stdout)["is_clean"] is True
