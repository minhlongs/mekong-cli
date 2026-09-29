# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Forestry Management, VNTLAS Timber Legality, FSC & Forest Carbon Sinks (Phase 68)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.forestry_engine import (
    FIRE_DANGER_LEVELS,
    FOREST_TYPES,
    PFES_RATES,
    VNTLAS_ENTERPRISE_TIERS,
    ForestryEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestForestryCoreBoundary:
    """Ensure ForestryEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/forestry_engine.py")
        assert source_path.exists(), "forestry_engine.py must exist"

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


class TestForestryEngine:
    """Test ForestryEngine plot registration, VNTLAS timber verification, afforestation, PFES, and fire danger."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> ForestryEngine:
        db_file = tmp_path / "test_forestry.db"
        return ForestryEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Check conversion multipliers
        assert FOREST_TYPES["SPECIAL_USE"]["conversion_multiplier"] == 3.0
        assert FOREST_TYPES["PROTECTION"]["conversion_multiplier"] == 3.0
        assert FOREST_TYPES["PRODUCTION_NATURAL"]["conversion_multiplier"] == 3.0
        assert FOREST_TYPES["PRODUCTION_PLANTATION"]["conversion_multiplier"] == 1.0

        # Check PFES rates
        assert PFES_RATES["HYDROPOWER"]["rate_vnd"] == 36.0
        assert PFES_RATES["CLEAN_WATER"]["rate_vnd"] == 52.0
        assert PFES_RATES["INDUSTRIAL_WATER"]["rate_vnd"] == 50.0

        # Check VNTLAS tiers
        assert VNTLAS_ENTERPRISE_TIERS["TIER_1"]["green_channel"] is True
        assert VNTLAS_ENTERPRISE_TIERS["TIER_2"]["green_channel"] is False

    def test_register_forest_plot(self, engine: ForestryEngine) -> None:
        res = engine.register_forest_plot(
            plot_name="Lô Rừng Trồng Đại Lộc",
            forest_type="PRODUCTION_PLANTATION",
            province="Quảng Nam",
            area_hectares=200.0,
            canopy_cover_pct=65.0,
            trees_per_hectare=1500.0,
            main_species="Acacia auriculiformis",
            is_fsc_certified=True,
            fsc_code="FSC-C998877",
        )
        assert res["ok"] is True
        assert res["plot_id"].startswith("PLT-")
        assert res["profile"]["canopy_standard_met"] is True
        assert res["profile"]["total_estimated_trees"] == 300000
        assert res["profile"]["fsc_code"] == "FSC-C998877"

        plots = engine.list_forest_plots()
        assert len(plots) == 1
        assert plots[0]["plot_name"] == "Lô Rừng Trồng Đại Lộc"

    def test_register_special_use_forest(self, engine: ForestryEngine) -> None:
        res = engine.register_forest_plot(
            plot_name="Vườn Quốc Gia Bạch Mã",
            forest_type="SPECIAL_USE",
            province="Thừa Thiên Huế",
            area_hectares=37487.0,
            canopy_cover_pct=85.0,
            trees_per_hectare=800.0,
            main_species="Rừng Thường Xanh Nhiệt Đới",
            is_fsc_certified=False,
        )
        assert res["ok"] is True
        assert res["profile"]["felling_prohibited"] is True
        assert res["profile"]["fsc_code"] == "NONE"

    def test_verify_timber_vntlas_tier1_compliant(self, engine: ForestryEngine) -> None:
        res = engine.verify_timber_vntlas(
            enterprise_name="Tập Đoàn Gỗ Thuận An",
            product_type="FURNITURE",
            volume_m3=180.0,
            species="Keo tràm / Cao su",
            origin_province="Bình Dương",
            enterprise_tier="TIER_1",
            flegt_cites_license="FLEGT-VN-2026-9999",
            export_market="EU",
        )
        assert res["ok"] is True
        assert res["verification_report"]["is_vntlas_verified"] is True
        assert res["verification_report"]["customs_channel"] == "GREEN_FAST_TRACK"
        assert res["verification_report"]["risk_assessment"] == "LOW"

        consignments = engine.list_timber_consignments()
        assert len(consignments) == 1
        assert consignments[0]["enterprise_tier"] == "TIER_1"

    def test_verify_timber_vntlas_tier2_requires_audit(self, engine: ForestryEngine) -> None:
        res = engine.verify_timber_vntlas(
            enterprise_name="Xưởng Mộc Mới Thành Lập X",
            product_type="SAWN_TIMBER",
            volume_m3=45.0,
            species="Gỗ Nhập Khẩu Chưa Xác Minh",
            origin_province="Đồng Nai",
            enterprise_tier="TIER_2",
            flegt_cites_license=None,
            export_market="US",
        )
        assert res["ok"] is True
        assert res["verification_report"]["is_vntlas_verified"] is False
        assert res["verification_report"]["customs_channel"] == "RED_FULL_VERIFICATION_REQUIRED"
        assert res["verification_report"]["risk_assessment"] == "HIGH"

    def test_calculate_alternative_afforestation(self, engine: ForestryEngine) -> None:
        # Natural forest conversion: multiplier 3.0x
        res_nat = engine.calculate_alternative_afforestation(
            project_name="Thủy Điện A Vương",
            converted_forest_type="PRODUCTION_NATURAL",
            converted_area_ha=30.0,
            payment_rate_vnd_per_ha=100000000.0,  # 100M/ha
        )
        assert res_nat["ok"] is True
        assert res_nat["project_profile"]["statutory_multiplier"] == 3.0
        assert res_nat["project_profile"]["required_new_afforestation_ha"] == 90.0
        assert res_nat["project_profile"]["total_vnff_payment_vnd"] == 9000000000.0

        # Plantation forest conversion: multiplier 1.0x
        res_plan = engine.calculate_alternative_afforestation(
            project_name="Khu Công Nghiệp Hòa Cầm",
            converted_forest_type="PRODUCTION_PLANTATION",
            converted_area_ha=50.0,
            payment_rate_vnd_per_ha=90000000.0,
        )
        assert res_plan["project_profile"]["statutory_multiplier"] == 1.0
        assert res_plan["project_profile"]["required_new_afforestation_ha"] == 50.0
        assert res_plan["project_profile"]["total_vnff_payment_vnd"] == 4500000000.0

        affs = engine.list_afforestation_projects()
        assert len(affs) == 2

    def test_calculate_pfes_and_carbon(self, engine: ForestryEngine) -> None:
        # Hydropower test: 36 VND/kWh
        res_hydro = engine.calculate_pfes_and_carbon(
            facility_name="Thủy Điện Trị An",
            facility_type="HYDROPOWER",
            production_volume=1000000000.0,  # 1 tỷ kWh
            forest_area_ha=20000.0,
            carbon_sequestration_rate=4.0,  # 4 tCO2e/ha/yr
            erpa_price_usd_per_ton=5.0,
        )
        assert res_hydro["ok"] is True
        assert res_hydro["calculation_result"]["total_pfes_amount_vnd"] == 36000000000.0  # 36 tỷ VND
        assert res_hydro["calculation_result"]["annual_carbon_sequestration_tco2e"] == 80000.0
        assert res_hydro["calculation_result"]["total_erpa_carbon_revenue_usd"] == 400000.0

        # Eco-tourism test: 1.5% revenue
        res_tour = engine.calculate_pfes_and_carbon(
            facility_name="Khu Du Lịch Sinh Thái Cát Tiên",
            facility_type="ECO_TOURISM",
            production_volume=20000000000.0,  # 20 tỷ VND revenue
            forest_area_ha=5000.0,
        )
        assert res_tour["calculation_result"]["total_pfes_amount_vnd"] == 300000000.0  # 1.5% of 20B = 300M

        pfes_list = engine.list_pfes_records()
        assert len(pfes_list) == 2

    def test_assess_forest_fire_danger(self, engine: ForestryEngine) -> None:
        # Normal low danger (Level 1)
        res_low = engine.assess_forest_fire_danger(
            plot_id="PLT-TEST-1",
            temperature_c=25.0,
            humidity_pct=80.0,
            wind_speed_kmh=10.0,
            consecutive_dry_days=1,
        )
        assert res_low["fire_danger_verdict"]["danger_level"] == 1
        assert "CẤP I" in res_low["fire_danger_verdict"]["danger_name"]

        # Extreme high danger (Level 5)
        res_ext = engine.assess_forest_fire_danger(
            plot_id="PLT-TEST-2",
            temperature_c=39.0,
            humidity_pct=25.0,
            wind_speed_kmh=35.0,
            consecutive_dry_days=25,
        )
        assert res_ext["fire_danger_verdict"]["danger_level"] == 5
        assert "CẤP V" in res_ext["fire_danger_verdict"]["danger_name"]
        assert res_ext["fire_danger_verdict"]["badge_color"] == "red"

        fires = engine.list_fire_danger_assessments()
        assert len(fires) == 2

    def test_get_status_metrics(self, engine: ForestryEngine) -> None:
        engine.register_forest_plot(
            plot_name="Rừng Thử Nghiệm",
            area_hectares=100.0,
            is_fsc_certified=True,
        )
        engine.verify_timber_vntlas(
            enterprise_name="Công Ty Gỗ",
            volume_m3=50.0,
            enterprise_tier="TIER_1",
            flegt_cites_license="FLEGT-01",
        )
        engine.calculate_alternative_afforestation(
            project_name="Dự Án Đường",
            converted_area_ha=10.0,
        )
        engine.calculate_pfes_and_carbon(
            facility_name="Thủy Điện",
            production_volume=1000000.0,
            forest_area_ha=1000.0,
        )
        engine.assess_forest_fire_danger(
            plot_id="PLT-TEST",
            temperature_c=40.0,
            humidity_pct=20.0,
            wind_speed_kmh=30.0,
            consecutive_dry_days=30,
        )

        st = engine.get_status()
        assert st["ok"] is True
        assert st["status"] == "operational"
        assert st["metrics"]["registered_forest_plots"] == 1
        assert st["metrics"]["total_forest_area_ha"] == 100.0
        assert st["metrics"]["fsc_certified_area_ha"] == 100.0
        assert st["metrics"]["vntlas_verified_volume_m3"] == 50.0
        assert st["metrics"]["high_danger_warnings_active"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestForestryCLI:
    """Test Typer CLI commands for mekong forestry."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_overview(self, app) -> None:
        result = runner.invoke(app, ["forestry"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ LÂM NGHIỆP" in result.output

    def test_cli_overview_json(self, app) -> None:
        result = runner.invoke(app, ["forestry", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["engine"] == "ForestryEngine"

    def test_cli_plot(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "forestry",
                "plot",
                "Khu Rừng Keo Hương Sơn",
                "--type",
                "PRODUCTION_PLANTATION",
                "--province",
                "Hà Tĩnh",
                "--area",
                "350",
                "--canopy",
                "70",
                "--species",
                "Keo lai",
                "--fsc",
                "--fsc-code",
                "FSC-HT1234",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["profile"]["plot_name"] == "Khu Rừng Keo Hương Sơn"
        assert data["profile"]["province"] == "Hà Tĩnh"

    def test_cli_timber(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "forestry",
                "timber",
                "Công Ty Chế Biến Gỗ Trường Thành",
                "--product",
                "FURNITURE",
                "--volume",
                "250.0",
                "--tier",
                "TIER_1",
                "--license",
                "FLEGT-VN-2026-8888",
                "--market",
                "EU",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["verification_report"]["is_vntlas_verified"] is True
        assert data["verification_report"]["customs_channel"] == "GREEN_FAST_TRACK"

    def test_cli_afforestation(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "forestry",
                "afforestation",
                "Dự Án Tuyến Đường Cao Tốc",
                "--forest-type",
                "PRODUCTION_NATURAL",
                "--area",
                "40.0",
                "--rate",
                "95000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["project_profile"]["required_new_afforestation_ha"] == 120.0
        assert data["project_profile"]["total_vnff_payment_vnd"] == 11400000000.0

    def test_cli_pfes(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "forestry",
                "pfes",
                "Thủy Điện Đồng Nai 4",
                "--type",
                "HYDROPOWER",
                "--volume",
                "500000000",
                "--forest-area",
                "15000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["calculation_result"]["total_pfes_amount_vnd"] == 18000000000.0

    def test_cli_fire(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "forestry",
                "fire",
                "PLT-TEST-CLI",
                "--temp",
                "38.5",
                "--humidity",
                "30.0",
                "--wind",
                "25.0",
                "--dry-days",
                "15",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["fire_danger_verdict"]["danger_level"] >= 4

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["forestry", "list", "plots", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "plots" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["forestry", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Integration Tests
# ---------------------------------------------------------------------------


class TestForestryMCP:
    """Test MCP server tool handlers and FastMCP parity for forestry."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_forestry_plot,
            handle_forestry_timber,
            handle_forestry_afforestation,
            handle_forestry_pfes,
            handle_forestry_fire,
            handle_forestry_list,
            handle_forestry_status,
        )

        # Plot
        res_plot = json.loads(handle_forestry_plot({"plot_name": "Rừng MCP"}))
        assert res_plot["ok"] is True

        # Timber
        res_tim = json.loads(handle_forestry_timber({"enterprise_name": "Gỗ MCP"}))
        assert res_tim["ok"] is True

        # Afforestation
        res_aff = json.loads(handle_forestry_afforestation({"project_name": "Dự Án MCP"}))
        assert res_aff["ok"] is True

        # PFES
        res_pfe = json.loads(handle_forestry_pfes({"facility_name": "Thủy Điện MCP"}))
        assert res_pfe["ok"] is True

        # Fire
        res_fir = json.loads(handle_forestry_fire({"plot_id": "PLT-MCP"}))
        assert res_fir["ok"] is True

        # List & Status
        res_lst = json.loads(handle_forestry_list({"category": "plots"}))
        assert isinstance(res_lst, list)

        res_st = json.loads(handle_forestry_status({}))
        assert res_st["ok"] is True

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        res_plot = json.loads(server._handle_forestry_plot(plot_name="Rừng Core MCP"))
        assert res_plot["ok"] is True

        res_tim = json.loads(server._handle_forestry_timber(enterprise_name="Gỗ Core MCP"))
        assert res_tim["ok"] is True

        res_aff = json.loads(server._handle_forestry_afforestation(project_name="Dự Án Core MCP"))
        assert res_aff["ok"] is True

        res_pfe = json.loads(server._handle_forestry_pfes(facility_name="Thủy Điện Core MCP"))
        assert res_pfe["ok"] is True

        res_fir = json.loads(server._handle_forestry_fire(plot_id="PLT-CORE-MCP"))
        assert res_fir["ok"] is True

        res_lst = json.loads(server._handle_forestry_list(category="plots"))
        assert isinstance(res_lst, list)

        res_st = json.loads(server._handle_forestry_status())
        assert res_st["ok"] is True
