# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Environmental, Social & Governance (ESG), Green Transition & Carbon Trading Compliance Engine (Phase 54)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.esg_engine import (
    EMISSION_FACTORS,
    GRID_EMISSION_FACTOR_VIETNAM,
    MANDATORY_REPORTING_THRESHOLD_TCO2E,
    EsgEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestEsgCoreBoundary:
    """Ensure EsgEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/esg_engine.py")
        assert source_path.exists(), "esg_engine.py must exist"

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


class TestEsgEngine:
    """Test EsgEngine GHG accounting, CBAM liability, ESG scoring, and carbon credit trading."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> EsgEngine:
        db_file = tmp_path / "test_esg.db"
        return EsgEngine(db_path=db_file)

    def test_constants_and_factors(self) -> None:
        assert GRID_EMISSION_FACTOR_VIETNAM == 0.7221
        assert MANDATORY_REPORTING_THRESHOLD_TCO2E == 3_000.0
        assert "DIESEL_KG_PER_LITER" in EMISSION_FACTORS
        assert "COAL_TONS_PER_TON" in EMISSION_FACTORS

    def test_calculate_ghg_inventory_below_threshold(self, engine: EsgEngine) -> None:
        # Small facility: 1,000 liters diesel, 50,000 kWh electricity
        res = engine.calculate_ghg_inventory(
            enterprise_name="Green Agri Tech Ltd",
            reporting_year=2026,
            fuel_diesel_liters=1_000.0,
            electricity_kwh=50_000.0,
            scope3_logistics_tco2e=10.0,
        )
        assert res["ok"] is True
        assert res["enterprise_name"] == "Green Agri Tech Ltd"
        assert res["reporting_year"] == 2026
        # Scope 1: 1,000 * 2.68 / 1000 = 2.68 tCO2e
        assert res["breakdown"]["scope_1_direct_tco2e"] == 2.68
        # Scope 2: 50,000 * 0.7221 / 1000 = 36.105 tCO2e
        assert res["breakdown"]["scope_2_indirect_electricity_tco2e"] == 36.105
        assert res["breakdown"]["scope_3_value_chain_tco2e"] == 10.0
        assert res["total_ghg_emissions_tco2e"] < 3_000.0
        assert res["mandatory_reporting_status"]["is_mandatory_reporting_facility"] is False

    def test_calculate_ghg_inventory_above_threshold(self, engine: EsgEngine) -> None:
        # Heavy industry: 1,500 tons of coal (~3,675 tCO2e) + 1,000,000 kWh (~722 tCO2e)
        res = engine.calculate_ghg_inventory(
            enterprise_name="Hai Phong Heavy Steel JSC",
            reporting_year=2026,
            coal_tons=1_500.0,
            electricity_kwh=1_000_000.0,
        )
        assert res["ok"] is True
        assert res["total_ghg_emissions_tco2e"] >= 3_000.0
        assert res["mandatory_reporting_status"]["is_mandatory_reporting_facility"] is True
        assert "BẮT BUỘC KIỂM KÊ" in res["mandatory_reporting_status"]["conclusion"]

    def test_evaluate_cbam_liability(self, engine: EsgEngine) -> None:
        res = engine.evaluate_cbam_liability(
            product_type="STEEL",
            export_volume_tons=1_000.0,
            direct_emissions_tco2=1_800.0,
            indirect_emissions_tco2=200.0,
            cbam_carbon_price_eur_per_ton=80.0,
        )
        assert res["ok"] is True
        assert res["product_type"] == "STEEL"
        assert res["total_embedded_emissions_tco2e"] == 2_000.0
        assert res["specific_embedded_emissions_tco2_per_ton"] == 2.0
        assert res["estimated_cbam_liability_eur"] == 2_000.0 * 80.0  # 160,000 EUR
        assert res["estimated_cbam_liability_vnd"] > 0

    def test_audit_esg_score(self, engine: EsgEngine) -> None:
        # Full compliance corporation
        res = engine.audit_esg_score(
            enterprise_name="Vinamilk Dairy Corp",
            has_iso_14001=True,
            renewable_energy_ratio_pct=40.0,
            has_waste_treatment_license=True,
            full_social_insurance_compliance=True,
            workplace_accident_rate=0.0,
            female_leadership_ratio_pct=35.0,
            independent_board_members_ratio_pct=33.3,
            has_anti_corruption_policy=True,
            has_audited_financial_report=True,
        )
        assert res["ok"] is True
        assert res["enterprise_name"] == "Vinamilk Dairy Corp"
        assert res["pillars"]["environmental"]["score"] >= 80.0
        assert res["pillars"]["social"]["score"] >= 80.0
        assert res["pillars"]["governance"]["score"] >= 90.0
        assert res["composite_score"] >= 80.0
        assert res["rating_grade"] in ("AAA", "AA")

    def test_trade_carbon_credits(self, engine: EsgEngine) -> None:
        res = engine.trade_carbon_credits(
            project_name="Can Gio Mangrove Afforestation",
            credit_type="VCS",
            quantity_tco2e=1_000.0,
            unit_price_usd=15.0,
            action="BUY",
            counterparty="Sở Giao dịch Hàng hóa VN",
        )
        assert res["ok"] is True
        assert res["total_amount_usd"] == 15_000.0
        assert res["action"] == "BUY"
        assert res["total_amount_vnd"] == 15_000.0 * 25_450.0

    def test_list_and_status(self, engine: EsgEngine) -> None:
        engine.calculate_ghg_inventory(
            enterprise_name="Alpha Textile",
            reporting_year=2026,
            fuel_diesel_liters=500.0,
        )
        engine.trade_carbon_credits(
            project_name="Solar Rooftop Binh Duong",
            credit_type="I-REC",
            quantity_tco2e=200.0,
            unit_price_usd=8.0,
        )
        engine.audit_esg_score(
            enterprise_name="Alpha Textile",
        )

        invs = engine.list_inventories()
        txs = engine.list_transactions()
        assert len(invs) >= 1
        assert len(txs) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["status"] == "operational"
        assert status["metrics"]["total_ghg_inventories"] >= 1
        assert status["metrics"]["total_carbon_transactions"] >= 1
        assert status["metrics"]["total_esg_ratings"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestEsgCli:
    """Test Typer CLI surface for mekong esg."""

    @pytest.fixture
    def app(self) -> any:
        return build_app()

    def test_esg_overview(self, app: any) -> None:
        result = runner.invoke(app, ["esg"])
        assert result.exit_code == 0
        assert "ESG" in result.output or "Environmental" in result.output or "Khí nhà kính" in result.output

    def test_esg_ghg_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "esg",
                "ghg",
                "Saigon Tech Hub",
                "2026",
                "--diesel",
                "2000",
                "--electricity",
                "100000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["enterprise_name"] == "Saigon Tech Hub"
        assert data["breakdown"]["scope_1_direct_tco2e"] > 0

    def test_esg_cbam_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "esg",
                "cbam",
                "STEEL",
                "500",
                "900",
                "--carbon-price",
                "75",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["product_type"] == "STEEL"
        assert data["estimated_cbam_liability_eur"] > 0

    def test_esg_audit_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "esg",
                "audit",
                "Mekong Food Export Corp",
                "--renewable",
                "30",
                "--female-lead",
                "40",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["composite_score"] > 50.0
        assert data["rating_grade"] in ("AAA", "AA", "A", "BBB")

    def test_esg_carbon_trade_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "esg",
                "carbon-trade",
                "Dak Lak Wind Farm",
                "VCS",
                "300",
                "14",
                "--action",
                "BUY",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["total_amount_usd"] == 4200.0

    def test_esg_list_json(self, app: any) -> None:
        result = runner.invoke(app, ["esg", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "ghg_inventories" in data
        assert "carbon_transactions" in data

    def test_esg_status_json(self, app: any) -> None:
        result = runner.invoke(app, ["esg", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "operational"
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestEsgMcp:
    """Test dual-engine FastMCP and pure-Python JSON-RPC 2.0 tool handlers for ESG."""

    def test_scripts_mcp_server_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_esg_ghg,
            handle_esg_cbam,
            handle_esg_audit,
            handle_esg_carbon_trade,
            handle_esg_list,
            handle_esg_status,
        )

        ghg_raw = handle_esg_ghg({
            "enterprise_name": "MCP Solar Tech",
            "reporting_year": 2026,
            "electricity_kwh": 200_000.0,
        })
        ghg_data = json.loads(ghg_raw)
        assert ghg_data["ok"] is True

        cbam_raw = handle_esg_cbam({
            "product_type": "ALUMINUM",
            "export_volume_tons": 200.0,
            "direct_emissions_tco2": 450.0,
        })
        cbam_data = json.loads(cbam_raw)
        assert cbam_data["ok"] is True

        audit_raw = handle_esg_audit({
            "enterprise_name": "MCP Sustainable Plastics",
        })
        audit_data = json.loads(audit_raw)
        assert audit_data["ok"] is True

        trade_raw = handle_esg_carbon_trade({
            "project_name": "Hydro Clean Power",
            "credit_type": "GS",
            "quantity_tco2e": 100.0,
            "unit_price_usd": 12.0,
        })
        trade_data = json.loads(trade_raw)
        assert trade_data["ok"] is True

        list_raw = handle_esg_list({})
        list_data = json.loads(list_raw)
        assert list_data["ok"] is True

        status_raw = handle_esg_status({})
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        ghg_raw = server._handle_esg_ghg(
            enterprise_name="Core Solar Tech",
            reporting_year=2026,
            electricity_kwh=150_000.0,
        )
        ghg_data = json.loads(ghg_raw)
        assert ghg_data["ok"] is True

        status_raw = server._handle_esg_status()
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True
