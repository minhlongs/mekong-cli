# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Education, Higher Education, Accreditation & Degree Registry Suite (Phase 82)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.education_engine import (
    ACCREDITATION_STANDARDS,
    DEGREE_TYPES,
    INSTITUTION_TYPES,
    EducationEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestEducationCoreBoundary:
    """Ensure EducationEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/education_engine.py")
        assert source_path.exists(), "education_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestEducationEngine:
    """Test EducationEngine statutory licensing, accreditation, quota calculation & degree verification."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> EducationEngine:
        db_file = tmp_path / "test_education.db"
        return EducationEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Institution Types
        assert "UNIVERSITY" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["UNIVERSITY"]["min_investment_capital_vnd"] == 1_000_000_000_000.0
        assert INSTITUTION_TYPES["UNIVERSITY"]["min_land_area_sqm"] == 50_000.0
        assert "BRANCH_CAMPUS" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["BRANCH_CAMPUS"]["min_investment_capital_vnd"] == 250_000_000_000.0
        assert "K12_SCHOOL" in INSTITUTION_TYPES
        assert INSTITUTION_TYPES["K12_SCHOOL"]["min_investment_capital_vnd"] == 100_000_000_000.0

        # Accreditation Standards
        assert ACCREDITATION_STANDARDS["TOTAL_STANDARDS"] == 25
        assert ACCREDITATION_STANDARDS["TOTAL_CRITERIA"] == 111
        assert ACCREDITATION_STANDARDS["MAX_STUDENT_FACULTY_RATIO"] == 20.0
        assert ACCREDITATION_STANDARDS["MIN_PHD_FACULTY_RATIO_PCT"] == 35.0
        assert ACCREDITATION_STANDARDS["MIN_FLOOR_AREA_PER_STUDENT_SQM"] == 2.8

        # Degree Types
        assert "BACHELOR" in DEGREE_TYPES
        assert "MASTER" in DEGREE_TYPES
        assert "DOCTORATE" in DEGREE_TYPES

    def test_license_institution_success(self, engine: EducationEngine) -> None:
        res = engine.license_institution(
            institution_name="Trường Đại học Công nghệ & Trí tuệ Nhân tạo Mekong",
            institution_type="UNIVERSITY",
            tax_id="0109988771",
            investment_capital_vnd=1_200_000_000_000.0,
            land_area_sqm=60_000.0,
            campus_address="Khu Công nghệ cao, TP. Thủ Đức, TP. Hồ Chí Minh",
        )
        assert res["institution_type"] == "UNIVERSITY"
        assert res["investment_capital_vnd"] == 1_200_000_000_000.0
        assert res["land_area_sqm"] == 60_000.0
        assert res["status"] == "ACTIVE"
        assert "QĐ-TTg" in res["decision_number"]

        insts = engine.list_institutions()
        assert len(insts) == 1
        assert insts[0]["institution_name"] == "Trường Đại học Công nghệ & Trí tuệ Nhân tạo Mekong"

    def test_license_institution_validation_errors(self, engine: EducationEngine) -> None:
        # Invalid type
        with pytest.raises(ValueError, match="Loại hình cơ sở giáo dục không hợp lệ"):
            engine.license_institution("Trường ABC", institution_type="UNKNOWN_TYPE")

        # Insufficient capital
        with pytest.raises(ValueError, match="Vốn đầu tư .* chưa đạt mức tối thiểu quy định"):
            engine.license_institution(
                "Trường Đại học Thiếu Vốn",
                institution_type="UNIVERSITY",
                investment_capital_vnd=500_000_000_000.0,  # Required 1000B
            )

        # Insufficient land
        with pytest.raises(ValueError, match="Diện tích đất xây dựng .* chưa đạt chuẩn tối thiểu"):
            engine.license_institution(
                "Trường Đại học Thiếu Đất",
                institution_type="UNIVERSITY",
                investment_capital_vnd=1_200_000_000_000.0,
                land_area_sqm=30_000.0,  # Required 50,000 sqm
            )

    def test_audit_accreditation_accredited(self, engine: EducationEngine) -> None:
        res = engine.audit_accreditation(
            institution_name="Trường Đại học Quốc tế Mekong",
            total_students=10_000,
            total_faculty=600,  # STR = 16.67 <= 20
            phd_faculty_count=240,  # 40% >= 35%
            floor_area_sqm=35_000.0,  # 3.5 m2/SV >= 2.8
            average_criteria_score=4.8,
            passed_criteria_count=102,  # >= 90
            reporting_year=2026,
        )
        assert res["is_accredited"] is True
        assert res["accreditation_verdict"] == "ACCREDITED"
        assert res["validity_years"] == 5
        assert len(res["violations"]) == 0

        audits = engine.list_accreditations()
        assert len(audits) == 1
        assert audits[0]["is_accredited"] == 1

    def test_audit_accreditation_conditional_and_failed(self, engine: EducationEngine) -> None:
        # Violations -> FAILED
        res_fail = engine.audit_accreditation(
            institution_name="Trường Đại học Quá Tải",
            total_students=20_000,
            total_faculty=500,  # STR = 40 > 20
            phd_faculty_count=100,  # 20% < 35%
            floor_area_sqm=40_000.0,  # 2.0 m2/SV < 2.8
            average_criteria_score=3.5,
            passed_criteria_count=70,
        )
        assert res_fail["is_accredited"] is False
        assert res_fail["accreditation_verdict"] == "FAILED"
        assert res_fail["validity_years"] == 0
        assert len(res_fail["violations"]) == 4

        # Conditional when passed criteria >= 80 but criteria not full
        res_cond = engine.audit_accreditation(
            institution_name="Trường Đại học Chuẩn Bị",
            total_students=5_000,
            total_faculty=300,  # STR = 16.67
            phd_faculty_count=120,  # 40%
            floor_area_sqm=20_000.0,  # 4.0 m2/SV
            average_criteria_score=4.2,
            passed_criteria_count=85,  # between 80 and 89
        )
        assert res_cond["is_accredited"] is False
        assert res_cond["accreditation_verdict"] == "CONDITIONAL"
        assert res_cond["validity_years"] == 2

    def test_calculate_enrollment_quota(self, engine: EducationEngine) -> None:
        res = engine.calculate_enrollment_quota(
            institution_name="Trường Đại học Quốc tế Mekong",
            major_name="Công nghệ Thông tin / Trí tuệ Nhân tạo",
            degree_level="BACHELOR",
            fulltime_faculty_count=40,  # faculty capacity = 40 * 20 = 800
            floor_area_sqm=8400.0,  # floor capacity = 8400 / 2.8 = 3000
            academic_year=2026,
        )
        assert res["capacity_by_faculty"] == 800
        assert res["capacity_by_floor"] == 3000
        # max_annual_quota = min(800, 3000) / 4 = 200
        assert res["max_annual_quota"] == 200

        quotas = engine.list_enrollment_quotas()
        assert len(quotas) == 1
        assert quotas[0]["max_quota"] == 200

    def test_calculate_enrollment_quota_errors(self, engine: EducationEngine) -> None:
        with pytest.raises(ValueError, match="Số lượng giảng viên toàn thời gian"):
            engine.calculate_enrollment_quota("Trường A", fulltime_faculty_count=0)

        with pytest.raises(ValueError, match="Diện tích sàn xây dựng đào tạo"):
            engine.calculate_enrollment_quota("Trường A", fulltime_faculty_count=10, floor_area_sqm=-10.0)

    def test_degree_issuance_and_verification(self, engine: EducationEngine) -> None:
        # Issue degree
        deg = engine.issue_degree_certificate(
            student_name="Nguyễn Văn An",
            student_id="22IT0108",
            citizen_id="079099001234",
            major="Khoa học Máy tính",
            degree_type="BACHELOR",
            graduation_year=2026,
            classification="XUẤT SẮC",
            issuing_institution="Trường Đại học Quốc tế Mekong",
        )
        assert deg["status"] == "VALID"
        assert deg["degree_name_vi"] == "Bằng Cử nhân"
        assert deg["serial_number"].startswith("VB-2026-")
        assert len(deg["digital_hash"]) == 64

        degrees = engine.list_digital_degrees()
        assert len(degrees) == 1
        assert degrees[0]["student_name"] == "Nguyễn Văn An"

        # Verify authentic degree
        v_ok = engine.verify_degree_authenticity(
            serial_number=deg["serial_number"],
            citizen_id="079099001234",
        )
        assert v_ok["is_authentic"] is True
        assert v_ok["verification_status"] == "AUTHENTIC"
        assert v_ok["student_name"] == "Nguyễn Văn An"

        # Verify not found
        v_missing = engine.verify_degree_authenticity(
            serial_number="VB-9999-NONEXISTENT",
            citizen_id="079099001234",
        )
        assert v_missing["is_authentic"] is False
        assert v_missing["verification_status"] == "NOT_FOUND"

        # Verify identity mismatch
        v_mismatch = engine.verify_degree_authenticity(
            serial_number=deg["serial_number"],
            citizen_id="000000000000",
        )
        assert v_mismatch["is_authentic"] is False
        assert v_mismatch["verification_status"] == "IDENTITY_MISMATCH"

    def test_get_status_telemetry(self, engine: EducationEngine) -> None:
        engine.license_institution("Đại học Sài Gòn Mới")
        engine.audit_accreditation("Đại học Sài Gòn Mới", 5000, 300, 150, 20000.0)
        engine.calculate_enrollment_quota("Đại học Sài Gòn Mới", "Kinh tế số", fulltime_faculty_count=20, floor_area_sqm=5000.0)
        engine.issue_degree_certificate("Lê Thị Hoa", "20BA001", "080099112233", "Quản trị Kinh doanh")

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["institutions"]["total_licensed"] == 1
        assert status["accreditation"]["total_audits"] == 1
        assert status["enrollment_quotas"]["total_declared_majors"] == 1
        assert status["degree_registry"]["total_degrees_issued"] == 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestEducationCLI:
    """Test Typer CLI surface under 'mekong education'."""

    @pytest.fixture(autouse=True)
    def setup_app(self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
        db_file = tmp_path / "cli_education.db"
        from src.core.education_engine import EducationEngine

        orig_init = EducationEngine.__init__

        def custom_init(self: EducationEngine, db_path: str | pathlib.Path | None = None) -> None:
            orig_init(self, db_path=db_file)

        monkeypatch.setattr(EducationEngine, "__init__", custom_init)

    def test_education_cli_main_status(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["education"])
        assert result.exit_code == 0
        assert "HỆ THỐNG GIÁO DỤC, KIỂM ĐỊNH ĐẠI HỌC" in result.output

    def test_education_cli_json_mode(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["education", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "institutions" in data

    def test_education_cli_license(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "education",
                "license",
                "Trường Đại học Bách Khoa Mekong",
                "--type",
                "UNIVERSITY",
                "--tax-id",
                "0109988999",
                "--capital",
                "1500000000000",
                "--land",
                "70000",
            ],
        )
        assert result.exit_code == 0
        assert "QUYẾT ĐỊNH THÀNH LẬP" in result.output
        assert "Trường Đại học Bách Khoa Mekong" in result.output

    def test_education_cli_accredit(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "education",
                "accredit",
                "Trường Đại học Quốc tế Mekong",
                "10000",
                "600",
                "250",
                "35000",
                "--score",
                "4.7",
                "--passed",
                "100",
            ],
        )
        assert result.exit_code == 0
        assert "KẾT QUẢ KIỂM ĐỊNH CHẤT LƯỢNG" in result.output
        assert "ACCREDITED" in result.output

    def test_education_cli_quota(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "education",
                "quota",
                "Trường Đại học Quốc tế Mekong",
                "Kỹ thuật Dữ liệu & Trí tuệ Nhân tạo",
                "--faculty",
                "35",
                "--floor",
                "7000",
                "--year",
                "2026",
            ],
        )
        assert result.exit_code == 0
        assert "CHỈ TIÊU TUYỂN SINH HÀNG NĂM" in result.output
        assert "Kỹ thuật Dữ liệu & Trí tuệ Nhân tạo" in result.output

    def test_education_cli_degree_and_verify(self) -> None:
        app = build_app()
        # Issue degree
        res_deg = runner.invoke(
            app,
            [
                "education",
                "degree",
                "Trần Văn Bình",
                "22IT0999",
                "079099887766",
                "Trí tuệ Nhân tạo",
                "--json",
            ],
        )
        assert res_deg.exit_code == 0
        deg_data = json.loads(res_deg.output)
        serial = deg_data["serial_number"]

        # Verify degree success
        res_v = runner.invoke(app, ["education", "verify", serial, "079099887766"])
        assert res_v.exit_code == 0
        assert "VĂN BẰNG HỢP PHÁP VÀ ĐƯỢC XÁC THỰC" in res_v.output

        # Verify degree mismatch
        res_fail = runner.invoke(app, ["education", "verify", serial, "000000000000"])
        assert res_fail.exit_code == 0
        assert "CẢNH BÁO: VĂN BẰNG KHÔNG HỢP PHÁP" in res_fail.output

    def test_education_cli_list_and_status(self) -> None:
        app = build_app()
        # List institutions
        res_list = runner.invoke(app, ["education", "list", "institutions"])
        assert res_list.exit_code == 0
        assert "DANH SÁCH CƠ SỞ GIÁO DỤC" in res_list.output

        # List degrees
        res_degrees = runner.invoke(app, ["education", "list", "degrees"])
        assert res_degrees.exit_code == 0
        assert "SỔ CẤP PHÁT VĂN BẰNG" in res_degrees.output

        # Status
        res_status = runner.invoke(app, ["education", "status", "--json"])
        assert res_status.exit_code == 0
        data = json.loads(res_status.output)
        assert data["status"] == "HEALTHY"


# ---------------------------------------------------------------------------
# MCP Server Dual-Engine Parity Tests
# ---------------------------------------------------------------------------


class TestEducationMcpParity:
    """Ensure Education MCP tools function identically across FastMCP and JSON-RPC fallback."""

    @pytest.fixture(autouse=True)
    def setup_mcp_db(self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
        db_file = tmp_path / "mcp_education.db"
        from src.core.education_engine import EducationEngine

        orig_init = EducationEngine.__init__

        def custom_init(self: EducationEngine, db_path: str | pathlib.Path | None = None) -> None:
            orig_init(self, db_path=db_file)

        monkeypatch.setattr(EducationEngine, "__init__", custom_init)

    def test_mcp_scripts_server_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        assert "mekong_education_license" in CORE_HANDLERS
        assert "mekong_education_accredit" in CORE_HANDLERS
        assert "mekong_education_quota" in CORE_HANDLERS
        assert "mekong_education_degree" in CORE_HANDLERS
        assert "mekong_education_verify" in CORE_HANDLERS
        assert "mekong_education_list" in CORE_HANDLERS
        assert "mekong_education_status" in CORE_HANDLERS

        # Test license
        res_lic_str = CORE_HANDLERS["mekong_education_license"]({
            "institution_name": "Đại học Công nghệ Mekong",
            "institution_type": "UNIVERSITY",
            "tax_id": "0109988111",
            "investment_capital_vnd": 1_200_000_000_000.0,
            "land_area_sqm": 60_000.0,
        })
        res_lic = json.loads(res_lic_str)
        assert res_lic["status"] == "ACTIVE"

        # Test degree
        res_deg_str = CORE_HANDLERS["mekong_education_degree"]({
            "student_name": "Hoàng Minh Tuấn",
            "student_id": "22AI001",
            "citizen_id": "079099112233",
            "major": "Trí tuệ Nhân tạo",
        })
        res_deg = json.loads(res_deg_str)
        assert res_deg["status"] == "VALID"
        serial = res_deg["serial_number"]

        # Test verify
        res_ver_str = CORE_HANDLERS["mekong_education_verify"]({
            "serial_number": serial,
            "citizen_id": "079099112233",
        })
        res_ver = json.loads(res_ver_str)
        assert res_ver["is_authentic"] is True

        # Test status
        res_stat_str = CORE_HANDLERS["mekong_education_status"]({})
        res_stat = json.loads(res_stat_str)
        assert res_stat["status"] == "HEALTHY"

    def test_mcp_core_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_education_license")
        assert hasattr(server, "_handle_education_accredit")
        assert hasattr(server, "_handle_education_quota")
        assert hasattr(server, "_handle_education_degree")
        assert hasattr(server, "_handle_education_verify")
        assert hasattr(server, "_handle_education_list")
        assert hasattr(server, "_handle_education_status")

        # Test quota via core handler
        res_quota_str = server._handle_education_quota(
            institution_name="Đại học Mekong",
            major_name="An toàn Thông tin",
            fulltime_faculty_count=30,
            floor_area_sqm=6000.0,
        )
        res_quota = json.loads(res_quota_str)
        assert res_quota["max_annual_quota"] == 150
