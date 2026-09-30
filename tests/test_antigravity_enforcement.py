# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit, CLI, and MCP Integration Tests for Vietnamese Civil Judgment Enforcement Suite (Phase 116)."""

import json
import pytest
from typer.testing import CliRunner

from src.core.enforcement_engine import EnforcementEngine
from src.cli.commands.enforcement_command import enforcement_app
from scripts.mcp_server import (
    handle_enforcement_dossier,
    handle_enforcement_verify,
    handle_enforcement_coerce,
    handle_enforcement_distribute,
    handle_enforcement_list,
    handle_enforcement_status,
)
from src.core.mcp_server import MekongMcpServer


@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "enforcement_test.db"
    return EnforcementEngine(db_path=str(db_file))


class TestEnforcementEngine:
    def test_create_judgment_dossier_valid(self, temp_engine):
        res = temp_engine.create_judgment_dossier(
            judgment_title="Bản án 25/2026/KDTM-ST Tranh chấp hợp đồng mua bán thép",
            creditor_name="Tập đoàn Thép Hòa Phát",
            debtor_name="Công ty Xây dựng Tiến Hưng",
            total_claim_vnd=12_000_000_000.0,
            judgment_type="COURT_COMMERCIAL",
            enforcement_agency="Cục THADS TP. Đà Nẵng",
            judgment_date="2026-05-10",
        )
        assert res["id"].startswith("DOS-")
        assert res["judgment_title"] == "Bản án 25/2026/KDTM-ST Tranh chấp hợp đồng mua bán thép"
        assert res["creditor_name"] == "Tập đoàn Thép Hòa Phát"
        assert res["debtor_name"] == "Công ty Xây dựng Tiến Hưng"
        assert res["total_claim_vnd"] == 12_000_000_000.0
        assert res["judgment_type"] == "COURT_COMMERCIAL"
        assert res["status"] == "VOLUNTARY_PENDING"
        assert res["voluntary_deadline"] is not None

    def test_create_judgment_dossier_invalid_claim(self, temp_engine):
        with pytest.raises(ValueError, match="strictly positive"):
            temp_engine.create_judgment_dossier(
                judgment_title="Invalid Claim",
                creditor_name="Creditor",
                debtor_name="Debtor",
                total_claim_vnd=0.0,
            )

    def test_create_judgment_dossier_invalid_type(self, temp_engine):
        with pytest.raises(ValueError, match="Invalid judgment type"):
            temp_engine.create_judgment_dossier(
                judgment_title="Invalid Type",
                creditor_name="Creditor",
                debtor_name="Debtor",
                total_claim_vnd=1_000_000.0,
                judgment_type="UNKNOWN_TYPE",
            )

    def test_verify_debtor_condition_solvent(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Test Dossier Solvent",
            creditor_name="Creditor A",
            debtor_name="Debtor B",
            total_claim_vnd=5_000_000_000.0,
        )
        res = temp_engine.verify_debtor_condition(
            dossier_id=dossier["id"],
            verified_assets_vnd=8_000_000_000.0,
            is_solvent=True,
            bank_account_frozen=True,
            notes="Phát hiện tài khoản BIDV có số dư 3 tỷ và 1 xe tải",
        )
        assert res["id"].startswith("VER-")
        assert res["is_solvent"] is True
        assert res["bank_account_frozen"] is True
        assert res["exit_ban_imposed"] is False

        # Verify dossier status updated to COERCIVE_ENFORCING
        with temp_engine._get_connection() as conn:
            row = conn.execute("SELECT status FROM judgment_dossiers WHERE id = ?", (dossier["id"],)).fetchone()
            assert row["status"] == "COERCIVE_ENFORCING"

    def test_verify_debtor_condition_insolvent(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Test Dossier Insolvent",
            creditor_name="Creditor C",
            debtor_name="Debtor D",
            total_claim_vnd=10_000_000_000.0,
        )
        res = temp_engine.verify_debtor_condition(
            dossier_id=dossier["id"],
            verified_assets_vnd=0.0,
            is_solvent=False,
            exit_ban_imposed=True,
            notes="Người phải THA không còn tài sản tại địa phương",
        )
        assert res["is_solvent"] is False
        assert res["exit_ban_imposed"] is True

        with temp_engine._get_connection() as conn:
            row = conn.execute("SELECT status FROM judgment_dossiers WHERE id = ?", (dossier["id"],)).fetchone()
            assert row["status"] == "SUSPENDED_NO_CONDITIONS"

    def test_verify_debtor_condition_nonexistent_dossier(self, temp_engine):
        with pytest.raises(ValueError, match="not found"):
            temp_engine.verify_debtor_condition("DOS-NONEXISTENT", 1000.0, True)

    def test_verify_debtor_condition_negative_assets(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            "Test", "Creditor", "Debtor", 1_000_000.0
        )
        with pytest.raises(ValueError, match="cannot be negative"):
            temp_engine.verify_debtor_condition(dossier["id"], -500.0, True)

    def test_order_coercive_measure_valid(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Test Coercive Dossier",
            creditor_name="Bank Alpha",
            debtor_name="Enterprise Beta",
            total_claim_vnd=20_000_000_000.0,
        )
        res = temp_engine.order_coercive_measure(
            dossier_id=dossier["id"],
            measure_type="ASSET_DISTRAINT",
            target_description="Kê biên quyền sử dụng 5,000m2 đất tại KCN Tân Bình",
            estimated_value_vnd=25_000_000_000.0,
        )
        assert res["id"].startswith("COE-")
        assert res["measure_type"] == "ASSET_DISTRAINT"
        assert res["estimated_value_vnd"] == 25_000_000_000.0
        assert res["status"] == "EXECUTED"

    def test_order_coercive_measure_bank_freeze(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            "Test Freeze", "Creditor", "Debtor", 5_000_000_000.0
        )
        res = temp_engine.order_coercive_measure(
            dossier_id=dossier["id"],
            measure_type="BANK_FREEZE",
            target_description="Phong tỏa tài khoản Techcombank số 1903xxx",
            estimated_value_vnd=3_000_000_000.0,
        )
        assert res["measure_type"] == "BANK_FREEZE"

    def test_order_coercive_measure_invalid_type(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            "Test", "Creditor", "Debtor", 1_000_000.0
        )
        with pytest.raises(ValueError, match="Invalid coercive measure"):
            temp_engine.order_coercive_measure(dossier["id"], "INVALID_MEASURE", "Target", 100.0)

    def test_order_coercive_measure_negative_value(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            "Test", "Creditor", "Debtor", 1_000_000.0
        )
        with pytest.raises(ValueError, match="cannot be negative"):
            temp_engine.order_coercive_measure(dossier["id"], "ASSET_DISTRAINT", "Target", -100.0)

    def test_distribute_enforcement_proceeds_full(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Full Distribution Case",
            creditor_name="Creditor X",
            debtor_name="Debtor Y",
            total_claim_vnd=10_000_000_000.0,
        )
        res = temp_engine.distribute_enforcement_proceeds(
            dossier_id=dossier["id"],
            recovered_amount_vnd=15_000_000_000.0,
            enforcement_costs_vnd=200_000_000.0,       # Tier 1
            wages_and_alimony_vnd=500_000_000.0,       # Tier 2
            court_fees_vnd=100_000_000.0,              # Tier 3
            state_fines_vnd=50_000_000.0,              # Tier 4
            secured_claims_vnd=8_000_000_000.0,        # Tier 5
            unsecured_claims_vnd=4_000_000_000.0,      # Tier 6
        )
        # Total claims = 0.2 + 0.5 + 0.1 + 0.05 + 8 + 4 = 12.85B
        # Recovered = 15B -> Remaining = 15 - 12.85 = 2.15B
        assert res["id"].startswith("DIS-")
        assert res["enforcement_costs_paid_vnd"] == 200_000_000.0
        assert res["wages_alimony_paid_vnd"] == 500_000_000.0
        assert res["court_fees_paid_vnd"] == 100_000_000.0
        assert res["state_fines_paid_vnd"] == 50_000_000.0
        assert res["secured_paid_vnd"] == 8_000_000_000.0
        assert res["unsecured_paid_vnd"] == 4_000_000_000.0
        assert res["unsecured_recovery_rate_pct"] == 100.0
        assert res["remaining_balance_vnd"] == 2_150_000_000.0

    def test_distribute_enforcement_proceeds_partial_unsecured(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Partial Unsecured Case",
            creditor_name="Creditor P",
            debtor_name="Debtor Q",
            total_claim_vnd=10_000_000_000.0,
        )
        res = temp_engine.distribute_enforcement_proceeds(
            dossier_id=dossier["id"],
            recovered_amount_vnd=10_000_000_000.0,
            enforcement_costs_vnd=200_000_000.0,       # 0.2B -> remaining 9.8B
            wages_and_alimony_vnd=500_000_000.0,       # 0.5B -> remaining 9.3B
            court_fees_vnd=100_000_000.0,              # 0.1B -> remaining 9.2B
            state_fines_vnd=100_000_000.0,             # 0.1B -> remaining 9.1B
            secured_claims_vnd=7_000_000_000.0,        # 7.0B -> remaining 2.1B
            unsecured_claims_vnd=4_200_000_000.0,      # 4.2B claim, but only 2.1B available -> 50%
        )
        assert res["enforcement_costs_paid_vnd"] == 200_000_000.0
        assert res["secured_paid_vnd"] == 7_000_000_000.0
        assert res["unsecured_paid_vnd"] == 2_100_000_000.0
        assert res["unsecured_recovery_rate_pct"] == 50.0
        assert res["remaining_balance_vnd"] == 0.0

    def test_distribute_enforcement_proceeds_exhausted_at_costs(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            judgment_title="Exhausted Early",
            creditor_name="Creditor",
            debtor_name="Debtor",
            total_claim_vnd=5_000_000_000.0,
        )
        res = temp_engine.distribute_enforcement_proceeds(
            dossier_id=dossier["id"],
            recovered_amount_vnd=100_000_000.0,
            enforcement_costs_vnd=150_000_000.0,
            wages_and_alimony_vnd=200_000_000.0,
        )
        assert res["enforcement_costs_paid_vnd"] == 100_000_000.0
        assert res["wages_alimony_paid_vnd"] == 0.0
        assert res["remaining_balance_vnd"] == 0.0

    def test_distribute_enforcement_proceeds_invalid_amounts(self, temp_engine):
        dossier = temp_engine.create_judgment_dossier(
            "Test", "Creditor", "Debtor", 1_000_000.0
        )
        with pytest.raises(ValueError, match="negative"):
            temp_engine.distribute_enforcement_proceeds(dossier["id"], -100.0)

    def test_list_enforcement_records_and_telemetry(self, temp_engine):
        d = temp_engine.create_judgment_dossier("List Dossier", "Creditor", "Debtor", 8e9)
        temp_engine.verify_debtor_condition(d["id"], 5e9, True, True, False, True, "Verified")
        temp_engine.order_coercive_measure(d["id"], "BANK_FREEZE", "Techcombank", 3e9)
        temp_engine.distribute_enforcement_proceeds(d["id"], 4e9, 1e8, 2e8, 5e7, 0.0, 2e9, 1e9)

        all_records = temp_engine.list_enforcement_records("all")
        assert len(all_records["dossiers"]) == 1
        assert len(all_records["verifications"]) == 1
        assert len(all_records["measures"]) == 1
        assert len(all_records["distributions"]) == 1

        dossier_records = temp_engine.list_enforcement_records("dossiers")
        assert "dossiers" in dossier_records
        assert "verifications" not in dossier_records

        telemetry = temp_engine.get_enforcement_telemetry()
        assert telemetry["status"] == "HEALTHY"
        assert telemetry["dossiers"]["total_dossiers"] == 1
        assert telemetry["debtor_verifications"]["total_verifications"] == 1
        assert telemetry["debtor_verifications"]["exit_bans_imposed"] == 1
        assert telemetry["coercive_measures"]["total_measures"] == 1
        assert telemetry["coercive_measures"]["total_distrained_value_vnd"] == 3e9
        assert telemetry["proceeds_distributions"]["total_distributions"] == 1
        assert telemetry["proceeds_distributions"]["total_recovered_vnd"] == 4e9


class TestEnforcementCli:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_main_dashboard(self):
        res = self.runner.invoke(enforcement_app, [])
        assert res.exit_code == 0
        assert "THI HÀNH ÁN DÂN SỰ" in res.output or "THADS" in res.output

    def test_cli_main_dashboard_json(self):
        res = self.runner.invoke(enforcement_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"
        assert "dossiers" in data

    def test_cli_dossier(self):
        res = self.runner.invoke(
            enforcement_app,
            [
                "dossier",
                "Bản án 45/2026/KDTM-ST Tranh chấp hợp đồng thi công",
                "--creditor", "Công ty Xây dựng Hòa Bình",
                "--debtor", "Công ty CP Bất động sản Nam Long",
                "--claim", "25000000000",
                "--type", "COURT_COMMERCIAL",
                "--agency", "Cục THADS TP.HCM",
            ],
        )
        assert res.exit_code == 0
        assert "THỤ LÝ HỒ SƠ THI HÀNH ÁN" in res.output
        assert "Công ty Xây dựng Hòa Bình" in res.output

    def test_cli_dossier_json(self):
        res = self.runner.invoke(
            enforcement_app,
            [
                "dossier",
                "Phán quyết Trọng tài VIAC 12/2026",
                "--creditor", "Logistics A",
                "--debtor", "Trading B",
                "--claim", "8000000000",
                "--type", "ARBITRAL_AWARD",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["judgment_type"] == "ARBITRAL_AWARD"
        assert data["total_claim_vnd"] == 8_000_000_000.0

    def test_cli_verify(self):
        # Create dossier first
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Verify Test", "Bank", "Borrower", 5e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "verify",
                dos["id"],
                "--assets", "6000000000",
                "--solvent",
                "--bank-frozen",
                "--exit-ban",
                "--notes", "Tài sản gồm căn hộ và tài khoản ngân hàng",
            ],
        )
        assert res.exit_code == 0
        assert "KẾT QUẢ XÁC MINH ĐIỀU KIỆN THI HÀNH ÁN" in res.output
        assert "CÓ ĐIỀU KIỆN THI HÀNH ÁN" in res.output

    def test_cli_verify_json(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Verify JSON Test", "Bank", "Borrower", 3e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "verify",
                dos["id"],
                "--assets", "1000000000",
                "--insolvent",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_solvent"] is False

    def test_cli_coerce(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Coerce Test", "Creditor", "Debtor", 10e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "coerce",
                dos["id"],
                "--measure", "ASSET_DISTRAINT",
                "--target", "Kê biên nhà xưởng tại Long An",
                "--value", "12000000000",
            ],
        )
        assert res.exit_code == 0
        assert "QUYẾT ĐỊNH CƯỠNG CHẾ THI HÀNH ÁN" in res.output
        assert "ASSET_DISTRAINT" in res.output

    def test_cli_coerce_json(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Coerce JSON Test", "Creditor", "Debtor", 4e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "coerce",
                dos["id"],
                "--measure", "BANK_FREEZE",
                "--target", "Phong tỏa TK VietinBank",
                "--value", "4000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["measure_type"] == "BANK_FREEZE"

    def test_cli_distribute(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Distribute Test", "Creditor", "Debtor", 15e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "distribute",
                dos["id"],
                "--recovered", "12000000000",
                "--costs", "200000000",
                "--wages", "500000000",
                "--court-fees", "100000000",
                "--state-fines", "50000000",
                "--secured", "8000000000",
                "--unsecured", "5000000000",
            ],
        )
        assert res.exit_code == 0
        assert "KẾ HOẠCH PHÂN BỔ TIỀN THI HÀNH ÁN" in res.output

    def test_cli_distribute_json(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "CLI Distribute JSON Test", "Creditor", "Debtor", 8e9
        )
        res = self.runner.invoke(
            enforcement_app,
            [
                "distribute",
                dos["id"],
                "--recovered", "9000000000",
                "--secured", "6000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["recovered_amount_vnd"] == 9_000_000_000.0

    def test_cli_list(self):
        res = self.runner.invoke(enforcement_app, ["list", "all"])
        assert res.exit_code == 0

    def test_cli_list_json(self):
        res = self.runner.invoke(enforcement_app, ["list", "all", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, dict)

    def test_cli_status(self):
        res = self.runner.invoke(enforcement_app, ["status"])
        assert res.exit_code == 0
        assert "CHỈ SỐ TELEMETRY" in res.output

    def test_cli_status_json(self):
        res = self.runner.invoke(enforcement_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"


class TestEnforcementMcp:
    def test_scripts_mcp_dossier(self):
        res_str = handle_enforcement_dossier({
            "judgment_title": "MCP Enforcement Case",
            "creditor_name": "MCP Creditor",
            "debtor_name": "MCP Debtor",
            "total_claim_vnd": 6.5e9,
            "judgment_type": "COURT_COMMERCIAL",
        })
        data = json.loads(res_str)
        assert data["judgment_title"] == "MCP Enforcement Case"
        assert data["status"] == "VOLUNTARY_PENDING"

    def test_scripts_mcp_verify(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "MCP Verify", "Creditor", "Debtor", 5e9
        )
        res_str = handle_enforcement_verify({
            "dossier_id": dos["id"],
            "verified_assets_vnd": 7e9,
            "is_solvent": True,
            "bank_account_frozen": True,
        })
        data = json.loads(res_str)
        assert data["dossier_id"] == dos["id"]
        assert data["is_solvent"] is True

    def test_scripts_mcp_coerce(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "MCP Coerce", "Creditor", "Debtor", 8e9
        )
        res_str = handle_enforcement_coerce({
            "dossier_id": dos["id"],
            "measure_type": "EQUITY_SEIZURE",
            "target_description": "Kê biên 500,000 cổ phần",
            "estimated_value_vnd": 5e9,
        })
        data = json.loads(res_str)
        assert data["measure_type"] == "EQUITY_SEIZURE"

    def test_scripts_mcp_distribute(self):
        dos = EnforcementEngine().create_judgment_dossier(
            "MCP Distribute", "Creditor", "Debtor", 10e9
        )
        res_str = handle_enforcement_distribute({
            "dossier_id": dos["id"],
            "recovered_amount_vnd": 12e9,
            "secured_claims_vnd": 8e9,
            "unsecured_claims_vnd": 3e9,
        })
        data = json.loads(res_str)
        assert data["secured_paid_vnd"] == 8e9

    def test_scripts_mcp_list(self):
        res_str = handle_enforcement_list({"category": "all", "limit": 10})
        data = json.loads(res_str)
        assert isinstance(data, dict)

    def test_scripts_mcp_status(self):
        res_str = handle_enforcement_status({})
        data = json.loads(res_str)
        assert data["status"] == "HEALTHY"

    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer()
        assert hasattr(server, "_handle_enforcement_dossier")
        assert hasattr(server, "_handle_enforcement_verify")
        assert hasattr(server, "_handle_enforcement_coerce")
        assert hasattr(server, "_handle_enforcement_distribute")
        assert hasattr(server, "_handle_enforcement_list")
        assert hasattr(server, "_handle_enforcement_status")

        status_str = server._handle_enforcement_status()
        status_data = json.loads(status_str)
        assert status_data["status"] == "HEALTHY"
