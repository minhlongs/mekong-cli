# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Labor Code 2019, Foreign Work Permit & Safety Compliance Engine (Phase 56)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.labor_engine import (
    POSITION_CATEGORIES,
    EXEMPTION_MIN_CAPITAL_VND,
    MAX_OVERTIME_HOURS_PER_MONTH,
    STANDARD_MAX_OVERTIME_HOURS_PER_YEAR,
    EXTENDED_MAX_OVERTIME_HOURS_PER_YEAR,
    MIN_EMPLOYEES_FOR_MANDATORY_REGULATIONS,
    LaborEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestLaborCoreBoundary:
    """Ensure LaborEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/labor_engine.py")
        assert source_path.exists(), "labor_engine.py must exist"

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


class TestLaborEngine:
    """Test LaborEngine work permit evaluation, overtime calculations, caps, severance, and regulations."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> LaborEngine:
        db_file = tmp_path / "test_labor.db"
        return LaborEngine(db_path=db_file)

    def test_constants_and_thresholds(self) -> None:
        assert "EXPERT" in POSITION_CATEGORIES
        assert "EXECUTIVE_DIRECTOR" in POSITION_CATEGORIES
        assert "MANAGING_DIRECTOR" in POSITION_CATEGORIES
        assert "TECHNICAL_WORKER" in POSITION_CATEGORIES
        assert EXEMPTION_MIN_CAPITAL_VND == 3_000_000_000.0
        assert MAX_OVERTIME_HOURS_PER_MONTH == 40.0
        assert STANDARD_MAX_OVERTIME_HOURS_PER_YEAR == 200.0
        assert EXTENDED_MAX_OVERTIME_HOURS_PER_YEAR == 300.0
        assert MIN_EMPLOYEES_FOR_MANDATORY_REGULATIONS == 10

    def test_work_permit_expert_qualified(self, engine: LaborEngine) -> None:
        res = engine.evaluate_work_permit_eligibility(
            worker_name="Michael Chen",
            nationality="Singapore",
            position_category="EXPERT",
            job_title="Senior AI Architect",
            education_degree="MASTER OF COMPUTER SCIENCE",
            experience_years=5.0,
        )
        assert res["ok"] is True
        assert res["worker_id"].startswith("FW-")
        assert res["eligibility_status"] == "QUALIFIED"
        assert res["is_exempt_from_work_permit"] is False
        assert len(res["statutory_dossier_checklist"]) >= 5

    def test_work_permit_expert_disqualified(self, engine: LaborEngine) -> None:
        res = engine.evaluate_work_permit_eligibility(
            worker_name="John Junior",
            nationality="United States",
            position_category="EXPERT",
            job_title="Junior Analyst",
            education_degree="HIGH_SCHOOL",
            experience_years=1.0,
        )
        assert res["ok"] is True
        assert res["eligibility_status"] == "DISQUALIFIED"
        assert res["is_exempt_from_work_permit"] is False

    def test_work_permit_exemption_capital(self, engine: LaborEngine) -> None:
        res = engine.evaluate_work_permit_eligibility(
            worker_name="Takahashi Kenji",
            nationality="Japan",
            position_category="MANAGING_DIRECTOR",
            job_title="General Director & Investor",
            capital_contribution_vnd=4_000_000_000.0,
        )
        assert res["ok"] is True
        assert res["is_exempt_from_work_permit"] is True
        assert res["eligibility_status"] == "QUALIFIED"
        assert "Mẫu số 10/PLI" in res["statutory_procedure"]

    def test_work_permit_exemption_wto_and_marriage(self, engine: LaborEngine) -> None:
        # WTO internal transfer
        wto_res = engine.evaluate_work_permit_eligibility(
            worker_name="Marie Dupont",
            nationality="France",
            position_category="EXECUTIVE_DIRECTOR",
            job_title="Finance Controller",
            is_wto_internal_transfer=True,
        )
        assert wto_res["is_exempt_from_work_permit"] is True

        # Married to Vietnamese
        m_res = engine.evaluate_work_permit_eligibility(
            worker_name="Hans Schmidt",
            nationality="Germany",
            position_category="EXPERT",
            job_title="Technical Lead",
            married_to_vietnamese=True,
        )
        assert m_res["is_exempt_from_work_permit"] is True

    def test_calculate_overtime_pay_article_98(self, engine: LaborEngine) -> None:
        # Base hourly rate: 100,000 VND
        # Normal OT 10h (150%) = 1,500,000
        # Weekend OT 5h (200%) = 1,000,000
        # Holiday OT 2h (300%) = 600,000
        # Night regular 8h (+30%) = 240,000
        # Night OT 3h (200%) = 600,000
        # Total = 3,940,000 VND
        res = engine.calculate_overtime_pay(
            hourly_rate_vnd=100_000.0,
            normal_day_ot_hours=10.0,
            weekend_ot_hours=5.0,
            holiday_ot_hours=2.0,
            night_shift_regular_hours=8.0,
            night_shift_ot_hours=3.0,
        )
        assert res["ok"] is True
        assert res["base_hourly_rate_vnd"] == 100_000.0
        assert res["total_overtime_pay_vnd"] == 3_940_000
        assert res["total_overtime_hours"] == 20.0
        assert "Điều 98" in res["governing_article"]

    def test_validate_overtime_caps_compliant(self, engine: LaborEngine) -> None:
        res = engine.validate_overtime_caps(
            monthly_overtime_hours=30.0,
            yearly_cumulative_hours=150.0,
            is_extended_industry=False,
        )
        assert res["ok"] is True
        assert res["is_compliant"] is True
        assert len(res["violations"]) == 0

    def test_validate_overtime_caps_violations(self, engine: LaborEngine) -> None:
        res = engine.validate_overtime_caps(
            monthly_overtime_hours=45.0,  # exceeds 40h/mo
            yearly_cumulative_hours=210.0,  # exceeds standard 200h/yr
            is_extended_industry=False,
        )
        assert res["ok"] is True
        assert res["is_compliant"] is False
        assert len(res["violations"]) == 2

    def test_validate_overtime_caps_extended_industry(self, engine: LaborEngine) -> None:
        # 250h is violation for standard, but compliant for extended (<=300h)
        res = engine.validate_overtime_caps(
            monthly_overtime_hours=35.0,
            yearly_cumulative_hours=250.0,
            is_extended_industry=True,
        )
        assert res["ok"] is True
        assert res["is_compliant"] is True
        assert res["yearly_cap"] == 300.0

    def test_calculate_severance_article_46(self, engine: LaborEngine) -> None:
        # Salary 20,000,000 VND
        # Total 60 months (5 yrs), BHTN 36 months (3 yrs) -> 24 months qualifying (2 yrs)
        # 2 years * 20,000,000 * 0.5 = 20,000,000 VND
        res = engine.calculate_termination_allowance(
            average_salary_vnd=20_000_000.0,
            total_working_months=60,
            bhtn_working_months=36,
            termination_type="SEVERANCE",
        )
        assert res["ok"] is True
        assert res["qualifying_months_not_covered_by_bhtn"] == 24
        assert res["calculated_tenure_years"] == 2.0
        assert res["statutory_allowance_vnd"] == 20_000_000
        assert "Điều 46" in res["governing_article"]

    def test_calculate_job_loss_article_47(self, engine: LaborEngine) -> None:
        # Salary 25,000,000 VND
        # Total 24 months, BHTN 12 months -> 12 months (1 yr)
        # Under Article 47, guaranteed minimum is 2 months salary = 50,000,000 VND
        res = engine.calculate_termination_allowance(
            average_salary_vnd=25_000_000.0,
            total_working_months=24,
            bhtn_working_months=12,
            termination_type="JOB_LOSS",
        )
        assert res["ok"] is True
        assert res["statutory_allowance_vnd"] == 50_000_000  # min 2 months guaranteed
        assert "Điều 47" in res["governing_article"]

    def test_audit_internal_regulations_compliant(self, engine: LaborEngine) -> None:
        res = engine.audit_internal_regulations(
            enterprise_name="Tập đoàn Sản xuất Mekong",
            total_employees=50,
            has_written_regulations=True,
            is_registered_with_dolab=True,
        )
        assert res["ok"] is True
        assert res["compliance_status"] == "FULLY_COMPLIANT"
        assert res["mandatory_filing_required"] is True

    def test_audit_internal_regulations_non_compliant(self, engine: LaborEngine) -> None:
        res = engine.audit_internal_regulations(
            enterprise_name="Công ty May Mặc Đông Đô",
            total_employees=25,
            has_written_regulations=True,
            is_registered_with_dolab=False,
        )
        assert res["ok"] is True
        assert res["compliance_status"] == "NON_COMPLIANT"
        assert any("CHƯA ĐĂNG KÝ" in n for n in res["statutory_notes"])

    def test_list_and_status(self, engine: LaborEngine) -> None:
        engine.evaluate_work_permit_eligibility(
            worker_name="Test Worker",
            nationality="Canada",
            position_category="EXPERT",
            job_title="Consultant",
        )
        workers = engine.list_workers()
        assert len(workers) >= 1

        apps = engine.list_applications()
        assert len(apps) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["total_foreign_workers_assessed"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestLaborCLI:
    """Test mekong labor Typer CLI commands."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_dashboard(self) -> None:
        result = runner.invoke(self.app, ["labor"])
        assert result.exit_code == 0
        assert "HỆ THỐNG PHÁP LUẬT LAO ĐỘNG" in result.output

    def test_cli_status_json(self) -> None:
        result = runner.invoke(self.app, ["labor", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "regulatory_framework" in data

    def test_cli_permit_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "labor",
                "permit",
                "Alex Rivera",
                "Spain",
                "EXPERT",
                "Senior Architect",
                "--degree",
                "MASTER",
                "--exp",
                "4",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["worker_name"] == "Alex Rivera"
        assert data["eligibility_status"] == "QUALIFIED"

    def test_cli_overtime_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "labor",
                "overtime",
                "120000",
                "--day",
                "8",
                "--weekend",
                "4",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["total_overtime_pay_vnd"] > 0

    def test_cli_caps_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "labor",
                "caps",
                "32",
                "160",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_compliant"] is True

    def test_cli_severance_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "labor",
                "severance",
                "18000000",
                "60",
                "36",
                "--type",
                "SEVERANCE",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["statutory_allowance_vnd"] == 18_000_000

    def test_cli_regulations_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "labor",
                "regulations",
                "Công ty TNHH Phần mềm Nam Á",
                "30",
                "--registered",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["compliance_status"] == "FULLY_COMPLIANT"

    def test_cli_list_json(self) -> None:
        result = runner.invoke(self.app, ["labor", "list", "--type", "permits", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "applications" in data


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestLaborMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for labor tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_labor_permit")
        assert hasattr(server, "_handle_labor_overtime")
        assert hasattr(server, "_handle_labor_caps")
        assert hasattr(server, "_handle_labor_severance")
        assert hasattr(server, "_handle_labor_regulations")
        assert hasattr(server, "_handle_labor_list")
        assert hasattr(server, "_handle_labor_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_labor_permit",
            "mekong_labor_overtime",
            "mekong_labor_caps",
            "mekong_labor_severance",
            "mekong_labor_regulations",
            "mekong_labor_list",
            "mekong_labor_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        handler = CORE_HANDLERS["mekong_labor_permit"]
        raw = handler({
            "worker_name": "Oliver Twist",
            "nationality": "UK",
            "position": "EXPERT",
            "job_title": "Lead Engineer",
            "degree": "BACHELOR",
            "exp": 4.0,
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["worker_name"] == "Oliver Twist"
        assert res["eligibility_status"] == "QUALIFIED"

        ot_handler = CORE_HANDLERS["mekong_labor_overtime"]
        ot_raw = ot_handler({"hourly_rate": 150000.0, "weekday_ot": 5.0})
        ot_res = json.loads(ot_raw)
        assert ot_res["ok"] is True
        assert ot_res["total_overtime_pay_vnd"] == 1_125_000
