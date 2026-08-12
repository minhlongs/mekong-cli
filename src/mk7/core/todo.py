"""Mekong CLI 7 — Todo store (port of opencode Todo contract).

Todo = {id, content, status, priority}. Persisted per session/goal in
~/.mekong/state/<slug>-todos.json. Graph nodes map 1:1 to todo items:
node pending -> todo pending, node running -> in_progress,
node done -> completed, node failed/blocked -> cancelled.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import CONFIG_DIR

STATE_DIR = CONFIG_DIR / "state"

TODO_STATUSES = ("pending", "in_progress", "completed", "cancelled")
TODO_PRIORITIES = ("high", "medium", "low")


class TodoNotFound(KeyError):
    pass


@dataclass
class Todo:
    content: str
    status: str = "pending"
    priority: str = "medium"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "content": self.content, "status": self.status, "priority": self.priority}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Todo":
        return cls(
            id=str(data.get("id", uuid.uuid4().hex[:8])),
            content=str(data.get("content", "")),
            status=str(data.get("status", "pending")),
            priority=str(data.get("priority", "medium")),
        )


class TodoStore:
    """JSON-persisted todo list scoped to one goal/session slug."""

    def __init__(self, slug: str):
        self.slug = slug
        self.path = STATE_DIR / f"{slug}-todos.json"
        self.todos: list[Todo] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.todos = [Todo.from_dict(t) for t in data.get("todos", [])]
            except Exception:
                self.todos = []

    def save(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"slug": self.slug, "todos": [t.to_dict() for t in self.todos]}, indent=2)
        )

    # ── CRUD ────────────────────────────────────────────────

    def add(self, content: str, priority: str = "medium") -> Todo:
        priority = priority if priority in TODO_PRIORITIES else "medium"
        todo = Todo(content=content, priority=priority)
        self.todos.append(todo)
        self.save()
        return todo

    def get(self, todo_id: str) -> Todo:
        for t in self.todos:
            if t.id == todo_id:
                return t
        raise TodoNotFound(todo_id)

    def update(self, todo_id: str, **changes: Any) -> Todo:
        todo = self.get(todo_id)
        if "content" in changes:
            todo.content = str(changes["content"])
        if "status" in changes and changes["status"] in TODO_STATUSES:
            todo.status = changes["status"]
        if "priority" in changes and changes["priority"] in TODO_PRIORITIES:
            todo.priority = changes["priority"]
        self.save()
        return todo

    def remove(self, todo_id: str) -> bool:
        before = len(self.todos)
        self.todos = [t for t in self.todos if t.id != todo_id]
        if len(self.todos) != before:
            self.save()
            return True
        return False

    def list(self, status: str | None = None) -> list[Todo]:
        if status is None:
            return list(self.todos)
        return [t for t in self.todos if t.status == status]

    def summary(self) -> dict[str, int]:
        counts = {s: 0 for s in TODO_STATUSES}
        for t in self.todos:
            counts[t.status] = counts.get(t.status, 0) + 1
        return counts


def sync_todos_from_graph(store: TodoStore, nodes: list[Any], title_map: dict[str, str]) -> None:
    """Sync graph node states into the todo store (1 node = 1 todo).

    Creates todos for nodes without one; updates status:
    pending -> pending, running -> in_progress, done -> completed,
    failed/blocked -> cancelled. Preserves completed todos across resume.
    Todo id == node id so repeated syncs are idempotent.
    """
    node_status_map = {
        "pending": "pending",
        "running": "in_progress",
        "done": "completed",
        "failed": "cancelled",
        "blocked": "cancelled",
    }
    by_id = {t.id: t for t in store.todos}

    for node in nodes:
        key = getattr(node, "id", None) or ""
        if not key:
            continue
        existing = by_id.get(key)
        if existing is None:
            todo = store.add(
                title_map.get(key, getattr(node, "task", key)),
                priority="high" if getattr(node, "gate", None) else "medium",
            )
            # pin todo id to the node id for idempotent sync
            todo.id = key
            store.save()
            by_id[key] = todo
            existing = todo
        status = node_status_map.get(getattr(node, "status", "pending"), "pending")
        if existing.status != status and status != "pending":
            store.update(existing.id, status=status)
            by_id[key] = existing
