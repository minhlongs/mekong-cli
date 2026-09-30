"""
Comprehensive Unit & Integration Test Suite for Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite.
Statutory Framework:
- Luật Giám định tư pháp 2012 (sửa đổi, bổ sung 2020, Luật số 56/2020/QH14)
- Nghị định số 157/2020/NĐ-CP & Nghị định số 85/2013/NĐ-CP
- Bộ luật Tố tụng hình sự 2015 (Điều 99, 107; Điều 205-214)
- Bộ luật Tố tụng dân sự 2015 (Điều 102)
- Bộ luật Hình sự 2015 (Điều 382)
- Pháp lệnh số 02/2012/UBTVQH13 về chi phí giám định, định giá
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.forensic_engine import ForensicEngine
from src.cli.commands.forensic_command import forensic_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_forensic.db")
    return ForensicEngine(db_path=db_file)


class TestForensicEngine:
    def test_register_expert_valid(self, temp_engine):
        res = temp_engine.register_judicial_expert(
            full_name="Nguyễn Văn An",
            domain="DIGITAL_EVIDENCE",
            degree="Kỹ sư An toàn Thông tin / Thạc sĩ KHMT",
            years_experience=7,
            card_number="GĐTP-08/2023/BTP",
            issuing_authority="Bộ Tư pháp",
        )
        assert res["is_certified"] is True
        assert res["status"] == "CERTIFIED_EXPERT"
        assert res["expert_id"].startswith("JEX-")
        assert res["years_experience"] == 7
        assert len(res["violations"]) == 0

    def test_register_expert_underqualified(self, temp_engine):
        # Under 5 years experience required by Law on Judicial Expertise Art 7(1)(b)
        res = temp_engine.register_judicial_expert(
            full_name="Trần Văn Bình",
            domain="DIGITAL_EVIDENCE",
            years_experience=3,
        )
        assert res["is_certified"] is False
        assert res["status"] == "QUALIFICATION_DEFICIENT"
        assert any("05 năm theo Điều 7" in v for v in res["violations"])

    def test_register_expert_invalid_domain(self, temp_engine):
        res = temp_engine.register_judicial_expert(
            full_name="Lê Minh",
            domain="UNKNOWN_DOMAIN_123",
            years_experience=10,
        )
        assert res["is_certified"] is False
        assert any("Lĩnh vực giám định không hợp lệ" in v for v in res["violations"])

    def test_solicit_assessment_valid(self, temp_engine):
        res = temp_engine.solicit_assessment(
            requesting_agency="Cơ quan Cảnh sát Điều tra - Công an TP. Hà Nội",
            case_code="AN-2026/09/ĐTTH",
            assessment_target="Hệ thống cơ sở dữ liệu giao dịch tài chính nội bộ",
            domain="DIGITAL_EVIDENCE",
            dispute_value_vnd=2_000_000_000.0,
            deadline_days=30,
        )
        assert res["status"] == "REQUISITION_ACCEPTED"
        assert res["requisition_id"].startswith("REQ-")
        assert res["estimated_fee_vnd"] > 0
        assert "BLTTHS/BLTTDS" in res["statutory_notes"]

    def test_solicit_assessment_fee_brackets(self, temp_engine):
        # Small bracket <= 500M
        res_small = temp_engine.solicit_assessment(
            requesting_agency="TAND Quận 1",
            case_code="DS-01",
            assessment_target="Hợp đồng điện tử",
            dispute_value_vnd=200_000_000.0,
        )
        assert res_small["estimated_fee_vnd"] == 10_000_000.0  # max(10M, 200M * 0.04 = 8M)

        # Large bracket > 5B
        res_large = temp_engine.solicit_assessment(
            requesting_agency="Viện Kiểm sát Nhân dân Tối cao",
            case_code="HS-09",
            assessment_target="Toàn bộ hệ thống máy chủ ngân hàng",
            dispute_value_vnd=10_000_000_000.0,
        )
        # 110M + (10B - 5B) * 0.01 = 110M + 50M = 160M
        assert res_large["estimated_fee_vnd"] == 160_000_000.0

    def test_solicit_assessment_missing_info(self, temp_engine):
        res = temp_engine.solicit_assessment(
            requesting_agency="",
            case_code="",
            assessment_target="Dữ liệu mạng",
        )
        assert res["status"] == "REQUISITION_INVALID"
        assert "Thiếu thông tin cơ quan tiến hành tố tụng" in res["statutory_notes"]

    def test_issue_conclusion_valid(self, temp_engine):
        res = temp_engine.issue_expert_conclusion(
            requisition_id="REQ-TEST1234",
            lead_expert_id="JEX-EXPERT01",
            methodology="Phân tích pháp chứng bộ nhớ RAM và nhật ký sự kiện Event Log sử dụng EnCase / Volatility",
            conclusion_verdict="Xác định có hành vi can thiệp trái phép làm sai lệch số dư lúc 02:14 AM",
            has_sworn_statement=True,
            has_conflict_of_interest=False,
        )
        assert res["is_valid"] is True
        assert res["status"] == "CONCLUSION_LEGALLY_EFFECTIVE"
        assert res["conclusion_id"].startswith("CON-")
        assert "Điều 87 Bộ luật Tố tụng hình sự" in res["statutory_notes"]

    def test_issue_conclusion_missing_sworn_statement(self, temp_engine):
        res = temp_engine.issue_expert_conclusion(
            requisition_id="REQ-TEST1234",
            lead_expert_id="JEX-EXPERT01",
            methodology="Phương pháp phân tích pháp chứng số",
            conclusion_verdict="Phát hiện dấu hiệu truy cập trái phép",
            has_sworn_statement=False,  # Violates Art 382 Criminal Code
            has_conflict_of_interest=False,
        )
        assert res["is_valid"] is False
        assert res["status"] == "CONCLUSION_INVALID"
        assert any("Điều 382 Bộ luật Hình sự" in v for v in res["violations"])

    def test_issue_conclusion_conflict_of_interest(self, temp_engine):
        res = temp_engine.issue_expert_conclusion(
            requisition_id="REQ-TEST1234",
            lead_expert_id="JEX-EXPERT01",
            methodology="Phương pháp phân tích chứng cứ",
            conclusion_verdict="Kết luận xác định",
            has_sworn_statement=True,
            has_conflict_of_interest=True,  # Violates Art 34 Judicial Expertise Law
        )
        assert res["is_valid"] is False
        assert res["status"] == "CONCLUSION_INVALID"
        assert any("Điều 34 Luật Giám định tư pháp" in v for v in res["violations"])

    def test_audit_chain_of_custody_valid(self, temp_engine):
        sample_payload = "EVIDENCE_DUMP_HEX_ABCDEF1234567890_FORENSIC_RAW_PAYLOAD"
        res = temp_engine.audit_digital_chain_of_custody(
            evidence_name="Ổ cứng SSD Samsung 980 Pro 2TB (Serial: S6B0NX0R123456)",
            source_device="Máy trạm Workstation Giám đốc Tài chính",
            raw_evidence_data=sample_payload,
            write_blocker_used=True,
            seizure_witnesses_count=2,
        )
        assert res["is_admissible"] is True
        assert res["status"] == "CHAIN_OF_CUSTODY_INTACT"
        assert res["custody_id"].startswith("COC-")
        assert len(res["sha256_hash"]) == 64
        assert "Điều 99, 107 BLTTHS 2015" in res["statutory_notes"]

    def test_audit_chain_of_custody_no_write_blocker(self, temp_engine):
        res = temp_engine.audit_digital_chain_of_custody(
            evidence_name="USB Flash Drive 64GB",
            source_device="Cổng USB mặt trước",
            raw_evidence_data="RAW_DATA",
            write_blocker_used=False,
            seizure_witnesses_count=2,
        )
        assert res["is_admissible"] is False
        assert res["status"] == "CHAIN_COMPROMISED"
        assert any("Write-Blocker" in v for v in res["violations"])

    def test_audit_chain_of_custody_insufficient_witnesses(self, temp_engine):
        res = temp_engine.audit_digital_chain_of_custody(
            evidence_name="Server NAS Synology",
            source_device="Tủ rack phòng máy chủ",
            raw_evidence_data="RAW_DATA",
            write_blocker_used=True,
            seizure_witnesses_count=1,  # Required >= 2 witnesses under CPC Art 107
        )
        assert res["is_admissible"] is False
        assert res["status"] == "CHAIN_COMPROMISED"
        assert any("Điều 107 BLTTHS 2015" in v for v in res["violations"])

    def test_list_and_telemetry(self, temp_engine):
        # Register an expert
        temp_engine.register_judicial_expert(
            full_name="Võ Tấn Phát",
            domain="FINANCIAL_ACCOUNTING",
            years_experience=8,
        )
        # Solicit an assessment
        temp_engine.solicit_assessment(
            requesting_agency="Cơ quan An ninh Điều tra",
            case_code="AN-44/2026",
            assessment_target="Báo cáo tài chính năm 2025",
            domain="FINANCIAL_ACCOUNTING",
        )
        # Issue conclusion
        temp_engine.issue_expert_conclusion(
            requisition_id="REQ-44",
            lead_expert_id="JEX-01",
            methodology="Đối chiếu chứng từ ngân hàng",
            conclusion_verdict="Xác định thất thoát 1.2 tỷ VND",
            has_sworn_statement=True,
            has_conflict_of_interest=False,
        )
        # Custody
        temp_engine.audit_digital_chain_of_custody(
            evidence_name="Sao kê ngân hàng điện tử",
            source_device="Cổng Internet Banking",
            raw_evidence_data="BANK_STATEMENT_SHA256_DATA",
        )

        all_records = temp_engine.list_forensic_records(category="ALL")
        assert len(all_records["judicial_experts"]) == 1
        assert len(all_records["forensic_requisitions"]) == 1
        assert len(all_records["expert_conclusions"]) == 1
        assert len(all_records["chain_of_custody"]) == 1

        telemetry = temp_engine.get_forensic_telemetry()
        assert telemetry["total_experts"] == 1
        assert telemetry["certified_experts"] == 1
        assert telemetry["total_requisitions"] == 1
        assert telemetry["total_conclusions"] == 1
        assert telemetry["valid_conclusions"] == 1
        assert telemetry["validity_rate_pct"] == 100.0
        assert telemetry["total_custody_records"] == 1
        assert telemetry["admissible_evidence_records"] == 1


class TestForensicCli:
    def test_cli_expert_json(self):
        result = runner.invoke(forensic_app, [
            "expert",
            "Hoàng Kim Long",
            "--domain", "DIGITAL_EVIDENCE",
            "--exp", "9",
            "--card", "GĐTP-09/2022/BTP",
            "--authority", "Bộ Tư pháp",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["is_certified"] is True
        assert data["expert_id"].startswith("JEX-")

    def test_cli_expert_console(self):
        result = runner.invoke(forensic_app, [
            "expert",
            "Đỗ Văn Sơn",
            "--domain", "FINANCIAL_ACCOUNTING",
            "--exp", "6",
        ])
        assert result.exit_code == 0
        assert "Hồ Sơ Giám Định Viên Tư Pháp" in result.stdout

    def test_cli_solicit_json(self):
        result = runner.invoke(forensic_app, [
            "solicit",
            "TAND Tối cao",
            "VỤ ÁN HÌNH SỰ SỐ 12/2026",
            "--target", "Máy chủ lưu trữ dữ liệu thuế",
            "--domain", "DIGITAL_EVIDENCE",
            "--value", "3500000000",
            "--deadline", "25",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["requisition_id"].startswith("REQ-")
        assert data["status"] == "REQUISITION_ACCEPTED"

    def test_cli_solicit_console(self):
        result = runner.invoke(forensic_app, [
            "solicit",
            "Công an Tỉnh Đồng Nai",
            "HS-88/2026",
            "--target", "Dữ liệu kế toán công ty X",
        ])
        assert result.exit_code == 0
        assert "Quyết Định Trưng Cầu Giám Định Tư Pháp" in result.stdout

    def test_cli_conclude_json(self):
        result = runner.invoke(forensic_app, [
            "conclude",
            "REQ-TEST-CLI",
            "JEX-CLI-01",
            "--method", "Giám định chữ ký số và thời gian đóng dấu thời gian (Timestamp)",
            "--verdict", "Chữ ký số hợp lệ và được ký đúng thời điểm trước khi xảy ra sự cố",
            "--sworn",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["conclusion_id"].startswith("CON-")
        assert data["is_valid"] is True

    def test_cli_conclude_console(self):
        result = runner.invoke(forensic_app, [
            "conclude",
            "REQ-TEST-CONSOLE",
            "JEX-CLI-02",
            "--method", "Phân tích mã độc Trojan",
            "--verdict", "Phát hiện mã độc khai thác lỗ hổng zero-day",
            "--sworn",
        ])
        assert result.exit_code == 0
        assert "Kết Luận Giám Định Tư Pháp" in result.stdout

    def test_cli_custody_json(self):
        result = runner.invoke(forensic_app, [
            "custody",
            "Ổ cứng cơ Seagate IronWolf 8TB",
            "--device", "Server Dell PowerEdge R740",
            "--data", "BINARY_SECTOR_IMAGE_VERIFICATION_HASH_TEST",
            "--write-blocker",
            "--witnesses", "3",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["custody_id"].startswith("COC-")
        assert data["is_admissible"] is True

    def test_cli_custody_console(self):
        result = runner.invoke(forensic_app, [
            "custody",
            "Điện thoại iPhone 15 Pro",
            "--device", "Phòng làm việc Giám đốc",
            "--data", "IPHONE_EXTRACTION_DATA",
            "--write-blocker",
            "--witnesses", "2",
        ])
        assert result.exit_code == 0
        assert "Chuỗi Bảo Quản Chứng Cứ Điện Tử" in result.stdout

    def test_cli_list_json(self):
        result = runner.invoke(forensic_app, ["list", "--category", "ALL", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "judicial_experts" in data
        assert "forensic_requisitions" in data

    def test_cli_status_json(self):
        result = runner.invoke(forensic_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_experts" in data
        assert "validity_rate_pct" in data

    def test_cli_status_console(self):
        result = runner.invoke(forensic_app, ["status"])
        assert result.exit_code == 0
        assert "Chỉ Số Telemetry Giám Định Tư Pháp Quốc Gia" in result.stdout

    def test_cli_main_callback(self):
        result = runner.invoke(forensic_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG GIÁM ĐỊNH TƯ PHÁP, CHỨNG CỨ ĐIỆN TỬ & KỸ THUẬT HÌNH SỰ" in result.stdout


class TestForensicMcp:
    def test_core_mcp_server_handlers(self):
        srv = MekongMcpServer()
        # expert
        res_exp = json.loads(srv._handle_forensic_expert(
            full_name="Giám định viên Mai Lan Hương",
            domain="CONSTRUCTION_QUALITY",
            degree="Kỹ sư Xây dựng Cầu đường",
            years_experience=10,
        ))
        assert res_exp["is_certified"] is True

        # solicit
        res_sol = json.loads(srv._handle_forensic_solicit(
            requesting_agency="TAND Tỉnh Bình Dương",
            case_code="DS-55/2026",
            assessment_target="Công trình cầu cạn Km 18+200",
            domain="CONSTRUCTION_QUALITY",
            dispute_value_vnd=15000000000.0,
            deadline_days=45,
        ))
        assert res_sol["requisition_id"].startswith("REQ-")

        # conclude
        res_con = json.loads(srv._handle_forensic_conclude(
            requisition_id="REQ-TEST",
            lead_expert_id="JEX-01",
            methodology="Kiểm định siêu âm bê tông cốt thép",
            conclusion_verdict="Độ nén bê tông đạt mác thiết kế",
            has_sworn_statement=True,
            has_conflict_of_interest=False,
        ))
        assert res_con["is_valid"] is True

        # custody
        res_cus = json.loads(srv._handle_forensic_custody(
            evidence_name="File ảnh chụp hiện trường số",
            source_device="Máy ảnh kỹ thuật số Canon EOS",
            raw_evidence_data="RAW_IMAGE_PIXELS_DATA",
            write_blocker_used=True,
            seizure_witnesses_count=2,
        ))
        assert res_cus["is_admissible"] is True

        # list
        res_list = json.loads(srv._handle_forensic_list(category="ALL"))
        assert "judicial_experts" in res_list

        # status
        res_stat = json.loads(srv._handle_forensic_status())
        assert res_stat["total_experts"] >= 1

    def test_scripts_mcp_server_handlers(self):
        # expert
        res_exp = json.loads(mcp_script.handle_forensic_expert({
            "full_name": "Phan Hữu Dũng",
            "domain": "INTELLECTUAL_PROPERTY",
            "degree": "Thạc sĩ Luật Sở hữu Trí tuệ",
            "years_experience=6": 6,
            "years_experience": 6,
        }))
        assert res_exp["is_certified"] is True

        # solicit
        res_sol = json.loads(mcp_script.handle_forensic_solicit({
            "requesting_agency": "Cục Sở hữu Trí tuệ",
            "case_code": "SHTT-09/2026",
            "assessment_target": "Mã nguồn phần mềm Mekong CLI",
            "domain": "INTELLECTUAL_PROPERTY",
            "dispute_value_vnd": 800000000.0,
        }))
        assert res_sol["requisition_id"].startswith("REQ-")

        # conclude
        res_con = json.loads(mcp_script.handle_forensic_conclude({
            "requisition_id": "REQ-SHTT-09",
            "lead_expert_id": "JEX-IP-01",
            "methodology": "So sánh mã nguồn AST và bảng băm tương đồng",
            "conclusion_verdict": "Không có hành vi sao chép trái phép mã nguồn",
            "has_sworn_statement": True,
            "has_conflict_of_interest": False,
        }))
        assert res_con["is_valid"] is True

        # custody
        res_cus = json.loads(mcp_script.handle_forensic_custody({
            "evidence_name": "Kho lưu trữ Git Repository",
            "source_device": "Máy chủ GitLab nội bộ",
            "raw_evidence_data": "GIT_BUNDLE_DATA",
            "write_blocker_used": True,
            "seizure_witnesses_count": 2,
        }))
        assert res_cus["is_admissible"] is True

        # list
        res_list = json.loads(mcp_script.handle_forensic_list({"category": "ALL"}))
        assert "judicial_experts" in res_list

        # status
        res_stat = json.loads(mcp_script.handle_forensic_status({}))
        assert res_stat["total_experts"] >= 1

    def test_scripts_mcp_registration_and_spec_parity(self):
        assert "mekong_forensic_expert" in mcp_script.CORE_HANDLERS
        assert "mekong_forensic_solicit" in mcp_script.CORE_HANDLERS
        assert "mekong_forensic_conclude" in mcp_script.CORE_HANDLERS
        assert "mekong_forensic_custody" in mcp_script.CORE_HANDLERS
        assert "mekong_forensic_list" in mcp_script.CORE_HANDLERS
        assert "mekong_forensic_status" in mcp_script.CORE_HANDLERS

        assert "forensic_expert" in mcp_script.CORE_HANDLERS
        assert "forensic_solicit" in mcp_script.CORE_HANDLERS
        assert "forensic_conclude" in mcp_script.CORE_HANDLERS
        assert "forensic_custody" in mcp_script.CORE_HANDLERS
        assert "forensic_list" in mcp_script.CORE_HANDLERS
        assert "forensic_status" in mcp_script.CORE_HANDLERS

        spec_names = {t["name"] for t in mcp_script.CORE_TOOLS_SPEC}
        assert "mekong_forensic_expert" in spec_names
        assert "mekong_forensic_solicit" in spec_names
        assert "mekong_forensic_conclude" in spec_names
        assert "mekong_forensic_custody" in spec_names
        assert "mekong_forensic_list" in spec_names
        assert "mekong_forensic_status" in spec_names
