# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Civil Aviation, Air Cargo Freight & Ground Handling Engine (Phase 60)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.aviation_engine import (
    VIETNAM_AIRPORTS,
    AIRCRAFT_TYPES,
    IATA_DGR_CLASSES,
    IATA_VOLUMETRIC_RATIO_KG_PER_CBM,
    VND_PER_USD,
    AviationEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestAviationCoreBoundary:
    """Ensure AviationEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/aviation_engine.py")
        assert source_path.exists(), "aviation_engine.py must exist"

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


class TestAviationEngine:
    """Test AviationEngine flights, air cargo chargeable weight, tariffs, and DGR evaluation."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> AviationEngine:
        db_file = tmp_path / "test_aviation.db"
        return AviationEngine(db_path=db_file)

    def test_constants_and_airport_registry(self) -> None:
        assert "HAN" in VIETNAM_AIRPORTS
        assert "SGN" in VIETNAM_AIRPORTS
        assert "DAD" in VIETNAM_AIRPORTS
        assert "CXR" in VIETNAM_AIRPORTS
        assert "PQC" in VIETNAM_AIRPORTS
        assert VIETNAM_AIRPORTS["HAN"]["group"] == "GROUP_A"
        assert VIETNAM_AIRPORTS["HPH"]["group"] == "GROUP_B"

        assert "A321" in AIRCRAFT_TYPES
        assert "B787-9" in AIRCRAFT_TYPES
        assert "A350-900" in AIRCRAFT_TYPES
        assert "B777F" in AIRCRAFT_TYPES

        assert "CLASS_1" in IATA_DGR_CLASSES
        assert "CLASS_7" in IATA_DGR_CLASSES
        assert "CLASS_9" in IATA_DGR_CLASSES
        assert round(IATA_VOLUMETRIC_RATIO_KG_PER_CBM, 2) == 166.67
        assert VND_PER_USD > 20000

    def test_register_flight_schedule_narrowbody(self, engine: AviationEngine) -> None:
        res = engine.register_flight_schedule(
            flight_no="VN216",
            aircraft_type="A321",
            origin_airport="SGN",
            dest_airport="HAN",
            mtow_tons=89.0,
            parking_hours=2.5,
            is_international=False,
        )
        assert res["ok"] is True
        assert res["flight_id"].startswith("FLT-")
        assert res["flight_no"] == "VN216"
        assert res["aircraft"]["aircraft_type"] == "A321"
        assert res["aircraft"]["mtow_tons"] == 89.0
        assert res["aircraft"]["is_widebody"] is False
        assert res["routing"]["origin"] == "SGN"
        assert res["routing"]["destination"] == "HAN"
        assert res["routing"]["is_international"] is False
        assert res["slot_and_apron"]["overnight_parking"] is False

    def test_register_flight_schedule_widebody_international(self, engine: AviationEngine) -> None:
        res = engine.register_flight_schedule(
            flight_no="VN001",
            aircraft_type="B787-9",
            origin_airport="HAN",
            dest_airport="SFO",
            mtow_tons=254.0,
            parking_hours=10.0,
            is_international=True,
        )
        assert res["ok"] is True
        assert res["aircraft"]["is_widebody"] is True
        assert res["routing"]["is_international"] is True
        assert res["slot_and_apron"]["overnight_parking"] is True
        assert res["slot_and_apron"]["apron_contact_stand"] is True

    def test_calculate_air_cargo_chargeable_weight_heavy_cargo(self, engine: AviationEngine) -> None:
        # Gross weight (800 kg) > Volumetric weight (2 CBM * 166.67 = 333.34 kg)
        res = engine.calculate_air_cargo_chargeable_weight(
            mawb_no="738-12345675",
            origin_airport="SGN",
            dest_airport="HAN",
            piece_count=20,
            gross_weight_kg=800.0,
            volume_cbm=2.0,
            cargo_type="GENERAL",
            temperature_regime="AMBIENT",
        )
        assert res["ok"] is True
        assert res["shipment_id"].startswith("AWB-")
        assert res["weight_and_volume"]["gross_weight_kg"] == 800.0
        assert res["weight_and_volume"]["chargeable_weight_kg"] == 800.0
        assert res["weight_and_volume"]["is_volume_cargo"] is False
        assert res["weight_and_volume"]["basis"] == "GROSS_WEIGHT"
        assert res["weight_and_volume"]["density_kg_per_cbm"] == 400.0

    def test_calculate_air_cargo_chargeable_weight_volumetric_cold_chain(self, engine: AviationEngine) -> None:
        # Light voluminous pharma cargo: Gross 100 kg, Volume 3.0 CBM
        # Volumetric = 3.0 * 166.67 = 500.01 kg -> Chargeable weight = 500.01 kg
        res = engine.calculate_air_cargo_chargeable_weight(
            mawb_no="738-99887766",
            origin_airport="HAN",
            dest_airport="DAD",
            piece_count=15,
            gross_weight_kg=100.0,
            volume_cbm=3.0,
            cargo_type="PHARMA",
            temperature_regime="2_8C",
        )
        assert res["ok"] is True
        assert res["weight_and_volume"]["is_volume_cargo"] is True
        assert res["weight_and_volume"]["basis"] == "VOLUMETRIC_WEIGHT"
        assert res["weight_and_volume"]["chargeable_weight_kg"] == 500.01
        assert len(res["cargo_classification"]["special_handling_notes"]) > 0
        assert "+2°C đến +8°C" in res["cargo_classification"]["special_handling_notes"][0]

    def test_calculate_airport_tariffs_international(self, engine: AviationEngine) -> None:
        # HAN is Group A airport: Landing rate = $8.20/ton
        # 100 tons MTOW * $8.20 = $820.00
        # Parking 4 hours (3 billable hours * 100 tons * $0.25) = $75.00
        # Cargo 10 tons (10,000 kg * $0.015) = $150.00
        # Ground handling (10 tons * $25) = $250.00
        # Total USD = $820 + $75 + $150 + $250 = $1295.00
        res = engine.calculate_airport_tariffs(
            flight_no="VN216",
            airport_code="HAN",
            mtow_tons=100.0,
            parking_hours=4.0,
            cargo_tons=10.0,
            is_international=True,
        )
        assert res["ok"] is True
        assert res["tariff_id"].startswith("TRF-")
        assert res["breakdown_usd"]["landing_takeoff_fee_usd"] == 820.0
        assert res["breakdown_usd"]["aircraft_parking_fee_usd"] == 75.0
        assert res["breakdown_usd"]["cargo_security_screening_fee_usd"] == 150.0
        assert res["breakdown_usd"]["apron_ground_handling_fee_usd"] == 250.0
        assert res["financials"]["total_amount_usd"] == 1295.0
        assert res["financials"]["total_amount_vnd"] == round(1295.0 * VND_PER_USD)

    def test_calculate_airport_tariffs_domestic(self, engine: AviationEngine) -> None:
        # Group B airport (HPH): Domestic landing rate = $2.90/ton
        res = engine.calculate_airport_tariffs(
            flight_no="VJ401",
            airport_code="HPH",
            mtow_tons=50.0,
            parking_hours=1.0,
            cargo_tons=2.0,
            is_international=False,
        )
        assert res["ok"] is True
        assert res["airport_details"]["airport_group"] == "GROUP_B"
        assert res["airport_details"]["flight_nature"] == "DOMESTIC"
        assert res["breakdown_usd"]["landing_takeoff_fee_usd"] == round(50.0 * 2.90, 2)
        # 1.0 hr parking <= 1.0 hr free buffer -> parking fee = 0
        assert res["breakdown_usd"]["aircraft_parking_fee_usd"] == 0.0

    def test_evaluate_dangerous_goods_declaration_pax_forbidden(self, engine: AviationEngine) -> None:
        # Class 1 Explosive is forbidden on passenger aircraft
        res = engine.evaluate_dangerous_goods_declaration(
            un_number="UN0027",
            proper_shipping_name="Black Powder (Gunpowder)",
            hazard_class="CLASS_1",
            packing_group="I",
            quantity_kg=25.0,
        )
        assert res["ok"] is True
        assert res["declaration_id"].startswith("DGD-")
        assert res["air_transport_compliance"]["is_passenger_aircraft_forbidden"] is True
        assert res["air_transport_compliance"]["allowed_aircraft_mode"] == "CARGO_AIRCRAFT_ONLY"
        assert "CARGO_AIRCRAFT_ONLY" in res["packaging_requirements"]["dg_handling_labels"]

    def test_evaluate_dangerous_goods_declaration_lithium_batteries(self, engine: AviationEngine) -> None:
        # Standalone bulk lithium batteries UN3480 > 5kg -> Cargo Aircraft Only (CAO)
        res = engine.evaluate_dangerous_goods_declaration(
            un_number="UN3480",
            proper_shipping_name="Lithium Ion Batteries",
            hazard_class="CLASS_9",
            packing_group="II",
            quantity_kg=15.0,
        )
        assert res["ok"] is True
        assert res["air_transport_compliance"]["is_passenger_aircraft_forbidden"] is True
        assert res["air_transport_compliance"]["allowed_aircraft_mode"] == "CARGO_AIRCRAFT_ONLY"

    def test_evaluate_dangerous_goods_declaration_allowed_pax(self, engine: AviationEngine) -> None:
        # Small consumer paint / solvent Class 3 packing group III
        res = engine.evaluate_dangerous_goods_declaration(
            un_number="UN1263",
            proper_shipping_name="Paint Related Material",
            hazard_class="CLASS_3",
            packing_group="III",
            quantity_kg=2.0,
        )
        assert res["ok"] is True
        assert res["air_transport_compliance"]["is_passenger_aircraft_forbidden"] is False
        assert res["air_transport_compliance"]["allowed_aircraft_mode"] == "PASSENGER_AND_CARGO_AIRCRAFT"

    def test_list_records_and_record_list(self, engine: AviationEngine) -> None:
        engine.register_flight_schedule("VN101", "A321", "SGN", "HAN", 89.0, 2.0, False)
        engine.calculate_air_cargo_chargeable_weight("738-11112222", "SGN", "HAN", 5, 200.0, 1.0)
        engine.evaluate_dangerous_goods_declaration("UN1993", "Flammable Liquids N.O.S.", "CLASS_3", "II", 5.0)

        flights = engine.list_flight_schedules(limit=10)
        assert len(flights) >= 1
        assert flights["ok"] is True
        assert "flights" in flights
        assert isinstance(flights["flights"], list)

        cargo = engine.list_air_cargo_shipments(limit=10)
        assert len(cargo) >= 1
        assert cargo["ok"] is True
        assert "shipments" in cargo

        dg = engine.list_dangerous_goods(limit=10)
        assert len(dg) >= 1
        assert dg["ok"] is True
        assert "dg_declarations" in dg

    def test_get_status_telemetry(self, engine: AviationEngine) -> None:
        engine.register_flight_schedule("VN202", "A350-900", "SGN", "CDG", 280.0, 3.0, True)
        engine.calculate_air_cargo_chargeable_weight("738-33334444", "SGN", "CDG", 50, 2500.0, 10.0)
        engine.calculate_airport_tariffs("VN202", "SGN", 280.0, 3.0, 2.5, True)

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "AviationEngine"
        assert status["metrics"]["total_scheduled_flights"] >= 1
        assert status["metrics"]["total_mtow_handled_tons"] >= 280.0
        assert status["metrics"]["total_air_cargo_shipments"] >= 1
        assert status["metrics"]["total_airport_tariffs_assessed"] >= 1
        assert status["metrics"]["total_airport_revenue_usd"] > 0


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestAviationCli:
    """Test Typer CLI commands for aviation."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_flight_console(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "aviation",
                "flight",
                "VN216",
                "A321",
                "SGN",
                "HAN",
                "--mtow",
                "89.0",
                "--parking",
                "2.0",
            ],
        )
        assert result.exit_code == 0
        assert "VN216" in result.output

    def test_cli_flight_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "aviation",
                "flight",
                "VN216",
                "A321",
                "SGN",
                "HAN",
                "--mtow",
                "89.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["flight_no"] == "VN216"
        assert data["aircraft"]["aircraft_type"] == "A321"

    def test_cli_cargo_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "aviation",
                "cargo",
                "738-12345675",
                "SGN",
                "HAN",
                "20",
                "600.0",
                "4.5",
                "--type",
                "GENERAL",
                "--temp",
                "AMBIENT",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["mawb_no"] == "738-12345675"
        # 4.5 CBM * 166.67 = 750.015 kg > 600 kg
        assert data["weight_and_volume"]["chargeable_weight_kg"] > 600.0

    def test_cli_tariff_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "aviation",
                "tariff",
                "VN216",
                "HAN",
                "90.0",
                "--parking",
                "3.0",
                "--cargo",
                "8.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["flight_no"] == "VN216"
        assert data["financials"]["total_amount_usd"] > 0
        assert data["financials"]["total_amount_vnd"] > 0

    def test_cli_dg_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "aviation",
                "dg",
                "UN3480",
                "Lithium Ion Batteries",
                "CLASS_9",
                "--pg",
                "II",
                "--qty",
                "20.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["air_transport_compliance"]["is_passenger_aircraft_forbidden"] is True

    def test_cli_list_json(self) -> None:
        res = runner.invoke(self.app, ["aviation", "list", "--type", "flights", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "flights" in data

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["aviation", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestAviationMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for aviation tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_aviation_flight")
        assert hasattr(server, "_handle_aviation_cargo")
        assert hasattr(server, "_handle_aviation_tariff")
        assert hasattr(server, "_handle_aviation_dg")
        assert hasattr(server, "_handle_aviation_list")
        assert hasattr(server, "_handle_aviation_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_aviation_flight",
            "mekong_aviation_cargo",
            "mekong_aviation_tariff",
            "mekong_aviation_dg",
            "mekong_aviation_list",
            "mekong_aviation_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        f_handler = CORE_HANDLERS["mekong_aviation_flight"]
        f_raw = f_handler({
            "flight_no": "VN216",
            "aircraft_type": "A321",
            "origin_airport": "SGN",
            "dest_airport": "HAN",
            "mtow_tons": 90.0,
            "parking_hours": 2.0,
            "is_international": False,
        })
        f_res = json.loads(f_raw)
        assert f_res["ok"] is True
        assert f_res["flight_no"] == "VN216"

        c_handler = CORE_HANDLERS["mekong_aviation_cargo"]
        c_raw = c_handler({
            "mawb_no": "738-99998888",
            "origin_airport": "SGN",
            "dest_airport": "HAN",
            "piece_count": 10,
            "gross_weight_kg": 500.0,
            "volume_cbm": 4.0,
        })
        c_res = json.loads(c_raw)
        assert c_res["ok"] is True
        assert c_res["weight_and_volume"]["chargeable_weight_kg"] > 500.0

        t_handler = CORE_HANDLERS["mekong_aviation_tariff"]
        t_raw = t_handler({
            "flight_no": "VN216",
            "airport_code": "HAN",
            "mtow_tons": 90.0,
            "parking_hours": 2.0,
            "cargo_tons": 10.0,
            "is_international": True,
        })
        t_res = json.loads(t_raw)
        assert t_res["ok"] is True
        assert t_res["financials"]["total_amount_usd"] > 0
