# Mekong CLI — MIT License
# Tests for team command (cli/commands/team_command.py)

import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from src.cli.commands.team_command import team_app

runner = CliRunner()


def test_team_help():
    result = runner.invoke(team_app, ["--help"])
    assert result.exit_code == 0
    assert "Agent Teams" in result.output
    assert "create" in result.output
    assert "list" in result.output
    assert "assign" in result.output
    assert "dashboard" in result.output


def test_team_dashboard_json():
    result = runner.invoke(team_app, ["dashboard", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_teams" in data
    assert "total_members" in data


def test_team_list_and_filter():
    result = runner.invoke(team_app, ["list"])
    assert result.exit_code == 0
    assert "Đội Kỹ Thuật" in result.output or "ACTIVE" in result.output

    result_json = runner.invoke(team_app, ["list", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.output)
    assert data["ok"] is True
    assert len(data["teams"]) > 0


def test_team_create_and_assign():
    team_name = "Team Test-CLI"
    res_create = runner.invoke(team_app, ["create", team_name, "--members", "3", "--json"])
    assert res_create.exit_code == 0
    created = json.loads(res_create.output)
    assert created["ok"] is True
    assert created["team"]["name"] == team_name

    res_assign = runner.invoke(
        team_app,
        ["assign", team_name, "Deploy to Staging", "--priority", "high", "--json"],
    )
    assert res_assign.exit_code == 0
    assigned = json.loads(res_assign.output)
    assert assigned["ok"] is True
    assert assigned["task"]["title"] == "Deploy to Staging"

    # Cleanup
    res_del = runner.invoke(team_app, ["delete", team_name, "--force"])
    assert res_del.exit_code == 0


def test_team_orchestration_cli(tmp_path: Path):
    res_res = runner.invoke(
        team_app,
        ["research", "High Frequency Trading", "--researchers", "2", "--output", str(tmp_path), "--json"],
    )
    assert res_res.exit_code == 0
    data_res = json.loads(res_res.output)
    assert data_res["status"] == "completed"

    res_cook = runner.invoke(
        team_app,
        ["cook", "Real-time Order Book", "--devs", "2", "--no-worktree", "--output", str(tmp_path), "--json"],
    )
    assert res_cook.exit_code == 0
    data_cook = json.loads(res_cook.output)
    assert data_cook["status"] == "completed"

    res_rev = runner.invoke(
        team_app,
        ["review", "OrderMatchingEngine", "--reviewers", "2", "--output", str(tmp_path), "--json"],
    )
    assert res_rev.exit_code == 0
    data_rev = json.loads(res_rev.output)
    assert data_rev["status"] == "completed"

    res_dbg = runner.invoke(
        team_app,
        ["debug", "Latency spike in matcher", "--debuggers", "2", "--output", str(tmp_path), "--json"],
    )
    assert res_dbg.exit_code == 0
    data_dbg = json.loads(res_dbg.output)
    assert data_dbg["status"] == "completed"
