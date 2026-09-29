# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Customs Clearance, VNACCS Channeling & Cross-Border Logistics Engine (Phase 50)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.customs_engine import (
    EXCHANGE_RATE_USD_VND,
    HS_DATABASE,
    CustomsEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestCustomsCoreBoundary:
    """Ensure CustomsEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/customs_engine.py")
        assert source_path.exists(), "customs_engine.py must exist"

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


class TestCustomsEngine:
    """Test CustomsEngine business logic, tariff computation, and VNACCS channeling."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> CustomsEngine:
        db_file = tmp_path / "test_customs.db"
        return CustomsEngine(db_path=db_file)

    def test_database_and_constants(self) -> None:
        assert "8471.30.20" in HS_DATABASE
        assert "8542.31.00" in HS_DATABASE
        assert "0901.11.10" in HS_DATABASE
        assert "8504.40.11" in HS_DATABASE
        assert EXCHANGE_RATE_USD_VND == 25_450.0

    def test_lookup_hs_code_mfn(self, engine: CustomsEngine) -> None:
        res = engine.lookup_hs_code(hs_code="8471.30.20", fta="MFN")
        assert res["ok"] is True
        assert res["hs_code"] == "8471.30.20"
        assert "Máy tính xách tay" in res["description"]
        assert res["mfn_rate_pct"] == 0.0
        assert res["vat_rate_pct"] == 10.0
        assert res["applicable_duty_rate_pct"] == 0.0

    def test_lookup_hs_code_fta_preferential(self, engine: CustomsEngine) -> None:
        res = engine.lookup_hs_code(hs_code="8504.40.11", fta="EVFTA")
        assert res["ok"] is True
        assert res["hs_code"] == "8504.40.11"
        assert res["applicable_duty_rate_pct"] == 0.0

    def test_lookup_hs_code_not_found(self, engine: CustomsEngine) -> None:
        res = engine.lookup_hs_code(hs_code="9999.99.99")
        assert res["ok"] is False
        assert "không tồn tại trong danh mục" in res["error"]

    def test_calculate_customs_duties(self, engine: CustomsEngine) -> None:
        res = engine.calculate_customs_duties(
            invoice_value_usd=10_000.0,
            hs_code="8504.40.11",  # UPS: MFN 3%, VAT 10%
            freight_usd=500.0,
            insurance_usd=100.0,
            fta="MFN",
        )
        assert res["ok"] is True
        assert res["cif_value_usd"] == 10_600.0
        assert res["import_duty_rate_pct"] == 3.0
        assert res["dutiable_value_vnd"] == round(10_600.0 * EXCHANGE_RATE_USD_VND)
        assert res["import_duty_vnd"] == round(res["dutiable_value_vnd"] * 0.03)
        assert res["vat_vnd"] == round((res["dutiable_value_vnd"] + res["import_duty_vnd"]) * 0.10)
        assert res["total_tax_vnd"] == res["import_duty_vnd"] + res["vat_vnd"]

    def test_channeling_green(self, engine: CustomsEngine) -> None:
        res = engine.evaluate_customs_channel(
            enterprise_tax_id="0101234567",
            hs_code="8471.30.20",
            invoice_value_usd=5_000.0,
            origin_country="US",
            compliance_tier="TIER_1_AEO",
            has_valid_co=True,
        )
        assert res["ok"] is True
        assert res["channel"] == "GREEN"
        assert "Luồng Xanh" in res["channel_name"]

    def test_channeling_yellow(self, engine: CustomsEngine) -> None:
        res = engine.evaluate_customs_channel(
            enterprise_tax_id="0309876543",
            hs_code="8471.30.20",
            invoice_value_usd=30_000.0,
            origin_country="CN",
            compliance_tier="TIER_2_NORMAL",
            has_valid_co=False,  # Missing C/O triggers Yellow
        )
        assert res["ok"] is True
        assert res["channel"] == "YELLOW"
        assert "Luồng Vàng" in res["channel_name"]

    def test_channeling_red(self, engine: CustomsEngine) -> None:
        res = engine.evaluate_customs_channel(
            enterprise_tax_id="0405556667",
            hs_code="8504.40.11",
            invoice_value_usd=150_000.0,
            origin_country="XX",
            compliance_tier="TIER_4_LOW",  # High risk tier triggers Red
            has_valid_co=False,
        )
        assert res["ok"] is True
        assert res["channel"] == "RED"
        assert "Luồng Đỏ" in res["channel_name"]

    def test_create_declaration(self, engine: CustomsEngine) -> None:
        res = engine.create_declaration(
            enterprise_tax_id="0101234567",
            hs_code="8471.30.20",
            commodity_name="Lô máy tính phục vụ nghiên cứu AI",
            invoice_value_usd=20_000.0,
            origin_country="US",
            declaration_type="IMPORT_BUSINESS",
            compliance_tier="TIER_2_NORMAL",
            has_valid_co=True,
        )
        assert res["ok"] is True
        assert res["declaration_id"].startswith("TKHQ-")
        assert res["commodity_name"] == "Lô máy tính phục vụ nghiên cứu AI"
        assert res["channel"] == "GREEN"
        assert "total_tax_vnd" in res

        # Verify persisted in database
        lst = engine.list_declarations()
        assert len(lst) >= 1
        assert any(d["declaration_id"] == res["declaration_id"] for d in lst)

    def test_verify_rules_of_origin_qualifying(self, engine: CustomsEngine) -> None:
        # FOB = $10,000, Non-originating = $4,000 -> RVC = (10,000 - 4,000) / 10,000 = 60% >= 40%
        res = engine.verify_rules_of_origin(
            form_type="EUR.1",
            hs_code="0901.11.10",
            fob_value_usd=10_000.0,
            non_originating_value_usd=4_000.0,
            exporter_name="Công Ty Cà Phê Tây Nguyên",
            importer_country="DE",
        )
        assert res["ok"] is True
        assert res["rvc_pct"] == 60.0
        assert res["is_eligible"] is True
        assert res["criteria_code"] == "RVC_40"
        assert res["status"] == "QUALIFIED_FOR_PREFERENTIAL_TARIFF"

    def test_verify_rules_of_origin_non_qualifying(self, engine: CustomsEngine) -> None:
        # FOB = $10,000, Non-originating = $7,000 -> RVC = 30% < 40%
        res = engine.verify_rules_of_origin(
            form_type="CPTPP",
            hs_code="8471.30.20",
            fob_value_usd=10_000.0,
            non_originating_value_usd=7_000.0,
            exporter_name="Công Ty Lắp Ráp Máy Tính",
            importer_country="JP",
        )
        assert res["ok"] is True
        assert res["rvc_pct"] == 30.0
        assert res["is_eligible"] is False
        assert res["criteria_code"] == "INSUFFICIENT_WORKING"
        assert res["status"] == "ORIGIN_DISQUALIFIED"

    def test_get_status(self, engine: CustomsEngine) -> None:
        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "CustomsEngine"
        assert status["reference_exchange_rate"] == 25_450.0
        assert "metrics" in status
        assert status["metrics"]["supported_hs_codes"] == len(HS_DATABASE)


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestCustomsCLI:
    """Test Typer CLI surface for mekong customs."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_overview(self, app) -> None:
        result = runner.invoke(app, ["customs"])
        assert result.exit_code == 0
        assert "VNACCS" in result.output

    def test_cli_overview_json(self, app) -> None:
        result = runner.invoke(app, ["customs", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["engine"] == "CustomsEngine"

    def test_cli_hs_lookup(self, app) -> None:
        result = runner.invoke(app, ["customs", "hs-lookup", "8471.30.20"])
        assert result.exit_code == 0
        assert "8471.30.20" in result.output

    def test_cli_hs_lookup_json(self, app) -> None:
        result = runner.invoke(app, ["customs", "hs-lookup", "8471.30.20", "--fta", "EVFTA", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["hs_code"] == "8471.30.20"
        assert data["tariff_scheme"] == "EVFTA"

    def test_cli_duty_calc(self, app) -> None:
        result = runner.invoke(app, ["customs", "duty-calc", "10000", "--hs", "8504.40.11", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["cif_value_usd"] == 10_000.0
        assert "total_tax_vnd" in data

    def test_cli_channel(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "customs",
                "channel",
                "0101234567",
                "8471.30.20",
                "5000",
                "--tier",
                "TIER_1_AEO",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["channel"] == "GREEN"

    def test_cli_declare(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "customs",
                "declare",
                "0101234567",
                "8471.30.20",
                "Lô máy trạm phục vụ phòng lab",
                "15000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "declaration_id" in data

    def test_cli_origin(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "customs",
                "origin",
                "EUR.1",
                "0901.11.10",
                "20000",
                "5000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_eligible"] is True

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["customs", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "declarations" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["customs", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Server Integration Tests
# ---------------------------------------------------------------------------


class TestCustomsMCP:
    """Test customs tools in pure-Python and FastMCP servers."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_customs_channel,
            handle_customs_declare,
            handle_customs_duty_calc,
            handle_customs_hs_lookup,
            handle_customs_origin,
            handle_customs_status,
        )

        # Check registration in CORE_TOOLS_SPEC
        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_customs_hs_lookup" in tool_names
        assert "mekong_customs_duty_calc" in tool_names
        assert "mekong_customs_channel" in tool_names
        assert "mekong_customs_declare" in tool_names
        assert "mekong_customs_origin" in tool_names
        assert "mekong_customs_status" in tool_names

        # Check handler mappings in CORE_HANDLERS
        assert "mekong_customs_hs_lookup" in CORE_HANDLERS
        assert "customs_hs_lookup" in CORE_HANDLERS

        # Test HS lookup handler
        hs_res = json.loads(handle_customs_hs_lookup({"hs_code": "8471.30.20", "fta": "MFN"}))
        assert hs_res["ok"] is True
        assert hs_res["hs_code"] == "8471.30.20"

        # Test Duty calc handler
        duty_res = json.loads(handle_customs_duty_calc({"invoice_value_usd": 10000, "hs_code": "8471.30.20"}))
        assert duty_res["ok"] is True
        assert "total_tax_vnd" in duty_res

        # Test Channel handler
        chan_res = json.loads(
            handle_customs_channel({
                "enterprise_tax_id": "0101234567",
                "hs_code": "8471.30.20",
                "invoice_value_usd": 5000,
                "compliance_tier": "TIER_1_AEO",
            })
        )
        assert chan_res["ok"] is True
        assert chan_res["channel"] == "GREEN"

        # Test Declare handler
        decl_res = json.loads(
            handle_customs_declare({
                "enterprise_tax_id": "0101234567",
                "hs_code": "8471.30.20",
                "commodity_name": "Laptop thử nghiệm",
                "invoice_value_usd": 8000,
            })
        )
        assert decl_res["ok"] is True
        assert "declaration_id" in decl_res

        # Test Origin handler
        orig_res = json.loads(
            handle_customs_origin({
                "form_type": "EUR.1",
                "hs_code": "0901.11.10",
                "fob_value_usd": 10000,
                "non_originating_value_usd": 3000,
            })
        )
        assert orig_res["ok"] is True
        assert orig_res["is_eligible"] is True

        # Test Status handler
        stat_res = json.loads(handle_customs_status({}))
        assert stat_res["ok"] is True
        assert "metrics" in stat_res

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res = json.loads(server._handle_customs_hs_lookup(hs_code="8471.30.20"))
        assert res["ok"] is True
        assert res["hs_code"] == "8471.30.20"

        stat = json.loads(server._handle_customs_status())
        assert stat["ok"] is True
        assert "metrics" in stat
