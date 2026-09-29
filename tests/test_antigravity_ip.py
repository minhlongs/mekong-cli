# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Intellectual Property (IP), Trademark, Patent & Copyright Engine (Phase 49)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.ip_engine import (
    NICE_CLASSES,
    STATUTORY_FEES_VND,
    IPEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestIPCoreBoundary:
    """Ensure IPEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/ip_engine.py")
        assert source_path.exists(), "ip_engine.py must exist"

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


class TestIPEngine:
    """Test IPEngine business logic, algorithms, and persistence."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> IPEngine:
        db_file = tmp_path / "test_ip.db"
        return IPEngine(db_path=db_file)

    def test_nice_classes_and_fee_constants(self) -> None:
        assert "09" in NICE_CLASSES
        assert "35" in NICE_CLASSES
        assert "42" in NICE_CLASSES
        assert STATUTORY_FEES_VND["TM_FILING_FEE"] == 150_000
        assert STATUTORY_FEES_VND["COPYRIGHT_SOFTWARE_FEE"] == 100_000

    def test_register_trademark(self, engine: IPEngine) -> None:
        res = engine.register_trademark(
            mark_name="MekongAgent",
            nice_class="09",
            applicant_name="Công Ty AI Mekong",
            goods_services_spec="Phần mềm đại lý tự hành và mô hình ngôn ngữ lớn",
        )
        assert res["ok"] is True
        assert res["mark_name"] == "MekongAgent"
        assert res["nice_class"] == "09"
        assert res["status"] == "FILED_FORMAL_EXAMINATION"
        assert res["official_fee_vnd"] == 1_000_000
        assert "IP VIETNAM" in res["statutory_authority"]

    def test_search_trademark_similarity_conflict(self, engine: IPEngine) -> None:
        res = engine.search_trademark_similarity(mark_name="MekongMind", nice_class="09")
        assert res["ok"] is True
        assert res["highest_similarity_score"] >= 0.70
        assert res["overall_conflict_risk"] in ("HIGH", "MEDIUM")
        assert len(res["top_similar_marks"]) >= 1

    def test_search_trademark_similarity_distinctive(self, engine: IPEngine) -> None:
        res = engine.search_trademark_similarity(mark_name="XylophoniumOmegaZ99", nice_class="09")
        assert res["ok"] is True
        assert res["overall_conflict_risk"] == "LOW"
        assert "KHẢ NĂNG PHÂN BIỆT CAO" in res["legal_assessment"]

    def test_draft_patent_specification(self, engine: IPEngine) -> None:
        res = engine.draft_patent_specification(
            title="Phương pháp Điều phối Đa tác tử Tự phục hồi",
            technical_field="Hệ thống Phần mềm Phân tán và Trí tuệ Nhân tạo",
            applicant_name="Viện Công Nghệ Mekong",
            independent_claims=1,
            dependent_claims=2,
        )
        assert res["ok"] is True
        assert res["patent_id"].startswith("PAT-")
        assert res["total_claims_count"] == 3
        assert len(res["claims"]) == 3
        assert res["claims"][0]["type"] == "INDEPENDENT"
        assert res["claims"][1]["type"] == "DEPENDENT"
        assert "field_of_invention" in res["sections"]
        assert "claims" in res

    def test_register_software_copyright(self, engine: IPEngine) -> None:
        res = engine.register_software_copyright(
            software_name="Mekong CLI Runtime",
            author_name="Kỹ sư Trưởng Mekong",
            version="1.0.0",
            repository_url="https://github.com/minhlongs/mekong-cli",
            lines_of_code=45000,
        )
        assert res["ok"] is True
        assert res["copyright_id"].startswith("COPY-")
        assert res["software_name"] == "Mekong CLI Runtime"
        assert len(res["required_dossier_items"]) == 5
        assert res["official_fee_vnd"] == 100_000

    def test_calculate_statutory_fees(self, engine: IPEngine) -> None:
        fees = engine.calculate_statutory_fees(
            trademark_classes=1,
            patent_claims=1,
            software_copyrights=1,
        )
        assert fees["ok"] is True
        assert fees["trademark_fees_vnd"] == 1_000_000
        assert fees["patent_fees_vnd"] == 1_590_000
        assert fees["software_copyright_fees_vnd"] == 100_000
        assert fees["total_official_fees_vnd"] == 2_690_000

    def test_list_portfolio_and_status(self, engine: IPEngine) -> None:
        engine.register_trademark("BrandAlpha", "42")
        engine.draft_patent_specification("InventionBeta", "Robotics")
        engine.register_software_copyright("AppGamma", "Author Delta")

        portfolio = engine.list_portfolio()
        assert portfolio["ok"] is True
        assert portfolio["totals"]["trademarks_count"] >= 1
        assert portfolio["totals"]["patents_count"] >= 1
        assert portfolio["totals"]["software_copyrights_count"] >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "IPEngine"
        assert status["metrics"]["registered_trademarks"] >= 1
        assert status["metrics"]["supported_nice_classes"] >= 7


# ---------------------------------------------------------------------------
# CLI Integration Tests
# ---------------------------------------------------------------------------


class TestIPCLI:
    """Test CLI command suite for mekong ip."""

    def test_ip_overview(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ TÀI SẢN TRÍ TUỆ" in result.output

    def test_ip_overview_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_ip_trademark_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "trademark", "MekongOS", "--class", "09"])
        assert result.exit_code == 0
        assert "ĐÃ THIẾT LẬP HỒ SƠ ĐĂNG KÝ NHÃN HIỆU" in result.output

    def test_ip_trademark_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "trademark", "MekongOS", "--class", "09", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["mark_name"] == "MekongOS"
        assert data["nice_class"] == "09"

    def test_ip_search_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "search", "MekongAI", "--class", "42"])
        assert result.exit_code == 0
        assert "KẾT QUẢ TRA CỨU XUNG ĐỘT NHÃN HIỆU" in result.output

    def test_ip_search_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "search", "MekongAI", "--class", "42", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "overall_conflict_risk" in data

    def test_ip_patent_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "patent", "Hệ thống AI Tự phục hồi", "Xử lý dữ liệu phân tán"])
        assert result.exit_code == 0
        assert "BẢN MÔ TẢ VÀ YÊU CẦU BẢO HỘ SÁNG CHẾ" in result.output

    def test_ip_patent_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "patent", "Hệ thống AI Tự phục hồi", "Xử lý dữ liệu phân tán", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["title"] == "Hệ thống AI Tự phục hồi"
        assert data["total_claims_count"] == 3

    def test_ip_copyright_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "copyright", "Mekong CLI", "Mekong Team"])
        assert result.exit_code == 0
        assert "HỒ SƠ ĐĂNG KÝ QUYỀN TÁC GIẢ PHẦN MỀM" in result.output

    def test_ip_copyright_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "copyright", "Mekong CLI", "Mekong Team", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["software_name"] == "Mekong CLI"

    def test_ip_fees_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "fees", "--tm-classes", "2", "--pat-claims", "3"])
        assert result.exit_code == 0
        assert "BẢNG TÍNH LỆ PHÍ NHÀ NƯỚC SỞ HỮU TRÍ TUỆ" in result.output

    def test_ip_fees_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "fees", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["total_official_fees_vnd"] == 2_690_000

    def test_ip_list_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "list"])
        assert result.exit_code == 0

    def test_ip_list_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "trademarks" in data

    def test_ip_status_cli(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "status"])
        assert result.exit_code == 0
        assert "THÔNG SỐ QUẢN TRỊ HỆ THỐNG SỞ HỮU TRÍ TUỆ" in result.output

    def test_ip_status_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["ip", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["engine"] == "IPEngine"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestIPMCPParity:
    """Test MCP tool parity on FastMCP and standard JSON-RPC handlers."""

    def test_core_mcp_server_ip_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        srv = MekongMcpServer()
        res_tm = json.loads(srv._handle_ip_trademark(mark_name="MekongAgent", nice_class="09"))
        assert res_tm["ok"] is True
        assert res_tm["nice_class"] == "09"

        res_search = json.loads(srv._handle_ip_search(mark_name="MekongAI", nice_class="42"))
        assert res_search["ok"] is True

        res_pat = json.loads(srv._handle_ip_patent(title="AI Agent Scheduler", technical_field="Distributed Systems"))
        assert res_pat["ok"] is True

        res_cp = json.loads(srv._handle_ip_copyright(software_name="Agent OS", author_name="Dev Lead"))
        assert res_cp["ok"] is True

        res_fees = json.loads(srv._handle_ip_fees(trademark_classes=1, patent_claims=1))
        assert res_fees["ok"] is True

        res_status = json.loads(srv._handle_ip_status())
        assert res_status["ok"] is True
        assert res_status["engine"] == "IPEngine"

    def test_scripts_mcp_server_ip_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_ip_copyright,
            handle_ip_fees,
            handle_ip_patent,
            handle_ip_search,
            handle_ip_status,
            handle_ip_trademark,
        )

        res_tm = json.loads(handle_ip_trademark({"mark_name": "MekongKernel", "nice_class": "09"}))
        assert res_tm["ok"] is True

        res_search = json.loads(handle_ip_search({"mark_name": "KernelX", "nice_class": "09"}))
        assert res_search["ok"] is True

        res_pat = json.loads(handle_ip_patent({"title": "Quantum Circuit Simulator", "technical_field": "Quantum Computing"}))
        assert res_pat["ok"] is True

        res_cp = json.loads(handle_ip_copyright({"software_name": "QuantumLib", "author_name": "Dr. Alice"}))
        assert res_cp["ok"] is True

        res_fees = json.loads(handle_ip_fees({"trademark_classes": 2, "patent_claims": 2}))
        assert res_fees["ok"] is True

        res_status = json.loads(handle_ip_status({}))
        assert res_status["ok"] is True
        assert res_status["engine"] == "IPEngine"
