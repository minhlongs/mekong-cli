# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_support.py — Comprehensive test suite for Customer Success & Autonomous Support Suite.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.support_engine import (
    BugReport,
    FeedbackRecord,
    IssueTriage,
    NpsSummary,
    OnboardingStatus,
    SupportEngine,
)

runner = CliRunner()


@pytest.fixture
def temp_support_engine(tmp_path: Path) -> Generator[SupportEngine, None, None]:
    """Provide an isolated SupportEngine instance with a temporary database and workspace."""
    db_file = tmp_path / "support_test.db"
    engine = SupportEngine(db_path=db_file, project_root=tmp_path)
    yield engine


class TestSupportEngineCore:
    """Unit tests for SupportEngine core capabilities."""

    def test_onboarding_lifecycle(self, temp_support_engine: SupportEngine) -> None:
        # Initial status
        init_st = temp_support_engine.get_onboarding_status()
        assert isinstance(init_st, OnboardingStatus)
        assert init_st.total_count == 5
        assert init_st.completed_count == 0
        assert init_st.progress_pct == 0.0
        assert init_st.current_step == 1

        # Complete step 1
        st1 = temp_support_engine.complete_onboarding_step(step_index=1, notes="Set keys in .env")
        assert st1.completed_count == 1
        assert st1.progress_pct == 20.0
        assert st1.current_step == 2
        assert st1.steps[0]["completed"] is True
        assert st1.steps[0]["notes"] == "Set keys in .env"

        # Complete step 2
        st2 = temp_support_engine.complete_onboarding_step(step_index=2)
        assert st2.completed_count == 2
        assert st2.progress_pct == 40.0
        assert st2.current_step == 3

        # Invalid step index
        with pytest.raises(ValueError):
            temp_support_engine.complete_onboarding_step(step_index=99)

        # Reset onboarding
        reset_st = temp_support_engine.reset_onboarding()
        assert reset_st.completed_count == 0
        assert reset_st.progress_pct == 0.0
        assert reset_st.current_step == 1

    def test_feedback_and_nps_calculation(self, temp_support_engine: SupportEngine) -> None:
        # Initially empty NPS
        empty_nps = temp_support_engine.get_nps_summary()
        assert empty_nps.total_responses == 0
        assert empty_nps.nps_score == 0.0

        # Submit ratings: two promoters (10, 9), one passive (8), one detractor (4)
        fb1 = temp_support_engine.submit_feedback(nps_score=10, feedback_text="Loving the PEV engine!", category="product")
        assert isinstance(fb1, FeedbackRecord)
        assert fb1.id.startswith("FB-")
        assert fb1.nps_score == 10

        temp_support_engine.submit_feedback(nps_score=9, feedback_text="Very fast CLI", category="performance")
        temp_support_engine.submit_feedback(nps_score=8, feedback_text="Solid, needs more docs", category="product")
        temp_support_engine.submit_feedback(nps_score=4, feedback_text="Steep learning curve", category="support")

        summary = temp_support_engine.get_nps_summary()
        assert isinstance(summary, NpsSummary)
        assert summary.total_responses == 4
        assert summary.promoters == 2
        assert summary.passives == 1
        assert summary.detractors == 1
        # NPS = (2 - 1) / 4 * 100 = 25.0
        assert summary.nps_score == 25.0

        # Invalid score
        with pytest.raises(ValueError):
            temp_support_engine.submit_feedback(nps_score=15)

        # List feedback
        fbs = temp_support_engine.list_feedback()
        assert len(fbs) == 4

    def test_bug_report_submission(self, temp_support_engine: SupportEngine) -> None:
        bug = temp_support_engine.submit_bug(
            title="Database lock under high concurrent subagent load",
            severity="high",
            description="Operational engine timed out waiting for SQLite write lock",
            steps="Spawn 10 parallel subagents with --concurrency 10",
        )
        assert isinstance(bug, BugReport)
        assert bug.id.startswith("BUG-")
        assert bug.severity == "high"
        assert bug.status == "new"

        bugs = temp_support_engine.list_bugs(status="ALL")
        assert len(bugs) == 1
        assert bugs[0].id == bug.id

    def test_smart_issue_triage(self, temp_support_engine: SupportEngine) -> None:
        t_auth = temp_support_engine.triage_issue("401 Unauthorized API key missing")
        assert isinstance(t_auth, IssueTriage)
        assert t_auth.category == "auth_setup"
        assert t_auth.urgency == "high"
        assert "mekong config" in t_auth.recommended_action

        t_bill = temp_support_engine.triage_issue("Stripe subscription renewal failed for invoice 102")
        assert t_bill.category == "billing"
        assert t_bill.urgency == "high"

        t_crash = temp_support_engine.triage_issue("Process crash traceback fatal exception in AST")
        assert t_crash.category == "bug_report"
        assert t_crash.urgency in {"critical", "high"}

        t_perf = temp_support_engine.triage_issue("System is too slow and execution hangs")
        assert t_perf.category == "performance"
        assert t_perf.urgency == "medium"

        t_gen = temp_support_engine.triage_issue("How do I use this CLI?")
        assert t_gen.category == "general_inquiry"
        assert t_gen.urgency == "low"

    def test_get_support_channels(self, temp_support_engine: SupportEngine) -> None:
        channels = temp_support_engine.get_support_channels()
        assert isinstance(channels, dict)
        assert "github_issues" in channels
        assert "email_support" in channels
        assert "billing_support" in channels

    def test_get_status(self, temp_support_engine: SupportEngine) -> None:
        status = temp_support_engine.get_status()
        assert isinstance(status, dict)
        assert "onboarding_progress_pct" in status
        assert "nps_score" in status
        assert "open_bugs_count" in status
        assert "channels" in status


class TestSupportCliCommands:
    """Integration tests for Typer CLI commands."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_support_overview_json(self) -> None:
        res = runner.invoke(self.app, ["support", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "onboarding_progress_pct" in data
        assert "nps_score" in data
        assert "channels" in data

    def test_cli_support_overview_console(self) -> None:
        res = runner.invoke(self.app, ["support"])
        assert res.exit_code == 0
        assert "CUSTOMER SUCCESS & SUPPORT CONTROL PLANE" in res.output or "Customer Success Dashboard" in res.output

    def test_cli_support_onboard_json(self) -> None:
        res = runner.invoke(self.app, ["support", "onboard", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "steps" in data
        assert len(data["steps"]) == 5

    def test_cli_support_onboard_step_and_reset(self) -> None:
        # Step 1
        res = runner.invoke(self.app, ["support", "onboard", "--step", "1", "--notes", "Configured environment", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["completed_count"] >= 1

        # Reset
        res_reset = runner.invoke(self.app, ["support", "onboard", "--reset", "--json"])
        assert res_reset.exit_code == 0
        data_reset = json.loads(res_reset.output)
        assert data_reset["completed_count"] == 0

    def test_cli_support_feedback_and_report_json(self) -> None:
        # Submit feedback
        res_fb = runner.invoke(
            self.app,
            ["support", "feedback", "--nps", "10", "--text", "Super responsive!", "--category", "perf", "--json"],
        )
        assert res_fb.exit_code == 0
        fb_data = json.loads(res_fb.output)
        assert fb_data["nps_score"] == 10
        assert fb_data["category"] == "perf"

        # View report
        res_rep = runner.invoke(self.app, ["support", "feedback", "--report", "--json"])
        assert res_rep.exit_code == 0
        rep_data = json.loads(res_rep.output)
        assert "nps_score" in rep_data
        assert rep_data["total_responses"] >= 1

    def test_cli_support_bug_json(self) -> None:
        res = runner.invoke(
            self.app,
            ["support", "bug", "Memory spike during benchmark", "--severity", "high", "--desc", "High RSS memory", "--json"],
        )
        assert res.exit_code == 0
        bug_data = json.loads(res.output)
        assert bug_data["id"].startswith("BUG-")
        assert bug_data["severity"] == "high"

    def test_cli_support_triage_json(self) -> None:
        res = runner.invoke(
            self.app,
            ["support", "triage", "Error: 401 Unauthorized token expired", "--json"],
        )
        assert res.exit_code == 0
        triage_data = json.loads(res.output)
        assert triage_data["category"] == "auth_setup"
        assert "recommended_action" in triage_data

    def test_cli_support_contact_json(self) -> None:
        res = runner.invoke(self.app, ["support", "contact", "--json"])
        assert res.exit_code == 0
        channels = json.loads(res.output)
        assert "github_issues" in channels
        assert "email_support" in channels


class TestSupportMcpTools:
    """Test parity for native MCP tools across FastMCP and fallback stdio engine."""

    def test_scripts_mcp_support_tools(self) -> None:
        import scripts.mcp_server as mcp_scripts

        # Test onboard status
        onboard_out = mcp_scripts.handle_support_onboard_status({})
        onboard = json.loads(onboard_out)
        assert "progress_pct" in onboard
        assert "steps" in onboard

        # Test feedback submit
        fb_out = mcp_scripts.handle_support_feedback_submit({
            "nps_score": 9,
            "feedback_text": "Great platform experience",
            "category": "product",
        })
        fb = json.loads(fb_out)
        assert fb["id"].startswith("FB-")
        assert fb["nps_score"] == 9

        # Test triage
        triage_out = mcp_scripts.handle_support_triage({"issue_text": "billing credit card expired"})
        triage = json.loads(triage_out)
        assert triage["category"] == "billing"

    def test_core_mcp_support_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        onboard_out = server._handle_support_onboard_status()
        onboard = json.loads(onboard_out)
        assert "steps" in onboard

        fb_out = server._handle_support_feedback_submit(nps_score=10, feedback_text="Outstanding!")
        fb = json.loads(fb_out)
        assert fb["nps_score"] == 10

        triage_out = server._handle_support_triage(issue_text="traceback fatal exception")
        triage = json.loads(triage_out)
        assert triage["category"] == "bug_report"


class TestSupportBoundary:
    """Ensure src/core/support_engine.py complies with zero vendor SDK import boundary."""

    def test_ast_boundary_pure_standard_library(self) -> None:
        engine_file = Path(__file__).resolve().parents[1] / "src" / "core" / "support_engine.py"
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
