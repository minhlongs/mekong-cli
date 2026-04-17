"""File-system tool — writes are sandboxed under ./outputs/.

Paths are resolved against OUTPUTS_DIR and checked to prevent traversal outside
the sandbox. write_file creates parent directories as needed.
"""

from __future__ import annotations

import os
from pathlib import Path

OUTPUTS_DIR = Path(os.getenv("AGENT_CORE_OUTPUTS", "./outputs")).resolve()
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve(rel_path: str) -> Path:
    target = (OUTPUTS_DIR / rel_path).resolve()
    try:
        target.relative_to(OUTPUTS_DIR)
    except ValueError as e:
        raise ValueError(f"Path traversal rejected: {rel_path}") from e
    return target


def write_file(file_path: str, content: str) -> str:
    target = _resolve(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Đã ghi file: {target}"


def read_file(file_path: str) -> str:
    target = _resolve(file_path)
    if not target.exists():
        return f"File không tồn tại: {target}"
    return target.read_text(encoding="utf-8")
