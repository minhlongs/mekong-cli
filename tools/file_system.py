"""File system tools for seed agents."""

from __future__ import annotations

import subprocess
from pathlib import Path


def write_file(path: str, content: str) -> str:
    """Write content to file, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p.resolve())


def read_file(path: str) -> str:
    """Read file content, return empty string if not found."""
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def execute_command(cmd: str, cwd: str | None = None) -> dict:
    """Execute shell command, return stdout/stderr/returncode."""
    import shlex
    args = shlex.split(cmd)
    result = subprocess.run(
        args,
        shell=False,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=60,
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "success": result.returncode == 0,
    }
