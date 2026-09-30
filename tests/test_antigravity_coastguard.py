"""
Unit and integration tests for Vietnamese Coast Guard & Maritime Law Enforcement Suite.
Governed by:
- Law on Vietnam Coast Guard 2018 (Law No. 33/2018/QH14)
- Decree No. 61/2019/NĐ-CP (Guiding Implementation of Law on Vietnam Coast Guard)
- Circular No. 15/2019/TT-BQP (Coast Guard Enforcement & Operational Regulations)
- Decree No. 42/2019/NĐ-CP (Sanctions in Fisheries & Anti-IUU Enforcement)
- Decree No. 02/2021/NĐ-CP (Flags, Badges, Emblems & Uniforms of Vietnam Coast Guard)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.coastguard_command import app as coastguard_app
from src.core.coastguard_engine import (
    VALID_COASTGUARD_REGIONS,
    VALID_INSPECTION_REASONS,
    VALID_IUU_VIOLATIONS,
    VALID_PATROL_TYPES,
    VALID_SAR_TYPES,
    VALID_VESSEL_CLASSES,
    VALID_VESSEL_STATUS,
    CoastGuardEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_COASTGUARD_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCoastGuardEngine:
    def test_register_vessel_valid(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        res = engine.register_vessel(
            vessel_id="CSB-8002",
            hull_number="8002",
            vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
            assigned_region="REGION_2_CENTRAL",
            home_port="Cảng Kỳ Hà, Quảng Nam",
            displacement_tons=2500.0,
            commission_year=2015,
            status="ACTIVE_MISSION_READY",
        )
        assert res["vessel_id"] == "CSB-8002"
        assert res["hull_number"] == "8002"
        assert res["vessel_class"] == "OFFSHORE_PATROL_VESSEL_OPV"
        assert res["assigned_region"] == "REGION_2_CENTRAL"
        assert res["displacement_tons"] == 2500.0
        assert res["commission_year"] == 2015

    def test_register_vessel_duplicate(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.register_vessel(
            vessel_id="CSB-DUP",
            hull_number="9999",
            vessel_class="FAST_PATROL_BOAT_FPB",
            assigned_region="REGION_1_NORTH",
            home_port="Hải Phòng",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_vessel(
                vessel_id="CSB-DUP",
                hull_number="9999",
                vessel_class="FAST_PATROL_BOAT_FPB",
                assigned_region="REGION_1_NORTH",
                home_port="Hải Phòng",
            )

    def test_register_vessel_invalid_inputs(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_vessel(
                vessel_id="",
                hull_number="1234",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region="REGION_1_NORTH",
                home_port="",
            )

        with pytest.raises(ValueError, match="Invalid vessel_class"):
            engine.register_vessel(
                vessel_id="CSB-INV-CLASS",
                hull_number="1234",
                vessel_class="SUBMARINE_NUCLEAR",
                assigned_region="REGION_1_NORTH",
                home_port="Cảng",
            )

        with pytest.raises(ValueError, match="Invalid assigned_region"):
            engine.register_vessel(
                vessel_id="CSB-INV-REG",
                hull_number="1234",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region="REGION_PACIFIC",
                home_port="Cảng",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_vessel(
                vessel_id="CSB-INV-STAT",
                hull_number="1234",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region="REGION_1_NORTH",
                home_port="Cảng",
                status="SUNKEN_AT_SEA",
            )

        with pytest.raises(ValueError, match="displacement_tons must be positive"):
            engine.register_vessel(
                vessel_id="CSB-INV-TONS",
                hull_number="1234",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region="REGION_1_NORTH",
                home_port="Cảng",
                displacement_tons=-50.0,
            )

        with pytest.raises(ValueError, match="commission_year must be valid"):
            engine.register_vessel(
                vessel_id="CSB-INV-YEAR",
                hull_number="1234",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region="REGION_1_NORTH",
                home_port="Cảng",
                commission_year=1900,
            )

    def test_log_patrol_valid(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        res = engine.log_patrol(
            patrol_id="PATROL-2026-001",
            vessel_id="CSB-8002",
            patrol_type="SOVEREIGNTY_PROTECTION_SORTIE",
            sea_area_scope="Quần đảo Hoàng Sa & Thềm lục địa miền Trung",
            commanding_officer="Thượng tá Hoàng Văn Nam",
            days_at_sea=14,
            nautical_miles=1200.5,
            start_date="2026-03-01",
            end_date="2026-03-15",
            status="COMPLETED",
        )
        assert res["patrol_id"] == "PATROL-2026-001"
        assert res["vessel_id"] == "CSB-8002"
        assert res["patrol_type"] == "SOVEREIGNTY_PROTECTION_SORTIE"
        assert res["days_at_sea"] == 14
        assert res["nautical_miles"] == 1200.5

    def test_log_patrol_duplicate(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.log_patrol(
            patrol_id="PATROL-DUP",
            vessel_id="CSB-4031",
            patrol_type="ROUTINE_EEZ_PATROL",
            sea_area_scope="Vịnh Bắc Bộ",
            commanding_officer="Trung tá Lê Văn Hải",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_patrol(
                patrol_id="PATROL-DUP",
                vessel_id="CSB-4031",
                patrol_type="ROUTINE_EEZ_PATROL",
                sea_area_scope="Vịnh Bắc Bộ",
                commanding_officer="Trung tá Lê Văn Hải",
            )

    def test_log_patrol_invalid_inputs(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.log_patrol(
                patrol_id="",
                vessel_id="CSB-4031",
                patrol_type="ROUTINE_EEZ_PATROL",
                sea_area_scope="",
                commanding_officer="Chỉ huy",
            )

        with pytest.raises(ValueError, match="Invalid patrol_type"):
            engine.log_patrol(
                patrol_id="PATROL-INV",
                vessel_id="CSB-4031",
                patrol_type="PIRATE_RAID",
                sea_area_scope="Biển Đông",
                commanding_officer="Chỉ huy",
            )

        with pytest.raises(ValueError, match="days_at_sea must be positive"):
            engine.log_patrol(
                patrol_id="PATROL-INV-DAYS",
                vessel_id="CSB-4031",
                patrol_type="ROUTINE_EEZ_PATROL",
                sea_area_scope="Biển Đông",
                commanding_officer="Chỉ huy",
                days_at_sea=0,
            )

        with pytest.raises(ValueError, match="nautical_miles must be positive"):
            engine.log_patrol(
                patrol_id="PATROL-INV-MILES",
                vessel_id="CSB-4031",
                patrol_type="ROUTINE_EEZ_PATROL",
                sea_area_scope="Biển Đông",
                commanding_officer="Chỉ huy",
                nautical_miles=-10.0,
            )

    def test_record_inspection_valid(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        res = engine.record_inspection(
            inspection_id="INSP-2026-001",
            target_vessel_name="Tàu hàng Minh Phú 09",
            registration_or_imo="HP-98765-HH",
            inspection_reason="SMUGGLING_CONTRABAND_SUSPICION",
            location_coordinates="19°45'N 107°12'E",
            inspecting_vessel_id="CSB-8002",
            flag_state="VNM",
            violations_found=True,
            fine_amount_vnd=150000000.0,
            contraband_description="Vận chuyển 200,000 lít dầu DO không hóa đơn chứng từ",
            inspection_date="2026-03-10",
        )
        assert res["inspection_id"] == "INSP-2026-001"
        assert res["target_vessel_name"] == "Tàu hàng Minh Phú 09"
        assert res["violations_found"] is True
        assert res["fine_amount_vnd"] == 150000000.0
        assert "dầu DO" in res["contraband_description"]

    def test_record_inspection_duplicate(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.record_inspection(
            inspection_id="INSP-DUP",
            target_vessel_name="Tàu A",
            registration_or_imo="REG-123",
            inspection_reason="ROUTINE_CHECKS",
            location_coordinates="10°N 105°E",
            inspecting_vessel_id="CSB-8002",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.record_inspection(
                inspection_id="INSP-DUP",
                target_vessel_name="Tàu A",
                registration_or_imo="REG-123",
                inspection_reason="ROUTINE_CHECKS",
                location_coordinates="10°N 105°E",
                inspecting_vessel_id="CSB-8002",
            )

    def test_record_inspection_invalid_inputs(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.record_inspection(
                inspection_id="",
                target_vessel_name="Tàu",
                registration_or_imo="",
                inspection_reason="ROUTINE_CHECKS",
                location_coordinates="",
                inspecting_vessel_id="CSB-8002",
            )

        with pytest.raises(ValueError, match="Invalid inspection_reason"):
            engine.record_inspection(
                inspection_id="INSP-INV",
                target_vessel_name="Tàu",
                registration_or_imo="REG-1",
                inspection_reason="SPACE_ALIEN_INTERDICTION",
                location_coordinates="10°N 105°E",
                inspecting_vessel_id="CSB-8002",
            )

        with pytest.raises(ValueError, match="fine_amount_vnd cannot be negative"):
            engine.record_inspection(
                inspection_id="INSP-INV-FINE",
                target_vessel_name="Tàu",
                registration_or_imo="REG-1",
                inspection_reason="ROUTINE_CHECKS",
                location_coordinates="10°N 105°E",
                inspecting_vessel_id="CSB-8002",
                fine_amount_vnd=-1000.0,
            )

    def test_report_iuu_valid(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        res = engine.report_iuu_case(
            case_id="IUU-2026-001",
            fishing_vessel_id="BV-92456-TS",
            owner_or_captain="Nguyễn Văn Tèo",
            home_province="Bà Rịa - Vũng Tàu",
            violation_type="CROSSING_MARITIME_BOUNDARY",
            handling_authority="Bộ Tư lệnh Vùng Cảnh sát biển 3",
            penalty_amount_vnd=900000000.0,
            license_revoked=True,
            vessel_impounded=True,
            sanction_date="2026-03-12",
        )
        assert res["case_id"] == "IUU-2026-001"
        assert res["fishing_vessel_id"] == "BV-92456-TS"
        assert res["violation_type"] == "CROSSING_MARITIME_BOUNDARY"
        assert res["penalty_amount_vnd"] == 900000000.0
        assert res["license_revoked"] is True
        assert res["vessel_impounded"] is True

    def test_report_iuu_duplicate(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.report_iuu_case(
            case_id="IUU-DUP",
            fishing_vessel_id="QN-12345-TS",
            owner_or_captain="Trần Văn Cường",
            home_province="Quảng Ngãi",
            violation_type="VMS_DISCONNECTION",
            handling_authority="Vùng CSB 2",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.report_iuu_case(
                case_id="IUU-DUP",
                fishing_vessel_id="QN-12345-TS",
                owner_or_captain="Trần Văn Cường",
                home_province="Quảng Ngãi",
                violation_type="VMS_DISCONNECTION",
                handling_authority="Vùng CSB 2",
            )

    def test_report_iuu_invalid_inputs(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.report_iuu_case(
                case_id="",
                fishing_vessel_id="",
                owner_or_captain="",
                home_province="",
                violation_type="VMS_DISCONNECTION",
                handling_authority="CSB",
            )

        with pytest.raises(ValueError, match="Invalid violation_type"):
            engine.report_iuu_case(
                case_id="IUU-INV",
                fishing_vessel_id="QN-12345-TS",
                owner_or_captain="Trần Văn",
                home_province="Quảng Ngãi",
                violation_type="ILLEGAL_DOLPHIN_PETTING",
                handling_authority="CSB",
            )

        with pytest.raises(ValueError, match="penalty_amount_vnd cannot be negative"):
            engine.report_iuu_case(
                case_id="IUU-INV-PEN",
                fishing_vessel_id="QN-12345-TS",
                owner_or_captain="Trần Văn",
                home_province="Quảng Ngãi",
                violation_type="VMS_DISCONNECTION",
                handling_authority="CSB",
                penalty_amount_vnd=-500.0,
            )

    def test_log_sar_valid(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        res = engine.log_sar_mission(
            sar_id="SAR-2026-001",
            mission_name="Cứu nạn 12 ngư dân tàu cá BĐ-97123-TS chìm tại Trường Sa",
            sar_type="SHIPWRECK_SINKING_RESCUE",
            distress_location="10°15'N 114°20'E (Đảo Song Tử Tây)",
            involved_vessel_name="Tàu cá BĐ-97123-TS",
            responding_vessel_id="CSB-8002",
            rescued_persons_count=12,
            assisted_vessel_salvaged=False,
            mission_date="2026-03-14",
        )
        assert res["sar_id"] == "SAR-2026-001"
        assert res["rescued_persons_count"] == 12
        assert res["assisted_vessel_salvaged"] is False
        assert res["sar_type"] == "SHIPWRECK_SINKING_RESCUE"

    def test_log_sar_duplicate(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.log_sar_mission(
            sar_id="SAR-DUP",
            mission_name="Lai dắt tàu hỏng máy",
            sar_type="VESSEL_DISTRESS_TOW",
            distress_location="Vịnh Hạ Long",
            involved_vessel_name="Tàu Du lịch 01",
            responding_vessel_id="CSB-4031",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_sar_mission(
                sar_id="SAR-DUP",
                mission_name="Lai dắt tàu hỏng máy",
                sar_type="VESSEL_DISTRESS_TOW",
                distress_location="Vịnh Hạ Long",
                involved_vessel_name="Tàu Du lịch 01",
                responding_vessel_id="CSB-4031",
            )

    def test_log_sar_invalid_inputs(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.log_sar_mission(
                sar_id="",
                mission_name="",
                sar_type="VESSEL_DISTRESS_TOW",
                distress_location="",
                involved_vessel_name="",
                responding_vessel_id="CSB-4031",
            )

        with pytest.raises(ValueError, match="Invalid sar_type"):
            engine.log_sar_mission(
                sar_id="SAR-INV",
                mission_name="Nhiệm vụ",
                sar_type="SPACE_RECOVERY",
                distress_location="Biển",
                involved_vessel_name="Tàu",
                responding_vessel_id="CSB-4031",
            )

        with pytest.raises(ValueError, match="rescued_persons_count cannot be negative"):
            engine.log_sar_mission(
                sar_id="SAR-INV-CNT",
                mission_name="Nhiệm vụ",
                sar_type="VESSEL_DISTRESS_TOW",
                distress_location="Biển",
                involved_vessel_name="Tàu",
                responding_vessel_id="CSB-4031",
                rescued_persons_count=-3,
            )

    def test_list_records_categories(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.register_vessel("V-1", "8001", "OFFSHORE_PATROL_VESSEL_OPV", "REGION_1_NORTH", "Hải Phòng")
        engine.log_patrol("P-1", "V-1", "ROUTINE_EEZ_PATROL", "Vịnh Bắc Bộ", "Đại úy An")
        engine.record_inspection("I-1", "Tàu X", "IMO-1", "ROUTINE_CHECKS", "10N 105E", "V-1")
        engine.report_iuu_case("U-1", "F-1", "Nguyễn A", "Kiên Giang", "VMS_DISCONNECTION", "CSB 4")
        engine.log_sar_mission("S-1", "Cứu hộ", "VESSEL_DISTRESS_TOW", "10N 105E", "Tàu Y", "V-1")

        all_records = engine.list_records(record_type="all")
        assert len(all_records["vessels"]) == 1
        assert len(all_records["patrols"]) == 1
        assert len(all_records["inspections"]) == 1
        assert len(all_records["iuu"]) == 1
        assert len(all_records["sar"]) == 1

        vessels_only = engine.list_records(record_type="vessels")
        assert "vessels" in vessels_only
        assert "patrols" not in vessels_only

    def test_telemetry_status_calculations(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        engine.register_vessel("V-1", "8001", "OFFSHORE_PATROL_VESSEL_OPV", "REGION_1_NORTH", "Hải Phòng", status="ACTIVE_MISSION_READY")
        engine.register_vessel("V-2", "8002", "OFFSHORE_PATROL_VESSEL_OPV", "REGION_2_CENTRAL", "Kỳ Hà", status="ACTIVE_MISSION_READY")
        engine.register_vessel("V-3", "4031", "FAST_PATROL_BOAT_FPB", "REGION_2_CENTRAL", "Đà Nẵng", status="STANDBY_HARBOR")

        engine.log_patrol("P-1", "V-1", "ROUTINE_EEZ_PATROL", "Vịnh Bắc Bộ", "Chỉ huy 1", days_at_sea=10, nautical_miles=800.0)
        engine.log_patrol("P-2", "V-2", "SOVEREIGNTY_PROTECTION_SORTIE", "Hoàng Sa", "Chỉ huy 2", days_at_sea=20, nautical_miles=1500.0)

        engine.record_inspection("I-1", "Tàu 1", "REG-1", "SMUGGLING_CONTRABAND_SUSPICION", "10N 105E", "V-1", violations_found=True, fine_amount_vnd=50000000.0)
        engine.record_inspection("I-2", "Tàu 2", "REG-2", "ROUTINE_CHECKS", "11N 106E", "V-2", violations_found=False, fine_amount_vnd=0.0)

        engine.report_iuu_case("U-1", "F-1", "Chủ tàu 1", "Bình Định", "CROSSING_MARITIME_BOUNDARY", "CSB 2", penalty_amount_vnd=800000000.0)
        engine.log_sar_mission("S-1", "SAR 1", "SHIPWRECK_SINKING_RESCUE", "10N 110E", "Tàu đắm", "V-2", rescued_persons_count=8)

        telemetry = engine.get_telemetry_status()
        assert telemetry["mission_ready_vessels"] == 2
        assert telemetry["vessels_by_region"]["REGION_1_NORTH"] == 1
        assert telemetry["vessels_by_region"]["REGION_2_CENTRAL"] == 2
        assert telemetry["total_maritime_patrols"] == 2
        assert telemetry["total_days_at_sea"] == 30
        assert telemetry["total_nautical_miles"] == 2300.0
        assert telemetry["total_inspections"] == 2
        assert telemetry["infringements_detected"] == 1
        assert telemetry["total_inspection_fines_vnd"] == 50000000.0
        assert telemetry["total_iuu_cases"] == 1
        assert telemetry["total_iuu_penalties_vnd"] == 800000000.0
        assert telemetry["total_sar_missions"] == 1
        assert telemetry["total_lives_rescued"] == 8


class TestCoastGuardCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(coastguard_app, [])
        assert result.exit_code == 0
        assert "BỘ TƯ LỆNH CẢNH SÁT BIỂN VIỆT NAM" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(coastguard_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mission_ready_vessels" in data
        assert "total_maritime_patrols" in data

    def test_cli_status_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(coastguard_app, ["status"])
        assert res_text.exit_code == 0
        assert "Cảnh sát biển" in res_text.output

        res_json = runner.invoke(coastguard_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_lives_rescued" in data

    def test_cli_vessel_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "vessel",
                "--id", "CSB-8002",
                "--hull", "8002",
                "--class", "OFFSHORE_PATROL_VESSEL_OPV",
                "--region", "REGION_2_CENTRAL",
                "--port", "Cảng Kỳ Hà",
                "--displacement", "2500",
                "--year", "2015",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["vessel_id"] == "CSB-8002"
        assert data["displacement_tons"] == 2500.0

    def test_cli_vessel_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "vessel",
                "--id", "CSB-ERR",
                "--hull", "ERR",
                "--class", "INVALID_CLASS",
                "--region", "REGION_2_CENTRAL",
                "--port", "Port",
            ],
        )
        assert result.exit_code != 0

    def test_cli_patrol_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "patrol",
                "--id", "PATROL-CLI-01",
                "--vessel", "CSB-8002",
                "--type", "SOVEREIGNTY_PROTECTION_SORTIE",
                "--scope", "Vùng biển Quần đảo Hoàng Sa",
                "--commander", "Thượng tá Nguyễn Văn A",
                "--days", "15",
                "--miles", "1500",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["patrol_id"] == "PATROL-CLI-01"
        assert data["nautical_miles"] == 1500.0

    def test_cli_patrol_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "patrol",
                "--id", "PATROL-ERR",
                "--vessel", "CSB-ERR",
                "--type", "INVALID_TYPE",
                "--scope", "Scope",
                "--commander", "Cmd",
            ],
        )
        assert result.exit_code != 0

    def test_cli_inspect_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "inspect",
                "--id", "INSP-CLI-01",
                "--target", "Tàu vận tải Thái Bình 56",
                "--reg", "IMO-9871122",
                "--reason", "SMUGGLING_CONTRABAND_SUSPICION",
                "--coords", "15°30'N 109°20'E",
                "--by", "CSB-8002",
                "--violations",
                "--fine", "200000000",
                "--contraband", "500 thùng thuốc lá ngoại nhập lậu",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inspection_id"] == "INSP-CLI-01"
        assert data["fine_amount_vnd"] == 200000000.0
        assert data["violations_found"] is True

    def test_cli_inspect_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "inspect",
                "--id", "INSP-ERR",
                "--target", "Target",
                "--reg", "REG",
                "--reason", "INVALID_REASON",
                "--coords", "Coords",
                "--by", "By",
            ],
        )
        assert result.exit_code != 0

    def test_cli_iuu_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "iuu",
                "--id", "IUU-CLI-01",
                "--vessel", "KG-95567-TS",
                "--owner", "Lê Văn Hùng",
                "--province", "Kiên Giang",
                "--violation", "VMS_DISCONNECTION",
                "--authority", "Bộ Tư lệnh Vùng CSB 4",
                "--penalty", "25000000",
                "--revoke-license",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["case_id"] == "IUU-CLI-01"
        assert data["penalty_amount_vnd"] == 25000000.0
        assert data["license_revoked"] is True

    def test_cli_iuu_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "iuu",
                "--id", "IUU-ERR",
                "--vessel", "KG-123",
                "--owner", "Owner",
                "--province", "Prov",
                "--violation", "INVALID_IUU",
                "--authority", "Auth",
            ],
        )
        assert result.exit_code != 0

    def test_cli_sar_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "sar",
                "--id", "SAR-CLI-01",
                "--name", "Cứu nạn thuyền viên gãy chân trên biển",
                "--type", "CREW_MEDICAL_EMERGENCY",
                "--location", "08°40'N 105°10'E",
                "--target", "Tàu cá BV-7890-TS",
                "--by", "CSB-2011",
                "--rescued", "1",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["sar_id"] == "SAR-CLI-01"
        assert data["rescued_persons_count"] == 1

    def test_cli_sar_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            coastguard_app,
            [
                "sar",
                "--id", "SAR-ERR",
                "--name", "Name",
                "--type", "INVALID_SAR",
                "--location", "Loc",
                "--target", "Target",
                "--by", "By",
            ],
        )
        assert result.exit_code != 0

    def test_cli_list_command_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(coastguard_app, ["list", "--type", "all"])
        assert res_text.exit_code == 0

        res_json = runner.invoke(coastguard_app, ["list", "--type", "all", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "vessels" in data
        assert "sar" in data

    def test_cli_help_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(coastguard_app, ["--help"])
        assert result.exit_code == 0
        assert "vessel" in result.output
        assert "patrol" in result.output
        assert "inspect" in result.output
        assert "iuu" in result.output
        assert "sar" in result.output
        assert "list" in result.output
        assert "status" in result.output


class TestCoastGuardMCP:
    def test_mcp_standalone_vessel(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_vessel

        res_str = handle_coastguard_vessel({
            "vessel_id": "CSB-MCP-01",
            "hull_number": "8005",
            "vessel_class": "OFFSHORE_PATROL_VESSEL_OPV",
            "assigned_region": "REGION_3_SOUTH",
            "home_port": "Cảng Vũng Tàu",
            "displacement_tons": 2500.0,
            "commission_year": 2016,
        })
        res = json.loads(res_str)
        assert res["vessel_id"] == "CSB-MCP-01"
        assert res["assigned_region"] == "REGION_3_SOUTH"

    def test_mcp_standalone_patrol(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_patrol

        res_str = handle_coastguard_patrol({
            "patrol_id": "PATROL-MCP-01",
            "vessel_id": "CSB-8005",
            "patrol_type": "ANTI_SMUGGLING_SWEEP",
            "sea_area_scope": "Vùng biển giáp ranh Việt Nam - Indonesia",
            "commanding_officer": "Trung tá Vũ Hoàng Long",
            "days_at_sea": 10,
            "nautical_miles": 850.0,
        })
        res = json.loads(res_str)
        assert res["patrol_id"] == "PATROL-MCP-01"
        assert res["patrol_type"] == "ANTI_SMUGGLING_SWEEP"

    def test_mcp_standalone_inspect(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_inspect

        res_str = handle_coastguard_inspect({
            "inspection_id": "INSP-MCP-01",
            "target_vessel_name": "Tàu vận tải Biển Đông",
            "registration_or_imo": "IMO-9112233",
            "inspection_reason": "STS_ILLEGAL_TRANSFER",
            "location_coordinates": "07°30'N 104°20'E",
            "inspecting_vessel_id": "CSB-8005",
            "violations_found": True,
            "fine_amount_vnd": 300000000.0,
            "contraband_description": "Sang mạn dầu trái phép trên biển",
        })
        res = json.loads(res_str)
        assert res["inspection_id"] == "INSP-MCP-01"
        assert res["fine_amount_vnd"] == 300000000.0

    def test_mcp_standalone_iuu(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_iuu

        res_str = handle_coastguard_iuu({
            "case_id": "IUU-MCP-01",
            "fishing_vessel_id": "CM-91234-TS",
            "owner_or_captain": "Trịnh Quốc Đạt",
            "home_province": "Cà Mau",
            "violation_type": "UNREGISTERED_VESSEL_3_NO",
            "handling_authority": "Bộ Tư lệnh Vùng CSB 4",
            "penalty_amount_vnd": 50000000.0,
            "vessel_impounded": True,
        })
        res = json.loads(res_str)
        assert res["case_id"] == "IUU-MCP-01"
        assert res["violation_type"] == "UNREGISTERED_VESSEL_3_NO"
        assert res["vessel_impounded"] is True

    def test_mcp_standalone_sar(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_sar

        res_str = handle_coastguard_sar({
            "sar_id": "SAR-MCP-01",
            "mission_name": "Cứu hộ tàu cá hỏng máy trôi dạt",
            "sar_type": "VESSEL_DISTRESS_TOW",
            "distress_location": "12°30'N 110°10'E",
            "involved_vessel_name": "Tàu cá PY-90111-TS",
            "responding_vessel_id": "CSB-8005",
            "rescued_persons_count": 5,
            "assisted_vessel_salvaged": True,
        })
        res = json.loads(res_str)
        assert res["sar_id"] == "SAR-MCP-01"
        assert res["rescued_persons_count"] == 5

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_coastguard_list, handle_coastguard_status

        list_str = handle_coastguard_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "vessels" in lst
        assert "patrols" in lst

        stat_str = handle_coastguard_status({})
        stat = json.loads(stat_str)
        assert "mission_ready_vessels" in stat
        assert "total_maritime_patrols" in stat

    def test_mcp_standalone_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_coastguard_inspect,
            handle_coastguard_iuu,
            handle_coastguard_patrol,
            handle_coastguard_sar,
            handle_coastguard_vessel,
        )

        err_v = json.loads(handle_coastguard_vessel({}))
        assert err_v["ok"] is False
        assert "error" in err_v

        err_p = json.loads(handle_coastguard_patrol({}))
        assert err_p["ok"] is False

        err_i = json.loads(handle_coastguard_inspect({}))
        assert err_i["ok"] is False

        err_u = json.loads(handle_coastguard_iuu({}))
        assert err_u["ok"] is False

        err_s = json.loads(handle_coastguard_sar({}))
        assert err_s["ok"] is False

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        v_str = server._handle_coastguard_vessel(
            vessel_id="CSB-CORE-01",
            hull_number="4038",
            vessel_class="FAST_PATROL_BOAT_FPB",
            assigned_region="REGION_1_NORTH",
            home_port="Hải Phòng",
        )
        v_data = json.loads(v_str)
        assert v_data["vessel_id"] == "CSB-CORE-01"

        p_str = server._handle_coastguard_patrol(
            patrol_id="PAT-CORE-01",
            vessel_id="CSB-CORE-01",
            patrol_type="ROUTINE_EEZ_PATROL",
            sea_area_scope="Vịnh Bắc Bộ",
            commanding_officer="Đại úy Nguyễn",
        )
        p_data = json.loads(p_str)
        assert p_data["patrol_id"] == "PAT-CORE-01"

        i_str = server._handle_coastguard_inspect(
            inspection_id="INSP-CORE-01",
            target_vessel_name="Tàu Core",
            registration_or_imo="REG-CORE",
            location_coordinates="19N 107E",
            inspecting_vessel_id="CSB-CORE-01",
        )
        i_data = json.loads(i_str)
        assert i_data["inspection_id"] == "INSP-CORE-01"

        u_str = server._handle_coastguard_iuu(
            case_id="IUU-CORE-01",
            fishing_vessel_id="QN-CORE-TS",
            owner_or_captain="Chủ Core",
            home_province="Quảng Ninh",
            handling_authority="Vùng CSB 1",
        )
        u_data = json.loads(u_str)
        assert u_data["case_id"] == "IUU-CORE-01"

        s_str = server._handle_coastguard_sar(
            sar_id="SAR-CORE-01",
            mission_name="Cứu hộ Core",
            distress_location="Vịnh Bắc Bộ",
            involved_vessel_name="Tàu Core Đắm",
            responding_vessel_id="CSB-CORE-01",
        )
        s_data = json.loads(s_str)
        assert s_data["sar_id"] == "SAR-CORE-01"

        lst_str = server._handle_coastguard_list(category="all")
        lst_data = json.loads(lst_str)
        assert len(lst_data["vessels"]) >= 1

        stat_str = server._handle_coastguard_status()
        stat_data = json.loads(stat_str)
        assert stat_data["mission_ready_vessels"] >= 1

    def test_scripts_mcp_server_core_handlers_parity(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected_tools = [
            "mekong_coastguard_vessel",
            "mekong_coastguard_patrol",
            "mekong_coastguard_inspect",
            "mekong_coastguard_iuu",
            "mekong_coastguard_sar",
            "mekong_coastguard_list",
            "mekong_coastguard_status",
            "coastguard_vessel",
            "coastguard_patrol",
            "coastguard_inspect",
            "coastguard_iuu",
            "coastguard_sar",
            "coastguard_list",
            "coastguard_status",
        ]
        for tool in expected_tools:
            assert tool in CORE_HANDLERS, f"Missing {tool} in scripts.mcp_server.CORE_HANDLERS"
            assert callable(CORE_HANDLERS[tool]), f"{tool} handler is not callable"

    def test_scripts_mcp_server_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected_spec_tools = [
            "mekong_coastguard_vessel",
            "mekong_coastguard_patrol",
            "mekong_coastguard_inspect",
            "mekong_coastguard_iuu",
            "mekong_coastguard_sar",
            "mekong_coastguard_list",
            "mekong_coastguard_status",
        ]
        for tool in expected_spec_tools:
            assert tool in spec_names, f"Missing {tool} in scripts.mcp_server.CORE_TOOLS_SPEC"


class TestCoastGuardEdgeCases:
    def test_all_regions_supported(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        for i, reg in enumerate(sorted(VALID_COASTGUARD_REGIONS)):
            res = engine.register_vessel(
                vessel_id=f"CSB-REG-{i}",
                hull_number=f"800{i}",
                vessel_class="OFFSHORE_PATROL_VESSEL_OPV",
                assigned_region=reg,
                home_port="Cảng",
            )
            assert res["assigned_region"] == reg

    def test_all_vessel_classes_supported(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        for i, cls in enumerate(sorted(VALID_VESSEL_CLASSES)):
            res = engine.register_vessel(
                vessel_id=f"CSB-CLS-{i}",
                hull_number=f"400{i}",
                vessel_class=cls,
                assigned_region="REGION_2_CENTRAL",
                home_port="Cảng",
            )
            assert res["vessel_class"] == cls

    def test_all_patrol_types_supported(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        for i, ptype in enumerate(sorted(VALID_PATROL_TYPES)):
            res = engine.log_patrol(
                patrol_id=f"PAT-TYPE-{i}",
                vessel_id="CSB-8002",
                patrol_type=ptype,
                sea_area_scope="Vùng biển thử nghiệm",
                commanding_officer="Chỉ huy",
            )
            assert res["patrol_type"] == ptype

    def test_all_inspection_reasons_supported(self, temp_db: str) -> None:
        engine = CoastGuardEngine(db_path=temp_db)
        for i, reason in enumerate(sorted(VALID_INSPECTION_REASONS)):
            res = engine.record_inspection(
                inspection_id=f"INSP-REASON-{i}",
                target_vessel_name="Tàu Kiểm tra",
                registration_or_imo=f"IMO-00{i}",
                inspection_reason=reason,
                location_coordinates="10N 105E",
                inspecting_vessel_id="CSB-8002",
            )
            assert res["inspection_reason"] == reason
