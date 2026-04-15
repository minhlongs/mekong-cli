"""Telegram bot inbox — task queue backed by .mekong/inbox.json."""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

INBOX_PATH = Path(".mekong/inbox.json")


def _load_inbox() -> list:
    """Load inbox tasks from file."""
    if not INBOX_PATH.exists():
        return []
    try:
        result = json.loads(INBOX_PATH.read_text())
        return list(result)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load inbox: %s", e)
        return []


def _save_inbox(tasks: list) -> None:
    """Save inbox tasks to file."""
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INBOX_PATH.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))


def add_task(goal: str, project: str | None = None, chat_id: int = 0) -> dict:
    """Add a new task to the inbox."""
    task = {
        "id": uuid.uuid4().hex[:8],
        "goal": goal,
        "project": project,
        "chat_id": chat_id,
        "status": "pending",
        "created_at": time.time(),
        "created_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    inbox = _load_inbox()
    inbox.append(task)
    _save_inbox(inbox)
    return task


def get_pending_tasks() -> list:
    """Get all pending tasks from inbox."""
    return [t for t in _load_inbox() if t.get("status") == "pending"]


def mark_task(task_id: str, status: str, result: str = "") -> None:
    """Update a task's status."""
    inbox = _load_inbox()
    for t in inbox:
        if t["id"] == task_id:
            t["status"] = status
            t["result"] = result
            t["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    _save_inbox(inbox)


__all__ = [
    "INBOX_PATH",
    "_load_inbox",
    "_save_inbox",
    "add_task",
    "get_pending_tasks",
    "mark_task",
]
