# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Construction Engineering, Building Permits, FIDIC Contracts & QCVN Fire Safety (Phase 66)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.construction_engine import (
    BUILDING_GRADES,
    FIDIC_CONTRACT_FORMS,
    FIRE_SAFETY_RESISTANCE_TIERS,
    ConstructionEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestConstructionCoreBoundary:
    """Ensure ConstructionEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/construction_engine.py")
        assert source_path.exists(), "construction_engine.py must exist"

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


class TestConstructionEngine:
    """Test ConstructionEngine building grades, permit exemptions, FIDIC contracts & QCVN fire audits."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> ConstructionEngine:
        db_file = tmp_path / "test_construction.db"
        return ConstructionEngine(db_path=db_file)

    def test_constants_and_building_grades(self) -> None:
        assert "SPECIAL_GRADE" in BUILDING_GRADES
        assert "GRADE_I" in BUILDING_GRADES
        assert "GRADE_II" in BUILDING_GRADES
        assert "GRADE_III" in BUILDING_GRADES
        assert "GRADE_IV" in BUILDING_GRADES

        assert "FIDIC_RED_BOOK" in FIDIC_CONTRACT_FORMS
        assert "FIDIC_YELLOW_BOOK" in FIDIC_CONTRACT_FORMS
        assert "FIDIC_SILVER_BOOK" in FIDIC_CONTRACT_FORMS

        assert "TIER_I" in FIRE_SAFETY_RESISTANCE_TIERS
        assert "TIER_II" in FIRE_SAFETY_RESISTANCE_TIERS
        assert "TIER_III" in FIRE_SAFETY_RESISTANCE_TIERS

    def test_register_construction_project_special_grade(self, engine: ConstructionEngine) -> None:
        # Height >= 200m or floors > 50 -> SPECIAL_GRADE
        res = engine.register_construction_project(
            project_name="Keangnam Hanoi Landmark Tower",
            project_type="CIVIL_COMMERCIAL",
            total_investment_vnd=15000000000000.0,
            gross_floor_area_m2=120000.0,
            height_meters=345.0,
            floors_count=72,
            location_province="Hà Nội",
        )
        assert res["ok"] is True
        assert res["project_id"].startswith("PRJ-")
        assert res["statutory_classification"]["building_grade"] == "SPECIAL_GRADE"
        assert res["statutory_classification"]["statutory_authority"] == "Bộ Xây dựng"
        assert res["statutory_classification"]["mandatory_inspection_interval_months"] == 1

    def test_register_construction_project_grades(self, engine: ConstructionEngine) -> None:
        # Grade I: height 85m, 26 floors
        res_i = engine.register_construction_project(
            project_name="Vinhomes Metropolis",
            height_meters=85.0,
            floors_count=26,
            gross_floor_area_m2=35000.0,
        )
        assert res_i["statutory_classification"]["building_grade"] == "GRADE_I"
        assert res_i["statutory_classification"]["statutory_authority"] == "Sở Xây dựng tỉnh/thành phố"

        # Grade II: height 45m, 12 floors
        res_ii = engine.register_construction_project(
            project_name="Sunrise City Central",
            height_meters=45.0,
            floors_count=12,
            gross_floor_area_m2=15000.0,
        )
        assert res_ii["statutory_classification"]["building_grade"] == "GRADE_II"

        # Grade III: height 15m, 4 floors
        res_iii = engine.register_construction_project(
            project_name="Townhouse Shophouse",
            height_meters=15.0,
            floors_count=4,
            gross_floor_area_m2=600.0,
        )
        assert res_iii["statutory_classification"]["building_grade"] == "GRADE_III"
        assert res_iii["statutory_classification"]["statutory_authority"] == "UBND Quận/Huyện/Thị xã"

        # Grade IV: 1 floor
        res_iv = engine.register_construction_project(
            project_name="Temporary Warehouse",
            height_meters=4.5,
            floors_count=1,
            gross_floor_area_m2=200.0,
        )
        assert res_iv["statutory_classification"]["building_grade"] == "GRADE_IV"

    def test_evaluate_building_permit_exemptions(self, engine: ConstructionEngine) -> None:
        # Secret defense project (Khoan 2a Dieu 89)
        res_sec = engine.evaluate_building_permit(
            project_id="PRJ-SEC01",
            is_secret_defense_project=True,
        )
        assert res_sec["ok"] is True
        pe_sec = res_sec["permit_evaluation"]
        assert pe_sec["is_permit_exempt"] is True
        assert "Khoản 2a Điều 89" in pe_sec["exemption_clause"]
        assert pe_sec["status"] == "PERMIT_EXEMPT_VERIFIED"

        # Industrial park 1/500 (Khoan 2d Dieu 89)
        res_ip = engine.evaluate_building_permit(
            project_id="PRJ-IP01",
            is_industrial_park_approved_1_500=True,
        )
        pe_ip = res_ip["permit_evaluation"]
        assert pe_ip["is_permit_exempt"] is True
        assert "Khoản 2d Điều 89" in pe_ip["exemption_clause"]

        # Rural house under 7 floors (Khoan 2h Dieu 89)
        res_rural = engine.evaluate_building_permit(
            project_id="PRJ-RURAL01",
            is_rural_detached_house=True,
        )
        pe_rural = res_rural["permit_evaluation"]
        assert pe_rural["is_permit_exempt"] is True
        assert "Khoản 2h Điều 89" in pe_rural["exemption_clause"]

    def test_evaluate_building_permit_non_exempt_and_fire_safety(self, engine: ConstructionEngine) -> None:
        # Non-exempt with fire safety cleared -> Permit granted
        res_ok = engine.evaluate_building_permit(
            project_id="PRJ-NORMAL01",
            is_fire_safety_approved=True,
        )
        pe_ok = res_ok["permit_evaluation"]
        assert pe_ok["is_permit_exempt"] is False
        assert pe_ok["is_permit_approved"] is True
        assert pe_ok["status"] == "BUILDING_PERMIT_GRANTED"
        assert pe_ok["permit_number"].startswith("GPXD-")

        # Non-exempt without fire safety -> Permit rejected
        res_fail = engine.evaluate_building_permit(
            project_id="PRJ-NORMAL02",
            is_fire_safety_approved=False,
        )
        pe_fail = res_fail["permit_evaluation"]
        assert pe_fail["is_permit_approved"] is False
        assert pe_fail["status"] == "PERMIT_APPLICATION_REJECTED"

    def test_structure_fidic_contract_yellow_book(self, engine: ConstructionEngine) -> None:
        val = 200000000000.0  # 200 billion VND
        res = engine.structure_fidic_contract(
            project_id="PRJ-001",
            contract_name="EPC Package Civil & MEP",
            fidic_type="FIDIC_YELLOW_BOOK",
            employer_name="Vinhomes Joint Stock Company",
            contractor_name="Coteccons Construction Corporation",
            contract_value_vnd=val,
        )
        assert res["ok"] is True
        assert res["contract_id"].startswith("CTR-FIDIC-")
        ft = res["financial_terms_vnd"]
        # Yellow Book: advance 15%, bond 10%, retention 5%, max LD 12%
        assert ft["advance_payment_pct"] == 15.0
        assert ft["advance_payment_vnd"] == val * 0.15
        assert ft["performance_bond_pct"] == 10.0
        assert ft["performance_security_vnd"] == val * 0.10
        assert ft["warranty_retention_pct"] == 5.0
        assert ft["retention_money_vnd"] == val * 0.05
        assert ft["max_delay_liquidated_damages_pct"] == 12.0

    def test_structure_fidic_contract_red_and_silver_book(self, engine: ConstructionEngine) -> None:
        # Red book: advance 10%
        res_red = engine.structure_fidic_contract(
            project_id="PRJ-002",
            contract_name="Main Civil BOQ Contract",
            fidic_type="FIDIC_RED_BOOK",
            contract_value_vnd=100000000000.0,
        )
        assert res_red["financial_terms_vnd"]["advance_payment_pct"] == 10.0

        # Silver book: advance 20%
        res_silver = engine.structure_fidic_contract(
            project_id="PRJ-003",
            contract_name="Turnkey Power Plant Contract",
            fidic_type="FIDIC_SILVER_BOOK",
            contract_value_vnd=500000000000.0,
            custom_advance_pct=25.0,  # custom override
        )
        assert res_silver["financial_terms_vnd"]["advance_payment_pct"] == 25.0

    def test_audit_fire_safety_qcvn06(self, engine: ConstructionEngine) -> None:
        # Tier I: requires columns REI 150, floors REI 90, evac <= 40m
        # Passing test:
        res_pass = engine.audit_fire_safety_qcvn06(
            project_id="PRJ-001",
            fire_tier="TIER_I",
            tested_column_rei_min=150,
            tested_floor_rei_min=90,
            measured_evacuation_dist_m=35.0,
        )
        assert res_pass["ok"] is True
        assert res_pass["pccc_verdict"]["is_pccc_approved"] is True
        assert res_pass["pccc_verdict"]["status"] == "PCCC_QCVN06_CERTIFIED"

        # Failing test: column REI insufficient (120 < 150)
        res_fail = engine.audit_fire_safety_qcvn06(
            project_id="PRJ-001",
            fire_tier="TIER_I",
            tested_column_rei_min=120,
            tested_floor_rei_min=90,
            measured_evacuation_dist_m=35.0,
        )
        assert res_fail["pccc_verdict"]["is_pccc_approved"] is False
        assert res_fail["pccc_verdict"]["status"] == "PCCC_SAFETY_NON_COMPLIANT"

    def test_accept_construction_stage(self, engine: ConstructionEngine) -> None:
        # Pass: soundness >= 90% and as-built compliant
        res_pass = engine.accept_construction_stage(
            project_id="PRJ-001",
            acceptance_stage="FINAL_COMMISSIONING",
            structural_soundness_pct=98.5,
            as_built_compliance=True,
        )
        assert res_pass["ok"] is True
        assert res_pass["acceptance_audit"]["is_accepted_for_use"] is True
        assert res_pass["acceptance_audit"]["verdict"] == "ACCEPTED_FOR_COMMISSIONING"

        # Fail: structural soundness < 90%
        res_fail = engine.accept_construction_stage(
            project_id="PRJ-001",
            acceptance_stage="STRUCTURE",
            structural_soundness_pct=85.0,
            as_built_compliance=True,
        )
        assert res_fail["acceptance_audit"]["is_accepted_for_use"] is False
        assert res_fail["acceptance_audit"]["verdict"] == "REJECTED_DEFECTS_DETECTED"

    def test_list_and_status(self, engine: ConstructionEngine) -> None:
        # Seed records
        p = engine.register_construction_project("Sample Tower")
        engine.evaluate_building_permit(p["project_id"])
        engine.structure_fidic_contract(p["project_id"], "Contract A")
        engine.audit_fire_safety_qcvn06(p["project_id"])
        engine.accept_construction_stage(p["project_id"])

        assert len(engine.list_projects()) >= 1
        assert len(engine.list_permits()) >= 1
        assert len(engine.list_fidic_contracts()) >= 1
        assert len(engine.list_fire_safety_audits()) >= 1
        assert len(engine.list_acceptances()) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "ConstructionEngine"
        m = status["metrics"]
        assert m["construction_projects_count"] >= 1
        assert m["approved_building_permits"] >= 1
        assert m["fidic_contracts_count"] >= 1
        assert m["pccc_approved_projects"] >= 1
        assert m["accepted_for_commissioning"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Suite Tests
# ---------------------------------------------------------------------------


class TestConstructionCLI:
    """Test CLI commands under `mekong construction`."""

    @pytest.fixture
    def app(self) -> typing.Any:
        return build_app()

    def test_cli_main_and_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["construction", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["engine"] == "ConstructionEngine"

    def test_cli_project(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "construction",
                "project",
                "Saigon Centre Phase 3",
                "--type",
                "CIVIL_COMMERCIAL",
                "--investment",
                "5000000000000",
                "--area",
                "95000",
                "--height",
                "190",
                "--floors",
                "48",
                "--province",
                "TP. Hồ Chí Minh",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["statutory_classification"]["building_grade"] == "GRADE_I"

    def test_cli_permit(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "construction",
                "permit",
                "PRJ-CLI01",
                "--industrial-park",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["permit_evaluation"]["is_permit_exempt"] is True

    def test_cli_fidic(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "construction",
                "fidic",
                "PRJ-CLI01",
                "Civil Main Package",
                "--type",
                "FIDIC_RED_BOOK",
                "--value",
                "150000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["financial_terms_vnd"]["advance_payment_pct"] == 10.0

    def test_cli_pccc(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "construction",
                "pccc",
                "PRJ-CLI01",
                "--tier",
                "TIER_I",
                "--column-rei",
                "150",
                "--floor-rei",
                "90",
                "--evac-dist",
                "30.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["pccc_verdict"]["is_pccc_approved"] is True

    def test_cli_accept(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            [
                "construction",
                "accept",
                "PRJ-CLI01",
                "--stage",
                "FINAL_COMMISSIONING",
                "--soundness",
                "98.0",
                "--as-built",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["acceptance_audit"]["is_accepted_for_use"] is True

    def test_cli_list_and_status(self, app: typing.Any) -> None:
        res_list = runner.invoke(app, ["construction", "list", "projects", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.stdout)
        assert isinstance(data_list, list)

        res_status = runner.invoke(app, ["construction", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.stdout)
        assert data_status["ok"] is True


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestConstructionMCP:
    """Test MCP tool handlers on scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_server_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_construction_accept,
            handle_construction_fidic,
            handle_construction_list,
            handle_construction_pccc,
            handle_construction_permit,
            handle_construction_project,
            handle_construction_status,
        )

        # 1. Project
        res_p = json.loads(handle_construction_project({"project_name": "MCP Project Tower"}))
        assert res_p["ok"] is True
        prj_id = res_p["project_id"]

        # 2. Permit
        res_pm = json.loads(handle_construction_permit({"project_id": prj_id, "is_secret_defense_project": True}))
        assert res_pm["ok"] is True
        assert res_pm["permit_evaluation"]["is_permit_exempt"] is True

        # 3. FIDIC
        res_f = json.loads(handle_construction_fidic({"project_id": prj_id, "contract_name": "MCP Package"}))
        assert res_f["ok"] is True

        # 4. PCCC
        res_pc = json.loads(handle_construction_pccc({"project_id": prj_id, "fire_tier": "TIER_I", "tested_column_rei_min": 150}))
        assert res_pc["ok"] is True

        # 5. Accept
        res_a = json.loads(handle_construction_accept({"project_id": prj_id, "structural_soundness_pct": 98.5}))
        assert res_a["ok"] is True

        # 6. List
        res_l = json.loads(handle_construction_list({"category": "projects"}))
        assert isinstance(res_l, list)

        # 7. Status
        res_s = json.loads(handle_construction_status({}))
        assert res_s["ok"] is True

    def test_core_mcp_server_methods(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Project
        res_p = json.loads(server._handle_construction_project("Core MCP Tower"))
        assert res_p["ok"] is True
        prj_id = res_p["project_id"]

        # 2. Permit
        res_pm = json.loads(server._handle_construction_permit(prj_id, is_secret_defense_project=True))
        assert res_pm["ok"] is True

        # 3. FIDIC
        res_f = json.loads(server._handle_construction_fidic(prj_id, "Core Contract"))
        assert res_f["ok"] is True

        # 4. PCCC
        res_pc = json.loads(server._handle_construction_pccc(prj_id, "TIER_I", 150, 90, 32.5))
        assert res_pc["ok"] is True

        # 5. Accept
        res_a = json.loads(server._handle_construction_accept(prj_id, "FINAL_COMMISSIONING", "Apave", 98.5, True))
        assert res_a["ok"] is True

        # 6. List
        res_l = json.loads(server._handle_construction_list("projects"))
        assert isinstance(res_l, list)

        # 7. Status
        res_s = json.loads(server._handle_construction_status())
        assert res_s["ok"] is True
