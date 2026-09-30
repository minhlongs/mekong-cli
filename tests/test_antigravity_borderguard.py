"""
Unit and integration tests for Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite.
Governed by:
- Law on Vietnam Border Defense 2020 (Law No. 66/2020/QH14)
- Law on National Border 2003 (Law No. 06/2003/QH11)
- Decree No. 34/2014/NĐ-CP (Land Border Areas Regulations)
- Decree No. 106/2021/NĐ-CP (Guiding Implementation of Law on Vietnam Border Defense)
- Circular No. 163/2021/TT-BQP (Border Management and Territorial Protection)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.borderguard_command import app as borderguard_app
from src.core.borderguard_engine import (
    VALID_BORDER_SEGMENTS,
    VALID_GATE_STATUSES,
    VALID_GATE_TIERS,
    VALID_INCIDENT_TYPES,
    VALID_MARKER_INTEGRITY,
    VALID_MARKER_TYPES,
    VALID_PATROL_TYPES,
    VALID_SEVERITY_LEVELS,
    VALID_ZONE_TYPES,
    BorderGuardEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_BORDERGUARD_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestBorderGuardEngine:
    def test_register_marker_valid(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        res = engine.register_marker(
            marker_id="BM-VN-LA-450",
            marker_number="450",
            border_segment="VIETNAM_LAOS",
            managing_post="Đồn Biên phòng Cửa khẩu Quốc tế Cầu Treo",
            province="Hà Tĩnh",
            latitude=18.384,
            longitude=105.161,
            marker_type="MAIN_MONUMENT_GRANITE",
            elevation_meters=732.5,
            last_inspected_date="2026-03-15",
            physical_integrity="INTACT",
        )
        assert res["marker_id"] == "BM-VN-LA-450"
        assert res["marker_number"] == "450"
        assert res["border_segment"] == "VIETNAM_LAOS"
        assert res["physical_integrity"] == "INTACT"
        assert res["elevation_meters"] == 732.5

    def test_register_marker_duplicate(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        engine.register_marker(
            marker_id="BM-DUP",
            marker_number="100",
            border_segment="VIETNAM_CHINA",
            managing_post="Đồn Đồng Đăng",
            province="Lạng Sơn",
            latitude=21.9,
            longitude=106.7,
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_marker(
                marker_id="BM-DUP",
                marker_number="100",
                border_segment="VIETNAM_CHINA",
                managing_post="Đồn Đồng Đăng",
                province="Lạng Sơn",
                latitude=21.9,
                longitude=106.7,
            )

    def test_register_marker_invalid_inputs(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_marker(
                marker_id="",
                marker_number="101",
                border_segment="VIETNAM_CHINA",
                managing_post="Đồn A",
                province="Quảng Ninh",
                latitude=21.0,
                longitude=107.0,
            )

    def test_register_marker_invalid_enums(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid border_segment"):
            engine.register_marker(
                marker_id="BM-INV-SEG",
                marker_number="999",
                border_segment="VIETNAM_PACIFIC",
                managing_post="Đồn B",
                province="Tỉnh C",
                latitude=15.0,
                longitude=108.0,
            )

        with pytest.raises(ValueError, match="Invalid marker_type"):
            engine.register_marker(
                marker_id="BM-INV-TYPE",
                marker_number="999",
                border_segment="VIETNAM_LAOS",
                managing_post="Đồn B",
                province="Tỉnh C",
                latitude=15.0,
                longitude=108.0,
                marker_type="WOODEN_PLANK",
            )

        with pytest.raises(ValueError, match="Invalid physical_integrity"):
            engine.register_marker(
                marker_id="BM-INV-INT",
                marker_number="999",
                border_segment="VIETNAM_LAOS",
                managing_post="Đồn B",
                province="Tỉnh C",
                latitude=15.0,
                longitude=108.0,
                physical_integrity="DESTROYED_UNKNOWN",
            )

    def test_issue_border_permit_valid(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        res = engine.issue_border_permit(
            permit_id="PERMIT-2026-001",
            applicant_name="Trần Văn Khang",
            citizen_id_or_passport="038091002345",
            zone_type="BORDER_BELT",
            purpose="Khảo sát địa chất thủy văn công trình kè suối biên giới",
            issuing_post="Đồn Biên phòng Cửa khẩu Quốc tế Cha Lo",
            nationality="VNM",
            valid_from="2026-04-01",
            valid_until="2026-04-30",
        )
        assert res["permit_id"] == "PERMIT-2026-001"
        assert res["applicant_name"] == "Trần Văn Khang"
        assert res["zone_type"] == "BORDER_BELT"
        assert res["status"] == "ACTIVE"

    def test_issue_border_permit_duplicate(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        engine.issue_border_permit(
            permit_id="PERMIT-DUP",
            applicant_name="Nguyễn Văn A",
            citizen_id_or_passport="001090123456",
            zone_type="RESTRICTED_ZONE",
            purpose="Công tác",
            issuing_post="Đồn Mèo Vạc",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_border_permit(
                permit_id="PERMIT-DUP",
                applicant_name="Nguyễn Văn A",
                citizen_id_or_passport="001090123456",
                zone_type="RESTRICTED_ZONE",
                purpose="Công tác",
                issuing_post="Đồn Mèo Vạc",
            )

    def test_issue_border_permit_invalid_inputs(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.issue_border_permit(
                permit_id="",
                applicant_name="",
                citizen_id_or_passport="",
                zone_type="BORDER_BELT",
                purpose="",
                issuing_post="",
            )

        with pytest.raises(ValueError, match="Invalid zone_type"):
            engine.issue_border_permit(
                permit_id="PERMIT-INV",
                applicant_name="Lê Văn B",
                citizen_id_or_passport="001090111222",
                zone_type="COASTAL_BEACH",
                purpose="Du lịch",
                issuing_post="Đồn Đảo",
            )

    def test_log_patrol_mission_valid(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        # Register a marker first to test date update
        engine.register_marker(
            marker_id="BM-PAT-01",
            marker_number="12",
            border_segment="VIETNAM_LAOS",
            managing_post="Đồn Tây Trang",
            province="Điện Biên",
            latitude=21.2,
            longitude=102.9,
            last_inspected_date="2025-01-01",
        )

        res = engine.log_patrol_mission(
            mission_id="PATROL-2026-001",
            patrol_type="ROUTINE_FOOT_PATROL",
            commanding_post="Đồn Biên phòng Cửa khẩu Tây Trang",
            patrol_leader="Đại úy Hoàng Văn Sơn",
            summary_notes="Tuần tra bảo vệ đoạn biên giới mốc 12 đến mốc 15, đường biên thông thoáng",
            team_size=6,
            covered_markers=["BM-PAT-01"],
            duration_hours=5.5,
            infringements_detected=0,
            patrol_date="2026-04-10",
        )
        assert res["mission_id"] == "PATROL-2026-001"
        assert res["team_size"] == 6
        assert res["duration_hours"] == 5.5
        assert "BM-PAT-01" in res["covered_markers"]

        # Verify marker inspection date updated
        records = engine.list_records(record_type="markers")
        assert records["markers"][0]["last_inspected_date"] == "2026-04-10"

    def test_log_patrol_mission_duplicate(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        engine.log_patrol_mission(
            mission_id="PATROL-DUP",
            patrol_type="MOTORIZED_RECON",
            commanding_post="Đồn Mộc Bài",
            patrol_leader="Trung tá A",
            summary_notes="Ghi chú",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_patrol_mission(
                mission_id="PATROL-DUP",
                patrol_type="MOTORIZED_RECON",
                commanding_post="Đồn Mộc Bài",
                patrol_leader="Trung tá A",
                summary_notes="Ghi chú",
            )

    def test_log_patrol_mission_invalid_inputs(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.log_patrol_mission(
                mission_id="",
                patrol_type="ROUTINE_FOOT_PATROL",
                commanding_post="",
                patrol_leader="",
                summary_notes="",
            )

        with pytest.raises(ValueError, match="Invalid patrol_type"):
            engine.log_patrol_mission(
                mission_id="PAT-INV",
                patrol_type="SPACE_ORBITAL_PATROL",
                commanding_post="Đồn X",
                patrol_leader="Chỉ huy Y",
                summary_notes="Ghi chú",
            )

        with pytest.raises(ValueError, match="team_size must be positive"):
            engine.log_patrol_mission(
                mission_id="PAT-INV-TEAM",
                patrol_type="ROUTINE_FOOT_PATROL",
                commanding_post="Đồn X",
                patrol_leader="Chỉ huy Y",
                summary_notes="Ghi chú",
                team_size=0,
            )

        with pytest.raises(ValueError, match="duration_hours must be positive"):
            engine.log_patrol_mission(
                mission_id="PAT-INV-DUR",
                patrol_type="ROUTINE_FOOT_PATROL",
                commanding_post="Đồn X",
                patrol_leader="Chỉ huy Y",
                summary_notes="Ghi chú",
                duration_hours=-2.5,
            )

    def test_register_border_gate_valid(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        res = engine.register_border_gate(
            gate_id="GATE-HUU-NGHI",
            gate_name="Cửa khẩu Quốc tế Hữu Nghị",
            gate_tier="INTERNATIONAL",
            border_country="CHINA",
            controlling_station="Trạm Biên phòng Cửa khẩu Quốc tế Hữu Nghị",
            daily_transit_capacity=5000,
            status="NORMAL_OPERATION",
        )
        assert res["gate_id"] == "GATE-HUU-NGHI"
        assert res["gate_tier"] == "INTERNATIONAL"
        assert res["border_country"] == "CHINA"
        assert res["status"] == "NORMAL_OPERATION"

    def test_register_border_gate_duplicate(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        engine.register_border_gate(
            gate_id="GATE-DUP",
            gate_name="Cửa khẩu X",
            gate_tier="BILATERAL_MAIN",
            border_country="LAOS",
            controlling_station="Trạm X",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_border_gate(
                gate_id="GATE-DUP",
                gate_name="Cửa khẩu X",
                gate_tier="BILATERAL_MAIN",
                border_country="LAOS",
                controlling_station="Trạm X",
            )

    def test_register_border_gate_invalid_inputs(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_border_gate(
                gate_id="",
                gate_name="",
                gate_tier="INTERNATIONAL",
                border_country="CHINA",
                controlling_station="",
            )

        with pytest.raises(ValueError, match="Invalid gate_tier"):
            engine.register_border_gate(
                gate_id="GATE-INV",
                gate_name="Tên",
                gate_tier="INTERGALACTIC",
                border_country="CHINA",
                controlling_station="Trạm",
            )

        with pytest.raises(ValueError, match="border_country must be CHINA, LAOS, or CAMBODIA"):
            engine.register_border_gate(
                gate_id="GATE-INV-C",
                gate_name="Tên",
                gate_tier="INTERNATIONAL",
                border_country="THAILAND",
                controlling_station="Trạm",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_border_gate(
                gate_id="GATE-INV-S",
                gate_name="Tên",
                gate_tier="INTERNATIONAL",
                border_country="LAOS",
                controlling_station="Trạm",
                status="OFFLINE_MAINTENANCE",
            )

    def test_report_border_incident_valid(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        res = engine.report_border_incident(
            incident_id="INC-BG-2026-001",
            incident_type="ILLEGAL_ENTRY_EXIT",
            severity_level="MAJOR",
            location_description="Khu vực mốc 1088 tuyến biên giới Lạng Sơn",
            handling_post="Đồn Biên phòng Tân Thanh",
            involved_persons_count=4,
            contraband_value_vnd=150000000.0,
            bilateral_talks_held=True,
            outcome_status="UNDER_INVESTIGATION",
            incident_date="2026-04-12",
        )
        assert res["incident_id"] == "INC-BG-2026-001"
        assert res["incident_type"] == "ILLEGAL_ENTRY_EXIT"
        assert res["severity_level"] == "MAJOR"
        assert res["contraband_value_vnd"] == 150000000.0
        assert res["bilateral_talks_held"] is True

    def test_report_border_incident_duplicate(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        engine.report_border_incident(
            incident_id="INC-DUP",
            incident_type="SMUGGLING_CONTRABAND",
            severity_level="MODERATE",
            location_description="Khu vực bờ suối",
            handling_post="Đồn A",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.report_border_incident(
                incident_id="INC-DUP",
                incident_type="SMUGGLING_CONTRABAND",
                severity_level="MODERATE",
                location_description="Khu vực bờ suối",
                handling_post="Đồn A",
            )

    def test_report_border_incident_invalid_inputs(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.report_border_incident(
                incident_id="",
                incident_type="SMUGGLING_CONTRABAND",
                severity_level="MODERATE",
                location_description="",
                handling_post="",
            )

        with pytest.raises(ValueError, match="Invalid incident_type"):
            engine.report_border_incident(
                incident_id="INC-INV-T",
                incident_type="PIRACY_HIGH_SEAS",
                severity_level="MODERATE",
                location_description="Bờ sông",
                handling_post="Đồn A",
            )

        with pytest.raises(ValueError, match="Invalid severity_level"):
            engine.report_border_incident(
                incident_id="INC-INV-S",
                incident_type="SMUGGLING_CONTRABAND",
                severity_level="EXTREME",
                location_description="Bờ sông",
                handling_post="Đồn A",
            )

        with pytest.raises(ValueError, match="contraband_value_vnd cannot be negative"):
            engine.report_border_incident(
                incident_id="INC-INV-V",
                incident_type="SMUGGLING_CONTRABAND",
                severity_level="MODERATE",
                location_description="Bờ sông",
                handling_post="Đồn A",
                contraband_value_vnd=-1000.0,
            )

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        # Empty telemetry
        empty_tel = engine.get_telemetry_status()
        assert empty_tel["total_border_markers"] == 0
        assert empty_tel["total_patrol_missions"] == 0
        assert empty_tel["total_contraband_seized_vnd"] == 0.0

        # Seed records
        engine.register_marker(
            marker_id="BM-SEED-01",
            marker_number="1",
            border_segment="VIETNAM_LAOS",
            managing_post="Đồn A",
            province="Quảng Bình",
            latitude=17.5,
            longitude=106.1,
        )
        engine.register_marker(
            marker_id="BM-SEED-02",
            marker_number="2",
            border_segment="VIETNAM_CAMBODIA",
            managing_post="Đồn B",
            province="Tây Ninh",
            latitude=11.3,
            longitude=106.0,
        )
        engine.issue_border_permit(
            permit_id="PERM-SEED-01",
            applicant_name="Nguyễn Văn B",
            citizen_id_or_passport="001122334455",
            zone_type="BORDER_BELT",
            purpose="Khảo sát",
            issuing_post="Đồn A",
        )
        engine.log_patrol_mission(
            mission_id="PAT-SEED-01",
            patrol_type="ROUTINE_FOOT_PATROL",
            commanding_post="Đồn A",
            patrol_leader="Đại úy C",
            summary_notes="Ghi chú tuần tra",
            duration_hours=4.0,
            infringements_detected=1,
        )
        engine.register_border_gate(
            gate_id="GATE-SEED-01",
            gate_name="Cửa khẩu Mộc Bài",
            gate_tier="INTERNATIONAL",
            border_country="CAMBODIA",
            controlling_station="Trạm Mộc Bài",
        )
        engine.report_border_incident(
            incident_id="INC-SEED-01",
            incident_type="SMUGGLING_CONTRABAND",
            severity_level="MAJOR",
            location_description="Đường mòn gần mốc 2",
            handling_post="Đồn B",
            contraband_value_vnd=50000000.0,
        )

        telemetry = engine.get_telemetry_status()
        assert telemetry["total_border_markers"] == 2
        assert telemetry["markers_by_segment"]["VIETNAM_LAOS"] == 1
        assert telemetry["markers_by_segment"]["VIETNAM_CAMBODIA"] == 1
        assert telemetry["active_border_permits"] == 1
        assert telemetry["total_patrol_missions"] == 1
        assert telemetry["total_patrol_hours"] == 4.0
        assert telemetry["infringements_detected_patrols"] == 1
        assert telemetry["total_border_gates"] == 1
        assert telemetry["total_border_incidents"] == 1
        assert telemetry["total_contraband_seized_vnd"] == 50000000.0

        all_rec = engine.list_records(record_type="all")
        assert len(all_rec["markers"]) == 2
        assert len(all_rec["permits"]) == 1
        assert len(all_rec["patrols"]) == 1
        assert len(all_rec["gates"]) == 1
        assert len(all_rec["incidents"]) == 1

        markers_only = engine.list_records(record_type="markers")
        assert len(markers_only["markers"]) == 2
        assert "permits" not in markers_only


class TestBorderGuardCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(borderguard_app, [])
        assert result.exit_code == 0
        assert "Total National Border Markers" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(borderguard_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_border_markers" in data
        assert "active_border_permits" in data

    def test_cli_status_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(borderguard_app, ["status"])
        assert res_text.exit_code == 0
        assert "Chỉ số Thực thi Chủ quyền" in res_text.output

        res_json = runner.invoke(borderguard_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_patrol_missions" in data

    def test_cli_marker_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "marker",
                "--id", "BM-CLI-01",
                "--number", "92",
                "--segment", "VIETNAM_LAOS",
                "--post", "Đồn A Roàng",
                "--province", "Thừa Thiên Huế",
                "--lat", "16.1",
                "--lon", "107.3",
                "--type", "MAIN_MONUMENT_GRANITE",
                "--elev", "850.0",
                "--integrity", "INTACT",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["marker_id"] == "BM-CLI-01"
        assert data["marker_number"] == "92"

    def test_cli_marker_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "marker",
                "--id", "BM-ERR",
                "--number", "93",
                "--segment", "INVALID_SEGMENT",
                "--post", "Đồn X",
                "--province", "Tỉnh Y",
                "--lat", "16.0",
                "--lon", "107.0",
            ],
        )
        assert result.exit_code != 0

    def test_cli_permit_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "permit",
                "--id", "PERM-CLI-01",
                "--name", "Hoàng Kim Sơn",
                "--id-doc", "040089012345",
                "--zone", "BORDER_BELT",
                "--purpose", "Khảo sát vành đai",
                "--post", "Đồn Na Mèo",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["permit_id"] == "PERM-CLI-01"
        assert data["applicant_name"] == "Hoàng Kim Sơn"

    def test_cli_permit_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "permit",
                "--id", "PERM-ERR",
                "--name", "Ai Đó",
                "--id-doc", "123",
                "--zone", "UNKNOWN_ZONE",
                "--purpose", "Mục đích",
                "--post", "Đồn",
            ],
        )
        assert result.exit_code != 0

    def test_cli_patrol_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "patrol",
                "--id", "PAT-CLI-01",
                "--type", "ROUTINE_FOOT_PATROL",
                "--post", "Đồn Na Mèo",
                "--leader", "Thượng úy B",
                "--notes", "Tuần tra biên giới an toàn",
                "--team", "5",
                "--duration", "6.0",
                "--infringements", "0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mission_id"] == "PAT-CLI-01"
        assert data["duration_hours"] == 6.0

    def test_cli_patrol_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "patrol",
                "--id", "PAT-ERR",
                "--type", "INVALID_TYPE",
                "--post", "Đồn",
                "--leader", "Chỉ huy",
                "--notes", "Ghi chú",
            ],
        )
        assert result.exit_code != 0

    def test_cli_gate_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "gate",
                "--id", "GATE-CLI-01",
                "--name", "Cửa khẩu Na Mèo",
                "--tier", "INTERNATIONAL",
                "--country", "LAOS",
                "--station", "Trạm Na Mèo",
                "--capacity", "2000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["gate_id"] == "GATE-CLI-01"
        assert data["border_country"] == "LAOS"

    def test_cli_gate_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "gate",
                "--id", "GATE-ERR",
                "--name", "Cửa khẩu",
                "--tier", "INTERNATIONAL",
                "--country", "RUSSIA",
                "--station", "Trạm",
            ],
        )
        assert result.exit_code != 0

    def test_cli_incident_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "incident",
                "--id", "INC-CLI-01",
                "--type", "ILLEGAL_ENTRY_EXIT",
                "--severity", "MAJOR",
                "--location", "Khu vực mốc 92",
                "--post", "Đồn A Roàng",
                "--persons", "2",
                "--contraband", "20000000",
                "--talks",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["incident_id"] == "INC-CLI-01"
        assert data["contraband_value_vnd"] == 20000000.0
        assert data["bilateral_talks_held"] is True

    def test_cli_incident_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            borderguard_app,
            [
                "incident",
                "--id", "INC-ERR",
                "--type", "INVALID_INCIDENT",
                "--severity", "MAJOR",
                "--location", "Vị trí",
                "--post", "Đồn",
            ],
        )
        assert result.exit_code != 0

    def test_cli_list_command_all_and_filtered(self, temp_db: str) -> None:
        runner = CliRunner()
        # Seed via CLI
        runner.invoke(
            borderguard_app,
            [
                "marker",
                "--id", "BM-LIST-01",
                "--number", "10",
                "--segment", "VIETNAM_LAOS",
                "--post", "Đồn X",
                "--province", "Nghệ An",
                "--lat", "19.0",
                "--lon", "104.5",
                "--json",
            ],
        )
        res_all = runner.invoke(borderguard_app, ["list", "--json"])
        assert res_all.exit_code == 0
        data_all = json.loads(res_all.output)
        assert "markers" in data_all
        assert len(data_all["markers"]) == 1

        res_markers = runner.invoke(borderguard_app, ["list", "--type", "markers", "--json"])
        assert res_markers.exit_code == 0
        data_m = json.loads(res_markers.output)
        assert "markers" in data_m
        assert "permits" not in data_m

        res_console = runner.invoke(borderguard_app, ["list"])
        assert res_console.exit_code == 0
        assert "MARKERS" in res_console.output


class TestBorderGuardMCP:
    def test_mcp_standalone_marker(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_marker

        res_str = handle_borderguard_marker({
            "marker_id": "BM-MCP-01",
            "marker_number": "301",
            "border_segment": "VIETNAM_CHINA",
            "managing_post": "Đồn Trà Cổ",
            "province": "Quảng Ninh",
            "latitude": 21.5,
            "longitude": 107.9,
            "marker_type": "MAIN_MONUMENT_GRANITE",
            "elevation_meters": 12.0,
            "physical_integrity": "INTACT",
        })
        res = json.loads(res_str)
        assert res["marker_id"] == "BM-MCP-01"
        assert res["marker_number"] == "301"

    def test_mcp_standalone_permit(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_permit

        res_str = handle_borderguard_permit({
            "permit_id": "PERM-MCP-01",
            "applicant_name": "Phạm Quốc Toản",
            "citizen_id_or_passport": "031085001234",
            "zone_type": "BORDER_BELT",
            "purpose": "Thi công công trình viễn thông biên giới",
            "issuing_post": "Đồn Trà Cổ",
        })
        res = json.loads(res_str)
        assert res["permit_id"] == "PERM-MCP-01"
        assert res["status"] == "ACTIVE"

    def test_mcp_standalone_patrol(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_patrol

        res_str = handle_borderguard_patrol({
            "mission_id": "PAT-MCP-01",
            "patrol_type": "RIVERINE_MARITIME_SORTIE",
            "commanding_post": "Hải đội 2 Biên phòng Quảng Ninh",
            "patrol_leader": "Thiếu tá D",
            "summary_notes": "Tuần tra cửa sông Bắc Luân",
            "team_size": 8,
            "duration_hours": 6.5,
        })
        res = json.loads(res_str)
        assert res["mission_id"] == "PAT-MCP-01"
        assert res["duration_hours"] == 6.5

    def test_mcp_standalone_gate(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_gate

        res_str = handle_borderguard_gate({
            "gate_id": "GATE-MCP-01",
            "gate_name": "Cửa khẩu Quốc tế Móng Cái",
            "gate_tier": "INTERNATIONAL",
            "border_country": "CHINA",
            "controlling_station": "Trạm Biên phòng Cửa khẩu Quốc tế Móng Cái",
            "daily_transit_capacity": 8000,
        })
        res = json.loads(res_str)
        assert res["gate_id"] == "GATE-MCP-01"
        assert res["border_country"] == "CHINA"

    def test_mcp_standalone_incident(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_incident

        res_str = handle_borderguard_incident({
            "incident_id": "INC-MCP-01",
            "incident_type": "SMUGGLING_CONTRABAND",
            "severity_level": "CRITICAL",
            "location_description": "Vùng biển ven bờ biên giới Trà Cổ",
            "handling_post": "Hải đội 2",
            "involved_persons_count": 3,
            "contraband_value_vnd": 500000000.0,
            "bilateral_talks_held": False,
        })
        res = json.loads(res_str)
        assert res["incident_id"] == "INC-MCP-01"
        assert res["contraband_value_vnd"] == 500000000.0

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_borderguard_list, handle_borderguard_status

        list_str = handle_borderguard_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "markers" in lst
        assert "patrols" in lst

        stat_str = handle_borderguard_status({})
        stat = json.loads(stat_str)
        assert "total_border_markers" in stat
        assert "total_patrol_missions" in stat

    def test_mcp_standalone_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_borderguard_gate,
            handle_borderguard_incident,
            handle_borderguard_marker,
            handle_borderguard_patrol,
            handle_borderguard_permit,
        )

        err_m = json.loads(handle_borderguard_marker({}))
        assert err_m["ok"] is False
        assert "error" in err_m

        err_p = json.loads(handle_borderguard_permit({}))
        assert err_p["ok"] is False

        err_pat = json.loads(handle_borderguard_patrol({}))
        assert err_pat["ok"] is False

        err_g = json.loads(handle_borderguard_gate({}))
        assert err_g["ok"] is False

        err_i = json.loads(handle_borderguard_incident({}))
        assert err_i["ok"] is False

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        m_str = server._handle_borderguard_marker(
            marker_id="BM-CORE-01",
            marker_number="1000",
            border_segment="VIETNAM_CHINA",
            managing_post="Đồn P",
            province="Lạng Sơn",
            latitude=22.0,
            longitude=106.8,
        )
        m_data = json.loads(m_str)
        assert m_data["marker_id"] == "BM-CORE-01"

        perm_str = server._handle_borderguard_permit(
            permit_id="PERM-CORE-01",
            applicant_name="Vũ Hải",
            citizen_id_or_passport="001090998877",
            zone_type="RESTRICTED_ZONE",
            purpose="Nhiệm vụ đặc biệt",
            issuing_post="Đồn P",
        )
        perm_data = json.loads(perm_str)
        assert perm_data["permit_id"] == "PERM-CORE-01"

        pat_str = server._handle_borderguard_patrol(
            mission_id="PAT-CORE-01",
            patrol_type="UAV_AERIAL_SURVEILLANCE",
            commanding_post="Đồn P",
            patrol_leader="Thiếu tá E",
            summary_notes="Giám sát đường biên bằng UAV",
        )
        pat_data = json.loads(pat_str)
        assert pat_data["mission_id"] == "PAT-CORE-01"

        g_str = server._handle_borderguard_gate(
            gate_id="GATE-CORE-01",
            gate_name="Cửa khẩu Cốc Nam",
            gate_tier="SUB_BORDER_GATE",
            border_country="CHINA",
            controlling_station="Trạm Cốc Nam",
        )
        g_data = json.loads(g_str)
        assert g_data["gate_id"] == "GATE-CORE-01"

        inc_str = server._handle_borderguard_incident(
            incident_id="INC-CORE-01",
            incident_type="BORDER_LINE_ENCROACHMENT",
            severity_level="MODERATE",
            location_description="Khu vực mốc 1000",
            handling_post="Đồn P",
        )
        inc_data = json.loads(inc_str)
        assert inc_data["incident_id"] == "INC-CORE-01"

        lst_str = server._handle_borderguard_list(category="all", limit=5)
        lst_data = json.loads(lst_str)
        assert "markers" in lst_data

        stat_str = server._handle_borderguard_status()
        stat_data = json.loads(stat_str)
        assert stat_data["total_border_markers"] >= 1

        # Check aliases
        assert server._handle_mekong_borderguard_marker == server._handle_borderguard_marker
        assert server._handle_mekong_borderguard_permit == server._handle_borderguard_permit
        assert server._handle_mekong_borderguard_patrol == server._handle_borderguard_patrol
        assert server._handle_mekong_borderguard_gate == server._handle_borderguard_gate
        assert server._handle_mekong_borderguard_incident == server._handle_borderguard_incident
        assert server._handle_mekong_borderguard_list == server._handle_borderguard_list
        assert server._handle_mekong_borderguard_status == server._handle_borderguard_status

    def test_mcp_spec_and_handlers_parity(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_borderguard_marker",
            "mekong_borderguard_permit",
            "mekong_borderguard_patrol",
            "mekong_borderguard_gate",
            "mekong_borderguard_incident",
            "mekong_borderguard_list",
            "mekong_borderguard_status",
        ]
        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for name in expected_tools:
            assert name in tool_names, f"Tool {name} missing in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"Tool {name} missing in CORE_HANDLERS"
            short_name = name.replace("mekong_", "")
            assert short_name in CORE_HANDLERS, f"Short tool {short_name} missing in CORE_HANDLERS"


class TestBorderGuardEdgeCases:
    def test_all_border_segments(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        for i, seg in enumerate(VALID_BORDER_SEGMENTS):
            res = engine.register_marker(
                marker_id=f"BM-SEG-{i}",
                marker_number=str(i + 1),
                border_segment=seg,
                managing_post="Đồn X",
                province="Tỉnh Y",
                latitude=15.0,
                longitude=105.0,
            )
            assert res["border_segment"] == seg

    def test_all_marker_types(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        for i, mt in enumerate(VALID_MARKER_TYPES):
            res = engine.register_marker(
                marker_id=f"BM-TYPE-{i}",
                marker_number=str(10 + i),
                border_segment="VIETNAM_LAOS",
                managing_post="Đồn X",
                province="Tỉnh Y",
                latitude=15.0,
                longitude=105.0,
                marker_type=mt,
            )
            assert res["marker_type"] == mt

    def test_all_gate_tiers(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        for i, tier in enumerate(VALID_GATE_TIERS):
            res = engine.register_border_gate(
                gate_id=f"GATE-TIER-{i}",
                gate_name=f"Cửa khẩu {tier}",
                gate_tier=tier,
                border_country="LAOS",
                controlling_station="Trạm X",
            )
            assert res["gate_tier"] == tier

    def test_all_incident_types(self, temp_db: str) -> None:
        engine = BorderGuardEngine(db_path=temp_db)
        for i, it in enumerate(VALID_INCIDENT_TYPES):
            res = engine.report_border_incident(
                incident_id=f"INC-TYPE-{i}",
                incident_type=it,
                severity_level="MODERATE",
                location_description="Vị trí X",
                handling_post="Đồn Y",
            )
            assert res["incident_type"] == it
