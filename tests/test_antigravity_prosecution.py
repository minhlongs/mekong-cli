"""
Unit and integration tests for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
Governed by:
- Law on Organization of the People's Procuracies 2014 (Law No. 63/2014/QH13)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13)
- Law on Execution of Criminal Judgments 2019 (Law No. 41/2019/QH14)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.prosecution_command import app as prosecution_app
from src.core.prosecution_engine import (
    VALID_CRIME_GROUPS,
    VALID_INSPECTION_COMPLIANCE,
    VALID_PROCEDURAL_STAGES,
    VALID_PROCURACY_LEVELS,
    VALID_PROCURATOR_RANKS,
    VALID_PROCURATOR_STATUS,
    VALID_PROSECUTION_DECISIONS,
    VALID_REPORT_SOURCES,
    VALID_REPORT_STATUS,
    ProsecutionEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_PROSECUTION_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestProsecutionEngine:
    def test_register_procurator_valid(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        res = engine.register_procurator(
            procurator_id="KSV-VKS-001",
            full_name="Nguyễn Văn Minh",
            rank="KIEM_SAT_VIEN_TRUNG_CAP",
            procuracy_level="VKSND_CAP_TINH",
            unit_name="Phòng 1 Viện KSND TP.HCM",
            appointment_decision="QD-123/QD-CTN",
            status="ACTIVE_DUTY",
        )
        assert res["procurator_id"] == "KSV-VKS-001"
        assert res["full_name"] == "Nguyễn Văn Minh"
        assert res["rank"] == "KIEM_SAT_VIEN_TRUNG_CAP"
        assert res["procuracy_level"] == "VKSND_CAP_TINH"
        assert res["status"] == "ACTIVE_DUTY"

    def test_register_procurator_missing_fields(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.register_procurator(
                procurator_id="",
                full_name="Nguyễn Văn Minh",
                rank="KIEM_SAT_VIEN_SO_CAP",
                procuracy_level="VKSND_CAP_HUYEN",
                unit_name="Viện KSND",
                appointment_decision="QD-1",
            )

    def test_register_procurator_invalid_rank(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid rank"):
            engine.register_procurator(
                procurator_id="KSV-001",
                full_name="Test",
                rank="CHIEF_JUDGE",
                procuracy_level="VKSND_CAP_HUYEN",
                unit_name="Viện KSND",
                appointment_decision="QD-1",
            )

    def test_register_procurator_invalid_level(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid procuracy_level"):
            engine.register_procurator(
                procurator_id="KSV-001",
                full_name="Test",
                rank="KIEM_SAT_VIEN_SO_CAP",
                procuracy_level="SUPREME_COURT",
                unit_name="Viện KSND",
                appointment_decision="QD-1",
            )

    def test_register_procurator_invalid_status(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_procurator(
                procurator_id="KSV-001",
                full_name="Test",
                rank="KIEM_SAT_VIEN_SO_CAP",
                procuracy_level="VKSND_CAP_HUYEN",
                unit_name="Viện KSND",
                appointment_decision="QD-1",
                status="UNKNOWN_STATUS",
            )

    def test_register_procurator_duplicate(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        engine.register_procurator(
            procurator_id="KSV-001",
            full_name="Test",
            rank="KIEM_SAT_VIEN_SO_CAP",
            procuracy_level="VKSND_CAP_HUYEN",
            unit_name="Viện KSND",
            appointment_decision="QD-1",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_procurator(
                procurator_id="KSV-001",
                full_name="Test Duplicate",
                rank="KIEM_SAT_VIEN_SO_CAP",
                procuracy_level="VKSND_CAP_HUYEN",
                unit_name="Viện KSND",
                appointment_decision="QD-2",
            )

    def test_receive_crime_report_valid(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        res = engine.receive_crime_report(
            report_id="TNB-2024-001",
            source_type="TO_GIAC_TOI_PHAM",
            crime_summary="Tố giác hành vi lừa đảo chiếm đoạt tài sản qua mạng xã hội",
            alleged_crime_group="SO_HUU_TAI_SAN",
            receiving_procuracy="Viện KSND Quận 1",
            assigned_procurator_id="KSV-VKS-001",
            supervision_status="INVESTIGATING",
            resolution_deadline_days=20,
        )
        assert res["report_id"] == "TNB-2024-001"
        assert res["source_type"] == "TO_GIAC_TOI_PHAM"
        assert res["alleged_crime_group"] == "SO_HUU_TAI_SAN"
        assert res["supervision_status"] == "INVESTIGATING"
        assert res["resolution_deadline"] is not None

    def test_receive_crime_report_missing_fields(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.receive_crime_report(
                report_id="",
                source_type="TO_GIAC_TOI_PHAM",
                crime_summary="Tố giác tội phạm",
                alleged_crime_group="SO_HUU_TAI_SAN",
                receiving_procuracy="Viện KSND",
                assigned_procurator_id="KSV-001",
            )

    def test_receive_crime_report_invalid_source(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid source_type"):
            engine.receive_crime_report(
                report_id="TNB-001",
                source_type="ANONYMOUS_RUMOR",
                crime_summary="Tin đồn",
                alleged_crime_group="SO_HUU_TAI_SAN",
                receiving_procuracy="Viện KSND",
                assigned_procurator_id="KSV-001",
            )

    def test_receive_crime_report_invalid_group(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid alleged_crime_group"):
            engine.receive_crime_report(
                report_id="TNB-001",
                source_type="TO_GIAC_TOI_PHAM",
                crime_summary="Tội phạm",
                alleged_crime_group="UNKNOWN_GROUP",
                receiving_procuracy="Viện KSND",
                assigned_procurator_id="KSV-001",
            )

    def test_receive_crime_report_invalid_status(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid supervision_status"):
            engine.receive_crime_report(
                report_id="TNB-001",
                source_type="TO_GIAC_TOI_PHAM",
                crime_summary="Tội phạm",
                alleged_crime_group="SO_HUU_TAI_SAN",
                receiving_procuracy="Viện KSND",
                assigned_procurator_id="KSV-001",
                supervision_status="INVALID_STATUS",
            )

    def test_record_case_supervision_valid(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        res = engine.record_case_supervision(
            case_id="AN-HS-2024-001",
            case_name="Vụ án Buôn lậu qua đường hàng không",
            investigative_agency="Cơ quan CSĐT Công an TP.HCM",
            procurator_in_charge="KSV-VKS-001",
            legal_article="Điều 188 BLHS 2015",
            procedural_stage="KHOI_TO_DIEU_TRA",
            arrest_warrants_approved=2,
            detention_orders_approved=2,
            procuracy_demands_count=3,
        )
        assert res["case_id"] == "AN-HS-2024-001"
        assert res["arrest_warrants_approved"] == 2
        assert res["detention_orders_approved"] == 2
        assert res["procuracy_demands_count"] == 3

    def test_record_case_supervision_update(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        engine.record_case_supervision(
            case_id="AN-HS-2024-001",
            case_name="Vụ án Buôn lậu",
            investigative_agency="Cơ quan CSĐT",
            procurator_in_charge="KSV-001",
            legal_article="Điều 188",
            procedural_stage="KHOI_TO_DIEU_TRA",
        )
        updated = engine.record_case_supervision(
            case_id="AN-HS-2024-001",
            case_name="Vụ án Buôn lậu (Truy tố)",
            investigative_agency="Cơ quan CSĐT",
            procurator_in_charge="KSV-001",
            legal_article="Điều 188",
            procedural_stage="TRUY_TO",
            arrest_warrants_approved=3,
        )
        assert updated["procedural_stage"] == "TRUY_TO"
        assert updated["arrest_warrants_approved"] == 3

    def test_record_case_supervision_invalid_stage(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid procedural_stage"):
            engine.record_case_supervision(
                case_id="AN-001",
                case_name="Vụ án",
                investigative_agency="Agency",
                procurator_in_charge="KSV-001",
                legal_article="Điều 188",
                procedural_stage="ARBITRATION",
            )

    def test_issue_indictment_valid(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        res = engine.issue_indictment(
            indictment_id="CT-2024-001",
            case_id="AN-HS-2024-001",
            defendant_name="Trần Văn Quyết",
            charged_offense="Tội Buôn lậu",
            applicable_clause="Khoản 2 Điều 188 BLHS 2015",
            issuing_procuracy="Viện KSND TP.HCM",
            signing_procurator_id="KSV-VKS-001",
            prosecution_decision="PROCEED_TRIAL",
            issue_date="2024-08-15",
        )
        assert res["indictment_id"] == "CT-2024-001"
        assert res["defendant_name"] == "Trần Văn Quyết"
        assert res["charged_offense"] == "Tội Buôn lậu"
        assert res["prosecution_decision"] == "PROCEED_TRIAL"

    def test_issue_indictment_missing_fields(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.issue_indictment(
                indictment_id="",
                case_id="AN-001",
                defendant_name="Bị can",
                charged_offense="Tội danh",
                applicable_clause="Khoản 1",
                issuing_procuracy="VKS",
                signing_procurator_id="KSV-001",
            )

    def test_issue_indictment_invalid_decision(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid prosecution_decision"):
            engine.issue_indictment(
                indictment_id="CT-001",
                case_id="AN-001",
                defendant_name="Bị can",
                charged_offense="Tội danh",
                applicable_clause="Khoản 1",
                issuing_procuracy="VKS",
                signing_procurator_id="KSV-001",
                prosecution_decision="DISMISS_ALL_CHARGES",
            )

    def test_record_custody_inspection_valid(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        res = engine.record_custody_inspection(
            inspection_id="KS-TG-2024-001",
            facility_name="Nhà tạm giữ Công an Quận 1",
            inspecting_procuracy="Viện KSND Quận 1",
            lead_procurator_id="KSV-VKS-001",
            detainees_checked_count=45,
            violations_detected_count=0,
            protest_recommendation_issued=False,
            compliance_status="STANDARD_COMPLIANT",
            inspection_date="2024-08-20",
        )
        assert res["inspection_id"] == "KS-TG-2024-001"
        assert res["detainees_checked_count"] == 45
        assert res["violations_detected_count"] == 0
        assert res["compliance_status"] == "STANDARD_COMPLIANT"

    def test_record_custody_inspection_invalid_compliance(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid compliance_status"):
            engine.record_custody_inspection(
                inspection_id="KS-001",
                facility_name="Nhà tạm giữ",
                inspecting_procuracy="VKS",
                lead_procurator_id="KSV-001",
                compliance_status="UNKNOWN_COMPLIANCE",
            )

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = ProsecutionEngine(db_path=temp_db)
        engine.register_procurator(
            procurator_id="KSV-001",
            full_name="Nguyễn Văn A",
            rank="KIEM_SAT_VIEN_SO_CAP",
            procuracy_level="VKSND_CAP_HUYEN",
            unit_name="VKS",
            appointment_decision="QD-1",
        )
        engine.receive_crime_report(
            report_id="TNB-001",
            source_type="TO_GIAC_TOI_PHAM",
            crime_summary="Trộm cắp",
            alleged_crime_group="SO_HUU_TAI_SAN",
            receiving_procuracy="VKS",
            assigned_procurator_id="KSV-001",
        )
        engine.record_case_supervision(
            case_id="AN-001",
            case_name="Vụ án trộm cắp",
            investigative_agency="CSĐT",
            procurator_in_charge="KSV-001",
            legal_article="Điều 173",
            arrest_warrants_approved=1,
            detention_orders_approved=1,
            procuracy_demands_count=2,
        )
        engine.issue_indictment(
            indictment_id="CT-001",
            case_id="AN-001",
            defendant_name="Bị can A",
            charged_offense="Trộm cắp tài sản",
            applicable_clause="Khoản 1 Điều 173",
            issuing_procuracy="VKS",
            signing_procurator_id="KSV-001",
        )
        engine.record_custody_inspection(
            inspection_id="KS-001",
            facility_name="Nhà tạm giữ",
            inspecting_procuracy="VKS",
            lead_procurator_id="KSV-001",
            detainees_checked_count=20,
            violations_detected_count=0,
        )

        records = engine.list_records("all")
        assert len(records["procurators"]) == 1
        assert len(records["reports"]) == 1
        assert len(records["cases"]) == 1
        assert len(records["indictments"]) == 1
        assert len(records["inspections"]) == 1

        telem = engine.get_telemetry_status()
        assert telem["total_procurators"] == 1
        assert telem["active_duty_procurators"] == 1
        assert telem["total_crime_reports_supervised"] == 1
        assert telem["supervised_criminal_cases"] == 1
        assert telem["approved_arrest_warrants"] == 1
        assert telem["approved_detention_orders"] == 1
        assert telem["total_indictments_issued"] == 1
        assert telem["cases_prosecuted_to_trial"] == 1
        assert telem["total_custody_inspections"] == 1
        assert telem["custody_compliance_rate_percent"] == 100.0


class TestProsecutionCLI:
    def test_cli_default_dashboard(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, [])
        assert result.exit_code == 0
        assert "VIỆN KIỂM SÁT NHÂN DÂN" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_procurators" in data

    def test_cli_procurator_register(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "procurator",
                "--id", "KSV-VKS-002",
                "--name", "Lê Văn Thắng",
                "--rank", "KIEM_SAT_VIEN_TRUNG_CAP",
                "--level", "VKSND_CAP_TINH",
                "--unit", "Phòng 2 Viện KSND TP.HCM",
                "--decision", "QD-99/QD-CTN",
            ],
        )
        assert result.exit_code == 0
        assert "Registered Procurator KSV-VKS-002" in result.output

    def test_cli_procurator_register_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "procurator",
                "--id", "KSV-VKS-003",
                "--name", "Phạm Thị Lan",
                "--unit", "Viện KSND Quận 3",
                "--decision", "QD-101/QD-CTN",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["procurator_id"] == "KSV-VKS-003"
        assert data["full_name"] == "Phạm Thị Lan"

    def test_cli_procurator_register_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "procurator",
                "--id", "KSV-001",
                "--name", "Test",
                "--rank", "INVALID_RANK",
                "--unit", "Unit",
                "--decision", "QD",
            ],
        )
        assert result.exit_code == 1
        assert "Error registering procurator" in result.output

    def test_cli_report_receive(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "report",
                "--id", "TNB-2024-002",
                "--summary", "Tin báo về tội đánh bạc",
                "--group", "TRAT_TU_CONG_CONG",
                "--procuracy", "Viện KSND Quận 1",
                "--procurator", "KSV-001",
            ],
        )
        assert result.exit_code == 0
        assert "Recorded Crime Report TNB-2024-002" in result.output

    def test_cli_report_receive_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "report",
                "--id", "TNB-2024-003",
                "--summary", "Tố giác tội trộm cắp",
                "--group", "SO_HUU_TAI_SAN",
                "--procuracy", "Viện KSND Quận 1",
                "--procurator", "KSV-001",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["report_id"] == "TNB-2024-003"

    def test_cli_case_record(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "case",
                "--id", "AN-2024-002",
                "--name", "Vụ án Cố ý gây thương tích",
                "--agency", "CSĐT Công an Quận 1",
                "--procurator", "KSV-001",
                "--article", "Điều 134 BLHS",
                "--warrants", "1",
                "--detentions", "1",
            ],
        )
        assert result.exit_code == 0
        assert "Updated Criminal Case Supervision AN-2024-002" in result.output

    def test_cli_case_record_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "case",
                "--id", "AN-2024-003",
                "--name", "Vụ án Lừa đảo",
                "--agency", "CSĐT",
                "--procurator", "KSV-001",
                "--article", "Điều 174",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["case_id"] == "AN-2024-003"

    def test_cli_indictment_issue(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "indictment",
                "--id", "CT-2024-002",
                "--case-id", "AN-2024-002",
                "--defendant", "Nguyễn Văn Hùng",
                "--offense", "Tội Cố ý gây thương tích",
                "--clause", "Khoản 1 Điều 134",
                "--procuracy", "Viện KSND Quận 1",
                "--procurator", "KSV-001",
            ],
        )
        assert result.exit_code == 0
        assert "Issued Indictment CT-2024-002" in result.output

    def test_cli_indictment_issue_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "indictment",
                "--id", "CT-2024-003",
                "--case-id", "AN-2024-003",
                "--defendant", "Vũ Minh Trí",
                "--offense", "Tội Lừa đảo",
                "--clause", "Khoản 2 Điều 174",
                "--procuracy", "Viện KSND Quận 1",
                "--procurator", "KSV-001",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["indictment_id"] == "CT-2024-003"

    def test_cli_inspection_record(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "inspection",
                "--id", "KS-2024-002",
                "--facility", "Trại tạm giam Bố Lá",
                "--procuracy", "Viện KSND TP.HCM",
                "--procurator", "KSV-001",
                "--checked", "120",
                "--violations", "0",
            ],
        )
        assert result.exit_code == 0
        assert "Recorded Custody Inspection KS-2024-002" in result.output

    def test_cli_inspection_record_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            prosecution_app,
            [
                "inspection",
                "--id", "KS-2024-003",
                "--facility", "Trại tạm giam Chí Hòa",
                "--procuracy", "Viện KSND TP.HCM",
                "--procurator", "KSV-001",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inspection_id"] == "KS-2024-003"

    def test_cli_list(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, ["list"])
        assert result.exit_code == 0

    def test_cli_list_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "procurators" in data

    def test_cli_status(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, ["status"])
        assert result.exit_code == 0
        assert "People's Procuracy" in result.output

    def test_cli_status_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(prosecution_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_procurators" in data


class TestProsecutionCoreMCP:
    def test_core_mcp_handlers(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Procurator
        raw_proc = server._handle_prosecution_procurator(
            procurator_id="KSV-MCP-01",
            full_name="Ngô Văn Khang",
            rank="KIEM_SAT_VIEN_CAO_CAP",
            procuracy_level="VKSND_CAP_CAO",
            unit_name="Viện Cấp cao 3",
            appointment_decision="QD-55/QD-CTN",
        )
        res_proc = json.loads(raw_proc)
        assert res_proc["procurator_id"] == "KSV-MCP-01"

        # 2. Report
        raw_rep = server._handle_prosecution_report(
            report_id="TNB-MCP-01",
            source_type="KIEN_NGHI_KHOI_TO",
            crime_summary="Kiến nghị khởi tố hành vi vi phạm quy định đất đai",
            alleged_crime_group="KINH_TE_THAM_NHUNG",
            receiving_procuracy="Viện Cấp cao 3",
            assigned_procurator_id="KSV-MCP-01",
        )
        res_rep = json.loads(raw_rep)
        assert res_rep["report_id"] == "TNB-MCP-01"

        # 3. Case
        raw_case = server._handle_prosecution_case(
            case_id="AN-MCP-01",
            case_name="Vụ án Tham ô tài sản",
            investigative_agency="Cơ quan ANĐT",
            procurator_in_charge="KSV-MCP-01",
            legal_article="Điều 353 BLHS",
            arrest_warrants_approved=2,
            detention_orders_approved=2,
        )
        res_case = json.loads(raw_case)
        assert res_case["case_id"] == "AN-MCP-01"

        # 4. Indictment
        raw_ind = server._handle_prosecution_indictment(
            indictment_id="CT-MCP-01",
            case_id="AN-MCP-01",
            defendant_name="Nguyễn Văn T",
            charged_offense="Tội Tham ô tài sản",
            applicable_clause="Khoản 3 Điều 353",
            issuing_procuracy="Viện Cấp cao 3",
            signing_procurator_id="KSV-MCP-01",
        )
        res_ind = json.loads(raw_ind)
        assert res_ind["indictment_id"] == "CT-MCP-01"

        # 5. Inspection
        raw_insp = server._handle_prosecution_inspection(
            inspection_id="KS-MCP-01",
            facility_name="Trại giam T30",
            inspecting_procuracy="Viện Cấp cao 3",
            lead_procurator_id="KSV-MCP-01",
            detainees_checked_count=200,
            violations_detected_count=0,
        )
        res_insp = json.loads(raw_insp)
        assert res_insp["inspection_id"] == "KS-MCP-01"

        # 6. List
        raw_list = server._handle_prosecution_list(category="all", limit=10)
        res_list = json.loads(raw_list)
        assert "procurators" in res_list

        # 7. Status
        raw_stat = server._handle_prosecution_status()
        res_stat = json.loads(raw_stat)
        assert res_stat["total_procurators"] == 1

    def test_core_mcp_aliases(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert server._handle_mekong_prosecution_procurator == server._handle_prosecution_procurator
        assert server._handle_mekong_prosecution_report == server._handle_prosecution_report
        assert server._handle_mekong_prosecution_case == server._handle_prosecution_case
        assert server._handle_mekong_prosecution_indictment == server._handle_prosecution_indictment
        assert server._handle_mekong_prosecution_inspection == server._handle_prosecution_inspection
        assert server._handle_mekong_prosecution_list == server._handle_prosecution_list
        assert server._handle_mekong_prosecution_status == server._handle_prosecution_status

    def test_core_mcp_error(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_prosecution_procurator(
            procurator_id="",
            full_name="Error Test",
        )
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Prosecution procurator error" in res["error"]


class TestProsecutionScriptsMCP:
    def test_scripts_mcp_core_handlers_registered(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected = [
            "mekong_prosecution_procurator",
            "mekong_prosecution_report",
            "mekong_prosecution_case",
            "mekong_prosecution_indictment",
            "mekong_prosecution_inspection",
            "mekong_prosecution_list",
            "mekong_prosecution_status",
            "prosecution_procurator",
            "prosecution_report",
            "prosecution_case",
            "prosecution_indictment",
            "prosecution_inspection",
            "prosecution_list",
            "prosecution_status",
        ]
        for name in expected:
            assert name in CORE_HANDLERS, f"Missing {name} in CORE_HANDLERS"

    def test_scripts_mcp_core_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        expected = [
            "mekong_prosecution_procurator",
            "mekong_prosecution_report",
            "mekong_prosecution_case",
            "mekong_prosecution_indictment",
            "mekong_prosecution_inspection",
            "mekong_prosecution_list",
            "mekong_prosecution_status",
        ]
        for name in expected:
            assert name in names, f"Missing {name} in CORE_TOOLS_SPEC"

    def test_scripts_mcp_handle_procurator(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_procurator

        raw = handle_prosecution_procurator({
            "procurator_id": "KSV-SCRIPTS-01",
            "full_name": "Đặng Thị Hoa",
            "rank": "KIEM_SAT_VIEN_SO_CAP",
            "procuracy_level": "VKSND_CAP_HUYEN",
            "unit_name": "Viện KSND Huyện Nhà Bè",
            "appointment_decision": "QD-77/QD-CTN",
        })
        res = json.loads(raw)
        assert res["procurator_id"] == "KSV-SCRIPTS-01"

    def test_scripts_mcp_handle_report(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_report

        raw = handle_prosecution_report({
            "report_id": "TNB-SCRIPTS-01",
            "source_type": "TO_GIAC_TOI_PHAM",
            "crime_summary": "Tố giác buôn bán hàng cấm",
            "alleged_crime_group": "KINH_TE_THAM_NHUNG",
            "receiving_procuracy": "Viện KSND Huyện Nhà Bè",
            "assigned_procurator_id": "KSV-SCRIPTS-01",
        })
        res = json.loads(raw)
        assert res["report_id"] == "TNB-SCRIPTS-01"

    def test_scripts_mcp_handle_case(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_case

        raw = handle_prosecution_case({
            "case_id": "AN-SCRIPTS-01",
            "case_name": "Vụ án buôn bán hàng cấm",
            "investigative_agency": "Công an Huyện Nhà Bè",
            "procurator_in_charge": "KSV-SCRIPTS-01",
            "legal_article": "Điều 190 BLHS",
        })
        res = json.loads(raw)
        assert res["case_id"] == "AN-SCRIPTS-01"

    def test_scripts_mcp_handle_indictment(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_indictment

        raw = handle_prosecution_indictment({
            "indictment_id": "CT-SCRIPTS-01",
            "case_id": "AN-SCRIPTS-01",
            "defendant_name": "Ngô Văn B",
            "charged_offense": "Buôn bán hàng cấm",
            "applicable_clause": "Khoản 1 Điều 190",
            "issuing_procuracy": "Viện KSND Huyện Nhà Bè",
            "signing_procurator_id": "KSV-SCRIPTS-01",
        })
        res = json.loads(raw)
        assert res["indictment_id"] == "CT-SCRIPTS-01"

    def test_scripts_mcp_handle_inspection(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_inspection

        raw = handle_prosecution_inspection({
            "inspection_id": "KS-SCRIPTS-01",
            "facility_name": "Nhà tạm giữ Công an Huyện",
            "inspecting_procuracy": "Viện KSND Huyện Nhà Bè",
            "lead_procurator_id": "KSV-SCRIPTS-01",
        })
        res = json.loads(raw)
        assert res["inspection_id"] == "KS-SCRIPTS-01"

    def test_scripts_mcp_handle_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_list

        raw = handle_prosecution_list({"category": "all", "limit": 10})
        res = json.loads(raw)
        assert "procurators" in res

    def test_scripts_mcp_handle_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_status

        raw = handle_prosecution_status({})
        res = json.loads(raw)
        assert "total_procurators" in res

    def test_scripts_mcp_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_prosecution_procurator

        raw = handle_prosecution_procurator({"procurator_id": ""})
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Prosecution procurator error" in res["error"]
