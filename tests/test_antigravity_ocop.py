# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Vietnamese OCOP Agricultural Star Rating, HS Code & Export Compliance Engine (Phase 43)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_ocop_compliance,
    handle_ocop_eval,
    handle_ocop_listing,
    handle_ocop_products,
    handle_ocop_status,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
from src.core.ocop_engine import (
    CANONICAL_OCOP_PRODUCTS,
    MARKET_STANDARDS,
    OcopEngine,
)

runner = CliRunner()


class TestOcopEngine:
    """Unit test battery for OcopEngine core business logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> OcopEngine:
        db_file = tmp_path / "test_ocop.db"
        return OcopEngine(db_path=db_file)

    def test_engine_init_and_default_products(self, engine: OcopEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_products"] == len(CANONICAL_OCOP_PRODUCTS)
        assert status["total_evaluations_run"] == 0
        assert status["total_export_listings"] == 0
        assert "Quyết định 148/QĐ-TTg" in status["governing_decrees"]
        assert status["star_breakdown"]["5_stars_national_export"] >= 2
        assert status["star_breakdown"]["4_stars_provincial_high"] >= 3

    def test_evaluate_star_rating_5_stars(self, engine: OcopEngine) -> None:
        res = engine.evaluate_star_rating(
            product_name="Gạo Đặc Sản",
            part_a_community=34.0,
            part_b_marketing=24.0,
            part_c_quality=38.0,
        )
        assert res["ok"] is True
        assert res["star_rating"] == 5
        assert res["scores"]["total_score_max100"] == 96.0
        assert "Cấp Quốc gia" in res["grade_title"]
        assert res["eval_id"].startswith("OEVAL-")

    def test_evaluate_star_rating_4_stars(self, engine: OcopEngine) -> None:
        res = engine.evaluate_star_rating(
            product_name="Cà Phê BMT",
            part_a_community=28.0,
            part_b_marketing=20.0,
            part_c_quality=32.0,
        )
        assert res["ok"] is True
        assert res["star_rating"] == 4
        assert res["scores"]["total_score_max100"] == 80.0
        assert "Cấp Tỉnh" in res["grade_title"]

    def test_evaluate_star_rating_3_stars(self, engine: OcopEngine) -> None:
        res = engine.evaluate_star_rating(
            product_name="Bưởi Da Xanh",
            part_a_community=20.0,
            part_b_marketing=15.0,
            part_c_quality=25.0,
        )
        assert res["ok"] is True
        assert res["star_rating"] == 3
        assert res["scores"]["total_score_max100"] == 60.0

    def test_evaluate_star_rating_clamping(self, engine: OcopEngine) -> None:
        # Pass values exceeding statutory maximums (35, 25, 40)
        res = engine.evaluate_star_rating(
            product_name="Sản Phẩm Test Max",
            part_a_community=999.0,
            part_b_marketing=999.0,
            part_c_quality=999.0,
        )
        assert res["scores"]["part_a_community_max35"] == 35.0
        assert res["scores"]["part_b_marketing_max25"] == 25.0
        assert res["scores"]["part_c_quality_max40"] == 40.0
        assert res["scores"]["total_score_max100"] == 100.0
        assert res["star_rating"] == 5

    def test_list_products_filters(self, engine: OcopEngine) -> None:
        # All products (min_stars=1)
        all_prods = engine.list_products(min_stars=1)
        assert len(all_prods) == len(CANONICAL_OCOP_PRODUCTS)

        # 5-star products only
        five_stars = engine.list_products(min_stars=5)
        assert len(five_stars) >= 2
        for p in five_stars:
            assert p["star_rating"] == 5
            assert isinstance(p["certifications"], list)

        # Province filter
        soc_trang = engine.list_products(min_stars=1, province="Sóc Trăng")
        assert len(soc_trang) >= 1
        assert "Sóc Trăng" in soc_trang[0]["origin_province"]

    def test_market_compliance(self, engine: OcopEngine) -> None:
        eu = engine.get_market_compliance("EU")
        assert eu["ok"] is True
        assert eu["free_trade_agreement"] == "EVFTA"
        assert "HACCP" in eu["mandatory_certifications"]

        us = engine.get_market_compliance("US")
        assert us["ok"] is True
        assert "US FDA" in us["mandatory_certifications"][0]

        japan = engine.get_market_compliance("Japan")
        assert japan["ok"] is True
        assert "CPTPP" in japan["free_trade_agreement"]

        # Unknown market fallback
        unknown = engine.get_market_compliance("Brazil")
        assert unknown["ok"] is True
        assert unknown["free_trade_agreement"] == "WTO MFN"

    def test_generate_b2b_listing(self, engine: OcopEngine) -> None:
        listing = engine.generate_b2b_listing(
            product_id="OCOP-ST25",
            target_market="EU",
            platform="alibaba",
        )
        assert listing["ok"] is True
        assert listing["listing_id"].startswith("OLIST-")
        assert "ST25" in listing["title_en"]
        assert "1006.30" in listing["hs_code"]
        assert listing["target_market"] == "EU"
        assert listing["platform"] == "alibaba"
        assert listing["compliance_summary"]["fta"] == "EVFTA"

        # Check telemetry after generation
        status = engine.get_status()
        assert status["total_export_listings"] == 1
        assert len(status["recent_listings"]) == 1


class TestOcopCliCommands:
    """CLI test battery for mekong ocop subcommands."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_ocop_overview_console(self, app) -> None:
        res = runner.invoke(app, ["ocop"])
        assert res.exit_code == 0
        assert "OCOP" in res.output

    def test_ocop_overview_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert data["total_products"] >= 5
        assert "star_breakdown" in data

    def test_ocop_eval_console(self, app) -> None:
        res = runner.invoke(app, ["ocop", "eval", "Nước Mắm Phú Quốc", "--part-a", "32", "--part-b", "22", "--part-c", "36"])
        assert res.exit_code == 0
        assert "Kết Quả Đánh Giá Phân Hạng OCOP" in res.output or "Nước Mắm Phú Quốc" in res.output

    def test_ocop_eval_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "eval", "Hồ Tiêu Phú Quốc", "--part-a", "28", "--part-b", "20", "--part-c", "32", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["product_name"] == "Hồ Tiêu Phú Quốc"
        assert data["star_rating"] == 4
        assert data["scores"]["total_score_max100"] == 80.0

    def test_ocop_products_console(self, app) -> None:
        res = runner.invoke(app, ["ocop", "products"])
        assert res.exit_code == 0
        assert "Danh Mục Sản Phẩm OCOP" in res.output

    def test_ocop_products_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "products", "--min-stars", "4", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total"] >= 5
        assert len(data["products"]) >= 5
        assert all(p["star_rating"] >= 4 for p in data["products"])

    def test_ocop_listing_console(self, app) -> None:
        res = runner.invoke(app, ["ocop", "listing", "OCOP-CF-BMT", "--market", "EU", "--platform", "alibaba"])
        assert res.exit_code == 0
        assert "Listing Xuất Khẩu B2B" in res.output or "OCOP" in res.output

    def test_ocop_listing_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "listing", "OCOP-ST25", "--market", "US", "--platform", "amazon", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["product_id"] == "OCOP-ST25"
        assert data["target_market"] == "US"
        assert data["platform"] == "amazon"
        assert data["status"] == "active_ready"

    def test_ocop_compliance_console(self, app) -> None:
        res = runner.invoke(app, ["ocop", "compliance", "EU"])
        assert res.exit_code == 0
        assert "EVFTA" in res.output

    def test_ocop_compliance_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "compliance", "Japan", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["market"] == "Japan"
        assert "VJEPA" in data["free_trade_agreement"]

    def test_ocop_status_json(self, app) -> None:
        res = runner.invoke(app, ["ocop", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "supported_target_markets" in data


class TestOcopMcpParity:
    """Test suite ensuring parity across FastMCP and pure-Python JSON-RPC 2.0 stdio engines."""

    def test_mcp_spec_registration(self) -> None:
        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        assert "mekong_ocop_eval" in names
        assert "mekong_ocop_products" in names
        assert "mekong_ocop_listing" in names
        assert "mekong_ocop_compliance" in names
        assert "mekong_ocop_status" in names

    def test_script_mcp_handlers(self) -> None:
        # Status
        status_raw = handle_ocop_status({})
        status = json.loads(status_raw)
        assert status["status"] == "operational"

        # Eval
        eval_raw = handle_ocop_eval({"product_name": "Trà Thái Nguyên", "part_a": 31, "part_b": 22, "part_c": 37})
        eval_res = json.loads(eval_raw)
        assert eval_res["ok"] is True
        assert eval_res["star_rating"] == 5

        # Products
        prods_raw = handle_ocop_products({"min_stars": 4})
        prods = json.loads(prods_raw)
        assert prods["ok"] is True
        assert prods["total"] >= 5

        # Listing
        listing_raw = handle_ocop_listing({"product_id": "OCOP-DIEU-BP", "target_market": "China", "platform": "alibaba"})
        listing = json.loads(listing_raw)
        assert listing["ok"] is True
        assert listing["target_market"] == "China"

        # Compliance
        comp_raw = handle_ocop_compliance({"market": "China"})
        comp = json.loads(comp_raw)
        assert comp["ok"] is True
        assert "ACFTA" in comp["free_trade_agreement"]

    def test_core_mcp_server_handlers_and_aliases(self) -> None:
        server = MekongMcpServer(name="test-server")

        # Handlers
        status_res = json.loads(server._handle_ocop_status())
        assert status_res["status"] == "operational"

        eval_res = json.loads(server._handle_ocop_eval(product_name="Gạo ST25", part_a=33, part_b=23, part_c=38))
        assert eval_res["ok"] is True
        assert eval_res["star_rating"] == 5

        prods_res = json.loads(server._handle_ocop_products(min_stars=1))
        assert prods_res["total"] >= 5

        comp_res = json.loads(server._handle_ocop_compliance(market="EU"))
        assert comp_res["ok"] is True

        listing_res = json.loads(server._handle_ocop_listing(product_id="OCOP-ST25", target_market="EU", platform="alibaba"))
        assert listing_res["ok"] is True

        # Aliases
        assert server._handle_mekong_ocop_eval == server._handle_ocop_eval
        assert server._handle_mekong_ocop_products == server._handle_ocop_products
        assert server._handle_mekong_ocop_listing == server._handle_ocop_listing
        assert server._handle_mekong_ocop_compliance == server._handle_ocop_compliance
        assert server._handle_mekong_ocop_status == server._handle_ocop_status


class TestOcopCoreBoundary:
    """Ensure src/core/ocop_engine.py is pure Python standard library with zero external HTTP or vendor SDK imports."""

    def test_core_ast_imports(self) -> None:
        engine_path = Path("src/core/ocop_engine.py")
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
