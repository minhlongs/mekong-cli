"""
Comprehensive test suite for Vietnamese Tax Administration, Electronic Invoices & Tax Audits (Luật Quản lý thuế số 38/2019/QH14).
Tests pure Python engine isolation, Typer CLI surface, dual MCP parity, and statutory calculations.
"""

import json
from pathlib import Path
from typing import Any, Dict
import pytest
from typer.testing import CliRunner

from src.core.taxadmin_engine import TaxAdminEngine
from src.cli.commands.taxadmin_command import taxadmin_app
from scripts.mcp_server import (
    handle_taxadmin_taxpayer,
    handle_taxadmin_assess,
    handle_taxadmin_invoice,
    handle_taxadmin_adjust,
    handle_taxadmin_audit,
    handle_taxadmin_list,
    handle_taxadmin_status,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TaxAdminEngine:
    db_file = tmp_path / "test_taxadmin.db"
    monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))
    return TaxAdminEngine(str(db_file))


# =============================================================================
# 1. Core Engine Tests
# =============================================================================

class TestTaxAdminEngine:
    def test_register_taxpayer_valid(self, temp_engine: TaxAdminEngine) -> None:
        # 10-digit enterprise MST
        res1 = temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty TNHH Mekong Tech",
            legal_rep="Trần Văn A",
            taxpayer_type="ENTERPRISE",
            tax_office="Cục Thuế TP. Hà Nội",
        )
        assert res1["ok"] is True
        assert res1["tax_code"] == "0108999888"
        assert res1["taxpayer_name"] == "Công ty TNHH Mekong Tech"
        assert res1["status"] == "ACTIVE"

        # 13-digit branch MST
        res2 = temp_engine.register_taxpayer(
            tax_code="0108999888-001",
            taxpayer_name="Chi nhánh Công ty TNHH Mekong Tech tại Đà Nẵng",
            legal_rep="Nguyễn Văn B",
            taxpayer_type="DEPENDENT_UNIT",
            tax_office="Cục Thuế TP. Đà Nẵng",
        )
        assert res2["ok"] is True
        assert res2["tax_code"] == "0108999888-001"

    def test_register_taxpayer_duplicate(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty TNHH Mekong Tech",
            legal_rep="Trần Văn A",
        )
        with pytest.raises(ValueError, match="đã tồn tại trong hệ thống"):
            temp_engine.register_taxpayer(
                tax_code="0108999888",
                taxpayer_name="Công ty TNHH Khác",
                legal_rep="Lê Văn C",
            )

    def test_register_taxpayer_invalid_code(self, temp_engine: TaxAdminEngine) -> None:
        with pytest.raises(ValueError, match="Mã số thuế không hợp lệ"):
            temp_engine.register_taxpayer(
                tax_code="12345",
                taxpayer_name="Doanh nghiệp X",
                legal_rep="Nguyễn A",
            )

        with pytest.raises(ValueError, match="Mã số thuế không hợp lệ"):
            temp_engine.register_taxpayer(
                tax_code="0108999888ABC",
                taxpayer_name="Doanh nghiệp X",
                legal_rep="Nguyễn A",
            )

    def test_register_taxpayer_invalid_inputs(self, temp_engine: TaxAdminEngine) -> None:
        with pytest.raises(ValueError, match="Loại người nộp thuế không hợp lệ"):
            temp_engine.register_taxpayer(
                tax_code="0108999888",
                taxpayer_name="Doanh nghiệp X",
                legal_rep="Nguyễn A",
                taxpayer_type="INVALID_TYPE",
            )

        with pytest.raises(ValueError, match="Tên người nộp thuế không được để trống"):
            temp_engine.register_taxpayer(
                tax_code="0108999888",
                taxpayer_name="   ",
                legal_rep="Nguyễn A",
            )

        with pytest.raises(ValueError, match="Người đại diện theo pháp luật không được để trống"):
            temp_engine.register_taxpayer(
                tax_code="0108999888",
                taxpayer_name="Doanh nghiệp X",
                legal_rep="   ",
            )

    def test_assess_tax_and_interest_on_time(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong",
            legal_rep="Trần A",
        )

        # Paid in full before due date
        res = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="CIT",
            tax_period="2026-Q1",
            declared_amount_vnd=100_000_000.0,
            assessed_amount_vnd=100_000_000.0,
            due_date_str="2026-04-30",
            paid_amount_vnd=100_000_000.0,
            current_date_str="2026-05-15",
        )
        assert res["ok"] is True
        assert res["outstanding_tax_vnd"] == 0.0
        assert res["days_overdue"] == 0
        assert res["late_payment_interest_vnd"] == 0.0
        assert res["status"] == "SETTLED"
        assert res["enforcement_measure"] == "NONE"
        assert res["exit_suspension"] is False

    def test_assess_tax_and_interest_overdue(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong",
            legal_rep="Trần A",
        )

        # 30 days overdue with 100,000,000 VND debt
        # Late interest: 100,000,000 * 0.0003 * 30 = 900,000 VND
        res = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="CIT",
            tax_period="2026-Q1",
            declared_amount_vnd=100_000_000.0,
            assessed_amount_vnd=100_000_000.0,
            due_date_str="2026-04-30",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-30",
        )
        assert res["ok"] is True
        assert res["outstanding_tax_vnd"] == 100_000_000.0
        assert res["days_overdue"] == 30
        assert res["late_payment_interest_vnd"] == 900_000.0
        assert res["total_payable_vnd"] == 100_900_000.0
        assert res["status"] == "PENDING"
        assert res["enforcement_measure"] == "NONE"

    def test_assess_tax_enforcement_over_90_days(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong",
            legal_rep="Trần A",
        )

        # 100 days overdue: Bank account freeze + Exit suspension (>50m VND)
        res100 = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="VAT",
            tax_period="2026-M01",
            declared_amount_vnd=60_000_000.0,
            assessed_amount_vnd=60_000_000.0,
            due_date_str="2026-02-20",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-31",  # 100 days overdue
        )
        assert res100["status"] == "ENFORCING"
        assert res100["enforcement_measure"] == "BANK_ACCOUNT_FREEZE"
        assert res100["exit_suspension"] is True

        # 130 days overdue: Invoice invalidation
        res130 = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="VAT",
            tax_period="2026-M01",
            declared_amount_vnd=60_000_000.0,
            assessed_amount_vnd=60_000_000.0,
            due_date_str="2026-01-20",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-30",  # 130 days
        )
        assert res130["enforcement_measure"] == "INVOICE_INVALIDATION"

        # 160 days overdue: Customs suspension
        res160 = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="VAT",
            tax_period="2026-M01",
            declared_amount_vnd=60_000_000.0,
            assessed_amount_vnd=60_000_000.0,
            due_date_str="2025-12-20",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-29",  # 160 days
        )
        assert res160["enforcement_measure"] == "CUSTOMS_SUSPENSION"

        # 190 days overdue: Asset seizure
        res190 = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="VAT",
            tax_period="2026-M01",
            declared_amount_vnd=60_000_000.0,
            assessed_amount_vnd=60_000_000.0,
            due_date_str="2025-11-20",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-29",  # 190 days
        )
        assert res190["enforcement_measure"] == "ASSET_SEIZURE"

        # 220 days overdue: License revocation
        res220 = temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="VAT",
            tax_period="2026-M01",
            declared_amount_vnd=60_000_000.0,
            assessed_amount_vnd=60_000_000.0,
            due_date_str="2025-10-20",
            paid_amount_vnd=0.0,
            current_date_str="2026-05-28",  # 220 days
        )
        assert res220["enforcement_measure"] == "LICENSE_REVOCATION"

    def test_assess_tax_invalid_inputs(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong",
            legal_rep="Trần A",
        )

        with pytest.raises(ValueError, match="Loại thuế không hợp lệ"):
            temp_engine.assess_tax_and_interest(
                tax_code="0108999888",
                tax_type="CRYPTO_TAX",
                tax_period="2026-Q1",
                declared_amount_vnd=1000.0,
                assessed_amount_vnd=1000.0,
                due_date_str="2026-04-30",
            )

        with pytest.raises(ValueError, match="Số tiền thuế không được âm"):
            temp_engine.assess_tax_and_interest(
                tax_code="0108999888",
                tax_type="CIT",
                tax_period="2026-Q1",
                declared_amount_vnd=-500.0,
                assessed_amount_vnd=1000.0,
                due_date_str="2026-04-30",
            )

        with pytest.raises(ValueError, match="Không tìm thấy người nộp thuế"):
            temp_engine.assess_tax_and_interest(
                tax_code="9999999999",
                tax_type="CIT",
                tax_period="2026-Q1",
                declared_amount_vnd=1000.0,
                assessed_amount_vnd=1000.0,
                due_date_str="2026-04-30",
            )

        with pytest.raises(ValueError, match="Hạn nộp thuế không đúng định dạng"):
            temp_engine.assess_tax_and_interest(
                tax_code="0108999888",
                tax_type="CIT",
                tax_period="2026-Q1",
                declared_amount_vnd=1000.0,
                assessed_amount_vnd=1000.0,
                due_date_str="30-04-2026",
            )

    def test_issue_electronic_invoice_with_cqt_code(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )

        res = temp_engine.issue_electronic_invoice(
            invoice_code="1C26TAA-0000001",
            invoice_type="VAT_INVOICE",
            seller_tax_code="0108999888",
            buyer_tax_code="0100109106",
            buyer_name="Tập đoàn Viễn thông Viettel",
            subtotal_vnd=500_000_000.0,
            vat_rate_pct=10.0,
            with_tax_authority_code=True,
        )
        assert res["ok"] is True
        assert res["invoice_code"] == "1C26TAA-0000001"
        assert res["subtotal_vnd"] == 500_000_000.0
        assert res["vat_amount_vnd"] == 50_000_000.0
        assert res["total_amount_vnd"] == 550_000_000.0
        assert res["tax_authority_code"].startswith("CQT-")
        assert res["issue_status"] == "ISSUED"

    def test_issue_electronic_invoice_inactive_seller(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
            status="SUSPENDED",
        )

        with pytest.raises(ValueError, match="không đủ điều kiện phát hành hóa đơn"):
            temp_engine.issue_electronic_invoice(
                invoice_code="1C26TAA-0000002",
                invoice_type="VAT_INVOICE",
                seller_tax_code="0108999888",
                buyer_tax_code="0100109106",
                buyer_name="Người mua",
                subtotal_vnd=10_000_000.0,
            )

    def test_issue_electronic_invoice_duplicate_code(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )
        temp_engine.issue_electronic_invoice(
            invoice_code="1C26TAA-DUP",
            invoice_type="VAT_INVOICE",
            seller_tax_code="0108999888",
            buyer_tax_code="0100109106",
            buyer_name="Khách hàng",
            subtotal_vnd=10_000_000.0,
        )

        with pytest.raises(ValueError, match="đã tồn tại trong hệ thống"):
            temp_engine.issue_electronic_invoice(
                invoice_code="1C26TAA-DUP",
                invoice_type="VAT_INVOICE",
                seller_tax_code="0108999888",
                buyer_tax_code="0100109106",
                buyer_name="Khách hàng khác",
                subtotal_vnd=20_000_000.0,
            )

    def test_adjust_electronic_invoice_adjust(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )
        temp_engine.issue_electronic_invoice(
            invoice_code="1C26TAA-ORIG",
            invoice_type="VAT_INVOICE",
            seller_tax_code="0108999888",
            buyer_tax_code="0100109106",
            buyer_name="Khách hàng",
            subtotal_vnd=100_000_000.0,
            vat_rate_pct=10.0,
        )

        # Adjust by +20,000,000 VND
        adj = temp_engine.adjust_electronic_invoice(
            original_invoice_code="1C26TAA-ORIG",
            action="ADJUST",
            new_invoice_code="1C26TAA-ADJ01",
            adjusted_diff_vnd=20_000_000.0,
            explanation="Điều chỉnh tăng giá dịch vụ",
        )
        assert adj["ok"] is True
        assert adj["action"] == "ADJUST"
        assert adj["status"] == "ADJUSTED"
        assert adj["new_total_amount_vnd"] == 132_000_000.0  # 120m + 10% = 132m

    def test_adjust_electronic_invoice_cancel_form_04(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )
        temp_engine.issue_electronic_invoice(
            invoice_code="1C26TAA-CANCEL",
            invoice_type="VAT_INVOICE",
            seller_tax_code="0108999888",
            buyer_tax_code="0100109106",
            buyer_name="Khách hàng",
            subtotal_vnd=50_000_000.0,
        )

        # Cancel with Form 04/SS-HDDT
        canc = temp_engine.adjust_electronic_invoice(
            original_invoice_code="1C26TAA-CANCEL",
            action="CANCEL_FORM_04",
            explanation="Hủy do sai thông tin MST khách hàng",
        )
        assert canc["ok"] is True
        assert canc["status"] == "CANCELLED_FORM_04"
        assert canc["form_04_notice"].startswith("TB-04SS-")

        # Re-cancelling or adjusting a cancelled invoice should fail
        with pytest.raises(ValueError, match="đã bị hủy theo Mẫu 04/SS-HĐĐT"):
            temp_engine.adjust_electronic_invoice(
                original_invoice_code="1C26TAA-CANCEL",
                action="ADJUST",
                new_invoice_code="1C26TAA-ERR",
            )

    def test_record_tax_audit_underdeclaration(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )

        # 20% underdeclaration penalty under Art 16 Decree 125
        res = temp_engine.record_tax_audit(
            tax_code="0108999888",
            audit_type="FIELD_EXAMINATION",
            tax_office="Cục Thuế TP. Hà Nội",
            decision_number="QĐ-TT-2026-01",
            audit_year=2026,
            underdeclared_tax_vnd=100_000_000.0,
            is_tax_evasion=False,
            late_payment_days=60,
            violation_description="Khai sai chỉ tiêu trên tờ khai thuế GTGT",
        )
        assert res["ok"] is True
        assert res["penalty_rate"] == "20%"
        assert res["penalty_amount_vnd"] == 20_000_000.0
        # Late interest: 100,000,000 * 0.0003 * 60 = 1,800,000 VND
        assert res["late_payment_fee_vnd"] == 1_800_000.0
        assert res["total_recovery_vnd"] == 121_800_000.0
        assert res["status"] == "CONCLUDED"

    def test_record_tax_audit_tax_evasion(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )

        # 1.5x tax evasion penalty under Art 17 Decree 125
        res = temp_engine.record_tax_audit(
            tax_code="0108999888",
            audit_type="COMPREHENSIVE_INSPECTION",
            tax_office="Cục Thuế TP. Hà Nội",
            decision_number="QĐ-TT-2026-02",
            audit_year=2026,
            underdeclared_tax_vnd=200_000_000.0,
            is_tax_evasion=True,
            evasion_penalty_multiplier=1.5,
            late_payment_days=100,
            violation_description="Hành vi sử dụng hóa đơn bất hợp pháp để trốn thuế",
        )
        assert res["ok"] is True
        assert res["penalty_rate"] == "1.5x"
        assert res["penalty_amount_vnd"] == 300_000_000.0
        # Late interest: 200,000,000 * 0.0003 * 100 = 6,000,000 VND
        assert res["late_payment_fee_vnd"] == 6_000_000.0
        assert res["total_recovery_vnd"] == 506_000_000.0

    def test_record_tax_audit_invalid_inputs(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty Mekong Tech",
            legal_rep="Trần A",
        )

        with pytest.raises(ValueError, match="Mức phạt trốn thuế phải từ 1.0 lần đến 3.0 lần"):
            temp_engine.record_tax_audit(
                tax_code="0108999888",
                audit_type="FIELD_EXAMINATION",
                tax_office="Cục Thuế",
                decision_number="QĐ-01",
                audit_year=2026,
                underdeclared_tax_vnd=100_000.0,
                is_tax_evasion=True,
                evasion_penalty_multiplier=4.0,
            )

        with pytest.raises(ValueError, match="Số tiền thuế khai thiếu hoặc trốn thuế không được âm"):
            temp_engine.record_tax_audit(
                tax_code="0108999888",
                audit_type="FIELD_EXAMINATION",
                tax_office="Cục Thuế",
                decision_number="QĐ-01",
                audit_year=2026,
                underdeclared_tax_vnd=-500.0,
            )

    def test_list_records(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty A",
            legal_rep="Trần A",
        )
        temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="CIT",
            tax_period="2026-Q1",
            declared_amount_vnd=50_000_000.0,
            assessed_amount_vnd=50_000_000.0,
            due_date_str="2026-04-30",
        )
        temp_engine.issue_electronic_invoice(
            invoice_code="1C26TAA-01",
            invoice_type="VAT_INVOICE",
            seller_tax_code="0108999888",
            buyer_tax_code="0100109106",
            buyer_name="Người mua",
            subtotal_vnd=30_000_000.0,
        )
        temp_engine.record_tax_audit(
            tax_code="0108999888",
            audit_type="DESK_EXAMINATION",
            tax_office="Cục Thuế",
            decision_number="QĐ-01",
            audit_year=2026,
            underdeclared_tax_vnd=5_000_000.0,
        )

        all_res = temp_engine.list_records(category="all")
        assert len(all_res["taxpayers"]) == 1
        assert len(all_res["assessments"]) == 1
        assert len(all_res["invoices"]) == 1
        assert len(all_res["audits"]) == 1

        inv_res = temp_engine.list_records(category="invoices")
        assert len(inv_res["invoices"]) == 1

    def test_get_telemetry_status(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Công ty B",
            legal_rep="Lê B",
        )
        temp_engine.assess_tax_and_interest(
            tax_code="0108999888",
            tax_type="CIT",
            tax_period="2026-Q1",
            declared_amount_vnd=100_000_000.0,
            assessed_amount_vnd=100_000_000.0,
            due_date_str="2026-01-30",
            paid_amount_vnd=40_000_000.0,
            current_date_str="2026-05-30",  # 120 days overdue => enforcing + exit suspension
        )
        status = temp_engine.get_telemetry_status()
        assert status["ok"] is True
        assert status["status"] == "HEALTHY"
        assert status["taxpayer_count"] == 1
        assert status["assessment_count"] == 1
        assert status["total_assessed_vnd"] == 100_000_000.0
        assert status["total_paid_vnd"] == 40_000_000.0
        assert status["collection_rate_pct"] == 40.0
        assert status["enforcing_count"] == 1
        assert status["exit_suspended_count"] == 1


# =============================================================================
# 2. Typer CLI Command Surface Tests
# =============================================================================

class TestTaxAdminCli:
    def test_cli_default_callback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        result = runner.invoke(taxadmin_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ THUẾ & HÓA ĐƠN ĐIỆN TỬ QUỐC GIA" in result.output

    def test_cli_status_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        result = runner.invoke(taxadmin_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

    def test_cli_taxpayer_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        result = runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty Cổ phần AI Mekong",
                "--rep", "Nguyễn Văn C",
                "--type", "ENTERPRISE",
                "--office", "Cục Thuế TP. Hà Nội",
            ],
        )
        assert result.exit_code == 0
        assert "ĐĂNG KÝ NGƯỜI NỘP THUẾ THÀNH CÔNG" in result.output
        assert "0108999888" in result.output

    def test_cli_taxpayer_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        result = runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty AI Mekong",
                "--rep", "Nguyễn Văn C",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["tax_code"] == "0108999888"

    def test_cli_assess_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty AI",
                "--rep", "Nguyễn C",
            ],
        )
        result = runner.invoke(
            taxadmin_app,
            [
                "assess",
                "--code", "0108999888",
                "--type", "CIT",
                "--period", "2026-Q1",
                "--declared", "80000000",
                "--due-date", "2026-04-30",
                "--paid", "20000000",
                "--calc-date", "2026-05-30",
            ],
        )
        assert result.exit_code == 0
        assert "THÔNG BÁO NGHĨA VỤ THUẾ & TIỀN CHẬM NỘP" in result.output
        assert "60,000,000 VND" in result.output

    def test_cli_invoice_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty Bán",
                "--rep", "Trần D",
            ],
        )
        result = runner.invoke(
            taxadmin_app,
            [
                "invoice",
                "--code", "1C26TAA-CLI01",
                "--type", "VAT_INVOICE",
                "--seller", "0108999888",
                "--buyer-tax", "0100109106",
                "--buyer-name", "Viettel Post",
                "--amount", "200000000",
                "--vat-rate", "10",
            ],
        )
        assert result.exit_code == 0
        assert "PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ THÀNH CÔNG" in result.output
        assert "1C26TAA-CLI01" in result.output

    def test_cli_adjust_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty Bán",
                "--rep", "Trần D",
            ],
        )
        runner.invoke(
            taxadmin_app,
            [
                "invoice",
                "--code", "1C26TAA-ADJ-ORIG",
                "--seller", "0108999888",
                "--buyer-name", "Khách hàng",
                "--amount", "100000000",
            ],
        )
        result = runner.invoke(
            taxadmin_app,
            [
                "adjust",
                "1C26TAA-ADJ-ORIG",
                "--action", "ADJUST",
                "--new-code", "1C26TAA-ADJ-NEW",
                "--diff", "10000000",
                "--reason", "Tăng sản lượng",
            ],
        )
        assert result.exit_code == 0
        assert "XỬ LÝ HÓA ĐƠN ĐIỆN TỬ CÓ SAI SÓT" in result.output
        assert "1C26TAA-ADJ-NEW" in result.output

    def test_cli_audit_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty Bị Thanh Tra",
                "--rep", "Trần D",
            ],
        )
        result = runner.invoke(
            taxadmin_app,
            [
                "audit",
                "--code", "0108999888",
                "--type", "FIELD_EXAMINATION",
                "--decision", "QĐ-TT-CLI-01",
                "--year", "2026",
                "--underdeclared", "50000000",
                "--no-evasion",
                "--days", "30",
            ],
        )
        assert result.exit_code == 0
        assert "KẾT LUẬN THANH TRA / KIỂM TRA THUẾ" in result.output
        assert "10,000,000 VND" in result.output  # 20% fine

    def test_cli_list_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        runner.invoke(
            taxadmin_app,
            [
                "taxpayer",
                "--code", "0108999888",
                "--name", "Công ty List Test",
                "--rep", "Trần D",
            ],
        )
        result = runner.invoke(
            taxadmin_app,
            ["list", "--type", "taxpayers"],
        )
        assert result.exit_code == 0
        assert "0108999888" in result.output
        assert "List Test" in result.output


# =============================================================================
# 3. MCP Tool Handler Tests (Dual Parity)
# =============================================================================

class TestTaxAdminMcp:
    def test_mcp_standalone_taxpayer(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        raw = handle_taxadmin_taxpayer({
            "tax_code": "0108999888",
            "taxpayer_name": "Công ty MCP Test",
            "legal_rep": "Trịnh E",
            "taxpayer_type": "ENTERPRISE",
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["tax_code"] == "0108999888"

    def test_mcp_standalone_taxpayer_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        raw = handle_taxadmin_taxpayer({
            "tax_code": "INVALID_MST",
            "taxpayer_name": "Test",
            "legal_rep": "Test",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_assess(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        handle_taxadmin_taxpayer({
            "tax_code": "0108999888",
            "taxpayer_name": "Công ty MCP",
            "legal_rep": "Trần A",
        })
        raw = handle_taxadmin_assess({
            "tax_code": "0108999888",
            "due_date_str": "2026-04-30",
            "declared_amount_vnd": 50_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["tax_code"] == "0108999888"

    def test_mcp_standalone_invoice(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        handle_taxadmin_taxpayer({
            "tax_code": "0108999888",
            "taxpayer_name": "Công ty Bán",
            "legal_rep": "Trần A",
        })
        raw = handle_taxadmin_invoice({
            "invoice_code": "1C26TAA-MCP01",
            "seller_tax_code": "0108999888",
            "buyer_tax_code": "0100109106",
            "buyer_name": "Khách MCP",
            "subtotal_vnd": 80_000_000.0,
            "vat_rate_pct": 10.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["total_amount_vnd"] == 88_000_000.0

    def test_mcp_standalone_adjust(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        handle_taxadmin_taxpayer({
            "tax_code": "0108999888",
            "taxpayer_name": "Công ty Bán",
            "legal_rep": "Trần A",
        })
        handle_taxadmin_invoice({
            "invoice_code": "1C26TAA-MCP-ORIG",
            "seller_tax_code": "0108999888",
            "buyer_tax_code": "0100109106",
            "buyer_name": "Khách MCP",
            "subtotal_vnd": 50_000_000.0,
        })
        raw = handle_taxadmin_adjust({
            "original_invoice_code": "1C26TAA-MCP-ORIG",
            "action": "CANCEL_FORM_04",
            "explanation": "Hủy hóa đơn sai địa chỉ",
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["status"] == "CANCELLED_FORM_04"

    def test_mcp_standalone_audit(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        handle_taxadmin_taxpayer({
            "tax_code": "0108999888",
            "taxpayer_name": "Công ty Thanh Tra",
            "legal_rep": "Trần A",
        })
        raw = handle_taxadmin_audit({
            "tax_code": "0108999888",
            "decision_number": "QĐ-MCP-01",
            "underdeclared_tax_vnd": 30_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["penalty_amount_vnd"] == 6_000_000.0

    def test_mcp_standalone_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        raw = handle_taxadmin_list({"category": "all"})
        data = json.loads(raw)
        assert data["ok"] is True
        assert "taxpayers" in data

    def test_mcp_standalone_status(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        raw = handle_taxadmin_status({})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

    def test_core_mcp_server_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "server_taxadmin.db"
        monkeypatch.setenv("MEKONG_TAXADMIN_DB", str(db_file))

        server = MekongMcpServer()
        app = server.create_app()
        assert app is not None

        # Verify handlers callable via server instance
        res_tp = server._handle_taxadmin_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Server Tax Test",
            legal_rep="Trần S",
        )
        data_tp = json.loads(res_tp)
        assert data_tp["ok"] is True

        res_st = server._handle_taxadmin_status()
        data_st = json.loads(res_st)
        assert data_st["ok"] is True
        assert data_st["taxpayer_count"] == 1


# =============================================================================
# 4. Edge Cases & Statutory Tax Rule Verifications
# =============================================================================

class TestTaxAdminEdgeCases:
    def test_all_taxpayer_types(self, temp_engine: TaxAdminEngine) -> None:
        for idx, t_type in enumerate(["ENTERPRISE", "INDIVIDUAL_BUSINESS", "FOREIGN_CONTRACTOR", "DEPENDENT_UNIT"]):
            code = f"01089998{idx:02d}"
            res = temp_engine.register_taxpayer(
                tax_code=code,
                taxpayer_name=f"Entity {t_type}",
                legal_rep="Rep",
                taxpayer_type=t_type,
            )
            assert res["taxpayer_type"] == t_type

    def test_all_tax_types(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="All Tax Entity",
            legal_rep="Rep",
        )
        for t_type in ["CIT", "VAT", "PIT", "FCT", "EXCISE", "RESOURCE_ROYALTY", "ENVIRONMENTAL"]:
            res = temp_engine.assess_tax_and_interest(
                tax_code="0108999888",
                tax_type=t_type,
                tax_period="2026",
                declared_amount_vnd=10_000_000.0,
                assessed_amount_vnd=10_000_000.0,
                due_date_str="2026-04-30",
            )
            assert res["tax_type"] == t_type

    def test_all_invoice_vat_rates(self, temp_engine: TaxAdminEngine) -> None:
        temp_engine.register_taxpayer(
            tax_code="0108999888",
            taxpayer_name="Seller",
            legal_rep="Rep",
        )
        for rate in [0.0, 5.0, 8.0, 10.0]:
            inv = temp_engine.issue_electronic_invoice(
                invoice_code=f"1C26TAA-RATE-{int(rate)}",
                invoice_type="VAT_INVOICE",
                seller_tax_code="0108999888",
                buyer_tax_code="0100109106",
                buyer_name="Buyer",
                subtotal_vnd=100_000_000.0,
                vat_rate_pct=rate,
            )
            expected_vat = 100_000_000.0 * (rate / 100.0)
            assert inv["vat_amount_vnd"] == expected_vat
            assert inv["total_amount_vnd"] == 100_000_000.0 + expected_vat
