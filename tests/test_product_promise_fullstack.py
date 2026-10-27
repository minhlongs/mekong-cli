# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Full-Stack Verification Suite for Mekong CLI Product Promise & Canonical Contracts.

Validates:
1. 197 capability entries across 10 departments and 6 layers (L0–L5) with zero missing contract fields.
2. Dual-path quantitative statutory verifiers for PIT (TNCN), CIT (TNDN), VAT (GTGT),
   VAS double-entry balance, BHXH, VietQR EMVCo CRC16, and administrative sanctions.
3. Cryptographic HMAC-SHA256 receipt signing, canonical RFC 8785 JSON serialization, and tamper detection.
4. SQLite WAL persistence for execution runs, signed receipts, L0–L5 milestone gates, and double-entry ledger.
5. In-process dispatching for core business commands without shell subprocessing.
6. FastAPI REST endpoints: capabilities, runs, receipt verification, and two-tier milestone gate status.
"""

from __future__ import annotations

import copy
import tempfile

import pytest
from starlette.testclient import TestClient

from src.core.capability_ledger import CapabilityLedger
from src.core.cli_command_dispatcher import CliCommandDispatcher
from src.core.cli_evidence_store import CliEvidenceStore
from src.core.receipt_signer import (
    build_command_receipt,
    canonical_json_bytes,
    verify_receipt_signature,
)
from src.core.statutory_verifiers import (
    verify_admin_sanction_fine,
    verify_bhxh_contribution,
    verify_cit_calculation,
    verify_pit_dual_path,
    verify_vas_double_entry,
    verify_vat_calculation,
    verify_vietqr_emvco,
)
from src.gateway import app


# ---------------------------------------------------------------------------
# Test Group 1: 197-Command Capability Ledger Contract Integrity
# ---------------------------------------------------------------------------


class TestCapabilityLedgerIntegrity:
    """Verifies that the capability ledger matches the advertised product promise exactly."""

    def test_ledger_total_count_and_integrity(self) -> None:
        ledger = CapabilityLedger()
        check = ledger.validate_integrity()
        assert check["valid"] is True, f"Integrity errors found: {check['errors']}"
        assert check["total_entries"] == 197

    def test_maturity_tiers_breakdown(self) -> None:
        ledger = CapabilityLedger()
        stats = ledger.get_summary_stats()
        tiers = stats["by_maturity_tier"]
        assert "REAL_VERIFIED" in tiers
        assert tiers["REAL_VERIFIED"] == 197
        assert sum(tiers.values()) == 197

    def test_all_197_commands_dispatch_in_process_without_a_synthetic_success(self) -> None:
        """Every advertised command is dispatched in-process and measured honestly.

        This test used to require ``COMPLETED`` from all 197 commands. That was the
        catalog-only-counts-as-executed fake: the dispatcher answered unmapped
        commands with a generated artifact and a PASSED verifier. What must hold
        now is stronger and measurable:

        * the advertised denominator is 197 (no command was deleted to make the
          ratio look better);
        * no dispatch is answered by the removed fail-open fallback
          (``FALLBACK_SCHEMA_VERIFIER``) or by the "engine was dispatched, trust
          me" verifier (``ENGINE_DISPATCHED``);
        * a command that is not completed carries a real reason and its
          verification is not green;
        * a command with no bound handler reports ``NOT_IMPLEMENTED`` instead of
          a success payload.
        """
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)
            entries = dispatcher.ledger.list_all()
            assert len(entries) == 197

            measured: dict[str, dict[str, object]] = {}
            for entry in entries:
                name = entry["name"]
                res = dispatcher.dispatch(name, {"subcommand": "status"})
                verification = res["domain_verification"]
                assert verification.get("verifier") != "FALLBACK_SCHEMA_VERIFIER", name
                assert verification.get("verifier") != "ENGINE_DISPATCHED", name
                assert res["status"] in {
                    "COMPLETED", "FAILED", "NOT_IMPLEMENTED", "NEEDS_RECONCILIATION",
                }, (name, res["status"])
                if res["status"] == "COMPLETED":
                    assert verification["status"] == "PASSED", name
                else:
                    # Never a green verification on an unfinished run, and never a
                    # bare failure without a machine-readable reason.
                    assert verification["status"] != "PASSED", name
                    assert verification.get("detail") or (res.get("output") or {}).get("reason") \
                        or (res.get("output") or {}).get("error"), name
                measured[name] = res

            completed = [n for n, r in measured.items() if r["status"] == "COMPLETED"]
            unresolved = [n for n, r in measured.items() if r["status"] != "COMPLETED"]
            # Measured today: all 197 advertised commands dispatch to a real
            # handler. ``gateway`` and ``system`` used to fail here — not because
            # of the product but because tests/conftest.py replaced
            # ``src.api.raas_router.router`` with a bare MagicMock, which trips
            # FastAPI's ``include_router`` assertion when the gateway module is
            # imported a second time inside the test session.
            assert len(completed) == 197, f"advertised commands regressed: {unresolved}"
            assert unresolved == []

    def test_unbound_command_reports_not_implemented(self) -> None:
        """Regression: the removed fail-open fallback must not come back."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)
            output, verification = dispatcher._execute_in_process(
                "definitely-not-a-bound-command", {"subcommand": "status"}
            )
            assert output["status"] == "NOT_IMPLEMENTED"
            assert output["next_step"]
            assert verification["verifier"] == "NO_HANDLER_BOUND"
            assert verification["status"] == "NOT_IMPLEMENTED"
            assert "deliverable" not in output
            assert "EXECUTED" not in str(output)

    def test_all_six_layers_represented(self) -> None:
        ledger = CapabilityLedger()
        stats = ledger.get_summary_stats()
        layers = stats["by_layer"]
        for expected in ("L0", "L1", "L2", "L3", "L4", "L5"):
            assert expected in layers
            assert layers[expected] > 0

    def test_command_resolution_by_alias_and_prefix(self) -> None:
        ledger = CapabilityLedger()
        # Direct name
        thue = ledger.resolve_command("thue")
        assert thue is not None
        assert thue["name"] == "thue"

        # Prefix 'mekong thue'
        thue_prefix = ledger.resolve_command("mekong thue")
        assert thue_prefix is not None
        assert thue_prefix["name"] == "thue"

        # Alias resolution
        vphc_alias = ledger.resolve_command("vphc")
        assert vphc_alias is not None
        assert vphc_alias["name"] == "adminsanction"

        cfo_alias = ledger.resolve_command("finance")
        assert cfo_alias is not None
        assert cfo_alias["name"] == "cfo"


# ---------------------------------------------------------------------------
# Test Group 2: Dual-Path Quantitative Statutory Verifiers
# ---------------------------------------------------------------------------


class TestStatutoryVerifiers:
    """Validates mathematical and regulatory precision against Vietnamese law."""

    def test_pit_dual_path_shortcut_formula(self) -> None:
        """Shortcut table of the *7-bracket* schedule in force until 31/12/2025."""
        pre_2026 = "2025-10-01"

        # 1. 0 taxable income -> 0 tax
        res0 = verify_pit_dual_path(0, 0, as_of=pre_2026)
        assert res0["status"] == "PASSED"
        assert res0["bracket"] == 0
        assert res0["bracket_count"] == 7

        # 2. Bracket 1: 5M taxable -> 5% = 250,000 VND
        res1 = verify_pit_dual_path(5_000_000, 250_000, as_of=pre_2026)
        assert res1["status"] == "PASSED"
        assert res1["bracket"] == 1

        # 3. Bracket 4: 25M taxable -> 20% * 25M - 1.65M = 3,350,000 VND
        res4 = verify_pit_dual_path(25_000_000, 3_350_000, as_of=pre_2026)
        assert res4["status"] == "PASSED"
        assert res4["bracket"] == 4

        # 4. Bracket 7: 100M taxable -> 35% * 100M - 9.85M = 25,150,000 VND
        res7 = verify_pit_dual_path(100_000_000, 25_150_000, as_of=pre_2026)
        assert res7["status"] == "PASSED"
        assert res7["bracket"] == 7

        # 5. Intentional tamper detection
        tampered = verify_pit_dual_path(25_000_000, 3_000_000, as_of=pre_2026)
        assert tampered["status"] == "FAILED"

    def test_pit_dual_path_luat_109_2025_schedule(self) -> None:
        """From tax year 2026 the 5-bracket schedule of Luật 109/2025/QH15 applies.

        A verifier pinned to the old table would reject a correct 2026 payslip,
        and a calculator pinned to the new table would under-tax 2025 income —
        both directions are asserted here.
        """
        # 13.3M taxable -> 10M @ 5% + 3.3M @ 10% = 830,000 VND (bracket 2 of 5)
        res2 = verify_pit_dual_path(13_300_000, 830_000, as_of="2026-10-01")
        assert res2["status"] == "PASSED"
        assert res2["bracket"] == 2
        assert res2["bracket_count"] == 5
        assert "109/2025" in res2["rule_version"]

        # 120M taxable -> 27,500,000 VND (top bracket of the 5-step schedule)
        res5 = verify_pit_dual_path(120_000_000, 27_500_000, as_of="2026-06-01")
        assert res5["status"] == "PASSED"
        assert res5["bracket"] == 5

        # The 2025 answer for the same income is different and must be rejected
        # when it is presented as a 2026 calculation.
        cross_period = verify_pit_dual_path(13_300_000, 1_245_000, as_of="2026-10-01")
        assert cross_period["status"] == "FAILED"

    def test_cit_calculation_standard_and_sme(self) -> None:
        """Điều 10 Luật Thuế TNDN 2025 (67/2025/QH15), effective 01/10/2025."""
        law_67 = "2026-06-30"

        # Standard rate 20% (revenue > 50B VND)
        res_std = verify_cit_calculation(
            annual_revenue_vnd=80_000_000_000,
            taxable_profit_vnd=1_000_000_000,
            reported_tax_vnd=200_000_000,
            is_sme_incentive=True,
            as_of=law_67,
        )
        assert res_std["status"] == "PASSED"
        assert res_std["applied_rate_pct"] == 20
        assert res_std["rate_tier"] == "STANDARD_20"

        # 15% for annual revenue <= 3B VND
        res_micro = verify_cit_calculation(
            annual_revenue_vnd=2_500_000_000,
            taxable_profit_vnd=500_000_000,
            reported_tax_vnd=75_000_000,
            is_sme_incentive=True,
            as_of=law_67,
        )
        assert res_micro["status"] == "PASSED"
        assert res_micro["applied_rate_pct"] == 15
        assert res_micro["rate_tier"] == "SME_SMALL_15"

        # 17% for 3B < revenue <= 50B VND
        res_small = verify_cit_calculation(
            annual_revenue_vnd=20_000_000_000,
            taxable_profit_vnd=2_000_000_000,
            reported_tax_vnd=340_000_000,
            is_sme_incentive=True,
            as_of=law_67,
        )
        assert res_small["status"] == "PASSED"
        assert res_small["applied_rate_pct"] == 17
        assert res_small["rate_tier"] == "SME_MEDIUM_17"

        # The old 17%-at-3B reading is wrong: 2.5B revenue x 500M profit is 75M,
        # not 85M, and a report of 85M must fail verification.
        assert verify_cit_calculation(
            annual_revenue_vnd=2_500_000_000, taxable_profit_vnd=500_000_000,
            reported_tax_vnd=85_000_000, is_sme_incentive=True, as_of=law_67,
        )["status"] == "FAILED"

        # Before 01/10/2025 the preferential tiers do not apply: 20% standard.
        res_prior = verify_cit_calculation(
            annual_revenue_vnd=2_500_000_000,
            taxable_profit_vnd=500_000_000,
            reported_tax_vnd=100_000_000,
            is_sme_incentive=True,
            as_of="2025-06-30",
        )
        assert res_prior["status"] == "PASSED"
        assert res_prior["applied_rate_pct"] == 20

    def test_vat_decimal_calculation(self) -> None:
        res = verify_vat_calculation(
            subtotal_vnd=100_000_000,
            vat_rate_pct=10,
            reported_vat_vnd=10_000_000,
            reported_total_vnd=110_000_000,
        )
        assert res["status"] == "PASSED"

        # Invalid rate rejected
        bad_rate = verify_vat_calculation(100_000_000, 15, 15_000_000, 115_000_000)
        assert bad_rate["status"] == "FAILED"

    def test_vas_double_entry_balance(self) -> None:
        lines = [
            {"account": "131", "debit": 110_000_000, "credit": 0},
            {"account": "511", "debit": 0, "credit": 100_000_000},
            {"account": "3331", "debit": 0, "credit": 10_000_000},
        ]
        res = verify_vas_double_entry(110_000_000, 110_000_000, lines)
        assert res["status"] == "PASSED"

        # Imbalance fails
        unbalanced = verify_vas_double_entry(110_000_000, 100_000_000, lines)
        assert unbalanced["status"] == "FAILED"

    def test_bhxh_statutory_cap_nd73(self) -> None:
        """NĐ 73/2024 period (until 30/06/2026): reference salary 2,340,000đ."""
        # Salary 60M > 46.8M cap (20 x 2,340,000đ); BHTN cap = 20 x 4,960,000đ (vùng I)
        # Employee expected = 46.8M * 9.5% + 60M * 1% = 4,446,000 + 600,000 = 5,046,000
        # Employer expected = 46.8M * 20.5% + 60M * 1% = 9,594,000 + 600,000 = 10,194,000
        res = verify_bhxh_contribution(
            raw_salary_vnd=60_000_000,
            reported_employee_vnd=5_046_000,
            reported_employer_vnd=10_194_000,
            include_kpcd=False,
            as_of="2025-06-01",
        )
        assert res["status"] == "PASSED"
        assert res["capped_salary_bhxh_vnd"] == 46_800_000
        assert res["cap_bhtn_vnd"] == 99_200_000

    def test_bhxh_statutory_cap_nd161_2026(self) -> None:
        """NĐ 161/2026 (from 01/07/2026): reference salary 2,530,000đ -> cap 50.6M.

        NĐ 293/2025 also lifted the vùng I minimum wage to 5,310,000đ from
        01/01/2026, so the BHTN ceiling becomes 106,200,000đ.
        """
        res = verify_bhxh_contribution(
            raw_salary_vnd=60_000_000,
            reported_employee_vnd=5_407_000,   # 50.6M * 9.5% + 60M * 1%
            reported_employer_vnd=11_985_000,  # 50.6M * 20.5% + 60M * 1% + 50.6M * 2% KPCĐ
            include_kpcd=True,
            region=1,
            as_of="2026-08-01",
        )
        assert res["status"] == "PASSED"
        assert res["cap_bhxh_bhyt_vnd"] == 50_600_000
        assert res["cap_bhtn_vnd"] == 106_200_000

        # The 2025 numbers must NOT pass as a 2026 calculation.
        stale = verify_bhxh_contribution(
            raw_salary_vnd=60_000_000,
            reported_employee_vnd=5_046_000,
            reported_employer_vnd=10_194_000,
            include_kpcd=False,
            as_of="2026-08-01",
        )
        assert stale["status"] == "FAILED"

    def test_vietqr_emvco_payload_and_crc16(self) -> None:
        # Valid EMVCo format generated from VietQrEngine
        from src.core.vietqr_engine import VietQrEngine
        vqr = VietQrEngine()
        qr_res = vqr.generate_qr(bank="MB", account_number="0988889999", amount_vnd=500_000, memo="TEST")
        payload = qr_res["emvco_payload"]

        verif = verify_vietqr_emvco(payload)
        assert verif["status"] == "PASSED"
        assert verif["has_napas_aid"] is True

        # Corrupted payload fails
        bad_payload = payload[:-4] + "FFFF"
        bad_verif = verify_vietqr_emvco(bad_payload)
        assert bad_verif["status"] == "FAILED"

    def test_admin_sanction_organization_multiplier(self) -> None:
        # Base fine 10M - 20M. Org multiplier 2.0x -> 20M - 40M. Midpoint = 30M.
        # 1 mitigating, 0 aggravating -> -10% of 30M = -3M -> 27M fine.
        res = verify_admin_sanction_fine(
            min_fine_vnd=10_000_000,
            max_fine_vnd=20_000_000,
            entity_type="ORGANIZATION",
            mitigating_count=1,
            aggravating_count=0,
            reported_fine_vnd=27_000_000,
        )
        assert res["status"] == "PASSED"
        assert res["entity_multiplier"] == 2


# ---------------------------------------------------------------------------
# Test Group 3: Cryptographic Receipts & Tamper Detection
# ---------------------------------------------------------------------------


class TestReceiptSigningAndTamperProof:
    """Verifies HMAC-SHA256 signing and RFC 8785 canonical JSON tamper proofing."""

    def test_canonical_json_determinism(self) -> None:
        dict_a = {"z": 1, "a": [3, 2, 1], "m": {"nested": "value"}}
        dict_b = {"a": [3, 2, 1], "m": {"nested": "value"}, "z": 1}
        assert canonical_json_bytes(dict_a) == canonical_json_bytes(dict_b)

    def test_build_and_verify_signature(self) -> None:
        receipt = build_command_receipt(
            run_id="RUN-TEST-001",
            command_id="thue",
            department_id="finance-tax",
            layer_id="L3",
            owner_agent="tax-accountant",
            sop_chain=["STEP-1", "STEP-2"],
            gate_artifact="RECEIPT-TAX.json",
            input_data={"subcommand": "tncn", "gross_income": 30_000_000},
            output_data={"tax_amount": 1_350_000},
            domain_verification={"status": "PASSED"},
        )
        assert receipt["receipt_tier"] == "TIER_1_COMMAND_EXECUTION"
        assert receipt["algorithm"] == "HMAC-SHA256"
        assert len(receipt["signature"]) == 64

        # Verify signature
        receipt_copy = dict(receipt)
        sig = receipt_copy.pop("signature")
        receipt_copy.pop("algorithm")
        assert verify_receipt_signature(receipt_copy, sig) is True

    def test_tamper_detection(self) -> None:
        receipt = build_command_receipt(
            run_id="RUN-TEST-002",
            command_id="thue",
            department_id="finance-tax",
            layer_id="L3",
            owner_agent="tax-accountant",
            sop_chain=[],
            gate_artifact="",
            input_data={"subcommand": "tncn"},
            output_data={"tax_amount": 1_000_000},
            domain_verification={"status": "PASSED"},
        )
        receipt_copy = dict(receipt)
        sig = receipt_copy.pop("signature")
        receipt_copy.pop("algorithm")

        # Malicious modification of output hash or payload
        receipt_copy["output_sha256"] = "tampered_hash_value"
        assert verify_receipt_signature(receipt_copy, sig) is False


# ---------------------------------------------------------------------------
# Test Group 4: In-Process Command Dispatcher & Persistence
# ---------------------------------------------------------------------------


class TestCommandDispatcherAndEvidenceStore:
    """Verifies full execution lifecycle from dispatcher to SQLite WAL persistence."""

    def test_dispatch_thue_tncn(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)

            res = dispatcher.dispatch(
                command_id="thue",
                params={"subcommand": "tncn", "gross_income": 35_000_000, "dependents": 1},
            )
            assert res["status"] == "COMPLETED"
            assert res["output"]["gross_income"] == 35_000_000
            assert res["domain_verification"]["status"] == "PASSED"
            assert res["receipt"]["signature"] is not None

            # Retrieve from SQLite WAL
            saved = store.get_run(res["run_id"])
            assert saved is not None
            assert saved["command_id"] == "thue"
            assert saved["receipt"]["run_id"] == res["run_id"]

    def test_dispatch_ke_toan_journal(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)

            res = dispatcher.dispatch(
                command_id="ke-toan",
                params={"subcommand": "journal", "amount": 20_000_000, "buyer": "Cong Ty ABC"},
            )
            assert res["status"] == "COMPLETED"
            assert res["domain_verification"]["status"] == "PASSED"
            assert res["domain_verification"]["imbalance_vnd"] == 0

    def test_two_tier_company_gates_initial_and_reconciliation(self) -> None:
        """A milestone gate is sealed by *measured* conditions, never by free text.

        This test used to assert that posting any two strings
        (``TXN-MBBANK-20261027-999`` + a URL) sealed ``first-revenue``. That was
        the fake gate: no transaction, no invoice and no tax record existed. The
        store now requires the condition map measured from persisted evidence.
        """
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            gates = store.list_gates()
            assert len(gates) == 6

            # Initial state is LOCKED (Tier 2 rule)
            for g in gates:
                assert g["status"] == "LOCKED"

            # 1. Free-text identifiers alone are not proof -> refused.
            refused = store.unlock_gate_with_reconciliation(
                gate_id="first-revenue",
                transaction_id="TXN-MBBANK-20261027-999",
                evidence_ref="https://vietqr.vn/reconciled/TXN-MBBANK-20261027-999",
            )
            assert refused is False
            still_locked = next(g for g in store.list_gates() if g["gate_id"] == "first-revenue")
            assert still_locked["status"] == "LOCKED"
            assert still_locked["reconciled_transaction_id"] is None

            # 2. A partially met condition set is still refused.
            partial = store.unlock_gate_with_reconciliation(
                gate_id="first-revenue",
                transaction_id="TXN-MBBANK-20261027-999",
                evidence_ref="EV-1",
                verified_conditions={
                    "reconciled_transaction": True,
                    "invoice_linked_to_revenue": False,
                    "tax_accounting_recorded": False,
                },
            )
            assert partial is False
            assert next(g for g in store.list_gates()
                        if g["gate_id"] == "first-revenue")["status"] == "LOCKED"

            # 3. Every condition measured as met -> sealed, references recorded.
            sealed = store.unlock_gate_with_reconciliation(
                gate_id="first-revenue",
                transaction_id="TXN-MBBANK-20261027-999",
                evidence_ref="EV-1",
                verified_conditions={
                    "reconciled_transaction": True,
                    "invoice_linked_to_revenue": True,
                    "tax_accounting_recorded": True,
                },
            )
            assert sealed is True
            l3_gate = next(g for g in store.list_gates() if g["gate_id"] == "first-revenue")
            assert l3_gate["status"] == "SEALED_VERIFIED"
            assert l3_gate["reconciled_transaction_id"] == "TXN-MBBANK-20261027-999"

            # 4. An unknown gate is never created by a reconciliation call.
            assert store.unlock_gate_with_reconciliation(
                gate_id="not-a-gate", transaction_id="T", evidence_ref="E",
                verified_conditions={"anything": True},
            ) is False

    def test_security_ssrf_and_path_traversal_rejection(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)

            # 1. SSRF to loopback / private IP rejected and marks run FAILED
            ssrf_res = dispatcher.dispatch("browse", {"url": "http://127.0.0.1:8000/v1/cli/gates"})
            assert ssrf_res["status"] == "FAILED"
            assert ssrf_res["domain_verification"]["status"] == "FAILED"

            # 2. Argument injection starting with '-' rejected
            arg_inj_res = dispatcher.dispatch("browse", {"url": "-K/etc/passwd"})
            assert arg_inj_res["status"] == "FAILED"
            assert arg_inj_res["domain_verification"]["status"] == "FAILED"

            # 3. Path traversal outside workspace rejected
            trav_res = dispatcher.dispatch("analyze", {"path": "../../../../etc"})
            assert trav_res["status"] == "FAILED"
            assert trav_res["domain_verification"]["status"] == "FAILED"

            # 4. Benchmark iterations clamped safely
            bench_res = dispatcher.dispatch("benchmark", {"suite": "pev", "iterations": 999999})
            assert bench_res["status"] == "COMPLETED"
            assert bench_res["domain_verification"]["status"] == "PASSED"


# ---------------------------------------------------------------------------
# Test Group 5: FastAPI Gateway Endpoints
# ---------------------------------------------------------------------------


class TestFastApiCliPromiseRoutes:
    """REST API: authenticated principal → runtime → verification → evidence.

    The routes are no longer open: an HTTP caller must present a credential, or
    the process must be in explicit single-operator local mode. Runs are executed
    by the shared promise runtime and are scoped to the caller's workspace.
    """

    @pytest.fixture(autouse=True)
    def setup_client(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MEKONG_PROMISE_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("MEKONG_PROMISE_LOCAL_MODE", "1")
        monkeypatch.setenv("MEKONG_WORKSPACE_ID", "ws-api-test")
        monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "test-signing-key-not-a-secret")
        from src.core.promise.service import reset_service

        reset_service()
        self.client = TestClient(app)
        self.tmp_path = tmp_path
        yield
        reset_service()

    def test_capabilities_requires_a_principal(self, monkeypatch) -> None:
        monkeypatch.delenv("MEKONG_PROMISE_LOCAL_MODE", raising=False)
        from src.core.promise.service import reset_service

        reset_service()
        resp = self.client.get("/v1/cli/capabilities")
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "MISSING_CREDENTIAL"

    def test_get_capabilities_endpoint(self) -> None:
        resp = self.client.get("/v1/cli/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["integrity"]["valid"] is True
        assert data["count"] == 197
        assert data["summary"]["total_command_groups"] == 197
        # The advertised ledger is reconciled against the executable registry.
        binding = data["execution_binding"]
        assert binding["advertised_command_groups"] == 197
        assert binding["executable_operations"] >= 20
        executable = [i for i in data["items"] if i["execution_status"] == "EXECUTABLE"]
        assert {i["name"] for i in executable} >= {"thue", "ke-toan", "bhxh", "payroll", "vietqr"}
        # An advertised command without a bound operation is reported, not hidden.
        not_implemented = [i for i in data["items"] if i["execution_status"] == "NOT_IMPLEMENTED"]
        assert len(not_implemented) == 197 - len(executable)

    def test_post_runs_endpoint_executes_real_handler(self) -> None:
        resp = self.client.post(
            "/v1/cli/runs",
            json={
                "command_id": "bhxh",
                "params": {"subcommand": "calculate", "salary": 25_000_000, "region": 1,
                           "contribution_period": "2026-08-01"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert data["op_id"] == "bhxh.calculate"
        assert data["output"]["employee"]["total"] == 2_625_000  # 10.5% of 25M (below the cap)
        assert data["domain_verification"]["business_conditions_met"] is True
        assert data["receipt"]["signature"] is not None
        assert data["receipt"]["signing"]["status"] == "SIGNED"

        run_id = data["run_id"]
        run_resp = self.client.get(f"/v1/cli/runs/{run_id}")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["job"]["run_id"] == run_id
        assert run_data["job"]["status"] == "COMPLETED"
        assert run_data["source"] == "promise_job_store"

        listed = self.client.get("/v1/cli/runs", params={"command_id": "bhxh"})
        assert listed.status_code == 200
        assert any(r["run_id"] == run_id for r in listed.json()["runs"])

    def test_runs_reject_invalid_input_and_unknown_commands(self) -> None:
        bad = self.client.post("/v1/cli/runs", json={
            "command_id": "bhxh",
            "params": {"subcommand": "calculate", "salary": -1, "region": 1},
        })
        assert bad.status_code == 200
        payload = bad.json()
        assert payload["status"] == "FAILED"
        assert payload["error_code"] == "INPUT_INVALID"
        assert payload["receipt"] is None or payload["domain_verification"]["handler_ran"] is False

        unknown = self.client.post("/v1/cli/runs", json={"command_id": "not-a-command"})
        assert unknown.status_code == 404
        assert unknown.json()["detail"]["code"] == "UNKNOWN_COMMAND"

    def test_post_receipts_verify_endpoint(self) -> None:
        run_resp = self.client.post(
            "/v1/cli/runs",
            json={"command_id": "thue",
                  "params": {"subcommand": "tncn", "monthly_income": 35_000_000,
                             "dependents": 1, "tax_period": "2026-10-01"}},
        )
        receipt = run_resp.json()["receipt"]
        assert receipt["receipt_version"] == "2.0.0"

        verif_resp = self.client.post("/v1/cli/receipts/verify", json={"receipt": receipt})
        assert verif_resp.status_code == 200
        body = verif_resp.json()
        assert body["valid"] is True
        assert body["domain_verification"]["business_conditions_met"] is True

        # Tampering with the recorded output digest invalidates the signature.
        tampered = copy.deepcopy(receipt)
        tampered["output_sha256"] = "deadbeef" * 8
        bad = self.client.post("/v1/cli/receipts/verify", json={"receipt": tampered})
        assert bad.status_code == 200
        assert bad.json()["valid"] is False

        # Claiming another signer's key id is rejected too.
        reattributed = copy.deepcopy(receipt)
        reattributed["signing"] = {**receipt["signing"], "key_id": "key-attacker"}
        assert self.client.post(
            "/v1/cli/receipts/verify", json={"receipt": reattributed}
        ).json()["valid"] is False

    def test_gates_are_measured_and_never_sealed_by_free_text(self) -> None:
        gates_resp = self.client.get("/v1/cli/gates")
        assert gates_resp.status_code == 200
        gates_data = gates_resp.json()
        assert gates_data["gate_tier"] == "TIER_2_COMPANY_MILESTONE"
        assert gates_data["total_gates"] == 7
        assert gates_data["unlocked_count"] == 0
        assert all(g["status"] != "SEALED_VERIFIED" for g in gates_data["gates"])

        # A green build or any two strings must not seal mvp-live.
        rec = self.client.post(
            "/v1/cli/gates/mvp-live/reconcile",
            json={"transaction_id": "TXN-BUILD-PASS-001", "evidence_ref": "git:sha:commit-proof"},
        )
        assert rec.status_code == 409
        detail = rec.json()["detail"]
        assert detail["code"] in ("EVIDENCE_REFERENCE_UNKNOWN", "GATE_CONDITIONS_UNMET")
        assert detail["status"] != "SEALED_VERIFIED"

        # The gate is still unsealed afterwards.
        after = self.client.get("/v1/cli/gates").json()
        assert after["unlocked_count"] == 0

    def test_first_revenue_gate_seals_only_from_reconciled_evidence(self) -> None:
        """End-to-end over HTTP: invoice → tax record → approved reconciliation → seal."""
        invoice = self.client.post("/v1/cli/runs", json={
            "command_id": "ke-toan",
            "params": {"subcommand": "create_invoice", "amount": 20_000_000,
                       "buyer": "Cong Ty ABC", "seller_tax_code": "0300588569"},
        }).json()
        assert invoice["status"] == "COMPLETED"
        invoice_id = invoice["output"]["invoice_id"]

        self.client.post("/v1/cli/runs", json={
            "command_id": "thue",
            "params": {"subcommand": "gtgt", "amount": 20_000_000, "rate": 10,
                       "tax_period": "2026-10-01"},
        })

        # Without a reconciled transaction the gate stays unmet.
        early = self.client.post("/v1/cli/gates/first-revenue/reconcile", json={
            "transaction_id": invoice["evidence_id"], "evidence_ref": invoice["evidence_id"],
        })
        assert early.status_code == 409
        assert early.json()["detail"]["status"] != "SEALED_VERIFIED"

        paused = self.client.post("/v1/cli/runs", json={
            "command_id": "vietqr",
            "params": {"subcommand": "reconcile_payment", "bank_tx_id": "MB-HTTP-0001",
                       "amount_vnd": 22_000_000, "memo": "HD C25TAA 000001",
                       "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-77431",
                       "invoice_ref": invoice_id},
        }).json()
        assert paused["status"] == "AWAITING_APPROVAL"
        token_id = paused["approval_request"]["approval_token_id"]

        decided = self.client.post(
            f"/v1/cli/runs/{paused['run_id']}/approval/decision",
            json={"token_id": token_id, "decision": "approve", "notes": "sao ke MB 27/10"},
        )
        assert decided.status_code == 200
        approved = decided.json()
        assert approved["status"] == "COMPLETED"
        assert approved["output"]["status"] == "RECONCILED"
        tx_id = approved["output"]["revenue_record"]["tx_id"]

        sealed = self.client.post("/v1/cli/gates/first-revenue/reconcile", json={
            "transaction_id": tx_id, "evidence_ref": approved["evidence_id"],
        })
        assert sealed.status_code == 200, sealed.json()
        body = sealed.json()
        assert body["sealed"] is True
        assert body["status"] == "SEALED_VERIFIED"
        assert all(c["met"] for c in body["conditions"])

        gates = self.client.get("/v1/cli/gates").json()
        assert gates["unlocked_count"] == 1
