"""Tests for jsonl MemoryStore (Step 8 Phase B)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from src.core.memory_store import MemoryEntry, MemoryStore, memory_search


class TestMemoryEntry(unittest.TestCase):
    def test_defaults(self):
        entry = MemoryEntry(agent="cto", action="deploy", outcome="success")
        assert entry.timestamp
        assert entry.agent == "cto"
        assert entry.action == "deploy"
        assert entry.outcome == "success"
        assert entry.tags == []
        assert entry.context == {}

    def test_roundtrip_json(self):
        entry = MemoryEntry(
            agent="cmo", action="email blast", outcome="failed", tags=["email", "spam"]
        )
        data = json.loads(json.dumps(entry, default=lambda o: o.__dict__))
        reconstructed = MemoryEntry(**data)
        assert reconstructed.agent == entry.agent


class TestMemoryStore(unittest.TestCase):
    def _make(self, tmpdir: str) -> MemoryStore:
        path = os.path.join(tmpdir, "memory.jsonl")
        return MemoryStore(path=path)

    def test_append_and_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(
                MemoryEntry(agent="a", action="act1", outcome="success", tags=["t1"])
            )
            store.append(
                MemoryEntry(agent="b", action="act2", outcome="failed", tags=["t2"])
            )
            recent = store.recent(limit=2)
            assert len(recent) == 2
            # recent() returns most-recent first
            assert recent[0].action == "act2"
            assert recent[0].outcome == "failed"
            assert recent[-1].action == "act1"
            assert recent[-1].outcome == "success"

    def test_append_requires_agent_and_action(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            with self.assertRaises(ValueError):
                store.append(MemoryEntry(outcome="success"))
            with self.assertRaises(ValueError):
                store.append(MemoryEntry(agent="x"))

    def test_search_matches_action_and_tags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(
                MemoryEntry(agent="cto", action="deploy prod", outcome="success", tags=["deploy", "prod"])
            )
            store.append(
                MemoryEntry(agent="cmo", action="email blast", outcome="failed", tags=["email"])
            )
            hits = store.search("deploy")
            assert len(hits) == 1
            assert hits[0].agent == "cto"
            hits2 = store.search("email")
            assert len(hits2) == 1
            assert hits2[0].outcome == "failed"

    def test_search_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            for i in range(10):
                store.append(MemoryEntry(agent="a", action=f"act{i}", outcome="success"))
            hits = store.search("act", limit=3)
            assert len(hits) == 3

    def test_search_empty_query_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            assert store.search("") == []
            assert store.search("   ") == []

    def test_search_no_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(MemoryEntry(agent="a", action="x", outcome="ok"))
            assert store.search("zzz-no-match") == []

    def test_search_malformed_line_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            path = store._path
            with path.open("a", encoding="utf-8") as f:
                f.write("not-json\n")
                f.write(json.dumps({"agent": "a", "action": "ok", "outcome": "ok"}) + "\n")
            hits = store.search("ok")
            assert len(hits) == 1
            assert hits[0].agent == "a"

    def test_clear_removes_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(MemoryEntry(agent="a", action="x", outcome="ok"))
            removed = store.clear()
            assert removed == 1
            assert store.recent() == []

    def test_clear_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nonexistent.jsonl")
            store = MemoryStore(path=path)
            assert store.clear() == 0

    def test_has_similar_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(
                MemoryEntry(agent="cto", action="billing bug", outcome="failed", context={"project": "x"})
            )
            # has_similar compares (action, context) of stored entry against the provided key
            prior = store.has_similar(
                goal="billing bug", context=json.dumps({"project": "x"}, sort_keys=True, ensure_ascii=False)
            )
            assert prior is not None
            assert prior.outcome == "failed"

    def test_has_similar_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self._make(tmpdir)
            store.append(MemoryEntry(agent="a", action="x", outcome="ok"))
            assert store.has_similar(goal="y", context="z") is None

    def test_memory_search_helper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "memory.jsonl")
            store = MemoryStore(path=path)
            store.append(
                MemoryEntry(agent="cfo", action="billing bug", outcome="failed", tags=["billing"])
            )
            hits = memory_search("billing bug", limit=5, path=path)
            assert len(hits) == 1
            assert hits[0].agent == "cfo"


if __name__ == "__main__":
    unittest.main()
