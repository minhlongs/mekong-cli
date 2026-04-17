"""Unit tests for src/core/session_lifecycle_manager.py (0% → full coverage).

Covers:
- SessionState enum values
- _TRANSITIONS state machine
- Session._record_event
- SessionManager.create
- SessionManager.get
- SessionManager.transition (valid, invalid, missing)
- SessionManager.list_active
- SessionManager.cleanup (age-based + terminal states)
- SessionManager.persist (happy path + missing session)
- SessionManager.restore (happy path + missing file + bad state)
"""
from __future__ import annotations

import json
import time

import pytest

from src.core.session_lifecycle_manager import (
    Session,
    SessionManager,
    SessionState,
    _TRANSITIONS,
)


# ---------------------------------------------------------------------------
# SessionState
# ---------------------------------------------------------------------------

class TestSessionState:
    def test_all_states_exist(self):
        states = {s.value for s in SessionState}
        assert states == {"created", "active", "paused", "completed", "failed", "expired"}

    def test_str_enum(self):
        assert SessionState.ACTIVE == "active"


# ---------------------------------------------------------------------------
# _TRANSITIONS
# ---------------------------------------------------------------------------

class TestTransitions:
    def test_created_can_transition_to_active(self):
        assert SessionState.ACTIVE in _TRANSITIONS[SessionState.CREATED]

    def test_expired_has_no_outgoing_transitions(self):
        assert _TRANSITIONS[SessionState.EXPIRED] == []

    def test_active_can_pause(self):
        assert SessionState.PAUSED in _TRANSITIONS[SessionState.ACTIVE]

    def test_completed_can_only_expire(self):
        assert _TRANSITIONS[SessionState.COMPLETED] == [SessionState.EXPIRED]


# ---------------------------------------------------------------------------
# Session._record_event
# ---------------------------------------------------------------------------

class TestSessionRecordEvent:
    def test_record_event_appends_entry(self):
        s = Session(
            session_id="s1",
            state=SessionState.CREATED,
            created_at=time.time(),
            updated_at=time.time(),
        )
        s._record_event("test_event")
        assert len(s.history) == 1
        assert s.history[0]["event"] == "test_event"
        assert "timestamp" in s.history[0]

    def test_record_event_with_extra(self):
        s = Session(
            session_id="s1",
            state=SessionState.CREATED,
            created_at=time.time(),
            updated_at=time.time(),
        )
        s._record_event("transition", {"from": "created", "to": "active"})
        assert s.history[0]["from"] == "created"
        assert s.history[0]["to"] == "active"


# ---------------------------------------------------------------------------
# SessionManager.create
# ---------------------------------------------------------------------------

class TestSessionManagerCreate:
    def test_create_returns_session_in_created_state(self):
        mgr = SessionManager()
        s = mgr.create()
        assert s.state == SessionState.CREATED

    def test_create_assigns_unique_ids(self):
        mgr = SessionManager()
        s1 = mgr.create()
        s2 = mgr.create()
        assert s1.session_id != s2.session_id

    def test_create_with_metadata(self):
        mgr = SessionManager()
        s = mgr.create(metadata={"goal": "deploy"})
        assert s.metadata["goal"] == "deploy"

    def test_create_records_created_event(self):
        mgr = SessionManager()
        s = mgr.create()
        assert any(e["event"] == "created" for e in s.history)

    def test_create_registers_session_in_store(self):
        mgr = SessionManager()
        s = mgr.create()
        assert mgr.get(s.session_id) is s


# ---------------------------------------------------------------------------
# SessionManager.get
# ---------------------------------------------------------------------------

class TestSessionManagerGet:
    def test_get_returns_none_for_unknown_id(self):
        mgr = SessionManager()
        assert mgr.get("nonexistent-id") is None

    def test_get_returns_correct_session(self):
        mgr = SessionManager()
        s = mgr.create()
        assert mgr.get(s.session_id) is s


# ---------------------------------------------------------------------------
# SessionManager.transition
# ---------------------------------------------------------------------------

class TestSessionManagerTransition:
    def test_valid_transition_changes_state(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        assert s.state == SessionState.ACTIVE

    def test_valid_transition_updates_updated_at(self):
        mgr = SessionManager()
        s = mgr.create()
        old_ts = s.updated_at
        time.sleep(0.01)
        mgr.transition(s.session_id, SessionState.ACTIVE)
        assert s.updated_at >= old_ts

    def test_valid_transition_records_history(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        transition_events = [e for e in s.history if e["event"] == "transition"]
        assert len(transition_events) == 1
        assert transition_events[0]["from"] == "created"
        assert transition_events[0]["to"] == "active"

    def test_invalid_transition_raises_value_error(self):
        mgr = SessionManager()
        s = mgr.create()
        with pytest.raises(ValueError, match="Invalid transition"):
            mgr.transition(s.session_id, SessionState.COMPLETED)  # CREATED → COMPLETED invalid

    def test_unknown_session_raises_key_error(self):
        mgr = SessionManager()
        with pytest.raises(KeyError, match="not found"):
            mgr.transition("bad-id", SessionState.ACTIVE)

    def test_full_happy_path(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        mgr.transition(s.session_id, SessionState.PAUSED)
        mgr.transition(s.session_id, SessionState.ACTIVE)
        mgr.transition(s.session_id, SessionState.COMPLETED)
        assert s.state == SessionState.COMPLETED

    def test_active_to_failed(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        mgr.transition(s.session_id, SessionState.FAILED)
        assert s.state == SessionState.FAILED


# ---------------------------------------------------------------------------
# SessionManager.list_active
# ---------------------------------------------------------------------------

class TestSessionManagerListActive:
    def test_list_active_empty_initially(self):
        mgr = SessionManager()
        assert mgr.list_active() == []

    def test_list_active_returns_active_sessions(self):
        mgr = SessionManager()
        s1 = mgr.create()
        mgr.transition(s1.session_id, SessionState.ACTIVE)
        s2 = mgr.create()
        mgr.transition(s2.session_id, SessionState.ACTIVE)
        mgr.transition(s2.session_id, SessionState.PAUSED)
        active = mgr.list_active()
        assert s1 in active
        assert s2 in active

    def test_list_active_excludes_completed(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        mgr.transition(s.session_id, SessionState.COMPLETED)
        assert s not in mgr.list_active()

    def test_list_active_excludes_created_state(self):
        mgr = SessionManager()
        s = mgr.create()
        # CREATED is not ACTIVE or PAUSED
        assert s not in mgr.list_active()


# ---------------------------------------------------------------------------
# SessionManager.cleanup
# ---------------------------------------------------------------------------

class TestSessionManagerCleanup:
    def test_cleanup_removes_terminal_sessions(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        mgr.transition(s.session_id, SessionState.COMPLETED)
        removed = mgr.cleanup(max_age_seconds=9999)
        assert removed == 1
        assert mgr.get(s.session_id) is None

    def test_cleanup_removes_old_sessions(self):
        mgr = SessionManager()
        s = mgr.create()
        # Force old timestamp
        s.updated_at = time.time() - 7200
        removed = mgr.cleanup(max_age_seconds=3600)
        assert removed == 1

    def test_cleanup_keeps_young_active_sessions(self):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        removed = mgr.cleanup(max_age_seconds=3600)
        assert removed == 0
        assert mgr.get(s.session_id) is not None

    def test_cleanup_returns_count(self):
        mgr = SessionManager()
        for _ in range(3):
            s = mgr.create()
            mgr.transition(s.session_id, SessionState.ACTIVE)
            mgr.transition(s.session_id, SessionState.FAILED)
        count = mgr.cleanup()
        assert count == 3


# ---------------------------------------------------------------------------
# SessionManager.persist
# ---------------------------------------------------------------------------

class TestSessionManagerPersist:
    def test_persist_creates_json_file(self, tmp_path):
        mgr = SessionManager()
        s = mgr.create()
        path = tmp_path / "session.json"
        mgr.persist(s.session_id, path)
        assert path.exists()

    def test_persist_file_contains_correct_state(self, tmp_path):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        path = tmp_path / "session.json"
        mgr.persist(s.session_id, path)
        data = json.loads(path.read_text())
        assert data["state"] == "active"
        assert data["session_id"] == s.session_id

    def test_persist_creates_parent_dirs(self, tmp_path):
        mgr = SessionManager()
        s = mgr.create()
        path = tmp_path / "nested" / "dir" / "session.json"
        mgr.persist(s.session_id, path)
        assert path.exists()

    def test_persist_raises_key_error_for_unknown_session(self, tmp_path):
        mgr = SessionManager()
        with pytest.raises(KeyError, match="not found"):
            mgr.persist("bad-id", tmp_path / "s.json")


# ---------------------------------------------------------------------------
# SessionManager.restore
# ---------------------------------------------------------------------------

class TestSessionManagerRestore:
    def test_restore_loads_session(self, tmp_path):
        mgr = SessionManager()
        s = mgr.create()
        mgr.transition(s.session_id, SessionState.ACTIVE)
        path = tmp_path / "session.json"
        mgr.persist(s.session_id, path)

        mgr2 = SessionManager()
        restored = mgr2.restore(path)
        assert restored.session_id == s.session_id
        assert restored.state == SessionState.ACTIVE

    def test_restore_registers_session_in_store(self, tmp_path):
        mgr = SessionManager()
        s = mgr.create()
        path = tmp_path / "session.json"
        mgr.persist(s.session_id, path)

        mgr2 = SessionManager()
        restored = mgr2.restore(path)
        assert mgr2.get(restored.session_id) is restored

    def test_restore_raises_for_missing_file(self, tmp_path):
        mgr = SessionManager()
        with pytest.raises(FileNotFoundError):
            mgr.restore(tmp_path / "nonexistent.json")

    def test_restore_raises_for_invalid_state(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({
            "session_id": "x",
            "state": "TOTALLY_INVALID",
            "created_at": 0.0,
            "updated_at": 0.0,
            "metadata": {},
            "history": [],
        }))
        mgr = SessionManager()
        with pytest.raises(ValueError):
            mgr.restore(path)
