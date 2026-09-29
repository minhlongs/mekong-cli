# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Petroleum Trading, Fuel Reserves & Retail Price Stabilization (Phase 64)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.petrol_engine import (
    MANDATORY_RESERVE_DAYS,
    PETROLEUM_PRODUCTS,
    PetrolEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPetrolCoreBoundary:
    """Ensure PetrolEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/petrol_engine.py")
        assert source_path.exists(), "petrol_engine.py must exist"

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


class TestPetrolEngine:
    """Test PetrolEngine base price calculations, fuel reserve audits, Euro 4/5 quality, and pump telemetry."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PetrolEngine:
        db_file = tmp_path / "test_petrol.db"
        return PetrolEngine(db_path=db_file)

    def test_constants_and_regulatory_baselines(self) -> None:
        assert "RON95_III" in PETROLEUM_PRODUCTS
        assert "E5_RON92" in PETROLEUM_PRODUCTS
        assert "DIESEL_005S" in PETROLEUM_PRODUCTS
        assert "KEROSENE" in PETROLEUM_PRODUCTS
        assert "MAZUT_180CST" in PETROLEUM_PRODUCTS

        assert PETROLEUM_PRODUCTS["RON95_III"]["excise_tax_pct"] == 10.0
        assert PETROLEUM_PRODUCTS["E5_RON92"]["excise_tax_pct"] == 8.0
        assert PETROLEUM_PRODUCTS["DIESEL_005S"]["excise_tax_pct"] == 0.0

        assert PETROLEUM_PRODUCTS["RON95_III"]["env_tax_vnd_per_unit"] == 2000.0
        assert PETROLEUM_PRODUCTS["DIESEL_005S"]["env_tax_vnd_per_unit"] == 1000.0
        assert PETROLEUM_PRODUCTS["KEROSENE"]["env_tax_vnd_per_unit"] == 600.0

        assert MANDATORY_RESERVE_DAYS["KEY_IMPORTER"] == 20
        assert MANDATORY_RESERVE_DAYS["DISTRIBUTOR"] == 5
        assert MANDATORY_RESERVE_DAYS["DOMESTIC_REFINERY"] == 30

    def test_calculate_fuel_base_and_retail_price(self, engine: PetrolEngine) -> None:
        res = engine.calculate_fuel_base_and_retail_price(
            product_code="RON95_III",
            mops_platts_usd_per_barrel=92.50,
            import_duty_pct=10.0,
            bog_fund_deduction_vnd=0.0,
            bog_fund_expenditure_vnd=0.0,
            cycle_date="2026-10-01",
        )
        assert res["ok"] is True
        assert res["adjustment_id"].startswith("ADJ-")

        fp = res["fuel_product"]
        assert fp["product_code"] == "RON95_III"
        assert fp["unit"] == "LITER"

        sb = res["statutory_price_breakdown_vnd"]
        assert sb["import_duty_vnd"] > 0
        assert sb["excise_tax_vnd"] > 0
        assert sb["environmental_tax_vnd"] == 2000
        assert sb["calculated_base_price_vnd"] > 0

        rc = res["retail_ceiling_prices_vnd"]
        assert rc["retail_zone_1_vnd"] > 0
        assert rc["retail_zone_2_vnd"] > rc["retail_zone_1_vnd"]
        # Zone 2 is exactly 102% of Zone 1
        assert rc["retail_zone_2_vnd"] == round(rc["retail_zone_1_vnd"] * 1.02)

    def test_calculate_price_with_bog_fund(self, engine: PetrolEngine) -> None:
        # Case with BOG deduction (quỹ bình ổn thu thêm)
        res_deduct = engine.calculate_fuel_base_and_retail_price(
            product_code="E5_RON92",
            mops_platts_usd_per_barrel=85.0,
            bog_fund_deduction_vnd=300.0,
            bog_fund_expenditure_vnd=0.0,
        )
        base = res_deduct["statutory_price_breakdown_vnd"]["calculated_base_price_vnd"]
        assert res_deduct["retail_ceiling_prices_vnd"]["retail_zone_1_vnd"] == base + 300

        # Case with BOG expenditure (quỹ bình ổn chi sử dụng)
        res_expend = engine.calculate_fuel_base_and_retail_price(
            product_code="E5_RON92",
            mops_platts_usd_per_barrel=85.0,
            bog_fund_deduction_vnd=0.0,
            bog_fund_expenditure_vnd=500.0,
        )
        assert res_expend["retail_ceiling_prices_vnd"]["retail_zone_1_vnd"] == base - 500

    def test_audit_national_fuel_reserves_compliant(self, engine: PetrolEngine) -> None:
        res = engine.audit_national_fuel_reserves(
            enterprise_name="Tập đoàn Xăng dầu Việt Nam (Petrolimex)",
            enterprise_type="KEY_IMPORTER",
            storage_capacity_m3=150000.0,
            current_stock_m3=100000.0,
            daily_consumption_m3=4000.0,
        )
        assert res["ok"] is True
        assert res["reserve_id"].startswith("RES-")

        rm = res["reserve_metrics"]
        assert rm["statutory_required_days"] == 20
        assert rm["actual_reserve_days"] == 25.0
        assert rm["is_reserve_compliant"] is True
        assert rm["stock_deficit_m3"] == 0.0
        assert rm["audit_verdict"] == "RESERVE_COMPLIANT"

    def test_audit_national_fuel_reserves_deficit(self, engine: PetrolEngine) -> None:
        # Stock only suffices for 12 days (required 20 days)
        res = engine.audit_national_fuel_reserves(
            enterprise_name="Thương nhân Đầu mối X",
            enterprise_type="KEY_IMPORTER",
            storage_capacity_m3=80000.0,
            current_stock_m3=36000.0,
            daily_consumption_m3=3000.0,
        )
        rm = res["reserve_metrics"]
        assert rm["actual_reserve_days"] == 12.0
        assert rm["is_reserve_compliant"] is False
        assert rm["stock_deficit_m3"] == 24000.0  # (20 * 3000) - 36000
        assert rm["audit_verdict"] == "RESERVE_DEFICIT_WARNING"

    def test_audit_distributor_and_refinery_reserves(self, engine: PetrolEngine) -> None:
        # Distributor: 5 days required
        res_dist = engine.audit_national_fuel_reserves(
            enterprise_name="Công ty Cổ phần Phân phối Y",
            enterprise_type="DISTRIBUTOR",
            storage_capacity_m3=10000.0,
            current_stock_m3=6000.0,
            daily_consumption_m3=1000.0,
        )
        assert res_dist["reserve_metrics"]["statutory_required_days"] == 5
        assert res_dist["reserve_metrics"]["actual_reserve_days"] == 6.0
        assert res_dist["reserve_metrics"]["is_reserve_compliant"] is True

        # Refinery: 30 days required
        res_ref = engine.audit_national_fuel_reserves(
            enterprise_name="Nhà máy Lọc dầu Dung Quất (BSR)",
            enterprise_type="DOMESTIC_REFINERY",
            storage_capacity_m3=500000.0,
            current_stock_m3=650000.0,
            daily_consumption_m3=20000.0,
        )
        assert res_ref["reserve_metrics"]["statutory_required_days"] == 30
        assert res_ref["reserve_metrics"]["actual_reserve_days"] == 32.5
        assert res_ref["reserve_metrics"]["is_reserve_compliant"] is True

    def test_inspect_fuel_quality(self, engine: PetrolEngine) -> None:
        # Euro 5 compliant sample (<=10 ppm sulfur, 0.0 lead)
        res_e5 = engine.inspect_fuel_quality(
            gas_station_id="ST-001",
            gas_station_name="Cửa hàng Xăng dầu Số 1",
            product_code="RON95_III",
            sulfur_content_ppm=8.5,
            lead_content_g_l=0.0,
        )
        assert res_e5["ok"] is True
        la_e5 = res_e5["laboratory_analysis"]
        assert la_e5["sulfur_compliant"] is True
        assert la_e5["lead_compliant"] is True
        assert la_e5["verified_emission_tier"] == "EURO_5_LEVEL_5"
        assert res_e5["quality_verdict"]["is_quality_compliant"] is True

        # Euro 4 compliant sample (<=50 ppm sulfur)
        res_e4 = engine.inspect_fuel_quality(
            gas_station_id="ST-002",
            gas_station_name="Cửa hàng Xăng dầu Số 2",
            product_code="DIESEL_005S",
            sulfur_content_ppm=42.0,
            lead_content_g_l=0.0,
        )
        assert res_e4["laboratory_analysis"]["verified_emission_tier"] == "EURO_4_LEVEL_4"
        assert res_e4["quality_verdict"]["is_quality_compliant"] is True

        # Substandard violation (excessive sulfur > 50 ppm for RON 95)
        res_sub = engine.inspect_fuel_quality(
            gas_station_id="ST-003",
            gas_station_name="Cửa hàng Vi phạm",
            product_code="RON95_III",
            sulfur_content_ppm=180.0,
            lead_content_g_l=0.01,
        )
        assert res_sub["quality_verdict"]["is_quality_compliant"] is False
        assert res_sub["quality_verdict"]["status"] == "QUALITY_SUBSTANDARD_VIOLATION"

    def test_report_pump_einvoice_telemetry(self, engine: PetrolEngine) -> None:
        # 100% compliance test under Official Telegram 1284/CD-TTg
        res_full = engine.report_pump_einvoice_telemetry(
            station_id="ST-PETROL-01",
            pump_count=8,
            daily_transactions=1500,
            daily_volume_liters=12000.0,
            daily_revenue_vnd=285000000.0,
            e_invoices_issued=1500,
        )
        assert res_full["ok"] is True
        assert res_full["tax_einvoice_compliance"]["compliance_ratio_pct"] == 100.0
        assert res_full["tax_einvoice_compliance"]["is_100pct_compliant"] is True
        assert res_full["tax_einvoice_compliance"]["status"] == "E_INVOICE_MANDATE_FULFILLED"

        # Partial compliance test
        res_part = engine.report_pump_einvoice_telemetry(
            station_id="ST-PETROL-02",
            pump_count=4,
            daily_transactions=1000,
            daily_volume_liters=7500.0,
            daily_revenue_vnd=180000000.0,
            e_invoices_issued=850,
        )
        assert res_part["tax_einvoice_compliance"]["compliance_ratio_pct"] == 85.0
        assert res_part["tax_einvoice_compliance"]["is_100pct_compliant"] is False
        assert res_part["tax_einvoice_compliance"]["status"] == "PARTIAL_E_INVOICE_DEFICIT"

    def test_list_records_and_status(self, engine: PetrolEngine) -> None:
        engine.calculate_fuel_base_and_retail_price(product_code="RON95_III", mops_platts_usd_per_barrel=90.0)
        engine.audit_national_fuel_reserves(enterprise_name="Ent A", current_stock_m3=80000, daily_consumption_m3=3000)
        engine.inspect_fuel_quality(gas_station_id="ST-01", gas_station_name="St 01", sulfur_content_ppm=25.0)
        engine.report_pump_einvoice_telemetry(station_id="ST-01", daily_transactions=1000, e_invoices_issued=1000)

        prices = engine.list_price_adjustments()
        reserves = engine.list_fuel_reserves()
        quality = engine.list_quality_inspections()
        pumps = engine.list_pump_telemetry()

        assert len(prices) == 1
        assert len(reserves) == 1
        assert len(quality) == 1
        assert len(pumps) == 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["price_adjustments_recorded"] == 1
        assert status["metrics"]["reserve_facilities_audited"] == 1
        assert status["metrics"]["quality_inspections_conducted"] == 1
        assert status["metrics"]["pump_stations_reporting"] == 1


# ---------------------------------------------------------------------------
# CLI Surface Tests
# ---------------------------------------------------------------------------


class TestPetrolCLI:
    """Test CLI commands for petrol."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_petrol_status(self) -> None:
        res = runner.invoke(self.app, ["petrol", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_petrol_price_json(self) -> None:
        res = runner.invoke(self.app, ["petrol", "price", "RON95_III", "--platts", "94.0", "--duty", "10.0", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["retail_ceiling_prices_vnd"]["retail_zone_1_vnd"] > 0

    def test_cli_petrol_price_console(self) -> None:
        res = runner.invoke(self.app, ["petrol", "price", "E5_RON92", "--platts", "88.0"])
        assert res.exit_code == 0
        assert "Kỳ Điều hành Giá Xăng Dầu" in res.output

    def test_cli_petrol_reserve(self) -> None:
        res = runner.invoke(self.app, [
            "petrol", "reserve", "Petrolimex Tây Nam Bộ",
            "--type", "KEY_IMPORTER",
            "--capacity", "120000",
            "--stock", "90000",
            "--daily", "3500",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["reserve_metrics"]["actual_reserve_days"] == 25.7

    def test_cli_petrol_quality(self) -> None:
        res = runner.invoke(self.app, [
            "petrol", "quality", "CHXD-01", "Cửa hàng Petrolimex 01",
            "--product", "RON95_III",
            "--sulfur", "30.0",
            "--lead", "0.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["quality_verdict"]["is_quality_compliant"] is True

    def test_cli_petrol_pump(self) -> None:
        res = runner.invoke(self.app, [
            "petrol", "pump", "CHXD-01",
            "--pumps", "8",
            "--tx", "1200",
            "--volume", "9500",
            "--revenue", "225000000",
            "--invoices", "1200",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["tax_einvoice_compliance"]["is_100pct_compliant"] is True

    def test_cli_petrol_list(self) -> None:
        res_p = runner.invoke(self.app, ["petrol", "list", "prices", "--json"])
        assert res_p.exit_code == 0
        data_p = json.loads(res_p.output)
        assert data_p["ok"] is True
        assert "prices" in data_p

        res_r = runner.invoke(self.app, ["petrol", "list", "--type", "reserves", "--json"])
        assert res_r.exit_code == 0
        data_r = json.loads(res_r.output)
        assert data_r["ok"] is True
        assert "reserves" in data_r


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestPetrolMCPIntegration:
    """Ensure FastMCP and JSON-RPC fallback handlers execute identically."""

    def test_fastmcp_core_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Price
        p_res = json.loads(server._handle_petrol_price(product_code="RON95_III", mops_platts_usd_per_barrel=92.5))
        assert p_res["ok"] is True

        # 2. Reserve
        r_res = json.loads(server._handle_petrol_reserve(
            enterprise_name="PVOIL Miền Trung",
            enterprise_type="KEY_IMPORTER",
            storage_capacity_m3=60000.0,
            current_stock_m3=45000.0,
            daily_consumption_m3=2000.0,
        ))
        assert r_res["ok"] is True
        assert r_res["reserve_metrics"]["actual_reserve_days"] == 22.5

        # 3. Quality
        q_res = json.loads(server._handle_petrol_quality(
            gas_station_id="ST-PVOIL-10",
            gas_station_name="Cửa hàng PVOIL 10",
            product_code="RON95_III",
            sulfur_content_ppm=35.0,
            lead_content_g_l=0.0,
        ))
        assert q_res["ok"] is True

        # 4. Pump
        m_res = json.loads(server._handle_petrol_pump(
            station_id="ST-PVOIL-10",
            pump_count=6,
            daily_transactions=800,
            daily_volume_liters=6000.0,
            daily_revenue_vnd=145000000.0,
            e_invoices_issued=800,
        ))
        assert m_res["ok"] is True

        # 5. List & Status
        l_res = json.loads(server._handle_petrol_list(item_type="prices"))
        assert isinstance(l_res, list)

        s_res = json.loads(server._handle_petrol_status())
        assert s_res["ok"] is True

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        # Price
        p_res = json.loads(smcp.handle_petrol_price({"product_code": "DIESEL_005S", "mops_platts_usd_per_barrel": 95.0}))
        assert p_res["ok"] is True

        # Reserve
        r_res = json.loads(smcp.handle_petrol_reserve({
            "enterprise_name": "Saigon Petro",
            "enterprise_type": "KEY_IMPORTER",
            "storage_capacity_m3": 80000.0,
            "current_stock_m3": 60000.0,
            "daily_consumption_m3": 2500.0,
        }))
        assert r_res["ok"] is True

        # Quality
        q_res = json.loads(smcp.handle_petrol_quality({
            "gas_station_id": "ST-SP-05",
            "gas_station_name": "Cây xăng Saigon Petro",
            "product_code": "DIESEL_005S",
            "sulfur_content_ppm": 45.0,
            "lead_content_g_l": 0.0,
        }))
        assert q_res["ok"] is True

        # Pump
        m_res = json.loads(smcp.handle_petrol_pump({
            "station_id": "ST-SP-05",
            "pump_count": 4,
            "daily_transactions": 600,
            "daily_volume_liters": 4800.0,
            "daily_revenue_vnd": 110000000.0,
            "e_invoices_issued": 600,
        }))
        assert m_res["ok"] is True

        # List & Status
        l_res = json.loads(smcp.handle_petrol_list({"item_type": "quality"}))
        assert isinstance(l_res, list)

        s_res = json.loads(smcp.handle_petrol_status({}))
        assert s_res["ok"] is True
