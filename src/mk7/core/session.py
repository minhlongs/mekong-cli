"""Mekong CLI 7 — Session store (port of opencode Session contract).

Session = {id, parentID?, directory, agentID, title?, todos, status}.
Child sessions = subagent work (graph runs, cook, debug). Persisted in
~/.mekong/sessions/<id>.json; a session index tracks the tree.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .config import CONFIG_DIR

SESSIONS_DIR = CONFIG_DIR / "sessions"
INDEX_FILE = SESSIONS_DIR / "index.json"

SESSION_STATUSES = ("active", "completed", "aborted", "failed")


class SessionNotFound(KeyError):
    pass


@dataclass
class Session:
    directory: str = ""
    agent_id: str = "ceo"
    parent_id: str | None = None
    title: str = ""
    status: str = "active"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    todo_ids: list[str] = field(default_factory=list)
    # ── B5: session affinity pin (OmniRoute sessionAffinityPin fix) ──
    provider_pin: str = ""   # model id được pin (thắng forced khi còn sống)
    last_model: str = ""     # model dùng ở call gần nhất
    unpin_after: float = 0   # epoch; pin hết hạn khi now > unpin_after

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "directory": self.directory,
            "agent_id": self.agent_id,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "todo_ids": self.todo_ids,
            "provider_pin": self.provider_pin,
            "last_model": self.last_model,
            "unpin_after": self.unpin_after,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            id=str(data.get("id", uuid.uuid4().hex[:12])),
            parent_id=data.get("parent_id"),
            directory=str(data.get("directory", "")),
            agent_id=str(data.get("agent_id", "ceo")),
            title=str(data.get("title", "")),
            status=str(data.get("status", "active")),
            created_at=float(data.get("created_at", 0)),
            updated_at=float(data.get("updated_at", 0)),
            todo_ids=list(data.get("todo_ids", [])),
            provider_pin=str(data.get("provider_pin", "")),
            last_model=str(data.get("last_model", "")),
            unpin_after=float(data.get("unpin_after", 0)),
        )

    # ── B5: pin helpers ──────────────────────────────────────

    def pin_model(self, model: str, duration_s: float = 3600) -> None:
        """Pin provider/model trong duration_s — pin thắng forced khi còn sống."""
        self.provider_pin = model
        self.unpin_after = time.time() + duration_s

    def pin_active(self) -> bool:
        return bool(self.provider_pin) and self.unpin_after > time.time()

    def unpin(self) -> None:
        """429 → unpin + ghi failure (sessionAffinityPin fix 3.8.50)."""
        self.provider_pin = ""
        self.unpin_after = 0.0


def _load_index() -> dict[str, str]:
    """Map session id -> relative filename."""
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_index(index: dict[str, str]) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2))


class SessionStore:
    def __init__(self):
        self._index = _load_index()

    # ── CRUD ────────────────────────────────────────────────

    def create(self, directory: str, agent_id: str = "ceo", title: str = "", parent_id: str | None = None) -> Session:
        session = Session(directory=directory, agent_id=agent_id, title=title, parent_id=parent_id)
        self._index[session.id] = f"{session.id}.json"
        self.save(session)
        _save_index(self._index)
        return session

    def get(self, session_id: str) -> Session:
        if session_id not in self._index:
            raise SessionNotFound(session_id)
        path = SESSIONS_DIR / self._index[session_id]
        if not path.exists():
            raise SessionNotFound(session_id)
        return Session.from_dict(json.loads(path.read_text()))

    def save(self, session: Session) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session.updated_at = time.time()
        path = SESSIONS_DIR / f"{session.id}.json"
        path.write_text(json.dumps(session.to_dict(), indent=2))

    def update(self, session_id: str, **changes: Any) -> Session:
        session = self.get(session_id)
        for key, value in changes.items():
            if key == "status" and value in SESSION_STATUSES:
                session.status = value
            elif key == "title":
                session.title = str(value)
            elif key == "agent_id":
                session.agent_id = str(value)
            elif key == "parent_id":
                session.parent_id = value
            elif key == "todo_ids" and isinstance(value, list):
                session.todo_ids = [str(v) for v in value]
            elif key == "provider_pin":
                session.provider_pin = str(value or "")
            elif key == "last_model":
                session.last_model = str(value or "")
            elif key == "unpin_after":
                session.unpin_after = float(value or 0)
        self.save(session)
        return session

    def delete(self, session_id: str) -> bool:
        if session_id not in self._index:
            return False
        path = SESSIONS_DIR / self._index[session_id]
        if path.exists():
            path.unlink()
        del self._index[session_id]
        _save_index(self._index)
        return True

    def list(self) -> list[Session]:
        out = []
        for sid in self._index:
            try:
                out.append(self.get(sid))
            except SessionNotFound:
                continue
        return sorted(out, key=lambda s: s.updated_at, reverse=True)

    # ── Tree ────────────────────────────────────────────────

    def children(self, parent_id: str) -> list[Session]:
        return [s for s in self.list() if s.parent_id == parent_id]

    def ancestors(self, session_id: str) -> list[Session]:
        """Parent chain of a session (excluding itself), root-most last."""
        chain: list[Session] = []
        try:
            start = self.get(session_id)
        except SessionNotFound:
            return chain
        current = start.parent_id
        while current is not None:
            try:
                parent = self.get(current)
            except SessionNotFound:
                break
            chain.append(parent)
            current = parent.parent_id
        return chain

    def subtree_ids(self, root_id: str) -> list[str]:
        ids: list[str] = [root_id]
        changed = True
        while changed:
            changed = False
            for s in self.list():
                if s.parent_id in ids and s.id not in ids:
                    ids.append(s.id)
                    changed = True
        return ids

    def attach_todo(self, session_id: str, todo_id: str) -> None:
        session = self.get(session_id)
        if todo_id not in session.todo_ids:
            session.todo_ids.append(todo_id)
            self.save(session)
