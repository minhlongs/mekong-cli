# Mekong CLI — Pure Standard-Library Vendor Marketplace Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_vendor.py — Comprehensive tests for Autonomous Vendor Marketplace & Provider Governance Engine.
Verifies core engine, CLI command suite, dual MCP tools, and zero-dependency standard library boundary.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.vendor_engine import VendorEngine, get_vendor_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def clean_engine(tmp_path: Path) -> VendorEngine:
    """Fixture providing an isolated VendorEngine instance with a temporary database."""
    db_file = tmp_path / "vendor_test.db"
    return VendorEngine(db_path=db_file)


class TestVendorEngine:
    """Unit tests for the VendorEngine core implementation."""

    def test_engine_init_and_default_seeds(self, clean_engine: VendorEngine) -> None:
        status = clean_engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_vendors"] >= 5
        assert status["active_vendors"] >= 5
        assert "agent" in status["supported_types"]

        # Check default seeded vendor
        claude = clean_engine.get_vendor("anthropic-router")
        assert claude is not None
        assert claude["name"] == "anthropic-router"
        assert claude["trust_score"] >= 95.0
        assert "llm_routing" in claude["capabilities"]

    def test_onboard_vendor_and_retrieve(self, clean_engine: VendorEngine) -> None:
        v = clean_engine.onboard_vendor(
            name="custom-rag-agent",
            vendor_type="agent",
            version="1.2.0",
            description="Autonomous RAG retrieval and indexing agent",
            author="Vector Corp",
            capabilities=["rag_search", "document_chunking"],
            trust_score=92.0,
        )
        assert v["name"] == "custom-rag-agent"
        assert v["vendor_type"] == "agent"
        assert v["version"] == "1.2.0"
        assert v["author"] == "Vector Corp"
        assert v["trust_score"] == 92.0
        assert v["status"] == "active"
        assert "rag_search" in v["capabilities"]

        retrieved = clean_engine.get_vendor("custom-rag-agent")
        assert retrieved is not None
        assert retrieved["id"] == v["id"]

    def test_onboard_vendor_update(self, clean_engine: VendorEngine) -> None:
        clean_engine.onboard_vendor(
            name="test-plugin",
            vendor_type="plugin",
            version="1.0.0",
            trust_score=80.0,
        )
        updated = clean_engine.onboard_vendor(
            name="test-plugin",
            vendor_type="plugin",
            version="2.0.0",
            trust_score=95.0,
        )
        assert updated["version"] == "2.0.0"
        assert updated["trust_score"] == 95.0

    def test_list_vendors_filtering(self, clean_engine: VendorEngine) -> None:
        all_vendors = clean_engine.list_vendors()
        assert len(all_vendors) >= 5

        providers = clean_engine.list_vendors(vendor_type="provider")
        assert len(providers) >= 2
        for p in providers:
            assert p["vendor_type"] == "provider"

        clean_engine.delist_vendor("anthropic-router")
        active = clean_engine.list_vendors(status="active")
        delisted = clean_engine.list_vendors(status="delisted")
        assert any(d["name"] == "anthropic-router" for d in delisted)
        assert not any(a["name"] == "anthropic-router" for a in active)

    def test_delist_vendor(self, clean_engine: VendorEngine) -> None:
        res = clean_engine.delist_vendor("deepmind-gemini", reason="Scheduled maintenance")
        assert res["success"] is True
        assert res["status"] == "delisted"
        assert res["reason"] == "Scheduled maintenance"

        vendor = clean_engine.get_vendor("deepmind-gemini")
        assert vendor is not None
        assert vendor["status"] == "delisted"

        err = clean_engine.delist_vendor("nonexistent-vendor-xyz")
        assert err["success"] is False
        assert "not found" in err["error"]

    def test_audit_vendor(self, clean_engine: VendorEngine) -> None:
        audit = clean_engine.audit_vendor("qdrant-vector", audit_type="security")
        assert audit["name"] == "qdrant-vector"
        assert audit["audit_type"] == "security"
        assert audit["audit_score"] >= 80.0
        assert audit["status"] == "PASSED"
        assert len(audit["findings"]) > 0
        assert audit["audit_id"].startswith("aud_")

        # Verify audit is recorded in status count
        status = clean_engine.get_status()
        assert status["total_audits_performed"] >= 1

        err = clean_engine.audit_vendor("unknown-vendor-abc")
        assert err["success"] is False
        assert "not found" in err["error"]


class TestVendorCli:
    """CLI tests for `mekong vendor` commands."""

    def test_vendor_overview_cli(self) -> None:
        result = runner.invoke(app, ["vendor"])
        assert result.exit_code == 0
        assert "Mekong Sovereign Vendor Marketplace" in result.output

    def test_vendor_overview_json_cli(self) -> None:
        result = runner.invoke(app, ["vendor", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "total_vendors" in data
        assert "recent_vendors" in data

    def test_vendor_onboard_cli(self) -> None:
        result = runner.invoke(
            app,
            [
                "vendor",
                "onboard",
                "cli-test-agent",
                "--type",
                "agent",
                "--version",
                "1.0.0",
                "--description",
                "Test agent from CLI",
                "--author",
                "CLI Suite",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "cli-test-agent"
        assert data["vendor_type"] == "agent"

    def test_vendor_list_cli(self) -> None:
        result = runner.invoke(app, ["vendor", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_vendor_audit_cli(self) -> None:
        result = runner.invoke(
            app,
            ["vendor", "audit", "anthropic-router", "--type", "security", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "anthropic-router"
        assert data["status"] == "PASSED"

    def test_vendor_delist_cli(self) -> None:
        # Delist test agent
        result = runner.invoke(
            app,
            ["vendor", "delist", "cli-test-agent", "--reason", "Testing cleanup", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["status"] == "delisted"


class TestVendorMcpParity:
    """Verifies FastMCP and JSON-RPC 2.0 dual server parity for vendor tools."""

    def test_scripts_mcp_vendor_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_vendor_assess,
            handle_vendor_list,
            handle_vendor_onboard,
        )

        # 1. Onboard
        onboard_res = handle_vendor_onboard({
            "name": "mcp-test-vendor",
            "vendor_type": "tool",
            "version": "1.0.0",
            "description": "MCP registered tool",
            "author": "MCP Tester",
            "trust_score": 90.0,
        })
        onboard_data = json.loads(onboard_res)
        assert onboard_data["name"] == "mcp-test-vendor"
        assert onboard_data["vendor_type"] == "tool"

        # 2. List
        list_res = handle_vendor_list({"vendor_type": "all", "limit": 10})
        list_data = json.loads(list_res)
        assert isinstance(list_data, list)
        assert any(v["name"] == "mcp-test-vendor" for v in list_data)

        # 3. Assess
        assess_res = handle_vendor_assess({"name": "mcp-test-vendor", "audit_type": "compliance"})
        assess_data = json.loads(assess_res)
        assert assess_data["name"] == "mcp-test-vendor"
        assert assess_data["status"] == "PASSED"

    def test_core_mcp_server_vendor_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        # 1. Onboard
        res = server._handle_vendor_onboard(
            name="core-mcp-vendor",
            vendor_type="recipe",
            version="2.1.0",
            trust_score=93.0,
        )
        data = json.loads(res)
        assert data["name"] == "core-mcp-vendor"

        # 2. List
        list_res = server._handle_vendor_list(vendor_type="recipe")
        list_data = json.loads(list_res)
        assert any(v["name"] == "core-mcp-vendor" for v in list_data)

        # 3. Assess
        audit_res = server._handle_vendor_assess(name="core-mcp-vendor", audit_type="performance")
        audit_data = json.loads(audit_res)
        assert audit_data["name"] == "core-mcp-vendor"
        assert audit_data["status"] == "PASSED"

        # 4. Aliases
        assert server._handle_mekong_vendor_onboard == server._handle_vendor_onboard
        assert server._handle_mekong_vendor_list == server._handle_vendor_list
        assert server._handle_mekong_vendor_assess == server._handle_vendor_assess


class TestVendorCoreBoundary:
    """Strict AST standard-library boundary verification for `src/core/vendor_engine.py`."""

    def test_no_prohibited_imports_in_vendor_engine(self) -> None:
        vendor_file = Path("src/core/vendor_engine.py")
        assert vendor_file.exists(), "src/core/vendor_engine.py must exist"

        tree = ast.parse(vendor_file.read_text(encoding="utf-8"))

        prohibited_prefixes = (
            "requests",
            "httpx",
            "aiohttp",
            "urllib3",
            "typer",
            "rich",
            "click",
            "fastmcp",
            "mcp",
            "pydantic",
            "openai",
            "anthropic",
            "google",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in prohibited_prefixes:
                        assert not alias.name.startswith(prefix), (
                            f"Prohibited import '{alias.name}' detected in src/core/vendor_engine.py"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for prefix in prohibited_prefixes:
                        assert not node.module.startswith(prefix), (
                            f"Prohibited from-import '{node.module}' detected in src/core/vendor_engine.py"
                        )
