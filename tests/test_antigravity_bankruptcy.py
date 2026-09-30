"""
Comprehensive Unit & Integration Test Suite for Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite.
Statutory Framework:
- Luật Phá sản 2014 (Luật số 51/2014/QH13)
- Nghị định số 22/2015/NĐ-CP hướng dẫn Luật Phá sản về Quản tài viên
- Nghị quyết số 03/2016/NQ-HĐTP của Hội đồng Thẩm phán TANDTC
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.bankruptcy_engine import BankruptcyEngine
from src.cli.commands.bankruptcy_command import bankruptcy_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_bankruptcy.db")
    return BankruptcyEngine(db_path=db_file)


class TestBankruptcyEngine:
    def test_register_practitioner_valid(self, temp_engine):
        res = temp_engine.register_practitioner(
            full_name="Vũ Đức Trọng",
            cert_number="BTP-QTV-088/2021",
            org_name="Công ty Hợp danh Quản lý & Thanh lý Tài sản Mekong",
            profession="LUAT_SU",
            years_experience=9,
            is_practicing=True,
        )
        assert res["is_certified"] is True
        assert res["status"] == "CERTIFIED_PRACTICING"
        assert res["practitioner_id"].startswith("QTV-")
        assert len(res["violations"]) == 0

    def test_register_practitioner_invalid_cert(self, temp_engine):
        # Missing BTP accreditation
        res = temp_engine.register_practitioner(
            full_name="Nguyễn Văn A",
            cert_number="LOCAL-CERT-01",
            years_experience=8,
        )
        assert res["is_certified"] is False
        assert res["status"] == "QUALIFICATION_DEFICIENT"
        assert any("Bộ Tư pháp cấp" in v for v in res["violations"])

    def test_register_practitioner_insufficient_experience(self, temp_engine):
        # Less than 5 years experience under Art 12
        res = temp_engine.register_practitioner(
            full_name="Trần Thị B",
            cert_number="BTP-QTV-099/2024",
            years_experience=3,
        )
        assert res["is_certified"] is False
        assert res["status"] == "QUALIFICATION_DEFICIENT"
        assert any("tối thiểu 05 năm kinh nghiệm" in v for v in res["violations"])

    def test_register_practitioner_not_practicing(self, temp_engine):
        res = temp_engine.register_practitioner(
            full_name="Lê Quốc C",
            cert_number="BTP-QTV-012/2018",
            years_experience=7,
            is_practicing=False,
        )
        assert res["is_certified"] is False
        assert res["status"] == "QUALIFICATION_DEFICIENT"

    def test_file_bankruptcy_petition_valid(self, temp_engine):
        res = temp_engine.file_bankruptcy_petition(
            company_name="Công ty CP Xây dựng & Đầu tư Hạ tầng Mekong",
            tax_code="0312345678",
            petitioner_name="Ngân hàng TMCP Phát triển Công nghiệp",
            petitioner_role="UNSECURED_CREDITOR",
            overdue_days=105,  # >= 90 days
            overdue_debt_vnd=15000000000.0,
            court_name="Tòa án nhân dân Thành phố Hồ Chí Minh",
        )
        assert res["is_insolvent"] is True
        assert res["is_acceptable"] is True
        assert res["status"] == "PETITION_ACCEPTED_OPEN_HEARING"
        assert res["petition_id"].startswith("PET-")
        assert len(res["violations"]) == 0

    def test_file_bankruptcy_petition_insufficient_overdue_days(self, temp_engine):
        # Overdue < 90 days (under Art 4(1))
        res = temp_engine.file_bankruptcy_petition(
            company_name="Công ty TNHH Vận tải Sông Tiền",
            tax_code="0318765432",
            petitioner_name="Công ty Xăng dầu Mekong",
            petitioner_role="UNSECURED_CREDITOR",
            overdue_days=60,  # Below 90 days
            overdue_debt_vnd=3000000000.0,
        )
        assert res["is_insolvent"] is False
        assert res["is_acceptable"] is False
        assert res["status"] == "PETITION_REJECTED"
        assert any("03 tháng (90 ngày)" in v for v in res["violations"])

    def test_file_bankruptcy_petition_invalid_role(self, temp_engine):
        res = temp_engine.file_bankruptcy_petition(
            company_name="Công ty A",
            tax_code="0101010101",
            petitioner_name="Người dân qua đường",
            petitioner_role="STRANGER_PASSERBY",
            overdue_days=120,
            overdue_debt_vnd=1000000000.0,
        )
        assert res["is_acceptable"] is False
        assert res["status"] == "PETITION_REJECTED"
        assert any("Tư cách người nộp đơn không hợp lệ" in v for v in res["violations"])

    def test_file_bankruptcy_petition_missing_company(self, temp_engine):
        res = temp_engine.file_bankruptcy_petition(
            company_name="",
            tax_code="",
            petitioner_name="Chủ nợ B",
            overdue_days=120,
            overdue_debt_vnd=1000000000.0,
        )
        assert res["is_acceptable"] is False
        assert any("Thiếu tên doanh nghiệp hoặc mã số thuế" in v for v in res["violations"])

    def test_register_creditor_claim_valid_unsecured(self, temp_engine):
        res = temp_engine.register_creditor_claim(
            petition_id="PET-TEST01",
            creditor_name="Công ty Cung ứng Vật tư Mekong",
            id_or_tax_code="0319998888",
            claim_type="UNSECURED",
            claim_amount_vnd=2500000000.0,
            security_details="Hợp đồng mua bán nguyên vật liệu không có tài sản bảo đảm",
        )
        assert res["is_verified"] is True
        assert res["status"] == "CLAIM_VERIFIED_LISTED"
        assert res["claim_id"].startswith("CLM-")
        assert len(res["violations"]) == 0

    def test_register_creditor_claim_valid_secured(self, temp_engine):
        res = temp_engine.register_creditor_claim(
            petition_id="PET-TEST01",
            creditor_name="Ngân hàng Đầu tư Phát triển",
            id_or_tax_code="0100111222",
            claim_type="SECURED",
            claim_amount_vnd=10000000000.0,
            security_details="Thế chấp nhà xưởng số 12 đường KCN Tân Bình",
        )
        assert res["is_verified"] is True
        assert res["status"] == "CLAIM_VERIFIED_LISTED"
        assert res["claim_type"] == "SECURED"

    def test_register_creditor_claim_invalid_type(self, temp_engine):
        res = temp_engine.register_creditor_claim(
            petition_id="PET-TEST01",
            creditor_name="Chủ nợ X",
            id_or_tax_code="0109999999",
            claim_type="UNKNOWN_CLAIM_TYPE",
            claim_amount_vnd=500000000.0,
        )
        assert res["is_verified"] is False
        assert res["status"] == "CLAIM_DISPUTED_OR_INVALID"
        assert any("Loại yêu cầu đòi nợ không hợp lệ" in v for v in res["violations"])

    def test_register_creditor_claim_zero_amount(self, temp_engine):
        res = temp_engine.register_creditor_claim(
            petition_id="PET-TEST01",
            creditor_name="Chủ nợ Y",
            id_or_tax_code="0108888888",
            claim_type="UNSECURED",
            claim_amount_vnd=0.0,
        )
        assert res["is_verified"] is False
        assert any("phải lớn hơn 0 VND" in v for v in res["violations"])

    def test_conduct_creditors_meeting_valid(self, temp_engine):
        res = temp_engine.conduct_creditors_meeting(
            petition_id="PET-TEST01",
            attendees_unsecured_debt_vnd=14000000000.0,
            total_unsecured_debt_vnd=20000000000.0,  # 70% >= 51%
            resolution="RESTRUCTURING_PLAN",
            recovery_years=2.5,  # <= 3.0 years
        )
        assert res["is_quorum_reached"] is True
        assert res["is_valid"] is True
        assert res["attendance_ratio_pct"] == 70.0
        assert res["status"] == "MEETING_RESOLUTION_ADOPTED"
        assert res["meeting_id"].startswith("MTG-")

    def test_conduct_creditors_meeting_quorum_failed(self, temp_engine):
        # Attendance 40% < 51% under Art 79
        res = temp_engine.conduct_creditors_meeting(
            petition_id="PET-TEST01",
            attendees_unsecured_debt_vnd=8000000000.0,
            total_unsecured_debt_vnd=20000000000.0,  # 40% < 51%
            resolution="RESTRUCTURING_PLAN",
            recovery_years=2.0,
        )
        assert res["is_quorum_reached"] is False
        assert res["is_valid"] is False
        assert res["status"] == "MEETING_INVALID_OR_POSTPONED"
        assert any("tối thiểu 51%" in v for v in res["violations"])

    def test_conduct_creditors_meeting_excessive_recovery_years(self, temp_engine):
        # Recovery plan > 3.0 years under Art 89
        res = temp_engine.conduct_creditors_meeting(
            petition_id="PET-TEST01",
            attendees_unsecured_debt_vnd=16000000000.0,
            total_unsecured_debt_vnd=20000000000.0,  # 80%
            resolution="RESTRUCTURING_PLAN",
            recovery_years=4.5,  # > 3.0 years
        )
        assert res["is_quorum_reached"] is True
        assert res["is_valid"] is False
        assert res["status"] == "MEETING_INVALID_OR_POSTPONED"
        assert any("tối đa 03 năm theo Điều 89" in v for v in res["violations"])

    def test_conduct_creditors_meeting_declare_bankruptcy_resolution(self, temp_engine):
        res = temp_engine.conduct_creditors_meeting(
            petition_id="PET-TEST01",
            attendees_unsecured_debt_vnd=15000000000.0,
            total_unsecured_debt_vnd=20000000000.0,
            resolution="DECLARE_BANKRUPTCY",
            recovery_years=0.0,
        )
        assert res["is_valid"] is True
        assert res["status"] == "MEETING_RESOLUTION_ADOPTED"
        assert res["resolution"] == "DECLARE_BANKRUPTCY"

    def test_calculate_asset_distribution_full_solvency(self, temp_engine):
        # Proceeds exceed all debts -> residual goes to owners
        res = temp_engine.calculate_asset_distribution(
            petition_id="PET-TEST01",
            liquidation_proceeds_vnd=10000000000.0,
            bankruptcy_costs_vnd=500000000.0,
            worker_wages_and_insurance_vnd=1500000000.0,
            new_debts_vnd=500000000.0,
            tax_obligations_vnd=1000000000.0,
            unsecured_debts_claimed_vnd=4000000000.0,
        )
        assert res["status"] == "ASSET_DISTRIBUTION_COMPLETED"
        assert res["distribution_id"].startswith("DST-")
        assert res["bankruptcy_costs_paid_vnd"] == 500000000.0
        assert res["worker_wages_and_insurance_paid_vnd"] == 1500000000.0
        assert res["new_debts_paid_vnd"] == 500000000.0
        assert res["tax_obligations_paid_vnd"] == 1000000000.0
        assert res["unsecured_debts_paid_vnd"] == 4000000000.0
        assert res["unsecured_repayment_ratio_pct"] == 100.0
        assert res["residual_value_vnd"] == 2500000000.0  # 10B - (0.5+1.5+0.5+1.0+4.0) = 2.5B

    def test_calculate_asset_distribution_partial_unsecured(self, temp_engine):
        # Proceeds are exhausted while paying unsecured debts
        res = temp_engine.calculate_asset_distribution(
            petition_id="PET-TEST01",
            liquidation_proceeds_vnd=5000000000.0,
            bankruptcy_costs_vnd=500000000.0,        # 4.5B remaining
            worker_wages_and_insurance_vnd=1500000000.0,  # 3.0B remaining
            new_debts_vnd=500000000.0,               # 2.5B remaining
            tax_obligations_vnd=500000000.0,         # 2.0B remaining
            unsecured_debts_claimed_vnd=4000000000.0,# only 2.0B available -> 50%
        )
        assert res["bankruptcy_costs_paid_vnd"] == 500000000.0
        assert res["worker_wages_and_insurance_paid_vnd"] == 1500000000.0
        assert res["new_debts_paid_vnd"] == 500000000.0
        assert res["tax_obligations_paid_vnd"] == 500000000.0
        assert res["unsecured_debts_paid_vnd"] == 2000000000.0
        assert res["unsecured_repayment_ratio_pct"] == 50.0
        assert res["residual_value_vnd"] == 0.0

    def test_calculate_asset_distribution_exhausted_at_costs_or_wages(self, temp_engine):
        # Proceeds cannot even cover worker wages
        res = temp_engine.calculate_asset_distribution(
            petition_id="PET-TEST01",
            liquidation_proceeds_vnd=1000000000.0,
            bankruptcy_costs_vnd=400000000.0,        # 600M left
            worker_wages_and_insurance_vnd=1200000000.0,  # only 600M paid
            new_debts_vnd=300000000.0,
            tax_obligations_vnd=200000000.0,
            unsecured_debts_claimed_vnd=2000000000.0,
        )
        assert res["bankruptcy_costs_paid_vnd"] == 400000000.0
        assert res["worker_wages_and_insurance_paid_vnd"] == 600000000.0
        assert res["new_debts_paid_vnd"] == 0.0
        assert res["tax_obligations_paid_vnd"] == 0.0
        assert res["unsecured_debts_paid_vnd"] == 0.0
        assert res["unsecured_repayment_ratio_pct"] == 0.0
        assert res["residual_value_vnd"] == 0.0

    def test_list_bankruptcy_records_all_and_filtered(self, temp_engine):
        temp_engine.register_practitioner(full_name="Nguyễn Văn A")
        temp_engine.file_bankruptcy_petition(
            company_name="Công ty B",
            tax_code="01010101",
            petitioner_name="Chủ nợ C",
            overdue_days=95,
            overdue_debt_vnd=1000000.0,
        )
        all_records = temp_engine.list_bankruptcy_records(category="ALL")
        assert "insolvency_practitioners" in all_records
        assert "bankruptcy_petitions" in all_records
        assert len(all_records["insolvency_practitioners"]) >= 1
        assert len(all_records["bankruptcy_petitions"]) >= 1

        practitioners = temp_engine.list_bankruptcy_records(category="PRACTITIONERS")
        assert "insolvency_practitioners" in practitioners
        assert "bankruptcy_petitions" not in practitioners

    def test_get_bankruptcy_telemetry(self, temp_engine):
        temp_engine.register_practitioner(full_name="Đoàn Văn D")
        temp_engine.file_bankruptcy_petition(
            company_name="Công ty CP E",
            tax_code="03030303",
            petitioner_name="Ngân hàng F",
            overdue_days=100,
            overdue_debt_vnd=2000000000.0,
        )
        telemetry = temp_engine.get_bankruptcy_telemetry()
        assert telemetry["total_practitioners"] >= 1
        assert telemetry["total_petitions"] >= 1
        assert "compliance_framework" in telemetry
        assert "statutory_quorum_unsecured_debt_pct" in telemetry
        assert telemetry["statutory_quorum_unsecured_debt_pct"] == 51.0


class TestBankruptcyCli:
    def test_cli_practitioner(self):
        res = runner.invoke(bankruptcy_app, [
            "practitioner",
            "Đặng Minh Toàn",
            "--cert", "BTP-QTV-112/2020",
            "--org", "Hợp danh Quản tài viên Sài Gòn",
            "--profession", "LUAT_SU",
            "--years", "10",
        ])
        assert res.exit_code == 0
        assert "Hồ Sơ Quản Tài Viên" in res.stdout

    def test_cli_practitioner_json(self):
        res = runner.invoke(bankruptcy_app, [
            "practitioner",
            "Trần Thị Thảo",
            "--cert", "BTP-QTV-115/2021",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_certified"] is True
        assert data["practitioner_id"].startswith("QTV-")

    def test_cli_petition(self):
        res = runner.invoke(bankruptcy_app, [
            "petition",
            "Công ty CP Sản xuất Đồ gỗ Mekong",
            "0319876543",
            "Ngân hàng Phát triển Nông thôn",
            "--days", "110",
            "--debt", "5000000000",
        ])
        assert res.exit_code == 0
        assert "Thẩm Tra Đơn Yêu Cầu Mở Thủ Tục Phá Sản" in res.stdout

    def test_cli_petition_json(self):
        res = runner.invoke(bankruptcy_app, [
            "petition",
            "Công ty CP Thép Nam Bộ",
            "0315556666",
            "Công ty Quặng sắt Miền Đông",
            "--days", "100",
            "--debt", "3000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_insolvent"] is True
        assert data["status"] == "PETITION_ACCEPTED_OPEN_HEARING"

    def test_cli_claim(self):
        res = runner.invoke(bankruptcy_app, [
            "claim",
            "PET-TEST01",
            "Công ty CP Cung ứng Hóa chất",
            "0316789012",
            "--type", "UNSECURED",
            "--amount", "800000000",
        ])
        assert res.exit_code == 0
        assert "Hồ Sơ Yêu Cầu Đòi Nợ Của Chủ Nợ" in res.stdout

    def test_cli_claim_json(self):
        res = runner.invoke(bankruptcy_app, [
            "claim",
            "PET-TEST01",
            "Ngân hàng TMCP Quốc tế",
            "0109876543",
            "--type", "SECURED",
            "--amount", "12000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_verified"] is True
        assert data["claim_type"] == "SECURED"

    def test_cli_meeting(self):
        res = runner.invoke(bankruptcy_app, [
            "meeting",
            "PET-TEST01",
            "12000000000",
            "20000000000",
            "--resolution", "RESTRUCTURING_PLAN",
            "--years", "2.0",
        ])
        assert res.exit_code == 0
        assert "Nghị Quyết Hội Nghị Chủ Nợ" in res.stdout

    def test_cli_meeting_json(self):
        res = runner.invoke(bankruptcy_app, [
            "meeting",
            "PET-TEST01",
            "15000000000",
            "20000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_quorum_reached"] is True
        assert data["attendance_ratio_pct"] == 75.0

    def test_cli_distribute(self):
        res = runner.invoke(bankruptcy_app, [
            "distribute",
            "PET-TEST01",
            "10000000000",
            "500000000",
            "1500000000",
            "--unsecured", "5000000000",
        ])
        assert res.exit_code == 0
        assert "Bảng Phân Chia Tài Sản Thanh Lý Phá Sản" in res.stdout

    def test_cli_distribute_json(self):
        res = runner.invoke(bankruptcy_app, [
            "distribute",
            "PET-TEST01",
            "8000000000",
            "400000000",
            "1600000000",
            "--unsecured", "4000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "ASSET_DISTRIBUTION_COMPLETED"
        assert data["unsecured_repayment_ratio_pct"] == 100.0

    def test_cli_list(self):
        res = runner.invoke(bankruptcy_app, ["list", "--category", "ALL", "--limit", "10"])
        assert res.exit_code == 0
        assert "Danh mục" in res.stdout

    def test_cli_list_json(self):
        res = runner.invoke(bankruptcy_app, ["list", "--category", "PETITIONS", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "bankruptcy_petitions" in data

    def test_cli_status(self):
        res = runner.invoke(bankruptcy_app, ["status"])
        assert res.exit_code == 0
        assert "Chỉ Số Telemetry Phá Sản Doanh Nghiệp Quốc Gia" in res.stdout

    def test_cli_status_json(self):
        res = runner.invoke(bankruptcy_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "total_petitions" in data
        assert data["statutory_quorum_unsecured_debt_pct"] == 51.0


class TestBankruptcyMcp:
    def test_scripts_mcp_practitioner(self):
        raw = mcp_script.handle_bankruptcy_practitioner({
            "full_name": "Phạm Quốc Huy",
            "cert_number": "BTP-QTV-077/2020",
            "profession": "LUAT_SU",
            "years_experience": 8,
        })
        res = json.loads(raw)
        assert res["is_certified"] is True
        assert res["practitioner_id"].startswith("QTV-")

    def test_scripts_mcp_petition(self):
        raw = mcp_script.handle_bankruptcy_petition({
            "company_name": "Công ty TNHH Vận tải Biển Nam Định",
            "tax_code": "0601234567",
            "petitioner_name": "Ngân hàng Thương mại Ngoại thương",
            "overdue_days": 100,
            "overdue_debt_vnd": 8000000000.0,
        })
        res = json.loads(raw)
        assert res["is_insolvent"] is True

    def test_scripts_mcp_claim(self):
        raw = mcp_script.handle_bankruptcy_claim({
            "petition_id": "PET-TEST02",
            "creditor_name": "Công ty Nhiên liệu Hàng hải",
            "id_or_tax_code": "0311223344",
            "claim_type": "UNSECURED",
            "claim_amount_vnd": 1200000000.0,
        })
        res = json.loads(raw)
        assert res["is_verified"] is True

    def test_scripts_mcp_meeting(self):
        raw = mcp_script.handle_bankruptcy_meeting({
            "petition_id": "PET-TEST02",
            "attendees_unsecured_debt_vnd": 12000000000.0,
            "total_unsecured_debt_vnd": 20000000000.0,
            "resolution": "RESTRUCTURING_PLAN",
            "recovery_years": 2.0,
        })
        res = json.loads(raw)
        assert res["is_quorum_reached"] is True

    def test_scripts_mcp_distribute(self):
        raw = mcp_script.handle_bankruptcy_distribute({
            "petition_id": "PET-TEST02",
            "liquidation_proceeds_vnd": 5000000000.0,
            "bankruptcy_costs_vnd": 500000000.0,
            "worker_wages_and_insurance_vnd": 1500000000.0,
        })
        res = json.loads(raw)
        assert res["status"] == "ASSET_DISTRIBUTION_COMPLETED"

    def test_scripts_mcp_list(self):
        raw = mcp_script.handle_bankruptcy_list({"category": "ALL", "limit": 10})
        res = json.loads(raw)
        assert "insolvency_practitioners" in res

    def test_scripts_mcp_status(self):
        raw = mcp_script.handle_bankruptcy_status({})
        res = json.loads(raw)
        assert "total_petitions" in res

    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer()
        p_raw = server._handle_bankruptcy_practitioner(
            full_name="Đỗ Hoàng Nam",
            cert_number="BTP-QTV-022/2019",
            years_experience=9,
        )
        p_res = json.loads(p_raw)
        assert p_res["is_certified"] is True

        pet_raw = server._handle_bankruptcy_petition(
            company_name="Công ty Địa ốc Viễn Đông",
            tax_code="0309998888",
            petitioner_name="Ngân hàng Xây dựng",
            overdue_days=95,
            overdue_debt_vnd=10000000000.0,
        )
        pet_res = json.loads(pet_raw)
        assert pet_res["is_insolvent"] is True

        clm_raw = server._handle_bankruptcy_claim(
            petition_id="PET-TEST03",
            creditor_name="Tập đoàn Đầu tư Phương Nam",
            id_or_tax_code="0301112233",
            claim_type="UNSECURED",
            claim_amount_vnd=2000000000.0,
        )
        clm_res = json.loads(clm_raw)
        assert clm_res["is_verified"] is True

        mtg_raw = server._handle_bankruptcy_meeting(
            petition_id="PET-TEST03",
            attendees_unsecured_debt_vnd=18000000000.0,
            total_unsecured_debt_vnd=20000000000.0,
            resolution="RESTRUCTURING_PLAN",
            recovery_years=1.5,
        )
        mtg_res = json.loads(mtg_raw)
        assert mtg_res["is_quorum_reached"] is True

        dst_raw = server._handle_bankruptcy_distribute(
            petition_id="PET-TEST03",
            liquidation_proceeds_vnd=12000000000.0,
            bankruptcy_costs_vnd=600000000.0,
            worker_wages_and_insurance_vnd=2000000000.0,
            unsecured_debts_claimed_vnd=5000000000.0,
        )
        dst_res = json.loads(dst_raw)
        assert dst_res["status"] == "ASSET_DISTRIBUTION_COMPLETED"

        lst_raw = server._handle_bankruptcy_list(category="ALL", limit=5)
        lst_res = json.loads(lst_raw)
        assert "insolvency_practitioners" in lst_res

        stat_raw = server._handle_bankruptcy_status()
        stat_res = json.loads(stat_raw)
        assert "total_petitions" in stat_res
