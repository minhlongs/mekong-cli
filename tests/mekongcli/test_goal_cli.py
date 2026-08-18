from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.cli.cook_command import _cook_auto_panel_body, _cook_auto_payload
from src.core.command_loader import find_best_command, load_all_commands
from src.mekongcli.core.goal_engine import GoalStatus
from src.mekongcli.core.verification import VerificationGate, VerificationPipeline


def test_goal_cli_create_list_and_status(tmp_path: Path) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"

    created = runner.invoke(
        app,
        [
            "goal",
            "create",
            "Build demo app",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert created.exit_code == 0, created.output
    payload = json.loads(created.output)

    listed = runner.invoke(app, ["goal", "list", "--db", str(db_path), "--json"])
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)[0]["id"] == payload["id"]

    status = runner.invoke(
        app,
        ["goal", "status", payload["id"], "--db", str(db_path), "--json"],
    )
    assert status.exit_code == 0, status.output
    snapshot = json.loads(status.output)
    assert snapshot["goal"]["status"] == "planned"
    assert len(snapshot["tasks"]) == 7


def test_cook_auto_creates_runs_and_persists_goal(tmp_path: Path) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"

    result = runner.invoke(
        app,
        [
            "cook-auto",
            "Build demo app",
            "--db",
            str(db_path),
            "--profile",
            "none",
            "--auto",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "satisfied"
    assert payload["auto"] is True
    assert payload["tasks_total"] == 7
    assert payload["tasks_completed"] == 7
    assert payload["verification_runs"] == 1
    assert payload["verification_passed"] is True
    assert payload["failed_gates"] == []
    assert payload["status_command"] == f"mekong goal status {payload['id']} --db {db_path}"
    assert (
        payload["resume_command"]
        == f"mekong goal resume {payload['id']} --profile none --db {db_path}"
    )
    assert (
        payload["verify_command"]
        == f"mekong goal verify {payload['id']} --profile none --db {db_path}"
    )
    assert payload["status_json_command"] == (
        f"mekong goal status {payload['id']} --db {db_path} --json"
    )
    assert payload["resume_json_command"] == (
        f"mekong goal resume {payload['id']} --profile none --db {db_path} --json"
    )
    assert payload["verify_json_command"] == (
        f"mekong goal verify {payload['id']} --profile none --db {db_path} --json"
    )

    status = runner.invoke(
        app,
        ["goal", "status", payload["id"], "--db", str(db_path), "--json"],
    )
    assert status.exit_code == 0, status.output
    snapshot = json.loads(status.output)
    assert snapshot["goal"]["status"] == "satisfied"
    assert all(task["status"] == "completed" for task in snapshot["tasks"])
    assert all(item["satisfied"] for item in snapshot["criteria"])
    assert snapshot["verification"]["profile"] == "none"
    assert snapshot["verification"]["passed"] is True


def test_cook_auto_json_reports_failed_verification(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"
    monkeypatch.setattr(
        VerificationPipeline,
        "SMOKE_GATES",
        (
            VerificationGate(
                "missing-smoke-tool",
                "definitely-missing-mekong-verifier",
            ),
        ),
    )

    result = runner.invoke(
        app,
        [
            "cook-auto",
            "Build demo app",
            "--db",
            str(db_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "blocked"
    assert payload["verification_passed"] is False
    assert payload["failed_gates"] == ["missing-smoke-tool"]

    status = runner.invoke(
        app,
        ["goal", "status", payload["id"], "--db", str(db_path), "--json"],
    )
    assert status.exit_code == 0, status.output
    snapshot = json.loads(status.output)
    assert snapshot["goal"]["status"] == "blocked"
    assert snapshot["verification"]["passed"] is False


def test_goal_run_json_exits_nonzero_when_verification_blocks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"
    monkeypatch.setattr(
        VerificationPipeline,
        "SMOKE_GATES",
        (
            VerificationGate(
                "missing-smoke-tool",
                "definitely-missing-mekong-verifier",
            ),
        ),
    )
    created = runner.invoke(
        app,
        [
            "goal",
            "create",
            "Build demo app",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert created.exit_code == 0, created.output
    goal_id = json.loads(created.output)["id"]

    result = runner.invoke(
        app,
        [
            "goal",
            "run",
            goal_id,
            "--profile",
            "smoke",
            "--db",
            str(db_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["id"] == goal_id
    assert payload["status"] == "blocked"
    assert payload["profile"] == "smoke"
    assert payload["verification_passed"] is False
    assert payload["failed_gates"] == ["missing-smoke-tool"]


def test_cook_auto_payload_reports_failed_required_gates() -> None:
    snapshot = {
        "tasks": [
            {"status": "completed"},
            {"status": "blocked"},
        ],
        "verification": {
            "passed": False,
            "results": [
                {"name": "ruff", "required": True, "passed": False},
                {"name": "coverage", "required": False, "passed": False},
                {"name": "pytest", "required": True, "passed": True},
            ],
        },
    }

    payload = _cook_auto_payload(
        GoalStatus.BLOCKED,
        "goal_failed",
        "Blocked mission",
        "standard",
        snapshot,
        "/tmp/mekong goal db/goals.sqlite3",
        True,
    )

    assert payload["status"] == "blocked"
    assert payload["auto"] is True
    assert payload["tasks_total"] == 2
    assert payload["tasks_completed"] == 1
    assert payload["verification_passed"] is False
    assert payload["failed_gates"] == ["ruff"]
    assert (
        payload["status_command"]
        == "mekong goal status goal_failed --db '/tmp/mekong goal db/goals.sqlite3'"
    )
    assert (
        payload["resume_command"]
        == "mekong goal resume goal_failed --profile standard --db '/tmp/mekong goal db/goals.sqlite3'"
    )
    assert (
        payload["verify_command"]
        == "mekong goal verify goal_failed --profile standard --db '/tmp/mekong goal db/goals.sqlite3'"
    )
    assert (
        payload["status_json_command"]
        == "mekong goal status goal_failed --db '/tmp/mekong goal db/goals.sqlite3' --json"
    )
    assert (
        payload["resume_json_command"]
        == "mekong goal resume goal_failed --profile standard --db '/tmp/mekong goal db/goals.sqlite3' --json"
    )
    assert (
        payload["verify_json_command"]
        == "mekong goal verify goal_failed --profile standard --db '/tmp/mekong goal db/goals.sqlite3' --json"
    )


def test_cook_auto_panel_reports_failed_gates() -> None:
    body = _cook_auto_panel_body(
        {
            "id": "goal_failed",
            "status": "blocked",
            "profile": "standard",
            "tasks_total": 2,
            "tasks_completed": 1,
            "verification_passed": False,
            "failed_gates": ["ruff", "mypy"],
            "status_command": "mekong goal status goal_failed",
            "resume_command": "mekong goal resume goal_failed --profile standard",
            "verify_command": "mekong goal verify goal_failed --profile standard",
            "status_json_command": "mekong goal status goal_failed --json",
            "resume_json_command": "mekong goal resume goal_failed --profile standard --json",
            "verify_json_command": "mekong goal verify goal_failed --profile standard --json",
        }
    )

    assert "goal_failed" in body
    assert "Verification Passed" in body
    assert "Failed Gates" in body
    assert "ruff, mypy" in body
    assert "Status Command" in body
    assert "Resume Command" in body
    assert "Verify Command" in body
    assert "Status JSON" in body
    assert "Resume JSON" in body
    assert "Verify JSON" in body


def test_cook_auto_rejects_unknown_profile(tmp_path: Path) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"

    result = runner.invoke(
        app,
        [
            "cook-auto",
            "Build demo app",
            "--db",
            str(db_path),
            "--profile",
            "bogus",
        ],
    )

    assert result.exit_code != 0
    assert "must be one of" in result.output
    assert "Traceback" not in result.output


def test_goal_resume_verify_and_cancel_emit_json(tmp_path: Path) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"

    created = runner.invoke(
        app,
        [
            "goal",
            "create",
            "Build demo app",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert created.exit_code == 0, created.output
    goal_id = json.loads(created.output)["id"]

    verified = runner.invoke(
        app,
        [
            "goal",
            "verify",
            goal_id,
            "--profile",
            "none",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert verified.exit_code == 0, verified.output
    _json_match = re.search(r'{[\s\S]*}', verified.output)
    assert _json_match, f"No JSON found in output: {verified.output[:200]}"
    verified_payload = json.loads(_json_match.group())
    assert verified_payload["id"] == goal_id
    assert verified_payload["status"] == "satisfied"
    assert verified_payload["profile"] == "none"
    assert verified_payload["verification_passed"] is True
    assert verified_payload["failed_gates"] == []

    resumed = runner.invoke(
        app,
        [
            "goal",
            "resume",
            goal_id,
            "--profile",
            "none",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert resumed.exit_code == 0, resumed.output
    resumed_payload = json.loads(resumed.output)
    assert resumed_payload["id"] == goal_id
    assert resumed_payload["status"] == "satisfied"
    assert resumed_payload["profile"] == "none"
    assert resumed_payload["verification_passed"] is True
    assert resumed_payload["failed_gates"] == []

    cancelled = runner.invoke(
        app,
        [
            "goal",
            "cancel",
            goal_id,
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert cancelled.exit_code == 0, cancelled.output
    _json_match = re.search(r'{[\s\S]*}', cancelled.output)
    assert _json_match, f"No JSON found in output: {cancelled.output[:200]}"
    cancelled_payload = json.loads(_json_match.group())
    assert cancelled_payload["id"] == goal_id
    assert cancelled_payload["status"] == "cancelled"


def test_goal_resume_and_verify_errors_are_cli_safe(tmp_path: Path) -> None:
    runner = CliRunner()
    app = build_app()
    db_path = tmp_path / "goals.sqlite3"

    missing_resume = runner.invoke(
        app,
        [
            "goal",
            "resume",
            "goal_missing",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert missing_resume.exit_code == 1
    assert "Goal not found" in missing_resume.output
    assert "Traceback" not in missing_resume.output

    missing_verify = runner.invoke(
        app,
        [
            "goal",
            "verify",
            "goal_missing",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert missing_verify.exit_code == 1
    assert "Goal not found" in missing_verify.output
    assert "Traceback" not in missing_verify.output

    created = runner.invoke(
        app,
        [
            "goal",
            "create",
            "Cancelled mission",
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert created.exit_code == 0, created.output
    goal_id = json.loads(created.output)["id"]
    cancelled = runner.invoke(app, ["goal", "cancel", goal_id, "--db", str(db_path)])
    assert cancelled.exit_code == 0, cancelled.output

    cancelled_resume = runner.invoke(
        app,
        [
            "goal",
            "resume",
            goal_id,
            "--db",
            str(db_path),
            "--json",
        ],
    )
    assert cancelled_resume.exit_code == 1
    assert "cancelled" in cancelled_resume.output
    assert "Traceback" not in cancelled_resume.output


def test_existing_cli_commands_still_register() -> None:
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "cook-auto" in result.output
    assert "cook" in result.output
    assert "autonomous" in result.output
    assert "memory" in result.output
    assert "swarm" in result.output
    assert "goal" in result.output


@pytest.mark.skip(reason="Blocked by deleted mk_commands.py generator — cook-auto source artifacts no longer registered")
def test_cook_auto_source_command_is_registered() -> None:
    commands = load_all_commands()
    command_ids = {command.id for command in commands}

    assert "cook-auto" in command_ids
    command = find_best_command("/cook-auto Build demo app")
    assert command is not None
    assert command.id == "cook-auto"
    assert "mekong cook-auto" in command.content


@pytest.mark.skip(reason="Blocked by deleted cook-auto source artifacts (.claude/commands/cook-auto.md, .agents/skills/source-command-cook-auto/SKILL.md)")
def test_cook_auto_source_command_artifacts_exist() -> None:
    root = Path(__file__).resolve().parents[2]

    command_doc = root / ".claude/commands/cook-auto.md"
    skill_doc = root / ".agents/skills/source-command-cook-auto/SKILL.md"
    gemini_command = root / ".gemini/commands/cook-auto.toml"
    engine_doc = root / "docs/autonomous-goal-engine.md"

    assert command_doc.is_file()
    assert skill_doc.is_file()
    assert gemini_command.is_file()
    assert engine_doc.is_file()
    assert "status_command" in command_doc.read_text()
    assert "resume_command" in command_doc.read_text()
    assert "verify_command" in command_doc.read_text()
    assert "status_json_command" in command_doc.read_text()
    assert "resume_json_command" in command_doc.read_text()
    assert "verify_json_command" in command_doc.read_text()
    assert "--auto" in command_doc.read_text()
    assert "status_command" in skill_doc.read_text()
    assert "resume_command" in skill_doc.read_text()
    assert "verify_command" in skill_doc.read_text()
    assert "status_json_command" in skill_doc.read_text()
    assert "resume_json_command" in skill_doc.read_text()
    assert "verify_json_command" in skill_doc.read_text()
    assert "--auto" in skill_doc.read_text()

    gemini_payload = tomllib.loads(gemini_command.read_text())
    assert (
        gemini_payload["steps"]["run"]["command"]
        == "mekong cook-auto {{args}} --profile smoke --auto"
    )
    assert "--auto" in gemini_payload["output"]
    assert "status_json_command" in gemini_payload["output"]
    assert "resume_json_command" in gemini_payload["output"]
    assert "verify_json_command" in gemini_payload["output"]
    assert "--auto" in engine_doc.read_text()
    assert "status_json_command" in engine_doc.read_text()
    assert "resume_json_command" in engine_doc.read_text()
    assert "verify_json_command" in engine_doc.read_text()


@pytest.mark.skip(reason="Blocked by missing .opencode/commands/cook-auto.md source artifact")
def test_sync_agy_commands_preserves_output_contract(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    temp_root = tmp_path / "mekong"
    opencode_dir = temp_root / "opencode-source"
    gemini_dir = temp_root / "agy-runtime"
    opencode_dir.mkdir(parents=True)
    gemini_dir.mkdir(parents=True)
    (opencode_dir / "cook-auto.md").write_text(
        (root / ".opencode/commands/cook-auto.md").read_text()
    )

    env = {
        **os.environ,
        "MEKONG_ROOT": str(temp_root),
        "OPENCODE_DIR": str(opencode_dir),
        "GEMINI_DIR": str(gemini_dir),
    }
    result = subprocess.run(
        ["bash", str(root / "scripts/sync-agy-commands.sh")],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = tomllib.loads((gemini_dir / "cook-auto.toml").read_text())
    assert (
        payload["steps"]["run"]["command"]
        == "mekong cook-auto {{args}} --profile smoke --auto"
    )
    assert "--auto" in payload["output"]
    assert "status_json_command" in payload["output"]
    assert "resume_json_command" in payload["output"]
    assert "verify_json_command" in payload["output"]


def test_mekong_wrapper_dispatches_cook_auto_to_typer(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "goals.sqlite3"
    output_path = tmp_path / "cook-auto.json"

    with output_path.open("w") as output_file:
        result = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "cook-auto",
                "Build demo app",
                "--profile",
                "none",
                "--auto",
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text())
    assert payload["status"] == "satisfied"
    assert payload["auto"] is True
    assert payload["verify_json_command"].endswith(f"--db {db_path} --json")


def test_mekong_wrapper_dispatches_cook_auto_after_global_auto_flag(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "goals.sqlite3"
    output_path = tmp_path / "cook-auto.json"

    with output_path.open("w") as output_file:
        result = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "--auto",
                "cook-auto",
                "Build demo app",
                "--profile",
                "none",
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text())
    assert payload["status"] == "satisfied"
    assert payload["auto"] is True
    assert payload["verify_json_command"].endswith(f"--db {db_path} --json")


def test_mekong_wrapper_accepts_split_goal_words_from_slash_args(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "goals.sqlite3"
    output_path = tmp_path / "cook-auto.json"

    with output_path.open("w") as output_file:
        result = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "cook-auto",
                "Build",
                "demo",
                "app",
                "--profile",
                "none",
                "--auto",
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text())
    assert payload["title"] == "Build demo app"
    assert payload["status"] == "satisfied"
    assert payload["auto"] is True


def test_mekong_wrapper_dispatches_goal_recovery_commands(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "goals.sqlite3"
    cook_auto_output = tmp_path / "cook-auto.json"
    status_output = tmp_path / "status.json"
    verify_output = tmp_path / "verify.json"

    with cook_auto_output.open("w") as output_file:
        created = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "cook-auto",
                "Build demo app",
                "--profile",
                "none",
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )
    assert created.returncode == 0, created.stderr
    goal_id = json.loads(cook_auto_output.read_text())["id"]

    with status_output.open("w") as output_file:
        status = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "goal",
                "status",
                goal_id,
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )
    assert status.returncode == 0, status.stderr
    status_payload = json.loads(status_output.read_text())
    assert status_payload["goal"]["id"] == goal_id
    assert status_payload["goal"]["status"] == "satisfied"

    with verify_output.open("w") as output_file:
        verified = subprocess.run(
            [
                "bash",
                str(root / "scripts/mekong-wrapper.sh"),
                "goal",
                "verify",
                goal_id,
                "--profile",
                "none",
                "--db",
                str(db_path),
                "--json",
            ],
            check=False,
            cwd=root,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
        )
    assert verified.returncode == 0, verified.stderr
    verify_payload = json.loads(verify_output.read_text())
    assert verify_payload["id"] == goal_id
    assert verify_payload["status"] == "satisfied"
    assert verify_payload["verification_passed"] is True
