"""
Test Suite for Vietnamese Price Management, Anti-Price Gouging & Valuation Suite (Phase 90).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- PriceEngine domain logic (Luật Giá 2023, Chuẩn mực TĐGVN, Nghị định 87/2024, Nghị định 109/2013).
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
from src.core.price_engine import PriceEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestPriceBoundary:
    """Verifies that price_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "price_engine.py")
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


class TestPriceEngine:
    """Tests core domain and regulatory business logic of PriceEngine."""

    def test_declare_price_accepted(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.declare_price(
            enterprise_name="Công ty CP Sữa Mekong",
            product_name="Sữa tiệt trùng nguyên chất 1L",
            unit="Hộp",
            old_price_vnd=32_000.0,
            declared_price_vnd=34_000.0,
            effective_date="2026-10-01",
            is_stabilized_commodity=False,
        )
        assert res["status"] == "DECLARATION_ACCEPTED"
        assert res["is_approved"] is True
        assert res["change_pct"] == 6.25
        assert len(res["deficiencies"]) == 0
        assert res["declaration_code"].startswith("KKG-")

    def test_declare_price_stabilized_flagged(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        # Price stabilization catalog item (e.g. Sữa cho trẻ em dưới 06 tuổi) increasing > 15%
        res = engine.declare_price(
            enterprise_name="Tập đoàn Thực phẩm Trẻ em",
            product_name="SỮA CHO TRẺ EM DƯỚI 06 TUỔI Gold",
            unit="Lon 800g",
            old_price_vnd=400_000.0,
            declared_price_vnd=500_000.0,  # 25% increase
        )
        assert res["status"] == "DECLARATION_FLAGGED"
        assert res["is_approved"] is False
        assert res["is_stabilized_good"] is True
        assert any("vượt ngưỡng cho phép 15%" in d for d in res["deficiencies"])

    def test_declare_price_invalid_zero(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.declare_price(
            enterprise_name="Công ty Nông sản",
            product_name="Gạo thơm",
            unit="Kg",
            old_price_vnd=20_000.0,
            declared_price_vnd=0.0,
        )
        assert res["status"] == "DECLARATION_FLAGGED"
        assert res["is_approved"] is False
        assert any("nhỏ hơn hoặc bằng 0" in d for d in res["deficiencies"])

    def test_audit_price_posting_compliant(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.audit_price_posting(
            store_name="Siêu thị Bách Hóa Xanh",
            product_name="Dầu ăn Neptune 1L",
            listed_price_vnd=55_000.0,
            actual_selling_price_vnd=55_000.0,
            is_posted_clearly=True,
            currency="VND",
        )
        assert res["status"] == "COMPLIANT_POSTING"
        assert res["is_compliant"] is True
        assert res["estimated_fine_vnd"] == 0.0
        assert res["audit_code"].startswith("NYG-")

    def test_audit_price_posting_selling_above_listed(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.audit_price_posting(
            store_name="Cửa hàng Tiện lợi An Khang",
            product_name="Thịt bò phi lê 500g",
            listed_price_vnd=150_000.0,
            actual_selling_price_vnd=180_000.0,
            is_posted_clearly=True,
            currency="VND",
        )
        assert res["status"] == "SELLING_ABOVE_LISTED_PRICE"
        assert res["is_compliant"] is False
        assert res["estimated_fine_vnd"] == 25_000_000.0

    def test_audit_price_posting_foreign_currency(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.audit_price_posting(
            store_name="Cửa hàng Quà lưu niệm Khách sạn",
            product_name="Tượng gốm thủ công",
            listed_price_vnd=100.0,
            actual_selling_price_vnd=100.0,
            currency="USD",
        )
        assert res["status"] == "ILLEGAL_FOREIGN_CURRENCY_LISTING"
        assert res["is_compliant"] is False
        assert res["estimated_fine_vnd"] == 40_000_000.0

    def test_audit_price_posting_unlisted(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.audit_price_posting(
            store_name="Quầy tạp hóa Chợ Đồng Xuân",
            product_name="Bánh kẹo tết",
            listed_price_vnd=100_000.0,
            actual_selling_price_vnd=100_000.0,
            is_posted_clearly=False,
            currency="VND",
        )
        assert res["status"] == "UNLISTED_PRICE_VIOLATION"
        assert res["is_compliant"] is False
        assert res["estimated_fine_vnd"] == 1_000_000.0

    def test_issue_valuation_certificate_valid(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.issue_valuation_certificate(
            appraisal_firm="Công ty CP Thẩm định giá Mekong Value",
            client_name="Ngân hàng TMCP Ngoại thương Việt Nam",
            asset_description="Tòa nhà văn phòng 12 tầng tại Quận 1, TP.HCM",
            appraised_value_vnd=450_000_000_000.0,
            valuation_method="MARKET_COMPARISON",
            lead_appraiser="Thẩm định viên Lê Quốc Doanh (Thẻ TĐV 8899/TĐG)",
            licensed_appraisers_count=5,
            has_firm_insurance=True,
        )
        assert res["status"] == "CERTIFIED_VALID"
        assert res["is_valid"] is True
        assert res["validity_period_months"] == 6
        assert len(res["deficiencies"]) == 0
        assert res["certificate_code"].startswith("CTTDG-")

    def test_issue_valuation_certificate_insufficient_appraisers(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.issue_valuation_certificate(
            appraisal_firm="Công ty TNHH Thẩm định giá Thiếu nhân sự",
            client_name="Doanh nghiệp Tư nhân",
            asset_description="Nhà xưởng KCN",
            appraised_value_vnd=50_000_000_000.0,
            licensed_appraisers_count=2,  # Requirement: >= 3
            has_firm_insurance=True,
        )
        assert res["status"] == "CERTIFICATE_REVOKED"
        assert res["is_valid"] is False
        assert any("Tối thiểu 03 TĐV" in d or "chỉ có 2" in d for d in res["deficiencies"])

    def test_issue_valuation_certificate_no_insurance(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.issue_valuation_certificate(
            appraisal_firm="Công ty CP Thẩm định giá Chưa Mua BH",
            client_name="Khách hàng A",
            asset_description="Lô đất nông nghiệp",
            appraised_value_vnd=10_000_000_000.0,
            licensed_appraisers_count=3,
            has_firm_insurance=False,
        )
        assert res["status"] == "CERTIFICATE_REVOKED"
        assert res["is_valid"] is False
        assert any("bảo hiểm trách nhiệm nghề nghiệp" in d for d in res["deficiencies"])

    def test_check_price_gouging_confirmed(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.check_price_gouging(
            business_name="Đại lý Gạo Thiên Tai",
            product_name="Bao gạo ST25 5kg",
            base_price_vnd=180_000.0,
            gouged_price_vnd=270_000.0,  # 50% surge
            units_sold=1000,
            is_crisis_period=True,
        )
        assert res["status"] == "PRICE_GOUGING_CONFIRMED"
        assert res["increase_pct"] == 50.0
        assert res["illicit_profit_vnd"] > 0
        assert res["penalty_fine_vnd"] >= 50_000_000.0
        assert "HÀNH VI TĂNG GIÁ BẤT HỢP LÝ" in res["legal_conclusion"]

    def test_check_price_gouging_normal(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        res = engine.check_price_gouging(
            business_name="Cửa hàng Bình Thường",
            product_name="Gạo thơm lài 5kg",
            base_price_vnd=150_000.0,
            gouged_price_vnd=165_000.0,  # 10% increase
            units_sold=200,
            is_crisis_period=False,
        )
        assert res["status"] == "PRICE_NORMAL"
        assert res["illicit_profit_vnd"] == 0.0
        assert res["penalty_fine_vnd"] == 0.0

    def test_list_records_and_status(self, temp_db):
        engine = PriceEngine(db_path=temp_db)
        engine.declare_price("Công ty A", "Mặt hàng 1", "Hộp", 10000, 11000)
        engine.audit_price_posting("Cửa hàng B", "Mặt hàng 2", 20000, 20000)
        engine.issue_valuation_certificate("Cty TĐG C", "Khách C", "Đất", 100000000)
        engine.check_price_gouging("Cơ sở D", "Gạo", 10000, 25000, 100, is_crisis_period=True)

        decs = engine.list_records(category="declarations")
        assert len(decs) >= 1
        postings = engine.list_records(category="postings")
        assert len(postings) >= 1
        vals = engine.list_records(category="valuations")
        assert len(vals) >= 1
        gouges = engine.list_records(category="gouging")
        assert len(gouges) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_price_declarations"] >= 1
        assert status["total_price_posting_inspections"] >= 1
        assert status["total_valuation_certificates_issued"] >= 1
        assert status["price_gouging_cases_penalized"] >= 1


class TestPriceCLI:
    """Tests Typer CLI commands for the price app."""

    def test_cli_main_and_status(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["price", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"

        res_main = runner.invoke(app, ["price"])
        assert res_main.exit_code == 0
        assert "QUẢN LÝ GIÁ" in res_main.output

    def test_cli_declare_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "price",
                "declare",
                "Công ty CP Thực phẩm Mekong",
                "--product",
                "Thịt lợn đóng hộp 200g",
                "--unit",
                "Hộp",
                "--old",
                "35000",
                "--new",
                "38000",
                "--date",
                "2026-10-15",
                "--non-stabilized",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "DECLARATION_ACCEPTED"

    def test_cli_posting_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "price",
                "posting",
                "Siêu thị CoopMart",
                "--product",
                "Đường cát trắng 1kg",
                "--listed",
                "28000",
                "--actual",
                "28000",
                "--posted",
                "--curr",
                "VND",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_compliant"] is True
        assert data["status"] == "COMPLIANT_POSTING"

    def test_cli_valuation_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "price",
                "valuation",
                "Công ty Cổ phần Thẩm định giá Sài Gòn",
                "--client",
                "BIDV Chi nhánh TP.HCM",
                "--asset",
                "Khu nghỉ dưỡng Phú Quốc 2ha",
                "--value",
                "300000000000",
                "--method",
                "MARKET_COMPARISON",
                "--appraiser",
                "TĐV Trần Văn Nam",
                "--appraisers",
                "5",
                "--insurance",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_valid"] is True
        assert data["status"] == "CERTIFIED_VALID"

    def test_cli_gouge_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "price",
                "gouge",
                "Cửa hàng Vật liệu Bão lũ",
                "--product",
                "Tấm lợp fibro xi măng",
                "--base",
                "80000",
                "--gouged",
                "150000",
                "--units",
                "400",
                "--crisis",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "PRICE_GOUGING_CONFIRMED"
        assert data["illicit_profit_vnd"] > 0

    def test_cli_list_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["price", "list", "declarations", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestPriceMCP:
    """Tests dual FastMCP and fallback handlers for Price suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Declare
        res_dec = json.loads(
            server._handle_price_declare(
                enterprise_name="MCP Enterprise Test",
                product_name="Sản phẩm kiểm tra MCP",
                unit="Cái",
                old_price_vnd=100_000.0,
                declared_price_vnd=105_000.0,
            )
        )
        assert res_dec["status"] == "DECLARATION_ACCEPTED"

        # Posting
        res_post = json.loads(
            server._handle_price_posting(
                store_name="MCP Store Test",
                product_name="Hàng hóa niêm yết MCP",
                listed_price_vnd=50_000.0,
                actual_selling_price_vnd=50_000.0,
            )
        )
        assert res_post["status"] == "COMPLIANT_POSTING"

        # Valuation
        res_val = json.loads(
            server._handle_price_valuation(
                appraisal_firm="Công ty TĐG MCP",
                client_name="Khách hàng MCP",
                asset_description="Tài sản thẩm định MCP",
                appraised_value_vnd=120_000_000_000.0,
            )
        )
        assert res_val["status"] == "CERTIFIED_VALID"

        # Gouge
        res_gouge = json.loads(
            server._handle_price_gouge(
                business_name="Cơ sở MCP Tăng giá",
                product_name="Gạo cứu trợ",
                base_price_vnd=100_000.0,
                gouged_price_vnd=180_000.0,
                units_sold=200,
                is_crisis_period=True,
            )
        )
        assert res_gouge["status"] == "PRICE_GOUGING_CONFIRMED"

        # List
        res_list = json.loads(server._handle_price_list(category="declarations"))
        assert isinstance(res_list, list)

        # Status
        res_status = json.loads(server._handle_price_status())
        assert res_status["status"] == "HEALTHY"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as script_mcp

        # Test dictionary registration
        assert "mekong_price_declare" in script_mcp.CORE_HANDLERS
        assert "mekong_price_posting" in script_mcp.CORE_HANDLERS
        assert "mekong_price_valuation" in script_mcp.CORE_HANDLERS
        assert "mekong_price_gouge" in script_mcp.CORE_HANDLERS
        assert "mekong_price_list" in script_mcp.CORE_HANDLERS
        assert "mekong_price_status" in script_mcp.CORE_HANDLERS

        # Invocations
        h_dec = script_mcp.CORE_HANDLERS["mekong_price_declare"]
        res_dec = json.loads(h_dec({"enterprise_name": "Script MCP Enterprise"}))
        assert "declaration_code" in res_dec

        h_status = script_mcp.CORE_HANDLERS["mekong_price_status"]
        res_status = json.loads(h_status({}))
        assert res_status["status"] == "HEALTHY"
