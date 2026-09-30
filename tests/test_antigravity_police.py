"""
Unit and integration tests for Vietnamese People's Public Security & Grassroots Security Forces Suite.
Governed by:
- Law on People's Public Security 2018 (Law No. 37/2018/QH14) as amended by Law No. 21/2023/QH15
- Law on Forces Participating in Safeguarding Security and Order at the Grassroots Level 2023 (Law No. 30/2023/QH15)
- Decree No. 40/2024/NĐ-CP & Circular No. 14/2024/TT-BCA
- Law on Residence 2020 (Law No. 68/2020/QH15)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.police_command import app as police_app
from src.core.police_engine import (
    VALID_GEAR_TYPES,
    VALID_INCIDENT_SEVERITIES,
    VALID_INCIDENT_TYPES,
    VALID_OFFICER_STATUS,
    VALID_PATROL_TYPES,
    VALID_POLICE_RANKS,
    VALID_RESIDENCE_COMPLIANCE,
    VALID_RESOLUTION_STATUS,
    VALID_SPECIALIZATIONS,
    VALID_TEAM_STATUS,
    PoliceEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_POLICE_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestPoliceEngine:
    def test_register_officer_valid(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        res = engine.register_officer(
            officer_badge="BCA-CAND-012345",
            full_name="Nguyễn Văn Hùng",
            rank="DAI_UY",
            position="Cảnh sát khu vực",
            unit_name="Công an Phường Bến Nghé, Quận 1",
            specialization="CANH_SAT_QLHC_TTXH",
            status="ON_DUTY_ACTIVE",
        )
        assert res["officer_badge"] == "BCA-CAND-012345"
        assert res["full_name"] == "Nguyễn Văn Hùng"
        assert res["rank"] == "DAI_UY"
        assert res["status"] == "ON_DUTY_ACTIVE"

    def test_register_officer_missing_fields(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.register_officer(
                officer_badge="",
                full_name="Nguyễn Văn Hùng",
                rank="DAI_UY",
                position="Cảnh sát",
                unit_name="Công an Phường",
            )

    def test_register_officer_invalid_rank(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid rank"):
            engine.register_officer(
                officer_badge="BCA-001",
                full_name="Nguyễn Văn Hùng",
                rank="FIELD_MARSHAL",
                position="Cảnh sát",
                unit_name="Công an Phường",
            )

    def test_register_officer_invalid_specialization(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid specialization"):
            engine.register_officer(
                officer_badge="BCA-001",
                full_name="Nguyễn Văn Hùng",
                rank="DAI_UY",
                position="Cảnh sát",
                unit_name="Công an Phường",
                specialization="UNKNOWN_SPEC",
            )

    def test_register_officer_invalid_status(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_officer(
                officer_badge="BCA-001",
                full_name="Nguyễn Văn Hùng",
                rank="DAI_UY",
                position="Cảnh sát",
                unit_name="Công an Phường",
                status="SLEEPING",
            )

    def test_register_officer_duplicate(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.register_officer(
            officer_badge="BCA-DUP-01",
            full_name="Trần Thị Mai",
            rank="THIEU_TA",
            position="Phó Trưởng Công an Xã",
            unit_name="Công an Xã Tân Triều",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_officer(
                officer_badge="BCA-DUP-01",
                full_name="Trần Thị Mai",
                rank="THIEU_TA",
                position="Phó Trưởng Công an Xã",
                unit_name="Công an Xã Tân Triều",
            )

    def test_register_grassroots_team_valid(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        res = engine.register_grassroots_team(
            team_id="GR-TEAM-Q1-TDP05",
            team_name="Tổ Bảo vệ ANTT Tổ dân phố 5",
            ward_commune="Phường Bến Nghé",
            district_county="Quận 1",
            province_city="TP. Hồ Chí Minh",
            team_leader_name="Lê Minh Tâm",
            member_count=4,
            equipped_gear="STANDARD_SUPPORT_GEAR",
            status="ACTIVE_DEPLOYED",
        )
        assert res["team_id"] == "GR-TEAM-Q1-TDP05"
        assert res["member_count"] == 4
        assert res["status"] == "ACTIVE_DEPLOYED"

    def test_register_grassroots_team_min_members(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="at least 3 members"):
            engine.register_grassroots_team(
                team_id="GR-INVALID",
                team_name="Tổ Thiếu người",
                ward_commune="Phường 1",
                district_county="Quận 1",
                province_city="TP.HCM",
                team_leader_name="Ai Đó",
                member_count=2,
            )

    def test_register_grassroots_team_invalid_gear(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid equipped_gear"):
            engine.register_grassroots_team(
                team_id="GR-INV-GEAR",
                team_name="Tổ Test",
                ward_commune="Phường 1",
                district_county="Quận 1",
                province_city="TP.HCM",
                team_leader_name="Ai Đó",
                equipped_gear="HEAVY_ARTILLERY",
            )

    def test_register_grassroots_team_invalid_status(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_grassroots_team(
                team_id="GR-INV-STATUS",
                team_name="Tổ Test",
                ward_commune="Phường 1",
                district_county="Quận 1",
                province_city="TP.HCM",
                team_leader_name="Ai Đó",
                status="OFF_GRID",
            )

    def test_register_grassroots_team_missing_fields(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.register_grassroots_team(
                team_id="",
                team_name="Tổ Test",
                ward_commune="Phường 1",
                district_county="Quận 1",
                province_city="TP.HCM",
                team_leader_name="Ai Đó",
            )

    def test_register_grassroots_team_duplicate(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.register_grassroots_team(
            team_id="GR-DUP",
            team_name="Tổ Trùng lặp",
            ward_commune="Phường 1",
            district_county="Quận 1",
            province_city="TP.HCM",
            team_leader_name="Ai Đó",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_grassroots_team(
                team_id="GR-DUP",
                team_name="Tổ Trùng lặp",
                ward_commune="Phường 1",
                district_county="Quận 1",
                province_city="TP.HCM",
                team_leader_name="Ai Đó",
            )

    def test_report_incident_valid(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        res = engine.report_incident(
            incident_id="INC-POLICE-2026-001",
            incident_type="PUBLIC_DISORDER",
            location="Khu vực chợ Bến Thành, Quận 1",
            ward_commune="Phường Bến Thành",
            reported_by="Người dân phản ánh qua VNeID",
            assigned_unit="Công an Phường Bến Thành",
            severity="MEDIUM_INVESTIGATION",
            resolution_status="REPORTED_DISPATCHED",
        )
        assert res["incident_id"] == "INC-POLICE-2026-001"
        assert res["incident_type"] == "PUBLIC_DISORDER"
        assert res["resolution_status"] == "REPORTED_DISPATCHED"

    def test_report_incident_invalid_type(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid incident_type"):
            engine.report_incident(
                incident_id="INC-INV",
                incident_type="ALIEN_INVASION",
                location="Loc",
                ward_commune="Ward",
                reported_by="User",
                assigned_unit="Unit",
            )

    def test_report_incident_invalid_severity(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid severity"):
            engine.report_incident(
                incident_id="INC-INV2",
                incident_type="PUBLIC_DISORDER",
                location="Loc",
                ward_commune="Ward",
                reported_by="User",
                assigned_unit="Unit",
                severity="DOOMSDAY",
            )

    def test_report_incident_invalid_resolution_status(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid resolution_status"):
            engine.report_incident(
                incident_id="INC-INV3",
                incident_type="PUBLIC_DISORDER",
                location="Loc",
                ward_commune="Ward",
                reported_by="User",
                assigned_unit="Unit",
                resolution_status="FORGOTTEN",
            )

    def test_report_incident_missing_fields(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.report_incident(
                incident_id="",
                incident_type="PUBLIC_DISORDER",
                location="Loc",
                ward_commune="Ward",
                reported_by="User",
                assigned_unit="Unit",
            )

    def test_report_incident_duplicate(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.report_incident(
            incident_id="INC-DUP",
            incident_type="DOMESTIC_VIOLENCE",
            location="Số 12 Ngõ 3 Phố Huế",
            ward_commune="Phường Hàng Bài",
            reported_by="Tổ trưởng dân phố",
            assigned_unit="Công an Phường",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.report_incident(
                incident_id="INC-DUP",
                incident_type="DOMESTIC_VIOLENCE",
                location="Số 12 Ngõ 3 Phố Huế",
                ward_commune="Phường Hàng Bài",
                reported_by="Tổ trưởng dân phố",
                assigned_unit="Công an Phường",
            )

    def test_log_patrol_mission_valid(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        res = engine.log_patrol_mission(
            mission_id="PATROL-2026-001",
            patrol_type="JOINT_POLICE_GRASSROOTS",
            route_or_zone="Tuyến phố đi bộ Nguyễn Huệ và bờ sông Sài Gòn",
            lead_officer_badge="BCA-CAND-012345",
            grassroots_team_id="GR-TEAM-Q1-TDP05",
            persons_checked=15,
            infractions_detected=2,
        )
        assert res["mission_id"] == "PATROL-2026-001"
        assert res["persons_checked"] == 15
        assert res["infractions_detected"] == 2

    def test_log_patrol_mission_invalid_type(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid patrol_type"):
            engine.log_patrol_mission(
                mission_id="PAT-INV",
                patrol_type="GALACTIC_CRUISE",
                route_or_zone="Route",
                lead_officer_badge="BCA-001",
                grassroots_team_id="GR-001",
            )

    def test_log_patrol_mission_negative_counts(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.log_patrol_mission(
                mission_id="PAT-INV2",
                patrol_type="NIGHT_ROUTINE_SECURITY",
                route_or_zone="Route",
                lead_officer_badge="BCA-001",
                grassroots_team_id="GR-001",
                persons_checked=-1,
            )

    def test_log_patrol_mission_missing_fields(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.log_patrol_mission(
                mission_id="",
                patrol_type="NIGHT_ROUTINE_SECURITY",
                route_or_zone="Route",
                lead_officer_badge="BCA-001",
                grassroots_team_id="GR-001",
            )

    def test_log_patrol_mission_duplicate(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.log_patrol_mission(
            mission_id="PAT-DUP",
            patrol_type="NIGHT_ROUTINE_SECURITY",
            route_or_zone="Route",
            lead_officer_badge="BCA-001",
            grassroots_team_id="GR-001",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_patrol_mission(
                mission_id="PAT-DUP",
                patrol_type="NIGHT_ROUTINE_SECURITY",
                route_or_zone="Route",
                lead_officer_badge="BCA-001",
                grassroots_team_id="GR-001",
            )

    def test_record_residence_check_valid(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        res = engine.record_residence_check(
            check_id="RES-2026-001",
            address="Chung cư Vincom Đồng Khởi, Q1, TP.HCM",
            household_head_name="Phạm Gia Khiêm",
            inspecting_officer_badge="BCA-CAND-012345",
            registered_residents_count=3,
            actual_present_count=3,
            temporary_stay_verified=True,
            violating_persons_count=0,
            compliance_status="COMPLIANT_VERIFIED",
        )
        assert res["check_id"] == "RES-2026-001"
        assert res["temporary_stay_verified"] is True
        assert res["compliance_status"] == "COMPLIANT_VERIFIED"

    def test_record_residence_check_invalid_compliance(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid compliance_status"):
            engine.record_residence_check(
                check_id="RES-INV",
                address="Addr",
                household_head_name="Head",
                inspecting_officer_badge="BCA-001",
                compliance_status="ALL_GOOD_BRO",
            )

    def test_record_residence_check_negative_counts(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.record_residence_check(
                check_id="RES-INV2",
                address="Addr",
                household_head_name="Head",
                inspecting_officer_badge="BCA-001",
                registered_residents_count=-2,
            )

    def test_record_residence_check_missing_fields(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="required"):
            engine.record_residence_check(
                check_id="",
                address="Addr",
                household_head_name="Head",
                inspecting_officer_badge="BCA-001",
            )

    def test_record_residence_check_duplicate(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.record_residence_check(
            check_id="RES-DUP",
            address="Addr",
            household_head_name="Head",
            inspecting_officer_badge="BCA-001",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.record_residence_check(
                check_id="RES-DUP",
                address="Addr",
                household_head_name="Head",
                inspecting_officer_badge="BCA-001",
            )

    def test_list_records_all_and_categories(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.register_officer("BCA-01", "Officer A", "DAI_UY", "Pos", "Unit")
        engine.register_grassroots_team("GR-01", "Team A", "Ward", "District", "City", "Leader")
        engine.report_incident("INC-01", "PUBLIC_DISORDER", "Loc", "Ward", "Rep", "Unit")
        engine.log_patrol_mission("PAT-01", "JOINT_POLICE_GRASSROOTS", "Route", "BCA-01", "GR-01")
        engine.record_residence_check("RES-01", "Addr", "Head", "BCA-01")

        all_records = engine.list_records("all")
        assert len(all_records["officers"]) == 1
        assert len(all_records["teams"]) == 1
        assert len(all_records["incidents"]) == 1
        assert len(all_records["patrols"]) == 1
        assert len(all_records["residence"]) == 1

        off_only = engine.list_records("officers")
        assert "officers" in off_only
        assert "incidents" not in off_only

    def test_get_telemetry_status(self, temp_db: str) -> None:
        engine = PoliceEngine(db_path=temp_db)
        engine.register_officer("BCA-01", "Officer A", "DAI_UY", "Pos", "Unit")
        engine.register_grassroots_team("GR-01", "Team A", "Ward", "District", "City", "Leader", member_count=4)
        engine.report_incident("INC-01", "PROPERTY_THEFT_BURGLARY", "Loc", "Ward", "Rep", "Unit", severity="CRITICAL_EMERGENCY", resolution_status="REPORTED_DISPATCHED")
        engine.report_incident("INC-02", "DOMESTIC_VIOLENCE", "Loc", "Ward", "Rep", "Unit", severity="CRITICAL_EMERGENCY", resolution_status="RESOLVED_CLOSED")
        engine.log_patrol_mission("PAT-01", "NIGHT_ROUTINE_SECURITY", "Route", "BCA-01", "GR-01", persons_checked=10, infractions_detected=1)
        engine.record_residence_check("RES-01", "Addr 1", "Head 1", "BCA-01", compliance_status="COMPLIANT_VERIFIED")
        engine.record_residence_check("RES-02", "Addr 2", "Head 2", "BCA-01", compliance_status="IRREGULARITIES_NOTICE_ISSUED")

        telem = engine.get_telemetry_status()
        assert telem["active_duty_officers"] == 1
        assert telem["active_grassroots_teams"] == 1
        assert telem["grassroots_personnel_count"] == 4
        assert telem["total_security_incidents"] == 2
        assert telem["open_critical_emergencies"] == 1
        assert telem["total_patrol_missions"] == 1
        assert telem["patrol_persons_checked"] == 10
        assert telem["patrol_infractions_detected"] == 1
        assert telem["total_residence_checks"] == 2
        assert telem["residence_compliance_rate_percent"] == 50.0


class TestPoliceCLI:
    @pytest.fixture(autouse=True)
    def setup_runner(self) -> None:
        self.runner = CliRunner()

    def test_cli_dashboard_default(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, [])
        assert result.exit_code == 0
        assert "BỘ CÔNG AN" in result.stdout

    def test_cli_dashboard_json(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "active_duty_officers" in data
        assert "active_grassroots_teams" in data

    def test_cli_status(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, ["status"])
        assert result.exit_code == 0
        assert "Chỉ số Vận hành Lực lượng" in result.stdout

    def test_cli_status_json(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "active_duty_officers" in data

    def test_cli_officer_register(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "officer",
                "--badge", "BCA-CLI-01",
                "--name", "Hoàng Văn Tuấn",
                "--rank", "TRUNG_TA",
                "--position", "Phó Trưởng Công an Phường",
                "--unit", "Công an Phường Cầu Giấy",
            ],
        )
        assert result.exit_code == 0
        assert "Đăng ký Cán bộ Chiến sĩ" in result.stdout

    def test_cli_officer_register_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "officer",
                "--badge", "BCA-CLI-JSON",
                "--name", "Lê Văn Hùng",
                "--rank", "DAI_UY",
                "--position", "Cảnh sát khu vực",
                "--unit", "Công an Phường Dịch Vọng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["officer_badge"] == "BCA-CLI-JSON"

    def test_cli_officer_register_invalid(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "officer",
                "--badge", "BCA-ERR",
                "--name", "Test",
                "--rank", "INVALID_RANK",
                "--position", "Pos",
                "--unit", "Unit",
            ],
        )
        assert result.exit_code != 0

    def test_cli_team_register(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "team",
                "--id", "GR-CLI-01",
                "--name", "Tổ Bảo vệ ANTT Tổ 1",
                "--ward", "Phường Nghĩa Đô",
                "--district", "Quận Cầu Giấy",
                "--leader", "Trần Văn An",
                "--members", "5",
            ],
        )
        assert result.exit_code == 0
        assert "Tổ Bảo vệ An ninh, Trật tự ở Cơ sở" in result.stdout

    def test_cli_team_register_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "team",
                "--id", "GR-CLI-JSON",
                "--name", "Tổ Bảo vệ ANTT Tổ 2",
                "--ward", "Phường Nghĩa Đô",
                "--district", "Quận Cầu Giấy",
                "--leader", "Nguyễn Văn Bình",
                "--members", "3",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["team_id"] == "GR-CLI-JSON"

    def test_cli_team_register_invalid_members(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "team",
                "--id", "GR-ERR",
                "--name", "Tổ Ít Người",
                "--ward", "Phường 1",
                "--district", "Quận 1",
                "--leader", "Ai Đó",
                "--members", "1",
            ],
        )
        assert result.exit_code != 0

    def test_cli_incident_report(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "incident",
                "--id", "INC-CLI-01",
                "--type", "PROPERTY_THEFT_BURGLARY",
                "--location", "Số 15 Hoàng Hoa Thám",
                "--ward", "Phường Ngọc Hà",
                "--reporter", "Trần Thị Cúc",
                "--unit", "Công an Phường Ngọc Hà",
            ],
        )
        assert result.exit_code == 0
        assert "Tiếp nhận & Xử lý Vụ việc" in result.stdout

    def test_cli_incident_report_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "incident",
                "--id", "INC-CLI-JSON",
                "--type", "DOMESTIC_VIOLENCE",
                "--location", "Số 20 Đội Cấn",
                "--ward", "Phường Đội Cấn",
                "--reporter", "Hàng xóm báo tin",
                "--unit", "Công an Phường Đội Cấn",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["incident_id"] == "INC-CLI-JSON"

    def test_cli_patrol_log(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "patrol",
                "--id", "PAT-CLI-01",
                "--type", "JOINT_POLICE_GRASSROOTS",
                "--route", "Đường Liễu Giai - Kim Mã",
                "--badge", "BCA-CLI-01",
                "--team", "GR-CLI-01",
                "--checked", "8",
                "--infractions", "1",
            ],
        )
        assert result.exit_code == 0
        assert "Nhật ký Tuần tra Kiểm soát" in result.stdout

    def test_cli_patrol_log_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "patrol",
                "--id", "PAT-CLI-JSON",
                "--type", "NIGHT_ROUTINE_SECURITY",
                "--route", "Khu đô thị Trung Hòa",
                "--badge", "BCA-CLI-01",
                "--team", "GR-CLI-01",
                "--checked", "12",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["mission_id"] == "PAT-CLI-JSON"

    def test_cli_residence_record(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "residence",
                "--id", "RES-CLI-01",
                "--address", "Tòa nhà Landmark 81, P.22, Bình Thạnh",
                "--head", "Vũ Hoàng Giang",
                "--badge", "BCA-CLI-01",
                "--registered", "4",
                "--present", "4",
                "--temp-stay",
            ],
        )
        assert result.exit_code == 0
        assert "Biên bản Kiểm tra Hành chính Cư trú" in result.stdout

    def test_cli_residence_record_json(self, temp_db: str) -> None:
        result = self.runner.invoke(
            police_app,
            [
                "residence",
                "--id", "RES-CLI-JSON",
                "--address", "Số 55 Bà Triệu, Hà Nội",
                "--head", "Nguyễn Tiến Đạt",
                "--badge", "BCA-CLI-01",
                "--no-temp-stay",
                "--violating", "1",
                "--compliance", "IRREGULARITIES_NOTICE_ISSUED",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["check_id"] == "RES-CLI-JSON"
        assert data["compliance_status"] == "IRREGULARITIES_NOTICE_ISSUED"

    def test_cli_list_records(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, ["list", "--type", "all", "--limit", "10"])
        assert result.exit_code == 0

    def test_cli_list_records_json(self, temp_db: str) -> None:
        result = self.runner.invoke(police_app, ["list", "--type", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)


class TestPoliceMCPServer:
    def test_core_mcp_police_officer(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_officer(
            officer_badge="BCA-MCP-01",
            full_name="Nguyễn Văn Đại",
            rank="THIEU_TA",
            position="Trưởng Đội",
            unit_name="Công an Quận 1",
        )
        res = json.loads(raw)
        assert res["officer_badge"] == "BCA-MCP-01"

    def test_core_mcp_police_team(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_team(
            team_id="GR-MCP-01",
            team_name="Tổ 1",
            ward_commune="Phường 1",
            district_county="Quận 1",
            team_leader_name="Leader A",
        )
        res = json.loads(raw)
        assert res["team_id"] == "GR-MCP-01"

    def test_core_mcp_police_incident(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_incident(
            incident_id="INC-MCP-01",
            incident_type="PUBLIC_DISORDER",
            location="Loc",
            ward_commune="Ward",
            reported_by="Citizen",
            assigned_unit="Unit",
        )
        res = json.loads(raw)
        assert res["incident_id"] == "INC-MCP-01"

    def test_core_mcp_police_patrol(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_patrol(
            mission_id="PAT-MCP-01",
            patrol_type="JOINT_POLICE_GRASSROOTS",
            route_or_zone="Zone A",
            lead_officer_badge="BCA-001",
            grassroots_team_id="GR-001",
        )
        res = json.loads(raw)
        assert res["mission_id"] == "PAT-MCP-01"

    def test_core_mcp_police_residence(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_residence(
            check_id="RES-MCP-01",
            address="Addr",
            household_head_name="Head",
            inspecting_officer_badge="BCA-001",
        )
        res = json.loads(raw)
        assert res["check_id"] == "RES-MCP-01"

    def test_core_mcp_police_list(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_list(category="all", limit=10)
        res = json.loads(raw)
        assert "officers" in res

    def test_core_mcp_police_status(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_status()
        res = json.loads(raw)
        assert "active_duty_officers" in res

    def test_core_mcp_aliases(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert server._handle_mekong_police_officer == server._handle_police_officer
        assert server._handle_mekong_police_team == server._handle_police_team
        assert server._handle_mekong_police_incident == server._handle_police_incident
        assert server._handle_mekong_police_patrol == server._handle_police_patrol
        assert server._handle_mekong_police_residence == server._handle_police_residence
        assert server._handle_mekong_police_list == server._handle_police_list
        assert server._handle_mekong_police_status == server._handle_police_status

    def test_core_mcp_error_handling(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_police_officer(
            officer_badge="",
            full_name="Test",
            rank="INVALID",
            position="",
            unit_name="",
        )
        res = json.loads(raw)
        assert res["ok"] is False
        assert "error" in res


class TestPoliceScriptsMCPServer:
    def test_scripts_mcp_handlers_present(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected = [
            "mekong_police_officer",
            "mekong_police_team",
            "mekong_police_incident",
            "mekong_police_patrol",
            "mekong_police_residence",
            "mekong_police_list",
            "mekong_police_status",
            "police_officer",
            "police_team",
            "police_incident",
            "police_patrol",
            "police_residence",
            "police_list",
            "police_status",
        ]
        for name in expected:
            assert name in CORE_HANDLERS, f"Missing handler {name} in CORE_HANDLERS"

    def test_scripts_mcp_core_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        expected = [
            "mekong_police_officer",
            "mekong_police_team",
            "mekong_police_incident",
            "mekong_police_patrol",
            "mekong_police_residence",
            "mekong_police_list",
            "mekong_police_status",
        ]
        for name in expected:
            assert name in names, f"Missing {name} in CORE_TOOLS_SPEC"

    def test_scripts_mcp_handle_officer(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_officer

        raw = handle_police_officer({
            "officer_badge": "BCA-SCRIPTS-01",
            "full_name": "Lê Văn Tám",
            "rank": "DAI_UY",
            "position": "CSKV",
            "unit_name": "Công an Xã",
        })
        res = json.loads(raw)
        assert res["officer_badge"] == "BCA-SCRIPTS-01"

    def test_scripts_mcp_handle_team(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_team

        raw = handle_police_team({
            "team_id": "GR-SCRIPTS-01",
            "team_name": "Tổ 1",
            "ward_commune": "Xã 1",
            "district_county": "Huyện 1",
            "team_leader_name": "Tổ trưởng 1",
        })
        res = json.loads(raw)
        assert res["team_id"] == "GR-SCRIPTS-01"

    def test_scripts_mcp_handle_incident(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_incident

        raw = handle_police_incident({
            "incident_id": "INC-SCRIPTS-01",
            "incident_type": "PROPERTY_THEFT_BURGLARY",
            "location": "Loc",
            "ward_commune": "Ward",
            "reported_by": "Rep",
            "assigned_unit": "Unit",
        })
        res = json.loads(raw)
        assert res["incident_id"] == "INC-SCRIPTS-01"

    def test_scripts_mcp_handle_patrol(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_patrol

        raw = handle_police_patrol({
            "mission_id": "PAT-SCRIPTS-01",
            "patrol_type": "NIGHT_ROUTINE_SECURITY",
            "route_or_zone": "Route",
            "lead_officer_badge": "BCA-001",
            "grassroots_team_id": "GR-001",
        })
        res = json.loads(raw)
        assert res["mission_id"] == "PAT-SCRIPTS-01"

    def test_scripts_mcp_handle_residence(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_residence

        raw = handle_police_residence({
            "check_id": "RES-SCRIPTS-01",
            "address": "Addr",
            "household_head_name": "Head",
            "inspecting_officer_badge": "BCA-001",
        })
        res = json.loads(raw)
        assert res["check_id"] == "RES-SCRIPTS-01"

    def test_scripts_mcp_handle_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_list

        raw = handle_police_list({"category": "all", "limit": 10})
        res = json.loads(raw)
        assert "officers" in res

    def test_scripts_mcp_handle_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_status

        raw = handle_police_status({})
        res = json.loads(raw)
        assert "active_duty_officers" in res

    def test_scripts_mcp_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_police_officer

        raw = handle_police_officer({"officer_badge": ""})
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Police officer error" in res["error"]
