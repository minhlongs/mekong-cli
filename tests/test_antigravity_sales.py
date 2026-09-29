# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_sales.py — Autonomous Sales & Revenue Dealflow Engine Test Battery.

Covers:
1. SalesEngine core operations (deal CRUD, pipeline metrics, stage weighting, SQLite persistence)
2. Outreach generation (email, linkedin, zalo channels)
3. Deal preparation & objection handling playbook
4. Deal close reports & customer success onboarding receipt
5. Typer CLI commands (dashboard, add, list, update, outreach, prep, close, and --json output)
6. Dual-engine MCP tools (FastMCP & pure JSON-RPC handlers in scripts/ and src/core/)
7. Core boundary compliance (pure standard library, zero vendor SDKs)
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.core.sales_engine import (
    DealStage,
    SalesEngine,
    get_sales_engine,
)

runner = CliRunner()


@pytest.fixture
def temp_sales_engine(tmp_path: Path) -> SalesEngine:
    """Fixture providing an isolated SalesEngine backed by temporary SQLite DB."""
    db_file = tmp_path / "sales_test.db"
    return SalesEngine(db_path=db_file)


class TestSalesEngineCore:
    """Test suite for SalesEngine business logic and SQLite persistence."""

    def test_add_and_get_deal(self, temp_sales_engine: SalesEngine) -> None:
        deal = temp_sales_engine.add_deal(
            name="Enterprise Pilot",
            company="Acme Corp",
            value=25000.0,
            stage="qualified",
            contact_email="tech@acme.com",
            notes="Interested in agentic CI/CD",
        )
        assert deal.id.startswith("deal_")
        assert deal.name == "Enterprise Pilot"
        assert deal.company == "Acme Corp"
        assert deal.value == 25000.0
        assert deal.stage == "qualified"
        assert deal.contact_email == "tech@acme.com"
        assert deal.notes == "Interested in agentic CI/CD"
        assert deal.weighted_value == 25000.0 * 0.25

        retrieved = temp_sales_engine.get_deal(deal.id)
        assert retrieved is not None
        assert retrieved.id == deal.id
        assert retrieved.name == deal.name
        assert retrieved.company == deal.company
        assert retrieved.value == 25000.0

    def test_get_nonexistent_deal(self, temp_sales_engine: SalesEngine) -> None:
        assert temp_sales_engine.get_deal("deal_nonexistent") is None

    def test_update_deal(self, temp_sales_engine: SalesEngine) -> None:
        deal = temp_sales_engine.add_deal(
            name="Initial Lead",
            company="Beta LLC",
            value=10000.0,
            stage="lead",
        )
        updated = temp_sales_engine.update_deal(
            deal.id,
            stage="negotiation",
            value=15000.0,
            notes="Expanded scope",
        )
        assert updated is not None
        assert updated.stage == "negotiation"
        assert updated.value == 15000.0
        assert updated.notes == "Expanded scope"
        assert updated.weighted_value == 15000.0 * 0.75

        # Test updating non-existent deal
        assert temp_sales_engine.update_deal("deal_missing", stage="won") is None

    def test_list_deals_filtered(self, temp_sales_engine: SalesEngine) -> None:
        temp_sales_engine.add_deal("Deal 1", "Co A", 10000, "lead")
        temp_sales_engine.add_deal("Deal 2", "Co B", 20000, "qualified")
        temp_sales_engine.add_deal("Deal 3", "Co C", 30000, "won")

        all_deals = temp_sales_engine.list_deals()
        assert len(all_deals) == 3
        # Should be sorted by value DESC
        assert all_deals[0].value == 30000.0

        won_deals = temp_sales_engine.list_deals(stage="won")
        assert len(won_deals) == 1
        assert won_deals[0].name == "Deal 3"

        empty_deals = temp_sales_engine.list_deals(stage="lost")
        assert len(empty_deals) == 0

    def test_pipeline_metrics_calculation(self, temp_sales_engine: SalesEngine) -> None:
        temp_sales_engine.add_deal("Lead 1", "Alpha", 10000.0, "lead")          # 0.10 * 10000 = 1000
        temp_sales_engine.add_deal("Prop 1", "Beta", 20000.0, "proposal")        # 0.50 * 20000 = 10000
        temp_sales_engine.add_deal("Won 1", "Gamma", 30000.0, "won")             # 1.00 * 30000 = 30000
        temp_sales_engine.add_deal("Lost 1", "Delta", 15000.0, "lost")           # 0.00 * 15000 = 0

        metrics = temp_sales_engine.get_pipeline_metrics()
        assert metrics.total_deals == 4
        assert metrics.total_pipeline_value == 75000.0
        assert metrics.weighted_pipeline_value == 41000.0
        assert metrics.won_value == 30000.0
        # Closed: 1 won, 1 lost -> 50% win rate
        assert metrics.win_rate == 50.0
        assert metrics.deals_by_stage["lead"] == 1
        assert metrics.deals_by_stage["won"] == 1
        assert len(metrics.top_deals) == 4

        d_dict = metrics.to_dict()
        assert "total_pipeline_value" in d_dict
        assert "top_deals" in d_dict

    def test_outreach_generation(self, temp_sales_engine: SalesEngine) -> None:
        # Email channel
        email_copy = temp_sales_engine.generate_outreach("Fintech VN", persona="CTO", channel="email")
        assert email_copy.company == "Fintech VN"
        assert email_copy.channel == "email"
        assert "Fintech VN" in email_copy.subject
        assert len(email_copy.follow_up_sequence) == 4

        # LinkedIn channel
        li_copy = temp_sales_engine.generate_outreach("Ecom Global", persona="VP Engineering", channel="linkedin")
        assert li_copy.channel == "linkedin"
        assert "Ecom Global" in li_copy.subject
        assert "velocity" in li_copy.body

        # Zalo channel
        zalo_copy = temp_sales_engine.generate_outreach("Cong Ty Cong Nghe", persona="Anh Nam", channel="zalo")
        assert zalo_copy.channel == "zalo"
        assert "Mekong CLI" in zalo_copy.body
        assert "Cong Ty Cong Nghe" in zalo_copy.body

    def test_deal_prep_generation(self, temp_sales_engine: SalesEngine) -> None:
        prep = temp_sales_engine.generate_deal_prep(
            company="Retail Corp",
            value=20000.0,
            pain_points="Deployment failures, Manual audits",
        )
        assert prep.company == "Retail Corp"
        assert prep.deal_value == 20000.0
        assert len(prep.pain_points) == 2
        assert "Deployment failures" in prep.pain_points
        assert prep.roi_multiplier > 1.0
        assert len(prep.objections_playbook) >= 3
        assert "objection" in prep.objections_playbook[0]
        assert "rebuttal" in prep.objections_playbook[0]

    def test_deal_close_report(self, temp_sales_engine: SalesEngine) -> None:
        deal = temp_sales_engine.add_deal("Gov Contract", "Gov Agency", 50000.0, "negotiation")
        report = temp_sales_engine.generate_close_report(deal.id)
        assert report is not None
        assert report.deal_id == deal.id
        assert report.final_value == 50000.0
        assert len(report.onboarding_checklist) == 4
        assert report.revenue_attribution["contract_value"] == 50000.0
        assert report.revenue_attribution["mrr_contribution"] == round(50000.0 / 12.0, 2)

        # Check that deal stage in DB transitioned to 'won'
        refreshed = temp_sales_engine.get_deal(deal.id)
        assert refreshed is not None
        assert refreshed.stage == "won"

        # Non-existent deal close returns None
        assert temp_sales_engine.generate_close_report("deal_fake") is None


class TestSalesCliCommands:
    """Test suite for Typer CLI commands under `mekong sales`."""

    def test_cli_sales_overview_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["sales", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_deals" in data
        assert "total_pipeline_value" in data
        assert "win_rate" in data

    def test_cli_sales_overview_console(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["sales"])
        assert result.exit_code == 0
        assert "SALES & REVENUE" in result.output or "Pipeline" in result.output

    def test_cli_sales_add_and_list_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        add_result = runner.invoke(
            app,
            [
                "sales",
                "add",
                "Enterprise Automation Tier",
                "--company",
                "Test Corp VN",
                "--value",
                "18500",
                "--stage",
                "qualified",
                "--email",
                "contact@testcorp.vn",
                "--json",
            ],
        )
        assert add_result.exit_code == 0
        deal_data = json.loads(add_result.output)
        assert deal_data["company"] == "Test Corp VN"
        assert deal_data["value"] == 18500.0
        deal_id = deal_data["id"]

        list_result = runner.invoke(app, ["sales", "list", "--stage", "qualified", "--json"])
        assert list_result.exit_code == 0
        deals_list = json.loads(list_result.output)
        assert any(d["id"] == deal_id for d in deals_list)

    def test_cli_sales_update_and_close_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        add_res = runner.invoke(
            app,
            ["sales", "add", "Midmarket Deal", "--company", "Midmarket Co", "--value", "8000", "--json"],
        )
        deal_id = json.loads(add_res.output)["id"]

        update_res = runner.invoke(
            app,
            ["sales", "update", deal_id, "--stage", "proposal", "--value", "9500", "--json"],
        )
        assert update_res.exit_code == 0
        updated = json.loads(update_res.output)
        assert updated["stage"] == "proposal"
        assert updated["value"] == 9500.0

        close_res = runner.invoke(app, ["sales", "close", deal_id, "--json"])
        assert close_res.exit_code == 0
        closed = json.loads(close_res.output)
        assert closed["deal_id"] == deal_id
        assert closed["final_value"] == 9500.0

    def test_cli_sales_outreach_and_prep_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        outreach_res = runner.invoke(
            app,
            ["sales", "outreach", "TechAsia", "--persona", "CTO", "--channel", "linkedin", "--json"],
        )
        assert outreach_res.exit_code == 0
        outreach_data = json.loads(outreach_res.output)
        assert outreach_data["company"] == "TechAsia"
        assert outreach_data["channel"] == "linkedin"

        prep_res = runner.invoke(
            app,
            ["sales", "prep", "TechAsia", "--value", "25000", "--json"],
        )
        assert prep_res.exit_code == 0
        prep_data = json.loads(prep_res.output)
        assert prep_data["company"] == "TechAsia"
        assert prep_data["deal_value"] == 25000.0


class TestSalesMcpTools:
    """Test suite for MCP sales tools across scripts/ and src/core/."""

    def test_scripts_mcp_sales_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        assert "mekong_sales_pipeline" in mcp_scripts.CORE_HANDLERS
        assert "mekong_sales_deal_add" in mcp_scripts.CORE_HANDLERS
        assert "mekong_sales_outreach" in mcp_scripts.CORE_HANDLERS

        # Test deal add
        add_out = mcp_scripts.handle_sales_deal_add({
            "name": "MCP Deal",
            "company": "MCP Inc",
            "value": 12000.0,
            "stage": "qualified",
        })
        deal = json.loads(add_out)
        assert deal["name"] == "MCP Deal"
        assert deal["company"] == "MCP Inc"

        # Test pipeline query
        pipe_out = mcp_scripts.handle_sales_pipeline({})
        pipe = json.loads(pipe_out)
        assert "total_deals" in pipe
        assert "total_pipeline_value" in pipe

        # Test outreach query
        reach_out = mcp_scripts.handle_sales_outreach({
            "company": "MCP Partner",
            "persona": "Head of Engineering",
            "channel": "email",
        })
        reach = json.loads(reach_out)
        assert reach["company"] == "MCP Partner"

    def test_core_mcp_sales_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        pipe_out = server._handle_sales_pipeline()
        pipe = json.loads(pipe_out)
        assert "total_deals" in pipe

        add_out = server._handle_sales_deal_add(name="Core Deal", company="Core Co", value=30000.0)
        deal = json.loads(add_out)
        assert deal["name"] == "Core Deal"

        reach_out = server._handle_sales_outreach(company="Core Co", persona="CTO", channel="zalo")
        reach = json.loads(reach_out)
        assert reach["company"] == "Core Co"
        assert reach["channel"] == "zalo"


class TestSalesBoundary:
    """Ensure src/core/sales_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "sales_engine.py"
        assert engine_file.exists(), f"Missing {engine_file}"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "aiohttp", "openai", "anthropic", "google", "boto3"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed module import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import module: {pkg}"
