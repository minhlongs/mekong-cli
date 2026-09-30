"""
Test Suite for Vietnamese Cybersecurity, Critical Infrastructure & Network Security Suite (Phase 95).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- CyberEngine domain logic (Luật An ninh mạng 2018, Nghị định 53/2022/NĐ-CP, Nghị định 85/2016/NĐ-CP, Thông tư 20/2017/TT-BTTTT).
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
from src.core.cyber_engine import CyberEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCyberBoundary:
    """Verifies that cyber_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "cyber_engine.py")
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


class TestCyberEngine:
    """Tests core domain and regulatory business logic of CyberEngine."""

    def test_audit_data_localization_compliant(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.audit_data_localization(
            service_name="Mekong Cloud Services",
            provider_type="FOREIGN_TECH_PLATFORM",
            stores_personal_data=True,
            stores_user_generated_data=True,
            stores_relationship_data=True,
            local_storage_active=True,
            retention_months=24,
            has_local_branch=True,
        )

        assert res["is_compliant"] is True
        assert len(res["deficiencies"]) == 0
        assert res["rectification_deadline_days"] == 0
        assert res["service_name"] == "Mekong Cloud Services"
        assert res["audit_id"].startswith("CYB-LOC-")

    def test_audit_data_localization_non_compliant(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.audit_data_localization(
            service_name="Global Social App",
            provider_type="FOREIGN_TECH_PLATFORM",
            stores_personal_data=True,
            stores_user_generated_data=True,
            stores_relationship_data=True,
            local_storage_active=False,
            retention_months=12,
            has_local_branch=False,
        )

        assert res["is_compliant"] is False
        assert len(res["deficiencies"]) == 3
        assert res["rectification_deadline_days"] == 365
        assert any("Điều 26" in d for d in res["deficiencies"])
        assert any("24 tháng" in d for d in res["deficiencies"])
        assert any("chi nhánh" in d for d in res["deficiencies"])

    def test_assess_information_system_level_tier5(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.assess_information_system_level(
            system_name="Hệ thống Cơ yếu Tối mật Quốc gia",
            organization="Ban Cơ yếu Chính phủ",
            data_classification="TOPSECRET_TUYETMAT",
            service_scale="NATIONAL_CRITICAL",
        )

        assert res["recommended_level"] == 5
        assert res["audit_frequency_months"] == 6
        assert res["is_national_critical_infrastructure"] is True
        assert any("Ban Cơ yếu Chính phủ" in c for c in res["mandatory_controls"])

    def test_assess_information_system_level_tier4(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.assess_information_system_level(
            system_name="Lưới điện Quốc gia SCADA",
            organization="Tập đoàn Điện lực Việt Nam",
            data_classification="SECRET_TOIMAT",
            service_scale="NATIONAL_INFRASTRUCTURE",
        )

        assert res["recommended_level"] == 4
        assert res["audit_frequency_months"] == 6
        assert res["is_national_critical_infrastructure"] is True
        assert any("Air-Gap" in c for c in res["mandatory_controls"])

    def test_assess_information_system_level_tier3(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.assess_information_system_level(
            system_name="Cổng Thanh toán Điện tử",
            organization="Ngân hàng TMCP Sài Gòn",
            data_classification="CONFIDENTIAL_MAT",
            service_scale="NATIONAL",
        )

        assert res["recommended_level"] == 3
        assert res["audit_frequency_months"] == 12
        assert res["is_national_critical_infrastructure"] is False
        assert any("SOC/SIEM" in c for c in res["mandatory_controls"])

    def test_assess_information_system_level_tier1_and_tier2(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res2 = engine.assess_information_system_level(
            system_name="Cổng Dịch vụ công Cấp huyện",
            organization="UBND Huyện",
            data_classification="INTERNAL",
            service_scale="PROVINCIAL",
        )
        assert res2["recommended_level"] == 2
        assert res2["audit_frequency_months"] == 12

        res1 = engine.assess_information_system_level(
            system_name="Hệ thống Chấm công Nội bộ",
            organization="Công ty TNHH May mặc",
            data_classification="PUBLIC",
            service_scale="INTERNAL_ORG",
        )
        assert res1["recommended_level"] == 1
        assert res1["audit_frequency_months"] == 24

    def test_report_cyber_incident_timely(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.report_cyber_incident(
            incident_title="Tấn công DDoS làm nghẽn Cổng Dịch vụ công",
            system_name="Cổng Dịch vụ công Quốc gia",
            severity_level="HIGH",
            attack_vector="DDOS",
            affected_hosts_count=50,
            data_breached=False,
            reported_to_vncert_within_24h=True,
        )

        assert res["report_id"].startswith("CYB-INC-")
        assert "COORDINATING_RESPONSE" in res["status"]
        assert len(res["remediation_steps"]) >= 4

    def test_report_cyber_incident_late(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.report_cyber_incident(
            incident_title="Rò rỉ CSDL Khách hàng do lỗi SQL Injection",
            system_name="Cơ sở Dữ liệu Khách hàng",
            severity_level="CRITICAL",
            attack_vector="SQLI_DATALEAK",
            affected_hosts_count=2,
            data_breached=True,
            reported_to_vncert_within_24h=False,
        )

        assert "WARNING_LATE_REPORTING" in res["status"]
        assert res["data_breached"] is True

    def test_license_cybersecurity_service_firm_eligible(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.license_cybersecurity_service_firm(
            firm_name="Công ty An toàn Thông tin Mekong",
            director_name="Trần Văn An",
            certified_engineers_count=5,
            has_specialized_lab=True,
            service_scope="SECURITY_AUDIT_AND_MONITORING",
        )

        assert res["is_eligible"] is True
        assert res["validity_years"] == 10
        assert len(res["deficiencies"]) == 0
        assert res["license_id"].startswith("CYB-LIC-")

    def test_license_cybersecurity_service_firm_ineligible(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        res = engine.license_cybersecurity_service_firm(
            firm_name="Công ty Tin học Nhỏ",
            director_name="Lê Văn Bình",
            certified_engineers_count=1,
            has_specialized_lab=False,
            service_scope="PENETRATION_TESTING",
        )

        assert res["is_eligible"] is False
        assert res["validity_years"] == 0
        assert len(res["deficiencies"]) == 2

    def test_list_records_and_status(self, temp_db):
        engine = CyberEngine(db_path=temp_db)
        engine.audit_data_localization(service_name="Service 1")
        engine.assess_information_system_level(system_name="System 1", organization="Org 1")
        engine.report_cyber_incident(incident_title="Incident 1", system_name="System 1")
        engine.license_cybersecurity_service_firm(firm_name="Firm 1", director_name="Dir 1")

        all_records = engine.list_records("all")
        assert len(all_records) >= 4

        loc_records = engine.list_records("localizations")
        assert len(loc_records) >= 1
        assert loc_records[0]["type"] == "localization"

        lvl_records = engine.list_records("levels")
        assert len(lvl_records) >= 1
        assert lvl_records[0]["type"] == "security_level"

        inc_records = engine.list_records("incidents")
        assert len(inc_records) >= 1
        assert inc_records[0]["type"] == "incident"

        lic_records = engine.list_records("licenses")
        assert len(lic_records) >= 1
        assert lic_records[0]["type"] == "service_license"

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_data_localization_audits"] >= 1
        assert status["total_systems_classified_by_level"] >= 1
        assert status["total_cyber_incidents_handled"] >= 1
        assert status["licensed_cybersecurity_firms"] >= 1


class TestCyberCLI:
    """Tests Typer CLI interface for mekong cyber."""

    def test_cyber_status_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cyber"])
        assert result.exit_code == 0
        assert "AN NINH MẠNG" in result.output or "Cybersecurity" in result.output

    def test_cyber_status_json(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cyber", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "regulatory_framework" in data

    def test_cyber_localize_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "cyber",
                "localize",
                "Mekong Enterprise Cloud",
                "--type", "DOMESTIC_ENTERPRISE",
                "--retention", "36",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["service_name"] == "Mekong Enterprise Cloud"
        assert data["is_compliant"] is True

    def test_cyber_level_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "cyber",
                "level",
                "Hệ thống Điều khiển Trung tâm Hàng không",
                "--org", "Tổng công ty Quản lý bay",
                "--data-class", "SECRET_TOIMAT",
                "--scale", "NATIONAL_CRITICAL",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["recommended_level"] in (4, 5)
        assert data["is_national_critical_infrastructure"] is True

    def test_cyber_incident_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "cyber",
                "incident",
                "Mã độc tống tiền khóa máy chủ kế toán",
                "--system", "Máy chủ Kế toán",
                "--severity", "HIGH",
                "--vector", "RANSOMWARE",
                "--hosts", "5",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "CYB-INC-" in data["report_id"]
        assert data["affected_hosts_count"] == 5

    def test_cyber_license_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "cyber",
                "license",
                "Công ty An ninh mạng CyberGuard",
                "--director", "Đỗ Hữu Trí",
                "--engineers", "4",
                "--scope", "SOC_MONITORING",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_eligible"] is True
        assert data["validity_years"] == 10

    def test_cyber_list_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["cyber", "list", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestCyberMCP:
    """Tests dual MCP handlers for cybersecurity tools."""

    def test_core_mcp_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-cyber-core")

        # Localize
        res1 = json.loads(server._handle_cyber_localize(service_name="MCP Test Cloud"))
        assert res1["service_name"] == "MCP Test Cloud"
        assert res1["is_compliant"] is True

        # Level
        res2 = json.loads(server._handle_cyber_level(system_name="MCP Core Bank", service_scale="NATIONAL"))
        assert res2["recommended_level"] == 3

        # Incident
        res3 = json.loads(server._handle_cyber_incident(incident_title="MCP Ransomware Test"))
        assert "CYB-INC-" in res3["report_id"]

        # License
        res4 = json.loads(server._handle_cyber_license(firm_name="MCP Sec Firm"))
        assert res4["is_eligible"] is True

        # List
        res5 = json.loads(server._handle_cyber_list(category="all", limit=5))
        assert isinstance(res5, list)

        # Status
        res6 = json.loads(server._handle_cyber_status())
        assert res6["status"] == "operational"

    def test_scripts_mcp_handlers(self):
        from scripts.mcp_server import (
            handle_cyber_incident,
            handle_cyber_level,
            handle_cyber_license,
            handle_cyber_list,
            handle_cyber_localize,
            handle_cyber_status,
        )

        res1 = json.loads(handle_cyber_localize({"service_name": "Fallback Script Cloud"}))
        assert res1["service_name"] == "Fallback Script Cloud"

        res2 = json.loads(handle_cyber_level({"system_name": "Fallback Script Bank"}))
        assert "recommended_level" in res2

        res3 = json.loads(handle_cyber_incident({"incident_title": "Fallback Script Incident"}))
        assert "CYB-INC-" in res3["report_id"]

        res4 = json.loads(handle_cyber_license({"firm_name": "Fallback Script Sec Firm"}))
        assert "is_eligible" in res4

        res5 = json.loads(handle_cyber_list({"category": "all", "limit": 5}))
        assert isinstance(res5, list)

        res6 = json.loads(handle_cyber_status({}))
        assert res6["status"] == "operational"
