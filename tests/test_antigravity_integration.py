# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Test suite for Google Antigravity integration."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


from scripts.antigravity_agent_loader import get_agent, get_define_subagent_payload
from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.agent_cli_package import (
    materialize_agent_cli_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"
SUBAGENTS_DIR = AGENTS_DIR / "subagents"


def test_antigravity_skills_exist_and_are_valid() -> None:
    """Ensure .agents/skills contains all expected skills with valid frontmatter."""
    assert SKILLS_DIR.exists(), f"Missing {SKILLS_DIR}"
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    assert len(skill_dirs) >= 150, f"Expected at least 150 skills, found {len(skill_dirs)}"

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
    ]
    for skill_name in key_skills:
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.exists(), f"Missing key skill directory: {skill_name}"
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"Missing SKILL.md in {skill_name}"

        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name}/SKILL.md does not start with YAML frontmatter"
        assert f"name: {skill_name}" in content, f"{skill_name}/SKILL.md missing name frontmatter"
        assert "description:" in content, f"{skill_name}/SKILL.md missing description frontmatter"


def test_every_skill_frontmatter_conformance() -> None:
    """Audit all skills in .agents/skills to verify no syntax or frontmatter errors."""
    for sdir in SKILLS_DIR.iterdir():
        if not sdir.is_dir():
            continue
        skill_file = sdir / "SKILL.md"
        assert skill_file.exists(), f"Missing SKILL.md in {sdir.name}"
        content = skill_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert lines[0].strip() == "---", f"{sdir.name}/SKILL.md missing opening ---"

        # Check closing frontmatter
        has_closing = any(line.strip() == "---" for line in lines[1:20])
        assert has_closing, f"{sdir.name}/SKILL.md missing closing --- in frontmatter header"
        assert "name:" in content, f"{sdir.name}/SKILL.md missing 'name:'"
        assert "description:" in content, f"{sdir.name}/SKILL.md missing 'description:'"


def test_antigravity_subagent_registry() -> None:
    """Verify subagent registry contains all core harness roles with valid definitions."""
    registry_file = SUBAGENTS_DIR / "registry.json"
    assert registry_file.exists(), f"Missing {registry_file}"

    data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert data.get("schema") == "antigravity.subagents.registry.v1"
    agents = data.get("agents", [])
    assert len(agents) >= 13, f"Expected at least 13 agents, found {len(agents)}"

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
    assert len(skill_dirs) >= 150, f"Global skills count too low: {len(skill_dirs)}"

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


