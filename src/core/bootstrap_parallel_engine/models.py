"""Data models and exceptions for the parallel bootstrap engine."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
import stat
import threading
from typing import Any, Callable, Optional


class CyclicDependencyError(Exception):
    """Raised when circular dependencies exist in the task dependency DAG."""


class TaskStatus(str, Enum):
    """Execution status of a bootstrap task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskTiming:
    """Execution timing and telemetry for a single task."""

    task_id: str
    name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    worker_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "worker_id": self.worker_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else str(self.status),
            "error": self.error,
        }


@dataclass
class BootstrapTask:
    """A single unit of work in the parallel bootstrap pipeline."""

    id: str
    name: str
    dependencies: list[str] = field(default_factory=list)
    action: Callable[["BootstrapContext"], Any] = field(default=lambda ctx: None)
    optional: bool = False
    timeout_seconds: float = 30.0


@dataclass
class BootstrapContext:
    """Thread-safe execution context for workspace scaffolding."""

    target_path: Path
    profile: str = "standard"
    template: str = "default"
    workers: int = 4
    dry_run: bool = False
    force: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)
    created_files: list[str] = field(default_factory=list)
    created_directories: list[str] = field(default_factory=list)
    overwritten_files: dict[str, str] = field(default_factory=dict)
    task_timings: dict[str, TaskTiming] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def write_file(self, rel_path: str, content: str) -> None:
        """Thread-safe file creation with immediate snapshot registration."""
        with self.lock:
            clean_rel = os.path.normpath(rel_path).lstrip(os.sep)
            dest = (self.target_path / clean_rel).resolve()
            target_res = self.target_path.resolve()
            if not dest.is_relative_to(target_res):
                raise ValueError(f"Path traversal detected: {rel_path} escapes target directory {target_res}")
            dest_exists = dest.exists()
            if dest_exists and not self.force:
                return
            if dest_exists:
                if clean_rel not in self.overwritten_files:
                    try:
                        self.overwritten_files[clean_rel] = dest.read_text(encoding="utf-8")
                    except Exception:
                        self.overwritten_files[clean_rel] = ""
            if not self.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                if clean_rel.startswith("scripts/") and clean_rel.endswith(".py") and os.name != "nt":
                    try:
                        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    except OSError:
                        pass
            if not dest_exists and clean_rel not in self.created_files:
                self.created_files.append(clean_rel)

    def register_dir(self, rel_dir: str) -> None:
        """Thread-safe directory registration."""
        with self.lock:
            clean_rel = os.path.normpath(rel_dir).lstrip(os.sep)
            dest = (self.target_path / clean_rel).resolve()
            target_res = self.target_path.resolve()
            if not dest.is_relative_to(target_res):
                raise ValueError(f"Path traversal detected: {rel_dir} escapes target directory {target_res}")
            dest_existed = dest.exists()
            if not self.dry_run:
                dest.mkdir(parents=True, exist_ok=True)
            if not dest_existed and clean_rel not in self.created_directories:
                self.created_directories.append(clean_rel)


@dataclass
class BootstrapResult:
    """Result summary of parallel project bootstrap execution."""

    ok: bool
    rolled_back: bool
    error: Optional[str]
    target_path: Path
    profile: str
    template: str
    workers: int
    dry_run: bool
    created_files: list[str] = field(default_factory=list)
    created_directories: list[str] = field(default_factory=list)
    task_timings: dict[str, TaskTiming] = field(default_factory=dict)
    duration_ms: float = 0.0
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.ok

    def to_dict(self) -> dict[str, Any]:
        target_str = str(self.target_path.resolve())
        timings_dict = {
            tid: (t.to_dict() if hasattr(t, "to_dict") else dataclasses.asdict(t))
            for tid, t in self.task_timings.items()
        }
        return {
            "ok": self.ok,
            "success": self.ok,
            "rolled_back": self.rolled_back,
            "error": self.error,
            "target_path": target_str,
            "target": target_str,
            "profile": self.profile,
            "template": self.template,
            "workers": self.workers,
            "dry_run": self.dry_run,
            "created_files": list(self.created_files),
            "created_directories": list(self.created_directories),
            "task_timings": timings_dict,
            "duration_ms": self.duration_ms,
            "stats": self.stats,
        }
