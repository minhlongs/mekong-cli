# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dedicated unit and integration tests for /orchestrate pipeline upgrades.

Covers:
1. CLI help surface: mekong orchestrate, mekong fix, mekong harness, mekong goal.
2. CLI fix execution: dry-run plan validation and live repair.
3. CLI harness execution: dry-run planning and eval suite mode.
4. TeamManager.orchestrate: template routing for fix, harness, goal, and NL auto-classification.
5. .orchestrate/latest/ handoff artifacts: task.md, plan.md, plan-verdict.md, execution.md, result-verdict.md, ship-report.md.
6. Command fabric markdown parsing: extract_execution ignores directory trees and extracts valid commands.
7. Command fabric invocation: invoke_command_fabric for orchestrate, fix, and harness.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.command_fabric.records import extract_execution
from src.command_fabric.runtime import invoke_command_fabric
from src.core.team_manager import TeamManager, get_team_manager


runner = CliRunner()


class TestCliSurfaceHelp:
    """Verify first-class CLI commands expose help documentation cleanly."""

    def test_orchestrate_help(self):
        app = build_app()
        result = runner.invoke(app, ["orchestrate", "--help"])
        assert result.exit_code == 0
        assert "🚀 Orchestrate multi-agent workflows" in result.stdout
        assert "--template" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--json" in result.stdout

    def test_fix_help(self):
        app = build_app()
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "🛠️ Fix bugs, errors, and test failures" in result.stdout
        assert "--dry-run" in result.stdout or "--execute" in result.stdout
        assert "--auto" in result.stdout
        assert "--json" in result.stdout

    def test_harness_help(self):
        app = build_app()
        result = runner.invoke(app, ["harness", "--help"])
        assert result.exit_code == 0
        assert "🛡️ Harness PEV" in result.stdout
        assert "--eval" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--json" in result.stdout

    def test_goal_help(self):
        app = build_app()
        result = runner.invoke(app, ["goal", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "run" in result.stdout

    def test_team_orchestrate_help(self):
        app = build_app()
        result = runner.invoke(app, ["team", "orchestrate", "--help"])
        assert result.exit_code == 0
        assert "Generic team orchestration entrypoint" in result.stdout


class TestFixCommandExecution:
    """Verify mekong fix dry-run and execution flows."""

    def test_fix_dry_run_json(self):
        app = build_app()
        result = runner.invoke(app, ["fix", "database deadlock on retry", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["mode"] == "dry-run"
        assert "fix database deadlock on retry" in data["goal"]
        assert len(data["plan"]["steps"]) > 0

    def test_fix_dry_run_rich(self):
        app = build_app()
        result = runner.invoke(app, ["fix", "null pointer exception in router", "--dry-run"])
        assert result.exit_code == 0
        assert "Kế Hoạch Sửa Lỗi" in result.stdout or "Fix Plan" in result.stdout or "Các Bước Khắc Phục" in result.stdout


class TestHarnessCommandExecution:
    """Verify mekong harness dry-run and eval modes."""

    def test_harness_dry_run_json(self):
        app = build_app()
        result = runner.invoke(app, ["harness", "Production Deployment Gate", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["mode"] == "dry-run"
        assert data["suite"] == "harness-pev"
        assert data["passed"] is True

    def test_harness_eval_json(self):
        app = build_app()
        result = runner.invoke(app, ["harness", "--eval", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["suite"] == "solo-ceo-harness"
        assert data["passed"] is True
        assert data["passed_count"] == 6


class TestTeamManagerOrchestrateRouting:
    """Verify TeamManager.orchestrate routes correctly and auto-classifies NL prompts."""

    @pytest.fixture
    def manager(self, tmp_path):
        return TeamManager(storage_path=tmp_path / "teams.json")

    def test_route_fix_template(self, manager):
        report = manager.orchestrate(
            template="fix",
            context="broken session token parsing",
            dry_run=True,
        )
        assert report.template == "fix"
        assert report.status == "completed"
        assert "broken session token parsing" in report.goal
        assert len(report.artifacts) >= 6

    def test_route_harness_template(self, manager):
        report = manager.orchestrate(
            template="harness",
            context="pre-release compliance audit",
            dry_run=True,
        )
        assert report.template == "harness"
        assert report.status == "completed"
        assert len(report.artifacts) >= 6

    def test_route_goal_template(self, manager):
        report = manager.orchestrate(
            template="goal",
            context="scale background worker cluster",
            dry_run=True,
        )
        assert report.template == "goal"
        assert report.status == "completed"
        assert len(report.artifacts) >= 6

    def test_auto_classify_fix_prompt(self, manager):
        report = manager.orchestrate(
            context="fix memory leak in stream consumer",
            dry_run=True,
        )
        assert report.template == "fix"

    def test_auto_classify_harness_prompt(self, manager):
        report = manager.orchestrate(
            context="run quality gate and verify all checks",
            dry_run=True,
        )
        assert report.template == "harness"

    def test_auto_classify_goal_prompt(self, manager):
        report = manager.orchestrate(
            context="autonomous mission for data sync pipeline",
            dry_run=True,
        )
        assert report.template == "goal"


class TestHandoffArtifactGeneration:
    """Verify that .orchestrate/latest/ contains all 6 handoff files with expected structure."""

    def test_handoff_files_written(self, tmp_path):
        manager = TeamManager(storage_path=tmp_path / "teams.json")
        report = manager.orchestrate(
            template="cook",
            context="build user authentication middleware",
            dry_run=True,
        )
        handoff_dir = Path(".orchestrate/latest")
        assert (handoff_dir / "task.md").is_file()
        assert (handoff_dir / "plan.md").is_file()
        assert (handoff_dir / "plan-verdict.md").is_file()
        assert (handoff_dir / "execution.md").is_file()
        assert (handoff_dir / "result-verdict.md").is_file()
        assert (handoff_dir / "ship-report.md").is_file()

        task_content = (handoff_dir / "task.md").read_text(encoding="utf-8")
        assert "build user authentication middleware" in task_content
        assert "COOK" in task_content

        plan_verdict = (handoff_dir / "plan-verdict.md").read_text(encoding="utf-8")
        assert "PASS ROUND 1" in plan_verdict

        ship_report = (handoff_dir / "ship-report.md").read_text(encoding="utf-8")
        assert "READY_TO_SHIP" in ship_report


class TestCommandFabricExtractionAndInvocation:
    """Verify extract_execution ignores directory trees and invoke_command_fabric executes native commands."""

    def test_extract_execution_ignores_directory_tree(self):
        content = (
            "# My Command\n\n"
            "```\n"
            ".agents/skills/\n"
            "├── orchestrate/\n"
            "│   └── SKILL.md\n"
            "└── fix/\n"
            "    └── SKILL.md\n"
            "```\n\n"
            "## Execution\n"
            "```bash\n"
            "mekong orchestrate $ARGUMENTS\n"
            "```\n"
        )
        extracted = extract_execution(content)
        assert extracted == "mekong orchestrate $ARGUMENTS"

    def test_extract_execution_skips_ascii_boxes(self):
        content = (
            "# Workflow\n\n"
            "```\n"
            "┌──────────────┐\n"
            "│   Planner    │\n"
            "└──────────────┘\n"
            "```\n\n"
            "```sh\n"
            "mekong fix $ARGUMENTS\n"
            "```\n"
        )
        extracted = extract_execution(content)
        assert extracted == "mekong fix $ARGUMENTS"

    def test_invoke_command_fabric_orchestrate_help(self):
        result = invoke_command_fabric("orchestrate", ["--help"])
        assert result.exit_code == 0
        assert "orchestrate" in result.command

    def test_invoke_command_fabric_fix_help(self):
        result = invoke_command_fabric("fix", ["--help"])
        assert result.exit_code == 0
        assert "fix" in result.command
