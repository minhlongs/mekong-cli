"""
Test Suite for Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite (Phase 97).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- RadiationEngine domain logic (Luật Năng lượng nguyên tử 2008, Nghị định 142/2020/NĐ-CP, Thông tư 19/2012/TT-BKHCN, Quyết định 446/QĐ-BKHCN, TTLT 13/2014/TTLT-BKHCN-BYT).
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
from src.core.radiation_engine import (
    RadiationEngine,
    ANNUAL_EFFECTIVE_DOSE_LIMIT_MSV,
    LEAK_DOSE_RATE_LIMIT_USV_H,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestRadiationBoundary:
    """Verifies that radiation_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "radiation_engine.py")
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


class TestRadiationEngine:
    """Tests core domain and regulatory business logic of RadiationEngine."""

    def test_audit_radiation_facility_license_eligible(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.audit_radiation_facility_license(
            facility_name="Bệnh viện Chợ Rẫy - Trung tâm Ung bướu",
            facility_type="HOSPITAL_RADIOLOGY",
            equipment_type="LINEAR_ACCELERATOR",
            safety_officer_certified=True,
            emergency_plan_approved=True,
            storage_shielding_compliant=True,
            has_warning_signs=True,
            radiation_leak_dose_rate_uSv_h=0.20,
        )

        assert res["is_eligible"] is True
        assert len(res["deficiencies"]) == 0
        assert res["validity_years"] == 3
        assert res["license_id"].startswith("RAD-LIC-")

    def test_audit_radiation_facility_license_ineligible(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.audit_radiation_facility_license(
            facility_name="Phòng chụp X-quang Chui",
            facility_type="HOSPITAL_RADIOLOGY",
            equipment_type="MEDICAL_XRAY",
            safety_officer_certified=False,
            emergency_plan_approved=False,
            storage_shielding_compliant=False,
            has_warning_signs=False,
            radiation_leak_dose_rate_uSv_h=0.85,  # > 0.5 uSv/h limit
        )

        assert res["is_eligible"] is False
        assert len(res["deficiencies"]) >= 4
        assert any("Suất liều rò rỉ" in d for d in res["deficiencies"])
        assert any("Người phụ trách an toàn bức xạ" in d for d in res["deficiencies"])

    def test_record_personal_dosimetry_normal(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.record_personal_dosimetry(
            employee_name="Nguyễn Văn A",
            employee_id="NV-RAD-001",
            facility_name="Bệnh viện Đa khoa Quốc tế",
            quarter=1,
            year=2026,
            effective_dose_mSv=1.1,
            cumulative_annual_dose_mSv=3.5,
            wearing_period_days=90,
        )

        assert "NORMAL_COMPLIANT" in res["status"]
        assert res["record_id"].startswith("DOS-REC-")
        assert len(res["recommendations"]) >= 1

    def test_record_personal_dosimetry_warning(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.record_personal_dosimetry(
            employee_name="Trần Thị B",
            employee_id="NV-RAD-002",
            facility_name="Công ty Kiểm định NDT",
            quarter=3,
            year=2026,
            effective_dose_mSv=4.2,
            cumulative_annual_dose_mSv=16.8,  # > 15 mSv, < 20 mSv
            wearing_period_days=88,
        )

        assert "WARNING_HIGH_EXPOSURE" in res["status"]
        assert any("tiệm cận giới hạn cho phép" in r or "kiểm tra rò rỉ" in r for r in res["recommendations"])

    def test_record_personal_dosimetry_limit_exceeded(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.record_personal_dosimetry(
            employee_name="Lê Văn C",
            employee_id="NV-RAD-003",
            facility_name="Cơ sở Chiếu xạ Công nghiệp",
            quarter=4,
            year=2026,
            effective_dose_mSv=6.5,
            cumulative_annual_dose_mSv=21.5,  # > 20 mSv limit
            wearing_period_days=105,           # Overdue (> 95 days)
        )

        assert "CRITICAL_EXCEED_ANNUAL_LIMIT" in res["status"]
        assert any("Đình chỉ ngay công việc" in r for r in res["recommendations"])
        assert any("vượt chu kỳ quy định" in r for r in res["recommendations"])

    def test_audit_radioactive_source_security_compliant(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.audit_radioactive_source_security(
            source_serial="SRC-IR192-2026-99",
            isotope="IR-192",
            initial_activity_curie=100.0,
            current_activity_curie=65.0,
            application_type="INDUSTRIAL_NDT",
            has_gps_tracker=True,
            gps_signal_active=True,
            within_authorized_perimeter=True,
            storage_vault_secured=True,
        )

        assert res["iaea_category"] in (1, 2, 3, 4)
        assert "SECURED_COMPLIANT" in res["security_status"]
        assert len(res["violations"]) == 0
        assert res["audit_id"].startswith("SRC-SEC-")

    def test_audit_radioactive_source_security_critical_alarm(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.audit_radioactive_source_security(
            source_serial="SRC-CO60-ALARM",
            isotope="CO-60",
            initial_activity_curie=500.0,
            current_activity_curie=450.0,
            application_type="INDUSTRIAL_NDT",
            has_gps_tracker=True,
            gps_signal_active=False,            # Signal lost
            within_authorized_perimeter=False,  # Perimeter breached
            storage_vault_secured=False,
        )

        assert res["iaea_category"] == 1
        assert "CRITICAL_ALERT_BREACH" in res["security_status"]
        assert len(res["violations"]) >= 3
        assert any("NGOÀI PHẠM VI CẤP PHÉP" in v for v in res["violations"])
        assert any("mất kết nối tín hiệu" in v for v in res["violations"])

    def test_inspect_medical_xray_compliant(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.inspect_medical_xray_machine(
            clinic_name="Phòng khám Đa khoa Quốc tế Hạnh Phúc",
            machine_model="GE Definium 646 HD",
            machine_type="CONVENTIONAL_XRAY",
            kvp_accuracy_pct=3.2,
            timer_accuracy_pct=4.1,
            lead_shielding_thickness_mm=2.5,
            last_inspection_months_ago=6,
            warning_light_operational=True,
        )

        assert res["is_compliant"] is True
        assert "ĐẠT CHUẨN" in res["qa_rating"]
        assert len(res["deficiencies"]) == 0
        assert res["inspection_id"].startswith("XRY-INS-")

    def test_inspect_medical_xray_failed(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)
        res = engine.inspect_medical_xray_machine(
            clinic_name="Cơ sở X-quang Lạc Hậu",
            machine_model="Cũ kỹ 1995",
            machine_type="CONVENTIONAL_XRAY",
            kvp_accuracy_pct=14.5,            # > 10%
            timer_accuracy_pct=12.0,          # > 10%
            lead_shielding_thickness_mm=1.2,  # < 2.0 mm Pb
            last_inspection_months_ago=18,     # > 12 months
            warning_light_operational=False,
        )

        assert res["is_compliant"] is False
        assert "KHÔNG ĐẠT CHUẨN" in res["qa_rating"]
        assert len(res["deficiencies"]) >= 4

    def test_list_records_and_status(self, temp_db):
        engine = RadiationEngine(db_path=temp_db)

        # Populate records
        engine.audit_radiation_facility_license(
            facility_name="Test Clinic",
            safety_officer_certified=True,
            emergency_plan_approved=True,
            storage_shielding_compliant=True,
            has_warning_signs=True,
            radiation_leak_dose_rate_uSv_h=0.15,
        )
        engine.record_personal_dosimetry(
            employee_name="Tech 1",
            employee_id="NV-TEST-1",
            facility_name="Test Clinic",
            effective_dose_mSv=1.0,
            cumulative_annual_dose_mSv=2.0,
        )
        engine.audit_radioactive_source_security(
            source_serial="TEST-SRC-01",
            has_gps_tracker=True,
            gps_signal_active=True,
            within_authorized_perimeter=True,
            storage_vault_secured=True,
        )
        engine.inspect_medical_xray_machine(
            clinic_name="X-ray Test Lab",
            machine_model="Lab-Model-1",
            kvp_accuracy_pct=2.0,
            timer_accuracy_pct=3.0,
            lead_shielding_thickness_mm=2.5,
            last_inspection_months_ago=4,
            warning_light_operational=True,
        )

        # List all
        records = engine.list_records(category="all", limit=10)
        assert len(records) == 4

        # List individual categories
        assert len(engine.list_records(category="facilities")) == 1
        assert len(engine.list_records(category="dosimetry")) == 1
        assert len(engine.list_records(category="sources")) == 1
        assert len(engine.list_records(category="xray")) == 1

        # Check telemetry status
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_licensed_facilities"] == 1
        assert status["personal_dosimetry_records_count"] == 1
        assert status["monitored_radioactive_sources"] == 1
        assert status["medical_xray_machines_inspected"] == 1


class TestRadiationCLI:
    """Tests Typer CLI interface for radiation commands in --json mode."""

    def test_radiation_license_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "radiation",
                "license",
                "Bệnh viện Quốc tế Mekong",
                "--fac-type", "HOSPITAL_RADIOLOGY",
                "--equipment", "MEDICAL_XRAY",
                "--leak-rate", "0.25",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_eligible"] is True
        assert data["facility_name"] == "Bệnh viện Quốc tế Mekong"

    def test_radiation_dose_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "radiation",
                "dose",
                "Đặng Quốc Việt",
                "--id", "NV-MK-99",
                "--facility", "Viện Y học Hạt nhân",
                "--dose", "1.5",
                "--cumulative", "5.2",
                "--days", "90",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "NORMAL_COMPLIANT" in data["status"]
        assert data["employee_name"] == "Đặng Quốc Việt"

    def test_radiation_source_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "radiation",
                "source",
                "SRC-IR192-MK01",
                "--isotope", "IR-192",
                "--init-act", "75.0",
                "--cur-act", "40.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "SECURED_COMPLIANT" in data["security_status"]
        assert data["source_serial"] == "SRC-IR192-MK01"

    def test_radiation_xray_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "radiation",
                "xray",
                "Phòng khám Phổi Hà Nội",
                "--model", "Philips Digital X-Ray",
                "--kvp", "4.0",
                "--timer", "3.5",
                "--lead", "2.2",
                "--months", "6",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_compliant"] is True
        assert data["clinic_name"] == "Phòng khám Phổi Hà Nội"

    def test_radiation_list_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["radiation", "list", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_radiation_status_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["radiation", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "total_licensed_facilities" in data


class TestRadiationMCP:
    """Tests dual MCP handlers for radiation safety and nuclear source tools."""

    def test_core_mcp_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-radiation-core")

        # License
        res1 = json.loads(server._handle_radiation_license(facility_name="MCP Test Hospital"))
        assert res1["facility_name"] == "MCP Test Hospital"
        assert res1["is_eligible"] is True

        # Dose
        res2 = json.loads(server._handle_radiation_dose(employee_name="MCP Tech", effective_dose_mSv=1.2))
        assert "NORMAL_COMPLIANT" in res2["status"]

        # Source
        res3 = json.loads(server._handle_radiation_source(source_serial="MCP-SRC-01", isotope="IR-192"))
        assert "SECURED_COMPLIANT" in res3["security_status"]

        # X-ray
        res4 = json.loads(server._handle_radiation_xray(clinic_name="MCP Clinic", kvp_accuracy_pct=3.0))
        assert res4["is_compliant"] is True

        # List
        res5 = json.loads(server._handle_radiation_list(category="all", limit=5))
        assert isinstance(res5, list)

        # Status
        res6 = json.loads(server._handle_radiation_status())
        assert res6["status"] == "operational"

    def test_scripts_mcp_handlers(self):
        from scripts.mcp_server import (
            handle_radiation_license,
            handle_radiation_dose,
            handle_radiation_source,
            handle_radiation_xray,
            handle_radiation_list,
            handle_radiation_status,
        )

        res1 = json.loads(handle_radiation_license({"facility_name": "Fallback Radiation Center"}))
        assert res1["facility_name"] == "Fallback Radiation Center"

        res2 = json.loads(handle_radiation_dose({"employee_name": "Fallback Officer"}))
        assert "status" in res2

        res3 = json.loads(handle_radiation_source({"source_serial": "Fallback Source"}))
        assert "security_status" in res3

        res4 = json.loads(handle_radiation_xray({"clinic_name": "Fallback X-Ray"}))
        assert "qa_rating" in res4

        res5 = json.loads(handle_radiation_list({"category": "all", "limit": 5}))
        assert isinstance(res5, list)

        res6 = json.loads(handle_radiation_status({}))
        assert res6["status"] == "operational"
