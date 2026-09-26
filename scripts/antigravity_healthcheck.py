#!/usr/bin/env python3
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Antigravity integration health check — CI-ready verification.

Run:  python3 scripts/antigravity_healthcheck.py
Exit: 0 = healthy, 1 = critical failure, 2 = warnings only

Checks:
1. Mekong binary available on PATH
2. All SKILL.md files have valid YAML frontmatter
3. Key commands resolve via mekong <cmd> --help
4. Global and local skill counts match
5. Sync verification passes
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"
GLOBAL_SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"

KEY_COMMANDS = [
    "cook", "cook-auto", "cook-auto-parallel",
    "bootstrap-auto", "bootstrap-auto-parallel", "bootstrap-auto-fast",
    "goal", "g",
    "binh-phap", "idea",
    "ke-toan", "thue", "zalo-oa",
    "plan", "deploy", "code", "spec",
    "doctor", "version",
]


class HealthReport:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.failures: list[str] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    @property
    def exit_code(self) -> int:
        if self.failures:
            return 1
        if self.warnings:
            return 2
        return 0

    def print_summary(self) -> None:
        total = len(self.passed) + len(self.warnings) + len(self.failures)
        print(f"\n{'=' * 60}")
        print(f"Antigravity Health Check — {total} checks")
        print(f"{'=' * 60}")
        print(f"  ✅ Passed:   {len(self.passed)}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print(f"  ❌ Failures: {len(self.failures)}")

        if self.warnings:
            print(f"\nWarnings:")
            for w in self.warnings:
                print(f"  ⚠️  {w}")

        if self.failures:
            print(f"\nFailures:")
            for f in self.failures:
                print(f"  ❌ {f}")

        status = "HEALTHY" if self.exit_code == 0 else ("DEGRADED" if self.exit_code == 2 else "UNHEALTHY")
        print(f"\nStatus: {status} (exit {self.exit_code})")


def check_mekong_binary(report: HealthReport) -> str | None:
    """Check that mekong binary is available on PATH."""
    mekong = shutil.which("mekong")
    if mekong:
        report.ok(f"mekong binary found at {mekong}")
        return mekong
    else:
        report.fail("mekong binary not found on PATH")
        return None


def check_skill_frontmatter(report: HealthReport) -> None:
    """Validate all SKILL.md files have valid YAML frontmatter."""
    if not SKILLS_DIR.exists():
        report.fail(f"Skills directory missing: {SKILLS_DIR}")
        return

    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    report.ok(f"Found {len(skill_dirs)} skill directories")

    if len(skill_dirs) < 150:
        report.fail(f"Expected at least 150 skills, found {len(skill_dirs)}")
    else:
        report.ok(f"Skill count ≥ 150 threshold")

    bad_frontmatter = []
    for sdir in skill_dirs:
        skill_file = sdir / "SKILL.md"
        if not skill_file.exists():
            bad_frontmatter.append(f"{sdir.name}: missing SKILL.md")
            continue
        content = skill_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            bad_frontmatter.append(f"{sdir.name}: missing opening ---")
            continue
        has_closing = any(line.strip() == "---" for line in lines[1:20])
        if not has_closing:
            bad_frontmatter.append(f"{sdir.name}: missing closing ---")
            continue
        if "name:" not in content:
            bad_frontmatter.append(f"{sdir.name}: missing name:")
            continue
        if "description:" not in content:
            bad_frontmatter.append(f"{sdir.name}: missing description:")

    if bad_frontmatter:
        for msg in bad_frontmatter:
            report.warn(f"Frontmatter issue: {msg}")
    else:
        report.ok("All SKILL.md files have valid frontmatter")


def check_key_commands(report: HealthReport, mekong_bin: str | None) -> None:
    """Test that key commands resolve correctly."""
    if not mekong_bin:
        report.fail("Skipping command checks — no mekong binary")
        return

    for cmd in KEY_COMMANDS:
        try:
            result = subprocess.run(
                [mekong_bin, cmd, "--help"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                report.ok(f"mekong {cmd} --help → exit 0")
            else:
                report.fail(f"mekong {cmd} --help → exit {result.returncode}")
        except subprocess.TimeoutExpired:
            report.warn(f"mekong {cmd} --help → timeout")
        except Exception as e:
            report.fail(f"mekong {cmd} --help → {e}")


def check_global_sync(report: HealthReport) -> None:
    """Verify global and local skill directories are in sync."""
    if not GLOBAL_SKILLS_DIR.exists():
        report.warn(f"Global skills directory missing: {GLOBAL_SKILLS_DIR}")
        return

    local_count = len([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    global_count = len([d for d in GLOBAL_SKILLS_DIR.iterdir() if d.is_dir()])

    if local_count == global_count:
        report.ok(f"Local ({local_count}) and global ({global_count}) skill counts match")
    else:
        report.warn(f"Skill count mismatch: local={local_count} global={global_count}")


def check_sync_verify(report: HealthReport) -> None:
    """Run sync_antigravity.py --verify."""
    verify_script = PROJECT_ROOT / "scripts" / "sync_antigravity.py"
    if not verify_script.exists():
        report.warn("sync_antigravity.py not found")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(verify_script), "--verify"],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0 and "Verification passed" in result.stdout:
            report.ok("sync_antigravity.py --verify passed")
        else:
            report.fail(f"sync_antigravity.py --verify failed: {result.stderr[:200]}")
    except Exception as e:
        report.fail(f"sync_antigravity.py --verify error: {e}")


def main() -> int:
    report = HealthReport()

    mekong_bin = check_mekong_binary(report)
    check_skill_frontmatter(report)
    check_key_commands(report, mekong_bin)
    check_global_sync(report)
    check_sync_verify(report)

    report.print_summary()
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
