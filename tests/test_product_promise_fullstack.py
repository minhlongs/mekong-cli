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

    def test_all_197_commands_execute_in_process_without_fallback(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            dispatcher = CliCommandDispatcher(evidence_store=store)
            ledger = dispatcher.ledger
            for entry in ledger.list_all():
                cmd_name = entry["name"]
                res = dispatcher.dispatch(cmd_name, {"subcommand": "status"})
                assert res["status"] == "COMPLETED", f"Command {cmd_name} failed: {res.get('output')}"
                verifier = res["domain_verification"].get("verifier", "")
                assert verifier != "FALLBACK_SCHEMA_VERIFIER", f"Command {cmd_name} hit fallback verifier"
                assert verifier != "ENGINE_DISPATCHED", f"Command {cmd_name} hit uncalled engine verifier"
                assert res["domain_verification"]["status"] == "PASSED"

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
        # 1. 0 taxable income -> 0 tax
        res0 = verify_pit_dual_path(0, 0)
        assert res0["status"] == "PASSED"
        assert res0["bracket"] == 0

        # 2. Bracket 1: 5M taxable -> 5% = 250,000 VND
        res1 = verify_pit_dual_path(5_000_000, 250_000)
        assert res1["status"] == "PASSED"
        assert res1["bracket"] == 1

        # 3. Bracket 4: 25M taxable -> 20% * 25M - 1.65M = 3,350,000 VND
        res4 = verify_pit_dual_path(25_000_000, 3_350_000)
        assert res4["status"] == "PASSED"
        assert res4["bracket"] == 4

        # 4. Bracket 7: 100M taxable -> 35% * 100M - 9.85M = 25,150,000 VND
        res7 = verify_pit_dual_path(100_000_000, 25_150_000)
        assert res7["status"] == "PASSED"
        assert res7["bracket"] == 7

        # 5. Intentional tamper detection
        tampered = verify_pit_dual_path(25_000_000, 3_000_000)
        assert tampered["status"] == "FAILED"

    def test_cit_calculation_standard_and_sme(self) -> None:
        # Standard rate 20% (revenue > 3B VND)
        res_std = verify_cit_calculation(
            annual_revenue_vnd=5_000_000_000,
            taxable_profit_vnd=1_000_000_000,
            reported_tax_vnd=200_000_000,
            is_sme_incentive=False,
        )
        assert res_std["status"] == "PASSED"
        assert res_std["applied_rate_pct"] == 20

        # SME rate 17% (revenue <= 3B VND)
        res_sme = verify_cit_calculation(
            annual_revenue_vnd=2_500_000_000,
            taxable_profit_vnd=500_000_000,
            reported_tax_vnd=85_000_000,
            is_sme_incentive=True,
        )
        assert res_sme["status"] == "PASSED"
        assert res_sme["applied_rate_pct"] == 17

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
        # Salary 60M > 46.8M cap
        # Capped BHXH = 46.8M
        # Employee expected = 46.8M * 9.5% + 60M * 1% = 4,446,000 + 600,000 = 5,046,000
        # Employer expected = 46.8M * 20.5% + 60M * 1% = 9,594,000 + 600,000 = 10,194,000
        res = verify_bhxh_contribution(
            raw_salary_vnd=60_000_000,
            reported_employee_vnd=5_046_000,
            reported_employer_vnd=10_194_000,
            include_kpcd=False,
        )
        assert res["status"] == "PASSED"
        assert res["capped_salary_bhxh_vnd"] == 46_800_000

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
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = CliEvidenceStore(db_path=tmp.name)
            gates = store.list_gates()
            assert len(gates) == 6

            # Check that initial state is LOCKED (Tier 2 rule)
            for g in gates:
                assert g["status"] == "LOCKED"

            # Reconcile first-revenue (L3)
            unlocked = store.unlock_gate_with_reconciliation(
                gate_id="first-revenue",
                transaction_id="TXN-MBBANK-20261027-999",
                evidence_ref="https://vietqr.vn/reconciled/TXN-MBBANK-20261027-999",
            )
            assert unlocked is True

            updated_gates = store.list_gates()
            l3_gate = next(g for g in updated_gates if g["gate_id"] == "first-revenue")
            assert l3_gate["status"] == "SEALED_VERIFIED"
            assert l3_gate["reconciled_transaction_id"] == "TXN-MBBANK-20261027-999"


# ---------------------------------------------------------------------------
# Test Group 5: FastAPI Gateway Endpoints
# ---------------------------------------------------------------------------


class TestFastApiCliPromiseRoutes:
    """Verifies that the REST API responds to Next.js proxy queries correctly."""

    @pytest.fixture(autouse=True)
    def setup_client(self) -> None:
        self.client = TestClient(app)

    def test_get_capabilities_endpoint(self) -> None:
        resp = self.client.get("/v1/cli/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["integrity"]["valid"] is True
        assert data["count"] == 197
        assert data["summary"]["total_command_groups"] == 197

    def test_post_runs_endpoint(self) -> None:
        resp = self.client.post(
            "/v1/cli/runs",
            json={
                "command_id": "bhxh",
                "params": {"subcommand": "calculate", "salary": 25_000_000, "region": 1},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert "receipt" in data
        assert data["receipt"]["signature"] is not None

        # Fetch run details
        run_id = data["run_id"]
        run_resp = self.client.get(f"/v1/cli/runs/{run_id}")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["run_id"] == run_id

    def test_post_receipts_verify_endpoint(self) -> None:
        # Create a run first
        run_resp = self.client.post(
            "/v1/cli/runs",
            json={
                "command_id": "vietqr",
                "params": {"subcommand": "generate", "amount": 1_000_000, "memo": "DEMO-RUN"},
            },
        )
        receipt = run_resp.json()["receipt"]

        # Verify receipt via API
        verif_resp = self.client.post("/v1/cli/receipts/verify", json={"receipt": receipt})
        assert verif_resp.status_code == 200
        assert verif_resp.json()["valid"] is True

        # Tampered receipt verification
        tampered_receipt = copy.deepcopy(receipt)
        tampered_receipt["output_sha256"] = "deadbeef" * 8
        bad_verif = self.client.post("/v1/cli/receipts/verify", json={"receipt": tampered_receipt})
        assert bad_verif.status_code == 200
        assert bad_verif.json()["valid"] is False

    def test_get_gates_and_reconciliation_endpoint(self) -> None:
        gates_resp = self.client.get("/v1/cli/gates")
        assert gates_resp.status_code == 200
        gates_data = gates_resp.json()
        assert gates_data["total_gates"] == 6

        # Reconcile gate
        rec_resp = self.client.post(
            "/v1/cli/gates/mvp-live/reconcile",
            json={
                "transaction_id": "TXN-BUILD-PASS-001",
                "evidence_ref": "git:sha:commit-proof",
            },
        )
        assert rec_resp.status_code == 200
        assert rec_resp.json()["status"] == "SEALED_VERIFIED"
