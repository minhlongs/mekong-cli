"""
Unit and integration tests for Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite.
Governed by:
- Law on Anti-Terrorism 2013 (Law No. 28/2013/QH13)
- Decree No. 07/2014/NĐ-CP (Command, coordination, and counter-terrorism emergency response)
- Decree No. 37/2009/NĐ-CP (Target Protection List: Special Class, Class I, Class II vital national security targets)
- Prime Minister Decision No. 42/2015/QĐ-TTg (Security and Civil Defense of Vital Targets)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.antiterrorism_command import app as antiterrorism_app
from src.core.antiterrorism_engine import (
    VALID_PROTECTION_LEVELS,
    VALID_TACTICAL_SCENARIOS,
    VALID_TARGET_CATEGORIES,
    VALID_TARGET_STATUSES,
    VALID_THREAT_LEVELS,
    VALID_THREAT_STATUSES,
    VALID_THREAT_TYPES,
    AntiTerrorismEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_ANTITERRORISM_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestAntiTerrorismEngine:
    def test_register_target_valid(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        res = engine.register_target(
            target_id="TGT-BCA-01",
            target_name="Trụ sở Bộ Công an",
            target_category="POLITICAL_HEADQUARTERS",
            protection_level="SPECIAL_CLASS",
            guard_force="Bộ Tư lệnh Cảnh vệ K01",
            location_address="47 Phạm Văn Đồng, Cầu Giấy, Hà Nội",
            security_perimeter_meters=200.0,
            status="SECURE",
        )
        assert res["target_id"] == "TGT-BCA-01"
        assert res["target_name"] == "Trụ sở Bộ Công an"
        assert res["protection_level"] == "SPECIAL_CLASS"
        assert res["status"] == "SECURE"
        assert res["security_perimeter_meters"] == 200.0

    def test_register_target_duplicate(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-DUP",
            target_name="Mục tiêu A",
            target_category="CRITICAL_INFRASTRUCTURE",
            protection_level="CLASS_I",
            guard_force="Cảnh sát Cơ động K02",
            location_address="Hà Nội",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_target(
                target_id="TGT-DUP",
                target_name="Mục tiêu A",
                target_category="CRITICAL_INFRASTRUCTURE",
                protection_level="CLASS_I",
                guard_force="Cảnh sát Cơ động K02",
                location_address="Hà Nội",
            )

    def test_register_target_invalid_inputs(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_target(
                target_id="",
                target_name="Tên mục tiêu",
                target_category="POLITICAL_HEADQUARTERS",
                protection_level="SPECIAL_CLASS",
                guard_force="K01",
                location_address="Hà Nội",
            )

        with pytest.raises(ValueError, match="Invalid target_category"):
            engine.register_target(
                target_id="TGT-INV-CAT",
                target_name="Tên mục tiêu",
                target_category="INVALID_CATEGORY",
                protection_level="SPECIAL_CLASS",
                guard_force="K01",
                location_address="Hà Nội",
            )

        with pytest.raises(ValueError, match="Invalid protection_level"):
            engine.register_target(
                target_id="TGT-INV-LVL",
                target_name="Tên mục tiêu",
                target_category="POLITICAL_HEADQUARTERS",
                protection_level="ULTRA_SECRET",
                guard_force="K01",
                location_address="Hà Nội",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_target(
                target_id="TGT-INV-STAT",
                target_name="Tên mục tiêu",
                target_category="POLITICAL_HEADQUARTERS",
                protection_level="SPECIAL_CLASS",
                guard_force="K01",
                location_address="Hà Nội",
                status="UNKNOWN_STATUS",
            )

        with pytest.raises(ValueError, match="must be positive"):
            engine.register_target(
                target_id="TGT-NEG-PERIM",
                target_name="Tên mục tiêu",
                target_category="POLITICAL_HEADQUARTERS",
                protection_level="SPECIAL_CLASS",
                guard_force="K01",
                location_address="Hà Nội",
                security_perimeter_meters=-50.0,
            )

    def test_issue_threat_alert_valid(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-THREAT-01",
            target_name="Nhà máy Thủy điện Hòa Bình",
            target_category="CRITICAL_INFRASTRUCTURE",
            protection_level="SPECIAL_CLASS",
            guard_force="Trung đoàn Cảnh sát Bảo vệ Mục tiêu",
            location_address="Hòa Bình",
        )
        alert = engine.issue_threat_alert(
            alert_id="ALERT-2026-001",
            threat_source="Cục An ninh mạng & PCTP sử dụng CNC (A05)",
            threat_type="CYBER_TERRORISM",
            threat_level="SEVERE_ORANGE",
            intelligence_summary="Phát hiện dấu hiệu tấn công mạng có chủ đích vào hệ thống SCADA điều khiển đập thủy điện.",
            affected_targets=["TGT-THREAT-01"],
            issued_at="2026-03-30",
        )
        assert alert["alert_id"] == "ALERT-2026-001"
        assert alert["threat_level"] == "SEVERE_ORANGE"
        assert alert["status"] == "ACTIVE"
        assert "TGT-THREAT-01" in alert["affected_targets"]

        # Check target status was updated to HEIGHTENED_ALERT
        records = engine.list_records(record_type="targets")
        tgt = [t for t in records["targets"] if t["target_id"] == "TGT-THREAT-01"][0]
        assert tgt["status"] == "HEIGHTENED_ALERT"

    def test_issue_threat_alert_duplicate(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.issue_threat_alert(
            alert_id="ALERT-DUP",
            threat_source="Tổng cục II - Bộ Quốc phòng",
            threat_type="ARMED_ATTACK",
            threat_level="SUBSTANTIAL_YELLOW",
            intelligence_summary="Báo cáo tình báo khu vực biên giới",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_threat_alert(
                alert_id="ALERT-DUP",
                threat_source="Tổng cục II - Bộ Quốc phòng",
                threat_type="ARMED_ATTACK",
                threat_level="SUBSTANTIAL_YELLOW",
                intelligence_summary="Báo cáo tình báo khu vực biên giới",
            )

    def test_issue_threat_alert_invalid_inputs(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.issue_threat_alert(
                alert_id="",
                threat_source="Nguồn tình báo",
                threat_type="ARMED_ATTACK",
                threat_level="SUBSTANTIAL_YELLOW",
                intelligence_summary="Tóm tắt tình báo",
            )

        with pytest.raises(ValueError, match="Invalid threat_type"):
            engine.issue_threat_alert(
                alert_id="ALERT-INV-TYPE",
                threat_source="Nguồn tình báo",
                threat_type="INVALID_TYPE",
                threat_level="SUBSTANTIAL_YELLOW",
                intelligence_summary="Tóm tắt tình báo",
            )

        with pytest.raises(ValueError, match="Invalid threat_level"):
            engine.issue_threat_alert(
                alert_id="ALERT-INV-LVL",
                threat_source="Nguồn tình báo",
                threat_type="ARMED_ATTACK",
                threat_level="INVALID_LEVEL",
                intelligence_summary="Tóm tắt tình báo",
            )

    def test_register_emergency_plan_valid(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-PLAN-01",
            target_name="Sân bay Quốc tế Nội Bài",
            target_category="CRITICAL_INFRASTRUCTURE",
            protection_level="SPECIAL_CLASS",
            guard_force="Công an Cửa khẩu Sân bay Nội Bài",
            location_address="Sóc Sơn, Hà Nội",
        )
        plan = engine.register_emergency_plan(
            plan_id="PLAN-CT-001",
            target_id="TGT-PLAN-01",
            plan_name="Phương án chống cướp tàu bay và giải cứu con tin Nội Bài",
            tactical_scenario="HOSTAGE_RESCUE",
            lead_command_agency="Bộ Tư lệnh Cảnh sát Cơ động (K02)",
            participating_units=["Trung đoàn CSCĐ Đặc nhiệm số 1", "A08", "Cục Cảnh sát PCCC & CNCH"],
            last_drill_date="2025-11-20",
        )
        assert plan["plan_id"] == "PLAN-CT-001"
        assert plan["tactical_scenario"] == "HOSTAGE_RESCUE"
        assert len(plan["participating_units"]) == 3
        assert plan["readiness_status"] == "READY"

    def test_register_emergency_plan_nonexistent_target(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="does not exist"):
            engine.register_emergency_plan(
                plan_id="PLAN-NONEXISTENT",
                target_id="TGT-MISSING",
                plan_name="Kế hoạch bảo vệ",
                tactical_scenario="BOMB_DISPOSAL_EOD",
                lead_command_agency="Binh chủng Công binh",
            )

    def test_register_emergency_plan_duplicate(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-PLAN-DUP",
            target_name="Kho bạc Nhà nước Trung ương",
            target_category="FINANCIAL_COMMUNICATION_HUB",
            protection_level="CLASS_I",
            guard_force="Cảnh sát Bảo vệ",
            location_address="Hà Nội",
        )
        engine.register_emergency_plan(
            plan_id="PLAN-DUP-01",
            target_id="TGT-PLAN-DUP",
            plan_name="Phương án bảo vệ kho tiền",
            tactical_scenario="ARMED_ATTACK" if "ARMED_ATTACK" in VALID_TACTICAL_SCENARIOS else "HOSTAGE_RESCUE",
            lead_command_agency="K02",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_emergency_plan(
                plan_id="PLAN-DUP-01",
                target_id="TGT-PLAN-DUP",
                plan_name="Phương án bảo vệ kho tiền",
                tactical_scenario="HOSTAGE_RESCUE",
                lead_command_agency="K02",
            )

    def test_register_emergency_plan_invalid_scenario(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-SCENARIO-TEST",
            target_name="Tổng Lãnh sự quán Hoa Kỳ",
            target_category="DIPLOMATIC_MISSION",
            protection_level="CLASS_I",
            guard_force="K01",
            location_address="TP. Hồ Chí Minh",
        )
        with pytest.raises(ValueError, match="Invalid tactical_scenario"):
            engine.register_emergency_plan(
                plan_id="PLAN-INV-SCEN",
                target_id="TGT-SCENARIO-TEST",
                plan_name="Phương án tác chiến",
                tactical_scenario="SPACE_INVASION",
                lead_command_agency="K02",
            )

    def test_designate_terrorist_entity_valid(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        entity = engine.designate_terrorist_entity(
            entity_id="TERR-ORG-01",
            entity_name="Tổ chức Khủng bố Quốc tế X",
            entity_type="ORGANIZATION",
            designation_decision="Thông báo số 05/TB-BCA của Bộ Công an",
            designation_date="2026-01-15",
            aliases=["Mạng lưới X", "Nhánh X Đông Nam Á"],
        )
        assert entity["entity_id"] == "TERR-ORG-01"
        assert entity["entity_type"] == "ORGANIZATION"
        assert entity["asset_freeze_mandate"] is True
        assert len(entity["aliases"]) == 2

    def test_designate_terrorist_entity_duplicate(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.designate_terrorist_entity(
            entity_id="TERR-DUP",
            entity_name="Tổ chức Y",
            entity_type="ORGANIZATION",
            designation_decision="QĐ-BCA-01",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.designate_terrorist_entity(
                entity_id="TERR-DUP",
                entity_name="Tổ chức Y",
                entity_type="ORGANIZATION",
                designation_decision="QĐ-BCA-01",
            )

    def test_designate_terrorist_entity_invalid_inputs(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.designate_terrorist_entity(
                entity_id="",
                entity_name="Tên cá nhân",
                entity_type="INDIVIDUAL",
                designation_decision="QĐ-01",
            )

        with pytest.raises(ValueError, match="must be ORGANIZATION or INDIVIDUAL"):
            engine.designate_terrorist_entity(
                entity_id="TERR-INV-TYPE",
                entity_name="Tên nhóm",
                entity_type="SYNDICATE",
                designation_decision="QĐ-01",
            )

    def test_record_asset_freeze_valid(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.designate_terrorist_entity(
            entity_id="TERR-FREEZE-01",
            entity_name="Tập hợp Phản động Vũ trang Z",
            entity_type="ORGANIZATION",
            designation_decision="Quyết định BCA số 99/QĐ-BCA",
        )
        freeze_res = engine.record_asset_freeze(
            entity_id="TERR-FREEZE-01",
            accounts_count=5,
            frozen_amount_vnd=15_000_000_000.0,
        )
        assert freeze_res["entity_id"] == "TERR-FREEZE-01"
        assert freeze_res["total_frozen_accounts"] == 5
        assert freeze_res["total_frozen_funds_vnd"] == 15_000_000_000.0

        # Incremental freeze
        freeze_res2 = engine.record_asset_freeze(
            entity_id="TERR-FREEZE-01",
            accounts_count=2,
            frozen_amount_vnd=5_000_000_000.0,
        )
        assert freeze_res2["total_frozen_accounts"] == 7
        assert freeze_res2["total_frozen_funds_vnd"] == 20_000_000_000.0

    def test_record_asset_freeze_nonexistent_entity(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="not found"):
            engine.record_asset_freeze(
                entity_id="TERR-MISSING",
                accounts_count=1,
                frozen_amount_vnd=1_000_000.0,
            )

    def test_record_asset_freeze_invalid_amounts(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.designate_terrorist_entity(
            entity_id="TERR-INV-AMT",
            entity_name="Đối tượng K",
            entity_type="INDIVIDUAL",
            designation_decision="QĐ-123",
        )
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.record_asset_freeze(
                entity_id="TERR-INV-AMT",
                accounts_count=-1,
                frozen_amount_vnd=500_000.0,
            )
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.record_asset_freeze(
                entity_id="TERR-INV-AMT",
                accounts_count=1,
                frozen_amount_vnd=-500_000.0,
            )

    def test_log_tactical_operation_valid_and_status_resolution(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-OP-01",
            target_name="Trung tâm Truyền hình Quốc gia VTV",
            target_category="FINANCIAL_COMMUNICATION_HUB",
            protection_level="CLASS_I",
            guard_force="Cảnh sát Bảo vệ",
            location_address="43 Nguyễn Chí Thanh, Hà Nội",
        )
        engine.issue_threat_alert(
            alert_id="ALERT-OP-01",
            threat_source="Trinh sát nội địa A02",
            threat_type="HOSTAGE_HIJACKING",
            threat_level="CRITICAL_RED",
            intelligence_summary="Nhóm vũ trang đột nhập khống chế trường quay",
            affected_targets=["TGT-OP-01"],
        )

        # Log tactical operation
        op_res = engine.log_tactical_operation(
            operation_id="OP-RESOLVE-01",
            alert_id="ALERT-OP-01",
            target_id="TGT-OP-01",
            tactical_action="Đột kích giải thoát toàn bộ con tin và khống chế đối tượng",
            commanding_officer="Đại tá Nguyễn Hữu Hiệp",
            hostages_rescued=18,
            suspects_neutralized=3,
            outcome_status="RESOLVED_SUCCESS",
            operation_date="2026-03-30",
        )
        assert op_res["operation_id"] == "OP-RESOLVE-01"
        assert op_res["hostages_rescued"] == 18
        assert op_res["suspects_neutralized"] == 3
        assert op_res["outcome_status"] == "RESOLVED_SUCCESS"

        # Verify alert and target statuses updated
        records = engine.list_records(record_type="all")
        alert = [a for a in records["alerts"] if a["alert_id"] == "ALERT-OP-01"][0]
        assert alert["status"] == "CONTAINED"
        target = [t for t in records["targets"] if t["target_id"] == "TGT-OP-01"][0]
        assert target["status"] == "SECURE"

    def test_log_tactical_operation_duplicate(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-OP-DUP",
            target_name="Cơ sở trọng yếu",
            target_category="MILITARY_DEFENSE_INSTALLATION",
            protection_level="SPECIAL_CLASS",
            guard_force="Vệ binh",
            location_address="Hà Nội",
        )
        engine.issue_threat_alert(
            alert_id="ALERT-OP-DUP",
            threat_source="Nguồn X",
            threat_type="ARMED_ATTACK",
            threat_level="SUBSTANTIAL_YELLOW",
            intelligence_summary="Tóm tắt",
        )
        engine.log_tactical_operation(
            operation_id="OP-DUP",
            alert_id="ALERT-OP-DUP",
            target_id="TGT-OP-DUP",
            tactical_action="Tuần tra ngăn chặn",
            commanding_officer="Chỉ huy trưởng",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.log_tactical_operation(
                operation_id="OP-DUP",
                alert_id="ALERT-OP-DUP",
                target_id="TGT-OP-DUP",
                tactical_action="Tuần tra ngăn chặn",
                commanding_officer="Chỉ huy trưởng",
            )

    def test_log_tactical_operation_invalid_inputs(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.log_tactical_operation(
                operation_id="",
                alert_id="ALERT-01",
                target_id="TGT-01",
                tactical_action="Tác chiến",
                commanding_officer="Sĩ quan",
            )

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        telemetry_empty = engine.get_telemetry_status()
        assert telemetry_empty["total_protected_targets"] == 0
        assert telemetry_empty["total_frozen_funds_vnd"] == 0.0

        # Seed data
        engine.register_target(
            target_id="TGT-SEED-01",
            target_name="Trung tâm Dữ liệu Quốc gia",
            target_category="CRITICAL_INFRASTRUCTURE",
            protection_level="SPECIAL_CLASS",
            guard_force="Cục An ninh mạng (A05)",
            location_address="Hà Nội",
        )
        engine.issue_threat_alert(
            alert_id="ALERT-SEED-01",
            threat_source="A05",
            threat_type="CYBER_TERRORISM",
            threat_level="SUBSTANTIAL_YELLOW",
            intelligence_summary="Quét cổng mạng bất thường",
        )
        engine.register_emergency_plan(
            plan_id="PLAN-SEED-01",
            target_id="TGT-SEED-01",
            plan_name="Phương án ứng cứu mạng",
            tactical_scenario="CYBER_COUNTERMEASURE",
            lead_command_agency="A05",
        )
        engine.designate_terrorist_entity(
            entity_id="TERR-SEED-01",
            entity_name="Hacker Group Shadow Terror",
            entity_type="ORGANIZATION",
            designation_decision="TB-01/BCA",
        )
        engine.record_asset_freeze(
            entity_id="TERR-SEED-01",
            accounts_count=3,
            frozen_amount_vnd=2_500_000_000.0,
        )
        engine.log_tactical_operation(
            operation_id="OP-SEED-01",
            alert_id="ALERT-SEED-01",
            target_id="TGT-SEED-01",
            tactical_action="Cô lập đường truyền máy chủ nhiễm độc",
            commanding_officer="Thượng tá Vũ Nam",
            hostages_rescued=0,
            suspects_neutralized=1,
            outcome_status="RESOLVED_SUCCESS",
        )

        telemetry = engine.get_telemetry_status()
        assert telemetry["total_protected_targets"] == 1
        assert telemetry["total_emergency_plans"] == 1
        assert telemetry["designated_terrorist_entities"] == 1
        assert telemetry["total_frozen_accounts"] == 3
        assert telemetry["total_frozen_funds_vnd"] == 2_500_000_000.0
        assert telemetry["tactical_operations_count"] == 1
        assert telemetry["suspects_neutralized"] == 1

        all_records = engine.list_records(record_type="all")
        assert len(all_records["targets"]) == 1
        assert len(all_records["alerts"]) == 1
        assert len(all_records["plans"]) == 1
        assert len(all_records["sanctions"]) == 1
        assert len(all_records["operations"]) == 1

        target_records = engine.list_records(record_type="targets")
        assert "targets" in target_records
        assert "alerts" not in target_records


class TestAntiTerrorismCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(antiterrorism_app, [])
        assert result.exit_code == 0
        assert "Total Protected Targets" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(antiterrorism_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_protected_targets" in data
        assert "total_frozen_funds_vnd" in data

    def test_cli_target_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            antiterrorism_app,
            [
                "target",
                "--id", "TGT-CLI-01",
                "--name", "Trung tâm Phát thanh Quốc gia",
                "--category", "FINANCIAL_COMMUNICATION_HUB",
                "--level", "CLASS_I",
                "--guard", "Cảnh sát Bảo vệ VOV",
                "--address", "58 Quán Sứ, Hà Nội",
                "--perimeter", "80.0",
                "--status", "SECURE",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["target_id"] == "TGT-CLI-01"
        assert data["protection_level"] == "CLASS_I"

    def test_cli_target_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            antiterrorism_app,
            [
                "target",
                "--id", "TGT-CLI-ERR",
                "--name", "Lỗi Danh mục",
                "--category", "NONEXISTENT_CATEGORY",
                "--guard", "K01",
                "--address", "Hà Nội",
            ],
        )
        assert result.exit_code == 1

    def test_cli_alert_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            antiterrorism_app,
            [
                "alert",
                "--id", "ALERT-CLI-01",
                "--source", "Công an Tỉnh Lào Cai",
                "--type", "ARMED_ATTACK",
                "--level", "SUBSTANTIAL_YELLOW",
                "--summary", "Phát hiện đối tượng nghi vấn vận chuyển vũ khí",
                "--date", "2026-03-30",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["alert_id"] == "ALERT-CLI-01"

    def test_cli_plan_command(self, temp_db: str) -> None:
        runner = CliRunner()
        # Register prerequisite target
        runner.invoke(
            antiterrorism_app,
            [
                "target",
                "--id", "TGT-CLI-PLAN",
                "--name", "Đại sứ quán",
                "--category", "DIPLOMATIC_MISSION",
                "--level", "CLASS_I",
                "--guard", "K01",
                "--address", "Hà Nội",
                "--json",
            ],
        )
        result = runner.invoke(
            antiterrorism_app,
            [
                "plan",
                "--id", "PLAN-CLI-01",
                "--target-id", "TGT-CLI-PLAN",
                "--name", "Phương án bảo vệ đại sứ quán",
                "--scenario", "HOSTAGE_RESCUE",
                "--agency", "Bộ Tư lệnh Cảnh vệ K01",
                "--units", "K01, K02, Công an Hà Nội",
                "--drill", "2025-10-10",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plan_id"] == "PLAN-CLI-01"

    def test_cli_designate_and_freeze_command(self, temp_db: str) -> None:
        runner = CliRunner()
        res_des = runner.invoke(
            antiterrorism_app,
            [
                "designate",
                "--id", "TERR-CLI-01",
                "--name", "Nhóm Bạo loạn Khủng bố Alpha",
                "--type", "ORGANIZATION",
                "--decision", "Thông cáo số 12/TC-BCA",
                "--aliases", "Alpha Squad, Alpha Network",
                "--date", "2026-02-01",
                "--json",
            ],
        )
        assert res_des.exit_code == 0
        des_data = json.loads(res_des.output)
        assert des_data["entity_id"] == "TERR-CLI-01"

        res_frz = runner.invoke(
            antiterrorism_app,
            [
                "freeze",
                "--id", "TERR-CLI-01",
                "--accounts", "4",
                "--amount", "8500000000",
                "--json",
            ],
        )
        assert res_frz.exit_code == 0
        frz_data = json.loads(res_frz.output)
        assert frz_data["total_frozen_accounts"] == 4
        assert frz_data["total_frozen_funds_vnd"] == 8_500_000_000.0

    def test_cli_operate_command(self, temp_db: str) -> None:
        runner = CliRunner()
        # Seed target and alert
        runner.invoke(
            antiterrorism_app,
            [
                "target",
                "--id", "TGT-CLI-OP",
                "--name", "Nhà ga Đường sắt Đô thị",
                "--category", "CRITICAL_INFRASTRUCTURE",
                "--level", "CLASS_II",
                "--guard", "Bảo vệ đường sắt",
                "--address", "Hà Nội",
                "--json",
            ],
        )
        runner.invoke(
            antiterrorism_app,
            [
                "alert",
                "--id", "ALERT-CLI-OP",
                "--source", "Trinh sát",
                "--type", "BOMB_EXPLOSIVE_CBRN",
                "--level", "SEVERE_ORANGE",
                "--summary", "Phát hiện gói hàng nghi chứa chất nổ",
                "--targets", "TGT-CLI-OP",
                "--json",
            ],
        )

        res_op = runner.invoke(
            antiterrorism_app,
            [
                "operate",
                "--id", "OP-CLI-01",
                "--alert-id", "ALERT-CLI-OP",
                "--target-id", "TGT-CLI-OP",
                "--action", "Rà phá bom mìn và vô hiệu hóa ngòi nổ",
                "--officer", "Thượng tá Nguyễn Văn B",
                "--hostages", "0",
                "--neutralized", "0",
                "--status", "RESOLVED_SUCCESS",
                "--date", "2026-03-30",
                "--json",
            ],
        )
        assert res_op.exit_code == 0
        data = json.loads(res_op.output)
        assert data["operation_id"] == "OP-CLI-01"
        assert data["outcome_status"] == "RESOLVED_SUCCESS"

    def test_cli_list_and_status(self, temp_db: str) -> None:
        runner = CliRunner()
        res_list = runner.invoke(antiterrorism_app, ["list", "--type", "all", "--json"])
        assert res_list.exit_code == 0
        list_data = json.loads(res_list.output)
        assert "targets" in list_data

        res_stat = runner.invoke(antiterrorism_app, ["status", "--json"])
        assert res_stat.exit_code == 0
        stat_data = json.loads(res_stat.output)
        assert "total_protected_targets" in stat_data


class TestAntiTerrorismMcp:
    def test_mcp_standalone_target(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_antiterrorism_target

        res_str = handle_antiterrorism_target({
            "target_id": "TGT-MCP-01",
            "target_name": "Tòa nhà Quốc hội",
            "target_category": "POLITICAL_HEADQUARTERS",
            "protection_level": "SPECIAL_CLASS",
            "guard_force": "Bộ Tư lệnh Cảnh vệ K01",
            "location_address": "Ba Đình, Hà Nội",
            "security_perimeter_meters": 150.0,
        })
        res = json.loads(res_str)
        assert res["target_id"] == "TGT-MCP-01"
        assert res["protection_level"] == "SPECIAL_CLASS"

    def test_mcp_standalone_alert(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_antiterrorism_alert

        res_str = handle_antiterrorism_alert({
            "alert_id": "ALERT-MCP-01",
            "threat_source": "Cục Chống khủng bố (A02)",
            "threat_type": "BOMB_EXPLOSIVE_CBRN",
            "threat_level": "SUBSTANTIAL_YELLOW",
            "intelligence_summary": "Cảnh báo an ninh hóa chất độc hại",
            "affected_targets": ["TGT-MCP-01"],
        })
        res = json.loads(res_str)
        assert res["alert_id"] == "ALERT-MCP-01"
        assert res["threat_level"] == "SUBSTANTIAL_YELLOW"

    def test_mcp_standalone_plan(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_antiterrorism_plan, handle_antiterrorism_target

        handle_antiterrorism_target({
            "target_id": "TGT-MCP-PLAN",
            "target_name": "Mục tiêu Kế hoạch MCP",
            "target_category": "POLITICAL_HEADQUARTERS",
            "protection_level": "CLASS_I",
            "guard_force": "K01",
            "location_address": "Hà Nội",
        })
        res_str = handle_antiterrorism_plan({
            "plan_id": "PLAN-MCP-01",
            "target_id": "TGT-MCP-PLAN",
            "plan_name": "Phương án xử lý tình huống khẩn cấp CBRN",
            "tactical_scenario": "CBRN_DECONTAMINATION",
            "lead_command_agency": "Binh chủng Hóa học",
            "participating_units": ["Viện Hóa học Môi trường Quân sự"],
        })
        res = json.loads(res_str)
        assert res["plan_id"] == "PLAN-MCP-01"
        assert res["tactical_scenario"] == "CBRN_DECONTAMINATION"

    def test_mcp_standalone_designate_and_freeze(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_antiterrorism_designate, handle_antiterrorism_freeze

        des_str = handle_antiterrorism_designate({
            "entity_id": "TERR-MCP-01",
            "entity_name": "Liên minh Khủng bố Mạng",
            "entity_type": "ORGANIZATION",
            "designation_decision": "QĐ số 88/QĐ-BCA",
            "aliases": ["Cyber Jihad Net", "Dark Web Terror"],
        })
        des = json.loads(des_str)
        assert des["entity_id"] == "TERR-MCP-01"

        frz_str = handle_antiterrorism_freeze({
            "entity_id": "TERR-MCP-01",
            "accounts_count": 3,
            "frozen_amount_vnd": 3_200_000_000.0,
        })
        frz = json.loads(frz_str)
        assert frz["total_frozen_accounts"] == 3
        assert frz["total_frozen_funds_vnd"] == 3_200_000_000.0

    def test_mcp_standalone_operate(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_antiterrorism_alert,
            handle_antiterrorism_operate,
            handle_antiterrorism_target,
        )

        handle_antiterrorism_target({
            "target_id": "TGT-MCP-OP",
            "target_name": "Sân bay",
            "target_category": "CRITICAL_INFRASTRUCTURE",
            "protection_level": "SPECIAL_CLASS",
            "guard_force": "An ninh Hàng không",
            "location_address": "Đà Nẵng",
        })
        handle_antiterrorism_alert({
            "alert_id": "ALERT-MCP-OP",
            "threat_source": "Trinh sát Hàng không",
            "threat_type": "HOSTAGE_HIJACKING",
            "threat_level": "CRITICAL_RED",
            "intelligence_summary": "Tình huống không tặc giả định",
            "affected_targets": ["TGT-MCP-OP"],
        })
        op_str = handle_antiterrorism_operate({
            "operation_id": "OP-MCP-01",
            "alert_id": "ALERT-MCP-OP",
            "target_id": "TGT-MCP-OP",
            "tactical_action": "Đặc nhiệm đột kích khống chế",
            "commanding_officer": "Trung tướng Chỉ huy trưởng",
            "hostages_rescued": 45,
            "suspects_neutralized": 2,
            "outcome_status": "RESOLVED_SUCCESS",
        })
        op = json.loads(op_str)
        assert op["operation_id"] == "OP-MCP-01"
        assert op["hostages_rescued"] == 45

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_antiterrorism_list, handle_antiterrorism_status

        list_str = handle_antiterrorism_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "targets" in lst

        stat_str = handle_antiterrorism_status({})
        stat = json.loads(stat_str)
        assert "total_protected_targets" in stat

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        tgt_str = server._handle_antiterrorism_target(
            target_id="TGT-CORE-01",
            target_name="Khu Di tích Chủ tịch Hồ Chí Minh tại Phủ Chủ tịch",
            target_category="POLITICAL_HEADQUARTERS",
            protection_level="SPECIAL_CLASS",
            guard_force="Trung đoàn Cảnh vệ K01",
            location_address="Ba Đình, Hà Nội",
        )
        tgt = json.loads(tgt_str)
        assert tgt["target_id"] == "TGT-CORE-01"

        stat_str = server._handle_antiterrorism_status()
        stat = json.loads(stat_str)
        assert stat["total_protected_targets"] >= 1


class TestAntiTerrorismEdgeCases:
    def test_all_target_categories(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        for i, cat in enumerate(VALID_TARGET_CATEGORIES):
            res = engine.register_target(
                target_id=f"TGT-CAT-{i}",
                target_name=f"Mục tiêu {cat}",
                target_category=cat,
                protection_level="CLASS_I",
                guard_force="Lực lượng bảo vệ",
                location_address="Địa chỉ",
            )
            assert res["target_category"] == cat

    def test_all_protection_levels(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        for i, lvl in enumerate(VALID_PROTECTION_LEVELS):
            res = engine.register_target(
                target_id=f"TGT-LVL-{i}",
                target_name=f"Mục tiêu {lvl}",
                target_category="CRITICAL_INFRASTRUCTURE",
                protection_level=lvl,
                guard_force="Lực lượng bảo vệ",
                location_address="Địa chỉ",
            )
            assert res["protection_level"] == lvl

    def test_all_threat_types(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        for i, tt in enumerate(VALID_THREAT_TYPES):
            res = engine.issue_threat_alert(
                alert_id=f"ALERT-TT-{i}",
                threat_source="Nguồn tình báo",
                threat_type=tt,
                threat_level="SUBSTANTIAL_YELLOW",
                intelligence_summary=f"Cảnh báo loại {tt}",
            )
            assert res["threat_type"] == tt

    def test_all_threat_levels(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        for i, tl in enumerate(VALID_THREAT_LEVELS):
            res = engine.issue_threat_alert(
                alert_id=f"ALERT-TL-{i}",
                threat_source="Nguồn tình báo",
                threat_type="ARMED_ATTACK",
                threat_level=tl,
                intelligence_summary=f"Cảnh báo cấp độ {tl}",
            )
            assert res["threat_level"] == tl

    def test_all_tactical_scenarios(self, temp_db: str) -> None:
        engine = AntiTerrorismEngine(db_path=temp_db)
        engine.register_target(
            target_id="TGT-SCEN-ALL",
            target_name="Mục tiêu đa kịch bản",
            target_category="MILITARY_DEFENSE_INSTALLATION",
            protection_level="SPECIAL_CLASS",
            guard_force="Lực lượng đặc nhiệm",
            location_address="Địa chỉ",
        )
        for i, sc in enumerate(VALID_TACTICAL_SCENARIOS):
            res = engine.register_emergency_plan(
                plan_id=f"PLAN-SCEN-{i}",
                target_id="TGT-SCEN-ALL",
                plan_name=f"Kế hoạch tác chiến {sc}",
                tactical_scenario=sc,
                lead_command_agency="Cơ quan chỉ huy",
            )
            assert res["tactical_scenario"] == sc
