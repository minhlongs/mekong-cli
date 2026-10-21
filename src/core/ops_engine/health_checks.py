"""Individual operations health checks."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def add_runtime_check(checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    """Record the Python runtime requirement result and return its score delta."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        checks.append({"category": "runtime", "name": "Python Version", "status": "PASS", "details": f"Python {version} meets requirement (>= 3.10)"})
        return 0
    checks.append({"category": "runtime", "name": "Python Version", "status": "FAIL", "details": f"Python {version} is unsupported (< 3.10)"})
    warnings.append(f"Outdated Python version: {version}")
    return -25


def add_workspace_check(project_root: Path, checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    """Confirm the workspace can create and remove a temporary file."""
    try:
        temporary_file = project_root / ".ops_health_tmp"
        temporary_file.write_text("ok", encoding="utf-8")
        temporary_file.unlink()
        checks.append({"category": "filesystem", "name": "Workspace Write Access", "status": "PASS", "details": f"Writable workspace at {project_root}"})
        return 0
    except Exception as exc:
        checks.append({"category": "filesystem", "name": "Workspace Write Access", "status": "FAIL", "details": f"Failed to write to project root: {exc}"})
        warnings.append("Workspace directory is not writable")
        return -30


def add_database_check(project_root: Path, checks: List[Dict[str, Any]], warnings: List[str]) -> int:
    """Verify integrity of local Mekong SQLite state files."""
    databases = list((project_root / ".mekong").glob("*.db"))
    errors: List[str] = []
    for database in databases:
        try:
            with sqlite3.connect(str(database)) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                errors.append(f"{database.name}: integrity check failed ({result})")
        except Exception as exc:
            errors.append(f"{database.name}: {exc}")
    if errors:
        checks.append({"category": "database", "name": "Database Integrity", "status": "FAIL", "details": "; ".join(errors)})
        warnings.append("Corrupted database file(s) detected in .mekong/")
        return -25
    detail = f"All {len(databases)} SQLite databases verified healthy" if databases else "No local SQLite databases initialized yet"
    checks.append({"category": "database", "name": "Database Integrity", "status": "PASS", "details": detail})
    return 0


def git_status(project_root: Path) -> Tuple[bool, int]:
    """Return whether the tree is clean and its number of changed paths."""
    try:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=str(project_root), capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            changed = len([line for line in result.stdout.splitlines() if line.strip()])
            return changed == 0, changed
    except Exception:
        pass
    return True, 0
