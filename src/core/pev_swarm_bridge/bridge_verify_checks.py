"""Verification criteria evaluation helpers for PEVSwarmBridge."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from .models import VerificationCriteria


def evaluate_verification_criteria(
    criteria: VerificationCriteria,
    project_root: Path,
    dry_run: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Run file-existence, test-command, and rubric checks for a task."""
    checks: dict[str, Any] = {}
    all_passed = True

    for req_file in criteria.file_exists:
        p = (project_root / req_file).resolve()
        exists = p.exists()
        checks[f"file_exists:{req_file}"] = {
            "expected": True,
            "actual": exists,
            "passed": exists,
        }
        if not exists:
            all_passed = False

    if criteria.test_command and not dry_run:
        try:
            cmd_res = subprocess.run(
                criteria.test_command,
                shell=True,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            cmd_passed = True
            if criteria.exit_code is not None and cmd_res.returncode != criteria.exit_code:
                cmd_passed = False

            for sub in criteria.output_contains:
                if sub not in cmd_res.stdout and sub not in cmd_res.stderr:
                    cmd_passed = False

            for neg in criteria.output_not_contains:
                if neg in cmd_res.stdout or neg in cmd_res.stderr:
                    cmd_passed = False

            checks["test_command"] = {
                "command": criteria.test_command,
                "exit_code": cmd_res.returncode,
                "expected_exit_code": criteria.exit_code,
                "passed": cmd_passed,
                "stdout_tail": cmd_res.stdout[-500:],
                "stderr_tail": cmd_res.stderr[-500:],
            }
            if not cmd_passed:
                all_passed = False
        except Exception as exc:
            checks["test_command"] = {
                "command": criteria.test_command,
                "passed": False,
                "error": str(exc),
            }
            all_passed = False
    elif criteria.test_command and dry_run:
        checks["test_command"] = {
            "command": criteria.test_command,
            "passed": True,
            "dry_run": True,
        }

    if criteria.rubric_prompt:
        checks["rubric"] = {
            "prompt": criteria.rubric_prompt,
            "passed": True,
        }

    return checks, all_passed
