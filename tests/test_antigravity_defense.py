"""
Test Suite for Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite (Phase 100 - Century Milestone).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- DefenseEngine domain logic (Luật CNQP, AN & ĐVCN 2024, Luật Quốc phòng 2018, TCVN/QS, TCVN/AN).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.defense_engine import (
    DefenseEngine,
    STATUTORY_MIN_MOBILIZATION_STOCK_DAYS,
    STRATEGIC_DUAL_USE_CATEGORIES,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestDefenseBoundary:
    """Verifies that defense_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "defense_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestDefenseEngine:
    """Tests core domain and regulatory business logic of DefenseEngine."""

    def test_audit_facility_license_approved(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.audit_facility_license(
            facility_name="Nhà máy Z111 - Tổng cục CNQP",
            entity_type="STATE_OWNED_DEFENSE_ENTERPRISE",
            product_category="WEAPONS_AMMUNITION",
            state_secrets_clearance="TOP_SECRET",
            personnel_security_cleared=True,
            perimeter_defense_and_pccc=True,
            hazardous_waste_clearance=True,
        )

        assert res["is_approved"] is True
        assert len(res["deficiencies"]) == 0
        assert res["valid_until"] != "N/A"
        assert res["license_id"].startswith("DEF-LIC-")

    def test_audit_facility_license_deficiencies(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.audit_facility_license(
            facility_name="Xưởng Cơ Khí Trôi Nổi",
            entity_type="UNAUTHORIZED_ENTITY",
            product_category="SPECIAL_EQUIPMENT",
            state_secrets_clearance="CONFIDENTIAL",
            personnel_security_cleared=False,
            perimeter_defense_and_pccc=False,
            hazardous_waste_clearance=False,
        )

        assert res["is_approved"] is False
        assert len(res["deficiencies"]) == 4
        assert any("Loại hình doanh nghiệp" in d for d in res["deficiencies"])
        assert any("an ninh chính trị" in d for d in res["deficiencies"])
        assert any("bảo vệ vành đai" in d for d in res["deficiencies"])
        assert any("chất thải độc hại quân sự" in d for d in res["deficiencies"])

    def test_verify_dual_use_export_control_authorized(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.verify_dual_use_export_control(
            item_name="Module Vi cơ điện tử bán dẫn MEMS cấp quân sự",
            dual_use_code="DU_SEMI_MIL",
            quantity=500,
            destination_country="SINGAPORE",
            end_user_name="TechDefense Corp",
            has_valid_euc=True,
            no_retransfer_commitment=True,
            mod_export_permit_issued=True,
        )

        assert "EXPORT_AUTHORIZED" in res["compliance_status"]
        assert len(res["restrictions"]) == 0
        assert res["control_id"].startswith("DUC-EXP-")

    def test_verify_dual_use_export_control_denied(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.verify_dual_use_export_control(
            item_name="Hợp kim Titan siêu nhẹ",
            dual_use_code="DU_TITANIUM_AERO",
            quantity=2000,
            destination_country="UNKNOWN",
            end_user_name="Shell Company",
            has_valid_euc=False,
            no_retransfer_commitment=False,
            mod_export_permit_issued=False,
        )

        assert "CRITICAL_VIOLATION_DENIED" in res["compliance_status"]
        assert len(res["restrictions"]) >= 3
        assert any("End-User Certificate" in r for r in res["restrictions"])
        assert any("tái xuất khẩu" in r for r in res["restrictions"])

    def test_evaluate_industrial_mobilization_combat_ready(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.evaluate_industrial_mobilization(
            enterprise_name="Công ty CP Chế tạo Hàng không Thăng Long",
            mobilization_capacity="DRONE_AIRFRAME",
            reserved_production_lines=3,
            strategic_material_stock_days=180,
            annual_mobilization_drill_done=True,
            cyber_hardened_facility=True,
        )

        assert res["is_ready"] is True
        assert len(res["action_items"]) == 0
        assert "COMBAT_READY" in res["readiness_rating"]
        assert res["plan_id"].startswith("IMB-PLN-")

    def test_evaluate_industrial_mobilization_deficient(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.evaluate_industrial_mobilization(
            enterprise_name="Nhà máy Dệt May Dân dụng",
            mobilization_capacity="MILITARY_UNIFORM_BALLISTIC",
            reserved_production_lines=0,
            strategic_material_stock_days=45,  # < 90 days statutory min
            annual_mobilization_drill_done=False,
            cyber_hardened_facility=False,
        )

        assert res["is_ready"] is False
        assert len(res["action_items"]) == 4
        assert any("dây chuyền sản xuất dự phòng" in a for a in res["action_items"])
        assert any("Dự trữ vật tư chiến lược" in a for a in res["action_items"])
        assert any("diễn tập thực binh" in a for a in res["action_items"])
        assert any("SCADA/ICS" in a for a in res["action_items"])

    def test_test_military_technical_qa_passed(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.test_military_technical_qa(
            equipment_name="Radar Cảnh giới Biển ven bờ thế hệ mới",
            standard_code="TCVN_QS_789",
            temp_range_celsius="-10C to +55C",
            salt_fog_resistance_hours=120,
            ecm_anti_jamming_resilience_db=36.5,
            tolerance_error_pct=0.04,
        )

        assert res["is_compliant"] is True
        assert len(res["deviation_points"]) == 0
        assert "PASSED_MILITARY_ACCEPTANCE" in res["test_verdict"]
        assert res["qa_id"].startswith("MIL-QA-")

    def test_test_military_technical_qa_failed(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        res = engine.test_military_technical_qa(
            equipment_name="Khí tài Quang điện tử mẫu thử nghiệm",
            standard_code="TCVN_QS_789",
            temp_range_celsius="-5C to +40C",
            salt_fog_resistance_hours=48,  # < 96h
            ecm_anti_jamming_resilience_db=18.0,  # < 30.0 dB
            tolerance_error_pct=0.25,  # > 0.10%
        )

        assert res["is_compliant"] is False
        assert len(res["deviation_points"]) == 3
        assert any("sương muối biển" in d for d in res["deviation_points"])
        assert any("chống tác chiến điện tử" in d for d in res["deviation_points"])
        assert any("Dung sai cơ khí" in d for d in res["deviation_points"])
        assert "FAILED_SPECIFICATION" in res["test_verdict"]

    def test_list_records_and_status(self, temp_db):
        engine = DefenseEngine(db_path=temp_db)
        engine.audit_facility_license(facility_name="Facility A")
        engine.verify_dual_use_export_control(item_name="Item B")
        engine.evaluate_industrial_mobilization(enterprise_name="Enterprise C")
        engine.test_military_technical_qa(equipment_name="Hardware D")

        all_records = engine.list_records(category="all")
        assert len(all_records) == 4

        licenses = engine.list_records(category="licenses")
        assert len(licenses) == 1
        assert licenses[0]["facility_name"] == "Facility A"

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_defense_facilities_audited"] == 1
        assert status["total_dual_use_exports_screened"] == 1
        assert status["industrial_mobilization_plans"] == 1
        assert status["military_technical_qas_conducted"] == 1


class TestDefenseCLI:
    """Tests Typer CLI commands for National Defense Industry Suite."""

    def setup_method(self):
        self.runner = CliRunner()
        self.app = build_app()

    def test_cli_defense_status_json(self):
        res = self.runner.invoke(self.app, ["defense", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "regulatory_framework" in data
        assert "competent_authority" in data

    def test_cli_defense_license_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "defense",
                "license",
                "Nhà máy Z111",
                "--type",
                "STATE_OWNED_DEFENSE_ENTERPRISE",
                "--category",
                "WEAPONS_AMMUNITION",
                "--clearance",
                "TOP_SECRET",
                "--personnel",
                "--perimeter",
                "--waste",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["facility_name"] == "Nhà máy Z111"
        assert data["is_approved"] is True

    def test_cli_defense_dual_use_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "defense",
                "dual-use",
                "Cảm biến hồng ngoại quan sát đêm",
                "--code",
                "DU_OPTICS_NIGHT",
                "--qty",
                "150",
                "--dest",
                "FRANCE",
                "--end-user",
                "Thales Defense",
                "--euc",
                "--no-retransfer",
                "--permit",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["item_name"] == "Cảm biến hồng ngoại quan sát đêm"
        assert "EXPORT_AUTHORIZED" in data["compliance_status"]

    def test_cli_defense_mobilization_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "defense",
                "mobilization",
                "Nhà máy Đóng tàu Dân dụng Ba Son",
                "--capacity",
                "DRONE_AIRFRAME",
                "--lines",
                "2",
                "--stock-days",
                "150",
                "--drill",
                "--cyber",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["enterprise_name"] == "Nhà máy Đóng tàu Dân dụng Ba Son"
        assert data["is_ready"] is True

    def test_cli_defense_qa_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "defense",
                "qa",
                "Hệ thống thông tin liên lạc sóng ngắn quân sự",
                "--standard",
                "TCVN_QS_789",
                "--temp",
                "-10C to +55C",
                "--salt-fog",
                "120",
                "--anti-jamming",
                "35.0",
                "--tolerance",
                "0.05",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["equipment_name"] == "Hệ thống thông tin liên lạc sóng ngắn quân sự"
        assert data["is_compliant"] is True

    def test_cli_defense_list_json(self):
        res = self.runner.invoke(self.app, ["defense", "list", "all", "--limit", "10", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestDefenseMCP:
    """Tests dual FastMCP and pure-Python JSON-RPC handlers for Defense Suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-defense-core")

        # License audit
        l_res = json.loads(
            server._handle_defense_license(
                facility_name="MCP Defense Factory",
                entity_type="STATE_OWNED_DEFENSE_ENTERPRISE",
            )
        )
        assert l_res["is_approved"] is True

        # Dual-use control
        d_res = json.loads(
            server._handle_defense_dual_use(
                item_name="MCP Dual-Use Sensor",
                dual_use_code="DU_SEMI_MIL",
                has_valid_euc=True,
                no_retransfer_commitment=True,
                mod_export_permit_issued=True,
            )
        )
        assert "EXPORT_AUTHORIZED" in d_res["compliance_status"]

        # Mobilization plan
        m_res = json.loads(
            server._handle_defense_mobilization(
                enterprise_name="MCP Drone Builder",
                strategic_material_stock_days=100,
            )
        )
        assert m_res["is_ready"] is True

        # QA test
        q_res = json.loads(
            server._handle_defense_qa(
                equipment_name="MCP Military Hardware",
                salt_fog_resistance_hours=100,
                ecm_anti_jamming_resilience_db=32.0,
                tolerance_error_pct=0.08,
            )
        )
        assert q_res["is_compliant"] is True

        # List and status
        list_res = json.loads(server._handle_defense_list(category="all", limit=5))
        assert isinstance(list_res, list)

        stat_res = json.loads(server._handle_defense_status())
        assert stat_res["status"] == "operational"

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_defense_license,
            handle_defense_dual_use,
            handle_defense_mobilization,
            handle_defense_qa,
            handle_defense_list,
            handle_defense_status,
            CORE_HANDLERS,
        )

        assert "mekong_defense_license" in CORE_HANDLERS
        assert "mekong_defense_dual_use" in CORE_HANDLERS
        assert "mekong_defense_mobilization" in CORE_HANDLERS
        assert "mekong_defense_qa" in CORE_HANDLERS
        assert "mekong_defense_list" in CORE_HANDLERS
        assert "mekong_defense_status" in CORE_HANDLERS

        l_res = json.loads(handle_defense_license({"facility_name": "Pure Stdio Z111"}))
        assert l_res["is_approved"] is True

        d_res = json.loads(handle_defense_dual_use({"item_name": "Pure Avionics", "has_valid_euc": True, "no_retransfer_commitment": True, "mod_export_permit_issued": True}))
        assert "EXPORT_AUTHORIZED" in d_res["compliance_status"]

        m_res = json.loads(handle_defense_mobilization({"enterprise_name": "Pure Mobilizer", "strategic_material_stock_days": 120}))
        assert m_res["is_ready"] is True

        q_res = json.loads(handle_defense_qa({"equipment_name": "Pure Radio", "salt_fog_resistance_hours": 120, "ecm_anti_jamming_resilience_db": 35.0, "tolerance_error_pct": 0.05}))
        assert q_res["is_compliant"] is True

        list_res = json.loads(handle_defense_list({"category": "all", "limit": 5}))
        assert isinstance(list_res, list)

        stat_res = json.loads(handle_defense_status({}))
        assert stat_res["status"] == "operational"
