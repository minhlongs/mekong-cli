# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Mining, Mineral Rights Fees, Royalties & Environmental Rehabilitation (Phase 67)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.mining_engine import (
    MINERAL_CATALOG,
    MINING_METHODS,
    MiningEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestMiningCoreBoundary:
    """Ensure MiningEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/mining_engine.py")
        assert source_path.exists(), "mining_engine.py must exist"

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


class TestMiningEngine:
    """Test MiningEngine concession licensing, rights fees, royalty taxes & rehabilitation escrow."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> MiningEngine:
        db_file = tmp_path / "test_mining.db"
        return MiningEngine(db_path=db_file)

    def test_constants_and_catalogs(self) -> None:
        assert "RARE_EARTH" in MINERAL_CATALOG
        assert "BAUXITE" in MINERAL_CATALOG
        assert "GOLD_ORE" in MINERAL_CATALOG
        assert "COAL_ENERGY" in MINERAL_CATALOG
        assert "RIVER_SAND" in MINERAL_CATALOG
        assert "CONSTRUCTION_STONE" in MINERAL_CATALOG

        assert "OPEN_PIT" in MINING_METHODS
        assert "UNDERGROUND" in MINING_METHODS
        assert MINING_METHODS["OPEN_PIT"]["coefficient_K"] == 1.0
        assert MINING_METHODS["UNDERGROUND"]["coefficient_K"] == 0.9

    def test_register_mining_license_strategic_vs_provincial(self, engine: MiningEngine) -> None:
        # Strategic mineral: RARE_EARTH -> Bộ Tài nguyên và Môi trường
        res_re = engine.register_mining_license(
            mine_name="Mỏ Đất hiếm Nậm Xe",
            mineral_type="RARE_EARTH",
            enterprise_name="Vietnam Rare Earth JSC",
            approved_reserve=2500000.0,
            annual_capacity=100000.0,
            mining_method="OPEN_PIT",
            duration_years=25,
        )
        assert res_re["ok"] is True
        assert res_re["license_id"].startswith("LIC-MIN-")
        assert res_re["statutory_jurisdiction"]["is_strategic_national_asset"] is True
        assert res_re["statutory_jurisdiction"]["licensing_authority"] == "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG"
        assert res_re["concession_profile"]["license_duration_years"] == 25

        # Common building material: RIVER_SAND -> UBND cấp tỉnh
        res_sand = engine.register_mining_license(
            mine_name="Mỏ Cát Sông Tiền Cồn Ấu",
            mineral_type="RIVER_SAND",
            enterprise_name="Công ty Khai thác Cát Miền Tây",
            approved_reserve=1200000.0,
            annual_capacity=300000.0,
            mining_method="OPEN_PIT",
            duration_years=35,  # Exceeds max 30 years
        )
        assert res_sand["statutory_jurisdiction"]["is_strategic_national_asset"] is False
        assert res_sand["statutory_jurisdiction"]["licensing_authority"] == "UBND CẤP TỈNH / THÀNH PHỐ"
        # Should be capped at 30 years
        assert res_sand["concession_profile"]["license_duration_years"] == 30

    def test_calculate_mineral_rights_fee_open_pit_and_underground(self, engine: MiningEngine) -> None:
        q = 1000000.0  # 1 million tonnes
        g = 850000000.0  # 850k VND / ton
        r = 5.0  # 5%

        # Open pit: K = 1.0 -> T = 1,000,000 * 850,000,000 * 1.0 * 0.05
        res_open = engine.calculate_mineral_rights_fee(
            license_id="LIC-001",
            reserve_volume=q,
            custom_unit_price_vnd=g,
            mining_method="OPEN_PIT",
            mineral_type="RARE_EARTH",
            payment_years=10,
        )
        assert res_open["ok"] is True
        rfc_open = res_open["rights_fee_computation"]
        expected_open = q * g * 1.0 * (r / 100.0)
        assert rfc_open["total_mineral_rights_fee_vnd"] == expected_open
        assert rfc_open["annual_installment_vnd"] == expected_open / 10.0

        # Underground: K = 0.9 -> T = 1,000,000 * 850,000,000 * 0.9 * 0.05
        res_ug = engine.calculate_mineral_rights_fee(
            license_id="LIC-002",
            reserve_volume=q,
            custom_unit_price_vnd=g,
            mining_method="UNDERGROUND",
            mineral_type="RARE_EARTH",
            payment_years=5,
        )
        rfc_ug = res_ug["rights_fee_computation"]
        expected_ug = q * g * 0.9 * (r / 100.0)
        assert rfc_ug["total_mineral_rights_fee_vnd"] == expected_ug
        assert rfc_ug["annual_installment_vnd"] == expected_ug / 5.0

    def test_calculate_resource_royalty_tax(self, engine: MiningEngine) -> None:
        volume = 20000.0
        price = 850000000.0
        rate = 18.0  # Rare Earth rate 18%

        res = engine.calculate_resource_royalty_tax(
            license_id="LIC-001",
            tax_period="2026-Q1",
            actual_mined_volume=volume,
            mineral_type="RARE_EARTH",
            taxable_unit_price_vnd=price,
        )
        assert res["ok"] is True
        assert res["tax_id"].startswith("TAX-RES-")
        rd = res["royalty_declaration"]
        assert rd["payable_royalty_tax_vnd"] == volume * price * (rate / 100.0)
        assert rd["royalty_tax_rate_pct"] == 18.0

    def test_audit_environmental_rehabilitation(self, engine: MiningEngine) -> None:
        cost = 20000000000.0  # 20 billion VND

        # Compliant case: deposit >= 25%, pH in [6.0, 9.0], TSS <= 50
        res_pass = engine.audit_environmental_rehabilitation(
            license_id="LIC-001",
            total_rehab_estimate_vnd=cost,
            initial_deposit_pct=25.0,
            replanted_trees_count=20000,
            wastewater_ph=7.4,
            wastewater_tss_mg_l=35.0,
        )
        assert res_pass["ok"] is True
        assert res_pass["environmental_escrow"]["initial_deposit_vnd"] == cost * 0.25
        assert res_pass["effluent_and_greening"]["is_qcvn40_compliant"] is True
        assert res_pass["effluent_and_greening"]["verdict"] == "ENVIRONMENTAL_REHABILITATION_COMPLIANT"

        # Non-compliant case: wastewater pH acid excursion (pH = 4.5 < 6.0)
        res_fail = engine.audit_environmental_rehabilitation(
            license_id="LIC-001",
            total_rehab_estimate_vnd=cost,
            initial_deposit_pct=20.0,  # Below 25% gets clamped to 25%
            replanted_trees_count=5000,
            wastewater_ph=4.5,
            wastewater_tss_mg_l=65.0,  # Exceeds 50
        )
        assert res_fail["effluent_and_greening"]["ph_compliant"] is False
        assert res_fail["effluent_and_greening"]["tss_compliant"] is False
        assert res_fail["effluent_and_greening"]["is_qcvn40_compliant"] is False
        assert res_fail["effluent_and_greening"]["verdict"] == "NON_COMPLIANT_EFFLUENT_DETECTED"

    def test_inspect_river_sand_gravel(self, engine: MiningEngine) -> None:
        # Daytime 10:30 with GPS and camera -> Compliant
        res_pass = engine.inspect_river_sand_gravel(
            license_id="LIC-SAND-01",
            vessel_plate="SG-9988",
            operation_time_hh_mm="10:30",
            is_gps_installed=True,
            is_dock_camera_installed=True,
            measured_cargo_m3=280.0,
        )
        assert res_pass["ok"] is True
        assert res_pass["vessel_audit"]["is_within_daytime_hours"] is True
        assert res_pass["vessel_audit"]["is_fully_compliant"] is True
        assert res_pass["vessel_audit"]["status"] == "RIVER_SAND_MINING_APPROVED"

        # Nighttime 21:00 -> Violation under Decree 23/2020
        res_night = engine.inspect_river_sand_gravel(
            license_id="LIC-SAND-01",
            vessel_plate="SG-9988",
            operation_time_hh_mm="21:15",
            is_gps_installed=True,
            is_dock_camera_installed=True,
        )
        assert res_night["vessel_audit"]["is_within_daytime_hours"] is False
        assert res_night["vessel_audit"]["is_fully_compliant"] is False
        assert res_night["vessel_audit"]["status"] == "VIOLATION_NĐ_23_2020_DETECTED"

    def test_list_and_status(self, engine: MiningEngine) -> None:
        # Register and process operations
        lic = engine.register_mining_license("Test Quarry")
        engine.calculate_mineral_rights_fee(lic["license_id"])
        engine.calculate_resource_royalty_tax(lic["license_id"])
        engine.audit_environmental_rehabilitation(lic["license_id"])
        engine.inspect_river_sand_gravel(lic["license_id"], "DN-1234")

        assert len(engine.list_mining_licenses()) >= 1
        assert len(engine.list_mineral_rights_fees()) >= 1
        assert len(engine.list_resource_royalty_taxes()) >= 1
        assert len(engine.list_environmental_rehabilitations()) >= 1
        assert len(engine.list_river_sand_inspections()) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "MiningEngine"
        m = status["metrics"]
        assert m["active_mining_licenses"] >= 1
        assert m["mineral_rights_fees_calculated"] >= 1
        assert m["royalty_tax_declarations"] >= 1
        assert m["environmental_rehab_audits"] >= 1
        assert m["river_sand_inspections_logged"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Suite Tests
# ---------------------------------------------------------------------------


class TestMiningCLI:
    """Test CLI commands under `mekong mining`."""

    @pytest.fixture
    def app(self) -> typing.Any:
        return build_app()

    def test_cli_main_and_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["mining", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["engine"] == "MiningEngine"

    def test_cli_license(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "mining",
                "license",
                "Mỏ Bauxit Nhân Cơ",
                "--type",
                "BAUXITE",
                "--enterprise",
                "Vinacomin Bauxite",
                "--reserve",
                "15000000",
                "--capacity",
                "650000",
                "--method",
                "OPEN_PIT",
                "--area",
                "120.0",
                "--province",
                "Đắk Nông",
                "--duration",
                "30",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["statutory_jurisdiction"]["licensing_authority"] == "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG"

    def test_cli_rights_fee(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "mining",
                "rights-fee",
                "LIC-TEST01",
                "--reserve",
                "5000000",
                "--price",
                "650000",
                "--method",
                "OPEN_PIT",
                "--type",
                "BAUXITE",
                "--installments",
                "10",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["rights_fee_computation"]["method_coefficient_K"] == 1.0

    def test_cli_royalty(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "mining",
                "royalty",
                "LIC-TEST01",
                "--period",
                "2026-Q1",
                "--volume",
                "45000",
                "--type",
                "BAUXITE",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["royalty_declaration"]["royalty_tax_rate_pct"] == 12.0

    def test_cli_rehab(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "mining",
                "rehab",
                "LIC-TEST01",
                "--cost",
                "18000000000",
                "--deposit-pct",
                "30",
                "--trees",
                "25000",
                "--ph",
                "7.1",
                "--tss",
                "28.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["effluent_and_greening"]["is_qcvn40_compliant"] is True

    def test_cli_sand(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "mining",
                "sand",
                "LIC-SAND-01",
                "SG-5566",
                "--time",
                "09:45",
                "--gps",
                "--camera",
                "--cargo",
                "260",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["vessel_audit"]["is_fully_compliant"] is True

    def test_cli_list_and_status(self, app: typing.Any) -> None:
        res_list = runner.invoke(app, ["mining", "list", "licenses", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.stdout)
        assert isinstance(data_list, list)

        res_status = runner.invoke(app, ["mining", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.stdout)
        assert data_status["ok"] is True


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestMiningMCP:
    """Test MCP tool handlers on scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_server_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_mining_license,
            handle_mining_list,
            handle_mining_rehab,
            handle_mining_rights_fee,
            handle_mining_royalty,
            handle_mining_sand,
            handle_mining_status,
        )

        # 1. License
        res_lic = json.loads(handle_mining_license({"mine_name": "MCP Titanium Mine", "mineral_type": "TITANIUM"}))
        assert res_lic["ok"] is True
        lic_id = res_lic["license_id"]

        # 2. Rights Fee
        res_fee = json.loads(handle_mining_rights_fee({"license_id": lic_id, "reserve_volume": 1000000, "mineral_type": "TITANIUM"}))
        assert res_fee["ok"] is True

        # 3. Royalty
        res_roy = json.loads(handle_mining_royalty({"license_id": lic_id, "actual_mined_volume": 20000, "mineral_type": "TITANIUM"}))
        assert res_roy["ok"] is True

        # 4. Rehab
        res_reh = json.loads(handle_mining_rehab({"license_id": lic_id, "wastewater_ph": 7.3, "wastewater_tss_mg_l": 30}))
        assert res_reh["ok"] is True

        # 5. Sand
        res_sand = json.loads(handle_mining_sand({"license_id": lic_id, "vessel_plate": "DN-8888", "operation_time_hh_mm": "14:20"}))
        assert res_sand["ok"] is True

        # 6. List
        res_list = json.loads(handle_mining_list({"category": "licenses"}))
        assert isinstance(res_list, list)

        # 7. Status
        res_stat = json.loads(handle_mining_status({}))
        assert res_stat["ok"] is True

    def test_core_mcp_server_methods(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. License
        res_lic = json.loads(server._handle_mining_license("Core MCP Coal Mine", mineral_type="COAL_ENERGY"))
        assert res_lic["ok"] is True
        lic_id = res_lic["license_id"]

        # 2. Rights Fee
        res_fee = json.loads(server._handle_mining_rights_fee(lic_id, reserve_volume=500000, mineral_type="COAL_ENERGY"))
        assert res_fee["ok"] is True

        # 3. Royalty
        res_roy = json.loads(server._handle_mining_royalty(lic_id, "2026-Q1", 25000, "COAL_ENERGY"))
        assert res_roy["ok"] is True

        # 4. Rehab
        res_reh = json.loads(server._handle_mining_rehab(lic_id, 8000000000.0, 25.0, 10000, 7.0, 40.0))
        assert res_reh["ok"] is True

        # 5. Sand
        res_sand = json.loads(server._handle_mining_sand(lic_id, "QN-1234", "11:00", True, True, 200.0))
        assert res_sand["ok"] is True

        # 6. List
        res_list = json.loads(server._handle_mining_list("licenses"))
        assert isinstance(res_list, list)

        # 7. Status
        res_stat = json.loads(server._handle_mining_status())
        assert res_stat["ok"] is True
