"""Tests for SeedMemory — SQLite fallback path (no chromadb needed)."""

from __future__ import annotations

from agent_core.memory import SeedMemory


def test_remember_returns_id(tmp_memory: SeedMemory):
    rid = tmp_memory.remember("alice", "hello world", {"type": "greeting"})
    assert isinstance(rid, str)
    assert len(rid) >= 16


def test_recall_like_search(tmp_memory: SeedMemory):
    tmp_memory.remember("alice", "Python là ngôn ngữ tốt cho AI")
    tmp_memory.remember("alice", "Go là ngôn ngữ tốt cho backend")
    tmp_memory.remember("bob", "Python is irrelevant for bob")

    hits = tmp_memory.recall("alice", "Python")
    assert len(hits) == 1
    assert "Python" in hits[0]


def test_get_recent_is_sorted_desc(tmp_memory: SeedMemory):
    tmp_memory.remember("alice", "first")
    tmp_memory.remember("alice", "second")
    tmp_memory.remember("alice", "third")

    rows = tmp_memory.get_recent("alice", limit=2)
    assert len(rows) == 2
    assert rows[0].content == "third"
    assert rows[1].content == "second"


def test_clear_agent_removes_only_that_agent(tmp_memory: SeedMemory):
    tmp_memory.remember("alice", "a1")
    tmp_memory.remember("alice", "a2")
    tmp_memory.remember("bob", "b1")

    deleted = tmp_memory.clear_agent("alice")
    assert deleted == 2
    assert tmp_memory.get_recent("alice") == []
    assert len(tmp_memory.get_recent("bob")) == 1


def test_metadata_roundtrip(tmp_memory: SeedMemory):
    tmp_memory.remember("alice", "payload", {"priority": "high", "tags": ["a", "b"]})
    rows = tmp_memory.get_recent("alice")
    assert rows[0].metadata == {"priority": "high", "tags": ["a", "b"]}


def test_sqlite_file_is_0600(tmp_memory: SeedMemory):
    import stat as stat_mod

    mode = tmp_memory.sqlite_path.stat().st_mode & 0o777
    owner_rw = stat_mod.S_IRUSR | stat_mod.S_IWUSR
    assert mode == owner_rw, f"expected 0o600, got {oct(mode)}"
