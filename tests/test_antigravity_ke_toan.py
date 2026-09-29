# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Vietnamese Accounting Standard (VAS) and TT78 E-Invoicing Engine (Phase 40)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_ke_toan_create,
    handle_ke_toan_journal,
    handle_ke_toan_status,
    handle_ke_toan_xml,
)
from src.cli.app_setup import build_app
from src.core.ke_toan_engine import (
    CANONICAL_ACCOUNTS,
    KeToanEngine,
    format_vnd,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


class TestKeToanEngine:
    """Unit test battery for KeToanEngine core logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> KeToanEngine:
        db_file = tmp_path / "test_ke_toan.db"
        return KeToanEngine(db_path=db_file)

    def test_engine_init_and_default_accounts(self, engine: KeToanEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_accounts"] == len(CANONICAL_ACCOUNTS)
        assert status["total_invoices"] == 0
        assert status["total_revenue"] == 0.0

    def test_format_vnd(self) -> None:
        formatted = format_vnd(25000000)
        assert "25.000.000 đ" in formatted

    def test_create_invoice_default_vat(self, engine: KeToanEngine) -> None:
        inv = engine.create_invoice(
            amount=10000000,
            buyer="Công Ty Công Nghệ Mekong",
            vat_rate=10,
            description="Dịch vụ phát triển AI",
        )
        assert inv["invoice_id"].startswith("INV-C25TAA-")
        assert inv["subtotal"] == 10000000.0
        assert inv["vat_rate"] == 10
        assert inv["vat_amount"] == 1000000.0
        assert inv["total_amount"] == 11000000.0
        assert "<HDon>" in inv["xml_content"]

        retrieved = engine.get_invoice(inv["invoice_id"])
        assert retrieved is not None
        assert retrieved["invoice_id"] == inv["invoice_id"]
        assert retrieved["buyer_name"] == "Công Ty Công Nghệ Mekong"

    def test_create_invoice_custom_vat(self, engine: KeToanEngine) -> None:
        # 8% preferential VAT
        inv_8 = engine.create_invoice(amount=50000000, buyer="Khách Hàng A", vat_rate=8)
        assert inv_8["vat_rate"] == 8
        assert inv_8["vat_amount"] == 4000000.0
        assert inv_8["total_amount"] == 54000000.0

        # 0% export VAT
        inv_0 = engine.create_invoice(amount=20000000, buyer="Khách Hàng Quốc Tế", vat_rate=0)
        assert inv_0["vat_rate"] == 0
        assert inv_0["vat_amount"] == 0.0
        assert inv_0["total_amount"] == 20000000.0

    def test_generate_tt78_xml_structure(self, engine: KeToanEngine) -> None:
        inv = engine.create_invoice(
            amount=15000000,
            buyer="Cửa Hàng Bán Lẻ",
            seller="Mekong Solutions",
            seller_tax_code="0318928172",
            description="Phần mềm quản lý bán hàng",
        )
        xml = inv["xml_content"]
        assert "<HDon>" in xml
        assert "<TTChung>" in xml
        assert "<KHHDon>C25TAA</KHHDon>" in xml
        assert "<NDHDon>" in xml
        assert "<NBan>" in xml
        assert "<Ten>Mekong Solutions</Ten>" in xml
        assert "<MST>0318928172</MST>" in xml
        assert "<NMua>" in xml
        assert "<Ten>Cửa Hàng Bán Lẻ</Ten>" in xml
        assert "<DSHHDVu>" in xml
        assert "<TToan>" in xml

    def test_create_vas_journal_balanced(self, engine: KeToanEngine) -> None:
        inv = engine.create_invoice(amount=30000000, buyer="Doanh Nghiệp B", vat_rate=10)
        jrn = engine.create_vas_journal(inv, save=True)

        assert jrn["balanced"] is True
        assert jrn["total_debit"] == 33000000.0
        assert jrn["total_credit"] == 33000000.0
        assert len(jrn["entries"]) == 3

        accounts = {e["account"]: e for e in jrn["entries"]}
        assert "131" in accounts
        assert accounts["131"]["debit"] == 33000000.0
        assert "511" in accounts
        assert accounts["511"]["credit"] == 30000000.0
        assert "3331" in accounts
        assert accounts["3331"]["credit"] == 3000000.0

    def test_create_vas_journal_from_id(self, engine: KeToanEngine) -> None:
        inv = engine.create_invoice(amount=12000000, buyer="Khách C", vat_rate=8)
        jrn = engine.create_vas_journal(inv["invoice_id"], save=True)
        assert jrn["balanced"] is True
        assert jrn["invoice_id"] == inv["invoice_id"]

    def test_list_and_status_telemetry(self, engine: KeToanEngine) -> None:
        engine.create_invoice(amount=10000000, buyer="Buyer 1", vat_rate=10)
        inv2 = engine.create_invoice(amount=20000000, buyer="Buyer 2", vat_rate=10)
        engine.create_vas_journal(inv2, save=True)

        invoices = engine.list_invoices(limit=10)
        assert len(invoices) == 2

        journals = engine.list_journal_entries(limit=10)
        assert len(journals) == 1

        status = engine.get_status()
        assert status["total_invoices"] == 2
        assert status["total_revenue"] == 30000000.0
        assert status["total_vat_output"] == 3000000.0
        assert status["total_gross_invoiced"] == 33000000.0
        assert status["total_journal_entries"] == 1


class TestKeToanCli:
    """CLI test battery for mekong ke-toan commands."""

    @pytest.fixture
    def app(self) -> typing.Any:
        return build_app()

    def test_ke_toan_overview_plain(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["ke-toan"])
        assert res.exit_code == 0
        assert "HỆ THỐNG KẾ TOÁN VAS" in res.output or "Kế Toán" in res.output

    def test_ke_toan_overview_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["ke-toan", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "total_invoices" in data
        assert "standards_compliance" in data

    def test_ke_toan_create_json(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "create", "5000000", "--vat", "8", "--buyer", "Test Buyer", "--json"],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["subtotal"] == 5000000.0
        assert data["vat_rate"] == 8
        assert data["vat_amount"] == 400000.0
        assert data["total_amount"] == 5400000.0

    def test_ke_toan_create_console(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "create", "5000000", "--vat", "10", "--buyer", "Test Buyer"],
        )
        assert res.exit_code == 0
        assert "5.000.000" in res.output

    def test_ke_toan_xml_console(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "xml", "8000000", "--vat", "10", "--buyer", "Test XML"],
        )
        assert res.exit_code == 0
        assert "<HDon>" in res.output

    def test_ke_toan_journal_json(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "journal", "15000000", "--vat", "10", "--buyer", "Test Journal", "--json"],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["balanced"] is True
        assert data["total_debit"] == 16500000.0
        assert data["total_credit"] == 16500000.0

    def test_ke_toan_journal_console(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "journal", "15000000", "--vat", "10", "--buyer", "Test Journal"],
        )
        assert res.exit_code == 0
        assert "131" in res.output

    def test_ke_toan_summary_console(self, app: typing.Any) -> None:
        res = runner.invoke(
            app,
            ["ke-toan", "summary", "6000000", "--vat", "10", "--buyer", "Test Summary"],
        )
        assert res.exit_code == 0
        assert "6.000.000" in res.output

    def test_ke_toan_status_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["ke-toan", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "total_accounts" in data

    def test_ke_toan_list_json(self, app: typing.Any) -> None:
        res = runner.invoke(app, ["ke-toan", "list", "--type", "invoice", "--limit", "5", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestKeToanMcpParity:
    """Parity tests for FastMCP and JSON-RPC fallback handlers."""

    def test_scripts_mcp_tools_spec_registered(self) -> None:
        tool_names = [tool["name"] for tool in CORE_TOOLS_SPEC]
        assert "mekong_ke_toan_create" in tool_names
        assert "mekong_ke_toan_xml" in tool_names
        assert "mekong_ke_toan_journal" in tool_names
        assert "mekong_ke_toan_status" in tool_names

    def test_scripts_mcp_handlers(self) -> None:
        # Create
        res_raw = handle_ke_toan_create({
            "amount": 20000000,
            "buyer": "MCP Client",
            "vat_rate": 10,
        })
        res_create = json.loads(res_raw)
        assert res_create["subtotal"] == 20000000.0
        assert res_create["vat_amount"] == 2000000.0

        # XML
        res_xml = handle_ke_toan_xml({
            "amount": 10000000,
            "buyer": "MCP XML Client",
            "vat_rate": 8,
        })
        assert "<HDon>" in res_xml

        # Journal
        res_raw = handle_ke_toan_journal({
            "amount": 10000000,
            "buyer": "MCP Journal Client",
            "vat_rate": 10,
        })
        res_jrn = json.loads(res_raw)
        assert res_jrn["balanced"] is True
        assert res_jrn["total_debit"] == 11000000.0

        # Status
        res_raw = handle_ke_toan_status({})
        res_status = json.loads(res_raw)
        assert res_status["status"] == "operational"

    def test_core_mcp_server_handlers(self) -> None:
        server = MekongMcpServer()

        # Create
        res_raw = server._handle_ke_toan_create(
            amount=25000000,
            buyer="Core Server Client",
            vat_rate=10,
        )
        res_create = json.loads(res_raw)
        assert res_create["subtotal"] == 25000000.0

        # XML
        res_xml = server._handle_ke_toan_xml(
            amount=15000000,
            buyer="Core XML Client",
        )
        assert "<HDon>" in res_xml

        # Journal
        res_raw = server._handle_ke_toan_journal(
            amount=30000000,
            buyer="Core Journal Client",
            vat_rate=10,
        )
        res_jrn = json.loads(res_raw)
        assert res_jrn["balanced"] is True

        # Status
        res_raw = server._handle_ke_toan_status()
        res_status = json.loads(res_raw)
        assert res_status["status"] == "operational"


class TestKeToanCoreBoundary:
    """Enforce strict standard-library-only core boundary on ke_toan_engine.py."""

    def test_ke_toan_engine_standard_library_only(self) -> None:
        target_path = Path("src/core/ke_toan_engine.py")
        assert target_path.exists()

        tree = ast.parse(target_path.read_text(encoding="utf-8"))
        allowed_modules = {
            "__future__",
            "datetime",
            "decimal",
            "json",
            "pathlib",
            "sqlite3",
            "typing",
            "uuid",
            "xml",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg in allowed_modules, f"Disallowed import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg in allowed_modules, f"Disallowed from-import: {node.module}"
