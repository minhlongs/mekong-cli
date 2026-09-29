# Mekong CLI — Pure Standard-Library Billing & Reconciliation Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_billing.py — Comprehensive tests for Autonomous Billing & Usage Reconciliation Engine.
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
from src.core.billing_engine import BillingEngine, get_billing_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def clean_engine(tmp_path: Path) -> BillingEngine:
    """Fixture providing an isolated BillingEngine instance with a temporary database."""
    db_file = tmp_path / "billing_test.db"
    return BillingEngine(db_path=db_file)


class TestBillingEngine:
    """Unit tests for the BillingEngine core implementation."""

    def test_engine_init_and_status(self, clean_engine: BillingEngine) -> None:
        status = clean_engine.get_engine_status()
        assert status["status"] == "HEALTHY"
        assert status["pricing_tiers_count"] >= 4
        assert "USD" in status["supported_currencies"]
        assert "VND" in status["supported_currencies"]
        assert status["exchange_rate_vnd_per_usd"] == 25400

    def test_get_pricing_tiers(self, clean_engine: BillingEngine) -> None:
        tiers = clean_engine.get_pricing_tiers()
        assert "free" in tiers
        assert "developer" in tiers
        assert "pro" in tiers
        assert "enterprise" in tiers
        assert tiers["pro"]["included_mcu"] == 3000
        assert tiers["pro"]["rates"]["llm_tokens"] == 0.001

    def test_record_usage_and_idempotency(self, clean_engine: BillingEngine) -> None:
        rec1 = clean_engine.record_usage(
            license_key="test_lic_100",
            event_type="llm_tokens",
            quantity=5000.0,
            idempotency_key="key_12345",
            tier="pro",
        )
        assert rec1["license_key"] == "test_lic_100"
        assert rec1["event_type"] == "llm_tokens"
        assert rec1["quantity"] == 5000.0
        assert rec1["total_cost"] == 5.0  # 5000 * 0.001
        assert rec1["is_duplicate"] is False

        # Idempotent re-submission
        rec2 = clean_engine.record_usage(
            license_key="test_lic_100",
            event_type="llm_tokens",
            quantity=5000.0,
            idempotency_key="key_12345",
            tier="pro",
        )
        assert rec2["is_duplicate"] is True
        assert rec2["id"] == rec1["id"]

    def test_simulate_billing(self, clean_engine: BillingEngine) -> None:
        clean_engine.record_usage(
            license_key="lic_sim",
            event_type="llm_tokens",
            quantity=10000.0,
            tier="pro",
        )
        clean_engine.record_usage(
            license_key="lic_sim",
            event_type="agent_minutes",
            quantity=60.0,
            tier="pro",
        )

        inv = clean_engine.simulate_billing(license_key="lic_sim", tier="pro", period_days=30)
        assert inv["license_key"] == "lic_sim"
        assert inv["tier"] == "pro"
        assert inv["base_monthly_usd"] == 199.0
        assert "llm_tokens" in inv["itemized"]
        assert "agent_minutes" in inv["itemized"]
        assert inv["total_usd"] >= 199.0
        assert inv["total_vnd"] == int(inv["total_usd"] * 25400)

    def test_reconcile_usage(self, clean_engine: BillingEngine) -> None:
        clean_engine.record_usage(
            license_key="lic_rec",
            event_type="api_calls",
            quantity=500.0,
            tier="pro",
        )
        audit = clean_engine.reconcile_usage(license_key="lic_rec")
        assert audit["events_reconciled"] == 1
        assert audit["total_volume_metered"] == 500.0
        assert audit["variance_detected"] is False
        assert audit["status"] == "clean"

    def test_get_billing_status_and_health(self, clean_engine: BillingEngine) -> None:
        clean_engine.record_usage(
            license_key="lic_status_test",
            event_type="mcu_credits",
            quantity=1500.0,
            tier="pro",
        )
        st = clean_engine.get_billing_status(license_key="lic_status_test")
        assert st["license_key"] == "lic_status_test"
        assert st["status"] == "HEALTHY"
        assert st["quota_consumed_mcu"] == 1500.0
        assert st["quota_usage_percent"] == 50.0

        # Push to warning threshold (>80%)
        clean_engine.record_usage(
            license_key="lic_status_test",
            event_type="mcu_credits",
            quantity=1000.0,
            tier="pro",
        )
        st2 = clean_engine.get_billing_status(license_key="lic_status_test")
        assert st2["status"] == "WARNING"

    def test_sync_usage_records(self, clean_engine: BillingEngine) -> None:
        clean_engine.record_usage(license_key="lic_sync", event_type="storage_mb", quantity=200.0)
        res = clean_engine.sync_usage_records()
        assert res["status"] == "SUCCESS"
        assert res["synced_records"] >= 1


class TestBillingCli:
    """CLI surface tests for `mekong billing`."""

    def test_cli_billing_overview_json(self) -> None:
        result = runner.invoke(app, ["billing", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "HEALTHY"
        assert "tiers" in data
        assert "pricing_tiers_count" in data

    def test_cli_billing_overview_console(self) -> None:
        result = runner.invoke(app, ["billing"])
        assert result.exit_code == 0
        assert "Mekong Autonomous Billing Engine" in result.stdout

    def test_cli_billing_simulate_json(self) -> None:
        result = runner.invoke(app, ["billing", "simulate", "--tier", "developer", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["tier"] == "developer"
        assert "total_usd" in data
        assert "total_vnd" in data

    def test_cli_billing_submit_usage_json(self) -> None:
        result = runner.invoke(
            app,
            [
                "billing",
                "submit-usage",
                "--event-type",
                "api_calls",
                "--value",
                "250",
                "--license",
                "cli_test_lic",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["license_key"] == "cli_test_lic"
        assert data["event_type"] == "api_calls"
        assert data["quantity"] == 250.0

    def test_cli_billing_status_json(self) -> None:
        result = runner.invoke(app, ["billing", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "quota_allocated_mcu" in data
        assert "status" in data

    def test_cli_billing_reconcile_json(self) -> None:
        result = runner.invoke(app, ["billing", "reconcile", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "events_reconciled" in data
        assert "status" in data

    def test_cli_billing_sync_json(self) -> None:
        result = runner.invoke(app, ["billing", "sync", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "SUCCESS"

    def test_cli_billing_tiers_json(self) -> None:
        result = runner.invoke(app, ["billing", "tiers", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "free" in data
        assert "enterprise" in data


class TestBillingMcpTools:
    """Parity tests for FastMCP and JSON-RPC MCP servers."""

    def test_scripts_mcp_billing_tools(self) -> None:
        from scripts.mcp_server import (
            handle_billing_record_usage,
            handle_billing_simulate,
            handle_billing_status,
        )

        sim_out = handle_billing_simulate({"license_key": "mcp_lic", "tier": "developer"})
        sim_data = json.loads(sim_out)
        assert sim_data["license_key"] == "mcp_lic"
        assert sim_data["tier"] == "developer"

        rec_out = handle_billing_record_usage({
            "license_key": "mcp_lic",
            "event_type": "llm_tokens",
            "quantity": 1000.0,
        })
        rec_data = json.loads(rec_out)
        assert rec_data["license_key"] == "mcp_lic"
        assert rec_data["quantity"] == 1000.0

        st_out = handle_billing_status({"license_key": "mcp_lic"})
        st_data = json.loads(st_out)
        assert st_data["license_key"] == "mcp_lic"
        assert "quota_allocated_mcu" in st_data

    def test_core_mcp_billing_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        sim_out = server._handle_billing_simulate(license_key="core_lic", tier="pro")
        sim_data = json.loads(sim_out)
        assert sim_data["license_key"] == "core_lic"

        rec_out = server._handle_billing_record_usage(
            license_key="core_lic",
            event_type="agent_minutes",
            quantity=15.0,
        )
        rec_data = json.loads(rec_out)
        assert rec_data["license_key"] == "core_lic"
        assert rec_data["quantity"] == 15.0

        st_out = server._handle_billing_status(license_key="core_lic")
        st_data = json.loads(st_out)
        assert st_data["license_key"] == "core_lic"


class TestBillingBoundary:
    """Enforce strict standard-library-only core boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        source_path = Path("src/core/billing_engine.py")
        assert source_path.exists()
        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        prohibited_modules = {
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "fastapi",
            "pydantic",
            "click",
            "typer",
            "rich",
            "boto3",
            "google",
            "anthropic",
            "openai",
        }

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        violations = imported_modules.intersection(prohibited_modules)
        assert not violations, f"Boundary violation: billing_engine.py imports prohibited modules: {violations}"
