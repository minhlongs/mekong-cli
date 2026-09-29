# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/shipping_engine.py — Autonomous Production Shipping Engine.

Coordinates the canonical shipping pipeline:
Pre-flight checks -> Linting -> Testing -> Staging -> Commit synthesis -> Remote push.
Pure Python standard library with zero external dependencies.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ShipPhase(str, Enum):
    PREFLIGHT = "preflight"
    VALIDATION = "validation"
    STAGING = "staging"
    COMMIT = "commit"
    PUSH = "push"
    COMPLETE = "complete"


@dataclass
class ValidationStep:
    """Outcome of a single validation command (linter, type checker, or test)."""

    name: str
    command: list[str]
    passed: bool
    duration_ms: float
    output: str
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": " ".join(self.command),
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "skipped": self.skipped,
        }


@dataclass
class ShippingReport:
    """Structured report produced by the shipping pipeline."""

    ok: bool
    phase: ShipPhase
    branch: str
    commit_sha: str
    commit_message: str
    remote_url: str
    pushed: bool
    files_staged: list[str]
    validations: list[ValidationStep] = field(default_factory=list)
    error: Optional[str] = None
    dry_run: bool = False
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "phase": self.phase.value,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "commit_message": self.commit_message,
            "remote_url": self.remote_url,
            "pushed": self.pushed,
            "files_staged": self.files_staged,
            "validations": [v.to_dict() for v in self.validations],
            "error": self.error,
            "dry_run": self.dry_run,
            "duration_ms": self.duration_ms,
        }


class ShippingEngine:
    """Core autonomous production shipping pipeline coordinator."""

    def __init__(self, repo_dir: str | Path | None = None) -> None:
        self.repo_dir = Path(repo_dir or os.getcwd()).resolve()

    def _run_cmd(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        timeout: int = 120,
    ) -> tuple[int, str, str, float]:
        """Execute a shell command returning (code, stdout, stderr, duration_ms)."""
        target_cwd = cwd or self.repo_dir
        start = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return res.returncode, res.stdout.strip(), res.stderr.strip(), duration_ms
        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return 124, "", f"Command timed out after {timeout}s", duration_ms
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return 1, "", str(exc), duration_ms

    def preflight_check(self) -> dict[str, Any]:
        """Inspect repository topology, remote URL, branch, and staged/dirty files."""
        code, root_out, err, _ = self._run_cmd(["git", "rev-parse", "--show-toplevel"])
        if code != 0:
            return {
                "ok": False,
                "error": err or f"Not a git repository: {self.repo_dir}",
                "repo_path": str(self.repo_dir),
            }

        repo_root = Path(root_out).resolve()
        _, branch, _, _ = self._run_cmd(["git", "branch", "--show-current"], cwd=repo_root)
        _, remote_url, _, _ = self._run_cmd(["git", "remote", "get-url", "origin"], cwd=repo_root)
        _, status_out, _, _ = self._run_cmd(["git", "status", "--porcelain"], cwd=repo_root)

        dirty_files = [line.strip().split()[-1] for line in status_out.split("\n") if line.strip()]

        # Ahead/behind tracking if upstream exists
        ahead, behind = 0, 0
        code, ahead_behind, _, _ = self._run_cmd(
            ["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
            cwd=repo_root,
        )
        if code == 0 and ahead_behind and "\t" in ahead_behind:
            parts = ahead_behind.split("\t")
            try:
                behind, ahead = int(parts[0]), int(parts[1])
            except ValueError:
                pass

        return {
            "ok": True,
            "repo_path": str(repo_root),
            "branch": branch or "HEAD (detached)",
            "remote_url": remote_url or "none",
            "has_remote": bool(remote_url),
            "dirty": bool(dirty_files),
            "dirty_count": len(dirty_files),
            "dirty_files": dirty_files,
            "ahead": ahead,
            "behind": behind,
        }

    def run_validation(
        self,
        run_lint: bool = True,
        run_tests: bool = True,
        timeout: int = 120,
    ) -> list[ValidationStep]:
        """Execute project-specific linters and tests."""
        steps: list[ValidationStep] = []

        is_python = (self.repo_dir / "pyproject.toml").exists() or (self.repo_dir / "setup.py").exists()
        is_node = (self.repo_dir / "package.json").exists()

        # 1. Lint step
        if run_lint:
            if is_python:
                code, out, err, dur = self._run_cmd(["python3", "-m", "ruff", "check", "."], timeout=timeout)
                # If ruff is not installed or fails gracefully
                if code != 0 and "No module named ruff" in (err or out):
                    steps.append(ValidationStep(
                        name="ruff",
                        command=["python3", "-m", "ruff", "check", "."],
                        passed=True,
                        duration_ms=dur,
                        output="ruff not available (skipped)",
                        skipped=True,
                    ))
                else:
                    steps.append(ValidationStep(
                        name="ruff",
                        command=["python3", "-m", "ruff", "check", "."],
                        passed=(code == 0),
                        duration_ms=dur,
                        output=out or err or "All checks passed",
                    ))
            elif is_node:
                code, out, err, dur = self._run_cmd(["npm", "run", "lint"], timeout=timeout)
                steps.append(ValidationStep(
                    name="npm-lint",
                    command=["npm", "run", "lint"],
                    passed=(code == 0),
                    duration_ms=dur,
                    output=out or err,
                ))

        # 2. Test step
        if run_tests:
            if is_python:
                code, out, err, dur = self._run_cmd(["python3", "-m", "pytest", "-q", "--tb=short"], timeout=timeout)
                if code != 0 and "No module named pytest" in (err or out):
                    steps.append(ValidationStep(
                        name="pytest",
                        command=["python3", "-m", "pytest", "-q"],
                        passed=True,
                        duration_ms=dur,
                        output="pytest not available (skipped)",
                        skipped=True,
                    ))
                else:
                    steps.append(ValidationStep(
                        name="pytest",
                        command=["python3", "-m", "pytest", "-q", "--tb=short"],
                        passed=(code == 0),
                        duration_ms=dur,
                        output=out or err or "Tests passed",
                    ))
            elif is_node:
                code, out, err, dur = self._run_cmd(["npm", "test"], timeout=timeout)
                steps.append(ValidationStep(
                    name="npm-test",
                    command=["npm", "test"],
                    passed=(code == 0),
                    duration_ms=dur,
                    output=out or err,
                ))

        return steps

    def synthesize_commit_message(
        self,
        custom_message: str | None = None,
        staged_files: list[str] | None = None,
    ) -> str:
        """Synthesize a conventional commit message from custom message or staged files."""
        if custom_message and custom_message.strip():
            msg = custom_message.strip()
            # If already has conventional prefix (e.g. feat:, fix:, chore:), preserve it
            if re.match(r"^(feat|fix|docs|refactor|test|perf|chore|build|ci)(\([a-zA-Z0-9_-]+\))?:", msg):
                return msg
            # Otherwise auto-prefix based on content
            msg_lower = msg.lower()
            if any(k in msg_lower for k in ("fix", "bug", "patch", "error", "issue", "resolve")):
                prefix = "fix"
            elif any(k in msg_lower for k in ("refactor", "clean", "rewrite", "simplify")):
                prefix = "refactor"
            elif any(k in msg_lower for k in ("doc", "docs", "readme", "guide", "manual", "handbook")):
                prefix = "docs"
            elif any(k in msg_lower for k in ("test", "spec", "eval", "benchmark")):
                prefix = "test"
            elif any(k in msg_lower for k in ("perf", "speed", "latency", "optimize")):
                prefix = "perf"
            else:
                prefix = "feat"
            return f"{prefix}: {msg}"

        # Inspect staged or dirty files
        files = staged_files or []
        if not files:
            pre = self.preflight_check()
            files = pre.get("dirty_files", [])

        if not files:
            return "chore: update repository state"

        # Determine type from file extensions and names
        all_docs = all(f.endswith((".md", ".txt", ".rst")) or "doc" in f.lower() for f in files)
        if all_docs:
            return f"docs: update documentation ({', '.join(Path(f).name for f in files[:3])})"

        all_tests = all("test" in f.lower() or f.startswith("tests/") for f in files)
        if all_tests:
            return f"test: add and update tests ({', '.join(Path(f).name for f in files[:3])})"

        has_fix = any("fix" in f.lower() or "bug" in f.lower() or "patch" in f.lower() for f in files)
        prefix = "fix" if has_fix else "feat"
        sample_names = [Path(f).stem for f in files[:3]]
        return f"{prefix}: update {', '.join(sample_names)}"

    def ship(
        self,
        message: str | None = None,
        run_lint: bool = True,
        run_tests: bool = True,
        push: bool = True,
        dry_run: bool = False,
    ) -> ShippingReport:
        """Execute the end-to-end shipping pipeline."""
        start_time = time.perf_counter()

        # Step 0: Pre-flight check
        preflight = self.preflight_check()
        if not preflight.get("ok"):
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            return ShippingReport(
                ok=False,
                phase=ShipPhase.PREFLIGHT,
                branch="",
                commit_sha="",
                commit_message="",
                remote_url="",
                pushed=False,
                files_staged=[],
                error=preflight.get("error", "Preflight check failed"),
                dry_run=dry_run,
                duration_ms=duration,
            )

        branch = preflight["branch"]
        remote_url = preflight["remote_url"]
        dirty_files = preflight["dirty_files"]

        # Step 1: Validation
        validations: list[ValidationStep] = []
        if run_lint or run_tests:
            validations = self.run_validation(run_lint=run_lint, run_tests=run_tests)
            for v in validations:
                if not v.passed and not v.skipped:
                    duration = round((time.perf_counter() - start_time) * 1000, 2)
                    return ShippingReport(
                        ok=False,
                        phase=ShipPhase.VALIDATION,
                        branch=branch,
                        commit_sha="",
                        commit_message="",
                        remote_url=remote_url,
                        pushed=False,
                        files_staged=dirty_files,
                        validations=validations,
                        error=f"Validation step '{v.name}' failed: {v.output}",
                        dry_run=dry_run,
                        duration_ms=duration,
                    )

        # Synthesize commit message
        commit_msg = self.synthesize_commit_message(custom_message=message, staged_files=dirty_files)

        if dry_run:
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            return ShippingReport(
                ok=True,
                phase=ShipPhase.COMPLETE,
                branch=branch,
                commit_sha="DRY_RUN",
                commit_message=commit_msg,
                remote_url=remote_url,
                pushed=push and preflight["has_remote"],
                files_staged=dirty_files,
                validations=validations,
                dry_run=True,
                duration_ms=duration,
            )

        # Step 2: Staging & Commit
        if dirty_files:
            code, _, add_err, _ = self._run_cmd(["git", "add", "-A"])
            if code != 0:
                duration = round((time.perf_counter() - start_time) * 1000, 2)
                return ShippingReport(
                    ok=False,
                    phase=ShipPhase.STAGING,
                    branch=branch,
                    commit_sha="",
                    commit_message=commit_msg,
                    remote_url=remote_url,
                    pushed=False,
                    files_staged=dirty_files,
                    validations=validations,
                    error=f"Failed to stage files: {add_err}",
                    duration_ms=duration,
                )

            code, _, commit_err, _ = self._run_cmd(["git", "commit", "-m", commit_msg])
            if code != 0:
                duration = round((time.perf_counter() - start_time) * 1000, 2)
                return ShippingReport(
                    ok=False,
                    phase=ShipPhase.COMMIT,
                    branch=branch,
                    commit_sha="",
                    commit_message=commit_msg,
                    remote_url=remote_url,
                    pushed=False,
                    files_staged=dirty_files,
                    validations=validations,
                    error=f"Commit failed: {commit_err}",
                    duration_ms=duration,
                )

        # Get latest commit SHA
        _, head_sha, _, _ = self._run_cmd(["git", "rev-parse", "HEAD"])

        # Step 3: Remote Push
        pushed = False
        if push and preflight["has_remote"] and branch:
            push_cmd = ["git", "push", "origin", branch]
            code, _, push_err, _ = self._run_cmd(push_cmd)
            if code != 0:
                # If upstream is not set yet, try -u origin <branch>
                code, _, push_err, _ = self._run_cmd(["git", "push", "-u", "origin", branch])
                if code != 0:
                    duration = round((time.perf_counter() - start_time) * 1000, 2)
                    return ShippingReport(
                        ok=False,
                        phase=ShipPhase.PUSH,
                        branch=branch,
                        commit_sha=head_sha or "HEAD",
                        commit_message=commit_msg,
                        remote_url=remote_url,
                        pushed=False,
                        files_staged=dirty_files,
                        validations=validations,
                        error=f"Push failed: {push_err}",
                        duration_ms=duration,
                    )
            pushed = True

        duration = round((time.perf_counter() - start_time) * 1000, 2)
        return ShippingReport(
            ok=True,
            phase=ShipPhase.COMPLETE,
            branch=branch,
            commit_sha=head_sha or "HEAD",
            commit_message=commit_msg,
            remote_url=remote_url,
            pushed=pushed,
            files_staged=dirty_files,
            validations=validations,
            duration_ms=duration,
        )


_shipping_engine_instance: ShippingEngine | None = None


def get_shipping_engine(repo_dir: str | Path | None = None) -> ShippingEngine:
    """Return the ShippingEngine singleton instance."""
    global _shipping_engine_instance
    if _shipping_engine_instance is None or repo_dir is not None:
        _shipping_engine_instance = ShippingEngine(repo_dir=repo_dir)
    return _shipping_engine_instance


__all__ = [
    "ShipPhase",
    "ShippingEngine",
    "ShippingReport",
    "ValidationStep",
    "get_shipping_engine",
]
