# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Test suite for Google Antigravity integration."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


from scripts.antigravity_agent_loader import get_agent, get_define_subagent_payload
from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.agent_cli_package import (
    materialize_agent_cli_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"
SUBAGENTS_DIR = AGENTS_DIR / "subagents"


def test_typer_cli_commands_have_skill_parity() -> None:
    """Assert 100% of top-level Typer CLI commands and groups in build_app() have a SKILL.md."""
    from src.cli.app_setup import build_app

    app = build_app()
    cmd_names = {
        c.name or (c.callback.__name__.replace("_", "-") if c.callback else None)
        for c in app.registered_commands
    }
    group_names = {g.name for g in app.registered_groups if g.name}
    all_commands = sorted((cmd_names | group_names) - {None})

    assert len(all_commands) == 81, f"Expected 81 Typer commands/groups, got {len(all_commands)}"

    missing_skills = []
    for cmd in all_commands:
        skill_file = SKILLS_DIR / cmd / "SKILL.md"
        if not skill_file.exists():
            missing_skills.append(cmd)

    assert not missing_skills, (
        f"Parity failure: missing SKILL.md for {len(missing_skills)} commands: {missing_skills}"
    )


def test_antigravity_skills_exist_and_are_valid() -> None:
    """Ensure .agents/skills contains all expected skills with valid frontmatter."""
    assert SKILLS_DIR.exists(), f"Missing {SKILLS_DIR}"
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    assert len(skill_dirs) >= 220, f"Expected at least 220 skills, found {len(skill_dirs)}"

    key_skills = [
        "cook",
        "binh-phap",
        "idea",
        "plan",
        "ship",
        "daily",
        "cto",
        "dev",
        "ke-toan",
        "thue",
        "zalo-oa",
        "agent",
        "cfo",
        "cmo",
        "doctor",
        "version",
        "deploy",
        "build",
        "spec",
        "bmad",
    ]
    for skill_name in key_skills:
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.exists(), f"Missing key skill directory: {skill_name}"
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"Missing SKILL.md in {skill_name}"

        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name}/SKILL.md does not start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"{skill_name}/SKILL.md missing frontmatter delimiters"
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict), f"{skill_name}/SKILL.md frontmatter did not parse as dictionary"
        assert fm.get("name") == skill_name, f"{skill_name}/SKILL.md name mismatch"
        desc = str(fm.get("description", "")).strip()
        assert desc not in (">-", "|", ">", "|-", ""), f"{skill_name}/SKILL.md has raw scalar marker: {desc}"
        assert not desc.startswith(">-"), f"{skill_name}/SKILL.md starts with scalar marker: {desc}"
        assert len(desc) >= 10, f"{skill_name}/SKILL.md description too short: {desc}"


def test_every_skill_frontmatter_conformance() -> None:
    """Audit all skills in .agents/skills to verify YAML frontmatter validity and description invariants."""
    raw_block_markers = {">-", "|", ">", "|-", "'-'", "''", '""'}
    generic_pattern = re.compile(
        r"^(Mekong CLI \S+ command|Execute Mekong CLI .* workflow|Run Mekong .*workflow command)\.*$",
        re.IGNORECASE,
    )

    failures: list[str] = []
    for sdir in sorted(SKILLS_DIR.iterdir()):
        if not sdir.is_dir():
            continue
        skill_file = sdir / "SKILL.md"
        if not skill_file.exists():
            failures.append(f"{sdir.name}: missing SKILL.md")
            continue
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) < 3:
            failures.append(f"{sdir.name}: missing frontmatter enclosed in '---'")
            continue

        try:
            fm = yaml.safe_load(parts[1])
        except Exception as exc:
            failures.append(f"{sdir.name}: YAML parsing error: {exc}")
            continue

        if not isinstance(fm, dict):
            failures.append(f"{sdir.name}: frontmatter did not parse as a dictionary")
            continue

        name = fm.get("name")
        if not name:
            failures.append(f"{sdir.name}: missing or empty 'name' field")
        elif name != sdir.name:
            failures.append(f"{sdir.name}: frontmatter name '{name}' does not match directory '{sdir.name}'")

        raw_desc = fm.get("description")
        if raw_desc is None:
            failures.append(f"{sdir.name}: missing 'description' field")
            continue

        desc = str(raw_desc).strip()
        if not desc:
            failures.append(f"{sdir.name}: description is empty")
        elif desc in raw_block_markers or desc.startswith(">-"):
            failures.append(f"{sdir.name}: description is raw/corrupted YAML block marker: {desc!r}")
        elif len(desc) < 10:
            failures.append(f"{sdir.name}: description too short ({len(desc)} chars): {desc!r}")
        elif generic_pattern.match(desc):
            failures.append(f"{sdir.name}: description contains uncurated generic fallback: {desc!r}")

    assert not failures, (
        f"Frontmatter conformance failures across {len(failures)} skill(s):\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


def test_antigravity_subagent_registry() -> None:
    """Verify subagent registry contains all core harness roles with valid definitions."""
    registry_file = SUBAGENTS_DIR / "registry.json"
    assert registry_file.exists(), f"Missing {registry_file}"

    data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert data.get("schema") == "antigravity.subagents.registry.v1"
    agents = data.get("agents", [])
    assert len(agents) == 25, f"Expected 25 agents, found {len(agents)}"

    agent_ids = {a["id"] for a in agents}
    required_roles = {
        "ceo",
        "sun-tzu",
        "ae",
        "pm",
        "eng",
        "ops",
        "tester",
        "cto",
        "cmo",
        "coo",
        "cfo",
        "cso",
        "planner",
        "brainstormer",
        "code-reviewer",
        "code-simplifier",
        "debugger",
        "docs-manager",
        "fullstack-developer",
        "git-manager",
        "journal-writer",
        "kongming",
        "project-manager",
        "researcher",
        "ui-ux-designer",
    }
    assert required_roles.issubset(agent_ids), f"Missing core roles: {required_roles - agent_ids}"

    for a in agents:
        assert "name" in a
        assert "role" in a
        assert "description" in a
        assert "tools" in a
        assert "definition_path" in a
        def_path = PROJECT_ROOT / a["definition_path"]
        assert def_path.exists(), f"Missing agent definition file: {def_path}"
        assert len(def_path.read_text(encoding="utf-8").strip()) > 0


def test_antigravity_agent_loader_helper() -> None:
    """Verify agent loader generates valid define_subagent payloads."""
    ceo_agent = get_agent("ceo")
    assert ceo_agent is not None
    assert ceo_agent["can_override"] is True

    payload = get_define_subagent_payload("ceo")
    assert payload["name"] == "ceo"
    assert "CEO Solo" in payload["system_prompt"]
    assert payload["enable_write_tools"] is True
    assert payload["enable_subagent_tools"] is True
    assert payload["enable_mcp_tools"] is True

    suntzu_payload = get_define_subagent_payload("sun-tzu")
    assert suntzu_payload["name"] == "sun_tzu"
    assert "Sun Tzu" in suntzu_payload["system_prompt"]


def test_gemini_rules_and_antigravity_doc() -> None:
    """Verify GEMINI.md rules and ANTIGRAVITY.md documentation exist and are populated."""
    gemini_file = PROJECT_ROOT / "GEMINI.md"
    assert gemini_file.exists(), "GEMINI.md does not exist"
    content = gemini_file.read_text(encoding="utf-8")
    assert "/cook" in content
    assert "/binh-phap" in content
    assert "Mekong CLI" in content

    antigravity_file = PROJECT_ROOT / "ANTIGRAVITY.md"
    assert antigravity_file.exists(), "ANTIGRAVITY.md does not exist"
    doc_content = antigravity_file.read_text(encoding="utf-8")
    assert ".agents/skills/" in doc_content
    assert "/ke-toan" in doc_content


def test_command_fabric_antigravity_export(tmp_path) -> None:
    """Verify command fabric exports antigravity manifest and skills."""
    manifest = export_adapter_manifest("antigravity")
    assert manifest["adapter"] == "antigravity"
    assert manifest["schema"] == "mekong.command_fabric.adapter.antigravity.v1"
    assert manifest["command_count"] > 0
    assert any(cmd["id"] == "cook" for cmd in manifest["commands"])

    # Test materialize package
    pkg = materialize_agent_cli_package(tmp_path, "antigravity")
    assert pkg["host"] == "antigravity"
    skills_root = tmp_path / "antigravity" / "skills"
    assert (skills_root / "cook" / "SKILL.md").exists()


def test_sync_antigravity_verify_cli() -> None:
    """Run sync_antigravity.py --verify and ensure return code 0."""
    res = subprocess.run(
        [sys.executable, "scripts/sync_antigravity.py", "--verify"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert res.returncode == 0, f"sync_antigravity --verify failed: {res.stderr}\n{res.stdout}"
    assert "Verification passed!" in res.stdout


def test_global_antigravity_installation() -> None:
    """Verify machine-wide skills, plugins, and skills.json exist for multi-project support."""
    user_home = Path.home()
    global_skills_dir = user_home / ".gemini" / "config" / "skills"
    global_skills_json = user_home / ".gemini" / "config" / "skills.json"
    global_plugin_dir = user_home / ".gemini" / "config" / "plugins" / "mekong-cli"

    assert global_skills_dir.exists(), f"Missing {global_skills_dir}"
    skill_dirs = [d for d in global_skills_dir.iterdir() if d.is_dir()]
    assert len(skill_dirs) >= 220, f"Global skills count too low: {len(skill_dirs)}"

    assert global_skills_json.exists(), f"Missing {global_skills_json}"
    manifest = json.loads(global_skills_json.read_text(encoding="utf-8"))
    assert "entries" in manifest
    assert any("skills" in entry.get("path", "") for entry in manifest["entries"])

    assert (global_plugin_dir / "plugin.json").exists(), f"Missing {global_plugin_dir / 'plugin.json'}"

    # Verify portability of command execution (mekong instead of python3 -m src.main)
    cook_skill = global_skills_dir / "cook" / "SKILL.md"
    assert cook_skill.exists()
    content = cook_skill.read_text(encoding="utf-8")
    assert "python3 -m src.main" not in content, "Execution should not use repo-relative python3 -m src.main"
    assert "mekong" in content, "Execution should use global mekong binary"

    # Verify frontmatter conformance of all global skills
    for sdir in skill_dirs:
        sfile = sdir / "SKILL.md"
        assert sfile.exists(), f"Global skill {sdir.name} missing SKILL.md"
        parts = sfile.read_text(encoding="utf-8").split("---", 2)
        assert len(parts) >= 3, f"Global skill {sdir.name} missing frontmatter delimiters"
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict), f"Global skill {sdir.name} frontmatter not dict"
        desc = str(fm.get("description", "")).strip()
        assert desc not in (">-", "|", ">", "|-", ""), f"Global skill {sdir.name} has corrupted marker: {desc}"
        assert not desc.startswith(">-"), f"Global skill {sdir.name} starts with marker: {desc}"
        assert len(desc) >= 10, f"Global skill {sdir.name} description too short: {desc}"


def test_target_project_scaffolding(tmp_path) -> None:
    """Verify scripts/sync_antigravity.py can scaffold any new project workspace."""
    target_project = tmp_path / "my_new_app"
    res = subprocess.run(
        [sys.executable, "scripts/sync_antigravity.py", "--target", str(target_project)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert res.returncode == 0
    assert (target_project / ".agents" / "skills" / "cook" / "SKILL.md").exists()
    assert (target_project / ".agents" / "subagents" / "registry.json").exists()
    assert (target_project / "GEMINI.md").exists()


def test_bootstrap_auto_and_g_command_aliases() -> None:
    """Verify bootstrap-auto-parallel, bootstrap-auto, bootstrap-auto-fast, and g CLI commands exist."""
    commands_to_check = [
        ["bootstrap-auto-parallel", "--help"],
        ["bootstrap-auto", "--help"],
        ["bootstrap-auto-fast", "--help"],
        ["g", "--help"],
    ]
    for cmd in commands_to_check:
        res = subprocess.run(
            [sys.executable, "-m", "src.main"] + cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert res.returncode == 0, f"Command failed: {cmd}, stderr: {res.stderr}"
        if cmd[0] == "g":
            assert "Goal alias (/g)" in res.stdout
        else:
            assert "bootstrap" in res.stdout.lower() or "durable autonomous goal" in res.stdout


def test_bootstrap_and_g_skills_in_antigravity() -> None:
    """Verify /g and /bootstrap-auto-parallel skills are present with valid execution blocks."""
    for skill_name in ["g", "goal", "bootstrap-auto-parallel", "bootstrap-auto"]:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Skill file missing: {skill_file}"
        content = skill_file.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in content
        assert "mekong " in content


