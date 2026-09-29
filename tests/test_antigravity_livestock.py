# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity (Phase 71)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.livestock_engine import (
    BIOSECURITY_MIN_DISTANCES,
    BANNED_SUBSTANCES,
    LIVESTOCK_UNIT_FACTORS,
    REGIONAL_DENSITY_CAPS,
    LivestockEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestLivestockCoreBoundary:
    """Ensure LivestockEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/livestock_engine.py")
        assert source_path.exists(), "livestock_engine.py must exist"

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


class TestLivestockEngine:
    """Test LivestockEngine ĐVN conversion, farm scale, biosecurity distances, feed safety, and biogas sizing."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> LivestockEngine:
        db_file = tmp_path / "test_livestock.db"
        return LivestockEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Check Livestock Unit Factors under Annex V Decree 13/2020
        assert "PIG_FATTENER" in LIVESTOCK_UNIT_FACTORS
        assert LIVESTOCK_UNIT_FACTORS["PIG_FATTENER"]["factor"] == 0.20
        assert LIVESTOCK_UNIT_FACTORS["PIG_SOW"]["factor"] == 0.50
        assert LIVESTOCK_UNIT_FACTORS["CATTLE_BEEF"]["factor"] == 1.00
        assert LIVESTOCK_UNIT_FACTORS["CATTLE_DAIRY"]["factor"] == 1.50
        assert LIVESTOCK_UNIT_FACTORS["BUFFALO"]["factor"] == 1.00
        assert LIVESTOCK_UNIT_FACTORS["POULTRY_BROILER"]["factor"] == 0.014
        assert LIVESTOCK_UNIT_FACTORS["POULTRY_LAYER"]["factor"] == 0.018
        assert LIVESTOCK_UNIT_FACTORS["DUCK"]["factor"] == 0.018
        assert LIVESTOCK_UNIT_FACTORS["GOAT_SHEEP"]["factor"] == 0.15

        # Check regional density caps
        assert REGIONAL_DENSITY_CAPS["SOUTHEAST"] == 1.5
        assert REGIONAL_DENSITY_CAPS["MEKONG_DELTA"] == 1.5
        assert REGIONAL_DENSITY_CAPS["CENTRAL_HIGHLANDS"] == 1.0

        # Check biosecurity minimum buffer distances
        assert BIOSECURITY_MIN_DISTANCES["LARGE_SCALE"]["residential_distance_m"] == 400.0
        assert BIOSECURITY_MIN_DISTANCES["LARGE_SCALE"]["water_source_distance_m"] == 100.0
        assert BIOSECURITY_MIN_DISTANCES["LARGE_SCALE"]["farm_to_farm_distance_m"] == 1000.0

        # Check prohibited Beta-agonist substances
        assert "SALBUTAMOL" in BANNED_SUBSTANCES
        assert "CLENBUTEROL" in BANNED_SUBSTANCES
        assert "RACTOPAMINE" in BANNED_SUBSTANCES

    def test_register_livestock_farm_large_scale(self, engine: LivestockEngine) -> None:
        res = engine.register_livestock_farm(
            farm_name="Trang Trại Heo CP Cẩm Mỹ",
            owner_name="C.P. Vietnam Corporation",
            province="Đồng Nai",
            animal_type="PIG_FATTENER",
            head_count=2500,
            agricultural_land_ha=350.0,
            region="SOUTHEAST",
        )
        assert res["ok"] is True
        assert res["farm_id"].startswith("LVF-")
        prof = res["farm_profile"]
        assert prof["head_count"] == 2500
        assert prof["livestock_units"] == 500.0  # 2500 * 0.20
        assert prof["farm_scale"] == "LARGE_SCALE"
        assert prof["actual_stocking_density"] == round(500.0 / 350.0, 2)
        assert prof["is_density_compliant"] is True

        farms = engine.list_livestock_farms()
        assert len(farms) == 1
        assert farms[0]["farm_name"] == "Trang Trại Heo CP Cẩm Mỹ"

    def test_register_livestock_farm_scales_and_density_violation(self, engine: LivestockEngine) -> None:
        # Medium scale: 50 cattle = 50 ĐVN (30 - 300 ĐVN)
        res_med = engine.register_livestock_farm(
            farm_name="Trang Trại Bò Sữa Mộc Châu",
            owner_name="Moc Chau Milk",
            province="Sơn La",
            animal_type="CATTLE_BEEF",
            head_count=50,
            agricultural_land_ha=60.0,
            region="NORTHERN_MIDLANDS_MOUNTAINS",
        )
        assert res_med["farm_profile"]["farm_scale"] == "MEDIUM_SCALE"
        assert res_med["farm_profile"]["livestock_units"] == 50.0

        # Small scale: 100 fattening pigs = 20 ĐVN (10 - 30 ĐVN)
        res_small = engine.register_livestock_farm(
            farm_name="Trại Heo Gia Đình Chú Ba",
            owner_name="Nguyễn Văn Ba",
            province="Bến Tre",
            animal_type="PIG_FATTENER",
            head_count=100,
            agricultural_land_ha=20.0,
            region="MEKONG_DELTA",
        )
        assert res_small["farm_profile"]["farm_scale"] == "SMALL_SCALE"
        assert res_small["farm_profile"]["livestock_units"] == 20.0

        # Household scale with density violation: 30 pigs = 6 ĐVN on 0.5 ha -> density 12.0 > 1.0
        res_house = engine.register_livestock_farm(
            farm_name="Hộ Chăn Nuôi Thím Bảy",
            owner_name="Trần Thị Bảy",
            province="Gia Lai",
            animal_type="PIG_FATTENER",
            head_count=30,
            agricultural_land_ha=0.5,
            region="CENTRAL_HIGHLANDS",
        )
        assert res_house["farm_profile"]["farm_scale"] == "HOUSEHOLD"
        assert res_house["farm_profile"]["actual_stocking_density"] == 12.0
        assert res_house["farm_profile"]["is_density_compliant"] is False

    def test_audit_biosecurity_distance_compliant(self, engine: LivestockEngine) -> None:
        res = engine.audit_biosecurity_distance(
            farm_id="LVF-12345678",
            farm_scale="LARGE_SCALE",
            residential_distance_m=500.0,
            water_source_distance_m=150.0,
            farm_to_farm_distance_m=1200.0,
        )
        assert res["ok"] is True
        assert res["audit_id"].startswith("BIO-")
        b = res["biosecurity_audit"]
        assert b["residential_distance_compliant"] is True
        assert b["water_source_distance_compliant"] is True
        assert b["farm_to_farm_distance_compliant"] is True
        assert b["is_biosecurity_compliant"] is True

        audits = engine.list_biosecurity_audits()
        assert len(audits) == 1

    def test_audit_biosecurity_distance_violations(self, engine: LivestockEngine) -> None:
        res = engine.audit_biosecurity_distance(
            farm_id="LVF-99999999",
            farm_scale="LARGE_SCALE",
            residential_distance_m=250.0,  # Req >= 400m
            water_source_distance_m=80.0,  # Req >= 100m
            farm_to_farm_distance_m=800.0,  # Req >= 1000m
        )
        assert res["ok"] is True
        b = res["biosecurity_audit"]
        assert b["residential_distance_compliant"] is False
        assert b["water_source_distance_compliant"] is False
        assert b["farm_to_farm_distance_compliant"] is False
        assert b["is_biosecurity_compliant"] is False
        assert "VI PHẠM" in b["biosecurity_verdict"]

    def test_inspect_feed_quality_compliant(self, engine: LivestockEngine) -> None:
        res = engine.inspect_feed_quality(
            product_name="Thức ăn hỗn hợp hoàn chỉnh cho heo vỗ béo P-501",
            feed_type="PIG_FEED_COMPLETE",
            manufacturer="C.P. Vietnam Corporation",
            crude_protein_pct=18.5,
            aflatoxin_b1_ppb=8.0,
            lead_pb_ppm=1.2,
            banned_substance=None,
        )
        assert res["ok"] is True
        assert res["inspection_id"].startswith("FEE-")
        f = res["feed_inspection"]
        assert f["crude_protein_compliant"] is True
        assert f["aflatoxin_compliant"] is True
        assert f["lead_compliant"] is True
        assert f["banned_substance_detected"] is False
        assert f["is_feed_compliant"] is True

        tests = engine.list_feed_inspections()
        assert len(tests) == 1

    def test_inspect_feed_quality_prohibited_beta_agonist(self, engine: LivestockEngine) -> None:
        res = engine.inspect_feed_quality(
            product_name="Bột tăng trọng siêu nạc lậu",
            feed_type="CONCENTRATE",
            manufacturer="Unknown Lab",
            crude_protein_pct=22.0,
            aflatoxin_b1_ppb=5.0,
            lead_pb_ppm=0.8,
            banned_substance="SALBUTAMOL_POSITIVE",
        )
        assert res["ok"] is True
        f = res["feed_inspection"]
        assert f["banned_substance_detected"] is True
        assert f["is_feed_compliant"] is False
        assert "CHẤT CẤM CHĂN NUÔI" in f["quality_verdict"]

    def test_inspect_feed_quality_toxic_limits(self, engine: LivestockEngine) -> None:
        # Aflatoxin over limit (> 20 ppb) and low protein (< 14%)
        res = engine.inspect_feed_quality(
            product_name="Cám ngô ẩm mốc kém chất lượng",
            feed_type="RAW_INGREDIENT",
            manufacturer="Local Mill",
            crude_protein_pct=11.0,
            aflatoxin_b1_ppb=35.0,
            lead_pb_ppm=6.5,  # Lead > 5.0 ppm
        )
        f = res["feed_inspection"]
        assert f["crude_protein_compliant"] is False
        assert f["aflatoxin_compliant"] is False
        assert f["lead_compliant"] is False
        assert f["is_feed_compliant"] is False

    def test_audit_waste_treatment_pig_biogas(self, engine: LivestockEngine) -> None:
        # 400 ĐVN pigs -> required volume = 400 * 0.8 = 320 m3
        res = engine.audit_waste_treatment(
            farm_id="LVF-12345678",
            livestock_units=400.0,
            treatment_method="BIOGAS_DIGESTER_HDPE",
            biogas_volume_m3=350.0,
            is_cattle=False,
        )
        assert res["ok"] is True
        assert res["waste_audit_id"].startswith("WST-")
        w = res["waste_treatment_audit"]
        assert w["required_biogas_volume_m3"] == 320.0
        assert w["rate_m3_per_dvn"] == 0.8
        assert w["is_biogas_sufficient"] is True

        audits = engine.list_waste_audits()
        assert len(audits) == 1

    def test_audit_waste_treatment_cattle_insufficient(self, engine: LivestockEngine) -> None:
        # 200 ĐVN cattle -> required volume = 200 * 1.2 = 240 m3, provided 180 m3
        res = engine.audit_waste_treatment(
            farm_id="LVF-88888888",
            livestock_units=200.0,
            treatment_method="BIOGAS_COVERED_LAGOON",
            biogas_volume_m3=180.0,
            is_cattle=True,
        )
        assert res["ok"] is True
        w = res["waste_treatment_audit"]
        assert w["required_biogas_volume_m3"] == 240.0
        assert w["rate_m3_per_dvn"] == 1.2
        assert w["is_biogas_sufficient"] is False
        assert "THIẾU HỤT" in w["treatment_verdict"]

    def test_status_telemetry(self, engine: LivestockEngine) -> None:
        engine.register_livestock_farm("Trại 1", agricultural_land_ha=100.0)
        engine.audit_biosecurity_distance("LVF-1", residential_distance_m=500.0, water_source_distance_m=120.0, farm_to_farm_distance_m=1100.0)
        engine.inspect_feed_quality("Cám 1", crude_protein_pct=16.0, aflatoxin_b1_ppb=5.0, lead_pb_ppm=1.0)
        engine.audit_waste_treatment("LVF-1", livestock_units=100.0, biogas_volume_m3=100.0)

        status = engine.get_status()
        assert status["ok"] is True
        m = status["metrics"]
        assert m["registered_livestock_farms"] == 1
        assert m["biosecurity_audits_conducted"] == 1
        assert m["feed_quality_inspections_conducted"] == 1
        assert m["waste_biogas_audits_performed"] == 1
        assert m["sufficient_biogas_farms"] == 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestLivestockCLI:
    """Test Typer CLI commands for livestock management."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_help(self, app) -> None:
        result = runner.invoke(app, ["livestock", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Animal Husbandry, Livestock Farming" in result.output
        assert "farm" in result.output
        assert "distance" in result.output
        assert "feed" in result.output
        assert "waste" in result.output
        assert "list" in result.output
        assert "status" in result.output

    def test_cli_main_status(self, app) -> None:
        result = runner.invoke(app, ["livestock"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ CHĂN NUÔI" in result.output

    def test_cli_main_status_json(self, app) -> None:
        result = runner.invoke(app, ["livestock", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_farm_command(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(app, [
            "livestock", "farm", "Trang Trại Heo CP Long Thành",
            "--owner", "CP Group",
            "--province", "Đồng Nai",
            "--animal", "PIG_FATTENER",
            "--heads", "1500",
            "--land", "25.0",
            "--region", "SOUTHEAST",
            "--json",
        ])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["farm_profile"]["livestock_units"] == 300.0

        # Console mode
        res_console = runner.invoke(app, [
            "livestock", "farm", "Trang Trại Bò Sữa Ba Vì",
            "--heads", "100",
            "--animal", "CATTLE_DAIRY",
        ])
        assert res_console.exit_code == 0
        assert "Trang Trại Bò Sữa Ba Vì" in res_console.output

    def test_cli_distance_command(self, app) -> None:
        res = runner.invoke(app, [
            "livestock", "distance", "LVF-CLI01",
            "--scale", "LARGE_SCALE",
            "--residential", "450",
            "--water", "120",
            "--farm-dist", "1200",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["biosecurity_audit"]["is_biosecurity_compliant"] is True

        res_con = runner.invoke(app, ["livestock", "distance", "LVF-CLI02"])
        assert res_con.exit_code == 0
        assert "Khoảng Cách An Toàn Sinh Học" in res_con.output

    def test_cli_feed_command(self, app) -> None:
        res = runner.invoke(app, [
            "livestock", "feed", "Thức Ăn Hỗn Hợp CP 502",
            "--type", "PIG_FEED_COMPLETE",
            "--maker", "CP Vietnam",
            "--protein", "18.0",
            "--aflatoxin", "10.0",
            "--lead", "1.5",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["feed_inspection"]["is_feed_compliant"] is True

        res_con = runner.invoke(app, ["livestock", "feed", "Cám Heo De Heus"])
        assert res_con.exit_code == 0
        assert "Kiểm Định An Toàn & Chất Lượng Thức Ăn Chăn Nuôi" in res_con.output

    def test_cli_waste_command(self, app) -> None:
        res = runner.invoke(app, [
            "livestock", "waste", "LVF-CLI01",
            "--dvn", "300.0",
            "--volume", "280.0",
            "--pig",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["waste_treatment_audit"]["is_biogas_sufficient"] is True

        res_con = runner.invoke(app, ["livestock", "waste", "LVF-CLI02"])
        assert res_con.exit_code == 0
        assert "Thẩm Định Xử Lý Chất Thải Chăn Nuôi" in res_con.output

    def test_cli_list_commands(self, app) -> None:
        for cat in ("farms", "biosecurity", "feed", "waste"):
            res = runner.invoke(app, ["livestock", "list", cat, "--json"])
            assert res.exit_code == 0
            assert "{" in res.output

        res_table = runner.invoke(app, ["livestock", "list", "farms"])
        assert res_table.exit_code == 0
        assert "Danh Sách Dữ Liệu Chăn Nuôi" in res_table.output

    def test_cli_status_subcommand(self, app) -> None:
        res = runner.invoke(app, ["livestock", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True

        res_con = runner.invoke(app, ["livestock", "status"])
        assert res_con.exit_code == 0
        assert "Tổng Quan Quản Lý Chăn Nuôi" in res_con.output


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestLivestockMCP:
    """Test Dual FastMCP & fallback stdio JSON-RPC MCP handlers."""

    def test_src_core_mcp_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Farm
        farm_raw = server._handle_livestock_farm(
            farm_name="Trang Trại MCP Core",
            owner_name="Mekong Agri",
            province="Bình Dương",
            animal_type="PIG_FATTENER",
            head_count=1000,
            agricultural_land_ha=20.0,
            region="SOUTHEAST",
        )
        farm_data = json.loads(farm_raw)
        assert farm_data["ok"] is True
        farm_id = farm_data["farm_id"]

        # 2. Distance
        dist_raw = server._handle_livestock_distance(
            farm_id=farm_id,
            farm_scale="LARGE_SCALE",
            residential_distance_m=420.0,
            water_source_distance_m=110.0,
            farm_to_farm_distance_m=1050.0,
        )
        dist_data = json.loads(dist_raw)
        assert dist_data["ok"] is True
        assert dist_data["biosecurity_audit"]["is_biosecurity_compliant"] is True

        # 3. Feed
        feed_raw = server._handle_livestock_feed(
            product_name="Cám hỗn hợp MCP",
            crude_protein_pct=17.0,
            aflatoxin_b1_ppb=7.0,
            lead_pb_ppm=1.0,
        )
        feed_data = json.loads(feed_raw)
        assert feed_data["ok"] is True
        assert feed_data["feed_inspection"]["is_feed_compliant"] is True

        # 4. Waste
        waste_raw = server._handle_livestock_waste(
            farm_id=farm_id,
            livestock_units=200.0,
            biogas_volume_m3=180.0,
        )
        waste_data = json.loads(waste_raw)
        assert waste_data["ok"] is True
        assert waste_data["waste_treatment_audit"]["is_biogas_sufficient"] is True

        # 5. List
        list_raw = server._handle_livestock_list(category="farms")
        list_data = json.loads(list_raw)
        assert isinstance(list_data, list)
        assert len(list_data) >= 1

        # 6. Status
        status_raw = server._handle_livestock_status()
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True
        assert "metrics" in status_data

    def test_scripts_mcp_server_handlers_and_spec_parity(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_livestock_distance,
            handle_livestock_farm,
            handle_livestock_feed,
            handle_livestock_list,
            handle_livestock_status,
            handle_livestock_waste,
        )

        # Check specification presence
        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        assert "mekong_livestock_farm" in tool_names
        assert "mekong_livestock_distance" in tool_names
        assert "mekong_livestock_feed" in tool_names
        assert "mekong_livestock_waste" in tool_names
        assert "mekong_livestock_list" in tool_names
        assert "mekong_livestock_status" in tool_names

        # Check CORE_HANDLERS mapping
        assert "mekong_livestock_farm" in CORE_HANDLERS
        assert "mekong_livestock_distance" in CORE_HANDLERS
        assert "mekong_livestock_feed" in CORE_HANDLERS
        assert "mekong_livestock_waste" in CORE_HANDLERS
        assert "mekong_livestock_list" in CORE_HANDLERS
        assert "mekong_livestock_status" in CORE_HANDLERS

        # Test scripts handlers directly
        farm_res = json.loads(handle_livestock_farm({"farm_name": "Trại Script Test", "head_count": 500}))
        assert farm_res["ok"] is True
        fid = farm_res["farm_id"]

        dist_res = json.loads(handle_livestock_distance({"farm_id": fid}))
        assert dist_res["ok"] is True

        feed_res = json.loads(handle_livestock_feed({"product_name": "Cám Script", "crude_protein_pct": 18.0}))
        assert feed_res["ok"] is True

        waste_res = json.loads(handle_livestock_waste({"farm_id": fid, "livestock_units": 100.0, "biogas_volume_m3": 100.0}))
        assert waste_res["ok"] is True

        list_res = json.loads(handle_livestock_list({"category": "farms"}))
        assert isinstance(list_res, list)

        stat_res = json.loads(handle_livestock_status({}))
        assert stat_res["ok"] is True
