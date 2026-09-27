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
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"
GLOBAL_SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"

KEY_SKILLS = [
    "cook", "plan", "goal", "g", "bootstrap-auto-parallel",
    "binh-phap", "ke-toan", "thue", "zalo-oa", "ship",
    "daily", "dev", "idea", "bootstrap-auto", "bootstrap-auto-fast",
    "cto", "sales", "marketing", "ops",
    "agent", "cfo", "cmo", "doctor", "version", "deploy", "build", "spec", "bmad",
    "implement", "tasks-sdd", "context-engineering", "tech-graph",
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
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"{skill_name}: missing frontmatter delimiters"
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict), f"{skill_name}: frontmatter did not parse as dictionary"
        assert fm.get("name") == skill_name, f"{skill_name}: wrong name in frontmatter"
        desc = str(fm.get("description", "")).strip()
        assert desc not in (">-", "|", ">", "|-", ""), f"{skill_name}: description is raw scalar marker: {desc}"
        assert not desc.startswith(">-"), f"{skill_name}: description starts with scalar marker: {desc}"
        assert len(desc) >= 10, f"{skill_name}: description too short ({len(desc)}): {desc}"


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
    generic_patterns = [
        re.compile(r"^Mekong CLI \S+ command\.*$", re.IGNORECASE),
        re.compile(r"^Execute Mekong CLI .* workflow\.*$", re.IGNORECASE),
        re.compile(r"^Run Mekong .*workflow command\.*$", re.IGNORECASE),
    ]
    for skill_name in KEY_SKILLS:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"{skill_name}: missing frontmatter delimiters"
        fm = yaml.safe_load(parts[1])
        assert isinstance(fm, dict), f"{skill_name}: frontmatter not a dict"
        desc_val = str(fm.get("description", "")).strip()
        assert desc_val not in (">-", "|", ">", "|-", ""), f"{skill_name}: raw scalar marker: {desc_val}"
        assert not desc_val.startswith(">-"), f"{skill_name}: corrupted marker: {desc_val}"
        assert len(desc_val) >= 10, f"{skill_name}: description too short ({len(desc_val)}): {desc_val}"
        assert not any(p.match(desc_val) for p in generic_patterns), (
            f"{skill_name} has generic auto-generated description: {desc_val}"
        )


def test_all_skills_across_destinations_description_invariants() -> None:
    """Verify 100% of skills in local and global destinations satisfy description invariants."""
    raw_block_markers = {">-", "|", ">", "|-", "'-'", "''", '""'}
    generic_patterns = [
        re.compile(r"^Mekong CLI \S+ command\.*$", re.IGNORECASE),
        re.compile(r"^Execute Mekong CLI .* workflow\.*$", re.IGNORECASE),
        re.compile(r"^Run Mekong .*workflow command\.*$", re.IGNORECASE),
    ]

    destinations = [SKILLS_DIR]
    if GLOBAL_SKILLS_DIR.exists():
        destinations.append(GLOBAL_SKILLS_DIR)

    for dest in destinations:
        for sdir in dest.iterdir():
            if not sdir.is_dir():
                continue
            skill_file = sdir / "SKILL.md"
            if not skill_file.exists():
                continue
            parts = skill_file.read_text(encoding="utf-8").split("---", 2)
            assert len(parts) >= 3, f"{dest.name}/{sdir.name}: missing frontmatter"
            fm = yaml.safe_load(parts[1])
            desc = str(fm.get("description", "")).strip()
            assert desc not in raw_block_markers and not desc.startswith(">-"), (
                f"{dest.name}/{sdir.name}: corrupted marker: {desc}"
            )
            assert len(desc) >= 10, (
                f"{dest.name}/{sdir.name}: description too short ({len(desc)}): {desc}"
            )
            assert not any(p.match(desc) for p in generic_patterns), (
                f"{dest.name}/{sdir.name}: generic description: {desc}"
            )


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
        "agent", "cfo", "cmo", "doctor", "version", "deploy", "build", "spec", "bmad",
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
