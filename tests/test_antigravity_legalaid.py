"""
Tests for Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite (Phase 137).
Compliant with:
- Law on Legal Aid 2017 (Luật Trợ giúp pháp lý - Law No. 11/2017/QH14)
- Decree No. 144/2017/NĐ-CP detailing implementation of the Law on Legal Aid
- Circular No. 08/2017/TT-BTP on Quality Standards & Assessment of Legal Aid Cases
- Criminal Procedure Code 2015 & Civil Procedure Code 2015
"""

import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.core.legalaid_engine import (
    LegalAidEngine,
    BeneficiaryCategory,
    OfficerType,
    LegalAidForm,
    LegalField,
    QualityRating,
)
from src.cli.commands.legalaid_command import legalaid_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as scripts_mcp


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MEKONG_LEGALAID_DB"] = path
    yield path
    os.environ.pop("MEKONG_LEGALAID_DB", None)
    for p in (path, f"{path}-wal", f"{path}-shm"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def engine(temp_db):
    return LegalAidEngine(db_path=temp_db)


@pytest.fixture
def runner():
    return CliRunner()


class TestLegalAidEngine:
    def test_register_beneficiary_valid(self, engine):
        res = engine.register_beneficiary(
            code="BEN-2025-001",
            full_name="Giàng A Páo",
            citizen_id="004098001234",
            category="DONG_BAO_DANTOC_THIEUSO",
            residence_province="Hà Giang",
            eligibility_proof="Sổ hộ khẩu & xác nhận xã Lũng Cú",
            status="VERIFIED",
        )
        assert res["success"] is True
        assert res["beneficiary"]["code"] == "BEN-2025-001"
        assert res["beneficiary"]["category"] == BeneficiaryCategory.DONG_BAO_DANTOC_THIEUSO.value
        assert "Article 7 Law on Legal Aid 2017" in res["statutory_reference"]

    def test_register_beneficiary_missing_fields(self, engine):
        res = engine.register_beneficiary(
            code="",
            full_name="Nguyễn Văn X",
            citizen_id="",
            category="HO_NGHEO",
            residence_province="",
            eligibility_proof="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_beneficiary_invalid_category(self, engine):
        res = engine.register_beneficiary(
            code="BEN-002",
            full_name="Trần Văn Y",
            citizen_id="001099123456",
            category="INVALID_CAT",
            residence_province="Hà Nội",
            eligibility_proof="GCN",
        )
        assert res["success"] is False
        assert "Invalid beneficiary category" in res["error"]

    def test_register_beneficiary_invalid_status(self, engine):
        res = engine.register_beneficiary(
            code="BEN-003",
            full_name="Lê Thị Z",
            citizen_id="001099654321",
            category="TRE_EM",
            residence_province="TP.HCM",
            eligibility_proof="Giấy khai sinh",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid beneficiary status" in res["error"]

    def test_register_beneficiary_update_existing(self, engine):
        engine.register_beneficiary(
            code="BEN-004",
            full_name="Vàng Thị Mai",
            citizen_id="004099111222",
            category="HO_NGHEO",
            residence_province="Lào Cai",
            eligibility_proof="GCN Hộ nghèo số 10",
        )
        res_update = engine.register_beneficiary(
            code="BEN-004",
            full_name="Vàng Thị Mai",
            citizen_id="004099111222",
            category="HO_NGHEO",
            residence_province="Lào Cai",
            eligibility_proof="GCN Hộ nghèo số 10 (Cấp lại)",
            status="VERIFIED",
        )
        assert res_update["success"] is True
        assert "Cấp lại" in res_update["beneficiary"]["eligibility_proof"]

    def test_register_officer_valid(self, engine):
        res = engine.register_officer(
            officer_code="TGV-HN-001",
            full_name="Trần Minh Đức",
            officer_type="TRO_GIUP_VIEN_PHAP_LY",
            card_number="TGV-0123/BTP",
            organization="Trung tâm Trợ giúp pháp lý nhà nước TP. Hà Nội",
            justice_dept="Sở Tư pháp TP. Hà Nội",
            status="ACTIVE",
        )
        assert res["success"] is True
        assert res["officer"]["officer_code"] == "TGV-HN-001"
        assert res["officer"]["officer_type"] == OfficerType.TRO_GIUP_VIEN_PHAP_LY.value
        assert "Articles 17-23" in res["statutory_reference"]

    def test_register_officer_missing_fields(self, engine):
        res = engine.register_officer(
            officer_code="",
            full_name="",
            officer_type="TRO_GIUP_VIEN_PHAP_LY",
            card_number="",
            organization="",
            justice_dept="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_officer_invalid_type(self, engine):
        res = engine.register_officer(
            officer_code="OFF-002",
            full_name="Nguyễn Văn A",
            officer_type="INVALID_TYPE",
            card_number="CARD-01",
            organization="Org A",
            justice_dept="Sở TP",
        )
        assert res["success"] is False
        assert "Invalid officer type" in res["error"]

    def test_register_officer_invalid_status(self, engine):
        res = engine.register_officer(
            officer_code="OFF-003",
            full_name="Nguyễn Văn B",
            officer_type="LUAT_SU_KY_HOP_DONG",
            card_number="LS-01",
            organization="VPLS B",
            justice_dept="Sở TP",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid officer status" in res["error"]

    def test_register_officer_update_existing(self, engine):
        engine.register_officer(
            officer_code="OFF-004",
            full_name="Lê Văn C",
            officer_type="LUAT_SU_CONG_TAC_VIEN",
            card_number="LS-02",
            organization="Công ty Luật C1",
            justice_dept="Sở Tư pháp",
        )
        res_update = engine.register_officer(
            officer_code="OFF-004",
            full_name="Lê Văn C",
            officer_type="LUAT_SU_CONG_TAC_VIEN",
            card_number="LS-02",
            organization="Công ty Luật C2",
            justice_dept="Sở Tư pháp",
        )
        assert res_update["success"] is True
        assert res_update["officer"]["organization"] == "Công ty Luật C2"

    def test_file_request_valid(self, engine):
        res = engine.file_request(
            request_code="YCTGPL-2025-001",
            beneficiary_code="BEN-2025-001",
            form="THAM_GIA_TO_TUNG",
            legal_field="HINH_SU",
            case_title="Bào chữa cho bị cáo trong vụ án hình sự sơ thẩm",
            request_date="2025-02-15",
            assigned_officer_code="TGV-HN-001",
            status="ASSIGNED",
        )
        assert res["success"] is True
        assert res["request"]["request_code"] == "YCTGPL-2025-001"
        assert res["request"]["form"] == LegalAidForm.THAM_GIA_TO_TUNG.value
        assert "Articles 29-33" in res["statutory_reference"]

    def test_file_request_missing_fields(self, engine):
        res = engine.file_request(
            request_code="",
            beneficiary_code="",
            form="TU_VAN_PHAP_LUAT",
            legal_field="DAN_SU",
            case_title="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_file_request_invalid_form(self, engine):
        res = engine.file_request(
            request_code="REQ-002",
            beneficiary_code="BEN-002",
            form="INVALID_FORM",
            legal_field="DAN_SU",
            case_title="Tranh chấp đất đai",
        )
        assert res["success"] is False
        assert "Invalid legal aid form" in res["error"]

    def test_file_request_invalid_field(self, engine):
        res = engine.file_request(
            request_code="REQ-003",
            beneficiary_code="BEN-003",
            form="TU_VAN_PHAP_LUAT",
            legal_field="INVALID_FIELD",
            case_title="Tư vấn",
        )
        assert res["success"] is False
        assert "Invalid legal field" in res["error"]

    def test_file_request_invalid_status(self, engine):
        res = engine.file_request(
            request_code="REQ-004",
            beneficiary_code="BEN-004",
            form="TU_VAN_PHAP_LUAT",
            legal_field="HON_NHAN_GIA_DINH",
            case_title="Hôn nhân gia đình",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid request status" in res["error"]

    def test_assign_proceeding_valid(self, engine):
        res = engine.assign_proceeding(
            assignment_code="QD-TGPL-2025-001",
            request_code="YCTGPL-2025-001",
            case_number="HSST-2025/08",
            proceeding_agency="Tòa án nhân dân huyện Mèo Vạc",
            procedural_role="NGUOI_BAO_CHUA",
            decision_date="2025-02-18",
            status="ACTIVE",
            notes="Cử Trợ giúp viên pháp lý bào chữa tại phiên tòa",
        )
        assert res["success"] is True
        assert res["proceeding"]["assignment_code"] == "QD-TGPL-2025-001"
        assert "Article 31 Law on Legal Aid 2017" in res["statutory_reference"]

    def test_assign_proceeding_missing_fields(self, engine):
        res = engine.assign_proceeding(
            assignment_code="",
            request_code="",
            case_number="",
            proceeding_agency="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_assign_proceeding_invalid_role(self, engine):
        res = engine.assign_proceeding(
            assignment_code="QD-002",
            request_code="REQ-002",
            case_number="DS-01",
            proceeding_agency="TAND Tỉnh",
            procedural_role="INVALID_ROLE",
        )
        assert res["success"] is False
        assert "Invalid procedural role" in res["error"]

    def test_assign_proceeding_invalid_status(self, engine):
        res = engine.assign_proceeding(
            assignment_code="QD-003",
            request_code="REQ-003",
            case_number="DS-02",
            proceeding_agency="TAND Tỉnh",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid proceeding status" in res["error"]

    def test_evaluate_quality_valid_auto_rating(self, engine):
        res = engine.evaluate_quality(
            eval_code="DGCL-2025-001",
            request_code="YCTGPL-2025-001",
            evaluator_name="Giám đốc Trung tâm TGPL",
            score=92.5,
            evaluation_date="2025-03-01",
            notes="Hồ sơ đầy đủ, bào chữa đạt kết quả tốt",
        )
        assert res["success"] is True
        assert res["evaluation"]["eval_code"] == "DGCL-2025-001"
        assert res["evaluation"]["quality_rating"] == QualityRating.XUAT_SAC.value
        assert "Circular No. 08/2017/TT-BTP" in res["statutory_reference"]

    def test_evaluate_quality_explicit_rating(self, engine):
        res = engine.evaluate_quality(
            eval_code="DGCL-2025-002",
            request_code="YCTGPL-2025-002",
            evaluator_name="Hội đồng Đánh giá",
            score=85.0,
            quality_rating="TOT",
        )
        assert res["success"] is True
        assert res["evaluation"]["quality_rating"] == QualityRating.TOT.value

    def test_evaluate_quality_missing_fields(self, engine):
        res = engine.evaluate_quality(
            eval_code="",
            request_code="",
            evaluator_name="",
            score=None,
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_evaluate_quality_score_out_of_bounds(self, engine):
        res = engine.evaluate_quality(
            eval_code="DGCL-003",
            request_code="REQ-003",
            evaluator_name="Evaluator A",
            score=105.0,
        )
        assert res["success"] is False
        assert "between 0.0 and 100.0" in res["error"]

    def test_evaluate_quality_invalid_rating(self, engine):
        res = engine.evaluate_quality(
            eval_code="DGCL-004",
            request_code="REQ-004",
            evaluator_name="Evaluator B",
            score=75.0,
            quality_rating="INVALID_RATING",
        )
        assert res["success"] is False
        assert "Invalid quality rating" in res["error"]

    def test_list_records_all_categories(self, engine):
        engine.register_beneficiary(
            code="BEN-01",
            full_name="Nguyen Van A",
            citizen_id="001",
            category="HO_NGHEO",
            residence_province="HN",
            eligibility_proof="Proof",
        )
        engine.register_officer(
            officer_code="OFF-01",
            full_name="Le Van B",
            officer_type="TRO_GIUP_VIEN_PHAP_LY",
            card_number="CARD-01",
            organization="Org",
            justice_dept="Dept",
        )
        engine.file_request(
            request_code="REQ-01",
            beneficiary_code="BEN-01",
            form="TU_VAN_PHAP_LUAT",
            legal_field="DAN_SU",
            case_title="Case 1",
        )
        engine.assign_proceeding(
            assignment_code="QD-01",
            request_code="REQ-01",
            case_number="Case-01",
            proceeding_agency="Agency",
        )
        engine.evaluate_quality(
            eval_code="EV-01",
            request_code="REQ-01",
            evaluator_name="Eval",
            score=88.0,
        )

        for cat in ("beneficiaries", "officers", "requests", "proceedings", "evaluations"):
            res = engine.list_records(category=cat, limit=10)
            assert res["success"] is True
            assert len(res["records"]) == 1

    def test_list_records_invalid_category(self, engine):
        res = engine.list_records(category="invalid_category")
        assert res["success"] is False
        assert "Invalid category" in res["error"]

    def test_telemetry_status(self, engine):
        status = engine.get_telemetry_status()
        assert status["success"] is True
        assert "telemetry" in status
        telemetry = status["telemetry"]
        assert "beneficiaries" in telemetry
        assert "legal_aid_officers" in telemetry
        assert "requests_and_dockets" in telemetry
        assert "court_proceedings" in telemetry
        assert "quality_evaluations" in telemetry


class TestLegalAidCli:
    def test_cli_status(self, runner, temp_db):
        res = runner.invoke(legalaid_app, ["status"])
        assert res.exit_code == 0
        assert "VIETNAMESE STATE LEGAL AID SYSTEM" in res.output

    def test_cli_status_json(self, runner, temp_db):
        res = runner.invoke(legalaid_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert "telemetry" in data

    def test_cli_main_callback_json(self, runner, temp_db):
        res = runner.invoke(legalaid_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_beneficiary_cmd(self, runner, temp_db):
        res = runner.invoke(legalaid_app, [
            "beneficiary",
            "--code", "BEN-CLI-01",
            "--name", "Hoàng A Sùng",
            "--citizen-id", "004099000111",
            "--category", "DONG_BAO_DANTOC_THIEUSO",
            "--province", "Lai Châu",
            "--proof", "Xác nhận UBND xã",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["beneficiary"]["code"] == "BEN-CLI-01"

    def test_cli_beneficiary_missing_options(self, runner, temp_db):
        res = runner.invoke(legalaid_app, ["beneficiary"])
        assert res.exit_code != 0

    def test_cli_officer_cmd(self, runner, temp_db):
        res = runner.invoke(legalaid_app, [
            "officer",
            "--code", "TGV-CLI-01",
            "--name", "Phan Thanh Liêm",
            "--type", "TRO_GIUP_VIEN_PHAP_LY",
            "--card", "TGV-9999",
            "--org", "Trung tâm TGPL Lai Châu",
            "--dept", "Sở Tư pháp Lai Châu",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["officer"]["officer_code"] == "TGV-CLI-01"

    def test_cli_request_cmd(self, runner, temp_db):
        res = runner.invoke(legalaid_app, [
            "request",
            "--code", "REQ-CLI-01",
            "--beneficiary", "BEN-CLI-01",
            "--form", "THAM_GIA_TO_TUNG",
            "--field", "HINH_SU",
            "--title", "Bào chữa vụ án hình sự",
            "--officer", "TGV-CLI-01",
            "--status", "ASSIGNED",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["request"]["request_code"] == "REQ-CLI-01"

    def test_cli_proceeding_cmd(self, runner, temp_db):
        res = runner.invoke(legalaid_app, [
            "proceeding",
            "--code", "QD-CLI-01",
            "--request", "REQ-CLI-01",
            "--case", "HSST-01/2025",
            "--agency", "TAND Tỉnh Lai Châu",
            "--role", "NGUOI_BAO_CHUA",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["proceeding"]["assignment_code"] == "QD-CLI-01"

    def test_cli_eval_cmd(self, runner, temp_db):
        res = runner.invoke(legalaid_app, [
            "eval",
            "--code", "DG-CLI-01",
            "--request", "REQ-CLI-01",
            "--evaluator", "Giám đốc Trung tâm",
            "--score", "91.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["evaluation"]["eval_code"] == "DG-CLI-01"

    def test_cli_list_cmd(self, runner, temp_db):
        runner.invoke(legalaid_app, [
            "beneficiary",
            "--code", "BEN-CLI-02",
            "--name", "Tran B",
            "--citizen-id", "002",
            "--category", "HO_NGHEO",
            "--province", "HN",
            "--proof", "Proof",
            "--json",
        ])
        res = runner.invoke(legalaid_app, ["list", "beneficiaries", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert len(data["records"]) >= 1


class TestLegalAidCoreMcp:
    def test_core_mcp_handlers(self, temp_db):
        server = MekongMcpServer()
        # Register beneficiary
        res_ben = json.loads(server._handle_legalaid_beneficiary(
            code="BEN-MCP-01",
            name="Triệu Thị Hoa",
            citizen_id="004099888999",
            category="DONG_BAO_DANTOC_THIEUSO",
            province="Cao Bằng",
            proof="Giấy xác nhận",
        ))
        assert res_ben["success"] is True

        # Register officer
        res_off = json.loads(server._handle_legalaid_officer(
            code="TGV-MCP-01",
            name="Đoàn Văn Hùng",
            card="TGV-CB-01",
            org="Trung tâm TGPL Cao Bằng",
            dept="Sở Tư pháp Cao Bằng",
        ))
        assert res_off["success"] is True

        # File request
        res_req = json.loads(server._handle_legalaid_request(
            code="REQ-MCP-01",
            beneficiary="BEN-MCP-01",
            title="Đại diện giải quyết tranh chấp đất rừng",
            form="DAI_DIEN_NGOAI_TO_TUNG",
            field="DAT_DAI",
        ))
        assert res_req["success"] is True

        # Assign proceeding
        res_proc = json.loads(server._handle_legalaid_proceeding(
            code="QD-MCP-01",
            request="REQ-MCP-01",
            case="DS-2025/11",
            agency="UBND Huyện",
            role="NGUOI_DAI_DIEN_HOP_PHAP",
        ))
        assert res_proc["success"] is True

        # Evaluate quality
        res_eval = json.loads(server._handle_legalaid_eval(
            code="DG-MCP-01",
            request="REQ-MCP-01",
            evaluator="Ban Đánh giá chất lượng",
            score=86.5,
        ))
        assert res_eval["success"] is True

        # List
        res_list = json.loads(server._handle_legalaid_list(category="beneficiaries"))
        assert res_list["success"] is True
        assert len(res_list["records"]) >= 1

        # Status
        res_status = json.loads(server._handle_legalaid_status())
        assert res_status["success"] is True

    def test_core_mcp_aliases(self, temp_db):
        server = MekongMcpServer()
        assert server._handle_mekong_legalaid_beneficiary == server._handle_legalaid_beneficiary
        assert server._handle_mekong_legalaid_officer == server._handle_legalaid_officer
        assert server._handle_mekong_legalaid_request == server._handle_legalaid_request
        assert server._handle_mekong_legalaid_proceeding == server._handle_legalaid_proceeding
        assert server._handle_mekong_legalaid_eval == server._handle_legalaid_eval
        assert server._handle_mekong_legalaid_list == server._handle_legalaid_list
        assert server._handle_mekong_legalaid_status == server._handle_legalaid_status


class TestLegalAidScriptsMcp:
    def test_scripts_mcp_handlers(self, temp_db):
        # Register beneficiary
        res_ben = json.loads(scripts_mcp.handle_legalaid_beneficiary({
            "code": "BEN-SCR-01",
            "name": "Lò Văn Khang",
            "citizen_id": "004099777888",
            "category": "DONG_BAO_DANTOC_THIEUSO",
            "province": "Sơn La",
            "proof": "Giấy xác nhận",
        }))
        assert res_ben["success"] is True

        # Register officer
        res_off = json.loads(scripts_mcp.handle_legalaid_officer({
            "code": "TGV-SCR-01",
            "name": "Hoàng Thị Quyên",
            "card": "TGV-SL-01",
            "org": "Trung tâm TGPL Sơn La",
            "dept": "Sở Tư pháp Sơn La",
        }))
        assert res_off["success"] is True

        # File request
        res_req = json.loads(scripts_mcp.handle_legalaid_request({
            "code": "REQ-SCR-01",
            "beneficiary": "BEN-SCR-01",
            "title": "Tư vấn chế độ bảo trợ xã hội",
            "form": "TU_VAN_PHAP_LUAT",
            "field": "HANH_CHINH",
        }))
        assert res_req["success"] is True

        # Assign proceeding
        res_proc = json.loads(scripts_mcp.handle_legalaid_proceeding({
            "code": "QD-SCR-01",
            "request": "REQ-SCR-01",
            "case": "HC-2025/03",
            "agency": "TAND Tỉnh Sơn La",
        }))
        assert res_proc["success"] is True

        # Evaluate quality
        res_eval = json.loads(scripts_mcp.handle_legalaid_eval({
            "code": "DG-SCR-01",
            "request": "REQ-SCR-01",
            "evaluator": "Giám đốc",
            "score": 95.0,
        }))
        assert res_eval["success"] is True

        # List
        res_list = json.loads(scripts_mcp.handle_legalaid_list({"category": "beneficiaries"}))
        assert res_list["success"] is True

        # Status
        res_status = json.loads(scripts_mcp.handle_legalaid_status({}))
        assert res_status["success"] is True

    def test_scripts_mcp_core_handlers_map(self):
        for name in (
            "mekong_legalaid_beneficiary",
            "mekong_legalaid_officer",
            "mekong_legalaid_request",
            "mekong_legalaid_proceeding",
            "mekong_legalaid_eval",
            "mekong_legalaid_list",
            "mekong_legalaid_status",
            "legalaid_beneficiary",
            "legalaid_officer",
            "legalaid_request",
            "legalaid_proceeding",
            "legalaid_eval",
            "legalaid_list",
            "legalaid_status",
        ):
            assert name in scripts_mcp.CORE_HANDLERS
            assert callable(scripts_mcp.CORE_HANDLERS[name])

    def test_scripts_mcp_tools_spec(self):
        names = {t["name"] for t in scripts_mcp.CORE_TOOLS_SPEC}
        for expected in (
            "mekong_legalaid_beneficiary",
            "mekong_legalaid_officer",
            "mekong_legalaid_request",
            "mekong_legalaid_proceeding",
            "mekong_legalaid_eval",
            "mekong_legalaid_list",
            "mekong_legalaid_status",
        ):
            assert expected in names
