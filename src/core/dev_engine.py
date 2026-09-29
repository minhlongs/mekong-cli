# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/dev_engine.py — Autonomous Fullstack Developer & Code Quality Suite.

Provides developer workspace diagnostics, static AST code auditing, module scaffolding,
pull request diff reviewing, and automated refactoring recommendations.

Pure Python standard library implementation with zero external dependencies.
"""

from __future__ import annotations

import ast
import datetime
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditSeverity(str, Enum):
    """Severity ratings for code audit issues."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AuditFinding:
    """Individual code quality or security audit finding."""

    file_path: str
    line_number: int
    severity: str
    code_pattern: str
    message: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    """Consolidated codebase audit report."""

    total_files_scanned: int
    quality_score: int
    grade: str
    findings: list[AuditFinding]
    high_count: int
    medium_count: int
    low_count: int
    scanned_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files_scanned": self.total_files_scanned,
            "quality_score": self.quality_score,
            "grade": self.grade,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "scanned_at": self.scanned_at,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ScaffoldResult:
    """Artifacts created during module scaffolding."""

    module_name: str
    module_type: str
    files_created: list[str]
    test_file_created: Optional[str]
    success: bool
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrReviewReport:
    """Pull request diff review analysis."""

    diff_summary: str
    status: str  # approved, changes_requested, neutral
    files_changed: int
    insertions: int
    deletions: int
    findings: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RefactorAdvice:
    """Refactoring suggestions for a specific module."""

    target_file: str
    total_lines: int
    complexity_risk: str  # low, moderate, high
    suggested_actions: list[str]
    anti_patterns_found: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeveloperStatus:
    """Fast developer environment snapshot."""

    active_branch: str
    uncommitted_files: int
    last_commit_hash: str
    last_commit_subject: str
    debt_markers: int
    python_version: str
    virtualenv: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DevEngine:
    """Autonomous fullstack engineering, code auditing, and scaffolding engine."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path(os.getcwd())

    def _run_git(self, args: list[str]) -> str:
        """Run a git command in the project root."""
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            return res.stdout.strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Developer Environment Status
    # -------------------------------------------------------------------------
    def get_status(self) -> DeveloperStatus:
        """Collect current developer environment state."""
        branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
        status_raw = self._run_git(["status", "--porcelain"])
        uncommitted = len([line for line in status_raw.splitlines() if line.strip()])

        last_hash = self._run_git(["log", "-1", "--format=%h"]) or "none"
        last_subject = self._run_git(["log", "-1", "--format=%s"]) or "none"

        # Count debt markers across python files
        debt_count = 0
        py_files = list(self.project_root.rglob("*.py"))[:100]
        debt_regex = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
        for p in py_files:
            if any(part in p.parts for part in (".venv", "venv", ".git", ".pytest_cache", "build", "dist")):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                debt_count += len(debt_regex.findall(content))
            except Exception:
                pass

        venv_name = os.environ.get("VIRTUAL_ENV", "")
        if venv_name:
            venv_name = Path(venv_name).name
        else:
            venv_name = "system"

        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        return DeveloperStatus(
            active_branch=branch,
            uncommitted_files=uncommitted,
            last_commit_hash=last_hash,
            last_commit_subject=last_subject,
            debt_markers=debt_count,
            python_version=py_ver,
            virtualenv=venv_name,
        )

    # -------------------------------------------------------------------------
    # Codebase Audit
    # -------------------------------------------------------------------------
    def audit_codebase(
        self,
        target_path: Optional[str | Path] = None,
        max_files: int = 150,
    ) -> AuditReport:
        """Perform static AST and pattern audit across target path."""
        scan_dir = Path(target_path) if target_path else self.project_root
        if not scan_dir.is_absolute():
            scan_dir = self.project_root / scan_dir

        findings: list[AuditFinding] = []
        files_scanned = 0

        # Disallowed skip directories
        skip_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build", ".archive"}

        py_files: list[Path] = []
        if scan_dir.is_file() and scan_dir.suffix == ".py":
            py_files = [scan_dir]
        elif scan_dir.is_dir():
            for root, dirs, files in os.walk(str(scan_dir)):
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                for f in files:
                    if f.endswith(".py"):
                        py_files.append(Path(root) / f)
                        if len(py_files) >= max_files:
                            break
                if len(py_files) >= max_files:
                    break

        files_scanned = len(py_files)

        secret_regex = re.compile(
            r"""(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|bearer[_-]?token)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]"""
        )
        bare_except_regex = re.compile(r"""^\s*except\s*:""")

        for file_path in py_files:
            rel_path = str(file_path.relative_to(self.project_root)) if str(file_path).startswith(str(self.project_root)) else str(file_path)
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
            except Exception:
                continue

            # AST Analysis
            try:
                tree = ast.parse(content, filename=str(file_path))
                for node in ast.walk(tree):
                    # Check for eval / exec
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                            findings.append(
                                AuditFinding(
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    severity=AuditSeverity.HIGH.value,
                                    code_pattern=f"{node.func.id}(...)",
                                    message=f"Dynamic code execution via '{node.func.id}' presents critical injection risks.",
                                    recommendation="Refactor using static dispatch tables or ast.literal_eval.",
                                )
                            )
                        # Check subprocess shell=True
                        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen", "call"):
                            for kw in node.keywords:
                                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    findings.append(
                                        AuditFinding(
                                            file_path=rel_path,
                                            line_number=node.lineno,
                                            severity=AuditSeverity.HIGH.value,
                                            code_pattern="subprocess(..., shell=True)",
                                            message="Shell execution enabled with shell=True vulnerable to command injection.",
                                            recommendation="Pass arguments as a list with shell=False.",
                                        )
                                    )
                    # Check function length
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        end_lineno = getattr(node, "end_lineno", node.lineno)
                        if end_lineno - node.lineno > 120:
                            findings.append(
                                AuditFinding(
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    severity=AuditSeverity.LOW.value,
                                    code_pattern=f"def {node.name}() > 120 lines",
                                    message=f"Function '{node.name}' is {end_lineno - node.lineno} lines long.",
                                    recommendation="Decompose into cohesive helper functions.",
                                )
                            )
            except SyntaxError:
                pass

            # Pattern Analysis
            for idx, line in enumerate(lines, 1):
                # Bare except
                if bare_except_regex.search(line):
                    findings.append(
                        AuditFinding(
                            file_path=rel_path,
                            line_number=idx,
                            severity=AuditSeverity.MEDIUM.value,
                            code_pattern="bare except:",
                            message="Bare except clause catches SystemExit and KeyboardInterrupt.",
                            recommendation="Catch specific exceptions or 'except Exception:'.",
                        )
                    )
                # Hardcoded secrets
                if secret_regex.search(line):
                    findings.append(
                        AuditFinding(
                            file_path=rel_path,
                            line_number=idx,
                            severity=AuditSeverity.HIGH.value,
                            code_pattern="api_key = '...' / secret = '...'",
                            message="Possible hardcoded secret or authentication token detected.",
                            recommendation="Load secrets from environment variables or a secrets manager.",
                        )
                    )

        high_count = sum(1 for f in findings if f.severity == AuditSeverity.HIGH.value)
        medium_count = sum(1 for f in findings if f.severity == AuditSeverity.MEDIUM.value)
        low_count = sum(1 for f in findings if f.severity == AuditSeverity.LOW.value)

        # Calculate composite score
        penalty = (high_count * 15) + (medium_count * 5) + (low_count * 1)
        score = max(0, min(100, 100 - penalty))

        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        else:
            grade = "D"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return AuditReport(
            total_files_scanned=files_scanned,
            quality_score=score,
            grade=grade,
            findings=findings,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            scanned_at=now_str,
        )

    # -------------------------------------------------------------------------
    # Module Scaffolding
    # -------------------------------------------------------------------------
    def scaffold_module(
        self,
        name: str,
        module_type: str = "service",
        target_dir: Optional[str | Path] = None,
        with_test: bool = True,
        dry_run: bool = False,
    ) -> ScaffoldResult:
        """Scaffold a new structured Python module with type annotations and tests."""
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower()).strip("_")
        if not clean_name:
            clean_name = "sample_module"

        mtype = module_type.lower()
        if mtype not in ("service", "api", "agent", "util"):
            mtype = "service"

        class_name = "".join(word.capitalize() for word in clean_name.split("_"))

        # Determine target paths
        if target_dir:
            base_dir = Path(target_dir) if Path(target_dir).is_absolute() else self.project_root / target_dir
        else:
            if mtype == "service":
                base_dir = self.project_root / "src" / "services"
            elif mtype == "api":
                base_dir = self.project_root / "src" / "api"
            elif mtype == "agent":
                base_dir = self.project_root / "src" / "agents"
            else:
                base_dir = self.project_root / "src" / "utils"

        src_file = base_dir / f"{clean_name}.py"
        test_file = self.project_root / "tests" / f"test_{clean_name}_{mtype}.py"

        # Generate module content
        src_content = (
            f"# Mekong CLI — AI-Powered Business Operations for Vietnam\n"
            f"# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.\n\n"
            f'"""\n{clean_name}.py — {mtype.capitalize()} component for {class_name}.\n"""\n\n'
            f"from __future__ import annotations\n\n"
            f"import logging\n"
            f"from typing import Any, Optional\n\n"
            f"logger = logging.getLogger(__name__)\n\n\n"
            f"class {class_name}{mtype.capitalize()}:\n"
            f'    """Primary {mtype} implementation for {class_name}."""\n\n'
            f"    def __init__(self, name: str = \"{clean_name}\") -> None:\n"
            f"        self.name = name\n"
            f"        self.is_active = True\n\n"
            f"    def execute(self, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:\n"
            f'        """Execute {clean_name} operation."""\n'
            f"        logger.info(\"Executing {class_name} with payload: %s\", payload)\n"
            f"        return {{\n"
            f"            \"ok\": True,\n"
            f"            \"module\": self.name,\n"
            f"            \"status\": \"executed\",\n"
            f"            \"payload\": payload or {{}},\n"
            f"        }}\n"
        )

        test_content = (
            f"# Mekong CLI — AI-Powered Business Operations for Vietnam\n"
            f"# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.\n\n"
            f'"""Tests for {clean_name} {mtype}."""\n\n'
            f"from __future__ import annotations\n\n"
            f"import pytest\n\n\n"
            f"def test_{clean_name}_initialization() -> None:\n"
            f"    # Replace import path as appropriate\n"
            f"    assert True\n"
        )

        files_created: list[str] = []
        test_created: Optional[str] = None

        if not dry_run:
            base_dir.mkdir(parents=True, exist_ok=True)
            src_file.write_text(src_content, encoding="utf-8")
            files_created.append(str(src_file))

            if with_test:
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text(test_content, encoding="utf-8")
                test_created = str(test_file)
                files_created.append(str(test_file))
        else:
            files_created.append(str(src_file) + " (dry-run)")
            if with_test:
                test_created = str(test_file) + " (dry-run)"
                files_created.append(str(test_file) + " (dry-run)")

        return ScaffoldResult(
            module_name=clean_name,
            module_type=mtype,
            files_created=files_created,
            test_file_created=test_created,
            success=True,
            summary=f"Scaffolded {mtype} component '{class_name}' with {len(files_created)} files.",
        )

    # -------------------------------------------------------------------------
    # Pull Request Diff Review
    # -------------------------------------------------------------------------
    def review_diff(self, diff_text: Optional[str] = None) -> PrReviewReport:
        """Inspect and review git diff for hazards and quality."""
        raw_diff = diff_text if diff_text is not None else self._run_git(["diff", "HEAD"])
        if not raw_diff:
            # Check uncommitted cached diff
            raw_diff = self._run_git(["diff", "--cached"])

        if not raw_diff.strip():
            return PrReviewReport(
                diff_summary="No changes detected in working tree.",
                status="neutral",
                files_changed=0,
                insertions=0,
                deletions=0,
                findings=[],
                recommendations=["Working tree is clean. Ready to create pull request."],
            )

        files_changed = 0
        insertions = 0
        deletions = 0
        findings: list[str] = []
        recommendations: list[str] = []

        lines = raw_diff.splitlines()
        for line in lines:
            if line.startswith("diff --git"):
                files_changed += 1
            elif line.startswith("+") and not line.startswith("+++"):
                insertions += 1
                if "eval(" in line or "exec(" in line:
                    findings.append("Added dynamic code execution (eval/exec)")
                if "print(" in line and "src/cli" not in raw_diff:
                    findings.append("Added stdout print statement in non-CLI module")
                if "TODO" in line or "FIXME" in line:
                    findings.append("Added unresolved technical debt marker (TODO/FIXME)")
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        if not findings:
            status = "approved"
            recommendations.append("Changes look clean and comply with coding standards.")
        else:
            status = "changes_requested"
            recommendations.append("Address the identified findings before merging.")

        summary = f"{files_changed} files changed, +{insertions} insertions, -{deletions} deletions."

        return PrReviewReport(
            diff_summary=summary,
            status=status,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            findings=findings,
            recommendations=recommendations,
        )

    # -------------------------------------------------------------------------
    # Refactoring Analysis
    # -------------------------------------------------------------------------
    def analyze_refactor(self, target_file: str | Path) -> RefactorAdvice:
        """Analyze a specific Python file and generate refactoring suggestions."""
        file_path = Path(target_file) if Path(target_file).is_absolute() else self.project_root / target_file
        if not file_path.exists():
            return RefactorAdvice(
                target_file=str(target_file),
                total_lines=0,
                complexity_risk="low",
                suggested_actions=["File does not exist."],
                anti_patterns_found=[],
            )

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        total_lines = len(lines)

        anti_patterns: list[str] = []
        actions: list[str] = []

        if total_lines > 500:
            anti_patterns.append("File exceeds 500 lines (God Object candidate)")
            actions.append("Decompose classes and extract secondary helper routines into separate modules.")

        try:
            tree = ast.parse(content)
            func_count = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_count += 1
                    end_lineno = getattr(node, "end_lineno", node.lineno)
                    if end_lineno - node.lineno > 80:
                        anti_patterns.append(f"Function '{node.name}' exceeds 80 lines")
                        actions.append(f"Extract sub-tasks from '{node.name}' into smaller private methods.")
            if func_count > 15:
                anti_patterns.append(f"High method count ({func_count} functions)")
                actions.append("Split domain logic into specialized service classes.")
        except SyntaxError:
            anti_patterns.append("Syntax error detected during AST parsing")

        if len(anti_patterns) >= 3:
            risk = "high"
        elif len(anti_patterns) >= 1:
            risk = "moderate"
        else:
            risk = "low"
            actions.append("Module structure is concise and conforms to single-responsibility guidelines.")

        return RefactorAdvice(
            target_file=str(file_path.relative_to(self.project_root) if str(file_path).startswith(str(self.project_root)) else file_path),
            total_lines=total_lines,
            complexity_risk=risk,
            suggested_actions=actions,
            anti_patterns_found=anti_patterns,
        )


def get_dev_engine(project_root: str | Path | None = None) -> DevEngine:
    """Factory helper returning DevEngine instance."""
    return DevEngine(project_root=project_root)
