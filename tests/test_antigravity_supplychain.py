# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Supply Chain Traceability, Anti-Deforestation (EUDR) & Digital Product Passport Engine (Phase 55)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.supplychain_engine import (
    EUDR_COMMODITIES,
    EUDR_CUTOFF_DATE,
    VALID_EVENT_TYPES,
    SupplyChainEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestSupplyChainCoreBoundary:
    """Ensure SupplyChainEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/supplychain_engine.py")
        assert source_path.exists(), "supplychain_engine.py must exist"

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


class TestSupplyChainEngine:
    """Test SupplyChainEngine plot registration, batch aggregation, custody event chaining, and EUDR DDS."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> SupplyChainEngine:
        db_file = tmp_path / "test_supplychain.db"
        return SupplyChainEngine(db_path=db_file)

    def test_constants_and_commodities(self) -> None:
        assert "COFFEE" in EUDR_COMMODITIES
        assert "RUBBER" in EUDR_COMMODITIES
        assert "TIMBER_WOOD" in EUDR_COMMODITIES
        assert EUDR_CUTOFF_DATE == "2020-12-31"
        assert "HARVEST" in VALID_EVENT_TYPES
        assert "SHIP" in VALID_EVENT_TYPES

    def test_register_plot_under_4ha_compliant(self, engine: SupplyChainEngine) -> None:
        res = engine.register_plot(
            farmer_name="Trần Văn Nam",
            province="Đắk Lắk",
            district="Cư M'gar",
            commodity="COFFEE",
            latitude=12.6667,
            longitude=108.0333,
            area_hectares=2.5,
            deforestation_free_post_2020=True,
        )
        assert res["ok"] is True
        assert res["plot_id"].startswith("PLOT-VN-")
        assert res["farmer_name"] == "Trần Văn Nam"
        assert res["commodity"] == "COFFEE"
        assert res["coordinates"]["polygon_required"] is False
        assert res["eudr_compliance"]["is_eudr_compliant"] is True

    def test_register_plot_over_4ha_missing_polygon(self, engine: SupplyChainEngine) -> None:
        # > 4 ha requires polygon coords under EUDR
        res = engine.register_plot(
            farmer_name="Công ty Lâm nghiệp Buôn Đôn",
            province="Đắk Lắk",
            commodity="TIMBER_WOOD",
            latitude=12.8000,
            longitude=107.9000,
            area_hectares=12.0,
            polygon_coords=None,
            deforestation_free_post_2020=True,
        )
        assert res["ok"] is True
        assert res["coordinates"]["polygon_required"] is True
        assert res["coordinates"]["has_polygon"] is False
        assert res["eudr_compliance"]["is_eudr_compliant"] is False

    def test_register_plot_over_4ha_with_polygon(self, engine: SupplyChainEngine) -> None:
        poly = [
            (12.8000, 107.9000),
            (12.8100, 107.9000),
            (12.8100, 107.9100),
            (12.8000, 107.9000),
        ]
        res = engine.register_plot(
            farmer_name="Nông trường Cao su Bình Phước",
            province="Bình Phước",
            commodity="RUBBER",
            latitude=11.7500,
            longitude=106.9000,
            area_hectares=8.5,
            polygon_coords=poly,
            deforestation_free_post_2020=True,
        )
        assert res["ok"] is True
        assert res["coordinates"]["polygon_required"] is True
        assert res["coordinates"]["has_polygon"] is True
        assert res["eudr_compliance"]["is_eudr_compliant"] is True

    def test_register_plot_deforestation_violation(self, engine: SupplyChainEngine) -> None:
        res = engine.register_plot(
            farmer_name="Hộ vi phạm",
            province="Gia Lai",
            commodity="COFFEE",
            latitude=13.9800,
            longitude=108.0000,
            area_hectares=1.5,
            deforestation_free_post_2020=False,
        )
        assert res["ok"] is True
        assert res["eudr_compliance"]["is_eudr_compliant"] is False
        assert "VI PHẠM MỐC CẮT ĐỨT" in res["eudr_compliance"]["notes"][0]

    def test_create_batch_and_hashing(self, engine: SupplyChainEngine) -> None:
        p1 = engine.register_plot(
            farmer_name="A Phò",
            province="Lâm Đồng",
            commodity="COFFEE",
            latitude=11.9400,
            longitude=108.4500,
            area_hectares=2.0,
        )
        batch = engine.create_batch(
            batch_code="LOT-CF-2026-TEST",
            commodity="COFFEE",
            quantity_kg=15_000.0,
            processor_name="Simexco DakLak",
            plot_ids=[p1["plot_id"]],
            certifications=["4C", "RA"],
        )
        assert batch["ok"] is True
        assert batch["batch_code"] == "LOT-CF-2026-TEST"
        assert batch["quantity_kg"] == 15_000.0
        assert batch["plots_summary"]["total_plots"] == 1
        assert batch["plots_summary"]["all_plots_deforestation_free"] is True
        assert len(batch["batch_hash"]) == 64

    def test_record_custody_events_chaining(self, engine: SupplyChainEngine) -> None:
        engine.create_batch(
            batch_code="LOT-RUB-01",
            commodity="RUBBER",
            quantity_kg=20_000.0,
            processor_name="Dong Nai Rubber",
        )
        e1 = engine.record_custody_event(
            batch_code="LOT-RUB-01",
            event_type="HARVEST",
            location="Nông trường Dầu Giây",
            actor_name="Đội thu hoạch 1",
            notes="Thu hoạch mủ cao su",
        )
        e2 = engine.record_custody_event(
            batch_code="LOT-RUB-01",
            event_type="PROCESS",
            location="Nhà máy Chế biến Long Khánh",
            actor_name="Phòng Kỹ thuật",
            notes="Chế biến cao su SVR 10",
        )
        e3 = engine.record_custody_event(
            batch_code="LOT-RUB-01",
            event_type="SHIP",
            location="Cảng Cát Lái",
            actor_name="Maersk Line",
            notes="Bốc dỡ container",
        )
        assert e1["ok"] is True
        assert e2["ok"] is True
        assert e3["ok"] is True
        # Verify hash chaining
        assert e2["chain_integrity"]["prev_hash"] == e1["chain_integrity"]["event_hash"]
        assert e3["chain_integrity"]["prev_hash"] == e2["chain_integrity"]["event_hash"]

    def test_generate_eudr_statement(self, engine: SupplyChainEngine) -> None:
        p1 = engine.register_plot(
            farmer_name="Nguyễn Văn A",
            province="Đắk Lắk",
            commodity="COFFEE",
            latitude=12.6000,
            longitude=108.0000,
            area_hectares=3.0,
            deforestation_free_post_2020=True,
        )
        engine.create_batch(
            batch_code="LOT-CF-EUDR",
            commodity="COFFEE",
            quantity_kg=19_200.0,
            processor_name="DakMan Vietnam",
            plot_ids=[p1["plot_id"]],
        )
        dds = engine.generate_eudr_statement(
            batch_code="LOT-CF-EUDR",
            exporter_name="DakMan Vietnam Co., Ltd",
            importer_name="Tchibo GmbH",
            destination_country="Germany",
        )
        assert dds["ok"] is True
        assert dds["dds_reference"].startswith("EUDR-VN-")
        assert dds["due_diligence_evaluation"]["risk_assessment_grade"] == "NEGLIGIBLE_RISK"
        assert dds["due_diligence_evaluation"]["zero_deforestation_verified"] is True
        assert len(dds["plots_included"]) == 1

    def test_get_batch_trace_and_status(self, engine: SupplyChainEngine) -> None:
        engine.create_batch(
            batch_code="LOT-WOOD-01",
            commodity="TIMBER_WOOD",
            quantity_kg=50_000.0,
            processor_name="An Cuong Wood JSC",
        )
        engine.record_custody_event(
            batch_code="LOT-WOOD-01",
            event_type="PROCESS",
            location="Bình Dương Factory",
            actor_name="An Cường Production",
        )
        trace = engine.get_batch_trace("LOT-WOOD-01")
        assert trace["ok"] is True
        assert trace["batch_code"] == "LOT-WOOD-01"
        assert len(trace["timeline"]) == 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["status"] == "operational"
        assert status["metrics"]["total_traceability_batches"] >= 1
        assert status["metrics"]["total_custody_events"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestSupplyChainCli:
    """Test Typer CLI surface for mekong supplychain."""

    @pytest.fixture
    def app(self) -> any:
        return build_app()

    def test_supplychain_overview(self, app: any) -> None:
        result = runner.invoke(app, ["supplychain"])
        assert result.exit_code == 0
        assert "Supply Chain" in result.output or "EUDR" in result.output or "TRUY XUẤT" in result.output

    def test_supplychain_plot_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "supplychain",
                "plot",
                "Trần Văn Bình",
                "Lâm Đồng",
                "COFFEE",
                "11.9404",
                "108.4583",
                "2.8",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["farmer_name"] == "Trần Văn Bình"
        assert data["commodity"] == "COFFEE"

    def test_supplychain_batch_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "supplychain",
                "batch",
                "LOT-CLI-001",
                "COFFEE",
                "10000",
                "Da Lat Coffee Mill",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["batch_code"] == "LOT-CLI-001"
        assert data["quantity_kg"] == 10000.0

    def test_supplychain_event_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "supplychain",
                "event",
                "LOT-CLI-001",
                "PROCESS",
                "Da Lat Factory",
                "Processor Team",
                "--notes",
                "Sơ chế hạt cà phê nhân xanh",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["event_type"] == "PROCESS"

    def test_supplychain_eudr_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "supplychain",
                "eudr",
                "LOT-CLI-001",
                "Vietnam Coffee Corp",
                "Hamburg Import AG",
                "--dest",
                "Germany",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["dds_reference"].startswith("EUDR-VN-")

    def test_supplychain_trace_json(self, app: any) -> None:
        result = runner.invoke(
            app,
            [
                "supplychain",
                "trace",
                "LOT-CLI-001",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["batch_code"] == "LOT-CLI-001"

    def test_supplychain_list_json(self, app: any) -> None:
        res_plots = runner.invoke(app, ["supplychain", "list", "--type", "plots", "--json"])
        assert res_plots.exit_code == 0
        data_plots = json.loads(res_plots.output)
        assert data_plots["ok"] is True
        assert "plots" in data_plots

        res_batches = runner.invoke(app, ["supplychain", "list", "--type", "batches", "--json"])
        assert res_batches.exit_code == 0
        data_batches = json.loads(res_batches.output)
        assert data_batches["ok"] is True
        assert "batches" in data_batches

    def test_supplychain_status_json(self, app: any) -> None:
        result = runner.invoke(app, ["supplychain", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "operational"
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestSupplyChainMcp:
    """Test dual-engine FastMCP and pure-Python JSON-RPC 2.0 tool handlers for supplychain."""

    def test_scripts_mcp_server_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_supplychain_plot,
            handle_supplychain_batch,
            handle_supplychain_event,
            handle_supplychain_eudr,
            handle_supplychain_trace,
            handle_supplychain_status,
        )

        plot_raw = handle_supplychain_plot({
            "farmer_name": "Nông dân MCP",
            "province": "Đắk Nông",
            "commodity": "COFFEE",
            "latitude": 12.0,
            "longitude": 107.5,
            "area_hectares": 3.0,
        })
        plot_data = json.loads(plot_raw)
        assert plot_data["ok"] is True

        batch_raw = handle_supplychain_batch({
            "batch_code": "LOT-MCP-01",
            "commodity": "COFFEE",
            "quantity_kg": 5000.0,
            "processor_name": "MCP Mill",
            "plot_ids": [plot_data["plot_id"]],
        })
        batch_data = json.loads(batch_raw)
        assert batch_data["ok"] is True

        event_raw = handle_supplychain_event({
            "batch_code": "LOT-MCP-01",
            "event_type": "COLLECT",
            "location": "Trạm thu mua",
            "actor_name": "Đại lý",
        })
        event_data = json.loads(event_raw)
        assert event_data["ok"] is True

        eudr_raw = handle_supplychain_eudr({
            "batch_code": "LOT-MCP-01",
            "exporter_name": "MCP Exporter",
            "importer_name": "EU Importer",
        })
        eudr_data = json.loads(eudr_raw)
        assert eudr_data["ok"] is True

        trace_raw = handle_supplychain_trace({
            "batch_code": "LOT-MCP-01",
        })
        trace_data = json.loads(trace_raw)
        assert trace_data["ok"] is True

        status_raw = handle_supplychain_status({})
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        plot_raw = server._handle_supplychain_plot(
            farmer_name="Core Farmer",
            province="Gia Lai",
            commodity="RUBBER",
            latitude=13.5,
            longitude=108.2,
            area_hectares=2.0,
        )
        plot_data = json.loads(plot_raw)
        assert plot_data["ok"] is True

        status_raw = server._handle_supplychain_status()
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True
