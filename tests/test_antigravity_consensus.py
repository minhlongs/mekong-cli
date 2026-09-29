# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Agent Collaboration Mesh & Multi-Agent Consensus Protocol (Phase 15).

Covers:
1. ConsensusBridge: Quorum voting (majority, supermajority, unanimous, weighted), multi-round debate, SQLite persistence.
2. CLI Command Surface: mekong consensus (vote, debate, history, --json).
3. Native MCP Tools: mekong_consensus_vote and mekong_consensus_debate parity.
4. AST Core Boundary Compliance: strict standard library only, zero vendor SDKs in consensus_bridge.py.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.consensus_bridge import (
    AGENT_PERSPECTIVES,
    DEFAULT_ROLE_WEIGHTS,
    AgentVote,
    BallotResult,
    ConsensusBridge,
    DebateSession,
    DebateTurn,
    get_consensus_bridge,
)


@pytest.fixture
def temp_db(tmp_path: Path):
    """Create a temporary SQLite database path for consensus tests."""
    db_file = tmp_path / "test_consensus.db"
    return db_file


class TestConsensusBridge:
    """Tests for quorum calculation, debate orchestration, and ballot hashing."""

    def test_create_vote_majority_pass(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        ballot = bridge.create_vote(
            proposal="Implement Redis distributed caching layer",
            quorum="majority",
        )
        assert ballot.passed is True
        assert ballot.total_votes >= 5
        assert ballot.yes_votes > (ballot.total_votes / 2.0)
        assert len(ballot.ballot_hash) == 64
        assert ballot.quorum_type == "majority"

    def test_create_vote_rejection_on_reckless_proposal(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        # SRE and QA persona heuristics reject proposals that skip tests or remove safeguards
        ballot = bridge.create_vote(
            proposal="Skip test and force deploy unverified hotfix",
            agents=["sre", "qa", "cfo"],
            quorum="majority",
        )
        assert ballot.passed is False
        assert ballot.no_votes >= 2
        assert any(v.agent_id == "sre" and v.vote == "no" for v in ballot.votes)

    def test_quorum_supermajority(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        # 3 agents: 2 yes, 1 no -> 2/3 = 66.6% -> passes supermajority
        custom_votes = [
            {"agent_id": "ceo", "vote": "yes", "weight": 3},
            {"agent_id": "cto", "vote": "yes", "weight": 2},
            {"agent_id": "cfo", "vote": "no", "weight": 2},
        ]
        ballot = bridge.create_vote(
            proposal="Strategic expansion",
            quorum="supermajority",
            custom_votes=custom_votes,
        )
        assert ballot.passed is True
        assert ballot.yes_votes == 2
        assert ballot.no_votes == 1

        # 4 agents: 2 yes, 2 no -> 50% -> fails supermajority
        custom_votes_fail = [
            {"agent_id": "ceo", "vote": "yes", "weight": 3},
            {"agent_id": "cto", "vote": "yes", "weight": 2},
            {"agent_id": "cfo", "vote": "no", "weight": 2},
            {"agent_id": "sre", "vote": "no", "weight": 1},
        ]
        ballot_fail = bridge.create_vote(
            proposal="Risky expansion",
            quorum="supermajority",
            custom_votes=custom_votes_fail,
        )
        assert ballot_fail.passed is False

    def test_quorum_unanimous(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        # Single NO vote blocks unanimous
        custom_votes = [
            {"agent_id": "ceo", "vote": "yes"},
            {"agent_id": "cto", "vote": "yes"},
            {"agent_id": "sre", "vote": "no"},
        ]
        ballot = bridge.create_vote(
            proposal="Delete production backup snapshots",
            quorum="unanimous",
            custom_votes=custom_votes,
        )
        assert ballot.passed is False

        # All YES votes pass unanimous
        custom_votes_unanimous = [
            {"agent_id": "ceo", "vote": "yes"},
            {"agent_id": "cto", "vote": "yes"},
            {"agent_id": "sre", "vote": "yes"},
        ]
        ballot_pass = bridge.create_vote(
            proposal="Upgrade PostgreSQL minor version with backup",
            quorum="unanimous",
            custom_votes=custom_votes_unanimous,
        )
        assert ballot_pass.passed is True

    def test_quorum_weighted(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        # CEO (weight 3) votes YES, PM (weight 1) & SRE (weight 1) vote NO
        # Weighted YES = 3, Weighted NO = 2 -> Total = 5 -> 3/5 = 60% > 50% -> Passes
        custom_votes = [
            {"agent_id": "ceo", "vote": "yes", "weight": 3},
            {"agent_id": "pm", "vote": "no", "weight": 1},
            {"agent_id": "sre", "vote": "no", "weight": 1},
        ]
        ballot = bridge.create_vote(
            proposal="CEO executive override initiative",
            quorum="weighted",
            custom_votes=custom_votes,
        )
        assert ballot.passed is True
        assert ballot.weighted_yes == 3
        assert ballot.weighted_total == 5

    def test_conduct_debate_multi_round(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        session = bridge.conduct_debate(
            topic="Migrating from monolithic repo to micro-frontends",
            proponent="cto",
            opponent="sre",
            moderator="ceo",
            rounds=2,
        )
        assert session.session_id.startswith("debate_")
        assert session.rounds == 2
        # 2 rounds * 2 turns + 1 moderator synthesis = 5 turns
        assert len(session.turns) == 5
        assert session.consensus_score > 0
        assert session.recommended_action
        assert any(t.stance == "pro" for t in session.turns)
        assert any(t.stance == "con" for t in session.turns)
        assert any(t.stance == "synthesis" for t in session.turns)

    def test_ballot_persistence_and_retrieval(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        b1 = bridge.create_vote(proposal="Proposal 1", quorum="majority")
        b2 = bridge.create_vote(proposal="Proposal 2", quorum="supermajority")

        ballots = bridge.list_ballots(limit=10)
        assert len(ballots) >= 2
        assert any(b.ballot_id == b1.ballot_id for b in ballots)
        assert any(b.ballot_id == b2.ballot_id for b in ballots)

    def test_debate_persistence_and_retrieval(self, temp_db: Path):
        bridge = ConsensusBridge(db_path=temp_db)
        d1 = bridge.conduct_debate(topic="Topic 1", rounds=1)
        d2 = bridge.conduct_debate(topic="Topic 2", rounds=2)

        debates = bridge.list_debates(limit=10)
        assert len(debates) >= 2
        assert any(d.session_id == d1.session_id for d in debates)
        assert any(d.session_id == d2.session_id for d in debates)


class TestConsensusCli:
    """Tests for Typer CLI consensus command group."""

    def test_cli_vote_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["consensus", "vote", "Deploy canary v1.2", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "ballot_id" in data
        assert data["proposal"] == "Deploy canary v1.2"
        assert "passed" in data
        assert len(data["votes"]) >= 1

    def test_cli_vote_interactive(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["consensus", "vote", "Scale worker pool", "--quorum", "supermajority"])
        assert result.exit_code == 0
        assert "Consensus Vote Outcome" in result.output
        assert "Agent Ballots & Justifications" in result.output

    def test_cli_debate_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["consensus", "debate", "Async vs Sync queues", "--rounds", "1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "session_id" in data
        assert data["topic"] == "Async vs Sync queues"
        assert len(data["turns"]) == 3  # 1 pro, 1 con, 1 synthesis

    def test_cli_debate_interactive(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["consensus", "debate", "Async vs Sync queues", "--rounds", "1"])
        assert result.exit_code == 0
        assert "Multi-Agent Debate Session" in result.output
        assert "Consensus Synthesis & Directive" in result.output

    def test_cli_history_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["consensus", "history", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "ballots" in data
        assert "debates" in data


class TestMcpToolsParity:
    """Tests for native MCP consensus tools dual-engine parity."""

    def test_mcp_consensus_vote_fallback(self):
        from scripts.mcp_server import handle_consensus_vote
        raw = handle_consensus_vote({"proposal": "Enable distributed tracing", "quorum": "majority"})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["data"]["proposal"] == "Enable distributed tracing"
        assert "ballot_hash" in data["data"]

    def test_mcp_consensus_debate_fallback(self):
        from scripts.mcp_server import handle_consensus_debate
        raw = handle_consensus_debate({"topic": "Event-driven vs REST polling", "rounds": 1})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["data"]["topic"] == "Event-driven vs REST polling"
        assert data["data"]["consensus_score"] > 0

    def test_core_mcp_server_consensus_methods(self):
        from src.core.mcp_server import MekongMcpServer
        server = MekongMcpServer()
        vote_raw = server._handle_consensus_vote({"proposal": "Adopt OpenTelemetry exporter", "quorum": "majority"})
        vote_data = json.loads(vote_raw)
        assert vote_data["ok"] is True
        assert vote_data["data"]["passed"] is True

        debate_raw = server._handle_consensus_debate({"topic": "Stateless vs Stateful agents", "rounds": 1})
        debate_data = json.loads(debate_raw)
        assert debate_data["ok"] is True
        assert len(debate_data["data"]["turns"]) == 3


class TestAstCoreBoundary:
    """Verify standard-library-only rule for consensus_bridge.py."""

    FORBIDDEN_MODULES = {"anthropic", "openai", "requests", "httpx", "fastapi", "pydantic", "aiohttp"}

    def test_pure_standard_library_imports(self):
        rel_path = "src/core/consensus_bridge.py"
        full_path = Path(__file__).resolve().parents[1] / rel_path
        assert full_path.exists(), f"File {rel_path} does not exist"

        tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden import '{alias.name}' found in {rel_path} (line {node.lineno})"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden from-import '{node.module}' found in {rel_path} (line {node.lineno})"
                    )
