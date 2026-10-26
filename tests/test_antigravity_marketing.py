# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_marketing.py — Autonomous Marketing, Content Engine & Growth Suite Test Battery.

Covers:
1. MarketingEngine core operations (campaign CRUD, metrics, channels, SQLite persistence)
2. Content Engine copy synthesis across channels (social, linkedin, zalo, blog)
3. SEO keyword gap analysis and on-page recommendations
4. Growth experimentation A/B framework & sample size models
5. Bootstrap 30-day marketing plan generation and markdown export
6. Typer CLI commands (dashboard, campaign, content, seo, growth, bootstrap, and --json output)
7. Dual-engine MCP tools (FastMCP & pure JSON-RPC handlers in scripts/ and src/core/)
8. Core boundary compliance (pure standard library, zero vendor SDKs)
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.core.marketing_engine import (
    MarketingEngine,
    SOP_REPEATABLE_CHANNEL_FIELDS,
)

runner = CliRunner()


@pytest.fixture
def temp_marketing_engine(tmp_path: Path) -> MarketingEngine:
    """Fixture providing an isolated MarketingEngine backed by temporary SQLite DB."""
    db_file = tmp_path / "marketing_test.db"
    return MarketingEngine(db_path=db_file)


class TestMarketingEngineCore:
    """Test suite for MarketingEngine business logic and SQLite persistence."""

    def test_create_and_get_campaign(self, temp_marketing_engine: MarketingEngine) -> None:
        camp = temp_marketing_engine.create_campaign(
            name="Developer Inbound Q4",
            channel="social",
            budget=2500.0,
            target_audience="Fullstack Engineers & Founders",
            status="active",
        )
        assert camp.id.startswith("camp_")
        assert camp.name == "Developer Inbound Q4"
        assert camp.channel == "social"
        assert camp.budget == 2500.0
        assert camp.status == "active"
        assert camp.target_audience == "Fullstack Engineers & Founders"
        assert camp.cpa == 0.0
        assert camp.conversion_rate == 0.0

        retrieved = temp_marketing_engine.get_campaign(camp.id)
        assert retrieved is not None
        assert retrieved.id == camp.id
        assert retrieved.name == camp.name
        assert retrieved.budget == 2500.0

    def test_get_nonexistent_campaign(self, temp_marketing_engine: MarketingEngine) -> None:
        assert temp_marketing_engine.get_campaign("camp_missing") is None

    def test_update_campaign(self, temp_marketing_engine: MarketingEngine) -> None:
        camp = temp_marketing_engine.create_campaign(
            name="Search Ads Beta",
            channel="search",
            budget=1000.0,
        )
        updated = temp_marketing_engine.update_campaign(
            campaign_id=camp.id,
            status="completed",
            budget=1200.0,
            impressions=24000,
            conversions=480,
        )
        assert updated is not None
        assert updated.status == "completed"
        assert updated.budget == 1200.0
        assert updated.impressions == 24000
        assert updated.conversions == 480
        # CPA = 1200 / 480 = 2.50
        assert updated.cpa == 2.50
        # Conversion rate = 480 / 24000 * 100 = 2.0%
        assert updated.conversion_rate == 2.0

        # Non-existent campaign update returns None
        assert temp_marketing_engine.update_campaign("camp_fake", status="paused") is None

    def test_list_campaigns_filtered(self, temp_marketing_engine: MarketingEngine) -> None:
        temp_marketing_engine.create_campaign("Camp 1", channel="social", budget=500.0, status="active")
        temp_marketing_engine.create_campaign("Camp 2", channel="search", budget=1500.0, status="active")
        temp_marketing_engine.create_campaign("Camp 3", channel="social", budget=3000.0, status="paused")

        all_camps = temp_marketing_engine.list_campaigns()
        assert len(all_camps) == 3
        # Should be ordered by budget DESC
        assert all_camps[0].budget == 3000.0

        social_camps = temp_marketing_engine.list_campaigns(channel="social")
        assert len(social_camps) == 2

        active_search = temp_marketing_engine.list_campaigns(status="active", channel="search")
        assert len(active_search) == 1
        assert active_search[0].name == "Camp 2"

    def test_marketing_metrics_calculation(self, temp_marketing_engine: MarketingEngine) -> None:
        c1 = temp_marketing_engine.create_campaign("Social", channel="social", budget=1000.0, status="active")
        c2 = temp_marketing_engine.create_campaign("Search", channel="search", budget=2000.0, status="active")
        temp_marketing_engine.update_campaign(c1.id, impressions=10000, conversions=100)
        temp_marketing_engine.update_campaign(c2.id, impressions=20000, conversions=300)

        metrics = temp_marketing_engine.get_marketing_metrics()
        assert metrics.total_campaigns == 2
        assert metrics.active_campaigns == 2
        assert metrics.total_budget == 3000.0
        assert metrics.total_impressions == 30000
        assert metrics.total_conversions == 400
        # Blended CPA = 3000 / 400 = 7.50
        assert metrics.blended_cpa == 7.50
        assert metrics.campaigns_by_channel["social"] == 1
        assert metrics.campaigns_by_channel["search"] == 1
        assert len(metrics.top_campaigns) == 2

        m_dict = metrics.to_dict()
        assert "total_budget" in m_dict
        assert "blended_cpa" in m_dict

    def test_content_engine_generation(self, temp_marketing_engine: MarketingEngine) -> None:
        # LinkedIn
        li = temp_marketing_engine.generate_content("Multi-Agent Workflows", channel="linkedin")
        assert li.channel == "linkedin"
        assert "Multi-Agent Workflows" in li.headline
        assert len(li.hashtags) >= 2
        assert "reach out" in li.call_to_action.lower() or "benchmark" in li.call_to_action.lower()

        # Zalo
        zalo = temp_marketing_engine.generate_content("Kế Toán Tự Động", channel="zalo")
        assert zalo.channel == "zalo"
        assert "Kế Toán Tự Động" in zalo.headline
        assert "TT78" in zalo.body
        assert "Zalo OA" in zalo.call_to_action

        # Blog
        blog = temp_marketing_engine.generate_content("Deterministic Harness Engineering", channel="blog")
        assert blog.channel == "blog"
        assert "# Mastering" in blog.body
        assert len(blog.hashtags) >= 2

        # General Social
        social = temp_marketing_engine.generate_content("Mekong CLI", channel="social")
        assert social.channel == "social"
        assert "⚡ 100%" in social.body

    def test_seo_audit_generation(self, temp_marketing_engine: MarketingEngine) -> None:
        seo = temp_marketing_engine.generate_seo_audit(keyword="ai agent harness", domain="testmekong.io")
        assert seo.keyword == "ai agent harness"
        assert seo.domain == "testmekong.io"
        assert "testmekong.io" in seo.recommended_title
        assert len(seo.heading_structure) >= 4
        assert len(seo.content_gap_topics) >= 3
        assert len(seo.backlink_opportunities) >= 3

    def test_growth_experiment_generation(self, temp_marketing_engine: MarketingEngine) -> None:
        exp = temp_marketing_engine.create_growth_experiment(
            hypothesis="Terminal recording video improves conversion rate",
            target_metric="Activation Rate",
            target_lift="+20%",
        )
        assert exp.id.startswith("exp_")
        assert exp.hypothesis == "Terminal recording video improves conversion rate"
        assert exp.target_metric == "Activation Rate"
        assert exp.target_lift == "+20%"
        assert exp.sample_size_per_variant == 1200
        assert exp.duration_days == 14
        assert "Variant" in exp.variant_b

    def test_bootstrap_plan_generation(self, temp_marketing_engine: MarketingEngine) -> None:
        plan = temp_marketing_engine.bootstrap_plan(
            business_name="TestStartup VN",
            industry="Fintech AI",
            export=False,
        )
        assert plan.business_name == "TestStartup VN"
        assert plan.industry == "Fintech AI"
        assert len(plan.channel_mix) >= 4
        assert len(plan.content_calendar_30d) >= 5
        assert "Month 1 Target Leads" in plan.key_kpis

    def test_outreach_and_cmo_swarm_14_fields(self, temp_marketing_engine: MarketingEngine, tmp_path: Path) -> None:
        outreach = temp_marketing_engine.run_outreach(
            target="Vietnam One-Person Companies",
            channel="zalo",
            prospect_count=10,
            qualification_threshold=70,
        )
        assert outreach.prospects_found == 10
        assert outreach.qualified_leads_count > 0
        assert len(outreach.email_sequence) == 3
        assert "sales-revenue" in outreach.sales_handoff["handoff_to"]

        swarm = temp_marketing_engine.run_cmo_swarm(
            brief="Tăng trưởng One-Person Company 2027",
            channel="zalo",
            budget=2500.0,
            export_sop_artifact=True,
            output_dir=tmp_path,
        )
        assert swarm["ok"] is True
        sop_data = swarm["sop_data"]
        for field_name in SOP_REPEATABLE_CHANNEL_FIELDS:
            assert field_name in sop_data, f"Missing SOP required field: {field_name}"

        artifact_path = Path(swarm["sop_artifact_exported"])
        assert artifact_path.exists()
        saved_json = json.loads(artifact_path.read_text(encoding="utf-8"))
        for field_name in SOP_REPEATABLE_CHANNEL_FIELDS:
            assert field_name in saved_json

    def test_commercial_marketing_and_growth_no_stubs(self) -> None:
        from src.commercial.marketing import MarketingEngine as CommercialMarketing
        from src.commercial.growth import GrowthEngine as CommercialGrowth

        cm = CommercialMarketing()
        camp_res = cm.plan_campaign(brief="Sovereign OPC Launch", channel="linkedin", budget=1800.0)
        assert camp_res["stub"] is False
        assert "campaign_asset" in camp_res
        assert "seo_blueprint" in camp_res

        out_res = cm.outreach(target="Tech Founders VN", channel="zalo")
        assert out_res["stub"] is False
        assert out_res["prospects_found"] > 0
        assert out_res["qualified_leads_count"] > 0

        cg = CommercialGrowth()
        exp_res = cg.experiment(channel="zalo")
        assert exp_res["stub"] is False
        assert "experiment_design" in exp_res

        launch_res = cg.launch(product="MEKONG OPC 2027", channel="zalo")
        assert launch_res["stub"] is False
        assert launch_res["readiness_score"] == 100.0
        for field_name in SOP_REPEATABLE_CHANNEL_FIELDS:
            assert field_name in launch_res["sop_data"]

        opt_res = cg.optimize_channel(channel="social")
        assert opt_res["stub"] is False
        assert opt_res["current_cpa"] is not None


class TestMarketingCliCommands:
    """Test suite for Typer CLI commands under `mekong marketing`."""

    def test_cli_marketing_overview_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["marketing", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_campaigns" in data
        assert "total_budget" in data
        assert "blended_cpa" in data

    def test_cli_marketing_overview_console(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        result = runner.invoke(app, ["marketing"])
        assert result.exit_code == 0
        assert "MARKETING & GROWTH" in result.output or "Campaign" in result.output

    def test_cli_campaign_create_and_list_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        create_res = runner.invoke(
            app,
            [
                "marketing",
                "campaign",
                "create",
                "Brand Launch Sprint",
                "--channel",
                "social",
                "--budget",
                "2200",
                "--audience",
                "CTOs and Heads of Product",
                "--json",
            ],
        )
        assert create_res.exit_code == 0
        camp = json.loads(create_res.output)
        assert camp["name"] == "Brand Launch Sprint"
        assert camp["budget"] == 2200.0
        camp_id = camp["id"]

        list_res = runner.invoke(app, ["marketing", "campaign", "list", "--channel", "social", "--json"])
        assert list_res.exit_code == 0
        camps = json.loads(list_res.output)
        assert any(c["id"] == camp_id for c in camps)

    def test_cli_campaign_update_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        create_res = runner.invoke(
            app,
            ["marketing", "campaign", "create", "Search PPC", "--channel", "search", "--budget", "1500", "--json"],
        )
        camp_id = json.loads(create_res.output)["id"]

        update_res = runner.invoke(
            app,
            [
                "marketing",
                "campaign",
                "update",
                camp_id,
                "--status",
                "completed",
                "--impressions",
                "50000",
                "--conversions",
                "625",
                "--json",
            ],
        )
        assert update_res.exit_code == 0
        updated = json.loads(update_res.output)
        assert updated["status"] == "completed"
        assert updated["conversions"] == 625

    def test_cli_content_and_seo_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        content_res = runner.invoke(
            app,
            ["marketing", "content", "Deterministic Agent Swarms", "--channel", "linkedin", "--json"],
        )
        assert content_res.exit_code == 0
        item = json.loads(content_res.output)
        assert item["channel"] == "linkedin"
        assert "Deterministic Agent Swarms" in item["headline"]

        seo_res = runner.invoke(
            app,
            ["marketing", "seo", "agent harness architecture", "--domain", "mekongmind.vn", "--json"],
        )
        assert seo_res.exit_code == 0
        audit = json.loads(seo_res.output)
        assert audit["domain"] == "mekongmind.vn"
        assert len(audit["heading_structure"]) >= 3

    def test_cli_growth_and_bootstrap_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        growth_res = runner.invoke(
            app,
            [
                "marketing",
                "growth",
                "Showing Rich CLI tables increases feature engagement",
                "--metric",
                "Feature Usage",
                "--lift",
                "+15%",
                "--json",
            ],
        )
        assert growth_res.exit_code == 0
        exp = json.loads(growth_res.output)
        assert exp["target_metric"] == "Feature Usage"

        boot_res = runner.invoke(
            app,
            ["marketing", "bootstrap", "Mekong Cloud", "--industry", "Developer Tools", "--no-export", "--json"],
        )
        assert boot_res.exit_code == 0
        plan = json.loads(boot_res.output)
        assert plan["business_name"] == "Mekong Cloud"
        assert len(plan["channel_mix"]) >= 4

    def test_cli_outreach_and_cmo_run_json(self) -> None:
        from src.cli.app_setup import build_app

        app = build_app()
        out_res = runner.invoke(
            app,
            ["marketing", "outreach", "Vietnam Tech Founders", "--channel", "zalo", "--count", "8", "--json"],
        )
        assert out_res.exit_code == 0
        out_data = json.loads(out_res.output)
        assert out_data["prospects_found"] == 8
        assert out_data["qualified_leads_count"] > 0

        cmo_res = runner.invoke(
            app,
            [
                "marketing",
                "cmo-run",
                "Sovereign OPC Launch 2027",
                "--channel",
                "zalo",
                "--budget",
                "2500",
                "--no-export-sop",
                "--json",
            ],
        )
        assert cmo_res.exit_code == 0
        cmo_data = json.loads(cmo_res.output)
        assert cmo_data["ok"] is True
        for field_name in SOP_REPEATABLE_CHANNEL_FIELDS:
            assert field_name in cmo_data["sop_data"]

        for topic in ("campaign", "outreach", "launch", "growth"):
            csuite_res = runner.invoke(app, ["cmo", topic])
            assert csuite_res.exit_code == 0
            csuite_data = json.loads(csuite_res.output)
            assert csuite_data["stub"] is False
            assert csuite_data["meta"]["command"] == "cmo"


class TestMarketingMcpTools:
    """Test suite for MCP marketing tools across scripts/ and src/core/."""

    def test_scripts_mcp_marketing_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        assert "mekong_marketing_metrics" in mcp_scripts.CORE_HANDLERS
        assert "mekong_marketing_campaign_create" in mcp_scripts.CORE_HANDLERS
        assert "mekong_marketing_content_generate" in mcp_scripts.CORE_HANDLERS

        # Test campaign create
        create_out = mcp_scripts.handle_marketing_campaign_create({
            "name": "MCP Campaign",
            "channel": "social",
            "budget": 1800.0,
            "target_audience": "Engineers",
        })
        camp = json.loads(create_out)
        assert camp["name"] == "MCP Campaign"
        assert camp["channel"] == "social"

        # Test metrics
        met_out = mcp_scripts.handle_marketing_metrics({})
        metrics = json.loads(met_out)
        assert "total_campaigns" in metrics
        assert "total_budget" in metrics

        # Test content generate
        cnt_out = mcp_scripts.handle_marketing_content_generate({
            "topic": "AI OS Architecture",
            "channel": "linkedin",
            "content_type": "post",
        })
        cnt = json.loads(cnt_out)
        assert cnt["channel"] == "linkedin"
        assert "AI OS Architecture" in cnt["headline"]

    def test_core_mcp_marketing_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        met_out = server._handle_marketing_metrics()
        metrics = json.loads(met_out)
        assert "total_campaigns" in metrics

        create_out = server._handle_marketing_campaign_create(
            name="Core Camp", channel="search", budget=2400.0
        )
        camp = json.loads(create_out)
        assert camp["name"] == "Core Camp"

        cnt_out = server._handle_marketing_content_generate(
            topic="Core Architecture", channel="zalo"
        )
        cnt = json.loads(cnt_out)
        assert cnt["channel"] == "zalo"
        assert "TT78" in cnt["body"]


class TestMarketingBoundary:
    """Ensure src/core/marketing_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "marketing_engine.py"
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
