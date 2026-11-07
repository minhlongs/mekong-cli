# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Regression tests for scripts/shell-init.sh path integrity and shell sourcing."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHELL_INIT = REPO_ROOT / "scripts" / "shell-init.sh"


def _extract_mekong_root_targets(script_text: str) -> list[tuple[int, str]]:
    """Extract (line_number, relative_path) for every non-comment $MEKONG_ROOT/<path> reference."""
    targets: list[tuple[int, str]] = []
    pattern = re.compile(r"\$\{?MEKONG_ROOT\}?/([A-Za-z0-9_./-]+)")

    for lineno, raw_line in enumerate(script_text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for match in pattern.finditer(raw_line):
            rel_path = match.group(1).rstrip("/")
            targets.append((lineno, rel_path))
    return targets


class TestShellInitScript:
    """Verify scripts/shell-init.sh syntax, referenced paths, and clean sourcing."""

    def test_shell_init_syntax_valid(self) -> None:
        """bash -n must accept scripts/shell-init.sh with zero syntax errors."""
        res = subprocess.run(
            ["bash", "-n", str(SHELL_INIT)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, f"bash -n failed: {res.stderr}"

    def test_all_referenced_mekong_root_paths_exist(self) -> None:
        """Every $MEKONG_ROOT/<path> referenced in active lines of shell-init.sh must exist."""
        script_text = SHELL_INIT.read_text(encoding="utf-8")
        targets = _extract_mekong_root_targets(script_text)
        assert len(targets) >= 4, "Expected active $MEKONG_ROOT/<path> references in shell-init.sh"

        missing = [
            f"line {lineno}: $MEKONG_ROOT/{rel_path}"
            for lineno, rel_path in targets
            if not (REPO_ROOT / rel_path).exists()
        ]
        assert missing == [], f"Dead paths in scripts/shell-init.sh: {missing}"

    def test_shell_init_sources_cleanly(self) -> None:
        """Sourcing scripts/shell-init.sh in bash must exit 0 and print the loaded banner."""
        env = os.environ.copy()
        env["MEKONG_ROOT"] = str(REPO_ROOT)
        res = subprocess.run(
            ["bash", "-c", f'source "{SHELL_INIT}"'],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert res.returncode == 0, f"Sourcing shell-init.sh failed: {res.stderr}"
        assert "Mekong CLI loaded." in res.stdout
        assert "Dual CLI: 'mk' (Mekong) | 'ak' (Agent Kit)" in res.stdout
