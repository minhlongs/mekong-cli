# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/cto_engine.py — Autonomous CTO Engineering Architecture & Review Suite.

Provides senior engineering leadership intelligence for solo founders and autonomous swarms:
  1. Architecture Decision Records (ADR): Generate formal ADRs with context and consequences.
  2. Code & Security Review: Detect anti-patterns, security risks, and code smells.
  3. Engineering Scorecard: Compute composite health score (0-100) and grade (A+ to D).
  4. Stack Diagnostics & Health: Fast environment, runtime, dependency, and test verification.
  5. Technical Roadmap: 3-horizon technical roadmap (Now, Next, Later) for tech debt remediation.

Pure Python standard library implementation with zero external dependencies.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Finding severity level."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ADRRecord:
    """Architecture Decision Record."""

    number: int
    title: str
    status: str  # "Proposed", "Accepted", "Superseded", "Rejected"
    date: str
    context: str
    decision: str
    consequences: str
    alternatives: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        alt_section = "\n".join(f"- {a}" for a in self.alternatives) if self.alternatives else "- None recorded"
        return f"""# ADR-{self.number:03d}: {self.title}

- **Status:** {self.status}
- **Date:** {self.date}

## Context
{self.context}

## Decision
{self.decision}

## Consequences
{self.consequences}

## Alternatives Considered
{alt_section}
"""

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "status": self.status,
            "date": self.date,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "alternatives": self.alternatives,
        }


@dataclass
class CodeReviewFinding:
    """Individual code review finding or recommendation."""

    file: str
    line: int
    severity: Severity
    category: str  # "security", "maintainability", "reliability", "performance"
    rule_id: str
    message: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity.value,
            "category": self.category,
            "rule_id": self.rule_id,
            "message": self.message,
            "recommendation": self.recommendation,
        }


@dataclass
class CodeReviewReport:
    """Consolidated code review report."""

    ok: bool
    files_scanned: int
    total_findings: int
    severity_counts: dict[str, int]
    findings: list[CodeReviewFinding]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "files_scanned": self.files_scanned,
            "total_findings": self.total_findings,
            "severity_counts": self.severity_counts,
            "findings": [f.to_dict() for f in self.findings],
            "passed": self.passed,
        }


@dataclass
class EngineeringScorecard:
    """Composite engineering health scorecard."""

    ok: bool
    composite_score: int  # 0 to 100
    grade: str  # "A+", "A", "B", "C", "D"
    metrics: dict[str, Any]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "composite_score": self.composite_score,
            "grade": self.grade,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
        }


@dataclass
class CtoHealthReport:
    """CTO environment and stack diagnostics report."""

    ok: bool
    git_clean: bool
    uncommitted_files: int
    python_version: str
    virtualenv_active: bool
    test_runner_available: bool
    linter_available: bool
    repo_branch: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalRoadmap:
    """3-Horizon engineering technical roadmap."""

    ok: bool
    horizons: dict[str, list[str]]  # "now", "next", "later"
    total_initiatives: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "horizons": self.horizons,
            "total_initiatives": self.total_initiatives,
        }


class CTOEngine:
    """Core CTO engineering intelligence and architecture audit engine."""

    EXCLUDED_DIRS = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        ".archive",
    }

    SUPPORTED_EXTENSIONS = {".py", ".ts", ".js", ".go", ".rs", ".json", ".yaml", ".yml", ".md"}

    def __init__(self, repo_dir: str | Path | None = None) -> None:
        self.repo_dir = Path(repo_dir or os.getcwd()).resolve()

    def _run_git(self, args: list[str], timeout: int = 15) -> tuple[int, str, str]:
        try:
            p = subprocess.run(
                ["git"] + args,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        except Exception as exc:
            return 1, "", str(exc)

    # -------------------------------------------------------------------------
    # 1. Architecture Decision Records (ADR)
    # -------------------------------------------------------------------------
    def generate_adr(
        self,
        title: str,
        context: str = "",
        decision: str = "",
        consequences: str = "",
        alternatives: list[str] | None = None,
        export: bool = False,
    ) -> ADRRecord:
        """Create a structured Architecture Decision Record."""
        clean_title = (title or "").strip() or "Standard Architecture Decision"
        adr_dir = self.repo_dir / "reports" / "cto" / "architect"
        if not adr_dir.exists():
            adr_dir.mkdir(parents=True, exist_ok=True)

        existing_adrs = list(adr_dir.glob("ADR-*.md"))
        next_num = len(existing_adrs) + 1

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        ctx = (context or "").strip() or (
            f"The codebase requires a standardized architectural pattern for {clean_title} "
            "to ensure maintainability, testability, and adherence to the Mekong Solo Harness spec."
        )
        dec = (decision or "").strip() or (
            f"Adopt modular standard-library design with explicit boundary isolation for {clean_title}. "
            "Expose Typer CLI commands, native MCP tools, and deterministic test batteries."
        )
        csq = (consequences or "").strip() or (
            "Positive: Zero third-party vendor lock-in, reproducible test builds, and rapid agentic dispatch.\n"
            "Negative: Custom domain logic must be maintained internally."
        )
        alts = alternatives or [
            "Use third-party monolith framework (rejected due to dependency bloat)",
            "Manual ad-hoc implementation (rejected due to lack of verification)",
        ]

        record = ADRRecord(
            number=next_num,
            title=clean_title,
            status="Accepted",
            date=today_str,
            context=ctx,
            decision=dec,
            consequences=csq,
            alternatives=alts,
        )

        if export:
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", clean_title.lower()).strip("-")
            filename = f"ADR-{next_num:03d}-{slug}.md"
            target_path = adr_dir / filename
            target_path.write_text(record.to_markdown(), encoding="utf-8")

        return record

    # -------------------------------------------------------------------------
    # 2. Code Review & Security Audit
    # -------------------------------------------------------------------------
    def run_code_review(self, target_path: Optional[str] = None, max_findings: int = 50) -> CodeReviewReport:
        """Scan codebase files for anti-patterns, security risks, and code smells."""
        scan_root = (self.repo_dir / target_path).resolve() if target_path else self.repo_dir
        findings: list[CodeReviewFinding] = []
        files_scanned = 0

        # Patterns
        re_eval = re.compile(r"\b(eval|exec)\s*\(", re.IGNORECASE)
        re_secret = re.compile(
            r"""(?i)(api[_-]?key|secret[_-]?key|password|bearer_token)\s*=\s*['\"][a-zA-Z0-9_\-]{12,}['\"]"""
        )
        re_shell_true = re.compile(r"""subprocess\.(Popen|run|call|check_output)\(.*shell\s*=\s*True""")
        re_bare_except = re.compile(r"""\bexcept\s*:""")
        re_todo = re.compile(r"""\b(FIXME|XXX)\b(?::?\s*(.*))?""")

        files_to_check: list[Path] = []
        if scan_root.is_file():
            files_to_check = [scan_root]
        elif scan_root.is_dir():
            for root, dirs, files in os.walk(scan_root):
                dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS and not d.startswith(".")]
                for f in files:
                    p = Path(root) / f
                    if p.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                        files_to_check.append(p)

        for path in files_to_check:
            files_scanned += 1
            rel_path = path.relative_to(self.repo_dir) if path.is_relative_to(self.repo_dir) else path

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if len(findings) >= max_findings:
                        break

                    # 1. Eval / Exec check
                    if re_eval.search(line):
                        findings.append(
                            CodeReviewFinding(
                                file=str(rel_path),
                                line=line_idx,
                                severity=Severity.HIGH,
                                category="security",
                                rule_id="SEC001-DYNAMIC-EXEC",
                                message="Use of dynamic code execution (eval/exec) detected.",
                                recommendation="Replace dynamic execution with safe AST parsing or declarative dispatch.",
                            )
                        )

                    # 2. Hardcoded secret check
                    if re_secret.search(line):
                        findings.append(
                            CodeReviewFinding(
                                file=str(rel_path),
                                line=line_idx,
                                severity=Severity.CRITICAL,
                                category="security",
                                rule_id="SEC002-HARDCODED-SECRET",
                                message="Potential hardcoded secret or API key found in source.",
                                recommendation="Extract secret into environment variable or secret store.",
                            )
                        )

                    # 3. Subprocess shell=True
                    if re_shell_true.search(line):
                        findings.append(
                            CodeReviewFinding(
                                file=str(rel_path),
                                line=line_idx,
                                severity=Severity.HIGH,
                                category="security",
                                rule_id="SEC003-SHELL-TRUE",
                                message="Subprocess invoked with shell=True, susceptible to injection.",
                                recommendation="Pass arguments as a list without shell=True.",
                            )
                        )

                    # 4. Bare except: pass
                    if re_bare_except.search(line):
                        findings.append(
                            CodeReviewFinding(
                                file=str(rel_path),
                                line=line_idx,
                                severity=Severity.MEDIUM,
                                category="reliability",
                                rule_id="REL001-BARE-EXCEPT-PASS",
                                message="Silent error suppression with 'except: pass'.",
                                recommendation="Catch specific exceptions and log the failure.",
                            )
                        )

                    # 5. FIXME / XXX
                    match_fixme = re_todo.search(line)
                    if match_fixme:
                        findings.append(
                            CodeReviewFinding(
                                file=str(rel_path),
                                line=line_idx,
                                severity=Severity.LOW,
                                category="maintainability",
                                rule_id="MNT001-FIXME-MARKER",
                                message=f"Unresolved marker: {match_fixme.group(1)}",
                                recommendation="Resolve action item or track in engineering roadmap.",
                            )
                        )

            except Exception:
                continue

        counts: dict[str, int] = {
            Severity.CRITICAL.value: sum(1 for f in findings if f.severity == Severity.CRITICAL),
            Severity.HIGH.value: sum(1 for f in findings if f.severity == Severity.HIGH),
            Severity.MEDIUM.value: sum(1 for f in findings if f.severity == Severity.MEDIUM),
            Severity.LOW.value: sum(1 for f in findings if f.severity == Severity.LOW),
        }

        has_blockers = counts[Severity.CRITICAL.value] > 0 or counts[Severity.HIGH.value] > 2

        return CodeReviewReport(
            ok=True,
            files_scanned=files_scanned,
            total_findings=len(findings),
            severity_counts=counts,
            findings=findings,
            passed=not has_blockers,
        )

    # -------------------------------------------------------------------------
    # 3. Engineering Scorecard
    # -------------------------------------------------------------------------
    def compute_scorecard(self) -> EngineeringScorecard:
        """Compute composite engineering health score (0-100) and grade."""
        # Metric 1: Tests presence
        has_tests = (self.repo_dir / "tests").is_dir()
        test_files = list((self.repo_dir / "tests").glob("test_*.py")) if has_tests else []
        test_score = min(30, len(test_files) * 3) if has_tests else 0

        # Metric 2: Git activity & hygiene
        _, status_out, _ = self._run_git(["status", "--porcelain"])
        dirty_count = len([l for l in status_out.splitlines() if l.strip()])
        code, commit_count_str, _ = self._run_git(["rev-list", "--count", "HEAD"])
        commit_count = int(commit_count_str) if code == 0 and commit_count_str.isdigit() else 0

        git_score = 25
        if dirty_count > 10:
            git_score -= 10
        elif dirty_count > 0:
            git_score -= 5
        if commit_count > 20:
            git_score = min(25, git_score + 5)

        # Metric 3: Code review / security posture
        review = self.run_code_review(max_findings=20)
        crit = review.severity_counts.get(Severity.CRITICAL.value, 0)
        high = review.severity_counts.get(Severity.HIGH.value, 0)
        med = review.severity_counts.get(Severity.MEDIUM.value, 0)

        security_score = max(0, 25 - (crit * 15) - (high * 5) - (med * 2))

        # Metric 4: Modularity & structure
        mod_score = 0
        if (self.repo_dir / "src").is_dir():
            mod_score += 10
        if (self.repo_dir / "pyproject.toml").is_file():
            mod_score += 5
        if (self.repo_dir / "README.md").is_file():
            mod_score += 5

        composite = max(0, min(100, test_score + git_score + security_score + mod_score))

        if composite >= 90:
            grade = "A+"
        elif composite >= 80:
            grade = "A"
        elif composite >= 70:
            grade = "B"
        elif composite >= 60:
            grade = "C"
        else:
            grade = "D"

        recommendations: list[str] = []
        if crit > 0 or high > 0:
            recommendations.append("Remediate critical/high security issues flagged in code review (`mekong cto review`)")
        if dirty_count > 0:
            recommendations.append(f"Stage and ship {dirty_count} uncommitted file changes (`mekong ship`)")
        if not has_tests or len(test_files) < 3:
            recommendations.append("Expand automated test suite coverage in `tests/` (`mekong test`)")
        if not recommendations:
            recommendations.append("Maintain high testing and architecture rigor; ready for production scale")

        metrics_breakdown = {
            "test_files_count": len(test_files),
            "test_score": test_score,
            "git_commits_count": commit_count,
            "uncommitted_files_count": dirty_count,
            "git_score": git_score,
            "security_score": security_score,
            "modularity_score": mod_score,
            "total_findings": review.total_findings,
        }

        return EngineeringScorecard(
            ok=True,
            composite_score=composite,
            grade=grade,
            metrics=metrics_breakdown,
            recommendations=recommendations,
        )

    # -------------------------------------------------------------------------
    # 4. Environment Diagnostics & Health
    # -------------------------------------------------------------------------
    def check_health(self) -> CtoHealthReport:
        """Inspect developer environment, runtime, git, and tooling health."""
        code, status_out, _ = self._run_git(["status", "--porcelain"])
        dirty_files = [l for l in status_out.splitlines() if l.strip()]
        is_clean = code == 0 and len(dirty_files) == 0

        _, branch_out, _ = self._run_git(["branch", "--show-current"])
        branch = branch_out.strip() or "main"

        in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ

        # Check pytest
        pytest_avail = False
        try:
            import pytest  # type: ignore

            pytest_avail = True
        except ImportError:
            pass

        # Check ruff
        ruff_avail = False
        try:
            p = subprocess.run(["ruff", "--version"], capture_output=True, text=True)
            ruff_avail = p.returncode == 0
        except Exception:
            pass

        return CtoHealthReport(
            ok=True,
            git_clean=is_clean,
            uncommitted_files=len(dirty_files),
            python_version=sys.version.split()[0],
            virtualenv_active=in_venv,
            test_runner_available=pytest_avail,
            linter_available=ruff_avail,
            repo_branch=branch,
        )

    # -------------------------------------------------------------------------
    # 5. Technical Roadmap
    # -------------------------------------------------------------------------
    def generate_roadmap(self) -> TechnicalRoadmap:
        """Synthesize technical debt and engineering findings into 3-horizon roadmap."""
        scorecard = self.compute_scorecard()

        now: list[str] = []
        next_items: list[str] = []
        later: list[str] = []

        # Now: Blockers & Uncommitted changes
        if scorecard.metrics["uncommitted_files_count"] > 0:
            now.append(f"Ship {scorecard.metrics['uncommitted_files_count']} uncommitted working files via `mekong ship`")
        if scorecard.metrics["security_score"] < 20:
            now.append("Patch high-priority code smells and security anti-patterns")
        if not now:
            now.append("Refine core pipeline performance and latency percentiles")

        # Next: Scaling & Modularization
        if scorecard.metrics["test_files_count"] < 10:
            next_items.append("Increase end-to-end integration and chaos test coverage")
        next_items.append("Introduce real-time streaming telemetry and Prometheus alert thresholds")
        next_items.append("Optimize subagent routing and context token budget enforcement")

        # Later: Platform Growth
        later.append("Multi-region distributed swarm execution and federated memory replication")
        later.append("Automated self-healing CI/CD pipeline with continuous regression repair")
        later.append("Autonomous marketplace plugin distribution and auto-publishing")

        horizons = {
            "now": now,
            "next": next_items,
            "later": later,
        }
        total = sum(len(v) for v in horizons.values())

        return TechnicalRoadmap(
            ok=True,
            horizons=horizons,
            total_initiatives=total,
        )

    # -------------------------------------------------------------------------
    # Executive Summary Overview
    # -------------------------------------------------------------------------
    def executive_summary(self) -> dict[str, Any]:
        """Aggregate high-level overview for CTO dashboard."""
        scorecard = self.compute_scorecard()
        health = self.check_health()
        roadmap = self.generate_roadmap()

        return {
            "ok": True,
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "scorecard": scorecard.to_dict(),
            "health": health.to_dict(),
            "top_priorities": scorecard.recommendations,
            "initiatives_count": roadmap.total_initiatives,
        }


def get_cto_engine(repo_dir: str | Path | None = None) -> CTOEngine:
    """Factory helper returning CTOEngine instance."""
    return CTOEngine(repo_dir=repo_dir)
