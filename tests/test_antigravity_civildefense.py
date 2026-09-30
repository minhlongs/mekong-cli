"""
Unit and integration tests for Vietnamese Civil Defense, Disaster Mitigation & Emergency Response Suite.
Governed by:
- Law on Civil Defense 2023 (Law No. 18/2023/QH15)
- Decree No. 02/2024/NĐ-CP (Implementation Guidelines for Law on Civil Defense)
- Prime Minister Decisions on National Civil Defense Strategy to 2030
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.civildefense_command import app as civildefense_app
from src.core.civildefense_engine import (
    VALID_ALERT_LEVELS,
    VALID_DISASTER_CATEGORIES,
    VALID_DRILL_TYPES,
    VALID_FORCE_TYPES,
    VALID_SHELTER_STATUS,
    VALID_SHELTER_TYPES,
    CivilDefenseEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_CIVILDEFENSE_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCivilDefenseEngine:
    def test_register_plan_valid(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        res = engine.register_plan(
            plan_id="PLAN-CD-HN-2026",
            plan_name="Kế hoạch Phòng thủ Dân sự Ứng phó Thảm họa Hóa chất Đô thị",
            category="CHEMICAL_TOXIC",
            jurisdiction_scope="Thành phố Hà Nội",
            commanding_body="UBND Thành phố Hà Nội",
            evacuation_capacity=50000,
            essential_supplies_days=30,
            approved_date="2026-02-15",
            status="ACTIVE",
        )
        assert res["plan_id"] == "PLAN-CD-HN-2026"
        assert res["category"] == "CHEMICAL_TOXIC"
        assert res["evacuation_capacity"] == 50000
        assert res["essential_supplies_days"] == 30

    def test_register_plan_duplicate(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        engine.register_plan(
            plan_id="PLAN-DUP",
            plan_name="Kế hoạch Trùng",
            category="WAR_CONFLICT",
            jurisdiction_scope="Quốc gia",
            commanding_body="Ban Chỉ đạo Quốc gia",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_plan(
                plan_id="PLAN-DUP",
                plan_name="Kế hoạch Trùng",
                category="WAR_CONFLICT",
                jurisdiction_scope="Quốc gia",
                commanding_body="Ban Chỉ đạo Quốc gia",
            )

    def test_register_plan_invalid_inputs(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_plan(
                plan_id="",
                plan_name="Tên",
                category="WAR_CONFLICT",
                jurisdiction_scope="",
                commanding_body="Cơ quan",
            )

        with pytest.raises(ValueError, match="Invalid category"):
            engine.register_plan(
                plan_id="PLAN-INV-CAT",
                plan_name="Tên",
                category="ASTEROID_IMPACT",
                jurisdiction_scope="Khu vực",
                commanding_body="Cơ quan",
            )

        with pytest.raises(ValueError, match="evacuation_capacity must be positive"):
            engine.register_plan(
                plan_id="PLAN-INV-CAP",
                plan_name="Tên",
                category="WAR_CONFLICT",
                jurisdiction_scope="Khu vực",
                commanding_body="Cơ quan",
                evacuation_capacity=0,
            )

        with pytest.raises(ValueError, match="essential_supplies_days must be positive"):
            engine.register_plan(
                plan_id="PLAN-INV-SUP",
                plan_name="Tên",
                category="WAR_CONFLICT",
                jurisdiction_scope="Khu vực",
                commanding_body="Cơ quan",
                essential_supplies_days=-5,
            )

    def test_issue_alert_valid(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        res = engine.issue_alert(
            alert_id="ALERT-CD-2026-001",
            disaster_category="CATACLYSMIC_GEOHAZARD",
            alert_level="LEVEL_2_PROVINCIAL",
            affected_region="Khu vực thượng nguồn sông Đà, tỉnh Lai Châu",
            declaring_authority="Chủ tịch UBND Tỉnh Lai Châu",
            evacuation_ordered=True,
            immediate_response_actions="Sơ tán khẩn cấp các bản vùng trũng, thiết lập trạm xá dã chiến",
            declared_date="2026-04-01",
        )
        assert res["alert_id"] == "ALERT-CD-2026-001"
        assert res["disaster_category"] == "CATACLYSMIC_GEOHAZARD"
        assert res["alert_level"] == "LEVEL_2_PROVINCIAL"
        assert res["evacuation_ordered"] is True

    def test_issue_alert_duplicate(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        engine.issue_alert(
            alert_id="ALERT-DUP",
            disaster_category="NUCLEAR_RADIATION",
            alert_level="LEVEL_3_REGIONAL",
            affected_region="Vùng biển X",
            declaring_authority="Bộ Quốc phòng",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_alert(
                alert_id="ALERT-DUP",
                disaster_category="NUCLEAR_RADIATION",
                alert_level="LEVEL_3_REGIONAL",
                affected_region="Vùng biển X",
                declaring_authority="Bộ Quốc phòng",
            )

    def test_issue_alert_invalid_inputs(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.issue_alert(
                alert_id="",
                disaster_category="NUCLEAR_RADIATION",
                alert_level="LEVEL_1_DISTRICT",
                affected_region="",
                declaring_authority="",
            )

        with pytest.raises(ValueError, match="Invalid disaster_category"):
            engine.issue_alert(
                alert_id="ALT-INV-CAT",
                disaster_category="ALIEN_INVASION",
                alert_level="LEVEL_1_DISTRICT",
                affected_region="Hà Nội",
                declaring_authority="Thủ tướng",
            )

        with pytest.raises(ValueError, match="Invalid alert_level"):
            engine.issue_alert(
                alert_id="ALT-INV-LVL",
                disaster_category="WAR_CONFLICT",
                alert_level="LEVEL_99_PLANETARY",
                affected_region="Hà Nội",
                declaring_authority="Thủ tướng",
            )

    def test_register_shelter_valid(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        res = engine.register_shelter(
            shelter_id="SHELTER-HN-001",
            shelter_name="Hầm Trú ẩn Ga Metro Ngầm Cát Linh",
            shelter_type="DUAL_USE_SUBWAY_BASEMENT",
            location_address="Ga Cát Linh, Quận Đống Đa, Hà Nội",
            capacity_persons=5000,
            air_filtration_equipped=True,
            cbrn_protection_level="LEVEL_2_HIGH",
            status="OPERATIONAL_READY",
            last_inspected_date="2026-03-01",
        )
        assert res["shelter_id"] == "SHELTER-HN-001"
        assert res["shelter_type"] == "DUAL_USE_SUBWAY_BASEMENT"
        assert res["capacity_persons"] == 5000
        assert res["air_filtration_equipped"] is True
        assert res["status"] == "OPERATIONAL_READY"

    def test_register_shelter_duplicate(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        engine.register_shelter(
            shelter_id="SHELTER-DUP",
            shelter_name="Hầm X",
            shelter_type="UNDERGROUND_BUNKER_SPECIALIZED",
            location_address="Địa chỉ",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_shelter(
                shelter_id="SHELTER-DUP",
                shelter_name="Hầm X",
                shelter_type="UNDERGROUND_BUNKER_SPECIALIZED",
                location_address="Địa chỉ",
            )

    def test_register_shelter_invalid_inputs(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_shelter(
                shelter_id="",
                shelter_name="",
                shelter_type="UNDERGROUND_BUNKER_SPECIALIZED",
                location_address="",
            )

        with pytest.raises(ValueError, match="Invalid shelter_type"):
            engine.register_shelter(
                shelter_id="SH-INV-T",
                shelter_name="Hầm",
                shelter_type="CARDBOARD_BOX",
                location_address="Đường A",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_shelter(
                shelter_id="SH-INV-S",
                shelter_name="Hầm",
                shelter_type="HARDENED_PUBLIC_SHELTER",
                location_address="Đường A",
                status="UNDERWATER_SUBMERGED",
            )

        with pytest.raises(ValueError, match="capacity_persons must be positive"):
            engine.register_shelter(
                shelter_id="SH-INV-C",
                shelter_name="Hầm",
                shelter_type="HARDENED_PUBLIC_SHELTER",
                location_address="Đường A",
                capacity_persons=0,
            )

    def test_deploy_force_valid(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        res = engine.deploy_force(
            deployment_id="FORCE-HN-01",
            unit_name="Tiểu đoàn Phòng hóa 78, Bộ Tư lệnh Hóa học",
            force_type="SPECIALIZED_ENGINEER_CORPS",
            stationed_base="Sơn Tây, Hà Nội",
            personnel_count=120,
            specialized_vehicles_count=18,
            readiness_hours=0.5,
            contact_officer="Thượng tá Nguyễn Hữu Dũng",
        )
        assert res["deployment_id"] == "FORCE-HN-01"
        assert res["unit_name"] == "Tiểu đoàn Phòng hóa 78, Bộ Tư lệnh Hóa học"
        assert res["personnel_count"] == 120
        assert res["specialized_vehicles_count"] == 18
        assert res["readiness_hours"] == 0.5

    def test_deploy_force_duplicate(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        engine.deploy_force(
            deployment_id="FORCE-DUP",
            unit_name="Đơn vị X",
            force_type="MILITARY_CORE_UNIT",
            stationed_base="Căn cứ Y",
            contact_officer="Chỉ huy Z",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.deploy_force(
                deployment_id="FORCE-DUP",
                unit_name="Đơn vị X",
                force_type="MILITARY_CORE_UNIT",
                stationed_base="Căn cứ Y",
                contact_officer="Chỉ huy Z",
            )

    def test_deploy_force_invalid_inputs(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.deploy_force(
                deployment_id="",
                unit_name="",
                force_type="MILITARY_CORE_UNIT",
                stationed_base="",
                contact_officer="",
            )

        with pytest.raises(ValueError, match="Invalid force_type"):
            engine.deploy_force(
                deployment_id="F-INV-T",
                unit_name="Đơn vị",
                force_type="SPACE_FLEET",
                stationed_base="Căn cứ",
                contact_officer="Chỉ huy",
            )

        with pytest.raises(ValueError, match="personnel_count must be positive"):
            engine.deploy_force(
                deployment_id="F-INV-P",
                unit_name="Đơn vị",
                force_type="MILITARY_CORE_UNIT",
                stationed_base="Căn cứ",
                contact_officer="Chỉ huy",
                personnel_count=0,
            )

        with pytest.raises(ValueError, match="specialized_vehicles_count cannot be negative"):
            engine.deploy_force(
                deployment_id="F-INV-V",
                unit_name="Đơn vị",
                force_type="MILITARY_CORE_UNIT",
                stationed_base="Căn cứ",
                contact_officer="Chỉ huy",
                specialized_vehicles_count=-2,
            )

        with pytest.raises(ValueError, match="readiness_hours cannot be negative"):
            engine.deploy_force(
                deployment_id="F-INV-R",
                unit_name="Đơn vị",
                force_type="MILITARY_CORE_UNIT",
                stationed_base="Căn cứ",
                contact_officer="Chỉ huy",
                readiness_hours=-1.0,
            )

    def test_log_drill_valid(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        res = engine.log_drill(
            drill_id="DRILL-2026-01",
            drill_code="PTDS-HN-26",
            drill_name="Diễn tập Thực binh Phòng thủ Dân sự Ứng phó Sự cố Phóng xạ Đô thị",
            drill_type="HAZMAT_CBRN_DRILL",
            organizing_agency="Bộ Tư lệnh Thủ đô Hà Nội",
            participants_count=650,
            duration_hours=12.0,
            drill_date="2026-03-20",
            evaluation_score=92.5,
            deficiencies_notes="Đạt xuất sắc tiêu tẩy thực địa và khoanh vùng kiểm soát",
        )
        assert res["drill_id"] == "DRILL-2026-01"
        assert res["drill_code"] == "PTDS-HN-26"
        assert res["participants_count"] == 650
        assert res["evaluation_score"] == 92.5

    def test_log_drill_duplicate(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        engine.log_drill(
            drill_id="DRILL-DUP",
            drill_code="DT-01",
            drill_name="Diễn tập Trùng",
            drill_type="TABLETOP_COMMAND_DRILL",
            organizing_agency="Cơ quan A",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_drill(
                drill_id="DRILL-DUP",
                drill_code="DT-01",
                drill_name="Diễn tập Trùng",
                drill_type="TABLETOP_COMMAND_DRILL",
                organizing_agency="Cơ quan A",
            )

    def test_log_drill_invalid_inputs(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.log_drill(
                drill_id="",
                drill_code="",
                drill_name="",
                drill_type="COMBINED_FULL_SCALE",
                organizing_agency="",
            )

        with pytest.raises(ValueError, match="Invalid drill_type"):
            engine.log_drill(
                drill_id="DR-INV-T",
                drill_code="D-01",
                drill_name="Tên",
                drill_type="VIDEO_GAME_SIMULATION",
                organizing_agency="Cơ quan",
            )

        with pytest.raises(ValueError, match="participants_count must be positive"):
            engine.log_drill(
                drill_id="DR-INV-P",
                drill_code="D-01",
                drill_name="Tên",
                drill_type="COMBINED_FULL_SCALE",
                organizing_agency="Cơ quan",
                participants_count=0,
            )

        with pytest.raises(ValueError, match="duration_hours must be positive"):
            engine.log_drill(
                drill_id="DR-INV-D",
                drill_code="D-01",
                drill_name="Tên",
                drill_type="COMBINED_FULL_SCALE",
                organizing_agency="Cơ quan",
                duration_hours=-1.0,
            )

        with pytest.raises(ValueError, match="evaluation_score must be between 0.0 and 100.0"):
            engine.log_drill(
                drill_id="DR-INV-S",
                drill_code="D-01",
                drill_name="Tên",
                drill_type="COMBINED_FULL_SCALE",
                organizing_agency="Cơ quan",
                evaluation_score=105.0,
            )

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        # Empty telemetry
        empty_tel = engine.get_telemetry_status()
        assert empty_tel["active_civil_plans"] == 0
        assert empty_tel["total_evacuation_capacity"] == 0
        assert empty_tel["operational_ready_shelters"] == 0
        assert empty_tel["mobilized_force_units"] == 0

        # Seed records
        engine.register_plan(
            plan_id="PLAN-SEED-01",
            plan_name="Kế hoạch A",
            category="WAR_CONFLICT",
            jurisdiction_scope="Tỉnh A",
            commanding_body="UBND A",
            evacuation_capacity=20000,
        )
        engine.issue_alert(
            alert_id="ALT-SEED-01",
            disaster_category="BIOLOGICAL_PANDEMIC",
            alert_level="LEVEL_1_DISTRICT",
            affected_region="Huyện B",
            declaring_authority="Chủ tịch Huyện B",
        )
        engine.register_shelter(
            shelter_id="SH-SEED-01",
            shelter_name="Hầm Trú C",
            shelter_type="HARDENED_PUBLIC_SHELTER",
            location_address="Địa chỉ C",
            capacity_persons=1500,
        )
        engine.deploy_force(
            deployment_id="F-SEED-01",
            unit_name="Đội D",
            force_type="COMMUNITY_SHOCK_TEAM",
            stationed_base="Xã D",
            personnel_count=40,
            specialized_vehicles_count=4,
            contact_officer="Đội trưởng E",
        )
        engine.log_drill(
            drill_id="DR-SEED-01",
            drill_code="DT-01",
            drill_name="Diễn tập F",
            drill_type="FIELD_EVACUATION_DRILL",
            organizing_agency="Cơ quan F",
            participants_count=300,
            evaluation_score=88.0,
        )

        telemetry = engine.get_telemetry_status()
        assert telemetry["active_civil_plans"] == 1
        assert telemetry["total_evacuation_capacity"] == 20000
        assert telemetry["active_alerts_by_level"]["LEVEL_1_DISTRICT"] == 1
        assert telemetry["operational_ready_shelters"] == 1
        assert telemetry["total_shelter_capacity_persons"] == 1500
        assert telemetry["mobilized_force_units"] == 1
        assert telemetry["total_mobilized_personnel"] == 40
        assert telemetry["total_specialized_vehicles"] == 4
        assert telemetry["total_emergency_drills"] == 1
        assert telemetry["average_drill_score"] == 88.0

        all_rec = engine.list_records(record_type="all")
        assert len(all_rec["plans"]) == 1
        assert len(all_rec["alerts"]) == 1
        assert len(all_rec["shelters"]) == 1
        assert len(all_rec["forces"]) == 1
        assert len(all_rec["drills"]) == 1

        shelters_only = engine.list_records(record_type="shelters")
        assert len(shelters_only["shelters"]) == 1
        assert "plans" not in shelters_only


class TestCivilDefenseCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(civildefense_app, [])
        assert result.exit_code == 0
        assert "Active Civil Defense Plans" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(civildefense_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "active_civil_plans" in data
        assert "operational_ready_shelters" in data

    def test_cli_status_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(civildefense_app, ["status"])
        assert res_text.exit_code == 0
        assert "Chỉ số Sẵn sàng Phòng thủ Dân sự" in res_text.output

        res_json = runner.invoke(civildefense_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "mobilized_force_units" in data

    def test_cli_plan_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "plan",
                "--id", "PLAN-CLI-01",
                "--name", "Kế hoạch Phòng thủ Dân sự TP Đà Nẵng",
                "--category", "WAR_CONFLICT",
                "--scope", "Thành phố Đà Nẵng",
                "--body", "UBND Thành phố Đà Nẵng",
                "--capacity", "35000",
                "--supplies", "21",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plan_id"] == "PLAN-CLI-01"
        assert data["evacuation_capacity"] == 35000

    def test_cli_plan_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "plan",
                "--id", "PLAN-ERR",
                "--name", "Kế hoạch",
                "--category", "INVALID_CATEGORY",
                "--scope", "Phạm vi",
                "--body", "Cơ quan",
            ],
        )
        assert result.exit_code != 0

    def test_cli_alert_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "alert",
                "--id", "ALT-CLI-01",
                "--category", "CATACLYSMIC_GEOHAZARD",
                "--level", "LEVEL_3_REGIONAL",
                "--region", "Ven biển Miền Trung",
                "--authority", "Ban Chỉ đạo Quốc gia PTDS",
                "--evacuation",
                "--actions", "Kích hoạt phương án phòng chống bão cấp 16",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["alert_id"] == "ALT-CLI-01"
        assert data["alert_level"] == "LEVEL_3_REGIONAL"
        assert data["evacuation_ordered"] is True

    def test_cli_alert_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "alert",
                "--id", "ALT-ERR",
                "--category", "CATACLYSMIC_GEOHAZARD",
                "--level", "INVALID_LEVEL",
                "--region", "Khu vực",
                "--authority", "Cơ quan",
                "--actions", "Hành động",
            ],
        )
        assert result.exit_code != 0

    def test_cli_shelter_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "shelter",
                "--id", "SH-CLI-01",
                "--name", "Hầm Trú ẩn Ngầm Quảng trường Hòa Bình",
                "--type", "UNDERGROUND_BUNKER_SPECIALIZED",
                "--address", "Trung tâm TP Hòa Bình",
                "--capacity", "3000",
                "--filtration",
                "--cbrn", "LEVEL_1",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["shelter_id"] == "SH-CLI-01"
        assert data["capacity_persons"] == 3000
        assert data["air_filtration_equipped"] is True

    def test_cli_shelter_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "shelter",
                "--id", "SH-ERR",
                "--name", "Hầm",
                "--type", "INVALID_SHELTER_TYPE",
                "--address", "Địa chỉ",
            ],
        )
        assert result.exit_code != 0

    def test_cli_force_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "force",
                "--id", "FORCE-CLI-01",
                "--unit", "Lữ đoàn Công binh 249",
                "--type", "SPECIALIZED_ENGINEER_CORPS",
                "--base", "Việt Trì, Phú Thọ",
                "--personnel", "200",
                "--vehicles", "25",
                "--readiness", "0.75",
                "--officer", "Đại tá Lê Văn Cường",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deployment_id"] == "FORCE-CLI-01"
        assert data["personnel_count"] == 200
        assert data["readiness_hours"] == 0.75

    def test_cli_force_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "force",
                "--id", "F-ERR",
                "--unit", "Đơn vị",
                "--type", "INVALID_FORCE",
                "--base", "Căn cứ",
                "--officer", "Chỉ huy",
            ],
        )
        assert result.exit_code != 0

    def test_cli_drill_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "drill",
                "--id", "DR-CLI-01",
                "--code", "PTDS-DN-26",
                "--name", "Diễn tập Sơ tán Nhân dân Vùng Ngập lụt Khẩn cấp",
                "--type", "FIELD_EVACUATION_DRILL",
                "--agency", "BCH Quân sự TP Đà Nẵng",
                "--participants", "450",
                "--duration", "10.0",
                "--score", "90.0",
                "--notes", "Triển khai đúng phương án",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["drill_id"] == "DR-CLI-01"
        assert data["evaluation_score"] == 90.0

    def test_cli_drill_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            civildefense_app,
            [
                "drill",
                "--id", "DR-ERR",
                "--code", "DT-01",
                "--name", "Diễn tập",
                "--type", "INVALID_DRILL",
                "--agency", "Cơ quan",
            ],
        )
        assert result.exit_code != 0

    def test_cli_list_command_all_and_filtered(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            civildefense_app,
            [
                "plan",
                "--id", "PLAN-L-01",
                "--name", "Kế hoạch L",
                "--category", "WAR_CONFLICT",
                "--scope", "Phạm vi L",
                "--body", "Cơ quan L",
                "--json",
            ],
        )
        res_all = runner.invoke(civildefense_app, ["list", "--json"])
        assert res_all.exit_code == 0
        data_all = json.loads(res_all.output)
        assert "plans" in data_all
        assert len(data_all["plans"]) == 1

        res_plans = runner.invoke(civildefense_app, ["list", "--type", "plans", "--json"])
        assert res_plans.exit_code == 0
        data_p = json.loads(res_plans.output)
        assert "plans" in data_p
        assert "shelters" not in data_p

        res_console = runner.invoke(civildefense_app, ["list"])
        assert res_console.exit_code == 0
        assert "PLANS" in res_console.output


class TestCivilDefenseMCP:
    def test_mcp_standalone_plan(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_plan

        res_str = handle_civildefense_plan({
            "plan_id": "PLAN-MCP-01",
            "plan_name": "Kế hoạch PTDS Cấp Quốc gia",
            "category": "NUCLEAR_RADIATION",
            "jurisdiction_scope": "Toàn quốc",
            "commanding_body": "Ban Chỉ đạo Quốc gia PTDS",
            "evacuation_capacity": 100000,
            "essential_supplies_days": 60,
        })
        res = json.loads(res_str)
        assert res["plan_id"] == "PLAN-MCP-01"
        assert res["category"] == "NUCLEAR_RADIATION"

    def test_mcp_standalone_alert(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_alert

        res_str = handle_civildefense_alert({
            "alert_id": "ALT-MCP-01",
            "disaster_category": "BIOLOGICAL_PANDEMIC",
            "alert_level": "LEVEL_4_NATIONAL",
            "affected_region": "Toàn quốc",
            "declaring_authority": "Thủ tướng Chính phủ",
            "evacuation_ordered": False,
            "immediate_response_actions": "Kích hoạt tình trạng khẩn cấp y tế",
        })
        res = json.loads(res_str)
        assert res["alert_id"] == "ALT-MCP-01"
        assert res["alert_level"] == "LEVEL_4_NATIONAL"

    def test_mcp_standalone_shelter(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_shelter

        res_str = handle_civildefense_shelter({
            "shelter_id": "SH-MCP-01",
            "shelter_name": "Hầm Trú ẩn Ngầm Trung tâm Hội nghị Quốc gia",
            "shelter_type": "UNDERGROUND_BUNKER_SPECIALIZED",
            "location_address": "Mễ Trì, Nam Từ Liêm, Hà Nội",
            "capacity_persons": 8000,
            "air_filtration_equipped": True,
            "cbrn_protection_level": "MAXIMUM",
        })
        res = json.loads(res_str)
        assert res["shelter_id"] == "SH-MCP-01"
        assert res["capacity_persons"] == 8000

    def test_mcp_standalone_force(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_force

        res_str = handle_civildefense_force({
            "deployment_id": "F-MCP-01",
            "unit_name": "Cục Cứu hộ - Cứu nạn, Bộ Tổng Tham mưu",
            "force_type": "MILITARY_CORE_UNIT",
            "stationed_base": "Hà Nội",
            "personnel_count": 500,
            "specialized_vehicles_count": 50,
            "readiness_hours": 0.25,
            "contact_officer": "Trung tướng X",
        })
        res = json.loads(res_str)
        assert res["deployment_id"] == "F-MCP-01"
        assert res["personnel_count"] == 500

    def test_mcp_standalone_drill(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_drill

        res_str = handle_civildefense_drill({
            "drill_id": "DR-MCP-01",
            "drill_code": "PTDS-QG-26",
            "drill_name": "Diễn tập Phòng thủ Dân sự Toàn quốc 2026",
            "drill_type": "COMBINED_FULL_SCALE",
            "organizing_agency": "Chính phủ & Bộ Quốc phòng",
            "participants_count": 5000,
            "duration_hours": 24.0,
            "evaluation_score": 96.0,
            "deficiencies_notes": "Hoàn thành xuất sắc mọi mục tiêu",
        })
        res = json.loads(res_str)
        assert res["drill_id"] == "DR-MCP-01"
        assert res["evaluation_score"] == 96.0

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_civildefense_list, handle_civildefense_status

        list_str = handle_civildefense_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "plans" in lst
        assert "shelters" in lst

        stat_str = handle_civildefense_status({})
        stat = json.loads(stat_str)
        assert "active_civil_plans" in stat
        assert "operational_ready_shelters" in stat

    def test_mcp_standalone_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_civildefense_alert,
            handle_civildefense_drill,
            handle_civildefense_force,
            handle_civildefense_plan,
            handle_civildefense_shelter,
        )

        err_p = json.loads(handle_civildefense_plan({}))
        assert err_p["ok"] is False
        assert "error" in err_p

        err_a = json.loads(handle_civildefense_alert({}))
        assert err_a["ok"] is False

        err_s = json.loads(handle_civildefense_shelter({}))
        assert err_s["ok"] is False

        err_f = json.loads(handle_civildefense_force({}))
        assert err_f["ok"] is False

        err_d = json.loads(handle_civildefense_drill({}))
        assert err_d["ok"] is False

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        p_str = server._handle_civildefense_plan(
            plan_id="PLAN-CORE-01",
            plan_name="Kế hoạch Core",
            category="WAR_CONFLICT",
            jurisdiction_scope="Tỉnh Core",
            commanding_body="UBND Core",
        )
        p_data = json.loads(p_str)
        assert p_data["plan_id"] == "PLAN-CORE-01"

        a_str = server._handle_civildefense_alert(
            alert_id="ALT-CORE-01",
            disaster_category="CHEMICAL_TOXIC",
            alert_level="LEVEL_1_DISTRICT",
            affected_region="Huyện Core",
            declaring_authority="Chủ tịch Huyện",
        )
        a_data = json.loads(a_str)
        assert a_data["alert_id"] == "ALT-CORE-01"

        s_str = server._handle_civildefense_shelter(
            shelter_id="SH-CORE-01",
            shelter_name="Hầm Core",
            shelter_type="HARDENED_PUBLIC_SHELTER",
            location_address="Đường Core",
        )
        s_data = json.loads(s_str)
        assert s_data["shelter_id"] == "SH-CORE-01"

        f_str = server._handle_civildefense_force(
            deployment_id="F-CORE-01",
            unit_name="Đơn vị Core",
            force_type="POLICE_RESCUE_UNIT",
            stationed_base="Trạm Core",
            contact_officer="Chỉ huy Core",
        )
        f_data = json.loads(f_str)
        assert f_data["deployment_id"] == "F-CORE-01"

        d_str = server._handle_civildefense_drill(
            drill_id="DR-CORE-01",
            drill_code="DT-CORE",
            drill_name="Diễn tập Core",
            drill_type="TABLETOP_COMMAND_DRILL",
            organizing_agency="Cơ quan Core",
        )
        d_data = json.loads(d_str)
        assert d_data["drill_id"] == "DR-CORE-01"

        lst_str = server._handle_civildefense_list(category="all", limit=5)
        lst_data = json.loads(lst_str)
        assert "plans" in lst_data

        stat_str = server._handle_civildefense_status()
        stat_data = json.loads(stat_str)
        assert stat_data["active_civil_plans"] >= 1

        # Check aliases
        assert server._handle_mekong_civildefense_plan == server._handle_civildefense_plan
        assert server._handle_mekong_civildefense_alert == server._handle_civildefense_alert
        assert server._handle_mekong_civildefense_shelter == server._handle_civildefense_shelter
        assert server._handle_mekong_civildefense_force == server._handle_civildefense_force
        assert server._handle_mekong_civildefense_drill == server._handle_civildefense_drill
        assert server._handle_mekong_civildefense_list == server._handle_civildefense_list
        assert server._handle_mekong_civildefense_status == server._handle_civildefense_status

    def test_mcp_spec_and_handlers_parity(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_civildefense_plan",
            "mekong_civildefense_alert",
            "mekong_civildefense_shelter",
            "mekong_civildefense_force",
            "mekong_civildefense_drill",
            "mekong_civildefense_list",
            "mekong_civildefense_status",
        ]
        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for name in expected_tools:
            assert name in tool_names, f"Tool {name} missing in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"Tool {name} missing in CORE_HANDLERS"
            short_name = name.replace("mekong_", "")
            assert short_name in CORE_HANDLERS, f"Short tool {short_name} missing in CORE_HANDLERS"


class TestCivilDefenseEdgeCases:
    def test_all_disaster_categories(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        for i, cat in enumerate(VALID_DISASTER_CATEGORIES):
            res = engine.register_plan(
                plan_id=f"PLAN-CAT-{i}",
                plan_name=f"Kế hoạch thảm họa {cat}",
                category=cat,
                jurisdiction_scope="Tỉnh X",
                commanding_body="UBND X",
            )
            assert res["category"] == cat

    def test_all_alert_levels(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        for i, lvl in enumerate(VALID_ALERT_LEVELS):
            res = engine.issue_alert(
                alert_id=f"ALT-LVL-{i}",
                disaster_category="WAR_CONFLICT",
                alert_level=lvl,
                affected_region=f"Vùng {i}",
                declaring_authority="Cơ quan Y",
            )
            assert res["alert_level"] == lvl

    def test_all_shelter_types(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        for i, st in enumerate(VALID_SHELTER_TYPES):
            res = engine.register_shelter(
                shelter_id=f"SH-TYPE-{i}",
                shelter_name=f"Hầm loại {st}",
                shelter_type=st,
                location_address="Địa chỉ Z",
            )
            assert res["shelter_type"] == st

    def test_all_force_types(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        for i, ft in enumerate(VALID_FORCE_TYPES):
            res = engine.deploy_force(
                deployment_id=f"F-TYPE-{i}",
                unit_name=f"Đơn vị {ft}",
                force_type=ft,
                stationed_base="Căn cứ M",
                contact_officer="Chỉ huy N",
            )
            assert res["force_type"] == ft

    def test_all_drill_types(self, temp_db: str) -> None:
        engine = CivilDefenseEngine(db_path=temp_db)
        for i, dt in enumerate(VALID_DRILL_TYPES):
            res = engine.log_drill(
                drill_id=f"DR-TYPE-{i}",
                drill_code=f"DT-{i}",
                drill_name=f"Diễn tập {dt}",
                drill_type=dt,
                organizing_agency="Cơ quan P",
            )
            assert res["drill_type"] == dt
