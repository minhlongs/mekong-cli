# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine (Phase 52)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.tender_engine import (
    COMPETITIVE_QUOTATION_CAP_VND,
    DIRECT_CONTRACTING_CAPS_VND,
    TenderEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestTenderCoreBoundary:
    """Ensure TenderEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/tender_engine.py")
        assert source_path.exists(), "tender_engine.py must exist"

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


class TestTenderEngine:
    """Test TenderEngine procurement method advisory, dossier creation, 4-step eval, and collusion detection."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> TenderEngine:
        db_file = tmp_path / "test_tenders.db"
        return TenderEngine(db_path=db_file)

    def test_procurement_constants(self) -> None:
        assert DIRECT_CONTRACTING_CAPS_VND["CONSULTING"] == 500_000_000.0
        assert DIRECT_CONTRACTING_CAPS_VND["GOODS"] == 1_000_000_000.0
        assert DIRECT_CONTRACTING_CAPS_VND["WORKS"] == 1_000_000_000.0
        assert COMPETITIVE_QUOTATION_CAP_VND == 5_000_000_000.0

    def test_evaluate_method_direct_contracting_cap(self, engine: TenderEngine) -> None:
        # Consulting <= 500M
        res = engine.evaluate_procurement_method(package_type="CONSULTING", budget_vnd=450_000_000.0)
        assert res["ok"] is True
        assert res["recommended_method"] == "DIRECT_CONTRACTING"
        assert res["bid_security_required"] is False

        # Goods <= 1B
        res_goods = engine.evaluate_procurement_method(package_type="GOODS", budget_vnd=900_000_000.0)
        assert res_goods["recommended_method"] == "DIRECT_CONTRACTING"

    def test_evaluate_method_competitive_quotation(self, engine: TenderEngine) -> None:
        # Goods > 1B and <= 5B
        res = engine.evaluate_procurement_method(package_type="GOODS", budget_vnd=2_500_000_000.0)
        assert res["ok"] is True
        assert res["recommended_method"] == "COMPETITIVE_QUOTATION"
        assert res["bid_security_required"] is True
        assert res["bid_security_rate_pct"] == 1.5
        assert res["bid_security_estimated_vnd"] == round(2_500_000_000.0 * 0.015)

    def test_evaluate_method_open_bidding(self, engine: TenderEngine) -> None:
        # Consulting > 500M goes directly to Open Bidding (no competitive quotation for consulting)
        res_c = engine.evaluate_procurement_method(package_type="CONSULTING", budget_vnd=800_000_000.0)
        assert res_c["recommended_method"] == "OPEN_BIDDING"

        # Goods > 5B
        res_g = engine.evaluate_procurement_method(package_type="GOODS", budget_vnd=15_000_000_000.0)
        assert res_g["recommended_method"] == "OPEN_BIDDING"
        assert res_g["bid_security_rate_pct"] == 2.0  # >10B uses 2.0%

    def test_evaluate_method_urgent_or_proprietary(self, engine: TenderEngine) -> None:
        # Large budget but urgent
        res_urg = engine.evaluate_procurement_method(
            package_type="WORKS", budget_vnd=20_000_000_000.0, is_urgent=True
        )
        assert res_urg["recommended_method"] == "DIRECT_CONTRACTING"
        assert "cấp bách" in res_urg["statutory_justification"]

        # Proprietary technology
        res_prop = engine.evaluate_procurement_method(
            package_type="GOODS", budget_vnd=8_000_000_000.0, is_proprietary_tech=True
        )
        assert res_prop["recommended_method"] == "DIRECT_CONTRACTING"
        assert "công nghệ độc quyền" in res_prop["statutory_justification"]

    def test_create_tender(self, engine: TenderEngine) -> None:
        res = engine.create_tender(
            package_name="Mua sắm máy chủ trung tâm dữ liệu",
            procuring_entity="Cục Tin học hóa - Bộ TT&TT",
            budget_vnd=4_000_000_000.0,
            package_type="GOODS",
            submission_days=20,
        )
        assert res["ok"] is True
        assert res["tender_id"].startswith("TD-")
        assert res["package_number"].startswith("EGP-")
        assert res["procurement_method"] == "COMPETITIVE_QUOTATION"
        assert res["statutory_criteria"]["min_3yr_avg_revenue_vnd"] == 6_000_000_000.0  # 1.5x
        assert res["statutory_criteria"]["min_similar_contract_val_vnd"] == 2_800_000_000.0  # 0.7x
        assert res["status"] == "PUBLISHED"

        # Check persistence
        tenders = engine.list_tenders()
        assert len(tenders) == 1
        assert tenders[0]["tender_id"] == res["tender_id"]

    def test_evaluate_bid_qualified(self, engine: TenderEngine) -> None:
        t_res = engine.create_tender(
            package_name="Xây dựng cổng thông tin chuyển đổi số",
            procuring_entity="UBND TP Đà Nẵng",
            budget_vnd=2_000_000_000.0,
            package_type="NON_CONSULTING",
        )
        t_id = t_res["tender_id"]

        # Bidder fulfills all 4 steps:
        # Budget = 2B -> req revenue = 3B, req similar = 1.4B
        eval_res = engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Công Ty Cổ Phần Công Nghệ Mekong",
            bid_price_vnd=1_850_000_000.0,
            bidder_tax_id="0312345678",
            revenue_3yr_avg_vnd=5_000_000_000.0,
            similar_contract_val_vnd=1_600_000_000.0,
            tech_score=92.0,
            has_valid_security=True,
        )
        assert eval_res["ok"] is True
        assert eval_res["step_1_eligibility"] is True
        assert eval_res["step_2_capacity"] is True
        assert eval_res["step_3_technical"] is True
        assert eval_res["step_4_financial"] is True
        assert eval_res["overall_qualified"] is True
        assert eval_res["savings_rate_pct"] == 7.5
        assert eval_res["recommendation"] == "ĐỀ NGHỊ TRÚNG THẦU"

    def test_evaluate_bid_disqualified_reasons(self, engine: TenderEngine) -> None:
        t_res = engine.create_tender(
            package_name="Gói thầu thiết bị văn phòng",
            procuring_entity="Bệnh viện Bạch Mai",
            budget_vnd=1_000_000_000.0,
            package_type="GOODS",
            procurement_method="OPEN_BIDDING",
        )
        t_id = t_res["tender_id"]

        # Missing security bond
        res_sec = engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu A",
            bid_price_vnd=900_000_000.0,
            has_valid_security=False,
            revenue_3yr_avg_vnd=2_000_000_000.0,
            similar_contract_val_vnd=800_000_000.0,
            tech_score=85.0,
        )
        assert res_sec["step_1_eligibility"] is False
        assert res_sec["overall_qualified"] is False

        # Insufficient financial capacity
        res_cap = engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu B",
            bid_price_vnd=900_000_000.0,
            has_valid_security=True,
            revenue_3yr_avg_vnd=1_000_000_000.0,  # Needs 1.5B
            similar_contract_val_vnd=800_000_000.0,
            tech_score=85.0,
        )
        assert res_cap["step_2_capacity"] is False
        assert res_cap["overall_qualified"] is False

        # Technical score below floor (70.0)
        res_tech = engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu C",
            bid_price_vnd=900_000_000.0,
            has_valid_security=True,
            revenue_3yr_avg_vnd=2_000_000_000.0,
            similar_contract_val_vnd=800_000_000.0,
            tech_score=65.0,
        )
        assert res_tech["step_3_technical"] is False
        assert res_tech["overall_qualified"] is False

        # Bid price exceeds package budget
        res_over = engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu D",
            bid_price_vnd=1_200_000_000.0,
            has_valid_security=True,
            revenue_3yr_avg_vnd=2_000_000_000.0,
            similar_contract_val_vnd=800_000_000.0,
            tech_score=85.0,
        )
        assert res_over["step_4_financial"] is False
        assert res_over["overall_qualified"] is False

    def test_evaluate_bid_invalid_tender_id(self, engine: TenderEngine) -> None:
        res = engine.evaluate_bid(
            tender_id="NON_EXISTENT_TENDER",
            bidder_name="Công Ty Z",
            bid_price_vnd=100_000_000.0,
        )
        assert res["ok"] is False
        assert "Không tìm thấy gói thầu" in res["error"]

    def test_detect_bid_collusion(self, engine: TenderEngine) -> None:
        t_res = engine.create_tender(
            package_name="Mua sắm máy trạm đồ họa",
            procuring_entity="Đại học Quốc gia",
            budget_vnd=3_000_000_000.0,
        )
        t_id = t_res["tender_id"]

        # Insert 2 bids with identical or near-identical prices (diff < 0.3%)
        engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu Liên minh 1",
            bid_price_vnd=2_950_000_000.0,
            bidder_tax_id="0101111111",
            revenue_3yr_avg_vnd=5_000_000_000.0,
            similar_contract_val_vnd=2_500_000_000.0,
            tech_score=80.0,
        )
        engine.evaluate_bid(
            tender_id=t_id,
            bidder_name="Nhà thầu Liên minh 2",
            bid_price_vnd=2_952_000_000.0,  # ~0.06% diff
            bidder_tax_id="0101111111",      # Same MST
            revenue_3yr_avg_vnd=5_000_000_000.0,
            similar_contract_val_vnd=2_500_000_000.0,
            tech_score=82.0,
        )

        scan_res = engine.detect_bid_collusion(tender_id=t_id)
        assert scan_res["ok"] is True
        assert scan_res["collusion_risk"] == "HIGH"
        assert scan_res["risk_score"] >= 50
        assert len(scan_res["red_flags"]) >= 2

    def test_status_metrics(self, engine: TenderEngine) -> None:
        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "TenderEngine"
        assert "metrics" in status
        assert "total_tenders" in status["metrics"]


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestTenderCLI:
    """Test Typer CLI surface for mekong tender commands."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_overview_help(self, app) -> None:
        result = runner.invoke(app, ["tender", "--help"])
        assert result.exit_code == 0
        assert "public procurement" in result.output.lower() or "tender" in result.output.lower()

    def test_cli_overview_json(self, app) -> None:
        result = runner.invoke(app, ["tender", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "operational"

    def test_cli_method_advisory(self, app) -> None:
        result = runner.invoke(app, ["tender", "method", "CONSULTING", "400000000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["recommended_method"] == "DIRECT_CONTRACTING"

        result_open = runner.invoke(app, ["tender", "method", "WORKS", "15000000000", "--json"])
        assert result_open.exit_code == 0
        data_open = json.loads(result_open.output)
        assert data_open["recommended_method"] == "OPEN_BIDDING"

    def test_cli_create_tender(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "tender",
                "create",
                "Gói thầu nâng cấp hệ thống mạng",
                "Sở Khoa học và Công nghệ",
                "3500000000",
                "--type",
                "GOODS",
                "--days",
                "15",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "tender_id" in data
        assert data["procurement_method"] == "COMPETITIVE_QUOTATION"

    def test_cli_eval_bid(self, app) -> None:
        # First create a tender
        c_res = runner.invoke(
            app,
            ["tender", "create", "Gói phần mềm kế toán", "Cục Thuế", "1500000000", "--type", "GOODS", "--json"],
        )
        t_id = json.loads(c_res.output)["tender_id"]

        result = runner.invoke(
            app,
            [
                "tender",
                "eval",
                t_id,
                "Công Ty Phần Mềm Mekong",
                "1400000000",
                "--tax-id",
                "0109988776",
                "--revenue",
                "3000000000",
                "--similar",
                "1200000000",
                "--tech-score",
                "88",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["overall_qualified"] is True
        assert data["recommendation"] == "ĐỀ NGHỊ TRÚNG THẦU"

    def test_cli_collusion_scan(self, app) -> None:
        c_res = runner.invoke(
            app,
            ["tender", "create", "Gói bảo trì hệ thống", "Viện Kiểm sát", "800000000", "--type", "NON_CONSULTING", "--json"],
        )
        t_id = json.loads(c_res.output)["tender_id"]

        result = runner.invoke(app, ["tender", "collusion-scan", t_id, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["collusion_risk"] in ("LOW", "MEDIUM", "HIGH")

    def test_cli_list_tenders(self, app) -> None:
        result = runner.invoke(app, ["tender", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "tenders" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["tender", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Server Integration Tests
# ---------------------------------------------------------------------------


class TestTenderMCP:
    """Test tender tools in pure-Python and FastMCP servers."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_tender_collusion_scan,
            handle_tender_create,
            handle_tender_eval,
            handle_tender_list,
            handle_tender_method,
            handle_tender_status,
        )

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_tender_method" in tool_names
        assert "mekong_tender_create" in tool_names
        assert "mekong_tender_eval" in tool_names
        assert "mekong_tender_collusion_scan" in tool_names
        assert "mekong_tender_list" in tool_names
        assert "mekong_tender_status" in tool_names

        assert "mekong_tender_method" in CORE_HANDLERS
        assert "tender_method" in CORE_HANDLERS
        assert "mekong_tender_create" in CORE_HANDLERS
        assert "tender_create" in CORE_HANDLERS

        # Method advisory handler
        m_res = json.loads(
            handle_tender_method({
                "package_type": "CONSULTING",
                "budget_vnd": 300_000_000.0,
            })
        )
        assert m_res["ok"] is True
        assert m_res["recommended_method"] == "DIRECT_CONTRACTING"

        # Create tender handler
        c_res = json.loads(
            handle_tender_create({
                "package_name": "Gói thiết bị số hóa tài liệu",
                "procuring_entity": "Trung tâm Lưu trữ Quốc gia",
                "budget_vnd": 1_200_000_000.0,
                "package_type": "GOODS",
            })
        )
        assert c_res["ok"] is True
        t_id = c_res["tender_id"]

        # Bid eval handler
        e_res = json.loads(
            handle_tender_eval({
                "tender_id": t_id,
                "bidder_name": "Tập đoàn Viễn thông Alpha",
                "bid_price_vnd": 1_100_000_000.0,
                "bidder_tax_id": "0109876543",
                "revenue_3yr_avg_vnd": 3_000_000_000.0,
                "similar_contract_val_vnd": 1_000_000_000.0,
                "tech_score": 85.0,
                "has_valid_security": True,
            })
        )
        assert e_res["ok"] is True
        assert e_res["overall_qualified"] is True

        # Collusion scan handler
        cs_res = json.loads(handle_tender_collusion_scan({"tender_id": t_id}))
        assert cs_res["ok"] is True

        # List handler
        l_res = json.loads(handle_tender_list({"status": "ALL"}))
        assert l_res["ok"] is True
        assert len(l_res["tenders"]) >= 1

        # Status handler
        s_res = json.loads(handle_tender_status({}))
        assert s_res["ok"] is True
        assert "metrics" in s_res

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res = json.loads(
            server._handle_tender_method(
                package_type="GOODS",
                budget_vnd=800_000_000.0,
            )
        )
        assert res["ok"] is True
        assert res["recommended_method"] == "DIRECT_CONTRACTING"

        stat = json.loads(server._handle_tender_status())
        assert stat["ok"] is True
        assert "metrics" in stat
