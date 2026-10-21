# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""FileAgent operations for find, read, write, tree, stats, and grep."""

from pathlib import Path
from typing import Any, List

from ..core.agent_base import Result, Task


def _file_mod() -> Any:
    import src.agents.file_agent as _mod
    return _mod


class FileAgentOpsMixin:
    """Mixin providing file system execution handlers for FileAgent."""

    cwd: str

    def _exec_find(self, task: Task) -> Result:
        pattern = task.input.get("pattern", "*")
        cmd = [
            "find", ".", "-name", pattern,
            "-not", "-path", "*/node_modules/*",
            "-not", "-path", "*/.git/*",
            "-not", "-path", "*/venv/*",
        ]
        result = _file_mod().subprocess.run(
            cmd, cwd=self.cwd, capture_output=True, text=True, timeout=15
        )
        files = [f for f in result.stdout.strip().split("\n") if f][:50]
        return Result(
            task_id=task.id,
            success=True,
            output={"files": files, "count": len(files)},
        )

    def _exec_read(self, task: Task) -> Result:
        filepath = (Path(self.cwd) / task.input.get("path", "")).resolve()
        cwd_resolved = Path(self.cwd).resolve()
        if not filepath.is_relative_to(cwd_resolved):
            return Result(task_id=task.id, success=False, output=None, error="Path traversal denied")
        if not filepath.exists():
            return Result(task_id=task.id, success=False, output=None, error=f"File not found: {filepath}")
        content = filepath.read_text(encoding="utf-8", errors="replace")
        lines = content.count("\n") + 1
        return Result(
            task_id=task.id,
            success=True,
            output={"content": content[:5000], "lines": lines, "size": len(content)},
        )

    def _exec_write(self, task: Task) -> Result:
        filepath = (Path(self.cwd) / task.input.get("path", "")).resolve()
        cwd_resolved = Path(self.cwd).resolve()
        if not filepath.is_relative_to(cwd_resolved):
            return Result(task_id=task.id, success=False, output=None, error="Path traversal denied")
        content = task.input.get("content", "")
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        return Result(
            task_id=task.id,
            success=True,
            output={"path": str(filepath), "size": len(content)},
        )

    def _exec_tree(self, task: Task) -> Result:
        depth = task.input.get("depth", 3)
        cmd = [
            "find", ".", "-maxdepth", str(depth),
            "-not", "-path", "*/node_modules/*",
            "-not", "-path", "*/.git/*",
            "-not", "-path", "*/venv/*",
            "-not", "-path", "*/__pycache__/*",
        ]
        result = _file_mod().subprocess.run(
            cmd, cwd=self.cwd, capture_output=True, text=True, timeout=15
        )
        entries = sorted(result.stdout.strip().split("\n"))[:100]
        return Result(
            task_id=task.id,
            success=True,
            output={"tree": entries, "count": len(entries)},
        )

    def _exec_stats(self, task: Task) -> Result:
        stats = {}
        requested_path = task.input.get("path") or "src"
        base = Path(self.cwd).resolve()
        root = (base / requested_path).resolve()
        if not root.is_relative_to(base) or not root.exists():
            root = base / "src"
        exts = [".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json", ".yaml", ".yml", ".css"]
        for ext in exts:
            path_files: List[Path] = [
                f for f in root.rglob(f"*{ext}")
                if not any(p in f.parts for p in ("node_modules", "venv", ".git", "__pycache__"))
            ]
            if path_files:
                total_lines = 0
                for f in path_files:
                    try:
                        total_lines += f.read_text(errors="replace").count("\n")
                    except (OSError, UnicodeDecodeError):
                        pass
                stats[ext] = {"files": len(path_files), "lines": total_lines}
        return Result(task_id=task.id, success=True, output=stats)

    def _exec_grep(self, task: Task) -> Result:
        pattern = task.input.get("pattern", "")
        cmd = [
            "grep", "-rn",
            "--include=*.py", "--include=*.ts", "--include=*.tsx",
            "--include=*.js", "--include=*.md",
            pattern, ".",
        ]
        result = _file_mod().subprocess.run(
            cmd, cwd=self.cwd, capture_output=True, text=True, timeout=15
        )
        matches = [m for m in result.stdout.strip().split("\n")[:30] if m]
        return Result(
            task_id=task.id,
            success=True,
            output={"matches": matches, "count": len(matches)},
        )
