"""
Comprehensive Unit & Integration Test Suite for Vietnamese Commercial Mediation & ADR Suite.
Statutory Framework:
- Nghị định số 22/2017/NĐ-CP ngày 24/02/2017 của Chính phủ về hòa giải thương mại
- Bộ luật Tố tụng dân sự 2015 — Chương XXXIII (Điều 416-419)
- Công ước Singapore về Hòa giải 2018 (Singapore Convention on Mediation)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.mediation_engine import MediationEngine
from src.cli.commands.mediation_command import mediation_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_mediation.db")
    return MediationEngine(db_path=db_file)


class TestMediationEngine:
    def test_draft_valid_agreement(self, temp_engine):
        res = temp_engine.draft_mediation_agreement(
            party_a="Công ty Cổ phần Công nghệ Mekong",
            party_b="Tập đoàn Bán lẻ Á Châu",
            dispute_scope="Tranh chấp hợp đồng triển khai giải pháp ERP",
            mediation_center="VICMC",
            language="VIETNAMESE",
        )
        assert res["is_valid"] is True
        assert res["status"] == "AGREEMENT_VALID"
        assert res["agreement_id"].startswith("MED-AGR-")
        assert "VICMC" in res["model_clause"]
        assert "Điều 11" in res["statutory_notes"]

    def test_draft_agreement_missing_party(self, temp_engine):
        res = temp_engine.draft_mediation_agreement(
            party_a="",
            party_b="Tập đoàn Bán lẻ Á Châu",
        )
        assert res["is_valid"] is False
        assert res["status"] == "INVALID_CLAUSE"

    def test_draft_agreement_invalid_center(self, temp_engine):
        res = temp_engine.draft_mediation_agreement(
            party_a="Công ty A",
            party_b="Công ty B",
            mediation_center="UNKNOWN_CENTER",
        )
        assert res["is_valid"] is False

    def test_initiate_case_accepted(self, temp_engine):
        res = temp_engine.initiate_mediation_case(
            party_a="Công ty TNHH Phần mềm Sài Gòn",
            party_b="Ngân hàng TMCP Việt Nam",
            claim_amount_vnd=1500000000.0,
            dispute_category="TECH_SERVICES",
            mediator_name="Hòa giải viên Luật sư Lê Hoàng Long",
            mediator_experience_years=6,
            mediation_center="VICMC",
        )
        assert res["is_valid"] is True
        assert res["status"] == "CASE_ACCEPTED"
        assert res["case_id"].startswith("MED-CAS-")
        assert res["mediation_fee_vnd"] > 0

    def test_initiate_case_underqualified_mediator(self, temp_engine):
        res = temp_engine.initiate_mediation_case(
            party_a="Công ty A",
            party_b="Công ty B",
            claim_amount_vnd=500000000.0,
            dispute_category="SALE_OF_GOODS",
            mediator_experience_years=1,  # Under statutory 2 years (Art 7)
        )
        assert res["is_valid"] is False
        assert res["status"] == "CASE_REJECTED"
        assert any("chưa đủ tiêu chuẩn hành nghề" in v for v in res["violations"])

    def test_initiate_case_invalid_category(self, temp_engine):
        res = temp_engine.initiate_mediation_case(
            party_a="Công ty A",
            party_b="Công ty B",
            claim_amount_vnd=500000000.0,
            dispute_category="FAMILY_DIVORCE",
        )
        assert res["is_valid"] is False

    def test_create_settlement_record_valid(self, temp_engine):
        res = temp_engine.create_settlement_record(
            case_id="MED-CAS-12345678",
            settlement_amount_vnd=400000000.0,
            settlement_summary="Bên B thanh toán đủ số tiền trong vòng 20 ngày và Bên A hoàn tất nghiệm thu hệ thống",
            mediator_signature=True,
            parties_signature=True,
        )
        assert res["is_valid"] is True
        assert res["status"] == "SETTLEMENT_SUCCESSFUL"
        assert res["settlement_id"].startswith("MED-SET-")
        assert "hiệu lực ràng buộc" in res["statutory_notes"]

    def test_create_settlement_record_prohibited_evasion(self, temp_engine):
        res = temp_engine.create_settlement_record(
            case_id="MED-CAS-12345678",
            settlement_amount_vnd=400000000.0,
            settlement_summary="Thỏa thuận chia nhỏ hóa đơn để trốn thuế và gian lận thuế đối với nhà nước",
            mediator_signature=True,
            parties_signature=True,
        )
        assert res["is_valid"] is False
        assert res["status"] == "INVALID_SETTLEMENT"
        assert any("trốn thuế" in v for v in res["violations"])

    def test_create_settlement_record_missing_mediator_signature(self, temp_engine):
        res = temp_engine.create_settlement_record(
            case_id="MED-CAS-12345678",
            settlement_amount_vnd=400000000.0,
            settlement_summary="Thỏa thuận hợp pháp nhưng hòa giải viên chưa ký xác nhận",
            mediator_signature=False,
            parties_signature=True,
        )
        assert res["is_valid"] is False
        assert any("chữ ký của Hòa giải viên" in v for v in res["violations"])

    def test_create_settlement_record_missing_parties_signature(self, temp_engine):
        res = temp_engine.create_settlement_record(
            case_id="MED-CAS-12345678",
            settlement_amount_vnd=400000000.0,
            settlement_summary="Thỏa thuận hợp pháp nhưng các bên chưa ký",
            mediator_signature=True,
            parties_signature=False,
        )
        assert res["is_valid"] is False
        assert any("chữ ký hoặc xác nhận của các bên" in v for v in res["violations"])

    def test_court_recognition_granted_within_time(self, temp_engine):
        res = temp_engine.audit_court_recognition(
            settlement_id="MED-SET-12345678",
            court_name="TAND Thành phố Hà Nội",
            filing_months_elapsed=2.5,
            has_capacity=True,
            is_voluntary=True,
        )
        assert res["is_recognized"] is True
        assert res["within_statute_limit"] is True
        assert res["status"] == "COURT_RECOGNITION_GRANTED"
        assert res["enforceability_order"] == "ENFORCEABLE_AS_COURT_JUDGMENT"
        assert res["recognition_id"].startswith("MED-REC-")

    def test_court_recognition_expired_statute(self, temp_engine):
        res = temp_engine.audit_court_recognition(
            settlement_id="MED-SET-12345678",
            court_name="TAND Thành phố Hà Nội",
            filing_months_elapsed=7.5,  # Exceeded 6 months (Art 416 CPC)
            has_capacity=True,
            is_voluntary=True,
        )
        assert res["is_recognized"] is False
        assert res["within_statute_limit"] is False
        assert res["status"] == "RECOGNITION_REJECTED"
        assert any("Quá thời hiệu nộp đơn" in v for v in res["violations"])

    def test_court_recognition_lacking_capacity_or_consent(self, temp_engine):
        res = temp_engine.audit_court_recognition(
            settlement_id="MED-SET-12345678",
            filing_months_elapsed=1.0,
            has_capacity=False,
            is_voluntary=False,
        )
        assert res["is_recognized"] is False
        assert len(res["violations"]) >= 2

    def test_singapore_convention_eligible(self, temp_engine):
        res = temp_engine.audit_singapore_convention(
            settlement_id="MED-SET-12345678",
            is_cross_border=True,
            is_commercial=True,
            mediator_attestation=True,
            has_consumer_or_family=False,
        )
        assert res["is_eligible"] is True
        assert res["status"] == "CONVENTION_ELIGIBLE"

    def test_singapore_convention_ineligible_consumer(self, temp_engine):
        res = temp_engine.audit_singapore_convention(
            settlement_id="MED-SET-12345678",
            is_cross_border=True,
            is_commercial=True,
            has_consumer_or_family=True,
        )
        assert res["is_eligible"] is False
        assert res["status"] == "INELIGIBLE"
        assert any("loại trừ tranh chấp tiêu dùng" in v for v in res["violations"])

    def test_list_and_telemetry(self, temp_engine):
        temp_engine.draft_mediation_agreement("Bên A", "Bên B")
        temp_engine.initiate_mediation_case("Bên A", "Bên B", 200000000.0)
        temp_engine.create_settlement_record("MED-CAS-1", 180000000.0, "Hòa giải thành")
        temp_engine.audit_court_recognition("MED-SET-1")

        records = temp_engine.list_mediation_records("ALL")
        assert len(records["mediation_agreements"]) >= 1
        assert len(records["mediation_cases"]) >= 1
        assert len(records["settlement_records"]) >= 1
        assert len(records["court_recognitions"]) >= 1

        telemetry = temp_engine.get_mediation_telemetry()
        assert telemetry["total_mediation_agreements"] >= 1
        assert telemetry["total_mediation_cases"] >= 1
        assert telemetry["successful_settlements"] >= 1
        assert telemetry["settlement_rate_pct"] > 0
        assert telemetry["enforceable_judgments"] >= 1


class TestMediationCliCommands:
    def test_cli_agreement_json(self):
        result = runner.invoke(mediation_app, [
            "agreement",
            "Công ty CP An Khang",
            "Công ty TNHH Bình Minh",
            "--scope", "Tranh chấp cung cấp linh kiện điện tử",
            "--center", "VICMC",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["party_a"] == "Công ty CP An Khang"
        assert data["is_valid"] is True

    def test_cli_agreement_console(self):
        result = runner.invoke(mediation_app, [
            "agreement",
            "Bên X",
            "Bên Y",
        ])
        assert result.exit_code == 0
        assert "Thỏa Thuận Hòa Giải" in result.output or "Nghị Định 22" in result.output

    def test_cli_case_json(self):
        result = runner.invoke(mediation_app, [
            "case",
            "Công ty Dược Phẩm Hải Hà",
            "Chuỗi Nhà Thuốc Tiện Lợi",
            "--amount", "850000000",
            "--category", "SALE_OF_GOODS",
            "--exp", "7",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["party_a"] == "Công ty Dược Phẩm Hải Hà"
        assert data["status"] == "CASE_ACCEPTED"

    def test_cli_settle_json(self):
        result = runner.invoke(mediation_app, [
            "settle",
            "MED-CAS-88AB",
            "--amount", "700000000",
            "--summary", "Bên B đồng ý thanh toán đủ số tiền và rút đơn phản tố",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "SETTLEMENT_SUCCESSFUL"
        assert data["settlement_amount_vnd"] == 700000000.0

    def test_cli_recognize_json(self):
        result = runner.invoke(mediation_app, [
            "recognize",
            "MED-SET-99CD",
            "--court", "TAND Quận Hoàn Kiếm",
            "--months", "2",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_recognized"] is True
        assert data["enforceability_order"] == "ENFORCEABLE_AS_COURT_JUDGMENT"

    def test_cli_convention_json(self):
        result = runner.invoke(mediation_app, [
            "convention",
            "MED-SET-99CD",
            "--cross-border",
            "--commercial",
            "--attestation",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_eligible"] is True

    def test_cli_list_json(self):
        result = runner.invoke(mediation_app, ["list", "--category", "ALL", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mediation_agreements" in data

    def test_cli_status_json(self):
        result = runner.invoke(mediation_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_mediation_agreements" in data


class TestMediationMcpParity:
    def test_scripts_mcp_mediation_handlers(self):
        # 1. Agreement
        a_raw = mcp_script.handle_mediation_agreement({
            "party_a": "Công ty Long Giang",
            "party_b": "Tập đoàn Vạn Phát",
        })
        a_res = json.loads(a_raw)
        assert a_res["is_valid"] is True

        # 2. Case
        c_raw = mcp_script.handle_mediation_case({
            "party_a": "Công ty Long Giang",
            "party_b": "Tập đoàn Vạn Phát",
            "claim_amount_vnd": 600000000.0,
            "mediator_experience_years": 4,
        })
        c_res = json.loads(c_raw)
        assert c_res["status"] == "CASE_ACCEPTED"

        # 3. Settle
        s_raw = mcp_script.handle_mediation_settle({
            "case_id": c_res["case_id"],
            "settlement_amount_vnd": 500000000.0,
            "settlement_summary": "Hai bên thống nhất hòa giải thành",
        })
        s_res = json.loads(s_raw)
        assert s_res["status"] == "SETTLEMENT_SUCCESSFUL"

        # 4. Recognize
        r_raw = mcp_script.handle_mediation_recognize({
            "settlement_id": s_res["settlement_id"],
            "filing_months_elapsed": 1.5,
        })
        r_res = json.loads(r_raw)
        assert r_res["is_recognized"] is True

        # 5. Convention
        cv_raw = mcp_script.handle_mediation_convention({
            "settlement_id": s_res["settlement_id"],
            "is_cross_border": True,
            "is_commercial": True,
        })
        cv_res = json.loads(cv_raw)
        assert cv_res["is_eligible"] is True

        # 6. List
        l_raw = mcp_script.handle_mediation_list({"category": "ALL", "limit": 5})
        l_res = json.loads(l_raw)
        assert "mediation_agreements" in l_res

        # 7. Status
        st_raw = mcp_script.handle_mediation_status({})
        st_res = json.loads(st_raw)
        assert "total_mediation_agreements" in st_res

    def test_core_mcp_mediation_handlers(self):
        server = MekongMcpServer()
        # 1. Agreement
        a_raw = server._handle_mediation_agreement(
            party_a="Công ty Logistics Ánh Dương",
            party_b="Công ty Cảng Biển Quốc Tế",
        )
        a_res = json.loads(a_raw)
        assert a_res["is_valid"] is True

        # 2. Case
        c_raw = server._handle_mediation_case(
            party_a="Công ty Logistics Ánh Dương",
            party_b="Công ty Cảng Biển Quốc Tế",
            claim_amount_vnd=900000000.0,
            mediator_experience_years=8,
        )
        c_res = json.loads(c_raw)
        assert c_res["status"] == "CASE_ACCEPTED"

        # 3. Settle
        s_raw = server._handle_mediation_settle(
            case_id=c_res["case_id"],
            settlement_amount_vnd=800000000.0,
            settlement_summary="Thỏa thuận bồi thường cước vận tải",
        )
        s_res = json.loads(s_raw)
        assert s_res["status"] == "SETTLEMENT_SUCCESSFUL"

        # 4. Recognize
        r_raw = server._handle_mediation_recognize(
            settlement_id=s_res["settlement_id"],
            filing_months_elapsed=3.0,
        )
        r_res = json.loads(r_raw)
        assert r_res["is_recognized"] is True

        # 5. Convention
        cv_raw = server._handle_mediation_convention(
            settlement_id=s_res["settlement_id"],
            is_cross_border=True,
            is_commercial=True,
        )
        cv_res = json.loads(cv_raw)
        assert cv_res["is_eligible"] is True

        # 6. List
        l_raw = server._handle_mediation_list(category="ALL", limit=5)
        l_res = json.loads(l_raw)
        assert "mediation_agreements" in l_res

        # 7. Status
        st_raw = server._handle_mediation_status()
        st_res = json.loads(st_raw)
        assert "total_mediation_agreements" in st_res
