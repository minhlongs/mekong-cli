"""
Unit and integration tests for Vietnamese State Audit (KTNN) & Public Financial Oversight Suite.
Governed by Law on State Audit 2015 (Law No. 81/2015/QH13) & Amending Law 2019 (Law No. 55/2019/QH14).
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.stateaudit_command import app as stateaudit_app
from src.core.stateaudit_engine import StateAuditEngine


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_STATEAUDIT_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestStateAuditEngine:
    def test_register_engagement_valid(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        res = engine.register_engagement(
            engagement_code="KTNN-2026-BXD-01",
            decision_number="QĐ 112/QĐ-KTNN",
            audited_entity="Bộ Xây dựng",
            entity_type="MINISTRY",
            audit_type="COMPLIANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Nguyễn Văn Kiểm",
            start_date="2026-03-01",
            end_date="2026-04-30",
        )
        assert res["engagement_code"] == "KTNN-2026-BXD-01"
        assert res["audited_entity"] == "Bộ Xây dựng"
        assert res["audit_scope_year"] == 2025
        assert res["status"] == "IN_PROGRESS"

    def test_register_engagement_duplicate(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-DUP",
            decision_number="QĐ 01",
            audited_entity="UBND Tỉnh A",
            entity_type="PROVINCIAL_GOVERNMENT",
            audit_type="FINANCIAL_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Trần Văn A",
            start_date="2026-01-01",
            end_date="2026-02-01",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_engagement(
                engagement_code="KTNN-DUP",
                decision_number="QĐ 02",
                audited_entity="UBND Tỉnh A",
                entity_type="PROVINCIAL_GOVERNMENT",
                audit_type="FINANCIAL_AUDIT",
                audit_scope_year=2025,
                lead_auditor="Trần Văn A",
                start_date="2026-01-01",
                end_date="2026-02-01",
            )

    def test_register_engagement_invalid_inputs(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid entity_type"):
            engine.register_engagement(
                engagement_code="KTNN-INV1",
                decision_number="QĐ 01",
                audited_entity="Cục A",
                entity_type="PRIVATE_COMPANY",
                audit_type="COMPLIANCE_AUDIT",
                audit_scope_year=2025,
                lead_auditor="Trần B",
                start_date="2026-01-01",
                end_date="2026-02-01",
            )
        with pytest.raises(ValueError, match="Invalid audit_type"):
            engine.register_engagement(
                engagement_code="KTNN-INV2",
                decision_number="QĐ 01",
                audited_entity="Cục A",
                entity_type="MINISTRY",
                audit_type="TAX_INSPECTION",
                audit_scope_year=2025,
                lead_auditor="Trần B",
                start_date="2026-01-01",
                end_date="2026-02-01",
            )
        with pytest.raises(ValueError, match="end_date cannot be earlier"):
            engine.register_engagement(
                engagement_code="KTNN-INV3",
                decision_number="QĐ 01",
                audited_entity="Cục A",
                entity_type="MINISTRY",
                audit_type="COMPLIANCE_AUDIT",
                audit_scope_year=2025,
                lead_auditor="Trần B",
                start_date="2026-05-01",
                end_date="2026-04-01",
            )

    def test_record_finding_valid(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-ENG-01",
            decision_number="QĐ 10",
            audited_entity="UBND Tỉnh Quảng Ninh",
            entity_type="PROVINCIAL_GOVERNMENT",
            audit_type="COMPLIANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Lê Văn C",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        res = engine.record_finding(
            finding_code="FIND-2026-QN01",
            engagement_code="KTNN-ENG-01",
            domain="PUBLIC_INVESTMENT",
            description="Nghiệm thu thanh toán khối lượng xây lắp đào đắp sai cự ly vận chuyển đất",
            statutory_violation="Khoản 2 Điều 132 Luật Xây dựng 2014",
            severity="HIGH",
            evidence_summary="Biên bản nghiệm thu đợt 4 và nhật ký thi công",
        )
        assert res["finding_code"] == "FIND-2026-QN01"
        assert res["domain"] == "PUBLIC_INVESTMENT"
        assert res["severity"] == "HIGH"

    def test_record_finding_invalid_engagement(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="does not exist"):
            engine.record_finding(
                finding_code="FIND-NOENG",
                engagement_code="NON_EXISTENT_ENG",
                domain="BUDGET_REVENUE",
                description="Trốn thuế",
                statutory_violation="Luật Quản lý thuế",
            )

    def test_issue_recommendation_valid(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-ENG-02",
            decision_number="QĐ 20",
            audited_entity="Tập đoàn Điện lực Việt Nam (EVN)",
            entity_type="STATE_OWNED_ENTERPRISE",
            audit_type="FINANCIAL_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Phạm Thị D",
            start_date="2026-02-01",
            end_date="2026-04-01",
        )
        engine.record_finding(
            finding_code="FIND-EVN-01",
            engagement_code="KTNN-ENG-02",
            domain="BUDGET_EXPENDITURE",
            description="Hạch toán chi phí quản lý doanh nghiệp không hợp lý hợp lệ",
            statutory_violation="Điều 6 Thông tư 96/2015/TT-BTC",
            severity="MEDIUM",
        )
        res = engine.issue_recommendation(
            recommendation_code="REC-EVN-01",
            finding_code="FIND-EVN-01",
            recommendation_type="EXPENDITURE_DISALLOWANCE",
            description="Giảm trừ chi phí sản xuất kinh doanh khi xác định thuế TNDN",
            target_agency="Công ty Nhiệt điện A",
            settlement_deadline="2026-09-30",
            amount_vnd=15000000000.0,
        )
        assert res["recommendation_code"] == "REC-EVN-01"
        assert res["recommendation_type"] == "EXPENDITURE_DISALLOWANCE"
        assert res["amount_vnd"] == 15000000000.0
        assert res["status"] == "PENDING"

    def test_record_settlement_partial_and_full(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-ENG-03",
            decision_number="QĐ 30",
            audited_entity="Bộ Giao thông Vận tải",
            entity_type="MINISTRY",
            audit_type="COMPLIANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Trương Quốc E",
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        engine.record_finding(
            finding_code="FIND-BGTVT-01",
            engagement_code="KTNN-ENG-03",
            domain="PUBLIC_INVESTMENT",
            description="Thanh toán tạm ứng vượt khối lượng hoàn thành",
            statutory_violation="Khoản 3 Điều 18 Nghị định 99/2021/NĐ-CP",
            severity="HIGH",
        )
        engine.issue_recommendation(
            recommendation_code="REC-BGTVT-01",
            finding_code="FIND-BGTVT-01",
            recommendation_type="REIMBURSEMENT",
            description="Thu hồi khoản tạm ứng quá hạn nộp vào tài khoản tạm giữ của KTNN",
            target_agency="Ban QLDA 7",
            settlement_deadline="2026-08-31",
            amount_vnd=20000000000.0,
        )

        # Partial settlement: 8 billion
        p1 = engine.record_settlement(
            settlement_id="SETTLE-01",
            recommendation_code="REC-BGTVT-01",
            settlement_date="2026-05-15",
            treasury_voucher_number="VOUCHER-KB-01",
            amount_settled_vnd=8000000000.0,
            evidence_notes="Nộp đợt 1 vào Kho bạc",
        )
        assert p1["new_status"] == "PARTIALLY_IMPLEMENTED"
        assert p1["cumulative_implemented_vnd"] == 8000000000.0

        # Complete settlement: 12 billion
        p2 = engine.record_settlement(
            settlement_id="SETTLE-02",
            recommendation_code="REC-BGTVT-01",
            settlement_date="2026-06-20",
            treasury_voucher_number="VOUCHER-KB-02",
            amount_settled_vnd=12000000000.0,
            evidence_notes="Nộp đợt 2 đủ 100%",
        )
        assert p2["new_status"] == "FULLY_IMPLEMENTED"
        assert p2["cumulative_implemented_vnd"] == 20000000000.0

    def test_conclude_engagement(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-CONC-01",
            decision_number="QĐ 99",
            audited_entity="Bộ Y tế",
            entity_type="MINISTRY",
            audit_type="PERFORMANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Đỗ Thị F",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        res = engine.conclude_engagement(engagement_code="KTNN-CONC-01", status="PUBLISHED")
        assert res["status"] == "PUBLISHED"
        assert res["status_updated"] is True

    def test_list_records(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-LST-01",
            decision_number="QĐ 100",
            audited_entity="UBND Tỉnh B",
            entity_type="PROVINCIAL_GOVERNMENT",
            audit_type="FINANCIAL_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Hoàng Văn G",
            start_date="2026-01-01",
            end_date="2026-02-01",
        )
        records = engine.list_records(record_type="all")
        assert len(records["engagements"]) == 1
        assert "findings" in records
        assert "recommendations" in records
        assert "settlements" in records

    def test_get_telemetry_status(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-TEL-01",
            decision_number="QĐ 200",
            audited_entity="UBND Tỉnh C",
            entity_type="PROVINCIAL_GOVERNMENT",
            audit_type="COMPREHENSIVE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Vũ Văn H",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        engine.record_finding(
            finding_code="FIND-TEL-01",
            engagement_code="KTNN-TEL-01",
            domain="TAX_COLLECTION",
            description="Để nợ đọng tiền thuế sử dụng đất quá hạn không có biện pháp cưỡng chế",
            statutory_violation="Luật Quản lý thuế",
            severity="CRITICAL",
        )
        engine.issue_recommendation(
            recommendation_code="REC-TEL-01",
            finding_code="FIND-TEL-01",
            recommendation_type="REVENUE_INCREASE",
            description="Truy thu tiền thuế sử dụng đất nộp ngân sách",
            target_agency="Cục Thuế Tỉnh C",
            settlement_deadline="2026-06-30",
            amount_vnd=5000000000.0,
        )
        engine.issue_recommendation(
            recommendation_code="REC-TEL-02",
            finding_code="FIND-TEL-01",
            recommendation_type="CRIMINAL_REFERRAL",
            description="Chuyển hồ sơ sang CQĐT do cố ý bỏ qua hành vi trốn thuế của doanh nghiệp",
            target_agency="Cơ quan CSĐT Công an Tỉnh C",
            settlement_deadline="2026-05-30",
            amount_vnd=0.0,
        )
        telemetry = engine.get_telemetry_status()
        assert telemetry["total_audit_engagements"] == 1
        assert telemetry["total_audit_findings"] == 1
        assert telemetry["total_recommendations"] == 2
        assert telemetry["total_recommended_amount_vnd"] == 5000000000.0
        assert telemetry["criminal_referrals_count"] == 1


class TestStateAuditCli:
    def test_cli_default_callback(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(stateaudit_app, [])
        assert result.exit_code == 0
        assert "KIỂM TOÁN NHÀ NƯỚC VIỆT NAM" in result.output

    def test_cli_status_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(stateaudit_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_audit_engagements" in data
        assert "total_recommended_amount_vnd" in data

    def test_cli_engagement_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            stateaudit_app,
            [
                "engagement",
                "--code", "KTNN-CLI-01",
                "--decision", "QĐ 555/QĐ-KTNN",
                "--entity", "Bộ Tài chính",
                "--type", "MINISTRY",
                "--audit-type", "FINANCIAL_AUDIT",
                "--year", "2025",
                "--lead", "Kiểm toán viên Trưởng",
                "--start", "2026-02-01",
                "--end", "2026-04-15",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["engagement_code"] == "KTNN-CLI-01"
        assert data["audited_entity"] == "Bộ Tài chính"

    def test_cli_finding_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            stateaudit_app,
            [
                "engagement",
                "--code", "KTNN-CLI-02",
                "--decision", "QĐ 556",
                "--entity", "Bộ Xây dựng",
                "--year", "2025",
                "--lead", "Trưởng đoàn A",
                "--start", "2026-01-01",
                "--end", "2026-03-01",
            ],
        )
        result = runner.invoke(
            stateaudit_app,
            [
                "finding",
                "--code", "FIND-CLI-01",
                "--engagement", "KTNN-CLI-02",
                "--domain", "PUBLIC_INVESTMENT",
                "--desc", "Dự toán xây lắp tính thừa khối lượng cát san nền",
                "--violation", "Thông tư 12/2021/TT-BXD",
                "--severity", "HIGH",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["finding_code"] == "FIND-CLI-01"

    def test_cli_recommend_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            stateaudit_app,
            [
                "engagement",
                "--code", "KTNN-CLI-03",
                "--decision", "QĐ 557",
                "--entity", "UBND TP. Cần Thơ",
                "--year", "2025",
                "--lead", "Trưởng đoàn B",
                "--start", "2026-01-01",
                "--end", "2026-03-01",
            ],
        )
        runner.invoke(
            stateaudit_app,
            [
                "finding",
                "--code", "FIND-CLI-03",
                "--engagement", "KTNN-CLI-03",
                "--domain", "BUDGET_REVENUE",
                "--desc", "Chưa thu tiền cấp quyền khai thác cát sông",
                "--violation", "Luật Khoáng sản",
            ],
        )
        result = runner.invoke(
            stateaudit_app,
            [
                "recommend",
                "--code", "REC-CLI-01",
                "--finding", "FIND-CLI-03",
                "--type", "REVENUE_INCREASE",
                "--desc", "Truy thu tiền cấp quyền khai thác cát nộp ngân sách địa phương",
                "--agency", "Sở Tài nguyên và Môi trường",
                "--deadline", "2026-10-31",
                "--amount", "8500000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["amount_vnd"] == 8500000000.0

    def test_cli_settle_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            stateaudit_app,
            [
                "engagement",
                "--code", "KTNN-CLI-04",
                "--decision", "QĐ 558",
                "--entity", "Cục Hàng không",
                "--year", "2025",
                "--lead", "Trưởng đoàn C",
                "--start", "2026-01-01",
                "--end", "2026-03-01",
            ],
        )
        runner.invoke(
            stateaudit_app,
            [
                "finding",
                "--code", "FIND-CLI-04",
                "--engagement", "KTNN-CLI-04",
                "--domain", "BUDGET_EXPENDITURE",
                "--desc", "Chi sai chế độ phụ cấp",
                "--violation", "Nghị định 204",
            ],
        )
        runner.invoke(
            stateaudit_app,
            [
                "recommend",
                "--code", "REC-CLI-04",
                "--finding", "FIND-CLI-04",
                "--type", "REIMBURSEMENT",
                "--desc", "Thu hồi phụ cấp chi sai nộp NSNN",
                "--agency", "Cục Hàng không",
                "--deadline", "2026-09-30",
                "--amount", "500000000",
            ],
        )
        result = runner.invoke(
            stateaudit_app,
            [
                "settle",
                "--id", "SETTLE-CLI-01",
                "--code", "REC-CLI-04",
                "--date", "2026-07-15",
                "--voucher", "GNT-KB-8899",
                "--amount", "500000000",
                "--evidence", "Chứng từ nộp NSNN",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["new_status"] == "FULLY_IMPLEMENTED"

    def test_cli_conclude_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            stateaudit_app,
            [
                "engagement",
                "--code", "KTNN-CLI-05",
                "--decision", "QĐ 559",
                "--entity", "Viện Hàn lâm KH&CN",
                "--year", "2025",
                "--lead", "Trưởng đoàn D",
                "--start", "2026-01-01",
                "--end", "2026-03-01",
            ],
        )
        result = runner.invoke(
            stateaudit_app,
            [
                "conclude",
                "--code", "KTNN-CLI-05",
                "--status", "CONCLUDED",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "CONCLUDED"

    def test_cli_list_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(stateaudit_app, ["list", "--type", "all", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "engagements" in data


class TestStateAuditMcp:
    def test_mcp_standalone_engagement(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_stateaudit_engagement

        res_str = handle_stateaudit_engagement({
            "engagement_code": "KTNN-MCP-01",
            "decision_number": "QĐ 888/QĐ-KTNN",
            "audited_entity": "Bộ Công Thương",
            "audit_scope_year": 2025,
            "lead_auditor": "Kiểm toán viên A",
            "start_date": "2026-03-01",
            "end_date": "2026-05-01",
        })
        res = json.loads(res_str)
        assert res["engagement_code"] == "KTNN-MCP-01"

    def test_mcp_standalone_finding(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_stateaudit_engagement,
            handle_stateaudit_finding,
        )

        handle_stateaudit_engagement({
            "engagement_code": "KTNN-MCP-02",
            "decision_number": "QĐ 889",
            "audited_entity": "UBND Tỉnh D",
            "audit_scope_year": 2025,
            "lead_auditor": "Kiểm toán viên B",
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
        })
        res_str = handle_stateaudit_finding({
            "finding_code": "FIND-MCP-01",
            "engagement_code": "KTNN-MCP-02",
            "domain": "ASSET_MANAGEMENT",
            "description": "Cho thuê đất công không qua đấu giá quyền sử dụng đất",
            "statutory_violation": "Điều 118 Luật Đất đai 2013",
            "severity": "CRITICAL",
        })
        res = json.loads(res_str)
        assert res["finding_code"] == "FIND-MCP-01"

    def test_mcp_standalone_recommend(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_stateaudit_engagement,
            handle_stateaudit_finding,
            handle_stateaudit_recommend,
        )

        handle_stateaudit_engagement({
            "engagement_code": "KTNN-MCP-03",
            "decision_number": "QĐ 890",
            "audited_entity": "UBND Tỉnh E",
            "audit_scope_year": 2025,
            "lead_auditor": "Kiểm toán viên C",
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
        })
        handle_stateaudit_finding({
            "finding_code": "FIND-MCP-03",
            "engagement_code": "KTNN-MCP-03",
            "domain": "BUDGET_REVENUE",
            "description": "Thu tiền sử dụng đất thiếu",
            "statutory_violation": "Luật Đất đai",
        })
        res_str = handle_stateaudit_recommend({
            "recommendation_code": "REC-MCP-01",
            "finding_code": "FIND-MCP-03",
            "recommendation_type": "REVENUE_INCREASE",
            "description": "Truy thu tiền sử dụng đất",
            "target_agency": "UBND Huyện X",
            "settlement_deadline": "2026-11-30",
            "amount_vnd": 3000000000,
        })
        res = json.loads(res_str)
        assert res["recommendation_code"] == "REC-MCP-01"

    def test_mcp_standalone_settle(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_stateaudit_engagement,
            handle_stateaudit_finding,
            handle_stateaudit_recommend,
            handle_stateaudit_settle,
        )

        handle_stateaudit_engagement({
            "engagement_code": "KTNN-MCP-04",
            "decision_number": "QĐ 891",
            "audited_entity": "Sở KH&ĐT",
            "audit_scope_year": 2025,
            "lead_auditor": "Trưởng đoàn",
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
        })
        handle_stateaudit_finding({
            "finding_code": "FIND-MCP-04",
            "engagement_code": "KTNN-MCP-04",
            "domain": "BUDGET_EXPENDITURE",
            "description": "Chi sai dự toán",
            "statutory_violation": "Luật NSNN",
        })
        handle_stateaudit_recommend({
            "recommendation_code": "REC-MCP-04",
            "finding_code": "FIND-MCP-04",
            "recommendation_type": "REIMBURSEMENT",
            "description": "Thu hồi ngân sách",
            "target_agency": "Sở KH&ĐT",
            "settlement_deadline": "2026-08-31",
            "amount_vnd": 1000000000,
        })
        res_str = handle_stateaudit_settle({
            "settlement_id": "SETTLE-MCP-01",
            "recommendation_code": "REC-MCP-04",
            "settlement_date": "2026-07-01",
            "treasury_voucher_number": "GNT-12345",
            "amount_settled_vnd": 1000000000,
        })
        res = json.loads(res_str)
        assert res["new_status"] == "FULLY_IMPLEMENTED"

    def test_mcp_standalone_conclude(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_stateaudit_conclude,
            handle_stateaudit_engagement,
        )

        handle_stateaudit_engagement({
            "engagement_code": "KTNN-MCP-05",
            "decision_number": "QĐ 892",
            "audited_entity": "UBND Tỉnh F",
            "audit_scope_year": 2025,
            "lead_auditor": "Trưởng đoàn",
            "start_date": "2026-01-01",
            "end_date": "2026-03-01",
        })
        res_str = handle_stateaudit_conclude({
            "engagement_code": "KTNN-MCP-05",
            "status": "PUBLISHED",
        })
        res = json.loads(res_str)
        assert res["status"] == "PUBLISHED"

    def test_mcp_standalone_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_stateaudit_list

        res_str = handle_stateaudit_list({"category": "all"})
        res = json.loads(res_str)
        assert "engagements" in res

    def test_mcp_standalone_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_stateaudit_status

        res_str = handle_stateaudit_status({})
        res = json.loads(res_str)
        assert "total_audit_engagements" in res

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_str = server._handle_stateaudit_engagement(
            engagement_code="KTNN-CORE-01",
            decision_number="QĐ 999",
            audited_entity="Ủy ban Quản lý vốn nhà nước tại doanh nghiệp",
            audit_scope_year=2025,
            lead_auditor="Trưởng đoàn Kiểm toán",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        res = json.loads(res_str)
        assert res["engagement_code"] == "KTNN-CORE-01"

        stat_str = server._handle_stateaudit_status()
        stat = json.loads(stat_str)
        assert stat["total_audit_engagements"] >= 1


class TestStateAuditEdgeCases:
    def test_all_recommendation_types(self, temp_db: str) -> None:
        from src.core.stateaudit_engine import VALID_RECOMMENDATION_TYPES

        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-EDGE-01",
            decision_number="QĐ 01",
            audited_entity="Đơn vị Test",
            entity_type="MINISTRY",
            audit_type="COMPLIANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Kiểm toán viên",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        engine.record_finding(
            finding_code="FIND-EDGE-01",
            engagement_code="KTNN-EDGE-01",
            domain="BUDGET_EXPENDITURE",
            description="Lỗi kiểm toán",
            statutory_violation="Luật",
        )
        for i, rtype in enumerate(VALID_RECOMMENDATION_TYPES):
            res = engine.issue_recommendation(
                recommendation_code=f"REC-EDGE-{i}",
                finding_code="FIND-EDGE-01",
                recommendation_type=rtype,
                description=f"Kiến nghị {rtype}",
                target_agency="Cơ quan A",
                settlement_deadline="2026-12-31",
                amount_vnd=1000000.0 if "REVENUE" in rtype or "EXPENDITURE" in rtype or "REIMBURSEMENT" in rtype else 0.0,
            )
            assert res["recommendation_type"] == rtype

    def test_criminal_referrals_and_disciplinary_actions(self, temp_db: str) -> None:
        engine = StateAuditEngine(db_path=temp_db)
        engine.register_engagement(
            engagement_code="KTNN-CRIM-01",
            decision_number="QĐ 777",
            audited_entity="Ban Quản lý Dự án B",
            entity_type="PROJECT_MANAGEMENT_UNIT",
            audit_type="COMPLIANCE_AUDIT",
            audit_scope_year=2025,
            lead_auditor="Trưởng đoàn Đặc nhiệm",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        engine.record_finding(
            finding_code="FIND-CRIM-01",
            engagement_code="KTNN-CRIM-01",
            domain="PROCUREMENT",
            description="Dấu hiệu thông thầu và đưa nhận hối lộ trong đấu thầu thiết bị y tế",
            statutory_violation="Điều 222 Bộ luật Hình sự 2015",
            severity="CRITICAL",
        )
        # Issue Criminal Referral
        engine.issue_recommendation(
            recommendation_code="REC-CRIM-01",
            finding_code="FIND-CRIM-01",
            recommendation_type="CRIMINAL_REFERRAL",
            description="Chuyển toàn bộ hồ sơ sang Cục Cảnh sát Điều tra tội phạm về tham nhũng, kinh tế, buôn lậu (C03)",
            target_agency="C03 Bộ Công an",
            settlement_deadline="2026-06-30",
            amount_vnd=0.0,
        )
        # Settle non-financial recommendation
        res = engine.record_settlement(
            settlement_id="SETTLE-CRIM-01",
            recommendation_code="REC-CRIM-01",
            settlement_date="2026-05-10",
            treasury_voucher_number="CV-999-C03",
            amount_settled_vnd=0.0,
            evidence_notes="Biên bản bàn giao hồ sơ vụ án sang CQĐT",
        )
        assert res["new_status"] == "FULLY_IMPLEMENTED"
