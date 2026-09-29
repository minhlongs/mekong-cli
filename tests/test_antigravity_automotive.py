# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite (Phase 83)."""

from __future__ import annotations

import ast
import datetime
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.automotive_engine import (
    EURO5_EMISSION_LIMITS,
    MIN_AUTHORIZED_SERVICE_CENTERS,
    MIN_TEST_TRACK_LENGTH_METERS,
    VEHICLE_TYPES,
    AutomotiveEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestAutomotiveCoreBoundary:
    """Ensure AutomotiveEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/automotive_engine.py")
        assert source_path.exists(), "automotive_engine.py must exist"

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


class TestAutomotiveEngine:
    """Test AutomotiveEngine manufacturing licensing, VTA, RVC localization, EV battery & inspection."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> AutomotiveEngine:
        db_file = tmp_path / "test_automotive.db"
        return AutomotiveEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Vehicle Types
        assert "PASSENGER_CAR_UNDER_9" in VEHICLE_TYPES
        assert "COMMERCIAL_PASSENGER" in VEHICLE_TYPES
        assert "COMMERCIAL_TRUCK" in VEHICLE_TYPES
        assert "ELECTRIC_VEHICLE" in VEHICLE_TYPES

        # Euro 5 emission limits
        assert "GASOLINE" in EURO5_EMISSION_LIMITS
        assert EURO5_EMISSION_LIMITS["GASOLINE"]["co_max_g_km"] == 1.00
        assert EURO5_EMISSION_LIMITS["GASOLINE"]["nox_max_g_km"] == 0.060
        assert "DIESEL" in EURO5_EMISSION_LIMITS
        assert EURO5_EMISSION_LIMITS["DIESEL"]["co_max_g_km"] == 0.50

        # Decree 116 minimum standards
        assert MIN_TEST_TRACK_LENGTH_METERS == 800.0
        assert MIN_AUTHORIZED_SERVICE_CENTERS == 10

    def test_license_manufacturer_success(self, engine: AutomotiveEngine) -> None:
        res = engine.license_manufacturer(
            company_name="Nhà máy Sản xuất Ô tô VinFast",
            tax_id="0108877665",
            factory_address="KCN Đình Vũ - Cát Hải, Hải Phòng, Việt Nam",
            test_track_length_m=850.0,
            has_side_slip_tester=True,
            has_brake_tester=True,
            has_emission_tester=True,
            authorized_service_centers_count=85,
        )
        assert res["is_compliant"] is True
        assert res["status"] == "LICENSED"
        assert res["test_track_length_m"] == 850.0
        assert len(res["deficiencies"]) == 0
        assert res["license_number"].startswith("GP-SX-")

        mfgs = engine.list_manufacturers()
        assert len(mfgs) == 1
        assert mfgs[0]["company_name"] == "Nhà máy Sản xuất Ô tô VinFast"

    def test_license_manufacturer_deficiencies(self, engine: AutomotiveEngine) -> None:
        res = engine.license_manufacturer(
            company_name="Xưởng Ô tô Thiếu Chuẩn",
            tax_id="0109999999",
            test_track_length_m=500.0,  # Below 800m
            has_side_slip_tester=False,
            has_brake_tester=True,
            has_emission_tester=False,
            authorized_service_centers_count=5,  # Below 10
        )
        assert res["is_compliant"] is False
        assert res["status"] == "NON_COMPLIANT"
        assert len(res["deficiencies"]) == 4

    def test_license_manufacturer_validation_errors(self, engine: AutomotiveEngine) -> None:
        with pytest.raises(ValueError, match="Chiều dài đường thử xe không được âm"):
            engine.license_manufacturer("Cơ sở Sai", test_track_length_m=-10.0)

        with pytest.raises(ValueError, match="Số lượng cơ sở bảo hành, bảo dưỡng ủy quyền không được âm"):
            engine.license_manufacturer("Cơ sở Sai", authorized_service_centers_count=-2)

    def test_audit_type_approval_euro5_and_rvc(self, engine: AutomotiveEngine) -> None:
        # Gasoline meeting Euro 5 and RVC >= 40%
        res_gas = engine.audit_type_approval(
            model_name="Mekong Lux A2.0",
            vehicle_type="PASSENGER_CAR_UNDER_9",
            powertrain_type="GASOLINE",
            co_g_km=0.65,
            nox_g_km=0.045,
            pm_g_km=0.002,
            rvc_rate_pct=42.5,
        )
        assert res_gas["is_emission_compliant"] is True
        assert res_gas["is_rvc_eligible_form_d"] is True
        assert res_gas["status"] == "CERTIFIED"

        # Electric Vehicle (zero emissions)
        res_ev = engine.audit_type_approval(
            model_name="Mekong E-SUV VF8",
            vehicle_type="ELECTRIC_VEHICLE",
            powertrain_type="ELECTRIC",
            co_g_km=0.0,
            nox_g_km=0.0,
            pm_g_km=0.0,
            rvc_rate_pct=48.0,
        )
        assert res_ev["is_emission_compliant"] is True
        assert res_ev["emission_standard"] == "ZERO_EMISSION"
        assert res_ev["status"] == "CERTIFIED"

        # Failed Euro 5
        res_fail = engine.audit_type_approval(
            model_name="Mekong Xe Khói",
            vehicle_type="PASSENGER_CAR_UNDER_9",
            powertrain_type="GASOLINE",
            co_g_km=1.50,  # exceeds 1.00
            nox_g_km=0.080,  # exceeds 0.060
            pm_g_km=0.010,  # exceeds 0.0045
            rvc_rate_pct=30.0,
        )
        assert res_fail["is_emission_compliant"] is False
        assert res_fail["is_rvc_eligible_form_d"] is False
        assert res_fail["status"] == "REJECTED"
        assert len(res_fail["emission_violations"]) == 3

    def test_calculate_rvc_localization(self, engine: AutomotiveEngine) -> None:
        # 650M FOB, 320M VNM -> Local = 330M -> RVC = 50.77% >= 40%
        res_ok = engine.calculate_rvc_localization(
            model_name="Mekong Sedan Lux",
            fob_price_vnd=650_000_000.0,
            non_originating_materials_vnd=320_000_000.0,
        )
        assert res_ok["rvc_rate_pct"] == 50.77
        assert res_ok["is_eligible_form_d"] is True
        assert res_ok["preferential_import_duty_pct"] == 0.0

        # Low localization
        res_low = engine.calculate_rvc_localization(
            model_name="Mekong CBU CKD",
            fob_price_vnd=600_000_000.0,
            non_originating_materials_vnd=450_000_000.0,  # Local = 150M -> RVC = 25% < 40%
        )
        assert res_low["rvc_rate_pct"] == 25.0
        assert res_low["is_eligible_form_d"] is False
        assert res_low["preferential_import_duty_pct"] == 70.0

    def test_calculate_rvc_validation_errors(self, engine: AutomotiveEngine) -> None:
        with pytest.raises(ValueError, match="Giá xuất xưởng/FOB xe phải lớn hơn 0"):
            engine.calculate_rvc_localization("Xe", fob_price_vnd=0.0, non_originating_materials_vnd=0.0)

        with pytest.raises(ValueError, match="Trị giá nguyên liệu ngoại nhập không được vượt quá giá FOB"):
            engine.calculate_rvc_localization("Xe", fob_price_vnd=500.0, non_originating_materials_vnd=600.0)

    def test_audit_ev_battery_safety(self, engine: AutomotiveEngine) -> None:
        # Full compliance
        res_ev = engine.audit_ev_battery_safety(
            model_name="Mekong E-SUV VF8",
            battery_chemistry="LFP",
            nominal_voltage_v=400.0,
            pack_capacity_kwh=87.7,
            overcharge_test_passed=True,
            short_circuit_test_passed=True,
            water_immersion_ip67=True,
            thermal_propagation_safe=True,
            crash_cutoff_ms=35.0,
        )
        assert res_ev["is_qcvn91_certified"] is True
        assert res_ev["verdict"] == "QCVN_CERTIFIED"
        assert len(res_ev["violations"]) == 0

        # Failed battery safety
        res_fail = engine.audit_ev_battery_safety(
            model_name="Pin Lỗi Thử Nghiệm",
            overcharge_test_passed=False,
            short_circuit_test_passed=True,
            water_immersion_ip67=False,
            thermal_propagation_safe=False,
            crash_cutoff_ms=150.0,  # > 100 ms
        )
        assert res_fail["is_qcvn91_certified"] is False
        assert res_fail["verdict"] == "SAFETY_FAIL"
        assert len(res_fail["violations"]) == 4

    def test_calculate_inspection_schedule(self, engine: AutomotiveEngine) -> None:
        today_year = datetime.date.today().year

        # Brand new non-commercial car: 36 months exempt
        res_new = engine.calculate_inspection_schedule(
            plate_number="51K-999.88",
            vehicle_category="PASSENGER_CAR_UNDER_9",
            is_commercial=False,
            manufacture_year=today_year,
            last_inspection_date=None,
        )
        assert res_new["cycle_months"] == 36
        assert res_new["is_exempt_first_inspection"] is True

        # 4-year-old car: 24 months
        res_mid = engine.calculate_inspection_schedule(
            plate_number="30H-123.45",
            vehicle_category="PASSENGER_CAR_UNDER_9",
            is_commercial=False,
            manufacture_year=today_year - 4,
            last_inspection_date="2024-01-15",
        )
        assert res_mid["cycle_months"] == 24
        assert res_mid["is_exempt_first_inspection"] is False

        # Commercial passenger vehicle: 12 months
        res_comm = engine.calculate_inspection_schedule(
            plate_number="29E-555.66",
            vehicle_category="COMMERCIAL_PASSENGER",
            is_commercial=True,
            manufacture_year=today_year - 2,
            last_inspection_date="2024-06-01",
        )
        assert res_comm["cycle_months"] == 12

    def test_get_status_telemetry(self, engine: AutomotiveEngine) -> None:
        engine.license_manufacturer("VinFast")
        engine.audit_type_approval("VF8", vehicle_type="ELECTRIC_VEHICLE", powertrain_type="ELECTRIC")
        engine.audit_ev_battery_safety("VF8")
        engine.calculate_inspection_schedule("51K-999.88")

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["manufacturers"]["total_licensed"] == 1
        assert status["type_approval"]["certified_models"] == 1
        assert status["electric_vehicles"]["qcvn91_certified_packs"] == 1
        assert status["inspections"]["total_scheduled"] == 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestAutomotiveCLI:
    """Test Typer CLI surface under 'mekong automotive'."""

    @pytest.fixture(autouse=True)
    def setup_app(self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
        db_file = tmp_path / "cli_automotive.db"
        from src.core.automotive_engine import AutomotiveEngine

        orig_init = AutomotiveEngine.__init__

        def custom_init(self: AutomotiveEngine, db_path: str | pathlib.Path | None = None) -> None:
            orig_init(self, db_path=db_file)

        monkeypatch.setattr(AutomotiveEngine, "__init__", custom_init)

    def test_automotive_cli_main_status(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["automotive"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ SẢN XUẤT Ô TÔ" in result.output

    def test_automotive_cli_json_mode(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["automotive", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "manufacturers" in data

    def test_automotive_cli_license(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "automotive",
                "license",
                "Nhà máy Ô tô Thaco Chu Lai",
                "--tax-id",
                "4000393849",
                "--address",
                "Kinh tế mở Chu Lai, Quảng Nam",
                "--track",
                "1000",
                "--side-slip",
                "--brake",
                "--emission",
                "--service-centers",
                "120",
            ],
        )
        assert result.exit_code == 0
        assert "KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN SẢN XUẤT" in result.output
        assert "Nhà máy Ô tô Thaco Chu Lai" in result.output

    def test_automotive_cli_vta(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "automotive",
                "vta",
                "Mekong E-SUV VF8",
                "--type",
                "ELECTRIC_VEHICLE",
                "--powertrain",
                "ELECTRIC",
                "--co",
                "0",
                "--nox",
                "0",
                "--pm",
                "0",
                "--rvc",
                "45.0",
            ],
        )
        assert result.exit_code == 0
        assert "CHỨNG NHẬN CHẤT LƯỢNG AN TOÀN KỸ THUẬT" in result.output
        assert "CERTIFIED" in result.output

    def test_automotive_cli_rvc(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "automotive",
                "rvc",
                "Mekong Sedan Lux",
                "700000000",
                "350000000",
            ],
        )
        assert result.exit_code == 0
        assert "TÍNH TOÁN HÀM LƯỢNG GIÁ TRỊ KHU VỰC" in result.output
        assert "50.00%" in result.output

    def test_automotive_cli_battery(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "automotive",
                "battery",
                "Mekong E-SUV VF8",
                "--chemistry",
                "LFP",
                "--voltage",
                "400",
                "--capacity",
                "87.7",
                "--overcharge",
                "--short-circuit",
                "--ip67",
                "--thermal",
                "--cutoff",
                "35",
            ],
        )
        assert result.exit_code == 0
        assert "KIỂM TOÁN AN TOÀN PIN XE ĐIỆN" in result.output
        assert "QCVN_CERTIFIED" in result.output

    def test_automotive_cli_inspect(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "automotive",
                "inspect",
                "51K-999.88",
                "--category",
                "PASSENGER_CAR_UNDER_9",
                "--non-commercial",
                "--year",
                "2026",
            ],
        )
        assert result.exit_code == 0
        assert "LỊCH HẠN ĐĂNG KIỂM XE CƠ GIỚI" in result.output
        assert "36 tháng" in result.output

    def test_automotive_cli_list_and_status(self) -> None:
        app = build_app()
        # List manufacturers
        res_mfg = runner.invoke(app, ["automotive", "list", "manufacturers"])
        assert res_mfg.exit_code == 0
        assert "DANH SÁCH DOANH NGHIỆP SẢN XUẤT" in res_mfg.output

        # List inspections
        res_ins = runner.invoke(app, ["automotive", "list", "inspections"])
        assert res_ins.exit_code == 0
        assert "SỔ QUẢN LÝ HẠN ĐĂNG KIỂM" in res_ins.output

        # Status
        res_stat = runner.invoke(app, ["automotive", "status", "--json"])
        assert res_stat.exit_code == 0
        data = json.loads(res_stat.output)
        assert data["status"] == "HEALTHY"


# ---------------------------------------------------------------------------
# MCP Server Dual-Engine Parity Tests
# ---------------------------------------------------------------------------


class TestAutomotiveMcpParity:
    """Ensure Automotive MCP tools function identically across FastMCP and JSON-RPC fallback."""

    @pytest.fixture(autouse=True)
    def setup_mcp_db(self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
        db_file = tmp_path / "mcp_automotive.db"
        from src.core.automotive_engine import AutomotiveEngine

        orig_init = AutomotiveEngine.__init__

        def custom_init(self: AutomotiveEngine, db_path: str | pathlib.Path | None = None) -> None:
            orig_init(self, db_path=db_file)

        monkeypatch.setattr(AutomotiveEngine, "__init__", custom_init)

    def test_mcp_scripts_server_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        assert "mekong_automotive_license" in CORE_HANDLERS
        assert "mekong_automotive_vta" in CORE_HANDLERS
        assert "mekong_automotive_rvc" in CORE_HANDLERS
        assert "mekong_automotive_battery" in CORE_HANDLERS
        assert "mekong_automotive_inspect" in CORE_HANDLERS
        assert "mekong_automotive_list" in CORE_HANDLERS
        assert "mekong_automotive_status" in CORE_HANDLERS

        # Test license
        res_lic_str = CORE_HANDLERS["mekong_automotive_license"]({
            "company_name": "Tổ hợp Ô tô Hải Phòng",
            "test_track_length_m": 900.0,
            "has_side_slip_tester": True,
            "has_brake_tester": True,
            "has_emission_tester": True,
            "authorized_service_centers_count": 50,
        })
        res_lic = json.loads(res_lic_str)
        assert res_lic["is_compliant"] is True
        assert res_lic["status"] == "LICENSED"

        # Test RVC
        res_rvc_str = CORE_HANDLERS["mekong_automotive_rvc"]({
            "model_name": "Mekong VF9",
            "fob_price_vnd": 1000000000.0,
            "non_originating_materials_vnd": 500000000.0,
        })
        res_rvc = json.loads(res_rvc_str)
        assert res_rvc["rvc_rate_pct"] == 50.0

        # Test battery
        res_bat_str = CORE_HANDLERS["mekong_automotive_battery"]({
            "model_name": "Mekong VF9",
            "battery_chemistry": "NMC",
            "pack_capacity_kwh": 123.0,
        })
        res_bat = json.loads(res_bat_str)
        assert res_bat["is_qcvn91_certified"] is True

        # Test status
        res_stat_str = CORE_HANDLERS["mekong_automotive_status"]({})
        res_stat = json.loads(res_stat_str)
        assert res_stat["status"] == "HEALTHY"

    def test_mcp_core_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_automotive_license")
        assert hasattr(server, "_handle_automotive_vta")
        assert hasattr(server, "_handle_automotive_rvc")
        assert hasattr(server, "_handle_automotive_battery")
        assert hasattr(server, "_handle_automotive_inspect")
        assert hasattr(server, "_handle_automotive_list")
        assert hasattr(server, "_handle_automotive_status")

        # Test VTA via core handler
        res_vta_str = server._handle_automotive_vta(
            model_name="VF6",
            vehicle_type="ELECTRIC_VEHICLE",
            powertrain_type="ELECTRIC",
        )
        res_vta = json.loads(res_vta_str)
        assert res_vta["status"] == "CERTIFIED"
