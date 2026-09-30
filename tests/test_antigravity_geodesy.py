"""
Test Suite for Vietnamese Geodesy, National Coordinates (VN-2000), Map Sovereignty & Cadastral GIS Suite (Phase 91).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- GeodesyEngine domain logic (Luật Đo đạc và bản đồ 2018, QĐ 83/2000/QĐ-TTg, Thông tư 25/2014, Nghị định 18/2020).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.geodesy_engine import GeodesyEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestGeodesyBoundary:
    """Verifies that geodesy_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "geodesy_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestGeodesyEngine:
    """Tests core domain and regulatory business logic of GeodesyEngine."""

    def test_validate_coordinate_system_hanoi(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.validate_coordinate_system(
            point_id="MOC-HN-001",
            latitude=21.028511,
            longitude=105.854444,
            zone_deg=3,
            province="HÀ NỘI",
        )
        assert res["status"] == "COORDINATE_VALID_VN2000"
        assert res["is_in_vietnam"] is True
        assert res["central_meridian_deg"] == 105.0
        assert res["scale_factor_k0"] == 0.9999
        assert res["x_northing_m"] > 2_000_000.0  # Approx 2.3M meters northing
        assert res["y_easting_m"] > 500_000.0  # False easting + dx
        assert res["conversion_code"].startswith("VN2K-")

    def test_validate_coordinate_system_hcm(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.validate_coordinate_system(
            point_id="MOC-HCM-BEN-NGHE",
            latitude=10.776889,
            longitude=106.700806,
            zone_deg=3,
            province="TP. HỒ CHÍ MINH",
        )
        assert res["status"] == "COORDINATE_VALID_VN2000"
        assert res["is_in_vietnam"] is True
        assert res["central_meridian_deg"] == 105.75
        assert res["x_northing_m"] > 1_000_000.0

    def test_validate_coordinate_system_outside(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.validate_coordinate_system(
            point_id="MOC-LONDON",
            latitude=51.5074,
            longitude=-0.1278,
            zone_deg=3,
        )
        assert res["status"] == "OUTSIDE_VIETNAM_TERRITORY"
        assert res["is_in_vietnam"] is False

    def test_audit_map_sovereignty_compliant(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.audit_map_sovereignty(
            map_title="Bản đồ Hành chính Quốc gia Việt Nam",
            publisher_or_platform="Cục Đo đạc, Bản đồ và Thông tin địa lý Việt Nam",
            has_hoang_sa=True,
            has_truong_sa=True,
            has_nine_dash_line=False,
            map_type="PRINTED_ATLAS",
        )
        assert res["status"] == "SOVEREIGNTY_COMPLIANT_MAP"
        assert res["is_compliant"] is True
        assert res["penalty_fine_vnd"] == 0.0
        assert len(res["deficiencies"]) == 0
        assert res["audit_code"].startswith("SOV-")

    def test_audit_map_sovereignty_nine_dash_line(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.audit_map_sovereignty(
            map_title="Bản đồ Du lịch Đông Á Vi phạm",
            publisher_or_platform="Website Ngoại quốc",
            has_hoang_sa=True,
            has_truong_sa=True,
            has_nine_dash_line=True,  # Severe violation!
        )
        assert res["status"] == "MAP_PROHIBITED_VIOLATION"
        assert res["is_compliant"] is False
        assert res["penalty_fine_vnd"] == 50_000_000.0
        assert any("đường chín đoạn" in d for d in res["deficiencies"])

    def test_audit_map_sovereignty_missing_islands(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.audit_map_sovereignty(
            map_title="Bản đồ Thời tiết Thiếu Biển Đảo",
            publisher_or_platform="Ứng dụng Weather App",
            has_hoang_sa=False,
            has_truong_sa=True,
            has_nine_dash_line=False,
        )
        assert res["status"] == "SOVEREIGNTY_DEFICIENT_MAP"
        assert res["is_compliant"] is False
        assert res["penalty_fine_vnd"] == 40_000_000.0
        assert any("quần đảo Hoàng Sa" in d for d in res["deficiencies"])

    def test_license_geodesy_activity_approved(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.license_geodesy_activity(
            enterprise_name="Công ty CP Trắc địa Bản đồ Mekong Geo",
            technical_director="KS. Nguyễn Thành Long",
            years_experience=7,
            certified_surveyors_count=4,
            has_calibrated_instruments=True,
            scope="CADASTRAL_AND_TOPOGRAPHIC",
        )
        assert res["status"] == "LICENSE_APPROVED"
        assert res["is_approved"] is True
        assert res["validity_years"] == 5
        assert len(res["deficiencies"]) == 0
        assert res["license_code"].startswith("GP-DDBĐ-")

    def test_license_geodesy_activity_deficient_experience(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.license_geodesy_activity(
            enterprise_name="Công ty Thiếu Kinh nghiệm",
            technical_director="Kỹ sư Trẻ",
            years_experience=3,  # Requirement: >= 5 years
            certified_surveyors_count=3,
            has_calibrated_instruments=True,
        )
        assert res["status"] == "LICENSE_REJECTED"
        assert res["is_approved"] is False
        assert any("chỉ có 3 năm kinh nghiệm" in d for d in res["deficiencies"])

    def test_license_geodesy_activity_deficient_surveyors(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.license_geodesy_activity(
            enterprise_name="Công ty Thiếu Nhân sự",
            technical_director="KS. Lê Văn A",
            years_experience=10,
            certified_surveyors_count=1,  # Requirement: >= 2
            has_calibrated_instruments=True,
        )
        assert res["status"] == "LICENSE_REJECTED"
        assert res["is_approved"] is False
        assert any("chỉ có 1 kỹ thuật viên" in d for d in res["deficiencies"])

    def test_license_geodesy_activity_uncalibrated_instruments(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        res = engine.license_geodesy_activity(
            enterprise_name="Công ty Máy hỏng",
            technical_director="KS. Trần Văn B",
            years_experience=6,
            certified_surveyors_count=2,
            has_calibrated_instruments=False,
        )
        assert res["status"] == "LICENSE_REJECTED"
        assert res["is_approved"] is False
        assert any("chưa được kiểm định" in d for d in res["deficiencies"])

    def test_inspect_cadastral_survey_compliant(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        # Urban 1:500 limit is 0.07m, measured is 0.05m -> compliant
        res = engine.inspect_cadastral_survey(
            parcel_id="THUA-102-TO-05",
            province="HÀ NỘI",
            map_scale="1:500",
            area_type="URBAN",
            measured_boundary_error_m=0.05,
        )
        assert res["status"] == "SURVEY_APPROVED_COMPLIANT"
        assert res["is_compliant"] is True
        assert res["max_boundary_error_m"] == 0.07
        assert len(res["deficiencies"]) == 0
        assert res["survey_code"].startswith("CAD-")

    def test_inspect_cadastral_survey_exceeded(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        # Urban 1:500 limit is 0.07m, measured is 0.12m -> exceeded
        res = engine.inspect_cadastral_survey(
            parcel_id="THUA-99-TO-01",
            province="TP. HỒ CHÍ MINH",
            map_scale="1:500",
            area_type="URBAN",
            measured_boundary_error_m=0.12,
        )
        assert res["status"] == "SURVEY_ERROR_EXCEEDED"
        assert res["is_compliant"] is False
        assert any("vượt quá hạn mức" in d for d in res["deficiencies"])

    def test_list_records_and_status(self, temp_db):
        engine = GeodesyEngine(db_path=temp_db)
        engine.validate_coordinate_system("P1", 21.0, 105.8)
        engine.audit_map_sovereignty("Map 1", "Pub 1", has_nine_dash_line=True)
        engine.license_geodesy_activity("Cty 1", "KS 1", 6, 3)
        engine.inspect_cadastral_survey("Thửa 1", "HN", "1:500", "URBAN", 0.05)

        coords = engine.list_records(category="coordinates")
        assert len(coords) >= 1
        sovs = engine.list_records(category="sovereignty")
        assert len(sovs) >= 1
        lics = engine.list_records(category="licenses")
        assert len(lics) >= 1
        surveys = engine.list_records(category="surveys")
        assert len(surveys) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_coordinate_points_transformed"] >= 1
        assert status["total_map_sovereignty_inspections"] >= 1
        assert status["prohibited_maps_detected"] >= 1
        assert status["total_geodesy_licenses_processed"] >= 1
        assert status["total_cadastral_surveys_audited"] >= 1


class TestGeodesyCLI:
    """Tests Typer CLI commands for the geodesy app."""

    def test_cli_main_and_status(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["geodesy", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"

        res_main = runner.invoke(app, ["geodesy"])
        assert res_main.exit_code == 0
        assert "ĐO ĐẠC BẢN ĐỒ" in res_main.output

    def test_cli_coord_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "geodesy",
                "coord",
                "MOC-CLI-HN-01",
                "--lat",
                "21.028511",
                "--lon",
                "105.854444",
                "--zone",
                "3",
                "--province",
                "HÀ NỘI",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_in_vietnam"] is True
        assert data["status"] == "COORDINATE_VALID_VN2000"

    def test_cli_sovereignty_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "geodesy",
                "sovereignty",
                "Bản đồ Địa lý CLI",
                "--publisher",
                "NXB Trắc địa",
                "--hoang-sa",
                "--truong-sa",
                "--no-nine-dash",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_compliant"] is True
        assert data["status"] == "SOVEREIGNTY_COMPLIANT_MAP"

    def test_cli_license_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "geodesy",
                "license",
                "Công ty TNHH Trắc địa CLI",
                "--director",
                "KS. Hoàng Minh",
                "--exp",
                "8",
                "--surveyors",
                "4",
                "--calibrated",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "LICENSE_APPROVED"

    def test_cli_cadastral_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "geodesy",
                "cadastral",
                "THUA-CLI-55",
                "--province",
                "HÀ NỘI",
                "--scale",
                "1:500",
                "--area",
                "URBAN",
                "--error",
                "0.04",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_compliant"] is True
        assert data["status"] == "SURVEY_APPROVED_COMPLIANT"

    def test_cli_list_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["geodesy", "list", "coordinates", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestGeodesyMCP:
    """Tests dual FastMCP and fallback handlers for Geodesy suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Coord
        res_coord = json.loads(
            server._handle_geodesy_coord(
                point_id="MCP-POINT-01",
                latitude=21.028511,
                longitude=105.854444,
            )
        )
        assert res_coord["is_in_vietnam"] is True

        # Sovereignty
        res_sov = json.loads(
            server._handle_geodesy_sovereignty(
                map_title="MCP Sovereignty Map",
                has_hoang_sa=True,
                has_truong_sa=True,
                has_nine_dash_line=False,
            )
        )
        assert res_sov["is_compliant"] is True

        # License
        res_lic = json.loads(
            server._handle_geodesy_license(
                enterprise_name="MCP Geo Enterprise",
                technical_director="KS. Test",
                years_experience=6,
                certified_surveyors_count=3,
            )
        )
        assert res_lic["is_approved"] is True

        # Cadastral
        res_cad = json.loads(
            server._handle_geodesy_cadastral(
                parcel_id="THUA-MCP-01",
                province="HÀ NỘI",
                map_scale="1:500",
                measured_boundary_error_m=0.04,
            )
        )
        assert res_cad["is_compliant"] is True

        # List
        res_list = json.loads(server._handle_geodesy_list(category="coordinates"))
        assert isinstance(res_list, list)

        # Status
        res_status = json.loads(server._handle_geodesy_status())
        assert res_status["status"] == "HEALTHY"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as script_mcp

        # Test dictionary registration
        assert "mekong_geodesy_coord" in script_mcp.CORE_HANDLERS
        assert "mekong_geodesy_sovereignty" in script_mcp.CORE_HANDLERS
        assert "mekong_geodesy_license" in script_mcp.CORE_HANDLERS
        assert "mekong_geodesy_cadastral" in script_mcp.CORE_HANDLERS
        assert "mekong_geodesy_list" in script_mcp.CORE_HANDLERS
        assert "mekong_geodesy_status" in script_mcp.CORE_HANDLERS

        # Invocations
        h_coord = script_mcp.CORE_HANDLERS["mekong_geodesy_coord"]
        res_coord = json.loads(h_coord({"point_id": "Script MCP Point"}))
        assert "x_northing_m" in res_coord

        h_status = script_mcp.CORE_HANDLERS["mekong_geodesy_status"]
        res_status = json.loads(h_status({}))
        assert res_status["status"] == "HEALTHY"
