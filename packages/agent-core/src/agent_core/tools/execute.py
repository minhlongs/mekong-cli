"""Execute tool — runs shell commands under ./outputs/ with a timeout.

Deliberately does NOT use shell=True; commands are split via shlex so the agent
cannot chain pipelines or redirect. Forest-phase workers should run this inside
a Docker container for real isolation.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from agent_core.tools.file_system import OUTPUTS_DIR

_DEFAULT_TIMEOUT = 30.0


def execute_command(
    command: str,
    cwd: str | Path | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> str:
    try:
        argv = shlex.split(command)
    except ValueError as e:
        return f"Lỗi parse lệnh: {e}"
    if not argv:
        return "Lỗi: lệnh rỗng"
    work_dir = Path(cwd) if cwd else OUTPUTS_DIR
    try:
        result = subprocess.run(
            argv,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Lỗi: lệnh vượt quá {timeout}s"
    except FileNotFoundError as e:
        return f"Lỗi: {e}"
    if result.returncode == 0:
        return result.stdout.strip() or "(no stdout)"
    return f"[exit {result.returncode}] {result.stderr.strip() or result.stdout.strip()}"
