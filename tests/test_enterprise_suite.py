# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Comprehensive test suite for Mekong Enterprise Suite (Phases 154 - 158).

Statutory & Technical Specifications Tested:
1. Law on Enterprises 2020: 90-day charter capital contribution obligation.
2. Law on Investment 2020: FDI Foreign Ownership Limits & approvals.
3. Law on Intellectual Property 2022: 45 Nice classes, distinctiveness scoring.
4. Labor Code 2019 & Decree 74/2024/ND-CP: Net/Gross, statutory BHXH/BHYT/BHTN, 7-bracket PIT.
5. Napas 247 VietQR Standard (EMVCo) & HMAC-SHA256 Webhook Reconciliation.
6. Commercial Law 2005 (Article 301): 8% contract breach penalty cap & 360-degree audit health.
7. CLI command surface & dual MCP server integration.
"""

from __future__ import annotations

import json
from typer.testing import CliRunner

from src.core.enterprise_suite_engine import (
    EnterpriseAuditEngine,
    EnterpriseFDIEngine,
    IntellectualPropertyEngine,
    InvestmentSector,
    LaborHRMEngine,
    Shareholder,
    VietQRReconEngine,
)
from src.cli.commands.enterprise_command import enterprise_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as script_mcp


runner = CliRunner()


# ==============================================================================
# 1. Doanh nghiệp & Đầu tư FDI (Law on Enterprises & Investment 2020)
# ==============================================================================


class TestEnterpriseFDIEngine:
    """Test suite for Charter Capital 90-day rule and FDI Ownership limits."""

    def test_charter_capital_fully_paid(self):
        """Doanh nghiệp góp đủ 100% vốn trong hạn 90 ngày."""
        res = EnterpriseFDIEngine.check_charter_capital(
            committed_vnd=2_000_000_000.0,
            contributed_vnd=2_000_000_000.0,
            inc_date="2026-01-01",
            audit_date="2026-02-01",
        )
        assert res.is_fully_paid is True
        assert res.is_overdue_90_days is False
        assert res.remaining_unpaid == 0.0
        assert res.contribution_ratio_pct == 100.0
        assert res.deadline_date == "2026-04-01"

    def test_charter_capital_underpaid_within_deadline(self):
        """Góp thiếu nhưng còn trong hạn 90 ngày."""
        res = EnterpriseFDIEngine.check_charter_capital(
            committed_vnd=1_000_000_000.0,
            contributed_vnd=600_000_000.0,
            inc_date="2026-01-01",
            audit_date="2026-02-15",
        )
        assert res.is_fully_paid is False
        assert res.is_overdue_90_days is False
        assert res.remaining_unpaid == 400_000_000.0
        assert res.contribution_ratio_pct == 60.0
        assert res.days_passed == 45
        assert res.days_remaining_in_window == 45

    def test_charter_capital_overdue_penalty_triggered(self):
        """Quá hạn 90 ngày chưa góp đủ vốn, rủi ro phạt hành chính."""
        res = EnterpriseFDIEngine.check_charter_capital(
            committed_vnd=1_000_000_000.0,
            contributed_vnd=500_000_000.0,
            inc_date="2025-10-01",
            audit_date="2026-02-01",
        )
        assert res.is_fully_paid is False
        assert res.is_overdue_90_days is True
        assert res.remaining_unpaid == 500_000_000.0
        assert "phạt tiền từ 30-50 triệu VNĐ" in res.penalty_risk_vn

    def test_fdi_ownership_it_software_100_pct(self):
        """Ngành phần mềm IT cho phép sở hữu nước ngoài tối đa 100%."""
        shs = [
            Shareholder(name="Foreign Fund", is_foreign=True, nationality="SG", capital_committed=100.0, capital_contributed=100.0)
        ]
        res = EnterpriseFDIEngine.assess_fdi_ownership(shs, InvestmentSector.IT_SOFTWARE)
        assert res.total_foreign_ownership_pct == 100.0
        assert res.cap_allowed_pct == 100.0
        assert res.is_compliant is True
        assert res.requires_approval_prior is True

    def test_fdi_ownership_logistics_capped_at_51_pct(self):
        """Ngành logistics giới hạn 51% vốn ngoại."""
        shs = [
            Shareholder(name="VN Partner", is_foreign=False, nationality="VN", capital_committed=49.0, capital_contributed=49.0),
            Shareholder(name="Foreign Partner", is_foreign=True, nationality="JP", capital_committed=51.0, capital_contributed=51.0),
        ]
        res = EnterpriseFDIEngine.assess_fdi_ownership(shs, InvestmentSector.LOGISTICS)
        assert res.total_foreign_ownership_pct == 51.0
        assert res.cap_allowed_pct == 51.0
        assert res.is_compliant is True

    def test_fdi_ownership_exceeds_cap_violation(self):
        """Sở hữu ngoại vượt trần quy định trong ngành Fintech/Ngân hàng (vượt 50%)."""
        shs = [
            Shareholder(name="Foreign Investor", is_foreign=True, nationality="US", capital_committed=65.0, capital_contributed=65.0),
            Shareholder(name="VN Founder", is_foreign=False, nationality="VN", capital_committed=35.0, capital_contributed=35.0),
        ]
        res = EnterpriseFDIEngine.assess_fdi_ownership(shs, InvestmentSector.FINTECH)
        assert res.total_foreign_ownership_pct == 65.0
        assert res.cap_allowed_pct == 50.0
        assert res.is_compliant is False


# ==============================================================================
# 2. Sở hữu Trí tuệ (Law on Intellectual Property 2022)
# ==============================================================================


class TestIntellectualPropertyEngine:
    """Test suite for Nice classes and Trademark Distinctiveness."""

    def test_nice_classes_count_and_lookup(self):
        """Đảm bảo chuẩn 45 nhóm Nice quốc tế được hỗ trợ đầy đủ."""
        assert len(IntellectualPropertyEngine.NICE_CLASSES) == 45
        assert "máy tính" in IntellectualPropertyEngine.get_nice_class_description(9)
        assert "quảng cáo" in IntellectualPropertyEngine.get_nice_class_description(35)
        assert "phần mềm" in IntellectualPropertyEngine.get_nice_class_description(42)

    def test_trademark_distinctive_name(self):
        """Nhãn hiệu sáng tạo có tính phân biệt cao, đủ điều kiện cấp bằng."""
        res = IntellectualPropertyEngine.evaluate_trademark("MekongMind", nice_class=9)
        assert res.is_registrable is True
        assert res.distinctiveness_score >= 80
        assert "Đủ điều kiện nộp đơn" in res.advice_vn

    def test_trademark_generic_descriptive_rejected(self):
        """Nhãn hiệu mô tả thuần túy hàng hóa hoặc quá ngắn bị trừ điểm nặng."""
        res = IntellectualPropertyEngine.evaluate_trademark("Phần mềm tốt", nice_class=42)
        assert res.is_registrable is False
        assert res.distinctiveness_score < 70
        assert any("mô tả" in r for r in res.risk_factors)


# ==============================================================================
# 3. Lao động & Tiền lương (Labor Code 2019 & Decree 74/2024/ND-CP)
# ==============================================================================


class TestLaborHRMEngine:
    """Test suite for Gross/Net calculations, statutory social insurance, and PIT."""

    def test_regional_minimum_wages(self):
        """Kiểm tra bảng lương tối thiểu vùng theo Nghị định 74/2024/NĐ-CP."""
        assert LaborHRMEngine.REGIONAL_MINIMUM_WAGE[1] == 4_960_000.0
        assert LaborHRMEngine.REGIONAL_MINIMUM_WAGE[2] == 4_410_000.0
        assert LaborHRMEngine.REGIONAL_MINIMUM_WAGE[3] == 3_860_000.0
        assert LaborHRMEngine.REGIONAL_MINIMUM_WAGE[4] == 3_450_000.0

    def test_payroll_under_tax_threshold(self):
        """Lương thấp dưới ngưỡng giảm trừ gia cảnh bản thân (11 triệu VNĐ) không phải đóng PIT."""
        p = LaborHRMEngine.calculate_payroll(gross_salary=10_000_000.0, dependents=0, region=1)
        assert p.gross_salary == 10_000_000.0
        # Bảo hiểm NLĐ: 8% + 1.5% + 1% = 10.5% = 1,050,000 VNĐ
        assert p.ee_bhxh == 800_000.0
        assert p.ee_bhyt == 150_000.0
        assert p.ee_bhtn == 100_000.0
        assert p.ee_total_insurance == 1_050_000.0
        assert p.pit_amount == 0.0
        assert p.net_salary == 8_950_000.0
        # Chi phí DN: 17.5% + 3% + 1% + 2% = 23.5% = 2,350,000 VNĐ
        assert p.er_total_insurance == 2_350_000.0
        assert p.total_company_burden == 12_350_000.0

    def test_payroll_high_salary_insurance_cap(self):
        """Lương cao vượt trần 20 lần mức lương cơ sở (20 * 2.34m = 46.8m VNĐ) bị chặn trần đóng BHXH/BHYT."""
        gross = 100_000_000.0
        p = LaborHRMEngine.calculate_payroll(gross_salary=gross, dependents=1, region=1)
        # Trần đóng BHXH/BHYT là 46,800,000
        assert p.base_insurance_salary == 46_800_000.0
        assert p.ee_bhxh == round(46_800_000.0 * 0.08)
        assert p.ee_bhyt == round(46_800_000.0 * 0.015)
        # BHTN trần 20 lần lương tối thiểu vùng I: 20 * 4,960,000 = 99,200,000
        assert p.ee_bhtn == round(99_200_000.0 * 0.01)
        # PIT lũy tiến 7 bậc phải phát sinh dương
        assert p.pit_amount > 0.0
        assert p.net_salary < gross
        assert p.total_company_burden > gross


# ==============================================================================
# 4. Đối soát VietQR & Ngân hàng (Napas 247 EMVCo & Webhooks)
# ==============================================================================


class TestVietQRReconEngine:
    """Test suite for EMVCo QR code payload and HMAC webhook verification."""

    def test_generate_vietqr_payload_crc(self):
        """Sinh chuỗi Napas 247 VietQR EMVCo và kiểm tra định dạng và checksum CRC16."""
        payload = VietQRReconEngine.generate_vietqr_payload(
            bank_bin="970422",
            account_number="0123456789",
            amount=500_000,
            memo="MEKONG-TEST",
        )
        assert payload.startswith("00020101021238")
        assert "5303704" in payload
        assert "5406500000" in payload
        assert "5802VN" in payload
        assert "62" in payload  # Additional Data Field
        assert "6304" in payload  # CRC Tag
        # 4 ký tự cuối cùng phải là CRC16 dạng HEX hoa
        crc_str = payload[-4:]
        assert len(crc_str) == 4
        assert all(c in "0123456789ABCDEF" for c in crc_str)

    def test_webhook_hmac_signature_verification(self):
        """Xác thực chữ ký số HMAC-SHA256 ngân hàng bảo đảm chống giả mạo."""
        secret = "mekong-super-secret-key-2026"
        raw_body = json.dumps({"trans_id": "TX999", "amount": 2500000, "memo": "ORDER-01"})

        # Ký hợp lệ
        import hmac
        import hashlib
        valid_sig = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
        assert VietQRReconEngine.verify_webhook_signature(raw_body, valid_sig, secret) is True

        # Giả mạo hoặc sai secret
        assert VietQRReconEngine.verify_webhook_signature(raw_body, "tampered_sig", secret) is False
        assert VietQRReconEngine.verify_webhook_signature(raw_body, valid_sig, "wrong_secret") is False

    def test_reconcile_transaction_matching(self):
        """Kiểm tra đối soát hóa đơn kế toán (112/131)."""
        tx = {"amount": 1_200_000, "memo": "THANH TOAN DON HANG DH-888"}
        inv = {"amount": 1_200_000, "code": "DH-888"}

        res = VietQRReconEngine.reconcile_transaction(tx, inv)
        assert res.matched is True
        assert res.diff_amount == 0.0
        assert res.accounting_entry == "Nợ 112 / Có 131"

    def test_reconcile_transaction_mismatch(self):
        """Phát hiện chênh lệch thiếu tiền khi đối soát."""
        tx = {"amount": 1_000_000, "memo": "DH-888"}
        inv = {"amount": 1_200_000, "code": "DH-888"}

        res = VietQRReconEngine.reconcile_transaction(tx, inv)
        assert res.matched is False
        assert res.diff_amount == 200_000.0


# ==============================================================================
# 5. Hợp đồng Thương mại & Audit Hub (Article 301 LTM 2005)
# ==============================================================================


class TestEnterpriseAuditEngine:
    """Test suite for 8% contract breach penalty cap and 360 Health Index."""

    def test_contract_penalty_compliant_at_8_pct(self):
        """Mức phạt thỏa thuận <= 8% tuân thủ Điều 301 Luật Thương mại 2005."""
        res = EnterpriseAuditEngine.review_contract_penalty(contract_value=1_000_000_000.0, agreed_penalty_pct=8.0)
        assert res.is_commercial_law_compliant is True
        assert res.max_legal_penalty_pct == 8.0
        assert res.max_legal_penalty_amount == 80_000_000.0
        assert "Hợp pháp" in res.warning_vn

    def test_contract_penalty_exceeds_cap_void(self):
        """Mức phạt thỏa thuận 15% vượt trần 8% bị vô hiệu phần vượt mức."""
        res = EnterpriseAuditEngine.review_contract_penalty(contract_value=500_000_000.0, agreed_penalty_pct=15.0)
        assert res.is_commercial_law_compliant is False
        assert res.agreed_penalty_amount == 75_000_000.0
        assert res.max_legal_penalty_amount == 40_000_000.0
        assert "VƯỢT TRẦN LUẬT ĐỊNH" in res.warning_vn

    def test_enterprise_health_audit_score(self):
        """Đánh giá sức khỏe toàn diện 5 trụ cột."""
        cap_status = EnterpriseFDIEngine.check_charter_capital(1_000_000_000.0, 1_000_000_000.0, "2026-01-01")
        tm_status = IntellectualPropertyEngine.evaluate_trademark("MekongAI", 9)
        report = EnterpriseAuditEngine.audit_enterprise_health(
            capital_status=cap_status,
            fdi_status=None,
            trademark_result=tm_status,
            payroll_count=15,
            unsettled_invoices_pct=2.0,
        )
        assert report.overall_score >= 90
        assert report.risk_level == "LOW"
        assert len(report.pillar_scores) == 5


# ==============================================================================
# 6. CLI Command Surface Tests
# ==============================================================================


class TestEnterpriseCLI:
    """Test suite for CLI subcommands."""

    def test_cli_dashboard(self):
        """Chạy mekong enterprise hiển thị dashboard."""
        res = runner.invoke(enterprise_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG ĐIỀU HÀNH DOANH NGHIỆP" in res.stdout

    def test_cli_corp_command(self):
        """Chạy lệnh corp."""
        res = runner.invoke(enterprise_app, ["corp", "--committed", "1000000000", "--contributed", "1000000000", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["charter_capital"]["is_fully_paid"] is True

    def test_cli_ip_command(self):
        """Chạy lệnh ip."""
        res = runner.invoke(enterprise_app, ["ip", "--mark", "MekongBiz", "--class", "9", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_registrable"] is True

    def test_cli_labor_command(self):
        """Chạy lệnh labor."""
        res = runner.invoke(enterprise_app, ["labor", "--gross", "25000000", "--dependents", "1", "--region", "1", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["net_salary"] > 0

    def test_cli_recon_command(self):
        """Chạy lệnh recon."""
        res = runner.invoke(enterprise_app, ["recon", "--bin", "970422", "--account", "0987654321", "--amount", "300000", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "00020101021238" in data["emvco_payload"]

    def test_cli_contract_command(self):
        """Chạy lệnh contract."""
        res = runner.invoke(enterprise_app, ["contract", "--value", "200000000", "--penalty-pct", "8", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_commercial_law_compliant"] is True

    def test_cli_audit_command(self):
        """Chạy lệnh audit."""
        res = runner.invoke(enterprise_app, ["audit", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["overall_score"] > 0


# ==============================================================================
# 7. Dual MCP Server Tools Tests
# ==============================================================================


class TestEnterpriseMCP:
    """Test suite for MCP server handlers."""

    def test_core_mcp_server_handlers(self):
        """Kiểm tra handlers trong MekongMcpServer (src/core/mcp_server.py)."""
        server = MekongMcpServer()

        # Corp
        res_corp = json.loads(server._handle_enterprise_corp(committed=500_000_000, contributed=500_000_000))
        assert res_corp["ok"] is True
        assert res_corp["charter_capital"]["is_fully_paid"] is True

        # IP
        res_ip = json.loads(server._handle_enterprise_ip(mark="SophiaOS", nice_class=42))
        assert res_ip["ok"] is True
        assert res_ip["distinctiveness_score"] > 0

        # Labor
        res_labor = json.loads(server._handle_enterprise_labor(gross=15_000_000, dependents=0, region=1))
        assert res_labor["ok"] is True
        assert res_labor["net_salary"] > 0

        # Recon
        res_recon = json.loads(server._handle_enterprise_recon(bank_bin="970422", account_number="123456"))
        assert res_recon["ok"] is True
        assert "emvco_payload" in res_recon

        # Audit
        res_audit = json.loads(server._handle_enterprise_audit(contract_value=100_000_000, agreed_penalty_pct=8.0))
        assert res_audit["ok"] is True
        assert "audit" in res_audit
        assert "contract_check" in res_audit

    def test_script_mcp_server_handlers(self):
        """Kiểm tra handlers trong scripts/mcp_server.py."""
        # Corp
        res_corp = json.loads(script_mcp.handle_enterprise_corp({"committed": 1_000_000_000, "contributed": 1_000_000_000}))
        assert res_corp["ok"] is True

        # IP
        res_ip = json.loads(script_mcp.handle_enterprise_ip({"mark": "MekongPay", "nice_class": 36}))
        assert res_ip["ok"] is True

        # Labor
        res_labor = json.loads(script_mcp.handle_enterprise_labor({"gross": 30_000_000, "dependents": 2, "region": 1}))
        assert res_labor["ok"] is True

        # Recon
        res_recon = json.loads(script_mcp.handle_enterprise_recon({"bank_bin": "970422", "account_number": "88888888"}))
        assert res_recon["ok"] is True

        # Audit
        res_audit = json.loads(script_mcp.handle_enterprise_audit({"contract_value": 500_000_000, "agreed_penalty_pct": 5.0}))
        assert res_audit["ok"] is True
