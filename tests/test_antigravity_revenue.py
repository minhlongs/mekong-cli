# Mekong CLI — Pure Standard-Library Revenue Operations Engine Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration tests for Revenue Operations & Financial Intelligence Suite.

Covers:
- Pure standard library RevenueEngine core and SQLite persistence
- MRR, ARR, ARPU, LTV, NRR, and MRR waterfall calculation
- Payment reconciliation and discrepancy detection
- Scenario-based revenue forecasting (conservative, base, aggressive)
- Typer CLI command surface with Rich rendering and --json mode
- Dual-engine MCP tool handlers (FastMCP & pure JSON-RPC)
- AST boundary verification (zero external HTTP or vendor SDK dependencies)
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.revenue_engine import RevenueEngine, get_revenue_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def temp_revenue_engine(tmp_path: Path) -> RevenueEngine:
    """Provide an isolated RevenueEngine with temporary SQLite database."""
    db_file = tmp_path / "test_revenue.db"
    return RevenueEngine(db_path=db_file)


class TestRevenueEngineCore:
    """Core domain logic tests for RevenueEngine."""

    def test_tier_catalog_pricing_and_currencies(self, temp_revenue_engine: RevenueEngine) -> None:
        usd_catalog = temp_revenue_engine.get_tier_catalog(currency="USD")
        assert "starter" in usd_catalog
        assert usd_catalog["starter"]["price"] == 49.0
        assert usd_catalog["starter"]["currency"] == "USD"
        assert usd_catalog["starter"]["credits"] == 300

        vnd_catalog = temp_revenue_engine.get_tier_catalog(currency="VND")
        assert "growth" in vnd_catalog
        assert vnd_catalog["growth"]["price"] == 3784600
        assert vnd_catalog["growth"]["currency"] == "VND"
        assert "VND" in vnd_catalog["growth"]["price_formatted"]

    def test_record_transactions_and_auto_subscription(self, temp_revenue_engine: RevenueEngine) -> None:
        # Record USD transaction
        res1 = temp_revenue_engine.record_transaction(
            customer_id="cust_001",
            amount=49.0,
            customer_name="Alpha Labs",
            currency="USD",
            tier="starter",
            type="subscription",
            gateway="stripe",
        )
        assert res1["id"].startswith("txn_")
        assert res1["amount_usd"] == 49.0
        assert res1["customer_name"] == "Alpha Labs"
        assert res1["subscription_id"] is not None

        # Record VND transaction
        res2 = temp_revenue_engine.record_transaction(
            customer_id="cust_002",
            amount=3784600,
            customer_name="Saigon AI",
            currency="VND",
            tier="growth",
            type="subscription",
            gateway="bank_transfer",
        )
        assert res2["id"].startswith("txn_")
        assert res2["amount_usd"] == 149.0
        assert res2["currency"] == "VND"

        # List transactions
        txns = temp_revenue_engine.list_transactions()
        assert len(txns) == 2

    def test_subscription_lifecycle(self, temp_revenue_engine: RevenueEngine) -> None:
        # Create subscription
        sub = temp_revenue_engine.create_or_renew_subscription(
            customer_id="cust_100",
            tier="scale",
            amount_usd=299.0,
            customer_name="Fintech Pro",
        )
        assert sub["status"] == "active"
        assert sub["tier"] == "scale"
        assert sub["amount_usd"] == 299.0
        assert sub["action"] == "created"

        # Renew / update existing subscription
        sub_renew = temp_revenue_engine.create_or_renew_subscription(
            customer_id="cust_100",
            tier="pro",
            amount_usd=499.0,
            customer_name="Fintech Pro",
        )
        assert sub_renew["action"] == "renewed"
        assert sub_renew["tier"] == "pro"
        assert sub_renew["amount_usd"] == 499.0

        # Cancel subscription
        cancel_res = temp_revenue_engine.cancel_subscription(
            subscription_id=sub["id"],
            reason="Upgraded to dedicated cluster",
        )
        assert cancel_res["success"] is True
        assert cancel_res["status"] == "cancelled"

        # Verify listed subscriptions
        active_subs = temp_revenue_engine.list_subscriptions(status="active")
        cancelled_subs = temp_revenue_engine.list_subscriptions(status="cancelled")
        assert len(active_subs) == 0
        assert len(cancelled_subs) == 1

    def test_metrics_and_waterfall_calculation(self, temp_revenue_engine: RevenueEngine) -> None:
        # Add 2 active subscriptions
        temp_revenue_engine.create_or_renew_subscription("c1", tier="starter", amount_usd=49.0)
        temp_revenue_engine.create_or_renew_subscription("c2", tier="growth", amount_usd=149.0)

        # Add 1 cancelled subscription
        c3 = temp_revenue_engine.create_or_renew_subscription("c3", tier="scale", amount_usd=299.0)
        temp_revenue_engine.cancel_subscription(c3["id"], reason="Budget cut")

        # Record succeeded transactions
        temp_revenue_engine.record_transaction("c1", 49.0, auto_subscription=False)
        temp_revenue_engine.record_transaction("c2", 149.0, auto_subscription=False)
        temp_revenue_engine.record_transaction("c2", 50.0, type="addon", auto_subscription=False)

        metrics = temp_revenue_engine.get_metrics()
        assert metrics["mrr"] == 198.0  # 49 + 149
        assert metrics["arr"] == 198.0 * 12
        assert metrics["total_revenue"] == 248.0  # 49 + 149 + 50
        assert metrics["active_subscriptions"] == 2
        assert metrics["paying_customers"] == 2
        assert metrics["arpu"] == 99.0
        assert metrics["mrr_waterfall"]["expansion_mrr"] == 50.0
        assert metrics["mrr_waterfall"]["churned_mrr"] == 299.0
        assert metrics["churn_rate_pct"] > 0

    def test_payment_reconciliation_and_autofix(self, temp_revenue_engine: RevenueEngine) -> None:
        # Customer 1 has subscription and matching payment
        temp_revenue_engine.create_or_renew_subscription("c1", tier="starter", amount_usd=49.0)
        temp_revenue_engine.record_transaction("c1", 49.0, auto_subscription=False)

        # Customer 2 has subscription but NO payment
        temp_revenue_engine.create_or_renew_subscription("c2", tier="growth", amount_usd=149.0)

        # Run reconciliation without auto_fix
        rec1 = temp_revenue_engine.reconcile_payments(auto_fix=False)
        assert rec1["status"] == "discrepancy_detected"
        assert rec1["discrepancies_count"] == 1
        assert rec1["discrepancies"][0]["customer_id"] == "c2"
        assert rec1["total_expected"] == 198.0
        assert rec1["total_collected"] == 49.0
        assert rec1["net_discrepancy"] == 149.0

        # Run reconciliation with auto_fix
        rec2 = temp_revenue_engine.reconcile_payments(auto_fix=True)
        assert rec2["auto_fix_applied"] is True

        # c2 subscription should now be past_due
        subs = temp_revenue_engine.list_subscriptions(status="past_due")
        assert len(subs) == 1
        assert subs[0]["customer_id"] == "c2"

    def test_revenue_forecasting_scenarios(self, temp_revenue_engine: RevenueEngine) -> None:
        temp_revenue_engine.create_or_renew_subscription("c1", tier="pro", amount_usd=499.0)

        fc_base = temp_revenue_engine.forecast_revenue(months=6, scenario="base")
        assert fc_base["scenario"] == "base"
        assert fc_base["horizon_months"] == 6
        assert len(fc_base["monthly_projections"]) == 6
        assert fc_base["projected_ending_mrr"] > fc_base["starting_mrr"]
        assert fc_base["total_forecasted_revenue"] > 0

        fc_cons = temp_revenue_engine.forecast_revenue(months=3, scenario="conservative")
        assert fc_cons["scenario"] == "conservative"
        assert len(fc_cons["monthly_projections"]) == 3

    def test_engine_status(self, temp_revenue_engine: RevenueEngine) -> None:
        status = temp_revenue_engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["transactions_count"] == 0
        assert status["active_subscriptions"] == 0
        assert "db_path" in status


class TestRevenueCliCommands:
    """Integration tests for Typer CLI commands."""

    def test_cli_revenue_overview_json(self) -> None:
        # using module-level app
        result = runner.invoke(app, ["revenue", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "HEALTHY"
        assert "metrics" in data
        assert "mrr" in data["metrics"]

    def test_cli_revenue_overview_console(self) -> None:
        # using module-level app
        result = runner.invoke(app, ["revenue"])
        assert result.exit_code == 0
        assert "Mekong Revenue Operations Dashboard" in result.stdout
        assert "Monthly Recurring (MRR)" in result.stdout

    def test_cli_revenue_metrics_json(self) -> None:
        # using module-level app
        result = runner.invoke(app, ["revenue", "metrics", "--period", "quarter", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["period"] == "quarter"
        assert "mrr_waterfall" in data

    def test_cli_revenue_catalog(self) -> None:
        # using module-level app
        result_usd = runner.invoke(app, ["revenue", "catalog", "--currency", "USD", "--json"])
        assert result_usd.exit_code == 0
        data_usd = json.loads(result_usd.stdout)
        assert "starter" in data_usd
        assert data_usd["starter"]["price"] == 49.0

        result_vnd = runner.invoke(app, ["revenue", "catalog", "--currency", "VND"])
        assert result_vnd.exit_code == 0
        assert "VND" in result_vnd.stdout

    def test_cli_revenue_record_json(self) -> None:
        # using module-level app
        result = runner.invoke(
            app,
            [
                "revenue",
                "record",
                "test_client_001",
                "--amount",
                "149.0",
                "--name",
                "Acme Corp",
                "--tier",
                "growth",
                "--gateway",
                "stripe",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["customer_id"] == "test_client_001"
        assert data["amount_usd"] == 149.0
        assert data["status"] == "succeeded"

    def test_cli_revenue_reconcile(self) -> None:
        # using module-level app
        result = runner.invoke(app, ["revenue", "reconcile", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_expected" in data
        assert "total_collected" in data

    def test_cli_revenue_forecast(self) -> None:
        # using module-level app
        result = runner.invoke(
            app,
            ["revenue", "forecast", "--months", "3", "--scenario", "aggressive", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["scenario"] == "aggressive"
        assert data["horizon_months"] == 3

    def test_cli_revenue_subscription_lifecycle(self) -> None:
        # using module-level app
        # Create
        res_create = runner.invoke(
            app,
            [
                "revenue",
                "subscription",
                "create",
                "sub_user_999",
                "--tier",
                "scale",
                "--amount",
                "299",
                "--name",
                "Scale Client",
                "--json",
            ],
        )
        assert res_create.exit_code == 0
        data_create = json.loads(res_create.stdout)
        sub_id = data_create["id"]
        assert sub_id.startswith("sub_")

        # List
        res_list = runner.invoke(app, ["revenue", "subscription", "list", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.stdout)
        assert any(s["id"] == sub_id for s in data_list)

        # Cancel
        res_cancel = runner.invoke(
            app,
            ["revenue", "subscription", "cancel", sub_id, "--reason", "Test cancel", "--json"],
        )
        assert res_cancel.exit_code == 0
        data_cancel = json.loads(res_cancel.stdout)
        assert data_cancel["success"] is True


class TestRevenueMcpTools:
    """Parity tests for FastMCP and JSON-RPC MCP servers."""

    def test_scripts_mcp_revenue_tools(self) -> None:
        from scripts.mcp_server import (
            handle_revenue_forecast,
            handle_revenue_metrics,
            handle_revenue_record,
        )

        res_metrics = json.loads(handle_revenue_metrics({"period": "month"}))
        assert "mrr" in res_metrics
        assert "arr" in res_metrics

        res_record = json.loads(
            handle_revenue_record(
                {
                    "customer_id": "mcp_cust_1",
                    "amount": 49.0,
                    "tier": "starter",
                }
            )
        )
        assert res_record["customer_id"] == "mcp_cust_1"
        assert res_record["amount_usd"] == 49.0

        res_fc = json.loads(handle_revenue_forecast({"months": 3, "scenario": "base"}))
        assert res_fc["horizon_months"] == 3

    def test_core_mcp_revenue_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_metrics = json.loads(server._handle_revenue_metrics(period="quarter"))
        assert "mrr" in res_metrics

        res_record = json.loads(
            server._handle_revenue_record(
                customer_id="core_mcp_cust",
                amount=149.0,
                tier="growth",
            )
        )
        assert res_record["customer_id"] == "core_mcp_cust"

        res_fc = json.loads(server._handle_revenue_forecast(months=6, scenario="conservative"))
        assert res_fc["scenario"] == "conservative"


class TestRevenueBoundary:
    """Enforce strict standard-library-only core boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        source_path = Path("src/core/revenue_engine.py")
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
        assert not violations, f"Boundary violation: revenue_engine.py imports prohibited modules: {violations}"
