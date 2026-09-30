"""
Comprehensive test battery for Vietnamese State Budget, Fiscal Discipline,
Public Treasury Accounts & Budget Allocations Suite (Phase 119).
Validates statutory adherence to:
- Law on State Budget 2015 (Law No. 83/2015/QH13)
- Decree No. 163/2016/ND-CP (Guidance on Law on State Budget implementation)
- Circular No. 342/2016/TT-BTC (Implementation of Decree No. 163/2016/ND-CP)
- Decree No. 11/2020/ND-CP (State Treasury Administrative Procedures)
"""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.core.statebudget_engine import StateBudgetEngine
from src.cli.commands.statebudget_command import statebudget_app
from scripts.mcp_server import (
    handle_statebudget_estimate,
    handle_statebudget_commit,
    handle_statebudget_payout,
    handle_statebudget_audit,
    handle_statebudget_list,
    handle_statebudget_status,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path: Path) -> StateBudgetEngine:
    db_file = tmp_path / "test_statebudget.db"
    return StateBudgetEngine(db_path=str(db_file))


# =============================================================================
# 1. Core Engine Tests
# =============================================================================

class TestStateBudgetEngine:
    def test_create_estimate_valid(self, temp_engine: StateBudgetEngine) -> None:
        res = temp_engine.create_estimate(
            estimate_code="DT-2026-BGD-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="EDUCATION_AND_TRAINING",
            budget_unit="Đại học Quốc gia Hà Nội",
            allocated_amount_vnd=2_500_000_000_000.0,
            approved_by="Quốc hội",
            decision_number="Nghị quyết số 105/2025/QH15",
            contingency_rate_pct=3.0,
        )
        assert res["ok"] is True
        assert res["estimate_id"].startswith("EST-")
        assert res["estimate_code"] == "DT-2026-BGD-01"
        assert res["fiscal_year"] == 2026
        assert res["budget_level"] == "CENTRAL_BUDGET"
        assert res["expenditure_type"] == "REGULAR_EXPENDITURE"
        assert res["sector"] == "EDUCATION_AND_TRAINING"
        assert res["allocated_amount_vnd"] == 2_500_000_000_000.0
        assert res["contingency_rate_pct"] == 3.0
        assert res["status"] == "APPROVED"

    def test_create_estimate_duplicate_code(self, temp_engine: StateBudgetEngine) -> None:
        temp_engine.create_estimate(
            estimate_code="DT-DUP-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="EDUCATION_AND_TRAINING",
            budget_unit="Trường A",
            allocated_amount_vnd=100_000_000_000.0,
            approved_by="Bộ GD&ĐT",
            decision_number="QĐ-01",
        )
        with pytest.raises(Exception):
            temp_engine.create_estimate(
                estimate_code="DT-DUP-01",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường B",
                allocated_amount_vnd=200_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-02",
            )

    def test_create_estimate_invalid_inputs(self, temp_engine: StateBudgetEngine) -> None:
        with pytest.raises(ValueError, match="Estimate code cannot be empty"):
            temp_engine.create_estimate(
                estimate_code="",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường A",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Allocated amount must be greater than zero"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-01",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường A",
                allocated_amount_vnd=0.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Budget unit cannot be empty"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-02",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Invalid budget level"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-03",
                fiscal_year=2026,
                budget_level="GLOBAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường A",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Invalid expenditure type"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-04",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="UNOFFICIAL_SPEND",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường A",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Invalid sector"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-05",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="CRYPTOCURRENCY_TRADING",
                budget_unit="Trường A",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
            )

        with pytest.raises(ValueError, match="Contingency rate percentage must be between 0% and 20%"):
            temp_engine.create_estimate(
                estimate_code="DT-ERR-06",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector="EDUCATION_AND_TRAINING",
                budget_unit="Trường A",
                allocated_amount_vnd=100_000_000_000.0,
                approved_by="Bộ GD&ĐT",
                decision_number="QĐ-01",
                contingency_rate_pct=25.0,
            )

    def test_register_commitment_valid(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-COMMIT-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="DEVELOPMENT_INVESTMENT",
            sector="HEALTHCARE_AND_POPULATION",
            budget_unit="Bệnh viện Bạch Mai",
            allocated_amount_vnd=1_000_000_000_000.0,
            approved_by="Thủ tướng Chính phủ",
            decision_number="QĐ-123/TTg",
        )
        com = temp_engine.register_commitment(
            estimate_id=est["estimate_id"],
            commitment_code="CKC-2026-001",
            contract_reference="HĐ-XAY-DUNG-KHOA-KHAM",
            beneficiary_name="Tổng công ty Xây dựng Vinaconex",
            committed_amount_vnd=300_000_000_000.0,
            treasury_office="Kho bạc Nhà nước TP. Hà Nội",
        )
        assert com["ok"] is True
        assert com["commitment_id"].startswith("COM-")
        assert com["commitment_code"] == "CKC-2026-001"
        assert com["committed_amount_vnd"] == 300_000_000_000.0
        assert com["cumulative_committed_vnd"] == 300_000_000_000.0
        assert com["remaining_uncommitted_vnd"] == 700_000_000_000.0
        assert com["status"] == "COMMITTED"

    def test_register_commitment_exceed_estimate(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-EXCEED-01",
            fiscal_year=2026,
            budget_level="PROVINCIAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="STATE_ADMINISTRATION",
            budget_unit="Văn phòng UBND Tỉnh",
            allocated_amount_vnd=50_000_000_000.0,
            approved_by="HĐND Tỉnh",
            decision_number="NQ-01",
        )
        with pytest.raises(ValueError, match="exceed approved budget estimate"):
            temp_engine.register_commitment(
                estimate_id=est["estimate_id"],
                commitment_code="CKC-EXCEED-01",
                contract_reference="HĐ-MUA-SAM-XE",
                beneficiary_name="Đại lý Xe",
                committed_amount_vnd=60_000_000_000.0,
                treasury_office="Kho bạc Nhà nước Tỉnh",
            )

    def test_register_commitment_invalid_inputs(self, temp_engine: StateBudgetEngine) -> None:
        with pytest.raises(KeyError, match="not found"):
            temp_engine.register_commitment(
                estimate_id="NON_EXISTENT_EST",
                commitment_code="CKC-01",
                contract_reference="HĐ-01",
                beneficiary_name="Nhà thầu",
                committed_amount_vnd=10_000_000.0,
                treasury_office="KBNN",
            )

        est = temp_engine.create_estimate(
            estimate_code="DT-INV-COM",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="SCIENCE_AND_TECHNOLOGY",
            budget_unit="Viện Hàn lâm KH&CN",
            allocated_amount_vnd=100_000_000_000.0,
            approved_by="Bộ KH&CN",
            decision_number="QĐ-KHCN",
        )
        with pytest.raises(ValueError, match="Commitment code cannot be empty"):
            temp_engine.register_commitment(
                estimate_id=est["estimate_id"],
                commitment_code="",
                contract_reference="HĐ-01",
                beneficiary_name="Nhà thầu",
                committed_amount_vnd=10_000_000.0,
                treasury_office="KBNN",
            )

        with pytest.raises(ValueError, match="Committed amount must be greater than zero"):
            temp_engine.register_commitment(
                estimate_id=est["estimate_id"],
                commitment_code="CKC-ZERO",
                contract_reference="HĐ-01",
                beneficiary_name="Nhà thầu",
                committed_amount_vnd=-1000.0,
                treasury_office="KBNN",
            )

    def test_record_payout_valid(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-PAY-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="EDUCATION_AND_TRAINING",
            budget_unit="Trường ĐH Bách Khoa",
            allocated_amount_vnd=500_000_000_000.0,
            approved_by="Bộ GD&ĐT",
            decision_number="QĐ-BK-01",
        )
        pay1 = temp_engine.record_payout(
            estimate_id=est["estimate_id"],
            payment_voucher_number="VOUCHER-BK-001",
            payout_amount_vnd=100_000_000_000.0,
            payout_category="ACTUAL_PAYOUT",
            treasury_office="Kho bạc Nhà nước Hai Bà Trưng",
            recipient_account="711-KBNN-BACHKHOA",
            notes="Chi trả lương và phụ cấp quý 1",
        )
        assert pay1["ok"] is True
        assert pay1["payout_id"].startswith("PAY-")
        assert pay1["payout_amount_vnd"] == 100_000_000_000.0
        assert pay1["total_disbursed_vnd"] == 100_000_000_000.0
        assert pay1["execution_rate_pct"] == 20.0
        assert pay1["remaining_estimate_vnd"] == 400_000_000_000.0

        pay2 = temp_engine.record_payout(
            estimate_id=est["estimate_id"],
            payment_voucher_number="VOUCHER-BK-002",
            payout_amount_vnd=150_000_000_000.0,
            payout_category="ADVANCE",
            treasury_office="Kho bạc Nhà nước Hai Bà Trưng",
            recipient_account="711-KBNN-BACHKHOA",
            notes="Tạm ứng mua sắm thiết bị phòng lab",
        )
        assert pay2["total_disbursed_vnd"] == 250_000_000_000.0
        assert pay2["execution_rate_pct"] == 50.0
        assert pay2["remaining_estimate_vnd"] == 250_000_000_000.0

    def test_record_payout_exceed_estimate(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-EXCEED-PAY",
            fiscal_year=2026,
            budget_level="COMMUNE_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="STATE_ADMINISTRATION",
            budget_unit="UBND Xã Y",
            allocated_amount_vnd=10_000_000_000.0,
            approved_by="HĐND Xã",
            decision_number="NQ-XA",
        )
        with pytest.raises(ValueError, match="exceed approved budget estimate"):
            temp_engine.record_payout(
                estimate_id=est["estimate_id"],
                payment_voucher_number="VOUCHER-ERR",
                payout_amount_vnd=15_000_000_000.0,
            )

    def test_record_payout_invalid_inputs(self, temp_engine: StateBudgetEngine) -> None:
        with pytest.raises(KeyError, match="not found"):
            temp_engine.record_payout(
                estimate_id="NON_EXISTENT_EST",
                payment_voucher_number="VOUCHER-01",
                payout_amount_vnd=10_000_000.0,
            )

        est = temp_engine.create_estimate(
            estimate_code="DT-INV-PAY",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="ENVIRONMENT_PROTECTION",
            budget_unit="Cục Môi trường",
            allocated_amount_vnd=50_000_000_000.0,
            approved_by="Bộ TN&MT",
            decision_number="QĐ-TNMT",
        )
        with pytest.raises(ValueError, match="Payout amount must be greater than zero"):
            temp_engine.record_payout(
                estimate_id=est["estimate_id"],
                payment_voucher_number="VOUCHER-NEG",
                payout_amount_vnd=-500.0,
            )

        with pytest.raises(ValueError, match="Payment voucher number cannot be empty"):
            temp_engine.record_payout(
                estimate_id=est["estimate_id"],
                payment_voucher_number="",
                payout_amount_vnd=5000.0,
            )

        with pytest.raises(ValueError, match="Invalid payout category"):
            temp_engine.record_payout(
                estimate_id=est["estimate_id"],
                payment_voucher_number="VOUCHER-CAT",
                payout_amount_vnd=5000.0,
                payout_category="ILLEGAL_WITHDRAWAL",
            )

    def test_record_audit_finding_valid(self, temp_engine: StateBudgetEngine) -> None:
        audit = temp_engine.record_audit_finding(
            fiscal_year=2026,
            target_budget_unit="Sở Tài nguyên và Môi trường Tỉnh Z",
            violation_type="UNAUTHORIZED_EXPENDITURE",
            severity_level="CRITICAL",
            discovered_amount_vnd=15_000_000_000.0,
            corrective_measures="Thu hồi toàn bộ số tiền nộp ngân sách nhà nước và kiến nghị khởi tố",
            auditor_agency="Kiểm toán Nhà nước",
        )
        assert audit["ok"] is True
        assert audit["audit_id"].startswith("AUD-")
        assert audit["violation_type"] == "UNAUTHORIZED_EXPENDITURE"
        assert audit["severity_level"] == "CRITICAL"
        assert audit["discovered_amount_vnd"] == 15_000_000_000.0
        assert audit["resolved"] is False

    def test_record_audit_finding_invalid(self, temp_engine: StateBudgetEngine) -> None:
        with pytest.raises(ValueError, match="Target budget unit cannot be empty"):
            temp_engine.record_audit_finding(
                fiscal_year=2026,
                target_budget_unit="",
                violation_type="UNAUTHORIZED_EXPENDITURE",
                severity_level="HIGH",
                discovered_amount_vnd=1000.0,
                corrective_measures="Xử lý",
            )

        with pytest.raises(ValueError, match="Discovered violation amount cannot be negative"):
            temp_engine.record_audit_finding(
                fiscal_year=2026,
                target_budget_unit="Đơn vị A",
                violation_type="UNAUTHORIZED_EXPENDITURE",
                severity_level="HIGH",
                discovered_amount_vnd=-500.0,
                corrective_measures="Xử lý",
            )

        with pytest.raises(ValueError, match="Invalid violation type"):
            temp_engine.record_audit_finding(
                fiscal_year=2026,
                target_budget_unit="Đơn vị A",
                violation_type="UNKNOWN_VIOLATION",
                severity_level="HIGH",
                discovered_amount_vnd=1000.0,
                corrective_measures="Xử lý",
            )

        with pytest.raises(ValueError, match="Invalid severity level"):
            temp_engine.record_audit_finding(
                fiscal_year=2026,
                target_budget_unit="Đơn vị A",
                violation_type="UNAUTHORIZED_EXPENDITURE",
                severity_level="SUPER_HIGH",
                discovered_amount_vnd=1000.0,
                corrective_measures="Xử lý",
            )

    def test_list_records(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-LIST-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="PUBLIC_SECURITY",
            budget_unit="Công an Tỉnh A",
            allocated_amount_vnd=200_000_000_000.0,
            approved_by="Bộ Công an",
            decision_number="QĐ-BCA-01",
        )
        temp_engine.register_commitment(
            estimate_id=est["estimate_id"],
            commitment_code="CKC-LIST-01",
            contract_reference="HĐ-01",
            beneficiary_name="Nhà thầu 1",
            committed_amount_vnd=50_000_000_000.0,
            treasury_office="KBNN Tỉnh A",
        )
        temp_engine.record_payout(
            estimate_id=est["estimate_id"],
            payment_voucher_number="VOUCHER-LIST-01",
            payout_amount_vnd=20_000_000_000.0,
        )
        temp_engine.record_audit_finding(
            fiscal_year=2026,
            target_budget_unit="Công an Tỉnh A",
            violation_type="LATE_FISCAL_SETTLEMENT",
            severity_level="MEDIUM",
            discovered_amount_vnd=0.0,
            corrective_measures="Chấn chỉnh thời hạn quyết toán",
        )

        all_res = temp_engine.list_records(category="all")
        assert len(all_res["estimates"]) == 1
        assert len(all_res["commitments"]) == 1
        assert len(all_res["payouts"]) == 1
        assert len(all_res["audits"]) == 1

        est_res = temp_engine.list_records(category="estimates")
        assert len(est_res["estimates"]) == 1

        com_res = temp_engine.list_records(category="commitments")
        assert len(com_res["commitments"]) == 1

        pay_res = temp_engine.list_records(category="payouts")
        assert len(pay_res["payouts"]) == 1

        aud_res = temp_engine.list_records(category="audits")
        assert len(aud_res["audits"]) == 1

    def test_get_telemetry_status(self, temp_engine: StateBudgetEngine) -> None:
        status_empty = temp_engine.get_telemetry_status()
        assert status_empty["ok"] is True
        assert status_empty["status"] == "HEALTHY"
        assert status_empty["budget_estimates"]["total_estimates"] == 0

        est = temp_engine.create_estimate(
            estimate_code="DT-TELEMETRY-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="REGULAR_EXPENDITURE",
            sector="EDUCATION_AND_TRAINING",
            budget_unit="Bộ GD&ĐT",
            allocated_amount_vnd=1_000_000_000_000.0,
            approved_by="Quốc hội",
            decision_number="NQ-QH",
        )
        temp_engine.register_commitment(
            estimate_id=est["estimate_id"],
            commitment_code="CKC-TELEM-01",
            contract_reference="HĐ-TELEM",
            beneficiary_name="Nhà xuất bản Giáo dục",
            committed_amount_vnd=600_000_000_000.0,
            treasury_office="KBNN Hà Nội",
        )
        temp_engine.record_payout(
            estimate_id=est["estimate_id"],
            payment_voucher_number="VOUCHER-TELEM-01",
            payout_amount_vnd=400_000_000_000.0,
        )
        temp_engine.record_audit_finding(
            fiscal_year=2026,
            target_budget_unit="Bộ GD&ĐT",
            violation_type="COMMISSION_KICKBACK",
            severity_level="CRITICAL",
            discovered_amount_vnd=5_000_000_000.0,
            corrective_measures="Thu hồi",
        )

        status = temp_engine.get_telemetry_status()
        assert status["budget_estimates"]["total_estimates"] == 1
        assert status["budget_estimates"]["total_allocated_vnd"] == 1_000_000_000_000.0
        assert status["treasury_execution"]["total_committed_vnd"] == 600_000_000_000.0
        assert status["treasury_execution"]["commitment_rate_pct"] == 60.0
        assert status["treasury_execution"]["total_disbursed_vnd"] == 400_000_000_000.0
        assert status["treasury_execution"]["execution_rate_pct"] == 40.0
        assert status["fiscal_discipline"]["total_audit_findings"] == 1
        assert status["fiscal_discipline"]["unresolved_critical_audits"] == 1


# =============================================================================
# 2. CLI Command Tests
# =============================================================================

class TestStateBudgetCli:
    def test_cli_main_callback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        result = runner.invoke(statebudget_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ DỰ TOÁN, CAM KẾT CHI & NGÂN SÁCH NHÀ NƯỚC QUỐC GIA" in result.output

        result_json = runner.invoke(statebudget_app, ["--json"])
        assert result_json.exit_code == 0
        data = json.loads(result_json.output)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

    def test_cli_estimate_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        result = runner.invoke(
            statebudget_app,
            [
                "estimate",
                "--code", "DT-CLI-01",
                "--year", "2026",
                "--level", "CENTRAL_BUDGET",
                "--type", "REGULAR_EXPENDITURE",
                "--sector", "EDUCATION_AND_TRAINING",
                "--unit", "Đại học Bách Khoa",
                "--amount", "500000000000",
                "--approver", "Bộ GD&ĐT",
                "--decision", "QĐ-500",
            ],
        )
        assert result.exit_code == 0
        assert "PHÊ DUYỆT DỰ TOÁN NGÂN SÁCH NHÀ NƯỚC THÀNH CÔNG" in result.output
        assert "DT-CLI-01" in result.output

    def test_cli_estimate_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        result = runner.invoke(
            statebudget_app,
            [
                "estimate",
                "--code", "DT-CLI-JSON",
                "--unit", "Viện Tim Hà Nội",
                "--amount", "100000000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["estimate_code"] == "DT-CLI-JSON"

    def test_cli_commit_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        runner.invoke(
            statebudget_app,
            [
                "estimate",
                "--code", "DT-CLI-COM",
                "--unit", "Bệnh viện Nhi",
                "--amount", "300000000000",
            ],
        )
        result = runner.invoke(
            statebudget_app,
            [
                "commit",
                "DT-CLI-COM",
                "--code", "CKC-CLI-01",
                "--contract", "HĐ-THIET-BI-01",
                "--beneficiary", "Công ty MedTech",
                "--amount", "80000000000",
            ],
        )
        assert result.exit_code == 0
        assert "ĐĂNG KÝ CAM KẾT CHI KBNN THÀNH CÔNG" in result.output
        assert "CKC-CLI-01" in result.output

    def test_cli_payout_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        runner.invoke(
            statebudget_app,
            [
                "estimate",
                "--code", "DT-CLI-PAY",
                "--unit", "Bệnh viện Bạch Mai",
                "--amount", "400000000000",
            ],
        )
        result = runner.invoke(
            statebudget_app,
            [
                "payout",
                "DT-CLI-PAY",
                "--voucher", "RUT-VON-2026-001",
                "--amount", "100000000000",
                "--category", "ACTUAL_PAYOUT",
            ],
        )
        assert result.exit_code == 0
        assert "XUẤT CHI NGÂN SÁCH QUA KBNN THÀNH CÔNG" in result.output
        assert "25.0%" in result.output

    def test_cli_audit_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        result = runner.invoke(
            statebudget_app,
            [
                "audit",
                "--unit", "UBND Quận X",
                "--violation", "UNAUTHORIZED_EXPENDITURE",
                "--severity", "HIGH",
                "--amount", "5000000000",
                "--measures", "Thu hồi nộp ngân sách nhà nước",
            ],
        )
        assert result.exit_code == 0
        assert "GHI NHẬN KẾT LUẬN KIỂM TOÁN TÀI KHÓA NGÂN SÁCH" in result.output
        assert "HIGH" in result.output

    def test_cli_list_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        runner.invoke(
            statebudget_app,
            [
                "estimate",
                "--code", "DT-CLI-LIST",
                "--unit", "Cục Thuế",
                "--amount", "50000000000",
            ],
        )
        result = runner.invoke(
            statebudget_app,
            ["list", "--type", "estimates"],
        )
        assert result.exit_code == 0
        assert "DT-CLI-" in result.output
        assert "Cục Thuế" in result.output

    def test_cli_status_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        result = runner.invoke(
            statebudget_app,
            ["status"],
        )
        assert result.exit_code == 0
        assert "State Budget Subsystem Status" in result.output


# =============================================================================
# 3. MCP Tool Handler Tests (Dual Parity)
# =============================================================================

class TestStateBudgetMcp:
    def test_mcp_standalone_estimate(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_estimate({
            "estimate_code": "DT-MCP-01",
            "budget_unit": "Sở Y tế",
            "allocated_amount_vnd": 300_000_000_000.0,
            "sector": "HEALTHCARE_AND_POPULATION",
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["estimate_code"] == "DT-MCP-01"

    def test_mcp_standalone_estimate_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_estimate({
            "estimate_code": "",
            "budget_unit": "Sở Y tế",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_commit(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        handle_statebudget_estimate({
            "estimate_code": "DT-MCP-COM",
            "budget_unit": "Sở GTVT",
            "allocated_amount_vnd": 500_000_000_000.0,
        })
        raw = handle_statebudget_commit({
            "estimate_id": "DT-MCP-COM",
            "commitment_code": "CKC-MCP-01",
            "contract_reference": "HĐ-GTVT-01",
            "beneficiary_name": "Công ty Cầu đường",
            "committed_amount_vnd": 150_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["commitment_code"] == "CKC-MCP-01"
        assert data["committed_amount_vnd"] == 150_000_000_000.0

    def test_mcp_standalone_commit_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_commit({
            "estimate_id": "NON_EXISTENT_ID",
            "commitment_code": "CKC-ERR",
            "contract_reference": "HĐ-ERR",
            "beneficiary_name": "Nhà thầu",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_payout(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        handle_statebudget_estimate({
            "estimate_code": "DT-MCP-PAY",
            "budget_unit": "Bệnh viện",
            "allocated_amount_vnd": 200_000_000_000.0,
        })
        raw = handle_statebudget_payout({
            "estimate_id": "DT-MCP-PAY",
            "payment_voucher_number": "LCT-MCP-01",
            "payout_amount_vnd": 50_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["execution_rate_pct"] == 25.0

    def test_mcp_standalone_payout_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_payout({
            "estimate_id": "NON_EXISTENT_ID",
            "payment_voucher_number": "ERR-VOUCHER",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_audit(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_audit({
            "target_budget_unit": "Sở KH&CN Tỉnh A",
            "corrective_measures": "Chấn chỉnh công tác đấu thầu đề tài khoa học",
            "violation_type": "UNAUTHORIZED_EXPENDITURE",
            "severity_level": "MEDIUM",
            "discovered_amount_vnd": 2_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["target_budget_unit"] == "Sở KH&CN Tỉnh A"

    def test_mcp_standalone_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_list({"category": "all"})
        data = json.loads(raw)
        assert data["ok"] is True
        assert "estimates" in data
        assert "commitments" in data

    def test_mcp_standalone_status(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        raw = handle_statebudget_status({})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"
        assert "regulatory_framework" in data

    def test_core_mcp_server_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_core_statebudget.db"
        monkeypatch.setenv("MEKONG_STATEBUDGET_DB", str(db_file))

        server = MekongMcpServer()

        # Test estimate tool
        est_raw = server._handle_statebudget_estimate(
            estimate_code="DT-CORE-MCP-01",
            budget_unit="Cục Hàng hải Việt Nam",
            allocated_amount_vnd=150_000_000_000.0,
            sector="ECONOMIC_SERVICES",
        )
        est_data = json.loads(est_raw)
        assert est_data["ok"] is True
        est_id = est_data["estimate_id"]

        # Test commit tool
        com_raw = server._handle_statebudget_commit(
            estimate_id=est_id,
            commitment_code="CKC-CORE-01",
            contract_reference="HĐ-NAO-VET-LUONG-TAU",
            beneficiary_name="Công ty Nạo vét",
            committed_amount_vnd=75_000_000_000.0,
        )
        com_data = json.loads(com_raw)
        assert com_data["ok"] is True
        assert com_data["committed_amount_vnd"] == 75_000_000_000.0

        # Test payout tool
        pay_raw = server._handle_statebudget_payout(
            estimate_id=est_id,
            payment_voucher_number="VOUCHER-CORE-PAY-01",
            payout_amount_vnd=50_000_000_000.0,
        )
        pay_data = json.loads(pay_raw)
        assert pay_data["ok"] is True
        assert pay_data["execution_rate_pct"] == 33.33

        # Test audit tool
        aud_raw = server._handle_statebudget_audit(
            target_budget_unit="Cục Hàng hải Việt Nam",
            corrective_measures="Báo cáo Bộ GTVT",
        )
        aud_data = json.loads(aud_raw)
        assert aud_data["ok"] is True

        # Test list tool
        list_raw = server._handle_statebudget_list(category="all")
        list_data = json.loads(list_raw)
        assert list_data["ok"] is True
        assert len(list_data["estimates"]) == 1

        # Test status tool
        status_raw = server._handle_statebudget_status()
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True
        assert status_data["budget_estimates"]["total_estimates"] == 1


# =============================================================================
# 4. In-Depth Boundary & Edge Case Tests
# =============================================================================

class TestStateBudgetEdgeCases:
    def test_all_budget_levels(self, temp_engine: StateBudgetEngine) -> None:
        for idx, level in enumerate(temp_engine.BUDGET_LEVELS):
            res = temp_engine.create_estimate(
                estimate_code=f"DT-LVL-{idx}",
                fiscal_year=2026,
                budget_level=level,
                expenditure_type="REGULAR_EXPENDITURE",
                sector="STATE_ADMINISTRATION",
                budget_unit=f"Đơn vị cấp {level}",
                allocated_amount_vnd=10_000_000_000.0,
                approved_by="Cấp thẩm quyền",
                decision_number="QĐ-LVL",
            )
            assert res["budget_level"] == level

    def test_all_expenditure_types(self, temp_engine: StateBudgetEngine) -> None:
        for idx, etype in enumerate(temp_engine.EXPENDITURE_TYPES):
            res = temp_engine.create_estimate(
                estimate_code=f"DT-TYPE-{idx}",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type=etype,
                sector="ECONOMIC_SERVICES",
                budget_unit="Đơn vị chi",
                allocated_amount_vnd=20_000_000_000.0,
                approved_by="Cấp thẩm quyền",
                decision_number="QĐ-TYPE",
            )
            assert res["expenditure_type"] == etype

    def test_all_sectors(self, temp_engine: StateBudgetEngine) -> None:
        for idx, sec in enumerate(temp_engine.SECTORS):
            res = temp_engine.create_estimate(
                estimate_code=f"DT-SEC-{idx}",
                fiscal_year=2026,
                budget_level="CENTRAL_BUDGET",
                expenditure_type="REGULAR_EXPENDITURE",
                sector=sec,
                budget_unit="Đơn vị lĩnh vực",
                allocated_amount_vnd=15_000_000_000.0,
                approved_by="Cấp thẩm quyền",
                decision_number="QĐ-SEC",
            )
            assert res["sector"] == sec

    def test_all_violation_types(self, temp_engine: StateBudgetEngine) -> None:
        for v_type in temp_engine.VIOLATION_TYPES:
            audit = temp_engine.record_audit_finding(
                fiscal_year=2026,
                target_budget_unit="Đơn vị kiểm toán",
                violation_type=v_type,
                severity_level="MEDIUM",
                discovered_amount_vnd=1_000_000_000.0,
                corrective_measures=f"Khắc phục vi phạm {v_type}",
            )
            assert audit["violation_type"] == v_type

    def test_sequential_payouts_and_execution_rate(self, temp_engine: StateBudgetEngine) -> None:
        est = temp_engine.create_estimate(
            estimate_code="DT-SEQ-01",
            fiscal_year=2026,
            budget_level="CENTRAL_BUDGET",
            expenditure_type="DEVELOPMENT_INVESTMENT",
            sector="ECONOMIC_SERVICES",
            budget_unit="Ban Quản lý Dự án Giao thông",
            allocated_amount_vnd=1_000_000_000_000.0,
            approved_by="Bộ GTVT",
            decision_number="QĐ-GTVT-2026",
        )
        # Sequence of 4 payouts: 25%, 50%, 75%, 100%
        for i in range(1, 5):
            pay = temp_engine.record_payout(
                estimate_id=est["estimate_id"],
                payment_voucher_number=f"VOUCHER-SEQ-{i}",
                payout_amount_vnd=250_000_000_000.0,
            )
            assert pay["execution_rate_pct"] == round(i * 25.0, 2)
            assert pay["remaining_estimate_vnd"] == (1_000_000_000_000.0 - i * 250_000_000_000.0)
