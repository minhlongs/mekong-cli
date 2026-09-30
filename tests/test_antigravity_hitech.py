"""
Test Suite for Vietnamese High-Tech Enterprise, Science Parks & Tech Transfer Suite (Phase 88).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- HitechEngine domain logic (QĐ 10/2021/QĐ-TTg audit, tech transfer registration, KCNC project audit, tax incentives).
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
from src.core.hitech_engine import HitechEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestHitechBoundary:
    """Verifies that hitech_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "hitech_engine.py")
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


class TestHitechEngine:
    """Tests core domain logic of HitechEngine."""

    def test_audit_hitech_enterprise_qualified(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_enterprise(
            company_name="Công ty CP Bán dẫn Viễn thông Mekong",
            total_revenue_vnd=100_000_000_000.0,
            hitech_revenue_vnd=75_000_000_000.0,  # 75% >= 70%
            rd_spending_vnd=2_000_000_000.0,       # 2% >= 1% for MEDIUM
            total_employees=200,
            rd_employees=15,                       # 7.5% >= 5%
            has_iso9001=True,
            enterprise_scale="MEDIUM",
        )
        assert res["status"] == "QUALIFIED_HITECH_ENTERPRISE"
        assert res["is_qualified"] is True
        assert res["hitech_ratio_pct"] == 75.0
        assert res["rd_ratio_pct"] == 2.0
        assert res["rd_employee_ratio_pct"] == 7.5
        assert len(res["deficiencies"]) == 0
        assert res["certificate_code"].startswith("CNC-")

    def test_audit_hitech_enterprise_deficient_revenue(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_enterprise(
            company_name="Công ty Công nghệ Thiếu Chuẩn",
            total_revenue_vnd=100_000_000_000.0,
            hitech_revenue_vnd=60_000_000_000.0,  # 60% < 70%
            rd_spending_vnd=2_000_000_000.0,
            total_employees=200,
            rd_employees=15,
            has_iso9001=True,
            enterprise_scale="MEDIUM",
        )
        assert res["status"] == "DEFICIENT_CONDITIONS"
        assert res["is_qualified"] is False
        assert any("thấp hơn mức tối thiểu 70%" in d for d in res["deficiencies"])

    def test_audit_hitech_enterprise_deficient_rd_spending_small(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        # Small enterprise requires >= 2.0% R&D spending
        res = engine.audit_hitech_enterprise(
            company_name="Công ty Phần mềm Nhỏ",
            total_revenue_vnd=20_000_000_000.0,
            hitech_revenue_vnd=18_000_000_000.0,  # 90%
            rd_spending_vnd=200_000_000.0,         # 1.0% < 2.0%
            total_employees=50,
            rd_employees=5,                        # 10%
            has_iso9001=True,
            enterprise_scale="SMALL",
        )
        assert res["status"] == "DEFICIENT_CONDITIONS"
        assert res["is_qualified"] is False
        assert any("ngưỡng quy định (2.0%)" in d for d in res["deficiencies"])

    def test_audit_hitech_enterprise_deficient_rd_staff(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_enterprise(
            company_name="Công ty Thiếu Nhân Lực R&D",
            total_revenue_vnd=100_000_000_000.0,
            hitech_revenue_vnd=80_000_000_000.0,
            rd_spending_vnd=2_000_000_000.0,
            total_employees=200,
            rd_employees=6,  # 3.0% < 5.0%
            has_iso9001=True,
            enterprise_scale="MEDIUM",
        )
        assert res["is_qualified"] is False
        assert any("thấp hơn mức tối thiểu 5.0%" in d for d in res["deficiencies"])

    def test_audit_hitech_enterprise_missing_iso9001(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_enterprise(
            company_name="Công ty Chưa Có ISO",
            total_revenue_vnd=100_000_000_000.0,
            hitech_revenue_vnd=85_000_000_000.0,
            rd_spending_vnd=3_000_000_000.0,
            total_employees=100,
            rd_employees=10,
            has_iso9001=False,
            enterprise_scale="MEDIUM",
        )
        assert res["is_qualified"] is False
        assert any("tiêu chuẩn ISO 9001" in d for d in res["deficiencies"])

    def test_register_tech_transfer_inward_foreign_compliant(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.register_tech_transfer_contract(
            contract_title="Chuyển giao công nghệ bán dẫn 7nm",
            transferor="Tokyo Semi Corp",
            transferee="Mekong Semi JSC",
            technology_name="Quy trình quang khắc EUV",
            transfer_direction="INWARD_FOREIGN",
            contract_value_usd=1_500_000.0,
            uses_state_capital=False,
            technology_category="ENCOURAGED",
        )
        assert res["status"] == "REGISTERED_COMPLIANT"
        assert res["is_mandatory_registration"] is True
        assert res["is_approved"] is True
        assert res["estimated_fine_vnd"] == 0.0
        assert res["registration_code"].startswith("DKCG-")

    def test_register_tech_transfer_prohibited_technology(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.register_tech_transfer_contract(
            contract_title="Chuyển giao công nghệ phát thải độc hại",
            transferor="Overseas Chemical Corp",
            transferee="Công ty CP Hóa chất Độc",
            technology_name="Công nghệ luyện chì thủ công lạc hậu",
            transfer_direction="INWARD_FOREIGN",
            contract_value_usd=200_000.0,
            uses_state_capital=False,
            technology_category="PROHIBITED",
        )
        assert res["status"] == "PROHIBITED_TECHNOLOGY_ILLEGAL"
        assert res["is_approved"] is False
        assert res["estimated_fine_vnd"] == 90_000_000.0
        assert "BỊ CẤM CHUYỂN GIAO" in res["legal_status"]

    def test_register_tech_transfer_domestic_voluntary(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.register_tech_transfer_contract(
            contract_title="Chuyển giao giải pháp ERP nội bộ",
            transferor="Công ty Tin học ABC",
            transferee="Công ty May mặc XYZ",
            technology_name="Phần mềm quản trị sản xuất",
            transfer_direction="DOMESTIC",
            contract_value_usd=50_000.0,
            uses_state_capital=False,
            technology_category="ENCOURAGED",
        )
        assert res["status"] == "VOLUNTARY_REGISTERED"
        assert res["is_mandatory_registration"] is False
        assert res["is_approved"] is True

    def test_audit_hitech_park_project_approved(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_park_project(
            project_name="Nhà máy bao bì bán dẫn tiên tiến",
            park_name="Khu Công Nghệ Cao TP. Hồ Chí Minh (SHTP)",
            land_area_ha=5.0,
            investment_capital_vnd=650_000_000_000.0,  # 130B/ha >= 100B/ha
            export_ratio_pct=90.0,
            commits_tech_transfer=True,
        )
        assert res["status"] == "APPROVED_FOR_HITECH_PARK"
        assert res["is_approved"] is True
        assert res["capital_per_ha_vnd"] == 130_000_000_000.0
        assert len(res["deficiencies"]) == 0
        assert res["project_code"].startswith("KCNC-")

    def test_audit_hitech_park_project_insufficient_density(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_park_project(
            project_name="Xưởng lắp ráp tiêu chuẩn thấp",
            park_name="Khu Công Nghệ Cao Hòa Lạc",
            land_area_ha=10.0,
            investment_capital_vnd=600_000_000_000.0,  # 60B/ha < 100B/ha
            export_ratio_pct=80.0,
            commits_tech_transfer=True,
        )
        assert res["status"] == "INSUFFICIENT_INVESTMENT_DENSITY"
        assert res["is_approved"] is False
        assert any("thấp hơn ngưỡng tối thiểu 100 tỷ VND/ha" in d for d in res["deficiencies"])

    def test_audit_hitech_park_project_no_tech_transfer(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.audit_hitech_park_project(
            project_name="Dự án không cam kết chuyển giao",
            park_name="Khu Công Nghệ Cao Đà Nẵng",
            land_area_ha=2.0,
            investment_capital_vnd=300_000_000_000.0,  # 150B/ha >= 100B/ha
            export_ratio_pct=85.0,
            commits_tech_transfer=False,
        )
        assert res["is_approved"] is False
        assert any("chưa cam kết lộ trình chuyển giao công nghệ" in d for d in res["deficiencies"])

    def test_calculate_tax_incentives_exempt_phase(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        # Year 3: 100% tax exemption (0%)
        res = engine.calculate_tax_incentives(
            company_name="Mekong Chip JSC",
            profit_before_tax_vnd=100_000_000_000.0,
            operating_year=3,
            is_certified_hitech=True,
        )
        assert res["applied_tax_rate_pct"] == 0.0
        assert res["incentive_tax_vnd"] == 0.0
        assert res["tax_saved_vnd"] == 20_000_000_000.0
        assert res["status"] == "INCENTIVE_APPLIED"

    def test_calculate_tax_incentives_50pct_reduction_phase(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        # Year 6: 50% of 10% = 5%
        res = engine.calculate_tax_incentives(
            company_name="Mekong Chip JSC",
            profit_before_tax_vnd=100_000_000_000.0,
            operating_year=6,
            is_certified_hitech=True,
        )
        assert res["applied_tax_rate_pct"] == 5.0
        assert res["incentive_tax_vnd"] == 5_000_000_000.0
        assert res["tax_saved_vnd"] == 15_000_000_000.0

    def test_calculate_tax_incentives_preferential_10pct_phase(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        # Year 14: 10%
        res = engine.calculate_tax_incentives(
            company_name="Mekong Chip JSC",
            profit_before_tax_vnd=100_000_000_000.0,
            operating_year=14,
            is_certified_hitech=True,
        )
        assert res["applied_tax_rate_pct"] == 10.0
        assert res["incentive_tax_vnd"] == 10_000_000_000.0
        assert res["tax_saved_vnd"] == 10_000_000_000.0

    def test_calculate_tax_incentives_non_hitech(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        res = engine.calculate_tax_incentives(
            company_name="Doanh nghiệp thường",
            profit_before_tax_vnd=50_000_000_000.0,
            operating_year=2,
            is_certified_hitech=False,
        )
        assert res["applied_tax_rate_pct"] == 20.0
        assert res["incentive_tax_vnd"] == 10_000_000_000.0
        assert res["tax_saved_vnd"] == 0.0
        assert res["status"] == "STANDARD_TAX"

    def test_list_records_and_status(self, temp_db):
        engine = HitechEngine(db_path=temp_db)
        engine.audit_hitech_enterprise(
            company_name="Test Enterprise",
            total_revenue_vnd=100_000_000_000.0,
            hitech_revenue_vnd=80_000_000_000.0,
            rd_spending_vnd=2_000_000_000.0,
            total_employees=100,
            rd_employees=10,
        )
        engine.register_tech_transfer_contract(
            contract_title="Test Contract",
            transferor="A",
            transferee="B",
            technology_name="Tech X",
        )
        engine.audit_hitech_park_project(
            project_name="Test Project",
            park_name="SHTP",
            land_area_ha=1.0,
            investment_capital_vnd=150_000_000_000.0,
        )
        engine.calculate_tax_incentives(
            company_name="Test Enterprise",
            profit_before_tax_vnd=10_000_000_000.0,
            operating_year=1,
        )

        ents = engine.list_records("enterprises")
        assert len(ents) >= 1
        contracts = engine.list_records("contracts")
        assert len(contracts) >= 1
        parks = engine.list_records("parks")
        assert len(parks) >= 1
        taxes = engine.list_records("taxes")
        assert len(taxes) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_hitech_enterprises_audited"] >= 1
        assert status["total_tech_transfer_contracts"] >= 1
        assert status["total_hitech_park_projects"] >= 1
        assert status["total_tax_evaluations"] >= 1


class TestHitechCLI:
    """Tests CLI commands using Typer's CliRunner."""

    def test_cli_status_and_main(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["hitech", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"

        res_main = runner.invoke(app, ["hitech"])
        assert res_main.exit_code == 0
        assert "DOANH NGHIỆP CÔNG NGHỆ CAO" in res_main.output

    def test_cli_enterprise_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "hitech",
                "enterprise",
                "Công ty Test CLI",
                "--rev",
                "100000000000",
                "--hitech-rev",
                "80000000000",
                "--rd",
                "2000000000",
                "--employees",
                "200",
                "--rd-employees",
                "20",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_qualified"] is True
        assert data["status"] == "QUALIFIED_HITECH_ENTERPRISE"

    def test_cli_transfer_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "hitech",
                "transfer",
                "Hợp đồng Test CLI",
                "--direction",
                "INWARD_FOREIGN",
                "--value",
                "800000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "REGISTERED_COMPLIANT"

    def test_cli_park_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "hitech",
                "park",
                "Dự án Vi mạch CLI",
                "--area",
                "2.0",
                "--capital",
                "300000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "APPROVED_FOR_HITECH_PARK"

    def test_cli_tax_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "hitech",
                "tax",
                "Công ty Test Thuế",
                "--profit",
                "40000000000",
                "--year",
                "2",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["applied_tax_rate_pct"] == 0.0
        assert data["tax_saved_vnd"] == 8_000_000_000.0

    def test_cli_list_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["hitech", "list", "enterprises", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestHitechMCP:
    """Tests dual FastMCP and fallback handlers for Hitech suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Audit
        res_audit = json.loads(
            server._handle_hitech_audit(
                company_name="Mekong MCP Corp",
                total_revenue_vnd=100_000_000_000.0,
                hitech_revenue_vnd=80_000_000_000.0,
            )
        )
        assert res_audit["is_qualified"] is True

        # Transfer
        res_transfer = json.loads(
            server._handle_hitech_transfer(
                contract_title="Chuyển giao MCP",
                technology_category="ENCOURAGED",
            )
        )
        assert res_transfer["is_approved"] is True

        # Park
        res_park = json.loads(
            server._handle_hitech_park(
                project_name="Dự án MCP Park",
                land_area_ha=2.0,
                investment_capital_vnd=300_000_000_000.0,
            )
        )
        assert res_park["is_approved"] is True

        # Tax
        res_tax = json.loads(
            server._handle_hitech_tax(
                company_name="Mekong MCP Corp",
                profit_before_tax_vnd=50_000_000_000.0,
                operating_year=1,
            )
        )
        assert res_tax["applied_tax_rate_pct"] == 0.0

        # List
        res_list = json.loads(server._handle_hitech_list(category="enterprises"))
        assert isinstance(res_list, list)

        # Status
        res_status = json.loads(server._handle_hitech_status())
        assert res_status["status"] == "HEALTHY"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as script_mcp

        # Test tool dictionary registration
        assert "mekong_hitech_audit" in script_mcp.CORE_HANDLERS
        assert "mekong_hitech_transfer" in script_mcp.CORE_HANDLERS
        assert "mekong_hitech_park" in script_mcp.CORE_HANDLERS
        assert "mekong_hitech_tax" in script_mcp.CORE_HANDLERS
        assert "mekong_hitech_list" in script_mcp.CORE_HANDLERS
        assert "mekong_hitech_status" in script_mcp.CORE_HANDLERS

        # Invocations
        h_audit = script_mcp.CORE_HANDLERS["mekong_hitech_audit"]
        res_audit = json.loads(h_audit({"company_name": "Script MCP Corp"}))
        assert "certificate_code" in res_audit

        h_status = script_mcp.CORE_HANDLERS["mekong_hitech_status"]
        res_status = json.loads(h_status({}))
        assert res_status["status"] == "HEALTHY"
