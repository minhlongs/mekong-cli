# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Vietnamese Social Insurance (BHXH, BHYT, BHTN) Contribution & Declaration Engine (Phase 42)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_bhxh_calc,
    handle_bhxh_declaration,
    handle_bhxh_employees,
    handle_bhxh_status,
)
from src.cli.app_setup import build_app
from src.core.bhxh_engine import (
    BASE_SALARY_2024,
    CANONICAL_EMPLOYEES,
    CEILING_BHXH_BHYT,
    BhxhEngine,
    format_vnd,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


class TestBhxhEngine:
    """Unit test battery for BhxhEngine core business logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> BhxhEngine:
        db_file = tmp_path / "test_bhxh.db"
        return BhxhEngine(db_path=db_file)

    def test_engine_init_and_default_employees(self, engine: BhxhEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_employees"] == len(CANONICAL_EMPLOYEES)
        assert status["total_calculations"] == 0
        assert status["total_declarations"] == 0
        assert status["statutory_regulations"]["base_salary_vnd"] == BASE_SALARY_2024
        assert status["statutory_regulations"]["ceiling_bhxh_bhyt_vnd"] == CEILING_BHXH_BHYT

    def test_format_vnd(self) -> None:
        formatted = format_vnd(25000000)
        assert "25.000.000 đ" in formatted

    def test_calculate_contribution_standard(self, engine: BhxhEngine) -> None:
        # Salary: 20M, Region 1, No KPCD
        res = engine.calculate_contribution(salary=20000000, region=1, include_kpcd=False)
        assert res["ok"] is True
        assert res["salary_gross"] == 20000000.0
        assert res["is_capped"] is False
        assert res["region"] == 1

        # Employee: 8% + 1.5% + 1% = 10.5% (2.1M)
        emp = res["employee"]
        assert emp["bhxh_8pct"] == 1600000.0
        assert emp["bhyt_1_5pct"] == 300000.0
        assert emp["bhtn_1pct"] == 200000.0
        assert emp["total"] == 2100000.0
        assert emp["effective_rate_pct"] == 10.5

        # Employer: 17.5% + 3% + 1% = 21.5% (4.3M)
        dn = res["employer"]
        assert dn["bhxh_17_5pct"] == 3500000.0
        assert dn["bhyt_3pct"] == 600000.0
        assert dn["bhtn_1pct"] == 200000.0
        assert dn["kpcd_2pct"] == 0.0
        assert dn["total"] == 4300000.0
        assert dn["effective_rate_pct"] == 21.5

        assert res["total_contribution"] == 6400000.0
        assert res["net_salary_estimated"] == 17900000.0

    def test_calculate_contribution_with_kpcd(self, engine: BhxhEngine) -> None:
        # Salary: 20M, Include KPCD (2% employer = 400,000 đ)
        res = engine.calculate_contribution(salary=20000000, region=1, include_kpcd=True)
        assert res["include_kpcd"] is True
        assert res["employer"]["kpcd_2pct"] == 400000.0
        assert res["employer"]["total"] == 4700000.0
        assert res["total_contribution"] == 6800000.0

    def test_calculate_contribution_above_ceiling(self, engine: BhxhEngine) -> None:
        # Salary: 60M (above 46.8M ceiling for BHXH/BHYT)
        res = engine.calculate_contribution(salary=60000000, region=1)
        assert res["is_capped"] is True
        assert res["salary_capped_bhxh"] == 46800000.0
        assert res["salary_capped_bhtn"] == 60000000.0

        # Employee BHXH: 46.8M * 8% = 3,744,000 đ
        # Employee BHYT: 46.8M * 1.5% = 702,000 đ
        # Employee BHTN: 60M * 1% = 600,000 đ
        emp = res["employee"]
        assert emp["bhxh_8pct"] == 3744000.0
        assert emp["bhyt_1_5pct"] == 702000.0
        assert emp["bhtn_1pct"] == 600000.0
        assert emp["total"] == 5046000.0

        # Employer BHXH: 46.8M * 17.5% = 8,190,000 đ
        # Employer BHYT: 46.8M * 3% = 1,404,000 đ
        # Employer BHTN: 60M * 1% = 600,000 đ
        dn = res["employer"]
        assert dn["bhxh_17_5pct"] == 8190000.0
        assert dn["bhyt_3pct"] == 1404000.0
        assert dn["bhtn_1pct"] == 600000.0
        assert dn["total"] == 10194000.0
        assert res["total_contribution"] == 15240000.0

    def test_list_and_add_employee(self, engine: BhxhEngine) -> None:
        emps = engine.list_employees(status="all")
        assert len(emps) == len(CANONICAL_EMPLOYEES)

        res = engine.add_employee(
            full_name="Võ Tấn Phát",
            bhxh_code="7988889999",
            salary_insurance=18000000.0,
            region=1,
            department="Product",
        )
        assert res["ok"] is True
        assert res["bhxh_code"] == "7988889999"

        updated = engine.list_employees()
        assert len(updated) == len(CANONICAL_EMPLOYEES) + 1

    def test_create_declaration_d02lt(self, engine: BhxhEngine) -> None:
        res = engine.create_declaration_d02lt(
            change_type="bao_tang",
            employee_id="EMP-001",
            effective_month="11/2026",
            note="Tuyển dụng mới tháng 11",
        )
        assert res["ok"] is True
        assert res["doc_code"] == "D02-LT"
        assert res["change_type"] == "bao_tang"
        assert res["employee_id"] == "EMP-001"
        assert res["full_name"] == "Nguyễn Văn An"
        assert res["status"] == "ready_to_submit"
        assert "D02-" in res["declaration_id"]

        status = engine.get_status()
        assert status["total_declarations"] == 1


class TestBhxhCli:
    """CLI test battery for mekong bhxh command hierarchy."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_bhxh_overview_console(self, app) -> None:
        res = runner.invoke(app, ["bhxh"])
        assert res.exit_code == 0
        assert "Bảo Hiểm Xã Hội Việt Nam" in res.output or "BHXH" in res.output

    def test_bhxh_overview_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["status"] == "operational"
        assert data["total_employees"] >= 5

    def test_bhxh_calc_console(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "calc", "20000000"])
        assert res.exit_code == 0
        assert "Chi Tiết Trích Nộp BHXH" in res.output

    def test_bhxh_calc_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "calc", "25000000", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["salary_gross"] == 25000000.0
        assert data["total_contribution"] == 8000000.0

    def test_bhxh_calc_with_kpcd_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "calc", "25000000", "--kpcd", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["include_kpcd"] is True
        assert data["employer"]["kpcd_2pct"] == 500000.0

    def test_bhxh_employees_console(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "employees"])
        assert res.exit_code == 0
        assert "Nguyễn Văn An" in res.output

    def test_bhxh_employees_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "employees", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total"] >= 5
        assert len(data["employees"]) >= 5

    def test_bhxh_declaration_console(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "declaration", "bao_tang", "EMP-001"])
        assert res.exit_code == 0
        assert "D02-LT" in res.output

    def test_bhxh_declaration_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "declaration", "dieu_chinh_luong", "EMP-001", "--new-salary", "30000000", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["doc_code"] == "D02-LT"
        assert data["new_salary"] == 30000000.0

    def test_bhxh_status_json(self, app) -> None:
        res = runner.invoke(app, ["bhxh", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "statutory_regulations" in data


class TestBhxhMcpParity:
    """Test suite ensuring parity across FastMCP and pure-Python JSON-RPC 2.0 stdio engines."""

    def test_mcp_spec_registration(self) -> None:
        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        assert "mekong_bhxh_calc" in names
        assert "mekong_bhxh_employees" in names
        assert "mekong_bhxh_declaration" in names
        assert "mekong_bhxh_status" in names

    def test_script_mcp_handlers(self) -> None:
        # Status
        status_raw = handle_bhxh_status({})
        status = json.loads(status_raw)
        assert status["status"] == "operational"

        # Calc
        calc_raw = handle_bhxh_calc({"salary": 20000000, "region": 1})
        calc = json.loads(calc_raw)
        assert calc["ok"] is True
        assert calc["total_contribution"] == 6400000.0

        # Employees
        emp_raw = handle_bhxh_employees({"status": "all"})
        emps = json.loads(emp_raw)
        assert emps["total"] >= 5

        # Declaration
        dec_raw = handle_bhxh_declaration({"change_type": "bao_giam", "employee_id": "EMP-002"})
        dec = json.loads(dec_raw)
        assert dec["ok"] is True
        assert dec["change_type"] == "bao_giam"

    def test_core_mcp_server_handlers_and_aliases(self) -> None:
        server = MekongMcpServer(name="test-server")

        # Handlers
        status_res = json.loads(server._handle_bhxh_status())
        assert status_res["status"] == "operational"

        calc_res = json.loads(server._handle_bhxh_calc(salary=30000000, region=1))
        assert calc_res["ok"] is True

        emps_res = json.loads(server._handle_bhxh_employees(status="active"))
        assert emps_res["total"] >= 5

        # Aliases
        assert server._handle_mekong_bhxh_calc == server._handle_bhxh_calc
        assert server._handle_mekong_bhxh_employees == server._handle_bhxh_employees
        assert server._handle_mekong_bhxh_declaration == server._handle_bhxh_declaration
        assert server._handle_mekong_bhxh_status == server._handle_bhxh_status


class TestBhxhCoreBoundary:
    """Ensure src/core/bhxh_engine.py is pure Python standard library with zero external HTTP or vendor SDK imports."""

    def test_core_ast_imports(self) -> None:
        engine_path = Path("src/core/bhxh_engine.py")
        assert engine_path.exists()

        tree = ast.parse(engine_path.read_text(encoding="utf-8"))
        disallowed_prefixes = (
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "flask",
            "fastapi",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for disallowed in disallowed_prefixes:
                        assert not alias.name.startswith(disallowed), (
                            f"Disallowed import '{alias.name}' in pure core engine {engine_path}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for disallowed in disallowed_prefixes:
                    assert not module.startswith(disallowed), (
                        f"Disallowed from-import '{module}' in pure core engine {engine_path}"
                    )
