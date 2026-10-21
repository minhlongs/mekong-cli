"""Heuristic syntax repair operation for the autonomous watcher."""

from __future__ import annotations

import ast
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ._watcher_compat import bridge_value
from ._watcher_models import DiagnosticResult, RepairAction

if TYPE_CHECKING:
    from ._watcher_repair import SelfRepairManager


def _action_id() -> str:
    clock = bridge_value("time", time)
    return f"repair_{int(clock.time() * 1000)}_{bridge_value('os', os).urandom(3).hex()}"


def auto_fix_syntax(manager: "SelfRepairManager", file_path: str | Path,
                    diagnostic: DiagnosticResult) -> RepairAction:
    """Attempt heuristic AST syntax auto-fix on common simple typos."""
    path = bridge_value("Path", Path)(file_path).resolve()
    action_id = _action_id()
    if not path.exists() or diagnostic.is_valid:
        return RepairAction(action_id, str(path), "noop", "failed",
                            "File does not exist or has no syntax error to repair")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file_handle:
            lines = file_handle.readlines()
        if not lines:
            return RepairAction(action_id, str(path), "syntax_auto_fix", "failed", "Empty file")
        line_number = diagnostic.line_number
        line_index = line_number - 1 if line_number and line_number <= len(lines) else -1
        fixed = False
        if line_index >= 0:
            trimmed = lines[line_index].rstrip()
            stripped = trimmed.strip()
            keywords = ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "finally", "with ")
            if any(stripped.startswith(keyword) for keyword in keywords) and not stripped.endswith(":"):
                lines[line_index], fixed = trimmed + ":\n", True
            if not fixed and trimmed.count("(") > trimmed.count(")"):
                lines[line_index] = trimmed + ")" * (trimmed.count("(") - trimmed.count(")")) + "\n"
                fixed = True
        if fixed:
            candidate_code = "".join(lines)
            try:
                bridge_value("ast", ast).parse(candidate_code, filename=str(path))
                with open(path, "w", encoding="utf-8") as file_handle:
                    file_handle.write(candidate_code)
                return manager._record(RepairAction(action_id, str(path), "syntax_auto_fix", "success",
                    f"Auto-fixed syntax error on line {line_number}"))
            except SyntaxError:
                pass
        return manager._record(RepairAction(action_id, str(path), "syntax_auto_fix", "failed",
                               "Syntax error could not be resolved via AST heuristics"))
    except Exception as error:
        return manager._record(RepairAction(action_id, str(path), "syntax_auto_fix", "failed",
                               f"Exception during auto-fix: {error}"))
