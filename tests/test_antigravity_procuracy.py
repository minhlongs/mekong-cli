"""
Tests for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Phase 139).
Compliant with:
- Law on Organization of the People's Procuracies 2014 (Luật Tổ chức Viện kiểm sát nhân dân - Law No. 63/2014/QH13)
- Criminal Procedure Code 2015 (Luật Tố tụng hình sự - Law No. 101/2015/QH13, amended 2021)
- Law on Temporary Detention and Custody 2015
"""

import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.core.procuracy_engine import (
    ProcuracyEngine,
    ProsecutorRank,
    ProcuracyLevel,
    DetentionMeasure,
    ProtestType,
)
from src.cli.commands.procuracy_command import procuracy_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as scripts_mcp


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MEKONG_PROCURACY_DB"] = path
    yield path
    os.environ.pop("MEKONG_PROCURACY_DB", None)
    for p in (path, f"{path}-wal", f"{path}-shm"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def engine(temp_db):
    return ProcuracyEngine(db_path=temp_db)


@pytest.fixture
def runner():
    return CliRunner()


class TestProcuracyEngine:
    def test_register_prosecutor_valid(self, engine):
        res = engine.register_prosecutor(
            badge_number="KSV-2025-001",
            full_name="Nguyễn Văn Kiểm",
            rank="KIEM_SAT_VIEN_CAO_CAP",
            procuracy_level="VKSND_CAP_CAO",
            office_unit="Viện Kiểm sát Thực hành quyền công tố tại Hà Nội",
            appointment_date="2024-05-15",
            status="ACTIVE",
        )
        assert res["success"] is True
        pros = res["prosecutor"]
        assert pros["badge_number"] == "KSV-2025-001"
        assert pros["rank"] == ProsecutorRank.KIEM_SAT_VIEN_CAO_CAP.value
        assert pros["procuracy_level"] == ProcuracyLevel.VKSND_CAP_CAO.value
        assert "Article 74 Law on Organization" in res["statutory_reference"]

    def test_register_prosecutor_missing_fields(self, engine):
        res = engine.register_prosecutor(
            badge_number="",
            full_name="",
            rank="",
            procuracy_level="",
            office_unit="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_prosecutor_invalid_rank(self, engine):
        res = engine.register_prosecutor(
            badge_number="KSV-002",
            full_name="Trần Văn A",
            rank="INVALID_RANK",
            procuracy_level="VKSND_CAP_HUYEN",
            office_unit="VKSND Huyện Gia Lâm",
        )
        assert res["success"] is False
        assert "Invalid prosecutor rank" in res["error"]

    def test_register_prosecutor_invalid_level(self, engine):
        res = engine.register_prosecutor(
            badge_number="KSV-003",
            full_name="Lê Văn B",
            rank="KIEM_SAT_VIEN_SO_CAP",
            procuracy_level="INVALID_LEVEL",
            office_unit="VKSND Quận",
        )
        assert res["success"] is False
        assert "Invalid procuracy level" in res["error"]

    def test_register_prosecutor_invalid_status(self, engine):
        res = engine.register_prosecutor(
            badge_number="KSV-004",
            full_name="Phạm Thị C",
            rank="KIEM_SAT_VIEN_TRUNG_CAP",
            procuracy_level="VKSND_CAP_TINH",
            office_unit="VKSND Tỉnh Quảng Ninh",
            status="UNKNOWN_STATUS",
        )
        assert res["success"] is False
        assert "Invalid status" in res["error"]

    def test_register_prosecutor_conflict_update(self, engine):
        engine.register_prosecutor(
            badge_number="KSV-2025-005",
            full_name="Hoàng Văn D",
            rank="KIEM_SAT_VIEN_SO_CAP",
            procuracy_level="VKSND_CAP_HUYEN",
            office_unit="VKSND Huyện A",
            status="ACTIVE",
        )
        res = engine.register_prosecutor(
            badge_number="KSV-2025-005",
            full_name="Hoàng Văn D",
            rank="KIEM_SAT_VIEN_TRUNG_CAP",
            procuracy_level="VKSND_CAP_TINH",
            office_unit="VKSND Tỉnh B",
            status="TRANSFERRED",
        )
        assert res["success"] is True
        assert res["prosecutor"]["rank"] == "KIEM_SAT_VIEN_TRUNG_CAP"
        assert res["prosecutor"]["status"] == "TRANSFERRED"

    def test_issue_indictment_valid(self, engine):
        res = engine.issue_indictment(
            indictment_number="15/CT-VKSTC-V1",
            case_name="Vụ án buôn lậu và trốn thuế xuyên quốc gia",
            accused_name="Trần Văn Tội",
            penal_code_article="Điều 188 & 200 BLHS 2015",
            prosecutor_badge="KSV-2025-001",
            trial_court="TAND Thành phố Hà Nội",
            issuing_date="2025-03-10",
            status="ISSUED",
        )
        assert res["success"] is True
        ind = res["indictment"]
        assert ind["indictment_number"] == "15/CT-VKSTC-V1"
        assert ind["accused_name"] == "Trần Văn Tội"
        assert ind["status"] == "ISSUED"
        assert "Article 243 Criminal Procedure Code" in res["statutory_reference"]

    def test_issue_indictment_missing_fields(self, engine):
        res = engine.issue_indictment(
            indictment_number="",
            case_name="",
            accused_name="",
            penal_code_article="",
            prosecutor_badge="",
            trial_court="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_issue_indictment_invalid_status(self, engine):
        res = engine.issue_indictment(
            indictment_number="01/CT-TEST",
            case_name="Test Case",
            accused_name="Accused",
            penal_code_article="Điều 1",
            prosecutor_badge="KSV-001",
            trial_court="TAND",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid status" in res["error"]

    def test_issue_indictment_conflict_update(self, engine):
        engine.issue_indictment(
            indictment_number="20/CT-VKSTC",
            case_name="Vụ án tham nhũng tài sản",
            accused_name="Ngô Văn G",
            penal_code_article="Điều 353 BLHS",
            prosecutor_badge="KSV-001",
            trial_court="TAND Tối cao",
            status="ISSUED",
        )
        res = engine.issue_indictment(
            indictment_number="20/CT-VKSTC",
            case_name="Vụ án tham nhũng tài sản",
            accused_name="Ngô Văn G",
            penal_code_article="Điều 353 BLHS",
            prosecutor_badge="KSV-001",
            trial_court="TAND Tối cao",
            status="CONVICTED",
        )
        assert res["success"] is True
        assert res["indictment"]["status"] == "CONVICTED"

    def test_record_detention_supervision_valid(self, engine):
        res = engine.record_detention_supervision(
            supervision_code="DET-2025-001",
            detention_facility="Trại tạm giam T16 - Bộ Công an",
            detainee_name="Nguyễn Văn Giam",
            measure_type="TAM_GIAM",
            custody_start_date="2025-01-01",
            custody_end_date="2025-04-01",
            inspector_badge="KSV-2025-001",
            compliance_status="COMPLIANT",
            inspection_date="2025-03-01",
            notes="Cơ sở thực hiện nghiêm ngặt chế độ ăn, ở, y tế và quyền gặp luật sư của người bị tạm giam.",
        )
        assert res["success"] is True
        det = res["detention_supervision"]
        assert det["supervision_code"] == "DET-2025-001"
        assert det["measure_type"] == DetentionMeasure.TAM_GIAM.value
        assert det["compliance_status"] == "COMPLIANT"
        assert "Articles 22-26" in res["statutory_reference"]

    def test_record_detention_supervision_missing_fields(self, engine):
        res = engine.record_detention_supervision(
            supervision_code="",
            detention_facility="",
            detainee_name="",
            measure_type="",
            custody_start_date="",
            custody_end_date="",
            inspector_badge="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_record_detention_supervision_invalid_measure(self, engine):
        res = engine.record_detention_supervision(
            supervision_code="DET-002",
            detention_facility="Facility",
            detainee_name="Detainee",
            measure_type="INVALID_MEASURE",
            custody_start_date="2025-01-01",
            custody_end_date="2025-01-03",
            inspector_badge="KSV-001",
        )
        assert res["success"] is False
        assert "Invalid detention measure" in res["error"]

    def test_record_detention_supervision_invalid_status(self, engine):
        res = engine.record_detention_supervision(
            supervision_code="DET-003",
            detention_facility="Facility",
            detainee_name="Detainee",
            measure_type="TAM_GIU",
            custody_start_date="2025-01-01",
            custody_end_date="2025-01-03",
            inspector_badge="KSV-001",
            compliance_status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid compliance status" in res["error"]

    def test_record_detention_supervision_conflict_update(self, engine):
        engine.record_detention_supervision(
            supervision_code="DET-2025-004",
            detention_facility="Nhà tạm giữ Công an Huyện X",
            detainee_name="Phạm Văn H",
            measure_type="TAM_GIU",
            custody_start_date="2025-02-01",
            custody_end_date="2025-02-04",
            inspector_badge="KSV-001",
            compliance_status="COMPLIANT",
        )
        res = engine.record_detention_supervision(
            supervision_code="DET-2025-004",
            detention_facility="Nhà tạm giữ Công an Huyện X",
            detainee_name="Phạm Văn H",
            measure_type="TAM_GIU",
            custody_start_date="2025-02-01",
            custody_end_date="2025-02-04",
            inspector_badge="KSV-001",
            compliance_status="OVERDUE_RELEASE_ORDERED",
            notes="Hết hạn tạm giữ nhưng chưa có lệnh gia hạn; KSV đã ban hành quyết định trả tự do ngay.",
        )
        assert res["success"] is True
        assert res["detention_supervision"]["compliance_status"] == "OVERDUE_RELEASE_ORDERED"

    def test_file_judicial_protest_valid(self, engine):
        res = engine.file_judicial_protest(
            protest_code="PRT-2025-001",
            judgment_number="45/2025/HS-ST",
            court_issued="TAND Quận 1, TP.HCM",
            protest_type="PHUC_THAM",
            legal_ground="Bản án sơ thẩm áp dụng sai tình tiết tăng nặng định khung tại khoản 2 Điều 174 BLHS.",
            prosecutor_badge="KSV-2025-001",
            filing_date="2025-03-12",
            hearing_status="PENDING",
        )
        assert res["success"] is True
        prot = res["judicial_protest"]
        assert prot["protest_code"] == "PRT-2025-001"
        assert prot["protest_type"] == ProtestType.PHUC_THAM.value
        assert prot["hearing_status"] == "PENDING"
        assert "Articles 27-31" in res["statutory_reference"]

    def test_file_judicial_protest_missing_fields(self, engine):
        res = engine.file_judicial_protest(
            protest_code="",
            judgment_number="",
            court_issued="",
            protest_type="",
            legal_ground="",
            prosecutor_badge="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_file_judicial_protest_invalid_type(self, engine):
        res = engine.file_judicial_protest(
            protest_code="PRT-002",
            judgment_number="12/2025/DS-ST",
            court_issued="TAND Huyện",
            protest_type="INVALID_TYPE",
            legal_ground="Ground",
            prosecutor_badge="KSV-001",
        )
        assert res["success"] is False
        assert "Invalid protest type" in res["error"]

    def test_file_judicial_protest_invalid_status(self, engine):
        res = engine.file_judicial_protest(
            protest_code="PRT-003",
            judgment_number="12/2025/DS-ST",
            court_issued="TAND Huyện",
            protest_type="GIAM_DOC_THAM",
            legal_ground="Ground",
            prosecutor_badge="KSV-001",
            hearing_status="UNKNOWN_STATUS",
        )
        assert res["success"] is False
        assert "Invalid hearing status" in res["error"]

    def test_file_judicial_protest_conflict_update(self, engine):
        engine.file_judicial_protest(
            protest_code="PRT-2025-004",
            judgment_number="88/2024/HC-ST",
            court_issued="TAND Tỉnh Bình Dương",
            protest_type="PHUC_THAM",
            legal_ground="Vi phạm nghiêm trọng thủ tục tố tụng hành chính",
            prosecutor_badge="KSV-001",
            hearing_status="PENDING",
        )
        res = engine.file_judicial_protest(
            protest_code="PRT-2025-004",
            judgment_number="88/2024/HC-ST",
            court_issued="TAND Tỉnh Bình Dương",
            protest_type="PHUC_THAM",
            legal_ground="Vi phạm nghiêm trọng thủ tục tố tụng hành chính",
            prosecutor_badge="KSV-001",
            hearing_status="ACCEPTED",
        )
        assert res["success"] is True
        assert res["judicial_protest"]["hearing_status"] == "ACCEPTED"

    def test_list_records_valid_categories(self, engine):
        engine.register_prosecutor("KSV-1", "Pros 1", "KIEM_SAT_VIEN_SO_CAP", "VKSND_CAP_HUYEN", "Unit 1")
        engine.issue_indictment("IND-1", "Case 1", "Accused 1", "Dieu 123", "KSV-1", "Court 1")
        engine.record_detention_supervision("DET-1", "Facility 1", "Detainee 1", "TAM_GIU", "2025-01-01", "2025-01-03", "KSV-1")
        engine.file_judicial_protest("PRT-1", "J-1", "Court 1", "PHUC_THAM", "Ground 1", "KSV-1")

        for cat in ("prosecutors", "indictments", "detentions", "protests"):
            res = engine.list_records(cat)
            assert res["success"] is True
            assert res["count"] >= 1
            assert len(res["records"]) >= 1

    def test_list_records_invalid_category(self, engine):
        res = engine.list_records("invalid_cat")
        assert res["success"] is False
        assert "Invalid category" in res["error"]

    def test_telemetry_status_empty(self, engine):
        status = engine.get_telemetry_status()
        assert status["success"] is True
        t = status["telemetry"]
        assert t["prosecutors"]["total"] == 0
        assert t["criminal_indictments"]["total_indictments"] == 0
        assert t["detention_supervisions"]["total_inspections"] == 0
        assert t["judicial_protests"]["total_protests"] == 0

    def test_telemetry_status_populated(self, engine):
        engine.register_prosecutor("KSV-1", "Pros 1", "KIEM_SAT_VIEN_SO_CAP", "VKSND_CAP_HUYEN", "Unit 1", status="ACTIVE")
        engine.register_prosecutor("KSV-2", "Pros 2", "KIEM_SAT_VIEN_CAO_CAP", "VKSND_CAP_CAO", "Unit 2", status="RETIRED")
        engine.issue_indictment("IND-1", "Case 1", "Accused 1", "Dieu 123", "KSV-1", "Court 1", status="ISSUED")
        engine.issue_indictment("IND-2", "Case 2", "Accused 2", "Dieu 134", "KSV-1", "Court 1", status="CONVICTED")
        engine.record_detention_supervision("DET-1", "Fac 1", "Det 1", "TAM_GIU", "2025-01-01", "2025-01-03", "KSV-1", compliance_status="COMPLIANT")
        engine.record_detention_supervision("DET-2", "Fac 2", "Det 2", "TAM_GIAM", "2025-01-01", "2025-03-01", "KSV-1", compliance_status="OVERDUE_RELEASE_ORDERED")
        engine.file_judicial_protest("PRT-1", "J-1", "Court 1", "PHUC_THAM", "Ground 1", "KSV-1", hearing_status="PENDING")
        engine.file_judicial_protest("PRT-2", "J-2", "Court 2", "GIAM_DOC_THAM", "Ground 2", "KSV-1", hearing_status="ACCEPTED")

        status = engine.get_telemetry_status()
        assert status["success"] is True
        t = status["telemetry"]
        assert t["prosecutors"]["total"] == 2
        assert t["prosecutors"]["active"] == 1
        assert t["criminal_indictments"]["total_indictments"] == 2
        assert t["criminal_indictments"]["pending_trial"] == 1
        assert t["criminal_indictments"]["convicted"] == 1
        assert t["detention_supervisions"]["total_inspections"] == 2
        assert t["detention_supervisions"]["compliant"] == 1
        assert t["detention_supervisions"]["overdue_releases_ordered"] == 1
        assert t["judicial_protests"]["total_protests"] == 2
        assert t["judicial_protests"]["pending_hearing"] == 1
        assert t["judicial_protests"]["protests_accepted"] == 1


class TestProcuracyCLI:
    def test_cli_help(self, runner):
        res = runner.invoke(procuracy_app, ["--help"])
        assert res.exit_code == 0
        assert "Vietnamese People's Procuracy" in res.output

    def test_cli_status_dashboard(self, runner, temp_db):
        res = runner.invoke(procuracy_app, ["status"])
        assert res.exit_code == 0
        assert "People's Procuracy Telemetry" in res.output

    def test_cli_status_json(self, runner, temp_db):
        res = runner.invoke(procuracy_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert "telemetry" in data

    def test_cli_prosecutor_success_and_json(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "prosecutor",
            "--badge", "KSV-001",
            "--name", "Nguyễn Văn K",
            "--rank", "KIEM_SAT_VIEN_SO_CAP",
            "--level", "VKSND_CAP_HUYEN",
            "--office", "VKSND Huyện M",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["prosecutor"]["badge_number"] == "KSV-001"

    def test_cli_prosecutor_validation_failure(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "prosecutor",
            "--badge", "KSV-002",
            "--name", "Trần Văn L",
            "--rank", "INVALID_RANK",
            "--level", "VKSND_CAP_HUYEN",
            "--office", "VKSND",
        ])
        assert res.exit_code == 1
        assert "Failed to register prosecutor" in res.output

    def test_cli_indictment_success_and_json(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "indictment",
            "--number", "10/CT-VKSTC",
            "--case", "Vụ án buôn lậu xăng dầu",
            "--accused", "Trần Văn Buôn",
            "--article", "Điều 188 BLHS",
            "--prosecutor", "KSV-001",
            "--court", "TAND Tỉnh Đồng Nai",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["indictment"]["indictment_number"] == "10/CT-VKSTC"

    def test_cli_indictment_validation_failure(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "indictment",
            "--number", "11/CT-TEST",
            "--case", "Case",
            "--accused", "Accused",
            "--article", "Dieu 1",
            "--prosecutor", "KSV-001",
            "--court", "Court",
            "--status", "INVALID_STATUS",
        ])
        assert res.exit_code == 1
        assert "Failed to issue indictment" in res.output

    def test_cli_detention_success_and_json(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "detention",
            "--code", "DET-001",
            "--facility", "Trại tạm giam Chí Hòa",
            "--detainee", "Lê Văn Tạm",
            "--measure", "TAM_GIAM",
            "--start", "2025-01-01",
            "--end", "2025-04-01",
            "--inspector", "KSV-001",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["detention_supervision"]["supervision_code"] == "DET-001"

    def test_cli_detention_validation_failure(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "detention",
            "--code", "DET-002",
            "--facility", "Facility",
            "--detainee", "Detainee",
            "--measure", "INVALID_MEASURE",
            "--start", "2025-01-01",
            "--end", "2025-01-03",
            "--inspector", "KSV-001",
        ])
        assert res.exit_code == 1
        assert "Failed to record detention supervision" in res.output

    def test_cli_protest_success_and_json(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "protest",
            "--code", "PRT-001",
            "--judgment", "20/2025/HS-ST",
            "--court", "TAND Quận Hải Châu",
            "--type", "PHUC_THAM",
            "--ground", "Tòa án bỏ lọt tội phạm và người phạm tội đồng phạm.",
            "--prosecutor", "KSV-001",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["judicial_protest"]["protest_code"] == "PRT-001"

    def test_cli_protest_validation_failure(self, runner, temp_db):
        res = runner.invoke(procuracy_app, [
            "protest",
            "--code", "PRT-002",
            "--judgment", "21/2025/HS-ST",
            "--court", "TAND",
            "--type", "INVALID_TYPE",
            "--ground", "Ground",
            "--prosecutor", "KSV-001",
        ])
        assert res.exit_code == 1
        assert "Failed to file judicial protest" in res.output

    def test_cli_list_records(self, runner, temp_db):
        # Insert records first
        runner.invoke(procuracy_app, [
            "prosecutor",
            "--badge", "KSV-100",
            "--name", "Phan Văn P",
            "--rank", "KIEM_SAT_VIEN_TRUNG_CAP",
            "--level", "VKSND_CAP_TINH",
            "--office", "Vụ Kiểm sát giải quyết án dân sự",
        ])
        runner.invoke(procuracy_app, [
            "indictment",
            "--number", "50/CT-VKS",
            "--case", "Vụ án sản xuất hàng giả",
            "--accused", "Vũ Văn Giả",
            "--article", "Điều 192 BLHS",
            "--prosecutor", "KSV-100",
            "--court", "TAND Tỉnh",
        ])
        runner.invoke(procuracy_app, [
            "detention",
            "--code", "DET-100",
            "--facility", "Trại tạm giam Công an Tỉnh",
            "--detainee", "Nguyễn Văn Nhốt",
            "--measure", "TAM_GIAM",
            "--start", "2025-01-10",
            "--end", "2025-04-10",
            "--inspector", "KSV-100",
        ])
        runner.invoke(procuracy_app, [
            "protest",
            "--code", "PRT-100",
            "--judgment", "99/2024/DS-ST",
            "--court", "TAND Thành phố",
            "--type", "GIAM_DOC_THAM",
            "--ground", "Có sai lầm nghiêm trọng trong việc áp dụng thời hiệu khởi kiện.",
            "--prosecutor", "KSV-100",
        ])

        for cat in ("prosecutors", "indictments", "detentions", "protests"):
            res_txt = runner.invoke(procuracy_app, ["list", "--category", cat])
            assert res_txt.exit_code == 0
            assert "People's Procuracy Records" in res_txt.output

            res_json = runner.invoke(procuracy_app, ["list", "--category", cat, "--json"])
            assert res_json.exit_code == 0
            data = json.loads(res_json.output)
            assert data["success"] is True
            assert data["count"] >= 1


class TestProcuracyMCP:
    def test_core_mcp_server_handlers(self, temp_db):
        server = MekongMcpServer()

        # 1. Prosecutor
        res_pros = json.loads(server._handle_procuracy_prosecutor(
            badge="KSV-MCP-01",
            name="Kiểm sát viên MCP",
            rank="KIEM_SAT_VIEN_CAO_CAP",
            level="VKSND_CAP_CAO",
            office="Vụ 1 - VKSND Tối cao",
        ))
        assert res_pros["success"] is True

        # 2. Indictment
        res_ind = json.loads(server._handle_procuracy_indictment(
            number="01/CT-MCP",
            case="Vụ án tham ô tài sản công nghệ",
            accused="Hacker Đen",
            article="Điều 353 BLHS",
            prosecutor="KSV-MCP-01",
            court="TAND Hà Nội",
        ))
        assert res_ind["success"] is True

        # 3. Detention
        res_det = json.loads(server._handle_procuracy_detention(
            code="DET-MCP-01",
            facility="Trại T16",
            detainee="Hacker Đen",
            measure="TAM_GIAM",
            start="2025-01-01",
            end="2025-04-01",
            inspector="KSV-MCP-01",
        ))
        assert res_det["success"] is True

        # 4. Protest
        res_prot = json.loads(server._handle_procuracy_protest(
            code="PRT-MCP-01",
            judgment="01/2025/HS-ST",
            court="TAND Quận",
            type="PHUC_THAM",
            ground="Áp dụng sai khung hình phạt",
            prosecutor="KSV-MCP-01",
        ))
        assert res_prot["success"] is True

        # 5. List
        res_list = json.loads(server._handle_procuracy_list(category="prosecutors", limit=10))
        assert res_list["success"] is True
        assert res_list["count"] >= 1

        # 6. Status
        res_status = json.loads(server._handle_procuracy_status())
        assert res_status["success"] is True
        assert res_status["telemetry"]["prosecutors"]["total"] >= 1

    def test_scripts_mcp_server_handlers_and_aliases(self, temp_db):
        tools = [
            "mekong_procuracy_prosecutor",
            "mekong_procuracy_indictment",
            "mekong_procuracy_detention",
            "mekong_procuracy_protest",
            "mekong_procuracy_list",
            "mekong_procuracy_status",
            "procuracy_prosecutor",
            "procuracy_indictment",
            "procuracy_detention",
            "procuracy_protest",
            "procuracy_list",
            "procuracy_status",
        ]
        for t in tools:
            assert t in scripts_mcp.CORE_HANDLERS, f"Missing handler for {t}"

        # 1. Prosecutor
        res_pros = json.loads(scripts_mcp.CORE_HANDLERS["mekong_procuracy_prosecutor"]({
            "badge": "KSV-SCRIPTS-01",
            "name": "Kiểm sát viên Scripts",
            "rank": "KIEM_SAT_VIEN_SO_CAP",
            "level": "VKSND_CAP_HUYEN",
            "office": "VKSND Huyện Y",
        }))
        assert res_pros["success"] is True

        # 2. Indictment
        res_ind = json.loads(scripts_mcp.CORE_HANDLERS["mekong_procuracy_indictment"]({
            "number": "02/CT-SCRIPTS",
            "case": "Vụ án trộm cắp tài sản",
            "accused": "Nguyễn Văn Trộm",
            "article": "Điều 173 BLHS",
            "prosecutor": "KSV-SCRIPTS-01",
            "court": "TAND Huyện Y",
        }))
        assert res_ind["success"] is True

        # 3. Detention
        res_det = json.loads(scripts_mcp.CORE_HANDLERS["mekong_procuracy_detention"]({
            "code": "DET-SCRIPTS-01",
            "facility": "Nhà tạm giữ Huyện Y",
            "detainee": "Nguyễn Văn Trộm",
            "measure": "TAM_GIU",
            "start": "2025-02-01",
            "end": "2025-02-04",
            "inspector": "KSV-SCRIPTS-01",
        }))
        assert res_det["success"] is True

        # 4. Protest
        res_prot = json.loads(scripts_mcp.CORE_HANDLERS["mekong_procuracy_protest"]({
            "code": "PRT-SCRIPTS-01",
            "judgment": "05/2025/HS-ST",
            "court": "TAND Huyện Y",
            "type": "PHUC_THAM",
            "ground": "Bản án bỏ sót tang vật vụ án",
            "prosecutor": "KSV-SCRIPTS-01",
        }))
        assert res_prot["success"] is True

        # 5. List
        res_list = json.loads(scripts_mcp.CORE_HANDLERS["procuracy_list"]({
            "category": "indictments",
        }))
        assert res_list["success"] is True
        assert res_list["count"] >= 1

        # 6. Status
        res_status = json.loads(scripts_mcp.CORE_HANDLERS["procuracy_status"]({}))
        assert res_status["success"] is True
        assert res_status["telemetry"]["prosecutors"]["total"] >= 1
