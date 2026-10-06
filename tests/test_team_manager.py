# Mekong CLI — MIT License
# Tests for TeamManager (core/team_manager.py)

import tempfile
from pathlib import Path
import pytest

from src.core.team_manager import (
    TeamManager,
    Team,
    TeamMember,
    TeamTask,
    _slugify,
)


@pytest.fixture
def temp_tm(tmp_path: Path):
    store_file = tmp_path / "teams.json"
    tm = TeamManager(storage_path=store_file)
    return tm


def test_slugify():
    assert _slugify("Đội Kỹ Thuật") == "đội-kỹ-thuật"
    assert _slugify("Team Alpha 123!") == "team-alpha-123"
    assert _slugify("") == "team"


def test_team_manager_init_defaults(temp_tm: TeamManager):
    teams = temp_tm.list_teams()
    assert len(teams) >= 4
    names = [t.name for t in teams]
    assert "Đội Kỹ Thuật" in names
    assert "Đội Kinh Doanh" in names


def test_create_and_get_team(temp_tm: TeamManager):
    team = temp_tm.create_team(
        name="Team Phoenix",
        members_count=4,
        roles=["lead", "dev", "reviewer", "qa"],
        description="Phoenix development swarm",
    )
    assert team.name == "Team Phoenix"
    assert team.member_count == 4
    assert team.status == "active"

    retrieved = temp_tm.get_team("Team Phoenix")
    assert retrieved is not None
    assert retrieved.id == team.id
    assert len(retrieved.members) == 4


def test_assign_and_update_task(temp_tm: TeamManager):
    team = temp_tm.create_team(name="Ops Team", members_count=2)
    task = temp_tm.assign_task(
        team_name_or_id=team.id,
        title="Check disk space",
        priority="high",
        owner="lead-1",
    )
    assert task.title == "Check disk space"
    assert task.status == "pending"

    # Update task
    updated = temp_tm.update_task(task.id, status="completed", result="Reclaimed 15GB")
    assert updated is not None
    assert updated.status == "completed"
    assert updated.result == "Reclaimed 15GB"
    assert updated.completed_at != ""


def test_delete_team(temp_tm: TeamManager):
    team = temp_tm.create_team(name="Temporary Team", members_count=1)
    assert temp_tm.get_team(team.id) is not None

    deleted = temp_tm.delete_team(team.id)
    assert deleted is True
    assert temp_tm.get_team(team.id) is None


def test_get_dashboard(temp_tm: TeamManager):
    db = temp_tm.get_dashboard()
    assert "total_teams" in db
    assert "total_members" in db
    assert "tasks_completed" in db
    assert db["total_teams"] >= 4


def test_orchestrate_templates(tmp_path: Path):
    store_file = tmp_path / "teams_orch.json"
    reports_dir = tmp_path / "reports"
    tm = TeamManager(storage_path=store_file)

    # Research
    rep_res = tm.orchestrate_research("Kubernetes Scaling", researchers=2, output_dir=str(reports_dir))
    assert rep_res.status == "completed"
    assert Path(rep_res.report_file).exists()

    # Cook
    rep_cook = tm.orchestrate_cook("API Gateway", devs=2, worktree=False, output_dir=str(reports_dir))
    assert rep_cook.status == "completed"
    assert Path(rep_cook.report_file).exists()

    # Review
    rep_rev = tm.orchestrate_review("AuthModule", reviewers=2, output_dir=str(reports_dir))
    assert rep_rev.status == "completed"
    assert len(rep_rev.findings) == 2

    # Debug
    rep_dbg = tm.orchestrate_debug("Timeout on /auth", debuggers=2, output_dir=str(reports_dir))
    assert rep_dbg.status == "completed"
    assert len(rep_dbg.findings) == 2
