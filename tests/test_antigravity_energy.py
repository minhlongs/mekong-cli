# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Renewable Energy, Rooftop Solar, DPPA & EV Charging Infrastructure Engine (Phase 58)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.energy_engine import (
    REGIONAL_PSH,
    CHARGER_TYPES,
    TOU_TARIFF_DECISION_2699,
    GRID_CO2_FACTOR_KG_PER_KWH,
    EnergyEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestEnergyCoreBoundary:
    """Ensure EnergyEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/energy_engine.py")
        assert source_path.exists(), "energy_engine.py must exist"

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


class TestEnergyEngine:
    """Test EnergyEngine solar modeling, DPPA contract valuation, and EV charging simulation."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> EnergyEngine:
        db_file = tmp_path / "test_energy.db"
        return EnergyEngine(db_path=db_file)

    def test_constants_and_coefficients(self) -> None:
        assert "Binh Thuan" in REGIONAL_PSH
        assert "Hanoi" in REGIONAL_PSH
        assert REGIONAL_PSH["Binh Thuan"] > REGIONAL_PSH["Hanoi"]
        assert "DC_120kW" in CHARGER_TYPES
        assert "normal" in TOU_TARIFF_DECISION_2699
        assert GRID_CO2_FACTOR_KG_PER_KWH == 0.7221

    def test_evaluate_rooftop_solar_exempt_tier(self, engine: EnergyEngine) -> None:
        # <= 100 kWp rooftop solar is exempt from registration under Decree 135/2024
        res = engine.evaluate_rooftop_solar(
            project_id="SOLAR-SMALL-01",
            capacity_kwp=50.0,
            location="Binh Duong",
            self_consumption_pct=85.0,
            grid_connection="connected",
            battery_storage_kwh=10.0,
        )
        assert res["ok"] is True
        assert res["project_id"] == "SOLAR-SMALL-01"
        assert res["permitting"]["tier"] == "EXEMPT_INSTALLATION"
        assert res["permitting"]["license_required"] is False
        assert res["generation"]["annual_generation_kwh"] > 0
        assert res["carbon_offset"]["annual_co2_offset_tonnes"] > 0
        assert res["storage"]["has_bess"] is True

    def test_evaluate_rooftop_solar_notification_tier(self, engine: EnergyEngine) -> None:
        # 100-1000 kWp requires notification to local Department of Industry and Trade (DOIT)
        res = engine.evaluate_rooftop_solar(
            project_id="SOLAR-FACTORY-02",
            capacity_kwp=450.0,
            location="Dong Nai",
            self_consumption_pct=75.0,
            grid_connection="connected",
        )
        assert res["ok"] is True
        assert res["permitting"]["tier"] == "NOTIFICATION_REQUIRED"
        assert res["permitting"]["license_required"] is False
        assert res["decree_135_compliance"]["max_allowable_grid_export_pct"] == 20.0
        # If self-consumption is 75%, surplus is 25%, which exceeds 20% cap -> capped at 20%
        assert res["decree_135_compliance"]["capped_export_kwh"] < res["decree_135_compliance"]["potential_export_kwh"]

    def test_evaluate_rooftop_solar_license_tier(self, engine: EnergyEngine) -> None:
        # > 1000 kWp requires Electricity Regulatory Authority of Vietnam (ERAV) license
        res = engine.evaluate_rooftop_solar(
            project_id="SOLAR-MEGA-03",
            capacity_kwp=1500.0,
            location="Ninh Thuan",
            self_consumption_pct=90.0,
            grid_connection="connected",
        )
        assert res["ok"] is True
        assert res["permitting"]["tier"] == "ERAV_LICENSE_REQUIRED"
        assert res["permitting"]["license_required"] is True

    def test_evaluate_rooftop_solar_off_grid(self, engine: EnergyEngine) -> None:
        # Off-grid island/remote microgrid
        res = engine.evaluate_rooftop_solar(
            project_id="SOLAR-OFFGRID-04",
            capacity_kwp=30.0,
            location="Kien Giang",
            self_consumption_pct=100.0,
            grid_connection="off_grid",
        )
        assert res["ok"] is True
        assert res["decree_135_compliance"]["is_grid_connected"] is False
        assert res["financials"]["annual_export_revenue_vnd"] == 0.0

    def test_evaluate_dppa_contract_direct_wire(self, engine: EnergyEngine) -> None:
        # Direct line DPPA: buyer and seller connected by dedicated private wire
        res = engine.evaluate_dppa_contract(
            contract_id="DPPA-DIRECT-01",
            buyer_id="Samsung Electronics Thai Nguyen",
            seller_id="Xuan Thien Solar Group",
            mechanism="direct",
            contract_kwh_month=800000.0,
            strike_price_vnd_kwh=1850.0,
            spot_price_vnd_kwh=1700.0,
        )
        assert res["ok"] is True
        assert res["eligibility"]["is_eligible"] is True
        assert res["mechanism"] == "DIRECT_LINE_PRIVATE_WIRE"
        assert res["financial_settlement"]["cfd_net_settlement_vnd"] == 0.0
        assert res["financial_settlement"]["direct_payment_monthly_vnd"] > 0
        assert res["environmental_impact"]["annual_co2_abatement_tonnes"] > 0

    def test_evaluate_dppa_contract_grid_cfd(self, engine: EnergyEngine) -> None:
        # Grid-connected DPPA via wholesale market (VWEM) with Contract for Differences (CfD)
        res = engine.evaluate_dppa_contract(
            contract_id="DPPA-GRID-02",
            buyer_id="VinFast Hai Phong Plant",
            seller_id="Trung Nam Wind Power",
            mechanism="grid",
            contract_kwh_month=1200000.0,
            strike_price_vnd_kwh=1900.0,
            spot_price_vnd_kwh=1600.0,
        )
        assert res["ok"] is True
        assert res["eligibility"]["is_eligible"] is True
        assert res["mechanism"] == "NATIONAL_GRID_VWEM_CFD"
        # Strike (1900) > Spot (1600): Buyer pays developer difference (300 VND/kWh * 1.2M kWh = 360M VND)
        cfd = res["financial_settlement"]["cfd_net_settlement_vnd"]
        assert cfd == pytest.approx(360_000_000.0, rel=1e-3)
        assert res["financial_settlement"]["cfd_direction"] == "BUYER_PAYS_SELLER"

    def test_evaluate_dppa_contract_ineligible_volume(self, engine: EnergyEngine) -> None:
        # Decree 80/2024 Article 3: Large consumer threshold >= 200,000 kWh/month
        res = engine.evaluate_dppa_contract(
            contract_id="DPPA-SMALL-03",
            buyer_id="Small Retail Store",
            seller_id="Local Solar Farm",
            mechanism="grid",
            contract_kwh_month=50000.0,  # Below 200,000 kWh/month
        )
        assert res["ok"] is True
        assert res["eligibility"]["is_eligible"] is False
        assert any("không đạt ngưỡng" in adv for adv in res["regulatory_advisories"])

    def test_simulate_ev_charging_session_dc_fast(self, engine: EnergyEngine) -> None:
        res = engine.simulate_ev_charging_session(
            session_id="EV-CHG-001",
            station_id="STATION-HN-TIMESCITY",
            charger_type="DC_120kW",
            energy_kwh=65.0,
            tou_period="peak",
            ev_model="VinFast VF8",
        )
        assert res["ok"] is True
        assert res["charger_specs"]["power_rating_kw"] == 120.0
        assert res["charger_specs"]["current_type"] == "DC_FAST"
        assert res["billing"]["tariff_vnd_per_kwh"] == TOU_TARIFF_DECISION_2699["peak"]
        assert res["billing"]["total_charge_vnd"] > 0
        assert res["environmental_impact"]["co2_avoided_kg"] > 0
        assert res["session_timing"]["estimated_duration_minutes"] > 0

    def test_simulate_ev_charging_session_ac_slow(self, engine: EnergyEngine) -> None:
        res = engine.simulate_ev_charging_session(
            session_id="EV-CHG-002",
            station_id="STATION-HCM-VHOME",
            charger_type="AC_7kW",
            energy_kwh=20.0,
            tou_period="off_peak",
            ev_model="VinFast VF5",
        )
        assert res["ok"] is True
        assert res["charger_specs"]["current_type"] == "AC_SLOW"
        assert res["session_timing"]["estimated_duration_minutes"] > 60

    def test_list_records_and_status(self, engine: EnergyEngine) -> None:
        # Populate records
        engine.evaluate_rooftop_solar("P-01", 100.0, "Hanoi")
        engine.evaluate_dppa_contract("D-01", "Buyer A", "Seller B", "direct", 300000.0)
        engine.simulate_ev_charging_session("S-01", "ST-01", "DC_60kW", 30.0)

        solars = engine.list_solar_projects()
        assert solars["ok"] is True
        assert len(solars["projects"]) >= 1

        dppas = engine.list_dppa_contracts()
        assert dppas["ok"] is True
        assert len(dppas["contracts"]) >= 1

        evs = engine.list_ev_sessions()
        assert evs["ok"] is True
        assert len(evs["sessions"]) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["total_solar_projects"] >= 1
        assert status["total_dppa_contracts"] >= 1
        assert status["total_ev_sessions"] >= 1
        assert status["metrics"]["total_installed_solar_kwp"] >= 100.0


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestEnergyCli:
    """Test mekong energy command group execution."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_main_json(self) -> None:
        result = runner.invoke(self.app, ["energy", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "regulatory_framework" in data
        assert "Nghị định 135/2024" in data["regulatory_framework"]
        assert "Nghị định 80/2024" in data["regulatory_framework"]

    def test_cli_solar_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "energy",
                "solar",
                "Dự án ĐMT Nhà máy May 10",
                "Tổng Công ty May 10",
                "NORTH",
                "350",
                "2500",
                "--self-pct",
                "85",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["solar_parameters"]["installed_capacity_kwp"] == 350.0
        assert data["regulatory_status"]["tier"] == "TIER_2_NOTIFICATION"

    def test_cli_solar_console(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "energy",
                "solar",
                "Dự án ĐMT Bến Tre",
                "Công ty Thủy sản Bến Tre",
                "SOUTH",
                "80",
                "600",
            ],
        )
        assert result.exit_code == 0
        assert "Dự án ĐMT Bến Tre" in result.output

    def test_cli_dppa_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "energy",
                "dppa",
                "BIM Energy Ninh Thuan",
                "Foxconn Bac Giang",
                "NATIONAL_GRID",
                "20",
                "800000",
                "--strike-price",
                "1850",
                "--market-price",
                "1700",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_statutory_eligible"] is True
        assert data["cfd_settlement_model"]["strike_price_vnd_per_kwh"] == 1850.0

    def test_cli_ev_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "energy",
                "ev",
                "ST-HN-01",
                "DC_120KW",
                "55",
                "--tou",
                "NORMAL",
                "--service-fee",
                "800",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["charger_specs"]["charger_type"] == "DC_120KW"
        assert data["billing"]["energy_delivered_kwh"] == 55.0

    def test_cli_list_json(self) -> None:
        res = runner.invoke(self.app, ["energy", "list", "--type", "solar", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "projects" in data

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["energy", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestEnergyMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for energy tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_energy_solar")
        assert hasattr(server, "_handle_energy_dppa")
        assert hasattr(server, "_handle_energy_ev")
        assert hasattr(server, "_handle_energy_list")
        assert hasattr(server, "_handle_energy_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_energy_solar",
            "mekong_energy_dppa",
            "mekong_energy_ev",
            "mekong_energy_list",
            "mekong_energy_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        s_handler = CORE_HANDLERS["mekong_energy_solar"]
        s_raw = s_handler({
            "project_id": "SOLAR-MCP-01",
            "capacity_kwp": 120.0,
            "location": "Binh Thuan",
            "self_consumption_pct": 80.0,
        })
        s_res = json.loads(s_raw)
        assert s_res["ok"] is True
        assert s_res["project_id"] == "SOLAR-MCP-01"

        d_handler = CORE_HANDLERS["mekong_energy_dppa"]
        d_raw = d_handler({
            "contract_id": "DPPA-MCP-01",
            "buyer_id": "FPT Telecom DC",
            "seller_id": "Ree Solar Corp",
            "mechanism": "grid",
            "contract_kwh_month": 450000.0,
            "strike_price_vnd_kwh": 1820.0,
            "spot_price_vnd_kwh": 1600.0,
        })
        d_res = json.loads(d_raw)
        assert d_res["ok"] is True
        assert d_res["contract_id"] == "DPPA-MCP-01"
        assert d_res["eligibility"]["is_eligible"] is True

        ev_handler = CORE_HANDLERS["mekong_energy_ev"]
        ev_raw = ev_handler({
            "session_id": "EV-MCP-01",
            "station_id": "STAT-V-01",
            "charger_type": "DC_120kW",
            "energy_kwh": 40.0,
            "tou_period": "peak",
            "ev_model": "VF9",
        })
        ev_res = json.loads(ev_raw)
        assert ev_res["ok"] is True
        assert ev_res["session_id"] == "EV-MCP-01"
