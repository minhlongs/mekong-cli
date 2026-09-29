# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Statutory Payroll & Compensation Engine (Phase 46)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.payroll_engine import (
    LUONG_CO_SO,
    TRAN_BHXH_BHYT,
    VUNG_MIN_WAGE,
    GIAM_TRU_BAN_THAN,
    GIAM_TRU_PHU_THUOC,
    PayrollEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPayrollCoreBoundary:
    """Ensure PayrollEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/payroll_engine.py")
        assert source_path.exists(), "payroll_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestPayrollEngine:
    """Test PayrollEngine calculation accuracy and persistence."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PayrollEngine:
        db_file = tmp_path / "test_payroll.db"
        return PayrollEngine(db_path=db_file)

    def test_regulatory_constants(self) -> None:
        assert LUONG_CO_SO == 2_340_000
        assert TRAN_BHXH_BHYT == 46_800_000
        assert VUNG_MIN_WAGE[1] == 4_960_000
        assert GIAM_TRU_BAN_THAN == 11_000_000
        assert GIAM_TRU_PHU_THUOC == 4_400_000

    def test_gross_to_net_low_salary_no_tax(self, engine: PayrollEngine) -> None:
        # Gross 10,000,000 VND, 0 dependents
        # Lunch 730,000 -> Insurable salary = 9,270,000
        # Employee insurance = 9,270,000 * 10.5% = 973,350
        # Income before tax = 10,000,000 - 973,350 = 9,026,650
        # Relief = 11,000,000 + 730,000 -> Taxable income = 0
        # PIT = 0
        # Net = 10,000,000 - 973,350 = 9,026,650
        res = engine.calculate_gross_to_net(gross=10_000_000, dependents=0, region=1)
        assert res["ok"] is True
        assert res["gross"] == 10_000_000
        assert res["tax_calculation"]["taxable_income"] == 0
        assert res["tax_calculation"]["pit_tax"] == 0
        assert res["net"] == 9_026_650
        assert res["employer_burden"]["total_cost_to_company"] > 10_000_000

    def test_gross_to_net_standard_salary_with_tax(self, engine: PayrollEngine) -> None:
        # Gross 30,000,000 VND, 1 dependent, Region 1
        res = engine.calculate_gross_to_net(gross=30_000_000, dependents=1, region=1)
        assert res["ok"] is True
        assert res["employee_deductions"]["total_insurance"] > 0
        assert res["tax_calculation"]["taxable_income"] > 0
        assert res["tax_calculation"]["pit_tax"] > 0
        assert res["net"] < 30_000_000
        assert res["net"] > 20_000_000
        assert len(res["tax_calculation"]["tier_breakdown"]) >= 1

    def test_gross_to_net_high_salary_insurance_ceiling(self, engine: PayrollEngine) -> None:
        # Gross 100,000,000 VND (exceeds 46,800,000 ceiling for BHXH/BHYT)
        res = engine.calculate_gross_to_net(gross=100_000_000, dependents=0, region=1)
        assert res["insurance_base"]["bhxh_bhyt"] == TRAN_BHXH_BHYT
        # BHXH (8%) capped at 46,800,000 * 0.08 = 3,744,000
        assert res["employee_deductions"]["bhxh_8_pct"] == 3_744_000

    def test_net_to_gross_roundtrip(self, engine: PayrollEngine) -> None:
        target_net = 25_000_000
        res = engine.calculate_net_to_gross(net=target_net, dependents=1, region=1)
        assert res["target_net"] == target_net
        # The resulting net should match target_net within 1 VND
        assert abs(res["net"] - target_net) <= 1

    def test_generate_payslip_and_status(self, engine: PayrollEngine) -> None:
        slip = engine.generate_payslip(
            employee_name="Nguyễn Văn A",
            gross=35_000_000,
            employee_id="EMP-001",
            month="2026-10",
            dependents=1,
            bonus=5_000_000,
        )
        assert slip["payslip_id"] == "PAY-2026-10-EMP-001"
        assert slip["gross"] == 40_000_000
        assert slip["net"] > 0

        records = engine.list_payslips()
        assert len(records) == 1
        assert records[0]["employee_name"] == "Nguyễn Văn A"

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["metrics"]["total_payslips_issued"] == 1
        assert status["metrics"]["total_gross_disbursed"] == 40_000_000


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestPayrollCLI:
    """Test Typer CLI commands for payroll."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_payroll_overview(self, app) -> None:
        result = runner.invoke(app, ["payroll"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ TIỀN LƯƠNG" in result.output

    def test_payroll_overview_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "statutory_rates" in data

    def test_payroll_gross_to_net_cli(self, app) -> None:
        result = runner.invoke(app, ["payroll", "gross-to-net", "25000000", "--dependents", "1"])
        assert result.exit_code == 0
        assert "KẾT QUẢ TÍNH LƯƠNG GROSS → NET" in result.output

    def test_payroll_gross_to_net_cli_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "gross-to-net", "25000000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["gross"] == 25_000_000
        assert "net" in data

    def test_payroll_net_to_gross_cli(self, app) -> None:
        result = runner.invoke(app, ["payroll", "net-to-gross", "20000000"])
        assert result.exit_code == 0
        assert "QUY ĐỔI NET → GROSS" in result.output

    def test_payroll_net_to_gross_cli_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "net-to-gross", "20000000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["target_net"] == 20_000_000
        assert data["solved_gross"] > 20_000_000

    def test_payroll_payslip_cli(self, app) -> None:
        result = runner.invoke(app, ["payroll", "payslip", "Trần Thị B", "30000000", "--id", "EMP-002"])
        assert result.exit_code == 0
        assert "PHIẾU LƯƠNG ĐIỆN TỬ" in result.output

    def test_payroll_payslip_cli_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "payslip", "Lê Văn C", "45000000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["employee_name"] == "Lê Văn C"
        assert "net" in data

    def test_payroll_list_cli(self, app) -> None:
        result = runner.invoke(app, ["payroll", "list"])
        assert result.exit_code == 0

    def test_payroll_list_cli_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "payslips" in data

    def test_payroll_status_cli(self, app) -> None:
        result = runner.invoke(app, ["payroll", "status"])
        assert result.exit_code == 0
        assert "TRẠNG THÁI HỆ THỐNG TIỀN LƯƠNG" in result.output

    def test_payroll_status_cli_json(self, app) -> None:
        result = runner.invoke(app, ["payroll", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestPayrollMCPParity:
    """Test FastMCP and scripts/mcp_server.py parity for payroll tools."""

    def test_scripts_mcp_handlers(self) -> None:
        import scripts.mcp_server as smcp

        g2n = json.loads(smcp.handle_payroll_gross_to_net({"gross": 20_000_000}))
        assert g2n["gross"] == 20_000_000
        assert g2n["net"] > 0

        n2g = json.loads(smcp.handle_payroll_net_to_gross({"net": 18_000_000}))
        assert n2g["target_net"] == 18_000_000
        assert n2g["solved_gross"] > 18_000_000

        slip = json.loads(
            smcp.handle_payroll_payslip({"employee_name": "Phạm Văn D", "gross": 22_000_000})
        )
        assert slip["employee_name"] == "Phạm Văn D"

        plist = json.loads(smcp.handle_payroll_list({}))
        assert plist["ok"] is True

        pstat = json.loads(smcp.handle_payroll_status({}))
        assert pstat["status"] == "operational"

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        g2n = json.loads(server._handle_payroll_gross_to_net(gross=28_000_000))
        assert g2n["gross"] == 28_000_000
        assert g2n["net"] > 0

        n2g = json.loads(server._handle_payroll_net_to_gross(net=25_000_000))
        assert n2g["target_net"] == 25_000_000
        assert n2g["solved_gross"] > 25_000_000

        slip = json.loads(server._handle_payroll_payslip(employee_name="Hoàng Thị E", gross=32_000_000))
        assert slip["employee_name"] == "Hoàng Thị E"

        plist = json.loads(server._handle_payroll_list())
        assert plist["ok"] is True

        pstat = json.loads(server._handle_payroll_status())
        assert pstat["status"] == "operational"
