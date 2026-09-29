# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_consulting.py — Comprehensive test suite for AI Agent Consulting & Advisory Suite.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.consulting_engine import (
    ConsultingEngine,
    ConsultingPackage,
    EngagementRecord,
    OutreachTemplate,
    ProposalReport,
)

runner = CliRunner()


@pytest.fixture
def temp_consulting_engine(tmp_path: Path) -> Generator[ConsultingEngine, None, None]:
    """Provide an isolated ConsultingEngine instance with a temporary database and workspace."""
    db_file = tmp_path / "consulting_test.db"
    engine = ConsultingEngine(db_path=db_file, project_root=tmp_path)
    yield engine


class TestConsultingEngineCore:
    """Unit tests for ConsultingEngine core capabilities."""

    def test_service_catalog_usd_and_vnd(self, temp_consulting_engine: ConsultingEngine) -> None:
        pkgs = temp_consulting_engine.get_service_catalog()
        assert len(pkgs) == 4
        tiers = {p.tier for p in pkgs}
        assert tiers == {"audit", "custom_agent", "full_stack", "retainer"}

        for p in pkgs:
            assert isinstance(p, ConsultingPackage)
            assert p.price_usd > 0
            assert p.price_vnd == int(p.price_usd * 25400)
            assert len(p.deliverables) >= 3

    def test_proposal_generation(self, temp_consulting_engine: ConsultingEngine, tmp_path: Path) -> None:
        p_dir = tmp_path / "proposals"
        prop = temp_consulting_engine.generate_proposal(
            prospect_name="Fintech Frontier",
            service_tier="custom_agent",
            requirements="Build autonomous loan risk assessment subagent",
            industry="Fintech",
            budget=2500.0,
            save_report=True,
            output_dir=p_dir,
        )

        assert isinstance(prop, ProposalReport)
        assert prop.prospect_name == "Fintech Frontier"
        assert prop.service_tier == "custom_agent"
        assert prop.price_usd == 2500.0
        assert prop.proposal_file is not None
        assert Path(prop.proposal_file).exists()

        content = Path(prop.proposal_file).read_text(encoding="utf-8")
        assert "# AI Agent Consulting Proposal: Fintech Frontier" in content
        assert "loan risk assessment" in content
        assert "$2,500.00 USD" in content
        assert len(prop.milestones) == 3

    def test_engagement_lifecycle(self, temp_consulting_engine: ConsultingEngine) -> None:
        # Create
        eng = temp_consulting_engine.create_engagement(
            client_name="Nexus AI",
            service_tier="full_stack",
            price_usd=5000.0,
            notes="Full Agency OS multi-tenant setup",
        )
        assert isinstance(eng, EngagementRecord)
        assert eng.id.startswith("ENG-")
        assert eng.client_name == "Nexus AI"
        assert eng.status == "ACTIVE"

        # Get
        retrieved = temp_consulting_engine.get_engagement(eng.id)
        assert retrieved is not None
        assert retrieved.client_name == "Nexus AI"

        # List
        all_engs = temp_consulting_engine.list_engagements()
        assert len(all_engs) == 1

        # Update
        updated = temp_consulting_engine.update_engagement(
            engagement_id=eng.id,
            status="COMPLETED",
            notes="Final sign-off completed",
        )
        assert updated is not None
        assert updated.status == "COMPLETED"
        assert updated.notes == "Final sign-off completed"

    def test_outreach_generation(self, temp_consulting_engine: ConsultingEngine) -> None:
        out = temp_consulting_engine.generate_outreach(
            prospect_name="OmniRetail",
            service_tier="audit",
            role="VP of Engineering",
        )
        assert isinstance(out, OutreachTemplate)
        assert out.prospect_name == "OmniRetail"
        assert "Autonomous AI Agent Architecture" in out.subject
        assert "OmniRetail" in out.email_body
        assert "VP of Engineering" in out.linkedin_body
        assert "MekongMind" in out.zalo_body

    def test_get_status(self, temp_consulting_engine: ConsultingEngine) -> None:
        status = temp_consulting_engine.get_status()
        assert isinstance(status, dict)
        assert "total_engagements" in status
        assert "pipeline_value_usd" in status
        assert "realized_revenue_usd" in status
        assert "standard_offerings" in status


class TestConsultingCliCommands:
    """Integration tests for Typer CLI commands."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_consulting_overview_json(self) -> None:
        res = runner.invoke(self.app, ["consulting", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "pipeline_value_usd" in data
        assert "standard_offerings" in data

    def test_cli_consulting_overview_console(self) -> None:
        res = runner.invoke(self.app, ["consulting"])
        assert res.exit_code == 0
        assert "MEKONG ADVISORY & CONSULTING CONTROL PLANE" in res.output or "Consulting Operations Dashboard" in res.output

    def test_cli_consulting_pricing_json(self) -> None:
        res = runner.invoke(self.app, ["consulting", "pricing", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)
        assert len(data) == 4

    def test_cli_consulting_pricing_vnd(self) -> None:
        res = runner.invoke(self.app, ["consulting", "pricing", "--currency", "VND", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert all(p["price_vnd"] > 1000000 for p in data)

    def test_cli_consulting_proposal_json(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "consulting",
                "proposal",
                "Beta Logistics",
                "--service",
                "custom_agent",
                "--industry",
                "Logistics",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["prospect_name"] == "Beta Logistics"
        assert "markdown_proposal" in data

    def test_cli_consulting_proposal_save(self, tmp_path: Path) -> None:
        p_dir = tmp_path / "custom_proposals"
        res = runner.invoke(
            self.app,
            [
                "consulting",
                "proposal",
                "Gamma Health",
                "--service",
                "audit",
                "--save",
                "--output-dir",
                str(p_dir),
            ],
        )
        assert res.exit_code == 0
        assert p_dir.exists()
        files = list(p_dir.glob("proposal_*.md"))
        assert len(files) == 1

    def test_cli_consulting_outreach_json(self) -> None:
        res = runner.invoke(
            self.app,
            ["consulting", "outreach", "Delta Corp", "--service", "full_stack", "--role", "Founder", "--json"],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "email_body" in data
        assert "linkedin_body" in data
        assert "zalo_body" in data

    def test_cli_consulting_engagement_lifecycle(self) -> None:
        # Create
        c_res = runner.invoke(
            self.app,
            [
                "consulting",
                "engagement",
                "create",
                "Epsilon Bank",
                "--service",
                "full_stack",
                "--price",
                "5000",
                "--notes",
                "Banking security agent",
                "--json",
            ],
        )
        assert c_res.exit_code == 0
        c_data = json.loads(c_res.output)
        eng_id = c_data["id"]
        assert eng_id.startswith("ENG-")

        # List
        l_res = runner.invoke(self.app, ["consulting", "engagement", "list", "--json"])
        assert l_res.exit_code == 0
        l_data = json.loads(l_res.output)
        assert any(e["id"] == eng_id for e in l_data)

        # Update
        u_res = runner.invoke(
            self.app,
            ["consulting", "engagement", "update", eng_id, "--status", "DELIVERED", "--notes", "Delivered on schedule", "--json"],
        )
        assert u_res.exit_code == 0
        u_data = json.loads(u_res.output)
        assert u_data["status"] == "DELIVERED"


class TestConsultingMcpTools:
    """Test parity for native MCP tools across FastMCP and fallback stdio engine."""

    def test_scripts_mcp_consulting_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        # Pricing
        p_out = mcp_scripts.handle_consulting_pricing({"currency": "USD"})
        pkgs = json.loads(p_out)
        assert isinstance(pkgs, list)
        assert len(pkgs) == 4

        # Proposal
        prop_out = mcp_scripts.handle_consulting_proposal({
            "prospect_name": "MCP Client",
            "service_tier": "audit",
            "requirements": "Verify boundary compliance",
        })
        prop = json.loads(prop_out)
        assert prop["prospect_name"] == "MCP Client"

        # Outreach
        out_out = mcp_scripts.handle_consulting_outreach({
            "prospect_name": "MCP Client",
            "service_tier": "custom_agent",
            "role": "CTO",
        })
        out = json.loads(out_out)
        assert "email_body" in out

    def test_core_mcp_consulting_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        p_out = server._handle_consulting_pricing(currency="USD")
        pkgs = json.loads(p_out)
        assert isinstance(pkgs, list)

        prop_out = server._handle_consulting_proposal(prospect_name="Core MCP Client", service_tier="retainer")
        prop = json.loads(prop_out)
        assert prop["prospect_name"] == "Core MCP Client"

        out_out = server._handle_consulting_outreach(prospect_name="Core MCP Client", service_tier="full_stack")
        out = json.loads(out_out)
        assert "subject" in out


class TestConsultingBoundary:
    """Ensure src/core/consulting_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "consulting_engine.py"
        assert engine_file.exists(), f"Missing {engine_file}"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "aiohttp", "openai", "anthropic", "google", "boto3", "psutil"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed module import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import module: {pkg}"
