# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Railway Transport, High-Speed Rail & Metro (Phase 72)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.railway_engine import (
    FREIGHT_RATES_VND_PER_TON_KM,
    RAIL_CATEGORIES,
    RAIL_GAUGES,
    ROLLING_STOCK_LIFESPANS,
    RailwayEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestRailwayCoreBoundary:
    """Ensure RailwayEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/railway_engine.py")
        assert source_path.exists(), "railway_engine.py must exist"

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


class TestRailwayEngine:
    """Test RailwayEngine line registration, safety corridor clearance, rolling stock age, freight tariff, and driver licensing."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> RailwayEngine:
        db_file = tmp_path / "test_railway.db"
        return RailwayEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Gauges
        assert "STANDARD_1435MM" in RAIL_GAUGES
        assert RAIL_GAUGES["STANDARD_1435MM"]["gauge_mm"] == 1435
        assert RAIL_GAUGES["STANDARD_1435MM"]["max_speed_kmh"] == 350.0
        assert "METRE_1000MM" in RAIL_GAUGES
        assert RAIL_GAUGES["METRE_1000MM"]["gauge_mm"] == 1000
        assert RAIL_GAUGES["METRE_1000MM"]["max_speed_kmh"] == 120.0
        assert "DUAL_GAUGE" in RAIL_GAUGES

        # Categories
        assert "HIGH_SPEED_RAIL" in RAIL_CATEGORIES
        assert RAIL_CATEGORIES["HIGH_SPEED_RAIL"]["min_corridor_buffer_m"] == 20.0
        assert RAIL_CATEGORIES["HIGH_SPEED_RAIL"]["barrier_mandatory"] is True
        assert "URBAN_METRO" in RAIL_CATEGORIES
        assert RAIL_CATEGORIES["URBAN_METRO"]["min_corridor_buffer_m"] == 5.0
        assert "NATIONAL_RAIL" in RAIL_CATEGORIES
        assert RAIL_CATEGORIES["NATIONAL_RAIL"]["min_corridor_buffer_m"] == 15.0

        # Lifespans
        assert ROLLING_STOCK_LIFESPANS["EMU_TRAINSET"] == 30
        assert ROLLING_STOCK_LIFESPANS["LOCOMOTIVE_DIESEL"] == 40
        assert ROLLING_STOCK_LIFESPANS["FREIGHT_WAGON"] == 45

        # Freight Rates
        assert FREIGHT_RATES_VND_PER_TON_KM["CONTAINER_TEU"] == 850.0
        assert FREIGHT_RATES_VND_PER_TON_KM["BULK_AGRICULTURAL"] == 650.0

    def test_register_railway_line_high_speed(self, engine: RailwayEngine) -> None:
        res = engine.register_railway_line(
            line_name="Tuyến Đường Sắt Tốc Độ Cao Bắc - Nam",
            line_code="HSR-BN-01",
            rail_category="HIGH_SPEED_RAIL",
            gauge_type="STANDARD_1435MM",
            length_km=1541.0,
            stations_count=23,
            design_speed_kmh=350.0,
            is_electrified=True,
            operator_name="Tổng Công ty Đường sắt Việt Nam (VNR)",
        )
        assert res["ok"] is True
        assert res["line_id"].startswith("RLN-")
        prof = res["line_profile"]
        assert prof["line_code"] == "HSR-BN-01"
        assert prof["gauge_mm"] == 1435
        assert prof["design_speed_kmh"] == 350.0
        assert prof["is_electrified"] is True
        assert prof["statutory_corridor_min_m"] == 20.0
        assert prof["barrier_mandatory"] is True

        lines = engine.list_railway_lines()
        assert len(lines) == 1
        assert lines[0]["line_code"] == "HSR-BN-01"

    def test_register_railway_line_speed_capped_by_gauge(self, engine: RailwayEngine) -> None:
        # Metre gauge (1000mm) cannot exceed 120 km/h physical cap
        res = engine.register_railway_line(
            line_name="Tuyến Đường Sắt Thống Nhất Hiện Hữu",
            line_code="NR-BN-OLD",
            rail_category="NATIONAL_RAIL",
            gauge_type="METRE_1000MM",
            length_km=1726.0,
            stations_count=190,
            design_speed_kmh=160.0,  # Requested 160, should cap at 120
            is_electrified=False,
        )
        assert res["line_profile"]["design_speed_kmh"] == 120.0
        assert res["line_profile"]["is_electrified"] is False

    def test_audit_safety_corridor_high_speed_compliant(self, engine: RailwayEngine) -> None:
        res = engine.audit_safety_corridor(
            line_id="RLN-HSR-01",
            structure_type="AT_GRADE",
            speed_kmh=350.0,
            actual_buffer_m=22.5,
        )
        assert res["ok"] is True
        assert res["audit_id"].startswith("SCA-")
        c = res["corridor_audit"]
        assert c["required_buffer_m"] == 20.0
        assert c["actual_buffer_m"] == 22.5
        assert c["is_corridor_compliant"] is True
        assert "ĐẠT TIÊU CHUẨN" in c["corridor_verdict"]

        audits = engine.list_corridor_audits()
        assert len(audits) == 1

    def test_audit_safety_corridor_high_speed_violation(self, engine: RailwayEngine) -> None:
        res = engine.audit_safety_corridor(
            line_id="RLN-HSR-02",
            structure_type="AT_GRADE",
            speed_kmh=350.0,
            actual_buffer_m=14.0,  # Requires 20m
        )
        assert res["ok"] is True
        c = res["corridor_audit"]
        assert c["is_corridor_compliant"] is False
        assert "VI PHẠM" in c["corridor_verdict"]

    def test_audit_safety_corridor_metro_elevated_and_tunnel(self, engine: RailwayEngine) -> None:
        # Metro elevated: requires 5.0m
        res_viaduct = engine.audit_safety_corridor(
            line_id="RLN-METRO-01",
            structure_type="ELEVATED_VIADUCT",
            speed_kmh=80.0,
            actual_buffer_m=6.5,
        )
        assert res_viaduct["corridor_audit"]["required_buffer_m"] == 5.0
        assert res_viaduct["corridor_audit"]["is_corridor_compliant"] is True

        # Metro underground: requires 3.0m
        res_tunnel = engine.audit_safety_corridor(
            line_id="RLN-METRO-02",
            structure_type="UNDERGROUND_TUNNEL",
            speed_kmh=80.0,
            actual_buffer_m=2.0,  # Requires 3.0m
        )
        assert res_tunnel["corridor_audit"]["required_buffer_m"] == 3.0
        assert res_tunnel["corridor_audit"]["is_corridor_compliant"] is False

    def test_register_rolling_stock_valid(self, engine: RailwayEngine) -> None:
        res = engine.register_rolling_stock(
            vehicle_code="HSR-EMU-350-01",
            vehicle_type="EMU_TRAINSET",
            manufacturer="Hitachi Rail / CRRC",
            year_built=2024,
            gauge_type="STANDARD_1435MM",
            current_year=2026,
        )
        assert res["ok"] is True
        assert res["vehicle_id"].startswith("RSK-")
        r = res["rolling_stock"]
        assert r["age_years"] == 2
        assert r["max_legal_years"] == 30
        assert r["years_remaining"] == 28
        assert r["is_lifespan_valid"] is True

        stock = engine.list_rolling_stock()
        assert len(stock) == 1

    def test_register_rolling_stock_expired(self, engine: RailwayEngine) -> None:
        # Diesel locomotive built in 1980 (age 46 > 40 max)
        res = engine.register_rolling_stock(
            vehicle_code="D19E-901-OLD",
            vehicle_type="LOCOMOTIVE_DIESEL",
            manufacturer="CSR Ziyang",
            year_built=1980,
            current_year=2026,
        )
        assert res["ok"] is True
        r = res["rolling_stock"]
        assert r["age_years"] == 46
        assert r["is_lifespan_valid"] is False
        assert "HẾT NIÊN HẠN" in r["lifespan_verdict"]

    def test_calculate_freight_tariff(self, engine: RailwayEngine) -> None:
        # Container TEU: 24 tons, 850 km, rate 850 VND/ton.km
        res = engine.calculate_freight_tariff(
            shipper_name="Công ty TNHH Vận Tải Logistics Sài Gòn",
            cargo_type="CONTAINER_TEU",
            weight_tons=24.0,
            distance_km=850.0,
        )
        assert res["ok"] is True
        assert res["order_id"].startswith("RFO-")
        b = res["freight_bill"]
        assert b["ton_km"] == 24.0 * 850.0  # 20,400 ton-km
        assert b["base_freight_vnd"] == 20400.0 * 850.0  # 17,340,000 VND
        assert b["terminal_handling_vnd"] == 24.0 * 45000.0  # 1,080,000 VND
        expected_subtotal = 17340000.0 + 1080000.0  # 18,420,000 VND
        assert b["subtotal_vnd"] == expected_subtotal
        assert b["vat_vnd"] == expected_subtotal * 0.10
        assert b["total_amount_vnd"] == expected_subtotal * 1.10

        orders = engine.list_freight_orders()
        assert len(orders) == 1

    def test_audit_train_driver_license_granted(self, engine: RailwayEngine) -> None:
        res = engine.audit_train_driver_license(
            driver_name="Nguyễn Văn Hùng",
            license_type="HIGH_SPEED_EMU",
            driver_age=36,
            experience_months=48,  # HSR requires >= 36 months
            health_class=1,
        )
        assert res["ok"] is True
        assert res["license_id"].startswith("TDL-")
        d = res["driver_license_audit"]
        assert d["age_compliant"] is True
        assert d["experience_compliant"] is True
        assert d["health_compliant"] is True
        assert d["is_license_granted"] is True

        licenses = engine.list_driver_licenses()
        assert len(licenses) == 1

    def test_audit_train_driver_license_rejected(self, engine: RailwayEngine) -> None:
        # Underage or insufficient practice
        res = engine.audit_train_driver_license(
            driver_name="Lê Trọng Tuấn",
            license_type="HIGH_SPEED_EMU",
            driver_age=20,  # Min 21
            experience_months=12,  # Min 36
            health_class=2,  # Class 1 required
        )
        d = res["driver_license_audit"]
        assert d["age_compliant"] is False
        assert d["experience_compliant"] is False
        assert d["health_compliant"] is False
        assert d["is_license_granted"] is False

    def test_status_telemetry(self, engine: RailwayEngine) -> None:
        engine.register_railway_line("Tuyến 1", "T1")
        engine.audit_safety_corridor("T1", actual_buffer_m=25.0)
        engine.register_rolling_stock("V1", year_built=2024)
        engine.calculate_freight_tariff("Shipper 1", weight_tons=50.0, distance_km=100.0)
        engine.audit_train_driver_license("Driver 1", health_class=1, experience_months=40)

        status = engine.get_status()
        assert status["ok"] is True
        m = status["metrics"]
        assert m["registered_railway_lines"] == 1
        assert m["corridor_safety_audits"] == 1
        assert m["compliant_corridor_sections"] == 1
        assert m["registered_rolling_stock_vehicles"] == 1
        assert m["legal_active_rolling_stock"] == 1
        assert m["freight_transport_orders"] == 1
        assert m["driver_license_audits"] == 1
        assert m["licensed_train_drivers"] == 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestRailwayCLI:
    """Test Typer CLI commands for railway management."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_help(self, app) -> None:
        result = runner.invoke(app, ["railway", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Railway Transport" in result.output
        assert "line" in result.output
        assert "corridor" in result.output
        assert "stock" in result.output
        assert "freight" in result.output
        assert "driver" in result.output
        assert "list" in result.output
        assert "status" in result.output

    def test_cli_main_status(self, app) -> None:
        result = runner.invoke(app, ["railway"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ ĐƯỜNG SẮT" in result.output

    def test_cli_main_status_json(self, app) -> None:
        result = runner.invoke(app, ["railway", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_line_command(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(app, [
            "railway", "line", "Tuyến Cao Tốc Bắc Nam", "HSR-CLI-01",
            "--category", "HIGH_SPEED_RAIL",
            "--gauge", "STANDARD_1435MM",
            "--length", "1541.0",
            "--stations", "23",
            "--speed", "350.0",
            "--electrified",
            "--json",
        ])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["line_profile"]["line_code"] == "HSR-CLI-01"

        # Console mode
        res_console = runner.invoke(app, [
            "railway", "line", "Metro Tuyến 1 Bến Thành - Suối Tiên", "METRO-HCM-01",
            "--category", "URBAN_METRO",
            "--length", "19.7",
            "--stations", "14",
        ])
        assert res_console.exit_code == 0
        assert "Metro Tuyến 1" in res_console.output

    def test_cli_corridor_command(self, app) -> None:
        res = runner.invoke(app, [
            "railway", "corridor", "RLN-CLI01",
            "--structure", "AT_GRADE",
            "--speed", "350.0",
            "--buffer", "25.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["corridor_audit"]["is_corridor_compliant"] is True

        res_con = runner.invoke(app, ["railway", "corridor", "RLN-CLI02"])
        assert res_con.exit_code == 0
        assert "Hành Lang An Toàn Đường Sắt" in res_con.output

    def test_cli_stock_command(self, app) -> None:
        res = runner.invoke(app, [
            "railway", "stock", "HSR-TRAIN-01",
            "--type", "EMU_TRAINSET",
            "--maker", "Hitachi",
            "--year", "2024",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["rolling_stock"]["is_lifespan_valid"] is True

        res_con = runner.invoke(app, ["railway", "stock", "D19E-902"])
        assert res_con.exit_code == 0
        assert "Hồ Sơ Đăng Kiểm Niên Hạn" in res_con.output

    def test_cli_freight_command(self, app) -> None:
        res = runner.invoke(app, [
            "railway", "freight", "Tập Đoàn Than Khoáng Sản",
            "--type", "HEAVY_INDUSTRIAL",
            "--weight", "100.0",
            "--distance", "500.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["freight_bill"]["ton_km"] == 50000.0

        res_con = runner.invoke(app, ["railway", "freight", "Vinatex"])
        assert res_con.exit_code == 0
        assert "Biểu Cước Vận Tải Hàng Hóa Đường Sắt" in res_con.output

    def test_cli_driver_command(self, app) -> None:
        res = runner.invoke(app, [
            "railway", "driver", "Trần Đình Trọng",
            "--type", "HIGH_SPEED_EMU",
            "--age", "38",
            "--exp", "40",
            "--health", "1",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["driver_license_audit"]["is_license_granted"] is True

        res_con = runner.invoke(app, ["railway", "driver", "Phạm Văn Minh"])
        assert res_con.exit_code == 0
        assert "Sát Hạch Giấy Phép Lái Tàu" in res_con.output

    def test_cli_list_commands(self, app) -> None:
        for cat in ("lines", "corridor", "stock", "freight", "drivers"):
            res = runner.invoke(app, ["railway", "list", cat, "--json"])
            assert res.exit_code == 0
            assert "{" in res.output

        res_table = runner.invoke(app, ["railway", "list", "lines"])
        assert res_table.exit_code == 0
        assert "Danh Sách Dữ Liệu Đường Sắt" in res_table.output

    def test_cli_status_subcommand(self, app) -> None:
        res = runner.invoke(app, ["railway", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True

        res_con = runner.invoke(app, ["railway", "status"])
        assert res_con.exit_code == 0
        assert "Tổng Quan Vận Tải Đường Sắt" in res_con.output


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestRailwayMCP:
    """Test Dual FastMCP & fallback stdio JSON-RPC MCP handlers."""

    def test_src_core_mcp_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Line
        line_raw = server._handle_railway_line(
            line_name="Tuyến MCP Core HSR",
            line_code="HSR-MCP-01",
            design_speed_kmh=350.0,
        )
        line_data = json.loads(line_raw)
        assert line_data["ok"] is True
        line_id = line_data["line_id"]

        # 2. Corridor
        corr_raw = server._handle_railway_corridor(
            line_id=line_id,
            structure_type="AT_GRADE",
            speed_kmh=350.0,
            actual_buffer_m=22.0,
        )
        corr_data = json.loads(corr_raw)
        assert corr_data["ok"] is True
        assert corr_data["corridor_audit"]["is_corridor_compliant"] is True

        # 3. Stock
        stock_raw = server._handle_railway_stock(
            vehicle_code="EMU-MCP-01",
            year_built=2024,
        )
        stock_data = json.loads(stock_raw)
        assert stock_data["ok"] is True
        assert stock_data["rolling_stock"]["is_lifespan_valid"] is True

        # 4. Freight
        freight_raw = server._handle_railway_freight(
            shipper_name="Mekong Logistics",
            weight_tons=30.0,
            distance_km=600.0,
        )
        freight_data = json.loads(freight_raw)
        assert freight_data["ok"] is True
        assert freight_data["freight_bill"]["ton_km"] == 18000.0

        # 5. Driver
        driver_raw = server._handle_railway_driver(
            driver_name="Tài Xế MCP",
            driver_age=32,
            experience_months=36,
            health_class=1,
        )
        driver_data = json.loads(driver_raw)
        assert driver_data["ok"] is True
        assert driver_data["driver_license_audit"]["is_license_granted"] is True

        # 6. List
        list_raw = server._handle_railway_list(category="lines")
        list_data = json.loads(list_raw)
        assert isinstance(list_data, list)
        assert len(list_data) >= 1

        # 7. Status
        status_raw = server._handle_railway_status()
        status_data = json.loads(status_raw)
        assert status_data["ok"] is True
        assert "metrics" in status_data

    def test_scripts_mcp_server_handlers_and_spec_parity(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_railway_corridor,
            handle_railway_driver,
            handle_railway_freight,
            handle_railway_line,
            handle_railway_list,
            handle_railway_status,
            handle_railway_stock,
        )

        # Check specification presence
        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        assert "mekong_railway_line" in tool_names
        assert "mekong_railway_corridor" in tool_names
        assert "mekong_railway_stock" in tool_names
        assert "mekong_railway_freight" in tool_names
        assert "mekong_railway_driver" in tool_names
        assert "mekong_railway_list" in tool_names
        assert "mekong_railway_status" in tool_names

        # Check CORE_HANDLERS mapping
        assert "mekong_railway_line" in CORE_HANDLERS
        assert "mekong_railway_corridor" in CORE_HANDLERS
        assert "mekong_railway_stock" in CORE_HANDLERS
        assert "mekong_railway_freight" in CORE_HANDLERS
        assert "mekong_railway_driver" in CORE_HANDLERS
        assert "mekong_railway_list" in CORE_HANDLERS
        assert "mekong_railway_status" in CORE_HANDLERS

        # Test scripts handlers directly
        line_res = json.loads(handle_railway_line({"line_name": "Tuyến Script", "line_code": "SCR-01"}))
        assert line_res["ok"] is True
        lid = line_res["line_id"]

        corr_res = json.loads(handle_railway_corridor({"line_id": lid, "actual_buffer_m": 25.0}))
        assert corr_res["ok"] is True

        stock_res = json.loads(handle_railway_stock({"vehicle_code": "SCR-VEH-01"}))
        assert stock_res["ok"] is True

        freight_res = json.loads(handle_railway_freight({"shipper_name": "Script Shipper", "weight_tons": 10.0, "distance_km": 100.0}))
        assert freight_res["ok"] is True

        driver_res = json.loads(handle_railway_driver({"driver_name": "Script Driver", "health_class": 1, "experience_months": 40}))
        assert driver_res["ok"] is True

        list_res = json.loads(handle_railway_list({"category": "lines"}))
        assert isinstance(list_res, list)

        stat_res = json.loads(handle_railway_status({}))
        assert stat_res["ok"] is True
