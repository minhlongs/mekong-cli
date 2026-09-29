# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Commercial Real Estate, Industrial Land & EPC Leasing Compliance Engine (Phase 53)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.realestate_engine import (
    MAX_BUILDING_DENSITY_MAP,
    MIN_GREEN_SPACE_PERCENT,
    PROPERTY_CATEGORIES,
    RealEstateEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestRealEstateCoreBoundary:
    """Ensure RealEstateEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/realestate_engine.py")
        assert source_path.exists(), "realestate_engine.py must exist"

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


class TestRealEstateEngine:
    """Test RealEstateEngine financial modeling, density checks, legal due diligence, and drafting."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> RealEstateEngine:
        db_file = tmp_path / "test_realestate.db"
        return RealEstateEngine(db_path=db_file)

    def test_constants_and_categories(self) -> None:
        assert "INDUSTRIAL_LAND" in PROPERTY_CATEGORIES
        assert "COMMERCIAL_OFFICE" in PROPERTY_CATEGORIES
        assert "READY_BUILT_FACTORY" in PROPERTY_CATEGORIES
        assert "BUILT_TO_SUIT" in PROPERTY_CATEGORIES
        assert MAX_BUILDING_DENSITY_MAP["UP_TO_20M"] == 70.0
        assert MIN_GREEN_SPACE_PERCENT == 10.0

    def test_calculate_lease_financials(self, engine: RealEstateEngine) -> None:
        res = engine.calculate_lease_financials(
            category="COMMERCIAL_OFFICE",
            area_sqm=500.0,
            unit_rent_usd=20.0,
            lease_term_months=36,
            maintenance_fee_usd=1.0,
            deposit_months=3,
            annual_escalation_pct=5.0,
        )
        assert res["ok"] is True
        assert res["category"] == "COMMERCIAL_OFFICE"
        assert res["leased_area_sqm"] == 500.0
        assert res["lease_term_months"] == 36
        assert res["deposit"]["deposit_amount_usd"] == 500.0 * 20.0 * 3  # $30,000
        assert len(res["yearly_cash_flow"]) == 3
        # Escalation in year 2 should be higher than year 1
        y1_rent = res["yearly_cash_flow"][0]["unit_rent_usd_sqm_month"]
        y2_rent = res["yearly_cash_flow"][1]["unit_rent_usd_sqm_month"]
        assert y2_rent > y1_rent

    def test_validate_construction_density_compliant(self, engine: RealEstateEngine) -> None:
        # Lot 10,000 sqm, footprint 6,500 sqm (65% <= 70%), green space 1,500 sqm (15% >= 10%)
        res = engine.validate_construction_density(
            lot_area_sqm=10_000.0,
            building_footprint_sqm=6_500.0,
            green_space_sqm=1_500.0,
            building_height_tier="UP_TO_20M",
        )
        assert res["ok"] is True
        assert res["actual_density_pct"] == 65.0
        assert res["density_compliant"] is True
        assert res["actual_green_pct"] == 15.0
        assert res["green_compliant"] is True
        assert res["overall_compliant"] is True
        assert len(res["violations"]) == 0

    def test_validate_construction_density_violations(self, engine: RealEstateEngine) -> None:
        # Lot 10,000 sqm, footprint 8,000 sqm (80% > 70%), green space 500 sqm (5% < 10%)
        res = engine.validate_construction_density(
            lot_area_sqm=10_000.0,
            building_footprint_sqm=8_000.0,
            green_space_sqm=500.0,
            building_height_tier="UP_TO_20M",
        )
        assert res["ok"] is True
        assert res["actual_density_pct"] == 80.0
        assert res["density_compliant"] is False
        assert res["actual_green_pct"] == 5.0
        assert res["green_compliant"] is False
        assert res["overall_compliant"] is False
        assert len(res["violations"]) == 2

    def test_validate_construction_density_invalid_lot(self, engine: RealEstateEngine) -> None:
        res = engine.validate_construction_density(
            lot_area_sqm=0.0,
            building_footprint_sqm=100.0,
            green_space_sqm=50.0,
        )
        assert res["ok"] is False
        assert "phải lớn hơn 0" in res["error"]

    def test_perform_due_diligence_qualified(self, engine: RealEstateEngine) -> None:
        res = engine.perform_due_diligence(
            project_name="Khu Công Nghiệp VSIP Hải Phòng",
            category="INDUSTRIAL_LAND",
            land_area_sqm=50_000.0,
            has_land_cert=True,
            has_construction_permit=True,
            has_fire_safety_cert=True,
            tenure_remaining_years=40.0,
            payment_term="LUMP_SUM_RENT",
            has_disputes=False,
            is_mortgaged_to_bank=False,
        )
        assert res["ok"] is True
        assert res["risk_score"] == 0
        assert res["risk_level"] == "LOW"
        assert res["is_permitted_for_lease"] is True
        assert res["legal_conclusion"] == "ĐỦ ĐIỀU KIỆN ĐƯA VÀO KINH DOANH CHO THUÊ"

        # Check persistence
        props = engine.list_properties()
        assert len(props) == 1
        assert props[0]["project_name"] == "Khu Công Nghiệp VSIP Hải Phòng"

    def test_perform_due_diligence_defects(self, engine: RealEstateEngine) -> None:
        # Missing land cert & fire safety cert & active dispute
        res = engine.perform_due_diligence(
            project_name="Cụm Công Nghiệp X",
            category="READY_BUILT_FACTORY",
            land_area_sqm=10_000.0,
            has_land_cert=False,
            has_construction_permit=False,
            has_fire_safety_cert=False,
            tenure_remaining_years=3.0,
            has_disputes=True,
            is_mortgaged_to_bank=True,
        )
        assert res["ok"] is True
        assert res["risk_score"] >= 60
        assert res["risk_level"] == "CRITICAL"
        assert res["is_permitted_for_lease"] is False
        assert "CHƯA ĐỦ ĐIỀU KIỆN CHO THUÊ" in res["legal_conclusion"]
        assert len(res["defects"]) >= 5

    def test_draft_lease_agreement(self, engine: RealEstateEngine) -> None:
        # First register property
        p_res = engine.perform_due_diligence(
            project_name="Tòa nhà văn phòng TechnoPark Tower",
            category="COMMERCIAL_OFFICE",
            land_area_sqm=5_000.0,
            has_land_cert=True,
            has_construction_permit=True,
            has_fire_safety_cert=True,
        )
        prop_id = p_res["property_id"]

        draft_res = engine.draft_lease_agreement(
            property_id=prop_id,
            lessor_name="Công Ty Cổ Phần Đầu Tư BĐS Mekong",
            lessee_name="Tập Đoàn Công Nghệ Toàn Cầu Alpha",
            leased_area_sqm=1_200.0,
            unit_rent_usd=28.0,
            lease_term_months=60,
            maintenance_fee_usd=1.5,
            deposit_months=3,
        )
        assert draft_res["ok"] is True
        assert draft_res["contract_id"].startswith("LC-")
        assert "HD-THUE" in draft_res["contract_number"]
        assert draft_res["leased_area_sqm"] == 1_200.0
        assert "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in draft_res["contract_text"]
        assert "Nghị định số 96/2024/NĐ-CP" in draft_res["contract_text"]

        # Check contracts list
        contracts = engine.list_contracts()
        assert len(contracts) == 1
        assert contracts[0]["contract_id"] == draft_res["contract_id"]

    def test_status_metrics(self, engine: RealEstateEngine) -> None:
        stat = engine.get_status()
        assert stat["ok"] is True
        assert stat["engine"] == "RealEstateEngine"
        assert "metrics" in stat
        assert "total_properties" in stat["metrics"]


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestRealEstateCLI:
    """Test Typer CLI commands for mekong realestate."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_overview_help(self, app) -> None:
        result = runner.invoke(app, ["realestate", "--help"])
        assert result.exit_code == 0
        assert "commercial real estate" in result.output.lower() or "real estate" in result.output.lower()

    def test_cli_overview_json(self, app) -> None:
        result = runner.invoke(app, ["realestate", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "operational"

    def test_cli_finance(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "realestate",
                "finance",
                "COMMERCIAL_OFFICE",
                "800",
                "22",
                "--months",
                "36",
                "--mgmt",
                "1.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["leased_area_sqm"] == 800.0
        assert "yearly_cash_flow" in data

    def test_cli_density_compliant(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "realestate",
                "density",
                "20000",
                "12000",
                "3000",
                "--height-tier",
                "UP_TO_20M",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["overall_compliant"] is True

    def test_cli_density_violation(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "realestate",
                "density",
                "10000",
                "8500",
                "400",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["overall_compliant"] is False
        assert len(data["violations"]) >= 1

    def test_cli_audit(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "realestate",
                "audit",
                "Khu Công Nghiệp Deep C Hải Phòng",
                "INDUSTRIAL_LAND",
                "100000",
                "--tenure-years",
                "45",
                "--payment-term",
                "LUMP_SUM_RENT",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_permitted_for_lease"] is True

    def test_cli_draft(self, app) -> None:
        # First audit
        a_res = runner.invoke(
            app,
            [
                "realestate",
                "audit",
                "Nhà xưởng Long Hậu",
                "READY_BUILT_FACTORY",
                "3000",
                "--json",
            ],
        )
        prop_id = json.loads(a_res.output)["property_id"]

        result = runner.invoke(
            app,
            [
                "realestate",
                "draft",
                prop_id,
                "Chủ đầu tư Long Hậu",
                "Công Ty May Mặc Châu Á",
                "2500",
                "6.5",
                "--months",
                "60",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "contract_id" in data
        assert "contract_text" in data

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["realestate", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "properties" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["realestate", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Server Integration Tests
# ---------------------------------------------------------------------------


class TestRealEstateMCP:
    """Test realestate tools in pure-Python and FastMCP servers."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_realestate_audit,
            handle_realestate_density,
            handle_realestate_draft,
            handle_realestate_finance,
            handle_realestate_list,
            handle_realestate_status,
        )

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_realestate_finance" in tool_names
        assert "mekong_realestate_density" in tool_names
        assert "mekong_realestate_audit" in tool_names
        assert "mekong_realestate_draft" in tool_names
        assert "mekong_realestate_list" in tool_names
        assert "mekong_realestate_status" in tool_names

        assert "mekong_realestate_finance" in CORE_HANDLERS
        assert "realestate_finance" in CORE_HANDLERS
        assert "mekong_realestate_density" in CORE_HANDLERS
        assert "realestate_density" in CORE_HANDLERS

        # Finance handler
        f_res = json.loads(
            handle_realestate_finance({
                "category": "READY_BUILT_FACTORY",
                "area_sqm": 2000,
                "unit_rent_usd": 5.5,
                "lease_term_months": 24,
            })
        )
        assert f_res["ok"] is True
        assert f_res["leased_area_sqm"] == 2000

        # Density handler
        d_res = json.loads(
            handle_realestate_density({
                "lot_area_sqm": 15000,
                "building_footprint_sqm": 9000,
                "green_space_sqm": 2500,
            })
        )
        assert d_res["ok"] is True
        assert d_res["overall_compliant"] is True

        # Audit handler
        a_res = json.loads(
            handle_realestate_audit({
                "project_name": "Lô đất B2 KCN Hiệp Phước",
                "category": "INDUSTRIAL_LAND",
                "land_area_sqm": 40000,
            })
        )
        assert a_res["ok"] is True
        prop_id = a_res["property_id"]

        # Draft handler
        dr_res = json.loads(
            handle_realestate_draft({
                "property_id": prop_id,
                "lessor_name": "KCN Hiệp Phước",
                "lessee_name": "Công Ty Hóa Chất Sài Gòn",
                "leased_area_sqm": 35000,
                "unit_rent_usd": 3.0,
            })
        )
        assert dr_res["ok"] is True
        assert "contract_id" in dr_res

        # List handler
        l_res = json.loads(handle_realestate_list({"category": "ALL"}))
        assert l_res["ok"] is True
        assert len(l_res["properties"]) >= 1

        # Status handler
        s_res = json.loads(handle_realestate_status({}))
        assert s_res["ok"] is True
        assert "metrics" in s_res

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        f_res = json.loads(
            server._handle_realestate_finance(
                category="COMMERCIAL_OFFICE",
                area_sqm=300,
                unit_rent_usd=18,
            )
        )
        assert f_res["ok"] is True

        stat = json.loads(server._handle_realestate_status())
        assert stat["ok"] is True
        assert "metrics" in stat
