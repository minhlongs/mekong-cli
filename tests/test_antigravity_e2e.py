# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""End-to-end Antigravity integration tests.

Validates the complete integration surface:
- Fresh project scaffolding
- Skill frontmatter conformance
- Global/local skill parity
- Key command execution
- Health check script
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"
GLOBAL_SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"

KEY_SKILLS = [
    "cook", "plan", "goal", "g", "bootstrap-auto-parallel",
    "binh-phap", "ke-toan", "thue", "zalo-oa", "ship",
    "daily", "dev", "idea", "bootstrap-auto", "bootstrap-auto-fast",
    "cto", "sales", "marketing", "ops",
]


def test_fresh_project_scaffolding(tmp_path) -> None:
    """Scaffold a brand new project and verify all key skills land correctly."""
    target = tmp_path / "fresh_project"
    result = subprocess.run(
        [sys.executable, "scripts/sync_antigravity.py", "--target", str(target)],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"Scaffolding failed: {result.stderr}"

    skills_dir = target / ".agents" / "skills"
    assert skills_dir.exists(), "Skills directory not created in target"

    for skill_name in KEY_SKILLS:
        skill_file = skills_dir / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Key skill missing in scaffold: {skill_name}"
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name} missing frontmatter"
        assert f"name: {skill_name}" in content, f"{skill_name} missing name in frontmatter"

    assert (target / ".agents" / "subagents" / "registry.json").exists()
    assert (target / "GEMINI.md").exists()


def test_global_skills_match_local() -> None:
    """Verify global skills at ~/.gemini/config/skills/ match local .agents/skills/."""
    assert GLOBAL_SKILLS_DIR.exists(), f"Global skills dir missing: {GLOBAL_SKILLS_DIR}"

    local_skills = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}
    global_skills = {d.name for d in GLOBAL_SKILLS_DIR.iterdir() if d.is_dir()}

    assert len(local_skills) == len(global_skills), (
        f"Skill count mismatch: local={len(local_skills)} global={len(global_skills)}"
    )

    for skill_name in KEY_SKILLS:
        assert skill_name in local_skills, f"Key skill missing locally: {skill_name}"
        assert skill_name in global_skills, f"Key skill missing globally: {skill_name}"


def test_all_key_skills_have_valid_frontmatter() -> None:
    """Verify every key skill has valid YAML frontmatter with name and description."""
    for skill_name in KEY_SKILLS:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing {skill_name}/SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert lines[0].strip() == "---", f"{skill_name}: missing opening ---"
        assert any(
            line.strip() == "---" for line in lines[1:20]
        ), f"{skill_name}: missing closing ---"
        assert f"name: {skill_name}" in content, f"{skill_name}: wrong name in frontmatter"
        assert "description:" in content, f"{skill_name}: missing description"


def test_all_skills_use_mekong_binary() -> None:
    """Verify no skill uses repo-relative python3 -m src.main invocation."""
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        content = skill_file.read_text(encoding="utf-8")
        assert "python3 -m src.main" not in content, (
            f"{skill_dir.name}/SKILL.md uses repo-relative invocation instead of mekong binary"
        )


def test_no_generic_descriptions_in_key_skills() -> None:
    """Verify key skills don't have auto-generated placeholder descriptions."""
    generic_pattern = re.compile(r"Execute Mekong CLI .* workflow\.")
    for skill_name in KEY_SKILLS:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        # Extract description from frontmatter
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("description:"):
                desc_val = line[len("description:"):].strip()
                if desc_val in (">-", "|"):
                    # Multi-line: grab next line
                    if i + 1 < len(lines):
                        desc_val = lines[i + 1].strip()
                assert not generic_pattern.match(desc_val), (
                    f"{skill_name} has generic auto-generated description: {desc_val}"
                )
                break


@pytest.mark.skipif(
    not shutil.which("mekong"),
    reason="mekong binary not on PATH",
)
def test_key_commands_resolve_via_cli() -> None:
    """Verify key CLI commands resolve with exit 0 via mekong --help."""
    mekong_bin = shutil.which("mekong")
    commands_to_check = [
        "cook", "cook-auto", "cook-auto-parallel",
        "bootstrap-auto", "bootstrap-auto-parallel",
        "goal", "g", "binh-phap", "idea",
        "ke-toan", "thue", "zalo-oa",
    ]
    for cmd in commands_to_check:
        result = subprocess.run(
            [mekong_bin, cmd, "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"mekong {cmd} --help failed with exit {result.returncode}: {result.stderr[:200]}"
        )


@pytest.mark.skipif(
    not shutil.which("mekong"),
    reason="mekong binary not on PATH",
)
def test_key_commands_from_outside_repo() -> None:
    """Verify key commands work from /tmp (outside the repo)."""
    mekong_bin = shutil.which("mekong")
    for cmd in ["bootstrap-auto-parallel", "g", "cook"]:
        result = subprocess.run(
            [mekong_bin, cmd, "--help"],
            capture_output=True, text=True, timeout=10,
            cwd="/tmp",
        )
        assert result.returncode == 0, (
            f"mekong {cmd} --help failed from /tmp: exit {result.returncode}"
        )


def test_healthcheck_script_exists() -> None:
    """Verify the healthcheck script is present and importable."""
    healthcheck = PROJECT_ROOT / "scripts" / "antigravity_healthcheck.py"
    assert healthcheck.exists(), "Missing scripts/antigravity_healthcheck.py"


def test_sync_verify_passes() -> None:
    """Verify sync_antigravity.py --verify still passes."""
    result = subprocess.run(
        [sys.executable, "scripts/sync_antigravity.py", "--verify"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"sync --verify failed: {result.stderr}"
    assert "Verification passed" in result.stdout
