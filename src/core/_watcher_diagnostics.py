"""Standard-library diagnostics for files monitored by the watcher."""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from ._watcher_compat import bridge_value
from ._watcher_models import DiagnosticResult


class DiagnosticsEngine:
    """Validates source files, detects syntax errors, and clusters failures."""

    def __init__(self, project_root: Optional[Path] = None, evals_db_path: Optional[Path] = None) -> None:
        path_type = bridge_value("Path", Path)
        self.project_root = path_type(project_root or path_type.cwd()).resolve()
        self.evals_db_path = evals_db_path or self.project_root / ".mekong" / "evals.db"

    def validate_source(self, code: str, filename: str = "<memory>") -> DiagnosticResult:
        parser = bridge_value("ast", ast)
        try:
            tree = parser.parse(code, filename=filename)
            for node in parser.walk(tree):
                if isinstance(node, (parser.Import, parser.ImportFrom)):
                    pass
            return DiagnosticResult(file_path=filename, is_valid=True, severity="info")
        except SyntaxError as error:
            return DiagnosticResult(file_path=filename, is_valid=False, error_type="SyntaxError",
                                    error_message=error.msg or "Syntax error", line_number=error.lineno,
                                    column_offset=error.offset, severity="error",
                                    matched_cluster_id=self.match_error_cluster(error.msg or "", "SyntaxError"))
        except Exception as error:
            return DiagnosticResult(file_path=filename, is_valid=False, error_type=type(error).__name__,
                                    error_message=str(error), severity="error",
                                    matched_cluster_id=self.match_error_cluster(str(error), type(error).__name__))

    def validate_file(self, file_path: str | Path) -> DiagnosticResult:
        path = bridge_value("Path", Path)(file_path).resolve()
        if not path.exists():
            return DiagnosticResult(str(path), False, "FileNotFoundError", f"File {path} does not exist", severity="error")
        if not path.name.endswith(".py"):
            return DiagnosticResult(str(path), True, severity="info")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as file_handle:
                return self.validate_source(file_handle.read(), filename=str(path))
        except Exception as error:
            return DiagnosticResult(str(path), False, type(error).__name__, str(error), severity="error")

    def match_error_cluster(self, error_msg: str, error_type: str) -> Optional[str]:
        try:
            regex = bridge_value("re", re)
            normalized = regex.sub(r"line \d+", "line <N>", error_msg.lower())
            normalized = regex.sub(r"0x[0-9a-f]+", "0x<HEX>", normalized)
            raw = f"{error_type}:{normalized}".strip()
            digest = bridge_value("hashlib", hashlib).sha256(raw.encode("utf-8")).hexdigest()[:8]
            return f"cluster_{digest}"
        except Exception:
            return None

    def run_tests_for_file(self, file_path: str | Path, timeout: float = 15.0) -> dict[str, Any]:
        path = bridge_value("Path", Path)(file_path).resolve()
        test_target = str(path)
        if "tests" not in path.parts:
            possible_test = self.project_root / "tests" / f"test_{path.stem}.py"
            if possible_test.exists():
                test_target = str(possible_test)
        try:
            system = bridge_value("sys", sys)
            process = bridge_value("subprocess", subprocess).run(
                [system.executable, "-m", "pytest", test_target, "-q"], cwd=str(self.project_root),
                capture_output=True, text=True, timeout=timeout)
            return {"ok": process.returncode == 0, "returncode": process.returncode,
                    "output": process.stdout + process.stderr, "target": test_target}
        except bridge_value("subprocess", subprocess).TimeoutExpired:
            return {"ok": False, "returncode": -1, "output": f"Test timed out after {timeout}s", "target": test_target}
        except Exception as error:
            return {"ok": False, "returncode": -1, "output": f"Failed to execute tests: {error}", "target": test_target}
