# Mekong CLI — Pure Standard-Library Governance Tests
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_governance.py — Comprehensive tests for Autonomous Constitutional Governance & Voting Engine.
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
from src.core.governance_engine import GovernanceEngine, get_governance_engine

runner = CliRunner()
app = build_app()


@pytest.fixture
def clean_engine(tmp_path: Path) -> GovernanceEngine:
    """Fixture providing an isolated GovernanceEngine instance with a temporary database."""
    db_file = tmp_path / "governance_test.db"
    return GovernanceEngine(db_path=db_file)


class TestGovernanceEngine:
    """Unit tests for the GovernanceEngine core implementation."""

    def test_engine_init_and_default_proposals(self, clean_engine: GovernanceEngine) -> None:
        status = clean_engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_proposals"] >= 3
        assert status["passed_or_enacted"] >= 2
        assert "soft" in status["tier_specifications"]
        assert "operational" in status["tier_specifications"]
        assert "foundational" in status["tier_specifications"]

        p1 = clean_engine.get_proposal("prop_zenos_001")
        assert p1 is not None
        assert p1["tier"] == "foundational"
        assert p1["status"] == "enacted"
        assert p1["threshold_percent"] == 75.0

    def test_create_proposal(self, clean_engine: GovernanceEngine) -> None:
        p = clean_engine.create_proposal(
            title="Expand Subagent Memory Quotas",
            description="Raise per-agent context memory quota to 64k tokens.",
            text="Context quota maximum is set to 64,000 tokens for specialized domain subagents.",
            proposer="engineer-lead",
            tier="operational",
            co_sponsors=["architect", "ops-steward"],
        )
        assert p["title"] == "Expand Subagent Memory Quotas"
        assert p["tier"] == "operational"
        assert p["threshold_percent"] == 66.7
        assert p["quorum_min"] == 5
        assert p["status"] == "voting"
        assert "architect" in p["co_sponsors"]

        retrieved = clean_engine.get_proposal(p["id"])
        assert retrieved is not None
        assert retrieved["id"] == p["id"]

    def test_list_proposals(self, clean_engine: GovernanceEngine) -> None:
        all_props = clean_engine.list_proposals()
        assert len(all_props) >= 3

        voting_props = clean_engine.list_proposals(status="voting")
        assert any(p["status"] == "voting" for p in voting_props)

        foundational = clean_engine.list_proposals(tier="foundational")
        assert all(p["tier"] == "foundational" for p in foundational)

    def test_cast_vote_and_hash(self, clean_engine: GovernanceEngine) -> None:
        p = clean_engine.create_proposal(
            title="Test Voting Proposal",
            description="Testing ballot hashing",
            text="Test text",
            tier="soft",
        )
        vote_res = clean_engine.cast_vote(
            proposal_id=p["id"],
            voter="alice",
            choice="yes",
            weight=1.5,
        )
        assert vote_res["success"] is True

        prop = clean_engine.get_proposal(p["id"])
        assert prop is not None
        assert prop["votes_count"] == 1
        ballot = prop["votes"][0]
        assert ballot["voter"] == "alice"
        assert ballot["choice"] == "yes"
        assert ballot["weight"] == 1.5
        assert len(ballot["ballot_hash"]) == 64  # SHA-256 hex string

    def test_tally_votes_quorum_and_supermajority(self, clean_engine: GovernanceEngine) -> None:
        # Create operational proposal (quorum: 5, threshold: 66.7%)
        p = clean_engine.create_proposal(
            title="Operational Quorum Test",
            description="Operational testing",
            text="Text",
            tier="operational",
        )

        # Cast 4 votes (below quorum of 5)
        clean_engine.cast_vote(p["id"], voter="v1", choice="yes", weight=1.0)
        clean_engine.cast_vote(p["id"], voter="v2", choice="yes", weight=1.0)
        clean_engine.cast_vote(p["id"], voter="v3", choice="yes", weight=1.0)
        tally1 = clean_engine.cast_vote(p["id"], voter="v4", choice="yes", weight=1.0)
        assert tally1["results"]["quorum_reached"] is False
        assert tally1["results"]["passed"] is False

        # Cast 5th vote (yes) -> quorum reached and passes (5/5 = 100% >= 66.7%)
        tally2 = clean_engine.cast_vote(p["id"], voter="v5", choice="yes", weight=1.0)
        assert tally2["results"]["quorum_reached"] is True
        assert tally2["results"]["passed"] is True
        assert tally2["status"] == "passed"

    def test_vote_on_closed_proposal(self, clean_engine: GovernanceEngine) -> None:
        # prop_zenos_001 is enacted
        res = clean_engine.cast_vote("prop_zenos_001", voter="bob", choice="yes")
        assert res["success"] is False
        assert "voting is closed" in res["error"]


class TestGovernanceCli:
    """CLI tests for `mekong governance` commands."""

    def test_governance_overview_cli(self) -> None:
        result = runner.invoke(app, ["governance"])
        assert result.exit_code == 0
        assert "ZenOS Commons Constitutional Governance" in result.output

    def test_governance_overview_json_cli(self) -> None:
        result = runner.invoke(app, ["governance", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "tier_specs" in data
        assert "total_proposals" in data

    def test_governance_status_cli(self) -> None:
        result = runner.invoke(app, ["governance", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "tier_specifications" in data

    def test_governance_propose_cli(self) -> None:
        result = runner.invoke(
            app,
            [
                "governance",
                "propose",
                "CLI Governance Proposal",
                "CLI Test Description",
                "CLI Test Text",
                "--from",
                "founder",
                "--tier",
                "operational",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "CLI Governance Proposal"
        assert data["tier"] == "operational"

    def test_governance_list_cli(self) -> None:
        result = runner.invoke(app, ["governance", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestGovernanceMcpParity:
    """Verifies FastMCP and JSON-RPC 2.0 dual server parity for governance tools."""

    def test_scripts_mcp_governance_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_governance_list,
            handle_governance_propose,
            handle_governance_tally,
            handle_governance_vote,
        )

        # 1. Propose
        prop_res = handle_governance_propose({
            "title": "MCP Governance Proposal",
            "description": "Submitted via MCP tool",
            "text": "MCP amendment content",
            "tier": "soft",
        })
        prop_data = json.loads(prop_res)
        assert prop_data["title"] == "MCP Governance Proposal"
        pid = prop_data["id"]

        # 2. Vote
        vote_res = handle_governance_vote({
            "proposal_id": pid,
            "voter": "mcp-agent",
            "choice": "yes",
            "weight": 2.0,
        })
        vote_data = json.loads(vote_res)
        assert vote_data["success"] is True

        # 3. Tally
        tally_res = handle_governance_tally({"proposal_id": pid})
        tally_data = json.loads(tally_res)
        assert tally_data["success"] is True
        assert tally_data["results"]["yes_weight"] >= 2.0

        # 4. List
        list_res = handle_governance_list({"status": "all", "limit": 10})
        list_data = json.loads(list_res)
        assert isinstance(list_data, list)
        assert any(p["id"] == pid for p in list_data)

    def test_core_mcp_server_governance_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        # 1. Propose
        res = server._handle_governance_propose(
            title="Core Server Governance Proposal",
            description="Submitted via core server",
            text="Core amendment",
            tier="soft",
        )
        data = json.loads(res)
        assert data["title"] == "Core Server Governance Proposal"
        pid = data["id"]

        # 2. Vote
        vote_res = server._handle_governance_vote(
            proposal_id=pid,
            choice="yes",
            voter="core-voter",
        )
        vote_data = json.loads(vote_res)
        assert vote_data["success"] is True

        # 3. Tally
        tally_res = server._handle_governance_tally(proposal_id=pid)
        tally_data = json.loads(tally_res)
        assert tally_data["success"] is True

        # 4. List
        list_res = server._handle_governance_list(limit=20)
        list_data = json.loads(list_res)
        assert any(p["id"] == pid for p in list_data)

        # 5. Aliases
        assert server._handle_mekong_governance_propose == server._handle_governance_propose
        assert server._handle_mekong_governance_vote == server._handle_governance_vote
        assert server._handle_mekong_governance_tally == server._handle_governance_tally
        assert server._handle_mekong_governance_list == server._handle_governance_list


class TestGovernanceCoreBoundary:
    """Strict AST standard-library boundary verification for `src/core/governance_engine.py`."""

    def test_no_prohibited_imports_in_governance_engine(self) -> None:
        engine_file = Path("src/core/governance_engine.py")
        assert engine_file.exists(), "src/core/governance_engine.py must exist"

        tree = ast.parse(engine_file.read_text(encoding="utf-8"))

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
                            f"Prohibited import '{alias.name}' detected in src/core/governance_engine.py"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for prefix in prohibited_prefixes:
                        assert not node.module.startswith(prefix), (
                            f"Prohibited from-import '{node.module}' detected in src/core/governance_engine.py"
                        )
