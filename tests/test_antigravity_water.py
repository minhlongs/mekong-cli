# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Clean Water Supply, Drainage, Wastewater & Tariff Regulations (Phase 69)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.water_engine import (
    DEFAULT_TARIFF_RATES,
    WASTEWATER_STANDARDS_BTNMT,
    WATER_QUALITY_STANDARDS_BYT,
    WaterEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestWaterCoreBoundary:
    """Ensure WaterEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/water_engine.py")
        assert source_path.exists(), "water_engine.py must exist"

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


class TestWaterEngine:
    """Test WaterEngine plant registration, QCVN 01 audit, tiered billing, NRW loss, and wastewater."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> WaterEngine:
        db_file = tmp_path / "test_water.db"
        return WaterEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Check drinking water quality limits (QCVN 01-1:2018/BYT)
        assert WATER_QUALITY_STANDARDS_BYT["ph_min"] == 6.0
        assert WATER_QUALITY_STANDARDS_BYT["ph_max"] == 8.5
        assert WATER_QUALITY_STANDARDS_BYT["turbidity_max_ntu"] == 2.0
        assert WATER_QUALITY_STANDARDS_BYT["residual_chlorine_min_mg_l"] == 0.2
        assert WATER_QUALITY_STANDARDS_BYT["residual_chlorine_max_mg_l"] == 1.0
        assert WATER_QUALITY_STANDARDS_BYT["coliform_max_cfu"] == 3.0
        assert WATER_QUALITY_STANDARDS_BYT["e_coli_max_cfu"] == 0.0

        # Check industrial wastewater standards (QCVN 40:2011/BTNMT)
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_A"]["bod5_max"] == 30.0
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_A"]["cod_max"] == 75.0
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_A"]["tss_max"] == 50.0
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_B"]["bod5_max"] == 50.0
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_B"]["cod_max"] == 150.0
        assert WASTEWATER_STANDARDS_BTNMT["COLUMN_B"]["tss_max"] == 100.0

        # Check statutory tariffs (Circular 44/2021/TT-BTC)
        tiers = DEFAULT_TARIFF_RATES["DOMESTIC_TIERS"]
        assert tiers[0]["rate_vnd"] == 8500.0
        assert tiers[1]["rate_vnd"] == 10500.0
        assert tiers[2]["rate_vnd"] == 13000.0
        assert tiers[3]["rate_vnd"] == 16000.0
        assert DEFAULT_TARIFF_RATES["ADMINISTRATIVE"] == 11500.0
        assert DEFAULT_TARIFF_RATES["PUBLIC_SERVICE"] == 12000.0
        assert DEFAULT_TARIFF_RATES["MANUFACTURING"] == 14000.0
        assert DEFAULT_TARIFF_RATES["COMMERCIAL"] == 22000.0
        assert DEFAULT_TARIFF_RATES["WASTEWATER_FEE_PCT"] == 10.0
        assert DEFAULT_TARIFF_RATES["VAT_PCT"] == 5.0

    def test_register_water_plant(self, engine: WaterEngine) -> None:
        res = engine.register_water_plant(
            plant_name="Nhà máy Nước Thủ Đức",
            capacity_m3_day=750000.0,
            water_source="Sông Đồng Nai (Nước mặt)",
            province="TP. Hồ Chí Minh",
            technology="Keo tụ tạo bông + Lắng cát + Lọc nhanh + Khử trùng Clo",
            operator_name="SAWACO",
        )
        assert res["ok"] is True
        assert res["plant_id"].startswith("PLT-")
        prof = res["plant_profile"]
        assert prof["plant_name"] == "Nhà máy Nước Thủ Đức"
        assert prof["capacity_m3_day"] == 750000.0
        assert prof["annual_capacity_m3"] == 750000.0 * 365
        assert prof["operator_name"] == "SAWACO"
        assert prof["is_operational"] is True

        plants = engine.list_water_plants()
        assert len(plants) == 1
        assert plants[0]["plant_name"] == "Nhà máy Nước Thủ Đức"

    def test_audit_water_quality_compliant(self, engine: WaterEngine) -> None:
        res = engine.audit_water_quality_qcvn01(
            plant_id="PLT-TEST-001",
            sample_location="Đài cấp nước trạm bơm 2",
            ph_level=7.3,
            turbidity_ntu=0.65,
            residual_chlorine_mg_l=0.45,
            coliform_cfu=0.0,
            e_coli_cfu=0.0,
            heavy_metal_pass=True,
            tested_by="Viện Pasteur TP.HCM",
        )
        assert res["ok"] is True
        assert res["test_id"].startswith("TST-")
        audit = res["quality_audit"]
        assert audit["is_qcvn01_compliant"] is True
        assert audit["safety_verdict"] == "SAFE_FOR_DOMESTIC_USE"

    def test_audit_water_quality_non_compliant(self, engine: WaterEngine) -> None:
        res = engine.audit_water_quality_qcvn01(
            plant_id="PLT-TEST-002",
            sample_location="Bể chứa sau xử lý",
            ph_level=5.5,  # Low pH
            turbidity_ntu=3.2,  # High turbidity
            residual_chlorine_mg_l=0.1,  # Low chlorine
            coliform_cfu=5.0,  # Coliform > 3
            e_coli_cfu=2.0,  # E. coli > 0
            heavy_metal_pass=False,
            tested_by="Trung tâm Y tế Dự phòng",
        )
        assert res["ok"] is True
        audit = res["quality_audit"]
        assert audit["is_qcvn01_compliant"] is False
        assert audit["safety_verdict"] == "UNSAFE_WATER_QUALITY_DEFECTS"
        p = audit["parameters"]
        assert p["ph_compliant"] is False
        assert p["turbidity_compliant"] is False
        assert p["chlorine_compliant"] is False
        assert p["coliform_compliant"] is False
        assert p["e_coli_compliant"] is False
        assert p["heavy_metal_pass"] is False

    def test_calculate_water_bill_domestic_progressive(self, engine: WaterEngine) -> None:
        # Test 25 m3 consumption:
        # Tier 1 (0-10 m3): 10 * 8,500 = 85,000 VND
        # Tier 2 (10-20 m3): 10 * 10,500 = 105,000 VND
        # Tier 3 (20-30 m3): 5 * 13,000 = 65,000 VND
        # Base water cost = 85,000 + 105,000 + 65,000 = 255,000 VND
        # Wastewater fee (10%) = 25,500 VND
        # Subtotal before VAT = 280,500 VND
        # VAT (5% on base water) = 255,000 * 0.05 = 12,750 VND
        # Total payable = 255,000 + 25,500 + 12,750 = 293,250 VND
        res = engine.calculate_water_bill(
            customer_code="KH-DOM-101",
            customer_name="Hộ gia đình Lê Văn C",
            consumption_m3=25.0,
            customer_category="DOMESTIC",
            billing_month="2026-03",
        )
        assert res["ok"] is True
        inv = res["billing_invoice"]
        assert inv["customer_code"] == "KH-DOM-101"
        assert inv["consumption_m3"] == 25.0
        assert inv["base_water_cost_vnd"] == 255000.0
        assert inv["wastewater_service_fee_vnd"] == 25500.0
        assert inv["vat_amount_vnd"] == 12750.0
        assert inv["total_payable_vnd"] == 293250.0
        assert len(inv["tier_breakdown"]) == 3

    def test_calculate_water_bill_commercial_flat(self, engine: WaterEngine) -> None:
        # Commercial rate: 22,000 VND/m3
        # Consumption: 100 m3 -> Base = 2,200,000 VND
        # Wastewater fee (10%) = 220,000 VND
        # VAT (5%) = 110,000 VND
        # Total = 2,530,000 VND
        res = engine.calculate_water_bill(
            customer_code="KH-COM-202",
            customer_name="Khách sạn Grand Saigon",
            consumption_m3=100.0,
            customer_category="COMMERCIAL",
            billing_month="2026-03",
        )
        assert res["ok"] is True
        inv = res["billing_invoice"]
        assert inv["base_water_cost_vnd"] == 2200000.0
        assert inv["wastewater_service_fee_vnd"] == 220000.0
        assert inv["vat_amount_vnd"] == 110000.0
        assert inv["total_payable_vnd"] == 2530000.0

    def test_calculate_water_bill_manufacturing(self, engine: WaterEngine) -> None:
        # Manufacturing rate: 14,000 VND/m3
        # Consumption: 500 m3 -> Base = 7,000,000 VND
        # Wastewater fee (10%) = 700,000 VND
        # VAT (5%) = 350,000 VND
        # Total = 8,050,000 VND
        res = engine.calculate_water_bill(
            customer_code="KH-MFG-303",
            customer_name="Công ty Chế biến Thực phẩm Á Châu",
            consumption_m3=500.0,
            customer_category="MANUFACTURING",
        )
        assert res["ok"] is True
        inv = res["billing_invoice"]
        assert inv["base_water_cost_vnd"] == 7000000.0
        assert inv["total_payable_vnd"] == 8050000.0

    def test_audit_nrw_loss_within_target(self, engine: WaterEngine) -> None:
        # Produced: 2,000,000 m3, Billed: 1,760,000 m3
        # Loss: 240,000 m3 -> NRW: 12.00% <= 15.0% target -> Achieved
        res = engine.audit_nrw_loss(
            plant_id="PLT-BIWASE-01",
            produced_volume_m3=2000000.0,
            billed_volume_m3=1760000.0,
            audit_period="2026-Q1",
            target_max_pct=15.0,
        )
        assert res["ok"] is True
        n = res["nrw_telemetry"]
        assert n["nrw_percentage"] == 12.0
        assert n["water_loss_volume_m3"] == 240000.0
        assert n["is_target_achieved"] is True
        assert n["performance_rating"] in ("EXCELLENT", "SATISFACTORY")

    def test_audit_nrw_loss_exceeding_target(self, engine: WaterEngine) -> None:
        # Produced: 1,000,000 m3, Billed: 780,000 m3
        # Loss: 220,000 m3 -> NRW: 22.00% > 15.0% target -> Exceeded
        res = engine.audit_nrw_loss(
            plant_id="PLT-OLD-01",
            produced_volume_m3=1000000.0,
            billed_volume_m3=780000.0,
            audit_period="2026-Q1",
            target_max_pct=15.0,
            notes="Mạng lưới ống cũ mục vỡ tại khu vực quận cũ",
        )
        assert res["ok"] is True
        n = res["nrw_telemetry"]
        assert n["nrw_percentage"] == 22.0
        assert n["is_target_achieved"] is False
        assert n["performance_rating"] == "HIGH_LEAKAGE_CRITICAL"

    def test_inspect_wastewater_discharge_column_a_pass(self, engine: WaterEngine) -> None:
        res = engine.inspect_wastewater_discharge(
            facility_name="Nhà máy Điện tử VSIP",
            industrial_park="KCN VSIP II",
            daily_flow_m3=1500.0,
            standard_column="COLUMN_A",
            bod5_mg_l=22.0,  # <= 30
            cod_mg_l=65.0,   # <= 75
            tss_mg_l=40.0,   # <= 50
            ammonium_mg_l=3.0,  # <= 5.0
            ph_level=7.2,    # 6.0 - 9.0
        )
        assert res["ok"] is True
        disp = res["effluent_inspection"]
        assert disp["is_discharge_compliant"] is True
        assert disp["discharge_verdict"] == "PERMITTED_TO_DISCHARGE"

    def test_inspect_wastewater_discharge_column_a_fail(self, engine: WaterEngine) -> None:
        res = engine.inspect_wastewater_discharge(
            facility_name="Cơ sở Dệt Nhuộm Nam Hưng",
            industrial_park="Cụm Công nghiệp Tân Bình",
            daily_flow_m3=800.0,
            standard_column="COLUMN_A",
            bod5_mg_l=45.0,  # > 30 (fails Column A)
            cod_mg_l=110.0,  # > 75 (fails Column A)
            tss_mg_l=60.0,   # > 50 (fails Column A)
            ammonium_mg_l=8.0,  # > 5.0
            ph_level=5.2,    # < 6.0
        )
        assert res["ok"] is True
        disp = res["effluent_inspection"]
        assert disp["is_discharge_compliant"] is False
        assert disp["discharge_verdict"] == "NON_COMPLIANT_DISCHARGE_VIOLATION"

    def test_inspect_wastewater_discharge_column_b_pass(self, engine: WaterEngine) -> None:
        # Values that fail Column A but pass Column B
        res = engine.inspect_wastewater_discharge(
            facility_name="Nhà máy Giày Da Long An",
            industrial_park="KCN Thuận Đạo",
            daily_flow_m3=2000.0,
            standard_column="COLUMN_B",
            bod5_mg_l=42.0,  # <= 50 (Passes Column B, fails Column A)
            cod_mg_l=130.0,  # <= 150 (Passes Column B, fails Column A)
            tss_mg_l=85.0,   # <= 100 (Passes Column B, fails Column A)
            ammonium_mg_l=7.5, # <= 10.0
            ph_level=6.8,
        )
        assert res["ok"] is True
        disp = res["effluent_inspection"]
        assert disp["is_discharge_compliant"] is True
        assert disp["applicable_standard"] == "QCVN 40:2011/BTNMT (COLUMN_B)"

    def test_list_and_get_status_aggregation(self, engine: WaterEngine) -> None:
        # Register a plant
        engine.register_water_plant("Trạm Nước A", 30000.0)
        # Test water quality
        engine.audit_water_quality_qcvn01("PLT-A", "Trạm bơm", 7.0, 1.0, 0.5, 0.0, 0.0, True)
        # Bill
        engine.calculate_water_bill("KH01", "Dân cư", 20.0, "DOMESTIC")
        # NRW
        engine.audit_nrw_loss("PLT-A", 100000.0, 88000.0)
        # Wastewater
        engine.inspect_wastewater_discharge("Xưởng A", "KCN B", 500.0, "COLUMN_A", 20.0, 50.0, 30.0, 2.0, 7.0)

        # Verify listing
        assert len(engine.list_water_plants()) == 1
        assert len(engine.list_water_quality_tests()) == 1
        assert len(engine.list_tariff_bills()) == 1
        assert len(engine.list_nrw_audits()) == 1
        assert len(engine.list_wastewater_discharges()) == 1

        # Verify status metrics
        st = engine.get_status()
        assert st["ok"] is True
        m = st["metrics"]
        assert m["registered_water_plants"] == 1
        assert m["total_water_capacity_m3_day"] == 30000.0
        assert m["water_quality_tests_conducted"] == 1
        assert m["qcvn01_compliant_tests"] == 1
        assert m["water_bills_issued"] == 1
        assert m["total_consumption_m3"] == 20.0
        assert m["nrw_audits_performed"] == 1
        assert m["wastewater_discharges_inspected"] == 1
        assert m["qcvn40_compliant_discharges"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestWaterCLI:
    """Test Typer CLI surface for mekong water."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_main_status(self, app) -> None:
        result = runner.invoke(app, ["water", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_plant(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "water",
                "plant",
                "Nhà máy Nước Dĩ An",
                "--capacity",
                "100000",
                "--source",
                "Sông Sài Gòn",
                "--province",
                "Bình Dương",
                "--tech",
                "Lọc cát nhanh + Ozon hóa",
                "--operator",
                "BIWASE",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["plant_profile"]["capacity_m3_day"] == 100000.0

    def test_cli_test_qcvn01(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "water",
                "test",
                "PLT-CLI-01",
                "--location",
                "Trạm trung chuyển",
                "--ph",
                "7.5",
                "--turbidity",
                "1.1",
                "--chlorine",
                "0.6",
                "--coliform",
                "0",
                "--ecoli",
                "0",
                "--metal-pass",
                "--tester",
                "CDC Bình Dương",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["quality_audit"]["is_qcvn01_compliant"] is True

    def test_cli_bill(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "water",
                "bill",
                "KH-CLI-99",
                "Căn Hộ Landmark",
                "35",
                "--category",
                "DOMESTIC",
                "--month",
                "2026-03",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["billing_invoice"]["consumption_m3"] == 35.0

    def test_cli_nrw(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "water",
                "nrw",
                "PLT-CLI-01",
                "--produced",
                "1000000",
                "--billed",
                "860000",
                "--period",
                "2026-Q1",
                "--target",
                "15.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["nrw_telemetry"]["nrw_percentage"] == 14.0
        assert data["nrw_telemetry"]["is_target_achieved"] is True

    def test_cli_discharge(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "water",
                "discharge",
                "Công ty Điện Cơ Sài Gòn",
                "--park",
                "KCN Linh Trung",
                "--flow",
                "1000",
                "--column",
                "COLUMN_A",
                "--bod5",
                "25.0",
                "--cod",
                "60.0",
                "--tss",
                "40.0",
                "--ammonium",
                "3.0",
                "--ph",
                "7.2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["effluent_inspection"]["is_discharge_compliant"] is True

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["water", "list", "plants", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "plants" in data


# ---------------------------------------------------------------------------
# MCP Integration Tests
# ---------------------------------------------------------------------------


class TestWaterMCP:
    """Test MCP server tool handlers and FastMCP parity for water."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_water_plant,
            handle_water_test,
            handle_water_bill,
            handle_water_nrw,
            handle_water_discharge,
            handle_water_list,
            handle_water_status,
        )

        # Plant
        res_plant = json.loads(handle_water_plant({"name": "Nhà máy Nước MCP"}))
        assert res_plant["ok"] is True

        # Test
        res_test = json.loads(handle_water_test({"plant_id": "PLT-MCP-01"}))
        assert res_test["ok"] is True

        # Bill
        res_bill = json.loads(handle_water_bill({"code": "KH-MCP", "name": "Khách Hàng MCP", "volume": 30.0}))
        assert res_bill["ok"] is True

        # NRW
        res_nrw = json.loads(handle_water_nrw({"plant_id": "PLT-MCP-01", "produced": 1000000, "billed": 880000}))
        assert res_nrw["ok"] is True

        # Discharge
        res_dis = json.loads(handle_water_discharge({"facility": "Cơ Sở MCP"}))
        assert res_dis["ok"] is True

        # List & Status
        res_lst = json.loads(handle_water_list({"category": "plants"}))
        assert isinstance(res_lst, list)

        res_st = json.loads(handle_water_status({}))
        assert res_st["ok"] is True

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Plant
        res_p = json.loads(server._handle_water_plant(plant_name="Nhà máy Nước Core MCP"))
        assert res_p["ok"] is True

        # Test
        res_t = json.loads(server._handle_water_test(plant_id="PLT-CORE-01"))
        assert res_t["ok"] is True

        # Bill
        res_b = json.loads(server._handle_water_bill(customer_code="KH-CORE", customer_name="Khách Core", consumption_m3=20.0))
        assert res_b["ok"] is True

        # NRW
        res_n = json.loads(server._handle_water_nrw(plant_id="PLT-CORE-01", produced_volume_m3=500000, billed_volume_m3=450000))
        assert res_n["ok"] is True

        # Discharge
        res_d = json.loads(server._handle_water_discharge(facility_name="Cơ Sở Core"))
        assert res_d["ok"] is True

        # List
        res_l = json.loads(server._handle_water_list(category="plants"))
        assert isinstance(res_l, list)

        # Status
        res_s = json.loads(server._handle_water_status())
        assert res_s["ok"] is True
