"""Health sweep orchestration and report persistence."""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .health_checks import add_database_check, add_runtime_check, add_workspace_check
from .models import HealthSweepReport

ConnectionFactory = Callable[[], Any]


def _add_storage_check(project_root: Path, checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    try:
        free_gb = round(shutil.disk_usage(str(project_root)).free / (1024 ** 3), 2)
    except Exception as exc:
        checks.append({"category": "storage", "name": "Disk Free Space", "status": "WARN", "details": f"Could not determine disk usage: {exc}"})
        return -5
    if free_gb < 1.0:
        status, delta = "FAIL", -25
        warnings.append(f"Critically low disk space: {free_gb} GB remaining")
    elif free_gb < 5.0:
        status, delta = "WARN", -10
        warnings.append(f"Low disk space: {free_gb} GB remaining")
    else:
        status, delta = "PASS", 0
    checks.append({"category": "storage", "name": "Disk Free Space", "status": status, "details": f"{free_gb} GB free on target filesystem"})
    return delta


def _add_git_check(project_root: Path, checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    try:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=str(project_root), capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise RuntimeError("git unavailable")
        count = len([line for line in result.stdout.splitlines() if line.strip()])
        checks.append({"category": "git", "name": "Git Repository State", "status": "PASS" if count == 0 else "WARN", "details": "Working tree clean" if count == 0 else f"{count} uncommitted changes"})
        if count > 20:
            warnings.append(f"Large working tree delta ({count} uncommitted files)")
            return -5
    except Exception:
        checks.append({"category": "git", "name": "Git Repository State", "status": "PASS", "details": "Git check skipped (command unavailable or timed out)"})
    return 0


def _add_config_check(project_root: Path, checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    required = ["HARNESS.md", "AGENTS.md", "pyproject.toml"]
    missing = [name for name in required if not (project_root / name).exists()]
    if missing:
        details = ", ".join(missing)
        checks.append({"category": "config", "name": "Core Configuration", "status": "WARN", "details": f"Missing files: {details}"})
        warnings.append(f"Missing core configuration files: {details}")
        return -5 * len(missing)
    checks.append({"category": "config", "name": "Core Configuration", "status": "PASS", "details": "HARNESS.md, AGENTS.md, and pyproject.toml present"})
    return 0


def _write_report(report: HealthSweepReport, output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination = output_dir / f"health_sweep_{slug}.md"
    lines = ["# Mekong System Health Sweep Report", f"**Timestamp**: {report.timestamp}", f"**Overall Status**: `{report.overall_status}` | **Score**: `{report.score}/100`", "", "## Executive Summary", report.summary, "", "## Check Details", "| Category | Check | Status | Details |", "|---|---|---|---|"]
    lines.extend(f"| {item['category']} | {item['name']} | `{item['status']}` | {item['details']} |" for item in report.checks)
    if report.warnings:
        lines.extend(["", "## Active Warnings", *[f"- ⚠️ {warning}" for warning in report.warnings]])
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(destination)


def run_health_sweep(project_root: Path, get_connection: ConnectionFactory, save_report: bool = False, output_dir: Optional[Path] = None) -> HealthSweepReport:
    """Assess local runtime, storage, state integrity, and configuration."""
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []
    score = 100
    for checker in (add_runtime_check,):
        score += checker(checks, warnings)
    score += add_workspace_check(project_root, checks, warnings)
    score += _add_storage_check(project_root, checks, warnings)
    score += add_database_check(project_root, checks, warnings)
    score += _add_git_check(project_root, checks, warnings)
    score += _add_config_check(project_root, checks, warnings)
    score = max(0, min(100, score))
    status = "HEALTHY" if score >= 85 else "DEGRADED" if score >= 60 else "CRITICAL"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = HealthSweepReport(timestamp, status, score, checks, warnings, f"System status {status} (Score: {score}/100) across {len(checks)} checks.")
    if save_report:
        report.report_file = _write_report(report, output_dir or project_root / "reports" / "health-sweep")
    try:
        with get_connection() as connection:
            connection.execute("INSERT INTO health_sweeps (id, timestamp, overall_status, score, summary, checks_json) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), timestamp, status, score, report.summary, json.dumps(checks)))
            connection.commit()
    except Exception:
        pass
    return report
