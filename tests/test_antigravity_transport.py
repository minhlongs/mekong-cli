# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation (Phase 73)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.transport_engine import (
    ETC_VEHICLE_CLASSES,
    TRANSPORT_BUSINESS_TYPES,
    VEHICLE_WEIGHT_CONFIGS,
    TransportEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestTransportCoreBoundary:
    """Ensure TransportEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/transport_engine.py")
        assert source_path.exists(), "transport_engine.py must exist"

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


class TestTransportEngine:
    """Test TransportEngine business licensing, badge issuance, ETC tolling, GPS monitoring, and overload auditing."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> TransportEngine:
        db_file = tmp_path / "test_transport.db"
        return TransportEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Transport business types
        assert "PASSENGER_COACH_FIXED" in TRANSPORT_BUSINESS_TYPES
        assert TRANSPORT_BUSINESS_TYPES["PASSENGER_COACH_FIXED"]["max_vehicle_age_years"] == 20
        assert TRANSPORT_BUSINESS_TYPES["PASSENGER_COACH_FIXED"]["requires_camera"] is True
        assert "PASSENGER_TAXI" in TRANSPORT_BUSINESS_TYPES
        assert TRANSPORT_BUSINESS_TYPES["PASSENGER_TAXI"]["max_vehicle_age_years"] == 12
        assert "CARGO_CONTAINER" in TRANSPORT_BUSINESS_TYPES
        assert TRANSPORT_BUSINESS_TYPES["CARGO_CONTAINER"]["requires_camera"] is True

        # ETC Vehicle Classes
        assert "CLASS_1" in ETC_VEHICLE_CLASSES
        assert ETC_VEHICLE_CLASSES["CLASS_1"]["standard_toll_vnd"] == 35000.0
        assert "CLASS_5" in ETC_VEHICLE_CLASSES
        assert ETC_VEHICLE_CLASSES["CLASS_5"]["standard_toll_vnd"] == 180000.0

        # Vehicle Weight Configs
        assert "RIGID_2AXLE" in VEHICLE_WEIGHT_CONFIGS
        assert VEHICLE_WEIGHT_CONFIGS["RIGID_2AXLE"]["max_gross_weight_tonnes"] == 16.0
        assert "ARTICULATED_5AXLE" in VEHICLE_WEIGHT_CONFIGS
        assert VEHICLE_WEIGHT_CONFIGS["ARTICULATED_5AXLE"]["max_gross_weight_tonnes"] == 44.0
        assert "ARTICULATED_6AXLE" in VEHICLE_WEIGHT_CONFIGS
        assert VEHICLE_WEIGHT_CONFIGS["ARTICULATED_6AXLE"]["max_gross_weight_tonnes"] == 48.0

    def test_issue_business_license_success(self, engine: TransportEngine) -> None:
        res = engine.issue_business_license(
            enterprise_name="Công ty Vận tải Phương Trang FUTA",
            tax_id="0303888999",
            business_type="PASSENGER_COACH_FIXED",
            authorized_fleet_size=300,
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["enterprise_name"] == "Công ty Vận tải Phương Trang FUTA"
        assert prof["badge_type"] == "XE TUYẾN CỐ ĐỊNH"
        assert prof["authorized_fleet_size"] == 300
        assert prof["status"] == "ACTIVE"

    def test_issue_business_license_invalid_type(self, engine: TransportEngine) -> None:
        with pytest.raises(ValueError, match="Loại hình kinh doanh không hợp lệ"):
            engine.issue_business_license(
                enterprise_name="Công ty Test",
                tax_id="0101234567",
                business_type="INVALID_BIZ_TYPE",
            )

    def test_issue_vehicle_badge_valid(self, engine: TransportEngine) -> None:
        lic = engine.issue_business_license(
            enterprise_name="Công ty Hoàng Long",
            tax_id="0202111222",
            business_type="PASSENGER_COACH_FIXED",
        )
        lic_num = lic["license_profile"]["license_number"]

        res = engine.issue_vehicle_badge(
            plate_number="15B-012.34",
            license_number=lic_num,
            vehicle_type="PASSENGER_COACH_FIXED",
            year_built=2022,
            seats_or_tonnage=45.0,
            has_gps=True,
            has_camera=True,
        )
        assert res["status"] == "success"
        prof = res["badge_profile"]
        assert prof["plate_number"] == "15B-012.34"
        assert prof["is_badge_granted"] is True
        assert prof["is_lifespan_valid"] is True
        assert prof["rejection_reason"] is None

    def test_issue_vehicle_badge_expired_lifespan(self, engine: TransportEngine) -> None:
        lic = engine.issue_business_license(
            enterprise_name="Công ty Mai Linh",
            tax_id="0303555666",
            business_type="PASSENGER_COACH_FIXED",
        )
        lic_num = lic["license_profile"]["license_number"]

        # 2000 built coach = 26 years old > 20 years legal limit
        res = engine.issue_vehicle_badge(
            plate_number="51B-999.00",
            license_number=lic_num,
            vehicle_type="PASSENGER_COACH_FIXED",
            year_built=2000,
            seats_or_tonnage=45.0,
            has_gps=True,
            has_camera=True,
        )
        assert res["status"] == "success"
        prof = res["badge_profile"]
        assert prof["is_badge_granted"] is False
        assert prof["is_lifespan_valid"] is False
        assert "quá niên hạn sử dụng" in prof["rejection_reason"]

    def test_issue_vehicle_badge_missing_camera_and_gps(self, engine: TransportEngine) -> None:
        lic = engine.issue_business_license(
            enterprise_name="Công ty Tân Đệ",
            tax_id="0404777888",
            business_type="CARGO_CONTAINER",
        )
        lic_num = lic["license_profile"]["license_number"]

        # Missing dashcam on container tractor truck
        res = engine.issue_vehicle_badge(
            plate_number="50LD-123.45",
            license_number=lic_num,
            vehicle_type="CARGO_CONTAINER",
            year_built=2023,
            seats_or_tonnage=32.0,
            has_gps=True,
            has_camera=False,
        )
        prof = res["badge_profile"]
        assert prof["is_badge_granted"] is False
        assert "Thiếu camera" in prof["rejection_reason"]

    def test_process_etc_toll_success(self, engine: TransportEngine) -> None:
        res = engine.process_etc_toll(
            plate_number="30E-123.45",
            etag_id="E-TAG-VETC-001122",
            bot_station_name="Trạm BOT Pháp Vân - Cầu Giẽ",
            vehicle_class="CLASS_1",
            account_balance_vnd=500000.0,
        )
        assert res["status"] == "success"
        prof = res["transaction_profile"]
        assert prof["toll_fee_vnd"] == 35000.0
        assert prof["remaining_balance_vnd"] == 465000.0
        assert prof["transaction_status"] == "SUCCESS"

    def test_process_etc_toll_insufficient_funds(self, engine: TransportEngine) -> None:
        res = engine.process_etc_toll(
            plate_number="50H-999.88",
            etag_id="E-TAG-EPASS-445566",
            bot_station_name="Trạm BOT Long Thành - Dầu Giây",
            vehicle_class="CLASS_5",
            account_balance_vnd=50000.0,  # Class 5 fee is 180,000 VND
        )
        prof = res["transaction_profile"]
        assert prof["toll_fee_vnd"] == 180000.0
        assert prof["remaining_balance_vnd"] == 50000.0
        assert prof["transaction_status"] == "INSUFFICIENT_FUNDS"

    def test_process_etc_toll_invalid_class(self, engine: TransportEngine) -> None:
        with pytest.raises(ValueError, match="Loại phương tiện ETC không hợp lệ"):
            engine.process_etc_toll(
                plate_number="29A-000.01",
                etag_id="E-TAG-001",
                bot_station_name="Trạm BOT",
                vehicle_class="CLASS_INVALID",
            )

    def test_audit_journey_monitoring_compliant(self, engine: TransportEngine) -> None:
        res = engine.audit_journey_monitoring(
            plate_number="51B-234.56",
            driver_name="Nguyễn Văn Hùng",
            driver_license_num="GPLX-E-123456",
            continuous_driving_hours=3.5,
            daily_driving_hours=8.0,
            last_rest_minutes=20,
            camera_online=True,
            gps_online=True,
        )
        assert res["status"] == "success"
        aud = res["journey_audit"]
        assert aud["is_compliant"] is True
        assert aud["violations_count"] == 0
        assert aud["violation_details"] is None

    def test_audit_journey_monitoring_violations(self, engine: TransportEngine) -> None:
        # Continuous driving > 4h, daily > 10h, and GPS offline
        res = engine.audit_journey_monitoring(
            plate_number="51B-234.56",
            driver_name="Trần Văn Nam",
            driver_license_num="GPLX-E-654321",
            continuous_driving_hours=4.8,
            daily_driving_hours=11.2,
            last_rest_minutes=10,
            camera_online=True,
            gps_online=False,
        )
        aud = res["journey_audit"]
        assert aud["is_compliant"] is False
        assert aud["violations_count"] >= 3
        assert "quá 4 giờ" in aud["violation_details"]
        assert "quá 10 giờ" in aud["violation_details"]
        assert "Mất tín hiệu" in aud["violation_details"]

    def test_audit_vehicle_weight_compliant(self, engine: TransportEngine) -> None:
        res = engine.audit_vehicle_weight(
            plate_number="29C-111.22",
            vehicle_configuration="RIGID_2AXLE",
            gross_weight_tonnes=15.0,  # limit is 16.0t
        )
        assert res["status"] == "success"
        aud = res["weight_audit"]
        assert aud["is_overloaded"] is False
        assert aud["is_tolerance_zone"] is False
        assert aud["fine_driver_vnd"] == 0.0
        assert aud["requires_offloading"] is False

    def test_audit_vehicle_weight_tolerance(self, engine: TransportEngine) -> None:
        res = engine.audit_vehicle_weight(
            plate_number="29C-111.22",
            vehicle_configuration="RIGID_2AXLE",
            gross_weight_tonnes=16.8,  # 0.8t overload = 5% (< 10% tolerance)
        )
        aud = res["weight_audit"]
        assert aud["is_overloaded"] is False
        assert aud["is_tolerance_zone"] is True
        assert aud["fine_driver_vnd"] == 0.0

    def test_audit_vehicle_weight_bracket_10_20(self, engine: TransportEngine) -> None:
        res = engine.audit_vehicle_weight(
            plate_number="50H-888.99",
            vehicle_configuration="ARTICULATED_5AXLE",
            gross_weight_tonnes=50.0,  # 50 - 44 = 6t overload = 13.64%
        )
        aud = res["weight_audit"]
        assert aud["is_overloaded"] is True
        assert aud["overload_percentage"] > 10.0
        assert aud["overload_percentage"] <= 20.0
        assert aud["fine_driver_vnd"] == 5000000.0
        assert aud["fine_owner_vnd"] == 6000000.0
        assert aud["license_suspension_months"] == 0
        assert aud["requires_offloading"] is True

    def test_audit_vehicle_weight_bracket_20_50(self, engine: TransportEngine) -> None:
        res = engine.audit_vehicle_weight(
            plate_number="50H-888.99",
            vehicle_configuration="ARTICULATED_5AXLE",
            gross_weight_tonnes=58.0,  # 58 - 44 = 14t overload = 31.82%
        )
        aud = res["weight_audit"]
        assert aud["is_overloaded"] is True
        assert 20.0 < aud["overload_percentage"] <= 50.0
        assert aud["fine_driver_vnd"] == 14000000.0
        assert aud["fine_owner_vnd"] == 15000000.0
        assert aud["license_suspension_months"] == 2
        assert aud["requires_offloading"] is True

    def test_audit_vehicle_weight_bracket_over_50(self, engine: TransportEngine) -> None:
        res = engine.audit_vehicle_weight(
            plate_number="50H-888.99",
            vehicle_configuration="ARTICULATED_5AXLE",
            gross_weight_tonnes=70.0,  # 70 - 44 = 26t overload = 59.09%
        )
        aud = res["weight_audit"]
        assert aud["is_overloaded"] is True
        assert aud["overload_percentage"] > 50.0
        assert aud["fine_driver_vnd"] == 45000000.0
        assert aud["fine_owner_vnd"] == 30000000.0
        assert aud["license_suspension_months"] == 4
        assert aud["requires_offloading"] is True

    def test_listing_methods_and_status_telemetry(self, engine: TransportEngine) -> None:
        engine.issue_business_license("DN A", "111", "CARGO_TRUCK")
        engine.issue_vehicle_badge("29C-111", "GPKD-1", "CARGO_TRUCK", 2022, 15.0)
        engine.process_etc_toll("29C-111", "E-01", "Trạm BOT", "CLASS_1")
        engine.audit_journey_monitoring("29C-111", "Tài xế A", "GPLX-01", 3.0, 7.0)
        engine.audit_vehicle_weight("29C-111", "RIGID_2AXLE", 18.0)

        assert len(engine.list_licenses()) >= 1
        assert len(engine.list_badges()) >= 1
        assert len(engine.list_etc_transactions()) >= 1
        assert len(engine.list_weight_audits()) >= 1

        status = engine.get_status()
        assert status["status"] == "online"
        m = status["metrics"]
        assert m["active_transport_licenses"] >= 1
        assert m["granted_vehicle_badges"] >= 1
        assert m["etc_toll_transactions"] >= 1
        assert m["compliant_journey_logs"] >= 1
        assert m["overload_violations_detected"] >= 1


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestTransportCLI:
    """Test CLI command suite for mekong transport."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_help(self, app) -> None:
        result = runner.invoke(app, ["transport", "--help"])
        assert result.exit_code == 0
        assert "Transport" in result.output
        assert "license" in result.output
        assert "badge" in result.output
        assert "etc" in result.output
        assert "gps" in result.output
        assert "weight" in result.output

    def test_cli_main_status(self, app) -> None:
        result = runner.invoke(app, ["transport"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ VẬN TẢI ĐƯỜNG BỘ" in result.output

    def test_cli_main_status_json(self, app) -> None:
        result = runner.invoke(app, ["transport", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "online"
        assert "metrics" in data

    def test_cli_license_command(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "transport",
                "license",
                "Công ty Vận tải Thành Bưởi",
                "0303777666",
                "--type",
                "PASSENGER_COACH_FIXED",
                "--fleet",
                "150",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["license_profile"]["enterprise_name"] == "Công ty Vận tải Thành Bưởi"

    def test_cli_badge_command(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "transport",
                "badge",
                "51B-555.66",
                "GPKD-PAS-001",
                "--type",
                "PASSENGER_COACH_FIXED",
                "--year",
                "2023",
                "--capacity",
                "45",
                "--gps",
                "--camera",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["badge_profile"]["is_badge_granted"] is True

    def test_cli_etc_command(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "transport",
                "etc",
                "30F-999.88",
                "E-TAG-VETC-889900",
                "--station",
                "Trạm BOT Pháp Vân - Cầu Giẽ",
                "--class",
                "CLASS_1",
                "--balance",
                "300000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["transaction_profile"]["transaction_status"] == "SUCCESS"

    def test_cli_gps_command(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "transport",
                "gps",
                "51B-555.66",
                "Lê Hoàng Anh",
                "GPLX-E-889900",
                "--continuous",
                "3.2",
                "--daily",
                "7.5",
                "--rest",
                "25",
                "--camera",
                "--gps",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["journey_audit"]["is_compliant"] is True

    def test_cli_weight_command(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "transport",
                "weight",
                "50H-123.45",
                "--config",
                "ARTICULATED_5AXLE",
                "--weight",
                "47.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["weight_audit"]["permitted_weight_tonnes"] == 44.0

    def test_cli_list_commands(self, app) -> None:
        for res_type in ["licenses", "badges", "etc", "weights"]:
            result = runner.invoke(app, ["transport", "list", res_type, "--json"])
            assert result.exit_code == 0
            assert isinstance(json.loads(result.output), list)

    def test_cli_status_subcommand(self, app) -> None:
        result = runner.invoke(app, ["transport", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Server Integration Tests
# ---------------------------------------------------------------------------


class TestTransportMCP:
    """Test MCP tool registration and handlers for road transport suite."""

    def test_src_core_mcp_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # License
        res_lic = server._handle_transport_license(
            enterprise_name="Tập đoàn Mai Linh",
            tax_id="0301234567",
            business_type="PASSENGER_TAXI",
        )
        data_lic = json.loads(res_lic)
        assert data_lic["status"] == "success"

        # Badge
        res_bdg = server._handle_transport_badge(
            plate_number="30A-999.11",
            license_number="GPKD-TAX-001",
            vehicle_type="PASSENGER_TAXI",
            year_built=2024,
            seats_or_tonnage=5.0,
        )
        data_bdg = json.loads(res_bdg)
        assert data_bdg["badge_profile"]["is_badge_granted"] is True

        # ETC
        res_etc = server._handle_transport_etc(
            plate_number="30A-999.11",
            etag_id="E-TAG-VETC-11",
            bot_station_name="Trạm BOT Hà Nội - Hải Phòng",
            vehicle_class="CLASS_1",
        )
        data_etc = json.loads(res_etc)
        assert data_etc["transaction_profile"]["transaction_status"] == "SUCCESS"

        # GPS
        res_gps = server._handle_transport_gps(
            plate_number="30A-999.11",
            driver_name="Phạm Văn Đồng",
            driver_license_num="GPLX-B2-111",
            continuous_driving_hours=2.5,
            daily_driving_hours=6.0,
        )
        data_gps = json.loads(res_gps)
        assert data_gps["journey_audit"]["is_compliant"] is True

        # Weight
        res_wgt = server._handle_transport_weight(
            plate_number="30A-999.11",
            vehicle_configuration="RIGID_2AXLE",
            gross_weight_tonnes=14.0,
        )
        data_wgt = json.loads(res_wgt)
        assert data_wgt["weight_audit"]["is_overloaded"] is False

        # List
        res_lst = server._handle_transport_list(resource="licenses", limit=10)
        assert isinstance(json.loads(res_lst), list)

        # Status
        res_st = server._handle_transport_status()
        data_st = json.loads(res_st)
        assert data_st["status"] == "online"

    def test_scripts_mcp_server_handlers_and_spec_parity(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_transport_badge,
            handle_transport_etc,
            handle_transport_gps,
            handle_transport_license,
            handle_transport_list,
            handle_transport_status,
            handle_transport_weight,
        )

        expected_tools = [
            "mekong_transport_license",
            "mekong_transport_badge",
            "mekong_transport_etc",
            "mekong_transport_gps",
            "mekong_transport_weight",
            "mekong_transport_list",
            "mekong_transport_status",
        ]

        # Verify handlers exist in CORE_HANDLERS
        for tool in expected_tools:
            assert tool in CORE_HANDLERS, f"{tool} must be in CORE_HANDLERS"

        # Verify tool schemas exist in CORE_TOOLS_SPEC
        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        for tool in expected_tools:
            assert tool in tool_names, f"{tool} schema must be in CORE_TOOLS_SPEC"

        # Test execution of handlers
        res_lic = handle_transport_license({
            "enterprise_name": "Công ty Vận tải Hải Vân",
            "tax_id": "0109998888",
            "business_type": "PASSENGER_COACH_FIXED",
        })
        assert json.loads(res_lic)["status"] == "success"

        res_bdg = handle_transport_badge({
            "plate_number": "51B-123.45",
            "license_number": "GPKD-123",
            "vehicle_type": "PASSENGER_COACH_FIXED",
            "year_built": 2023,
            "seats_or_tonnage": 45.0,
        })
        assert json.loads(res_bdg)["status"] == "success"

        res_etc = handle_transport_etc({
            "plate_number": "51B-123.45",
            "etag_id": "ETAG-001",
            "bot_station_name": "Trạm BOT",
            "vehicle_class": "CLASS_1",
        })
        assert json.loads(res_etc)["status"] == "success"

        res_gps = handle_transport_gps({
            "plate_number": "51B-123.45",
            "driver_name": "Tài xế A",
            "driver_license_num": "GPLX-01",
        })
        assert json.loads(res_gps)["status"] == "success"

        res_wgt = handle_transport_weight({
            "plate_number": "51B-123.45",
            "vehicle_configuration": "RIGID_2AXLE",
            "gross_weight_tonnes": 14.0,
        })
        assert json.loads(res_wgt)["status"] == "success"

        res_lst = handle_transport_list({"resource": "licenses"})
        assert isinstance(json.loads(res_lst), list)

        res_st = handle_transport_status({})
        assert json.loads(res_st)["status"] == "online"
