"""
Unit and integration tests for Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite.
Governed by:
- Law on Road Traffic Safety and Order 2024 (Law No. 36/2024/QH15 — Luật Trật tự, an toàn giao thông đường bộ 2024)
- Road Law 2024 (Law No. 35/2024/QH15 — Luật Đường bộ 2024)
- Decree No. 100/2019/NĐ-CP & Decree No. 123/2021/NĐ-CP (Administrative Penalties in Road Traffic)
- Circular No. 32/2023/TT-BCA (Traffic Police Patrol, Control & Enforcement Procedures)
- Circular No. 24/2023/TT-BCA (Vehicle Registration & Identification Plate Regulations)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.traffic_command import app as traffic_app
from src.core.traffic_engine import (
    VALID_ACTIONS_TAKEN,
    VALID_CAMERA_STATUS,
    VALID_CAMERA_VIOLATIONS,
    VALID_DRUG_RESULTS,
    VALID_EMISSIONS_STANDARDS,
    VALID_INSPECTION_RESULTS,
    VALID_LICENSE_CLASSES,
    VALID_LICENSE_STATUS,
    VALID_STOP_REASONS,
    VALID_VEHICLE_TYPES,
    TrafficEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_TRAFFIC_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestTrafficEngine:
    def test_register_license_valid(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        res = engine.register_license(
            license_number="GPLX-790123456789",
            driver_name="Nguyễn Văn An",
            citizen_id="001099012345",
            license_class="B",
            total_points=12,
            points_remaining=12,
            issue_date="2025-01-01",
            expiry_date="2035-01-01",
            status="ACTIVE_VALID",
        )
        assert res["license_number"] == "GPLX-790123456789"
        assert res["driver_name"] == "Nguyễn Văn An"
        assert res["total_points"] == 12
        assert res["points_remaining"] == 12
        assert res["status"] == "ACTIVE_VALID"

    def test_register_license_missing_fields(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.register_license(
                license_number="",
                driver_name="Nguyễn Văn An",
                citizen_id="001099012345",
                license_class="B",
            )

    def test_register_license_invalid_class(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid license_class"):
            engine.register_license(
                license_number="GPLX-001",
                driver_name="Nguyễn Văn An",
                citizen_id="001099012345",
                license_class="INVALID_CLASS",
            )

    def test_register_license_invalid_status(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_license(
                license_number="GPLX-001",
                driver_name="Nguyễn Văn An",
                citizen_id="001099012345",
                license_class="B",
                status="UNKNOWN_STATUS",
            )

    def test_register_license_invalid_points(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="total_points must be positive"):
            engine.register_license(
                license_number="GPLX-001",
                driver_name="Nguyễn Văn An",
                citizen_id="001099012345",
                license_class="B",
                total_points=0,
            )
        with pytest.raises(ValueError, match="points_remaining must be between 0 and 12"):
            engine.register_license(
                license_number="GPLX-002",
                driver_name="Nguyễn Văn An",
                citizen_id="001099012345",
                license_class="B",
                total_points=12,
                points_remaining=15,
            )

    def test_register_license_duplicate(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.register_license(
            license_number="GPLX-DUP-01",
            driver_name="Trần Thị Bình",
            citizen_id="001099099999",
            license_class="A1",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_license(
                license_number="GPLX-DUP-01",
                driver_name="Trần Thị Bình",
                citizen_id="001099099999",
                license_class="A1",
            )

    def test_issue_ticket_valid_and_points_deduction(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.register_license(
            license_number="GPLX-TKT-01",
            driver_name="Phạm Quốc Cường",
            citizen_id="079088001122",
            license_class="B",
            total_points=12,
            points_remaining=12,
        )

        res = engine.issue_ticket(
            ticket_id="TKT-2026-001",
            license_number="GPLX-TKT-01",
            vehicle_plate="51K-999.88",
            violation_code="D100-ART5-SPEED",
            violation_description="Chạy quá tốc độ quy định từ 10 km/h đến 20 km/h",
            location="Km 28+500 Cao tốc TP.HCM - Long Thành - Dầu Giây",
            officer_badge="BCA-CSGT-8842",
            fine_amount_vnd=5000000.0,
            points_deducted=4,
            paid=False,
        )
        assert res["ticket_id"] == "TKT-2026-001"
        assert res["points_deducted"] == 4
        assert res["license_points_remaining"] == 8
        assert res["fine_amount_vnd"] == 5000000.0

        # Check in DB that points were reduced
        records = engine.list_records("licenses")
        lic = next(l for l in records["licenses"] if l["license_number"] == "GPLX-TKT-01")
        assert lic["points_remaining"] == 8
        assert lic["status"] == "ACTIVE_VALID"

    def test_issue_ticket_exhaust_points_suspension(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.register_license(
            license_number="GPLX-TKT-EXHAUST",
            driver_name="Lê Minh Đạt",
            citizen_id="079088003344",
            license_class="C",
            total_points=12,
            points_remaining=4,
        )

        res = engine.issue_ticket(
            ticket_id="TKT-2026-002",
            license_number="GPLX-TKT-EXHAUST",
            vehicle_plate="60C-123.45",
            violation_code="D100-ART5-ALCOHOL-HIGH",
            violation_description="Điều khiển phương tiện có nồng độ cồn vượt quá 0.4 mg/l",
            location="Ngã tư Hàng Xanh, Bình Thạnh, TP.HCM",
            officer_badge="BCA-CSGT-1122",
            fine_amount_vnd=35000000.0,
            points_deducted=10,
        )
        assert res["points_deducted"] == 10
        assert res["license_points_remaining"] == 0

        # Status must now be POINTS_EXHAUSTED_SUSPENDED
        records = engine.list_records("licenses")
        lic = next(l for l in records["licenses"] if l["license_number"] == "GPLX-TKT-EXHAUST")
        assert lic["points_remaining"] == 0
        assert lic["status"] == "POINTS_EXHAUSTED_SUSPENDED"

    def test_issue_ticket_missing_fields(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.issue_ticket(
                ticket_id="",
                license_number="GPLX-001",
                vehicle_plate="51K-123.45",
                violation_code="V01",
                violation_description="Test",
                location="Loc",
                officer_badge="BADGE",
            )

    def test_issue_ticket_invalid_points_or_fine(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.issue_ticket(
                ticket_id="TKT-NEG",
                license_number="GPLX-001",
                vehicle_plate="51K-123.45",
                violation_code="V01",
                violation_description="Test",
                location="Loc",
                officer_badge="BADGE",
                fine_amount_vnd=-1000.0,
            )
        with pytest.raises(ValueError, match="must be between 0 and 12"):
            engine.issue_ticket(
                ticket_id="TKT-OVER",
                license_number="GPLX-001",
                vehicle_plate="51K-123.45",
                violation_code="V01",
                violation_description="Test",
                location="Loc",
                officer_badge="BADGE",
                points_deducted=15,
            )

    def test_issue_ticket_duplicate(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.issue_ticket(
            ticket_id="TKT-DUP",
            license_number="GPLX-001",
            vehicle_plate="51K-123.45",
            violation_code="V01",
            violation_description="Test",
            location="Loc",
            officer_badge="BADGE",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_ticket(
                ticket_id="TKT-DUP",
                license_number="GPLX-001",
                vehicle_plate="51K-123.45",
                violation_code="V01",
                violation_description="Test",
                location="Loc",
                officer_badge="BADGE",
            )

    def test_record_camera_notice_valid(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        res = engine.record_camera_notice(
            notice_id="CAM-2026-001",
            vehicle_plate="30H-888.99",
            violation_type="RUNNING_RED_LIGHT",
            camera_location="Nút giao Phạm Văn Đồng - Hoàng Quốc Việt, Hà Nội",
            measured_value="Vượt đèn đỏ sau 3.2 giây chuyển pha đỏ",
            notice_date="2026-02-15",
            due_date="2026-03-07",
            status="NOTICE_ISSUED",
        )
        assert res["notice_id"] == "CAM-2026-001"
        assert res["vehicle_plate"] == "30H-888.99"
        assert res["violation_type"] == "RUNNING_RED_LIGHT"
        assert res["status"] == "NOTICE_ISSUED"

    def test_record_camera_notice_invalid_violation_type(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid violation_type"):
            engine.record_camera_notice(
                notice_id="CAM-INV",
                vehicle_plate="30H-123.45",
                violation_type="UNKNOWN_VIOLATION",
                camera_location="Loc",
                measured_value="Val",
            )

    def test_record_camera_notice_invalid_status(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid status"):
            engine.record_camera_notice(
                notice_id="CAM-INV2",
                vehicle_plate="30H-123.45",
                violation_type="SPEEDING_OVER_LIMIT",
                camera_location="Loc",
                measured_value="Val",
                status="INVALID_STATUS",
            )

    def test_record_camera_notice_missing_fields(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.record_camera_notice(
                notice_id="",
                vehicle_plate="30H-123.45",
                violation_type="SPEEDING_OVER_LIMIT",
                camera_location="Loc",
                measured_value="Val",
            )

    def test_record_camera_notice_duplicate(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.record_camera_notice(
            notice_id="CAM-DUP",
            vehicle_plate="30H-123.45",
            violation_type="WRONG_LANE_USAGE",
            camera_location="Loc",
            measured_value="Val",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.record_camera_notice(
                notice_id="CAM-DUP",
                vehicle_plate="30H-123.45",
                violation_type="WRONG_LANE_USAGE",
                camera_location="Loc",
                measured_value="Val",
            )

    def test_record_inspection_valid(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        res = engine.record_inspection(
            inspection_id="INS-2026-001",
            vehicle_plate="50E-123.45",
            vin_number="RLHVF8EC9PK123456",
            center_code="50-01S",
            vehicle_type="ELECTRIC_VEHICLE",
            brake_efficiency_percent=78.5,
            emissions_standard="ZERO_EMISSION_EV",
            result="PASSED",
            valid_until="2027-02-15",
        )
        assert res["inspection_id"] == "INS-2026-001"
        assert res["vehicle_plate"] == "50E-123.45"
        assert res["emissions_standard"] == "ZERO_EMISSION_EV"
        assert res["brake_efficiency_percent"] == 78.5
        assert res["result"] == "PASSED"

    def test_record_inspection_invalid_vehicle_type(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid vehicle_type"):
            engine.record_inspection(
                inspection_id="INS-INV",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                center_code="50-01S",
                vehicle_type="SUBMARINE",
            )

    def test_record_inspection_invalid_emissions(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid emissions_standard"):
            engine.record_inspection(
                inspection_id="INS-INV2",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                vehicle_type="PASSENGER_CAR",
                center_code="50-01S",
                emissions_standard="EURO_99",
            )

    def test_record_inspection_invalid_result(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid result"):
            engine.record_inspection(
                inspection_id="INS-INV3",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                vehicle_type="PASSENGER_CAR",
                center_code="50-01S",
                result="MAYBE_PASSED",
            )

    def test_record_inspection_invalid_brake_efficiency(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            engine.record_inspection(
                inspection_id="INS-INV4",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                vehicle_type="PASSENGER_CAR",
                center_code="50-01S",
                brake_efficiency_percent=120.0,
            )

    def test_record_inspection_missing_fields(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.record_inspection(
                inspection_id="",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                vehicle_type="PASSENGER_CAR",
                center_code="50-01S",
            )

    def test_record_inspection_duplicate(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.record_inspection(
            inspection_id="INS-DUP",
            vehicle_plate="50E-123.45",
            vin_number="VIN123",
            vehicle_type="PASSENGER_CAR",
            center_code="50-01S",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.record_inspection(
                inspection_id="INS-DUP",
                vehicle_plate="50E-123.45",
                vin_number="VIN123",
                vehicle_type="PASSENGER_CAR",
                center_code="50-01S",
            )

    def test_log_road_stop_valid(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        res = engine.log_road_stop(
            stop_id="STP-2026-001",
            vehicle_plate="51F-111.22",
            stop_reason="ROUTINE_ALCOHOL_CHECK",
            officer_unit="Đội CSGT Bến Thành - PC08 TP.HCM",
            breath_alcohol_mg_l=0.0,
            drug_screening_result="NEGATIVE",
            action_taken="CLEARED_NO_VIOLATION",
        )
        assert res["stop_id"] == "STP-2026-001"
        assert res["breath_alcohol_mg_l"] == 0.0
        assert res["drug_screening_result"] == "NEGATIVE"
        assert res["action_taken"] == "CLEARED_NO_VIOLATION"

    def test_log_road_stop_with_alcohol_violation(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        res = engine.log_road_stop(
            stop_id="STP-2026-002",
            vehicle_plate="51G-888.88",
            stop_reason="ROUTINE_ALCOHOL_CHECK",
            officer_unit="Đội CSGT Tân Sơn Nhất - PC08 TP.HCM",
            breath_alcohol_mg_l=0.45,
            drug_screening_result="NEGATIVE",
            action_taken="VEHICLE_IMPOUNDED",
        )
        assert res["stop_id"] == "STP-2026-002"
        assert res["breath_alcohol_mg_l"] == 0.45
        assert res["action_taken"] == "VEHICLE_IMPOUNDED"

    def test_log_road_stop_invalid_reason(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid stop_reason"):
            engine.log_road_stop(
                stop_id="STP-INV",
                vehicle_plate="51G-123.45",
                stop_reason="CURIOUS_STOP",
                officer_unit="Unit",
            )

    def test_log_road_stop_invalid_drug_result(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid drug_screening_result"):
            engine.log_road_stop(
                stop_id="STP-INV2",
                vehicle_plate="51G-123.45",
                stop_reason="ROUTINE_ALCOHOL_CHECK",
                officer_unit="Unit",
                drug_screening_result="UNKNOWN_DRUG",
            )

    def test_log_road_stop_invalid_action(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid action_taken"):
            engine.log_road_stop(
                stop_id="STP-INV3",
                vehicle_plate="51G-123.45",
                stop_reason="ROUTINE_ALCOHOL_CHECK",
                officer_unit="Unit",
                action_taken="ARREST_EVERYONE",
            )

    def test_log_road_stop_negative_alcohol(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.log_road_stop(
                stop_id="STP-INV4",
                vehicle_plate="51G-123.45",
                stop_reason="ROUTINE_ALCOHOL_CHECK",
                officer_unit="Unit",
                breath_alcohol_mg_l=-0.5,
            )

    def test_log_road_stop_duplicate(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.log_road_stop(
            stop_id="STP-DUP",
            vehicle_plate="51G-123.45",
            stop_reason="ROUTINE_ALCOHOL_CHECK",
            officer_unit="Unit",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_road_stop(
                stop_id="STP-DUP",
                vehicle_plate="51G-123.45",
                stop_reason="ROUTINE_ALCOHOL_CHECK",
                officer_unit="Unit",
            )

    def test_list_records_all_and_categories(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.register_license("GPLX-01", "Driver A", "001", "B")
        engine.issue_ticket("TKT-01", "GPLX-01", "51A-123", "V01", "Speed", "Loc", "B1", 1000000, 2)
        engine.record_camera_notice("CAM-01", "51A-123", "SPEEDING_OVER_LIMIT", "CamLoc", "95 km/h")
        engine.record_inspection("INS-01", "51A-123", "VIN01", "PASSENGER_CAR", "50-01S")
        engine.log_road_stop("STP-01", "51A-123", "ROUTINE_ALCOHOL_CHECK", "Unit A")

        all_records = engine.list_records("all")
        assert len(all_records["licenses"]) == 1
        assert len(all_records["tickets"]) == 1
        assert len(all_records["camera"]) == 1
        assert len(all_records["inspections"]) == 1
        assert len(all_records["stops"]) == 1

        lic_only = engine.list_records("licenses")
        assert "licenses" in lic_only
        assert "tickets" not in lic_only

    def test_get_telemetry_status(self, temp_db: str) -> None:
        engine = TrafficEngine(db_path=temp_db)
        engine.register_license("GPLX-01", "Driver A", "001", "B", total_points=12, points_remaining=12)
        engine.register_license("GPLX-02", "Driver B", "002", "B", total_points=12, points_remaining=2)
        # Deduct all 2 points from Driver B to trigger suspension
        engine.issue_ticket("TKT-01", "GPLX-02", "51A-111", "V01", "Speed", "Loc", "B1", 5000000, 2)
        engine.record_camera_notice("CAM-01", "51A-111", "SPEEDING_OVER_LIMIT", "CamLoc", "100 km/h")
        engine.record_inspection("INS-01", "51A-111", "VIN01", "PASSENGER_CAR", "50-01S", result="PASSED")
        engine.log_road_stop("STP-01", "51A-111", "ROUTINE_ALCOHOL_CHECK", "Unit A", breath_alcohol_mg_l=0.25)
        engine.log_road_stop("STP-02", "51A-222", "ROUTINE_ALCOHOL_CHECK", "Unit B", breath_alcohol_mg_l=0.0)

        telem = engine.get_telemetry_status()
        assert telem["active_valid_licenses"] == 1
        assert telem["suspended_licenses_zero_points"] == 1
        assert telem["total_tickets_issued"] == 1
        assert telem["total_fines_vnd"] == 5000000.0
        assert telem["total_points_deducted"] == 2
        assert telem["pending_camera_notices"] == 1
        assert telem["passed_vehicle_inspections"] == 1
        assert telem["total_road_stops"] == 2
        assert telem["alcohol_violations_detected"] == 1


class TestTrafficCLI:
    @pytest.fixture(autouse=True)
    def setup_runner(self) -> None:
        self.runner = CliRunner()

    def test_cli_dashboard_default(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, [])
        assert result.exit_code == 0
        assert "CỤC CẢNH SÁT GIAO THÔNG" in result.stdout

    def test_cli_dashboard_json(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "active_valid_licenses" in data
        assert "total_tickets_issued" in data

    def test_cli_status(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, ["status"])
        assert result.exit_code == 0
        assert "Chỉ số Vận hành Hệ thống" in result.stdout

    def test_cli_status_json(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "active_valid_licenses" in data

    def test_cli_license_register(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "license",
                "--number", "GPLX-CLI-01",
                "--name", "Hoàng Văn Nam",
                "--citizen-id", "034099123456",
                "--class", "B",
                "--points", "12",
            ],
        )
        assert result.exit_code == 0
        assert "Giấy phép Lái xe" in result.stdout

    def test_cli_license_register_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "license",
                "--number", "GPLX-CLI-JSON",
                "--name", "Đỗ Văn Hùng",
                "--citizen-id", "034099888999",
                "--class", "C",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["license_number"] == "GPLX-CLI-JSON"
        assert data["license_class"] == "C"

    def test_cli_license_register_invalid(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "license",
                "--number", "GPLX-CLI-ERR",
                "--name", "Test",
                "--citizen-id", "001",
                "--class", "INVALID_CLASS",
            ],
        )
        assert result.exit_code != 0

    def test_cli_ticket_issue(self, temp_db: str) -> None:
        # First register license
        self.runner.invoke(
            traffic_app,
            ["license", "--number", "GPLX-TKT-CLI", "--name", "Test Driver", "--citizen-id", "001"],
        )
        result = self.runner.invoke(
            traffic_app,
            [
                "ticket",
                "--id", "TKT-CLI-01",
                "--license", "GPLX-TKT-CLI",
                "--plate", "51K-555.66",
                "--code", "D100-RED-LIGHT",
                "--desc", "Không chấp hành hiệu lệnh của đèn tín hiệu giao thông",
                "--location", "Ngã 4 Nguyễn Huệ - Lê Lợi, Q1, TP.HCM",
                "--officer", "CSGT-Q1-092",
                "--fine", "5000000",
                "--points", "3",
            ],
        )
        assert result.exit_code == 0
        assert "Lập Biên bản Xử phạt" in result.stdout

    def test_cli_ticket_issue_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "ticket",
                "--id", "TKT-CLI-JSON",
                "--license", "GPLX-TKT-CLI",
                "--plate", "51K-555.66",
                "--code", "D100-LANE",
                "--desc", "Đi sai làn đường",
                "--location", "Đường Mai Chí Thọ, TP. Thủ Đức",
                "--officer", "CSGT-TD-101",
                "--fine", "4000000",
                "--points", "2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["ticket_id"] == "TKT-CLI-JSON"
        assert data["points_deducted"] == 2

    def test_cli_camera_record(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "camera",
                "--id", "CAM-CLI-01",
                "--plate", "29A-999.99",
                "--type", "SPEEDING_OVER_LIMIT",
                "--location", "Km 10+200 Đường Võ Nguyên Giáp, Hà Nội",
                "--value", "98 km/h trên đoạn tối đa 80 km/h",
            ],
        )
        assert result.exit_code == 0
        assert "Thông báo Vi phạm Phạt nguội" in result.stdout

    def test_cli_camera_record_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "camera",
                "--id", "CAM-CLI-JSON",
                "--plate", "29A-999.99",
                "--type", "RUNNING_RED_LIGHT",
                "--location", "Nút giao Cầu Giấy, Hà Nội",
                "--value", "RED_PHASE_04S",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["notice_id"] == "CAM-CLI-JSON"

    def test_cli_inspection_record(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "inspection",
                "--id", "INS-CLI-01",
                "--plate", "51K-123.45",
                "--vin", "VFE34-VN-2025-001",
                "--center", "50-02S",
                "--type", "ELECTRIC_VEHICLE",
                "--brake", "82.0",
                "--emissions", "ZERO_EMISSION_EV",
                "--result", "PASSED",
            ],
        )
        assert result.exit_code == 0
        assert "Kiểm định An toàn Kỹ thuật" in result.stdout

    def test_cli_inspection_record_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "inspection",
                "--id", "INS-CLI-JSON",
                "--plate", "51K-123.45",
                "--vin", "VFE34-VN-2025-001",
                "--center", "50-02S",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["inspection_id"] == "INS-CLI-JSON"

    def test_cli_stop_log(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "stop",
                "--id", "STP-CLI-01",
                "--plate", "51A-777.88",
                "--reason", "ROUTINE_ALCOHOL_CHECK",
                "--alcohol", "0.0",
                "--drug", "NEGATIVE",
                "--unit", "Đội CSGT An Sương",
                "--action", "CLEARED_NO_VIOLATION",
            ],
        )
        assert result.exit_code == 0
        assert "Dừng xe & Kiểm tra" in result.stdout

    def test_cli_stop_log_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            traffic_app,
            [
                "stop",
                "--id", "STP-CLI-JSON",
                "--plate", "51A-777.88",
                "--reason", "ROUTINE_ALCOHOL_CHECK",
                "--alcohol", "0.0",
                "--drug", "NEGATIVE",
                "--unit", "Đội CSGT An Sương",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["stop_id"] == "STP-CLI-JSON"

    def test_cli_list_records(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, ["list", "--type", "all", "--limit", "10"])
        assert result.exit_code == 0

    def test_cli_list_records_json(self, temp_db: str) -> None:
        result = self.runner.invoke(traffic_app, ["list", "--type", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)


class TestTrafficMCPServer:
    def test_core_mcp_traffic_license(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_license(
            license_number="GPLX-MCP-01",
            driver_name="Phan Văn Đạt",
            citizen_id="001099112233",
            license_class="B",
        )
        res = json.loads(raw)
        assert res["license_number"] == "GPLX-MCP-01"
        assert res["points_remaining"] == 12

    def test_core_mcp_traffic_ticket(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        server._handle_traffic_license(
            license_number="GPLX-MCP-02",
            driver_name="Phan Văn Đạt",
            citizen_id="001099112233",
            license_class="B",
        )
        raw = server._handle_traffic_ticket(
            ticket_id="TKT-MCP-01",
            license_number="GPLX-MCP-02",
            vehicle_plate="51K-111.22",
            violation_code="V-OVER",
            violation_description="Chạy quá tốc độ",
            location="Km 50 QL1A",
            officer_badge="CSGT-991",
            fine_amount_vnd=3000000,
            points_deducted=2,
        )
        res = json.loads(raw)
        assert res["ticket_id"] == "TKT-MCP-01"
        assert res["license_points_remaining"] == 10

    def test_core_mcp_traffic_camera(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_camera(
            notice_id="CAM-MCP-01",
            vehicle_plate="30G-123.45",
            violation_type="SPEEDING_OVER_LIMIT",
            camera_location="Võ Văn Kiệt",
            measured_value="75 km/h",
        )
        res = json.loads(raw)
        assert res["notice_id"] == "CAM-MCP-01"

    def test_core_mcp_traffic_inspection(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_inspection(
            inspection_id="INS-MCP-01",
            vehicle_plate="30G-123.45",
            vin_number="VIN999",
            center_code="29-01V",
        )
        res = json.loads(raw)
        assert res["inspection_id"] == "INS-MCP-01"

    def test_core_mcp_traffic_stop(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_stop(
            stop_id="STP-MCP-01",
            vehicle_plate="30G-123.45",
            officer_unit="Đội CSGT Số 1 - CATP Hà Nội",
        )
        res = json.loads(raw)
        assert res["stop_id"] == "STP-MCP-01"

    def test_core_mcp_traffic_list(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_list(category="all", limit=10)
        res = json.loads(raw)
        assert "licenses" in res

    def test_core_mcp_traffic_status(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_status()
        res = json.loads(raw)
        assert "active_valid_licenses" in res

    def test_core_mcp_aliases(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert server._handle_mekong_traffic_license == server._handle_traffic_license
        assert server._handle_mekong_traffic_ticket == server._handle_traffic_ticket
        assert server._handle_mekong_traffic_camera == server._handle_traffic_camera
        assert server._handle_mekong_traffic_inspection == server._handle_traffic_inspection
        assert server._handle_mekong_traffic_stop == server._handle_traffic_stop
        assert server._handle_mekong_traffic_list == server._handle_traffic_list
        assert server._handle_mekong_traffic_status == server._handle_traffic_status

    def test_core_mcp_error_handling(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_traffic_license(
            license_number="",
            driver_name="Test",
            citizen_id="001",
        )
        res = json.loads(raw)
        assert res["ok"] is False
        assert "error" in res


class TestTrafficScriptsMCPServer:
    def test_scripts_mcp_handlers_present(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected = [
            "mekong_traffic_license",
            "mekong_traffic_ticket",
            "mekong_traffic_camera",
            "mekong_traffic_inspection",
            "mekong_traffic_stop",
            "mekong_traffic_list",
            "mekong_traffic_status",
            "traffic_license",
            "traffic_ticket",
            "traffic_camera",
            "traffic_inspection",
            "traffic_stop",
            "traffic_list",
            "traffic_status",
        ]
        for name in expected:
            assert name in CORE_HANDLERS, f"Missing handler {name} in CORE_HANDLERS"

    def test_scripts_mcp_core_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        expected = [
            "mekong_traffic_license",
            "mekong_traffic_ticket",
            "mekong_traffic_camera",
            "mekong_traffic_inspection",
            "mekong_traffic_stop",
            "mekong_traffic_list",
            "mekong_traffic_status",
        ]
        for name in expected:
            assert name in names, f"Missing {name} in CORE_TOOLS_SPEC"

    def test_scripts_mcp_handle_license(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_license

        raw = handle_traffic_license({
            "license_number": "GPLX-SCRIPTS-01",
            "driver_name": "Lê Văn Tám",
            "citizen_id": "001099555666",
            "license_class": "B",
        })
        res = json.loads(raw)
        assert res["license_number"] == "GPLX-SCRIPTS-01"

    def test_scripts_mcp_handle_ticket(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_license, handle_traffic_ticket

        handle_traffic_license({
            "license_number": "GPLX-SCRIPTS-02",
            "driver_name": "Lê Văn Tám",
            "citizen_id": "001099555666",
            "license_class": "B",
        })
        raw = handle_traffic_ticket({
            "ticket_id": "TKT-SCRIPTS-01",
            "license_number": "GPLX-SCRIPTS-02",
            "vehicle_plate": "51A-999.00",
            "violation_code": "V-SPD",
            "violation_description": "Speeding",
            "location": "Loc",
            "officer_badge": "B123",
            "fine_amount_vnd": 2000000,
            "points_deducted": 2,
        })
        res = json.loads(raw)
        assert res["ticket_id"] == "TKT-SCRIPTS-01"
        assert res["license_points_remaining"] == 10

    def test_scripts_mcp_handle_camera(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_camera

        raw = handle_traffic_camera({
            "notice_id": "CAM-SCRIPTS-01",
            "vehicle_plate": "51A-999.00",
            "violation_type": "WRONG_LANE_USAGE",
            "camera_location": "Loc",
            "measured_value": "Lane violation",
        })
        res = json.loads(raw)
        assert res["notice_id"] == "CAM-SCRIPTS-01"

    def test_scripts_mcp_handle_inspection(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_inspection

        raw = handle_traffic_inspection({
            "inspection_id": "INS-SCRIPTS-01",
            "vehicle_plate": "51A-999.00",
            "vin_number": "VIN-SCRIPTS",
            "center_code": "50-01S",
        })
        res = json.loads(raw)
        assert res["inspection_id"] == "INS-SCRIPTS-01"

    def test_scripts_mcp_handle_stop(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_stop

        raw = handle_traffic_stop({
            "stop_id": "STP-SCRIPTS-01",
            "vehicle_plate": "51A-999.00",
            "officer_unit": "Unit 1",
        })
        res = json.loads(raw)
        assert res["stop_id"] == "STP-SCRIPTS-01"

    def test_scripts_mcp_handle_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_list

        raw = handle_traffic_list({"category": "all", "limit": 10})
        res = json.loads(raw)
        assert "licenses" in res

    def test_scripts_mcp_handle_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_status

        raw = handle_traffic_status({})
        res = json.loads(raw)
        assert "active_valid_licenses" in res

    def test_scripts_mcp_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_traffic_license

        raw = handle_traffic_license({"license_number": ""})
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Traffic license error" in res["error"]
