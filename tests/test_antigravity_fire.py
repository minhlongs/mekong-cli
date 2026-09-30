"""
Test Suite for Vietnamese Fire Prevention, Safety, Rescue & Engineering Standards Suite (Phase 92).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- FireEngine domain logic (Luật PCCC, Nghị định 136/2020, Nghị định 50/2024, QCVN 06:2022/BXD, Nghị định 144/2021).
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
from src.core.fire_engine import FireEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestFireBoundary:
    """Verifies that fire_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "fire_engine.py")
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


class TestFireEngine:
    """Tests core domain and regulatory business logic of FireEngine."""

    def test_audit_fire_design_approval_commercial_valid(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.audit_fire_design_approval(
            facility_name="Tòa nhà Văn phòng Mekong Tower",
            facility_type="COMMERCIAL_BUILDING",
            floors_count=15,
            floor_area_sqm=12000.0,
            fire_resistance_class="CLASS_I",
            has_sprinkler=True,
            has_alarm=True,
            has_smoke_exhaust=True,
        )
        assert res["status"] == "FIRE_DESIGN_APPROVED"
        assert res["is_approved"] is True
        assert len(res["deficiencies"]) == 0
        assert res["approval_code"].startswith("TD-PCCC-")

    def test_audit_fire_design_approval_karaoke_missing_sprinkler(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        # Karaoke is high-risk facility requiring automatic sprinkler
        res = engine.audit_fire_design_approval(
            facility_name="Quán Karaoke Hoàng Gia",
            facility_type="KARAOKE_NIGHTCLUB",
            floors_count=4,
            floor_area_sqm=800.0,
            has_sprinkler=False,  # Violation!
            has_alarm=True,
            has_smoke_exhaust=True,
        )
        assert res["status"] == "FIRE_DESIGN_REJECTED"
        assert res["is_approved"] is False
        assert any("Sprinkler" in d for d in res["deficiencies"])

    def test_audit_fire_design_approval_high_rise_missing_smoke(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        # Building >= 10 floors requires smoke exhaust system
        res = engine.audit_fire_design_approval(
            facility_name="Chung cư Cao tầng Mekong Heights",
            facility_type="RESIDENTIAL_HIGHRISE",
            floors_count=18,
            floor_area_sqm=20000.0,
            has_sprinkler=True,
            has_alarm=True,
            has_smoke_exhaust=False,  # Violation!
        )
        assert res["status"] == "FIRE_DESIGN_REJECTED"
        assert res["is_approved"] is False
        assert any("hút khói sự cố" in d for d in res["deficiencies"])

    def test_inspect_fire_acceptance_compliant(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.inspect_fire_acceptance(
            facility_name="Trung tâm Thương mại Mekong Mall",
            water_pressure_mpa=0.45,  # >= 0.40 MPa
            generator_switch_sec=12.0,  # <= 15s
            is_smoke_system_ok=True,
            is_exit_doors_compliant=True,
            is_already_operational=False,
        )
        assert res["status"] == "FIRE_ACCEPTANCE_GRANTED"
        assert res["is_accepted"] is True
        assert res["penalty_fine_vnd"] == 0.0
        assert len(res["deficiencies"]) == 0
        assert res["inspection_code"].startswith("NT-PCCC-")

    def test_inspect_fire_acceptance_low_water_pressure(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.inspect_fire_acceptance(
            facility_name="Nhà xưởng Sản xuất Dệt may",
            water_pressure_mpa=0.25,  # Too low! Minimum is 0.40
            generator_switch_sec=10.0,
            is_smoke_system_ok=True,
            is_exit_doors_compliant=True,
            is_already_operational=False,
        )
        assert res["status"] == "FIRE_ACCEPTANCE_FAILED"
        assert res["is_accepted"] is False
        assert any("Áp lực nước" in d for d in res["deficiencies"])

    def test_inspect_fire_acceptance_unapproved_occupancy_violation(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        # Put into operation before approval with failing systems
        res = engine.inspect_fire_acceptance(
            facility_name="Chung cư Chưa Nghiệm thu Đã Ở",
            water_pressure_mpa=0.20,
            generator_switch_sec=25.0,
            is_smoke_system_ok=False,
            is_exit_doors_compliant=False,
            is_already_operational=True,  # Severe legal violation!
        )
        assert res["status"] == "UNAPPROVED_OCCUPANCY_VIOLATION"
        assert res["is_accepted"] is False
        assert res["penalty_fine_vnd"] == 45_000_000.0
        assert any("VI PHẠM ĐẶC BIỆT NGHIÊM TRỌNG" in d for d in res["deficiencies"])

    def test_verify_fire_equipment_stamped(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.verify_fire_equipment(
            equipment_type="EXTINGUISHER_ABC_4KG",
            serial_number="BC-ABC-2026-9999",
            manufacturer="Công ty PCCC Mekong",
            pressure_rating_bar=14.0,
            has_factory_testing=True,
        )
        assert res["status"] == "EQUIPMENT_CERTIFIED_STAMPED"
        assert res["is_certified"] is True
        assert res["stamp_issued"] == "TEM_KIEM_DINH_PCCC_BCA"
        assert res["validity_years"] == 2
        assert res["verification_code"].startswith("KD-TEM-PCCC-")

    def test_verify_fire_equipment_low_pressure(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.verify_fire_equipment(
            equipment_type="EXTINGUISHER_ABC_4KG",
            serial_number="BC-DEFICIENT",
            pressure_rating_bar=6.0,  # Below 10 bar minimum
            has_factory_testing=True,
        )
        assert res["status"] == "EQUIPMENT_REJECTED"
        assert res["is_certified"] is False

    def test_license_fire_service_firm_approved(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.license_fire_service_firm(
            firm_name="Công ty CP Kỹ thuật An toàn PCCC Sài Gòn",
            technical_director="Kỹ sư Trần Anh Tuấn",
            has_director_certificate=True,
            certified_engineers_count=3,
            has_equipment_facility=True,
            scope="DESIGN_AND_SUPERVISION",
        )
        assert res["status"] == "FIRE_SERVICE_LICENSED"
        assert res["is_licensed"] is True
        assert res["validity_years"] == 5
        assert len(res["deficiencies"]) == 0
        assert res["license_code"].startswith("GP-DV-PCCC-")

    def test_license_fire_service_firm_no_director_cert(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.license_fire_service_firm(
            firm_name="Công ty Thiếu Chứng Chỉ Giám Đốc",
            has_director_certificate=False,
            certified_engineers_count=2,
            has_equipment_facility=True,
        )
        assert res["status"] == "FIRE_SERVICE_DENIED"
        assert res["is_licensed"] is False
        assert any("Chứng chỉ bồi dưỡng" in d for d in res["deficiencies"])

    def test_license_fire_service_firm_no_engineers(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        res = engine.license_fire_service_firm(
            firm_name="Công ty Không Kỹ Sư",
            has_director_certificate=True,
            certified_engineers_count=0,
            has_equipment_facility=True,
        )
        assert res["status"] == "FIRE_SERVICE_DENIED"
        assert res["is_licensed"] is False
        assert any("Chứng chỉ hành nghề" in d for d in res["deficiencies"])

    def test_list_records_and_status(self, temp_db):
        engine = FireEngine(db_path=temp_db)
        engine.audit_fire_design_approval("Tòa nhà A")
        engine.inspect_fire_acceptance("Tòa nhà B", is_already_operational=True)
        engine.verify_fire_equipment(serial_number="EQ-001")
        engine.license_fire_service_firm("Doanh nghiệp C")

        designs = engine.list_records(category="designs")
        assert len(designs) >= 1
        accepts = engine.list_records(category="acceptances")
        assert len(accepts) >= 1
        equips = engine.list_records(category="equipments")
        assert len(equips) >= 1
        lics = engine.list_records(category="licenses")
        assert len(lics) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_design_approvals_audited"] >= 1
        assert status["total_acceptance_inspections"] >= 1
        assert status["total_equipment_inspected"] >= 1
        assert status["total_service_licenses_processed"] >= 1


class TestFireCLI:
    """Tests Typer CLI commands for the fire app."""

    def test_cli_main_and_status(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["fire", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"

        res_main = runner.invoke(app, ["fire"])
        assert res_main.exit_code == 0
        assert "PHÒNG CHÁY" in res_main.output

    def test_cli_design_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "fire",
                "design",
                "Tòa nhà Văn phòng CLI Tower",
                "--type",
                "COMMERCIAL_BUILDING",
                "--floors",
                "12",
                "--area",
                "10000",
                "--class",
                "CLASS_I",
                "--sprinkler",
                "--alarm",
                "--smoke",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "FIRE_DESIGN_APPROVED"

    def test_cli_accept_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "fire",
                "accept",
                "Chung cư Xanh CLI",
                "--pressure",
                "0.48",
                "--switch-sec",
                "11",
                "--smoke-ok",
                "--exit-ok",
                "--non-operational",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_accepted"] is True
        assert data["status"] == "FIRE_ACCEPTANCE_GRANTED"

    def test_cli_equip_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "fire",
                "equip",
                "BC-CLI-TEST-001",
                "--type",
                "EXTINGUISHER_ABC_4KG",
                "--mfr",
                "Mekong Fire Equipment",
                "--pressure",
                "14.5",
                "--tested",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_certified"] is True
        assert data["status"] == "EQUIPMENT_CERTIFIED_STAMPED"

    def test_cli_license_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "fire",
                "license",
                "Công ty TNHH Dịch vụ PCCC CLI",
                "--director",
                "KS. Lê Quốc Hùng",
                "--director-cert",
                "--engineers",
                "3",
                "--facility",
                "--scope",
                "DESIGN_AND_SUPERVISION",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_licensed"] is True
        assert data["status"] == "FIRE_SERVICE_LICENSED"

    def test_cli_list_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["fire", "list", "designs", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestFireMCP:
    """Tests dual FastMCP and fallback handlers for Fire suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Design
        res_des = json.loads(
            server._handle_fire_design(
                facility_name="MCP Fire Tower",
                facility_type="COMMERCIAL_BUILDING",
                floors_count=10,
                floor_area_sqm=8000.0,
            )
        )
        assert res_des["is_approved"] is True

        # Accept
        res_acc = json.loads(
            server._handle_fire_accept(
                facility_name="MCP Fire Facility",
                water_pressure_mpa=0.45,
                generator_switch_sec=12.0,
            )
        )
        assert res_acc["is_accepted"] is True

        # Equip
        res_eq = json.loads(
            server._handle_fire_equip(
                equipment_type="EXTINGUISHER_ABC_4KG",
                serial_number="MCP-EQ-001",
            )
        )
        assert res_eq["is_certified"] is True

        # License
        res_lic = json.loads(
            server._handle_fire_license(
                firm_name="MCP Fire Firm",
                technical_director="KS. MCP",
            )
        )
        assert res_lic["is_licensed"] is True

        # List
        res_list = json.loads(server._handle_fire_list(category="designs"))
        assert isinstance(res_list, list)

        # Status
        res_status = json.loads(server._handle_fire_status())
        assert res_status["status"] == "HEALTHY"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as script_mcp

        # Test dictionary registration
        assert "mekong_fire_design" in script_mcp.CORE_HANDLERS
        assert "mekong_fire_accept" in script_mcp.CORE_HANDLERS
        assert "mekong_fire_equip" in script_mcp.CORE_HANDLERS
        assert "mekong_fire_license" in script_mcp.CORE_HANDLERS
        assert "mekong_fire_list" in script_mcp.CORE_HANDLERS
        assert "mekong_fire_status" in script_mcp.CORE_HANDLERS

        # Invocations
        h_des = script_mcp.CORE_HANDLERS["mekong_fire_design"]
        res_des = json.loads(h_des({"facility_name": "Script MCP Facility"}))
        assert "approval_code" in res_des

        h_status = script_mcp.CORE_HANDLERS["mekong_fire_status"]
        res_status = json.loads(h_status({}))
        assert res_status["status"] == "HEALTHY"
