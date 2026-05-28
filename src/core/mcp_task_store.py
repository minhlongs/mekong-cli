"""Mekong MCP Task Store — simple JSON-backed task persistence for MCP tools."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TASK_STATUSES = ("todo", "in-progress", "done")

_DEFAULT_DIR = Path.home() / ".mekong"
_DEFAULT_PATH = _DEFAULT_DIR / "mcp_tasks.json"


class McpTask:
    """A single task managed via MCP tools."""

    def __init__(
        self,
        task_id: str,
        subject: str,
        status: str = "todo",
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.subject = subject
        self.status = status if status in TASK_STATUSES else "todo"
        self.created_at = created_at or _now()
        self.updated_at = updated_at or _now()

    def to_dict(self) -> dict[str, str]:
        return {
            "task_id": self.task_id,
            "subject": self.subject,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> "McpTask":
        return cls(
            task_id=d["task_id"],
            subject=d["subject"],
            status=d.get("status", "todo"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    import hashlib
    import time

    raw = f"{time.time_ns()}{threading.get_ident()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


class McpTaskStore:
    """Thread-safe JSON-backed task store for MCP tools."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else _DEFAULT_PATH
        self._lock = threading.Lock()
        self._tasks: dict[str, McpTask] = {}
        self._loaded = False
        self._dirty = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, subject: str) -> McpTask:
        task = McpTask(task_id=_generate_id(), subject=subject)
        with self._lock:
            self._load()
            self._tasks[task.task_id] = task
            self._dirty = True
            self._save()
        return task

    def list(self, status: str = "") -> list[McpTask]:
        with self._lock:
            self._load()
            tasks = list(self._tasks.values())
        if status:
            status_lower = status.lower().replace("_", "-")
            tasks = [t for t in tasks if t.status == status_lower]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def get(self, task_id: str) -> McpTask | None:
        with self._lock:
            self._load()
            return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: str) -> McpTask | None:
        if status not in TASK_STATUSES:
            return None
        with self._lock:
            self._load()
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.status = status
            task.updated_at = _now()
            self._dirty = True
            self._save()
        return task

    def delete(self, task_id: str) -> bool:
        with self._lock:
            self._load()
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
            self._dirty = True
            self._save()
        return True

    def stats(self) -> dict[str, int]:
        with self._lock:
            self._load()
            counts: dict[str, int] = {"total": len(self._tasks)}
            for t in self._tasks.values():
                counts[t.status] = counts.get(t.status, 0) + 1
        for s in TASK_STATUSES:
            counts.setdefault(s, 0)
        return counts

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        self._tasks = {}
        try:
            if self._path.exists():
                raw = self._path.read_text(encoding="utf-8").strip()
                if raw:
                    data = json.loads(raw)
                    if isinstance(data, list):
                        for item in data:
                            task = McpTask.from_dict(item)
                            self._tasks[task.task_id] = task
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load MCP tasks from %s: %s", self._path, exc)
        self._loaded = True

    def _save(self) -> None:
        if not self._dirty:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = [t.to_dict() for t in self._tasks.values()]
            self._path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            self._dirty = False
        except OSError as exc:
            logger.warning("Failed to save MCP tasks to %s: %s", self._path, exc)


# Module-level singleton
_store: McpTaskStore | None = None


def get_task_store(path: str | Path | None = None) -> McpTaskStore:
    global _store
    if _store is None:
        _store = McpTaskStore(path=path)
    return _store
