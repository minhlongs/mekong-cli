"""
Test Suite for Vietnamese Advertising, Media & Digital Marketing Compliance Suite (Phase 84).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- AdvertisingEngine domain logic (content checks, XNNDQC approvals, OOH billboards, cross-border 24h takedown, broadcast airtime ratios).
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
from src.core.advertising_engine import AdvertisingEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestAdvertisingBoundary:
    """Verifies that advertising_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "advertising_engine.py")
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


class TestAdvertisingEngine:
    """Tests core business logic of AdvertisingEngine."""

    def test_check_ad_content_compliant(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.check_ad_content(
            text="Cà phê nguyên chất Mekong thơm ngon từ vùng cao nguyên đất đỏ bazan.",
            product_type="general",
        )
        assert res["status"] == "COMPLIANT"
        assert res["is_compliant"] is True
        assert len(res["detected_prohibited_terms"]) == 0
        assert res["estimated_fine_min_vnd"] == 0

    def test_check_ad_content_prohibited_superlatives(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.check_ad_content(
            text="Trà thảo mộc Mekong số 1 chất lượng, tốt nhất thị trường hiện nay.",
            product_type="general",
            has_evidence=False,
        )
        assert res["status"] == "NON_COMPLIANT"
        assert res["is_compliant"] is False
        assert "số 1" in res["detected_prohibited_terms"]
        assert "tốt nhất" in res["detected_prohibited_terms"]
        assert res["estimated_fine_min_vnd"] >= 10000000

    def test_check_ad_content_with_evidence(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.check_ad_content(
            text="Sản phẩm bình chọn số 1 theo khảo sát người tiêu dùng hàng Việt Nam chất lượng cao.",
            product_type="general",
            has_evidence=True,
        )
        assert res["status"] == "WARNING_REQUIRES_PROOF_VERIFICATION"
        assert res["is_compliant"] is True
        assert res["estimated_fine_min_vnd"] == 0

    def test_check_supplement_missing_disclaimer(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.check_ad_content(
            text="Viên nang bổ não Mekong Ginkgo giúp tăng cường tuần hoàn não hiệu quả cao.",
            product_type="supplement",
        )
        assert res["status"] == "NON_COMPLIANT"
        assert any("không phải là thuốc" in d for d in res["missing_disclaimers"])

    def test_check_cure_claims_severe_fine(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.check_ad_content(
            text="Cao dược liệu bí truyền trị dứt điểm viêm xoang và chữa khỏi hoàn toàn trong 7 ngày.",
            product_type="supplement",
        )
        assert res["status"] == "NON_COMPLIANT"
        assert res["estimated_fine_min_vnd"] >= 50000000

    def test_register_content_approval(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.register_content_approval(
            product_name="Mekong Artichoke Detox",
            product_category="supplement",
            applicant_name="Công ty Dược Mekong",
            license_number="DK-8899/2026/BYT-ATTP",
            validity_years=2,
        )
        assert res["status"] == "APPROVED"
        assert res["xnndqc_code"].startswith("XNNDQC-")
        assert res["product_category"] == "supplement"

    def test_verify_ooh_billboard_highway_compliant(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_ooh_billboard(
            location_type="highway",
            area_sqm=110.0,
            height_m=14.0,
            clearance_m=5.5,
        )
        assert res["status"] == "APPROVED"
        assert len(res["deficiencies"]) == 0

    def test_verify_ooh_billboard_violations(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_ooh_billboard(
            location_type="urban_standalone",
            area_sqm=55.0,  # exceeds 40 sqm
            height_m=12.0,  # exceeds 10m
            clearance_m=2.5,  # below 4.0m
        )
        assert res["status"] == "REJECTED"
        assert len(res["deficiencies"]) == 3

    def test_verify_ooh_banner_duration(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_ooh_billboard(
            location_type="banner",
            area_sqm=8.0,
            height_m=1.8,
            clearance_m=3.5,
            duration_days=20,  # exceeds 15 days
            structure_type="banner",
        )
        assert res["status"] == "REJECTED"
        assert any("15 ngày" in d for d in res["deficiencies"])

    def test_track_cross_border_takedown_on_time(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        notice = "2026-09-29T08:00:00"
        resolved = "2026-09-29T20:00:00"  # 12 hours later <= 24h
        res = engine.track_cross_border_takedown(
            platform="Facebook",
            ad_id="AD-FB-12345",
            requester="Cục Phát thanh, Truyền hình và TTĐT",
            violation_type="Quảng cáo cờ bạc trái phép",
            notice_timestamp=notice,
            resolved_timestamp=resolved,
        )
        assert res["status"] == "COMPLIANT_REMOVED_ON_TIME"
        assert res["hours_elapsed"] == 12.0

    def test_track_cross_border_takedown_overdue(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        notice = "2026-09-27T08:00:00"
        resolved = "2026-09-29T12:00:00"  # 52 hours later > 24h
        res = engine.track_cross_border_takedown(
            platform="TikTok",
            ad_id="AD-TK-67890",
            requester="Bộ TTTT",
            violation_type="Quảng cáo bóng cười N2O",
            notice_timestamp=notice,
            resolved_timestamp=resolved,
        )
        assert res["status"] == "VIOLATION_TAKEDOWN_OVERDUE"
        assert res["hours_elapsed"] > 24.0

    def test_verify_broadcast_ratio_terrestrial_compliant(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_broadcast_ratio(
            channel_type="terrestrial",
            program_duration_min=90.0,
            ad_duration_min=8.0,  # 8.89% <= 10%
            break_count=2,
            max_break_min=4.0,
        )
        assert res["status"] == "COMPLIANT"
        assert res["excess_min"] == 0.0

    def test_verify_broadcast_ratio_pay_tv_exceeded(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_broadcast_ratio(
            channel_type="pay_tv",
            program_duration_min=100.0,
            ad_duration_min=8.0,  # 8% > 5% allowed
            break_count=1,
            max_break_min=3.0,
        )
        assert res["status"] == "NON_COMPLIANT"
        assert res["excess_min"] == 3.0  # 8 - 5 = 3 min

    def test_verify_broadcast_breaks_exceeded(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        res = engine.verify_broadcast_ratio(
            channel_type="terrestrial",
            program_duration_min=120.0,
            ad_duration_min=10.0,
            break_count=3,  # exceeds 2 breaks
            max_break_min=6.0,  # exceeds 5 min
        )
        assert res["status"] == "NON_COMPLIANT"
        assert len(res["deficiencies"]) == 2

    def test_list_records_and_status(self, temp_db):
        engine = AdvertisingEngine(db_path=temp_db)
        engine.check_ad_content("Quảng cáo mẫu Mekong", "general")
        engine.register_content_approval("Sữa Mekong", "supplement", "Công ty Sữa", "DK-01")
        engine.verify_ooh_billboard("highway", 100.0, 12.0, 5.5)

        checks = engine.list_records("checks")
        approvals = engine.list_records("approvals")
        billboards = engine.list_records("billboards")

        assert len(checks) >= 1
        assert len(approvals) >= 1
        assert len(billboards) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_content_checks"] >= 1


class TestAdvertisingCLI:
    """Tests CLI commands using Typer CliRunner."""

    def setup_method(self):
        self.app = build_app()
        self.runner = CliRunner()

    def test_cli_help(self):
        result = self.runner.invoke(self.app, ["advertising", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Advertising" in result.output

    def test_cli_status_json(self):
        result = self.runner.invoke(self.app, ["advertising", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"

    def test_cli_check_json(self):
        result = self.runner.invoke(
            self.app,
            ["advertising", "check", "Sản phẩm tốt nhất Mekong số 1 chất lượng", "--type", "general", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "NON_COMPLIANT"

    def test_cli_approval_json(self):
        result = self.runner.invoke(
            self.app,
            ["advertising", "approval", "Trà Gừng Mekong", "--category", "supplement", "--applicant", "Mekong Corp", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "APPROVED"

    def test_cli_billboard_json(self):
        result = self.runner.invoke(
            self.app,
            ["advertising", "billboard", "highway", "--area", "110", "--height", "14", "--clearance", "5.5", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "APPROVED"

    def test_cli_takedown_json(self):
        result = self.runner.invoke(
            self.app,
            ["advertising", "takedown", "Facebook", "--ad-id", "AD-9988", "--violation", "Quảng cáo sai sự thật", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["takedown_id"].startswith("TD-")

    def test_cli_broadcast_json(self):
        result = self.runner.invoke(
            self.app,
            ["advertising", "broadcast", "terrestrial", "--program-min", "60", "--ad-min", "5", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "COMPLIANT"

    def test_cli_list_json(self):
        result = self.runner.invoke(self.app, ["advertising", "list", "checks", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestAdvertisingMCP:
    """Tests FastMCP and JSON-RPC 2.0 dual engine parity for advertising tools."""

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_advertising_check,
            handle_advertising_approval,
            handle_advertising_billboard,
            handle_advertising_takedown,
            handle_advertising_broadcast,
            handle_advertising_list,
            handle_advertising_status,
        )

        chk_res = json.loads(handle_advertising_check({"text": "Quảng cáo chuẩn Mekong", "product_type": "general"}))
        assert chk_res["status"] == "COMPLIANT"

        app_res = json.loads(handle_advertising_approval({"product_name": "Serum Mekong C", "product_category": "cosmetic"}))
        assert app_res["status"] == "APPROVED"

        bb_res = json.loads(handle_advertising_billboard({"location_type": "highway", "area_sqm": 100.0}))
        assert bb_res["status"] == "APPROVED"

        td_res = json.loads(handle_advertising_takedown({"platform": "Google", "ad_id": "G-1234"}))
        assert "takedown_id" in td_res

        bc_res = json.loads(handle_advertising_broadcast({"channel_type": "terrestrial", "program_duration_min": 60.0, "ad_duration_min": 5.0}))
        assert bc_res["status"] == "COMPLIANT"

        ls_res = json.loads(handle_advertising_list({"category": "checks"}))
        assert isinstance(ls_res, list)

        st_res = json.loads(handle_advertising_status({}))
        assert st_res["status"] == "HEALTHY"

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        chk = json.loads(server._handle_advertising_check(text="Quảng cáo an toàn", product_type="general"))
        assert chk["status"] == "COMPLIANT"

        status = json.loads(server._handle_advertising_status())
        assert status["status"] == "HEALTHY"
