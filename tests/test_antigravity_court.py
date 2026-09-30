"""
Tests for Vietnamese People's Courts, Judicial Adjudication & Electronic Court Suite (Phase 135).
Compliant with:
- Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)
- Civil Procedure Code 2015, Criminal Procedure Code 2015, Law on Administrative Procedures 2015
- Resolution No. 33/2021/QH15 on Online Court Hearings
"""

import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.core.court_engine import (
    CourtEngine,
    JudicialRole,
    CourtLevel,
    CaseType,
    ProceduralStage,
    HearingFormat,
    JudgmentType,
    DocumentType,
)
from src.cli.commands.court_command import court_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as scripts_mcp


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MEKONG_COURT_DB"] = path
    yield path
    os.environ.pop("MEKONG_COURT_DB", None)
    for p in (path, f"{path}-wal", f"{path}-shm"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def engine(temp_db):
    return CourtEngine(db_path=temp_db)


@pytest.fixture
def runner():
    return CliRunner()


class TestCourtEngine:
    def test_register_officer_valid(self, engine):
        res = engine.register_officer(
            code="TP-2025-001",
            full_name="Nguyễn Văn An",
            role="THAM_PHAN_CHINH",
            court_level="TAND_CAP_TINH",
            court_name="Tòa án nhân dân TP. Hồ Chí Minh",
            appointment_decision="QD-123/CTN",
            appointed_date="2025-01-10",
            term_years=5,
            status="ACTIVE",
        )
        assert res["success"] is True
        assert res["officer"]["code"] == "TP-2025-001"
        assert res["officer"]["role"] == JudicialRole.THAM_PHAN_CHINH.value
        assert "Law on Organization of People's Courts 2024" in res["statutory_reference"]

    def test_register_officer_missing_fields(self, engine):
        res = engine.register_officer(
            code="",
            full_name="",
            role="THAM_PHAN",
            court_level="TAND_CAP_HUYEN",
            court_name="",
            appointment_decision="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_officer_invalid_role(self, engine):
        res = engine.register_officer(
            code="TP-002",
            full_name="Trần Thị B",
            role="INVALID_ROLE",
            court_level="TAND_CAP_TINH",
            court_name="TAND Hà Nội",
            appointment_decision="QD-456",
        )
        assert res["success"] is False
        assert "Invalid judicial role" in res["error"]

    def test_register_officer_invalid_level(self, engine):
        res = engine.register_officer(
            code="TP-003",
            full_name="Lê Văn C",
            role="THAM_PHAN",
            court_level="INVALID_LEVEL",
            court_name="TAND Đà Nẵng",
            appointment_decision="QD-789",
        )
        assert res["success"] is False
        assert "Invalid court level" in res["error"]

    def test_register_officer_invalid_status(self, engine):
        res = engine.register_officer(
            code="TP-004",
            full_name="Phạm Văn D",
            role="THAM_PHAN",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND Quận 1",
            appointment_decision="QD-101",
            status="UNKNOWN_STATUS",
        )
        assert res["success"] is False
        assert "Invalid officer status" in res["error"]

    def test_register_officer_supreme_term(self, engine):
        res = engine.register_officer(
            code="TP-TC-001",
            full_name="Nguyễn Hòa Bình",
            role="THAM_PHAN_TOI_CAO",
            court_level="TAND_TOI_CAO",
            court_name="Tòa án nhân dân tối cao",
            appointment_decision="NQ-QH15",
            term_years=3,
        )
        assert res["success"] is True
        assert res["officer"]["term_years"] >= 10

    def test_register_officer_update_existing(self, engine):
        engine.register_officer(
            code="TP-005",
            full_name="Võ Văn E",
            role="THAM_PHAN",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND Huyện A",
            appointment_decision="QD-1",
        )
        res = engine.register_officer(
            code="TP-005",
            full_name="Võ Văn E",
            role="THAM_PHAN_CHINH",
            court_level="TAND_CAP_TINH",
            court_name="TAND Tỉnh B",
            appointment_decision="QD-2",
        )
        assert res["success"] is True
        assert res["officer"]["role"] == "THAM_PHAN_CHINH"

    def test_file_case_valid(self, engine):
        res = engine.file_case(
            case_number="01/2025/TLST-KDTM",
            case_title="Tranh chấp hợp đồng mua bán linh kiện",
            case_type="KINH_DOANH_THUONG_MAI",
            court_level="TAND_CAP_TINH",
            court_name="TAND TP. Hà Nội",
            plaintiff_prosecutor="Công ty TNHH Kim Khí Á Châu",
            defendant_accused="Công ty Cổ phần Cơ khí Bắc Hà",
            claim_value=1500000000.0,
            is_electronic_dossier=True,
        )
        assert res["success"] is True
        assert res["case"]["case_number"] == "01/2025/TLST-KDTM"
        assert res["case"]["case_type"] == CaseType.KINH_DOANH_THUONG_MAI.value
        assert res["case"]["claim_value"] == 1500000000.0
        assert res["case"]["is_electronic_dossier"] is True

    def test_file_case_missing_fields(self, engine):
        res = engine.file_case(
            case_number="",
            case_title="",
            case_type="DAN_SU",
            court_level="",
            court_name="",
            plaintiff_prosecutor="",
            defendant_accused="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_file_case_invalid_type(self, engine):
        res = engine.file_case(
            case_number="02/2025/TLST",
            case_title="Vụ án mẫu",
            case_type="INVALID_TYPE",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND Quận 3",
            plaintiff_prosecutor="A",
            defendant_accused="B",
        )
        assert res["success"] is False
        assert "Invalid case type" in res["error"]

    def test_file_case_invalid_level(self, engine):
        res = engine.file_case(
            case_number="03/2025/TLST",
            case_title="Vụ án mẫu 2",
            case_type="DAN_SU",
            court_level="NONEXISTENT_LEVEL",
            court_name="TAND",
            plaintiff_prosecutor="A",
            defendant_accused="B",
        )
        assert res["success"] is False
        assert "Invalid court level" in res["error"]

    def test_file_case_invalid_stage(self, engine):
        res = engine.file_case(
            case_number="04/2025/TLST",
            case_title="Vụ án mẫu 3",
            case_type="DAN_SU",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND",
            plaintiff_prosecutor="A",
            defendant_accused="B",
            stage="INVALID_STAGE",
        )
        assert res["success"] is False
        assert "Invalid procedural stage" in res["error"]

    def test_file_case_update_existing(self, engine):
        engine.file_case(
            case_number="05/2025/TLST-DS",
            case_title="Tranh chấp quyền sử dụng đất",
            case_type="DAN_SU",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND Huyện X",
            plaintiff_prosecutor="Nguyễn Văn F",
            defendant_accused="Lê Văn G",
        )
        res = engine.file_case(
            case_number="05/2025/TLST-DS",
            case_title="Tranh chấp quyền sử dụng đất và tài sản gắn liền",
            case_type="DAN_SU",
            court_level="TAND_CAP_HUYEN",
            court_name="TAND Huyện X",
            plaintiff_prosecutor="Nguyễn Văn F",
            defendant_accused="Lê Văn G",
            stage="CHUAN_BI_XET_XU",
        )
        assert res["success"] is True
        assert res["case"]["stage"] == "CHUAN_BI_XET_XU"

    def test_schedule_hearing_valid(self, engine):
        engine.file_case(
            case_number="10/2025/TLST-HS",
            case_title="Vụ án lừa đảo chiếm đoạt tài sản",
            case_type="HINH_SU",
            court_level="TAND_CAP_TINH",
            court_name="TAND TP. Cần Thơ",
            plaintiff_prosecutor="VKSND TP. Cần Thơ",
            defendant_accused="Đặng Văn H",
        )
        res = engine.schedule_hearing(
            hearing_code="PT-2025-001",
            case_id="10/2025/TLST-HS",
            hearing_date="2025-03-15T08:30:00",
            hearing_type="SO_THAM",
            format="DIRECT",
            courtroom="Phòng xử án số 2",
        )
        assert res["success"] is True
        assert res["hearing"]["hearing_code"] == "PT-2025-001"
        assert res["hearing"]["format"] == "DIRECT"

    def test_schedule_hearing_nonexistent_case(self, engine):
        res = engine.schedule_hearing(
            hearing_code="PT-2025-002",
            case_id="NONEXISTENT_CASE",
            hearing_date="2025-03-20T08:00:00",
        )
        assert res["success"] is False
        assert "does not exist" in res["error"]

    def test_schedule_hearing_invalid_format(self, engine):
        res = engine.schedule_hearing(
            hearing_code="PT-2025-003",
            case_id="CASE_1",
            hearing_date="2025-03-20",
            format="INVALID_FORMAT",
        )
        assert res["success"] is False
        assert "Invalid hearing format" in res["error"]

    def test_schedule_hearing_invalid_status(self, engine):
        res = engine.schedule_hearing(
            hearing_code="PT-2025-004",
            case_id="CASE_1",
            hearing_date="2025-03-20",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid hearing status" in res["error"]

    def test_schedule_hearing_virtual_format(self, engine):
        engine.file_case(
            case_number="11/2025/TLST-HC",
            case_title="Khiếu kiện quyết định thu hồi đất",
            case_type="HANH_CHINH",
            court_level="TAND_CAP_TINH",
            court_name="TAND Tỉnh Đồng Nai",
            plaintiff_prosecutor="Ông Nguyễn Văn I",
            defendant_accused="UBND Huyện Long Thành",
        )
        res = engine.schedule_hearing(
            hearing_code="PT-2025-ONLINE-01",
            case_id="11/2025/TLST-HC",
            hearing_date="2025-04-10T09:00:00",
            hearing_type="SO_THAM",
            format="ONLINE_VIRTUAL",
            courtroom="https://ecourt.toaan.gov.vn/room/88219",
            notes="Phiên tòa trực tuyến theo Nghị quyết 33/2021/QH15",
        )
        assert res["success"] is True
        assert res["hearing"]["format"] == HearingFormat.ONLINE_VIRTUAL.value
        assert "Nghị quyết 33/2021/QH15" in res["hearing"]["notes"]

    def test_issue_judgment_valid(self, engine):
        engine.file_case(
            case_number="12/2025/TLST-KDTM",
            case_title="Tranh chấp bảo lãnh tín dụng",
            case_type="KINH_DOANH_THUONG_MAI",
            court_level="TAND_CAP_TINH",
            court_name="TAND TP. Hải Phòng",
            plaintiff_prosecutor="Ngân hàng TMCP Việt Á",
            defendant_accused="Công ty TNHH Vận tải Biển Đông",
        )
        res = engine.issue_judgment(
            judgment_number="05/2025/KDTM-ST",
            case_id="12/2025/TLST-KDTM",
            judgment_type="BAN_AN_SO_THAM",
            verdict_summary="Chấp nhận toàn bộ yêu cầu khởi kiện của nguyên đơn",
            penalty_or_remedy="Buộc bị đơn thanh toán nợ gốc 5 tỷ đồng và tiền lãi phát sinh",
            issue_date="2025-02-01",
            court_fee=112000000.0,
            appeal_deadline_days=15,
            is_public_portal_disclosed=True,
        )
        assert res["success"] is True
        assert res["judgment"]["judgment_number"] == "05/2025/KDTM-ST"
        assert res["judgment"]["judgment_type"] == JudgmentType.BAN_AN_SO_THAM.value
        assert res["judgment"]["effective_date"] == "2025-02-16"
        assert res["judgment"]["is_public_portal_disclosed"] is True

    def test_issue_judgment_nonexistent_case(self, engine):
        res = engine.issue_judgment(
            judgment_number="06/2025/DS-ST",
            case_id="NO_SUCH_CASE",
            judgment_type="BAN_AN_SO_THAM",
            verdict_summary="Tuyên xử",
            penalty_or_remedy="Không",
        )
        assert res["success"] is False
        assert "does not exist" in res["error"]

    def test_issue_judgment_invalid_type(self, engine):
        res = engine.issue_judgment(
            judgment_number="07/2025/ST",
            case_id="CASE_1",
            judgment_type="INVALID_TYPE",
            verdict_summary="Verdict",
            penalty_or_remedy="Remedy",
        )
        assert res["success"] is False
        assert "Invalid judgment type" in res["error"]

    def test_submit_electronic_filing_valid(self, engine):
        res = engine.submit_electronic_filing(
            filing_code="EC-2025-0001",
            submitter_name="Lê Quốc Bảo",
            submitter_id_card="079090123456",
            document_title="Đơn khởi kiện tranh chấp vi phạm hợp đồng",
            document_type="DON_KHOI_KIEN",
            content_payload="Kính gửi Tòa án nhân dân Quận 1...",
        )
        assert res["success"] is True
        assert res["electronic_filing"]["filing_code"] == "EC-2025-0001"
        assert res["electronic_filing"]["document_type"] == DocumentType.DON_KHOI_KIEN.value
        assert len(res["electronic_filing"]["verification_hash"]) == 64

    def test_submit_electronic_filing_missing_fields(self, engine):
        res = engine.submit_electronic_filing(
            filing_code="",
            submitter_name="",
            submitter_id_card="",
            document_title="",
            document_type="DON_KHOI_KIEN",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_submit_electronic_filing_invalid_type(self, engine):
        res = engine.submit_electronic_filing(
            filing_code="EC-002",
            submitter_name="B",
            submitter_id_card="001",
            document_title="Title",
            document_type="INVALID_DOC",
        )
        assert res["success"] is False
        assert "Invalid document type" in res["error"]

    def test_submit_electronic_filing_invalid_status(self, engine):
        res = engine.submit_electronic_filing(
            filing_code="EC-003",
            submitter_name="C",
            submitter_id_card="002",
            document_title="Title",
            document_type="DON_KHANG_CAO",
            status="UNKNOWN_STATUS",
        )
        assert res["success"] is False
        assert "Invalid filing status" in res["error"]

    def test_list_records_valid_and_invalid(self, engine):
        engine.register_officer(
            code="TP-LIST-01",
            full_name="Officer A",
            role="THAM_PHAN",
            court_level="TAND_CAP_HUYEN",
            court_name="Court A",
            appointment_decision="QD-1",
        )
        res_ok = engine.list_records(category="officers")
        assert res_ok["success"] is True
        assert res_ok["count"] >= 1

        res_err = engine.list_records(category="invalid_category")
        assert res_err["success"] is False
        assert "Invalid category" in res_err["error"]

    def test_get_telemetry_status(self, engine):
        engine.register_officer(
            code="TP-TEL-01",
            full_name="Judge Tel",
            role="THAM_PHAN_CHINH",
            court_level="TAND_CAP_TINH",
            court_name="Court Tel",
            appointment_decision="QD-TEL",
        )
        engine.file_case(
            case_number="99/2025/TLST-DS",
            case_title="Dispute Tel",
            case_type="DAN_SU",
            court_level="TAND_CAP_TINH",
            court_name="Court Tel",
            plaintiff_prosecutor="Plaintiff Tel",
            defendant_accused="Defendant Tel",
            claim_value=500000000.0,
            is_electronic_dossier=True,
        )
        status = engine.get_telemetry_status()
        assert status["success"] is True
        assert status["telemetry"]["officers"]["total"] >= 1
        assert status["telemetry"]["cases"]["total"] >= 1
        assert status["telemetry"]["cases"]["e_dossiers"] >= 1
        assert "Law on Organization of People's Courts 2024" in status["statutory_framework"]


class TestCourtCLI:
    def test_cli_default_dashboard(self, runner, temp_db):
        res = runner.invoke(court_app, [])
        assert res.exit_code == 0
        assert "TÒA ÁN NHÂN DÂN" in res.output

    def test_cli_default_dashboard_json(self, runner, temp_db):
        res = runner.invoke(court_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert "telemetry" in data

    def test_cli_officer_register(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "officer",
            "--code", "TP-CLI-01",
            "--name", "Hoàng Kim Oanh",
            "--role", "THAM_PHAN_CHINH",
            "--level", "TAND_CAP_TINH",
            "--court", "TAND TP. Đà Nẵng",
            "--decision", "QD-777",
        ])
        assert res.exit_code == 0
        assert "registered successfully" in res.output

    def test_cli_officer_register_json(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "officer",
            "--code", "TP-CLI-02",
            "--name", "Đoàn Văn M",
            "--role", "THAM_PHAN",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND Quận Hải Châu",
            "--decision", "QD-888",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["officer"]["code"] == "TP-CLI-02"

    def test_cli_officer_register_error(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "officer",
            "--code", "TP-CLI-ERR",
            "--name", "Error",
            "--role", "INVALID_ROLE",
            "--level", "TAND_CAP_HUYEN",
            "--court", "Court",
            "--decision", "QD-ERR",
        ])
        assert res.exit_code == 0
        assert "Failed to register" in res.output

    def test_cli_case_file(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "case",
            "--number", "20/2025/TLST-KDTM",
            "--title", "Tranh chấp phân phối độc quyền",
            "--type", "KINH_DOANH_THUONG_MAI",
            "--level", "TAND_CAP_TINH",
            "--court", "TAND Tỉnh Bình Dương",
            "--plaintiff", "Công ty CP Logistics A",
            "--defendant", "Công ty TNHH Vận tải B",
            "--claim", "2500000000",
        ])
        assert res.exit_code == 0
        assert "Case docketed successfully" in res.output

    def test_cli_case_file_json(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "case",
            "--number", "21/2025/TLST-DS",
            "--title", "Vay tài sản",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND Thủ Đức",
            "--plaintiff", "Bà K",
            "--defendant", "Ông L",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_hearing_schedule(self, runner, temp_db):
        runner.invoke(court_app, [
            "case",
            "--number", "25/2025/TLST-DS",
            "--title", "Case For Hearing",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND Quận 1",
            "--plaintiff", "A",
            "--defendant", "B",
        ])
        res = runner.invoke(court_app, [
            "hearing",
            "--code", "PT-CLI-01",
            "--case", "25/2025/TLST-DS",
            "--date", "2025-05-01T08:00:00",
            "--format", "DIRECT",
        ])
        assert res.exit_code == 0
        assert "Court hearing scheduled" in res.output

    def test_cli_hearing_schedule_json(self, runner, temp_db):
        runner.invoke(court_app, [
            "case",
            "--number", "26/2025/TLST-DS",
            "--title", "Case For Hearing 2",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND Quận 1",
            "--plaintiff", "A",
            "--defendant", "B",
        ])
        res = runner.invoke(court_app, [
            "hearing",
            "--code", "PT-CLI-02",
            "--case", "26/2025/TLST-DS",
            "--date", "2025-05-02T09:00:00",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_judgment_issue(self, runner, temp_db):
        runner.invoke(court_app, [
            "case",
            "--number", "30/2025/TLST-DS",
            "--title", "Case Judgment",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND",
            "--plaintiff", "A",
            "--defendant", "B",
        ])
        res = runner.invoke(court_app, [
            "judgment",
            "--number", "15/2025/DS-ST",
            "--case", "30/2025/TLST-DS",
            "--type", "BAN_AN_SO_THAM",
            "--verdict", "Chấp nhận yêu cầu",
            "--remedy", "Buộc bồi thường",
            "--fee", "25000000",
        ])
        assert res.exit_code == 0
        assert "Judgment issued successfully" in res.output

    def test_cli_judgment_issue_json(self, runner, temp_db):
        runner.invoke(court_app, [
            "case",
            "--number", "31/2025/TLST-DS",
            "--title", "Case Judgment 2",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND",
            "--plaintiff", "A",
            "--defendant", "B",
        ])
        res = runner.invoke(court_app, [
            "judgment",
            "--number", "16/2025/DS-ST",
            "--case", "31/2025/TLST-DS",
            "--type", "BAN_AN_SO_THAM",
            "--verdict", "Bác đơn kiện",
            "--remedy", "Nguyên đơn chịu án phí",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_filing_submit(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "filing",
            "--code", "EC-CLI-01",
            "--name", "Trần Đình Trọng",
            "--id-card", "001090001122",
            "--title", "Đơn khởi kiện trực tuyến",
            "--type", "DON_KHOI_KIEN",
        ])
        assert res.exit_code == 0
        assert "Electronic filing submitted" in res.output

    def test_cli_filing_submit_json(self, runner, temp_db):
        res = runner.invoke(court_app, [
            "filing",
            "--code", "EC-CLI-02",
            "--name", "Trần Đình Trọng",
            "--id-card", "001090001122",
            "--title", "Đơn kháng cáo phúc thẩm",
            "--type", "DON_KHANG_CAO",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_list(self, runner, temp_db):
        runner.invoke(court_app, [
            "case",
            "--number", "90/2025/TLST-DS",
            "--title", "Test List Case",
            "--type", "DAN_SU",
            "--level", "TAND_CAP_HUYEN",
            "--court", "TAND",
            "--plaintiff", "A",
            "--defendant", "B",
        ])
        res = runner.invoke(court_app, ["list", "cases"])
        assert res.exit_code == 0
        assert "Court Records" in res.output


    def test_cli_list_json(self, runner, temp_db):
        res = runner.invoke(court_app, ["list", "cases", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["category"] == "cases"

    def test_cli_status(self, runner, temp_db):
        res = runner.invoke(court_app, ["status"])
        assert res.exit_code == 0
        assert "OPERATIONS STATUS" in res.output

    def test_cli_status_json(self, runner, temp_db):
        res = runner.invoke(court_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True


class TestCourtCoreMCP:
    def test_core_mcp_handlers(self, temp_db):
        server = MekongMcpServer(name="test-court-mcp")

        # Officer
        res_raw = server._handle_court_officer(
            code="TP-MCP-01",
            name="Thẩm phán MCP",
            role="THAM_PHAN_CHINH",
            level="TAND_CAP_TINH",
            court="TAND Hà Nội",
            decision="QD-MCP",
        )
        res = json.loads(res_raw)
        assert res["success"] is True

        # Case
        res_case_raw = server._handle_court_case(
            number="50/2025/TLST-DS",
            title="MCP Case",
            type="DAN_SU",
            level="TAND_CAP_HUYEN",
            court="TAND Ba Đình",
            plaintiff="A",
            defendant="B",
        )
        res_case = json.loads(res_case_raw)
        assert res_case["success"] is True

        # Hearing
        res_hearing_raw = server._handle_court_hearing(
            code="PT-MCP-01",
            case="50/2025/TLST-DS",
            date="2025-06-01T08:00:00",
        )
        res_hearing = json.loads(res_hearing_raw)
        assert res_hearing["success"] is True

        # Judgment
        res_judgment_raw = server._handle_court_judgment(
            number="25/2025/DS-ST",
            case="50/2025/TLST-DS",
            type="BAN_AN_SO_THAM",
            verdict="Tuyên chấp nhận",
            remedy="Bồi thường 100tr",
        )
        res_judgment = json.loads(res_judgment_raw)
        assert res_judgment["success"] is True

        # Filing
        res_filing_raw = server._handle_court_filing(
            code="EC-MCP-01",
            name="Submitter MCP",
            id_card="001234567890",
            title="Filing MCP",
            type="DON_KHOI_KIEN",
        )
        res_filing = json.loads(res_filing_raw)
        assert res_filing["success"] is True

        # List
        res_list_raw = server._handle_court_list(category="cases")
        res_list = json.loads(res_list_raw)
        assert res_list["success"] is True

        # Status
        res_status_raw = server._handle_court_status()
        res_status = json.loads(res_status_raw)
        assert res_status["success"] is True

    def test_core_mcp_aliases(self):
        server = MekongMcpServer(name="test-court-aliases")
        assert server._handle_mekong_court_officer == server._handle_court_officer
        assert server._handle_mekong_court_case == server._handle_court_case
        assert server._handle_mekong_court_hearing == server._handle_court_hearing
        assert server._handle_mekong_court_judgment == server._handle_court_judgment
        assert server._handle_mekong_court_filing == server._handle_court_filing
        assert server._handle_mekong_court_list == server._handle_court_list
        assert server._handle_mekong_court_status == server._handle_court_status

    def test_core_mcp_error(self, monkeypatch):
        def bad_init(self, db_path=None):
            raise RuntimeError("Database corruption simulated")

        monkeypatch.setattr("src.core.court_engine.CourtEngine._init_db", bad_init)
        server = MekongMcpServer(name="test-court-err")
        res_raw = server._handle_court_status()
        res = json.loads(res_raw)
        assert res["ok"] is False
        assert "Court status error" in res["error"]


class TestCourtScriptsMCP:
    def test_scripts_mcp_core_handlers_registered(self):
        tools = [
            "mekong_court_officer",
            "mekong_court_case",
            "mekong_court_hearing",
            "mekong_court_judgment",
            "mekong_court_filing",
            "mekong_court_list",
            "mekong_court_status",
            "court_officer",
            "court_case",
            "court_hearing",
            "court_judgment",
            "court_filing",
            "court_list",
            "court_status",
        ]
        for t in tools:
            assert t in scripts_mcp.CORE_HANDLERS

    def test_scripts_mcp_core_tools_spec(self):
        names = {spec["name"] for spec in scripts_mcp.CORE_TOOLS_SPEC}
        assert "mekong_court_officer" in names
        assert "mekong_court_case" in names
        assert "mekong_court_hearing" in names
        assert "mekong_court_judgment" in names
        assert "mekong_court_filing" in names
        assert "mekong_court_list" in names
        assert "mekong_court_status" in names

    def test_scripts_mcp_handle_officer(self, temp_db):
        res_raw = scripts_mcp.handle_court_officer({
            "code": "TP-SCRIPTS-01",
            "name": "Judge Scripts",
            "role": "THAM_PHAN",
            "level": "TAND_CAP_HUYEN",
            "court": "TAND Quận 5",
            "decision": "QD-SCRIPTS",
        })
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_case(self, temp_db):
        res_raw = scripts_mcp.handle_court_case({
            "number": "60/2025/TLST-DS",
            "title": "Scripts Case",
            "type": "DAN_SU",
            "level": "TAND_CAP_HUYEN",
            "court": "TAND",
            "plaintiff": "A",
            "defendant": "B",
        })
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_hearing(self, temp_db):
        scripts_mcp.handle_court_case({
            "number": "65/2025/TLST-DS",
            "title": "Scripts Case For Hearing",
            "type": "DAN_SU",
            "level": "TAND_CAP_HUYEN",
            "court": "TAND",
            "plaintiff": "A",
            "defendant": "B",
        })
        res_raw = scripts_mcp.handle_court_hearing({
            "code": "PT-SCRIPTS-01",
            "case": "65/2025/TLST-DS",
            "date": "2025-07-01T08:30:00",
        })
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_judgment(self, temp_db):
        scripts_mcp.handle_court_case({
            "number": "70/2025/TLST-DS",
            "title": "Scripts Case For Judgment",
            "type": "DAN_SU",
            "level": "TAND_CAP_HUYEN",
            "court": "TAND",
            "plaintiff": "A",
            "defendant": "B",
        })
        res_raw = scripts_mcp.handle_court_judgment({
            "number": "35/2025/DS-ST",
            "case": "70/2025/TLST-DS",
            "type": "BAN_AN_SO_THAM",
            "verdict": "Chấp thuận",
            "remedy": "Buộc thi hành",
        })
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_filing(self, temp_db):
        res_raw = scripts_mcp.handle_court_filing({
            "code": "EC-SCRIPTS-01",
            "name": "Applicant",
            "id_card": "001090123456",
            "title": "Online petition",
            "type": "DON_YEU_CAU",
        })
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_list(self, temp_db):
        res_raw = scripts_mcp.handle_court_list({"category": "cases", "limit": 10})
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_handle_status(self, temp_db):
        res_raw = scripts_mcp.handle_court_status({})
        res = json.loads(res_raw)
        assert res["success"] is True

    def test_scripts_mcp_error_handling(self, monkeypatch):
        def bad_init(self, db_path=None):
            raise RuntimeError("Simulated failure")

        monkeypatch.setattr("src.core.court_engine.CourtEngine._init_db", bad_init)
        res_raw = scripts_mcp.handle_court_status({})
        res = json.loads(res_raw)
        assert res["ok"] is False
        assert "Court status error" in res["error"]
