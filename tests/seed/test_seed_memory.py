"""Unit tests for seed/memory.py — uses temp dirs, no real data persisted."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from seed.memory import SeedMemory


@pytest.fixture
def temp_memory(tmp_path):
    """SeedMemory instance with isolated temp dirs."""
    chroma_path = str(tmp_path / "chroma")
    sqlite_path = str(tmp_path / "memory.db")
    os.makedirs(chroma_path, exist_ok=True)
    with (
        patch("seed.memory.CHROMA_PATH", chroma_path),
        patch("seed.memory.SQLITE_PATH", sqlite_path),
    ):
        mem = SeedMemory()
        yield mem


class TestSeedMemory:
    def test_remember_returns_doc_id(self, temp_memory):
        doc_id = temp_memory.remember("test-agent", "I learned something", {"key": "val"})
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_get_recent_returns_stored_entry(self, temp_memory):
        temp_memory.remember("agent-a", "first memory")
        recent = temp_memory.get_recent("agent-a", limit=5)
        assert len(recent) >= 1
        assert recent[0]["content"] == "first memory"

    def test_get_recent_respects_limit(self, temp_memory):
        for i in range(5):
            temp_memory.remember("agent-b", f"memory {i}")
        recent = temp_memory.get_recent("agent-b", limit=3)
        assert len(recent) <= 3

    def test_get_recent_returns_newest_first(self, temp_memory):
        temp_memory.remember("agent-c", "old memory")
        temp_memory.remember("agent-c", "new memory")
        recent = temp_memory.get_recent("agent-c", limit=2)
        assert recent[0]["content"] == "new memory"

    def test_get_recent_empty_for_unknown_agent(self, temp_memory):
        recent = temp_memory.get_recent("no-such-agent", limit=5)
        assert recent == []

    def test_clear_agent_memory_removes_entries(self, temp_memory):
        temp_memory.remember("agent-d", "to be cleared")
        temp_memory.clear_agent_memory("agent-d")
        recent = temp_memory.get_recent("agent-d", limit=10)
        assert recent == []

    def test_metadata_stored_and_retrieved(self, temp_memory):
        meta = {"task": "write tests", "score": 9}
        temp_memory.remember("agent-e", "content with meta", meta)
        recent = temp_memory.get_recent("agent-e", limit=1)
        assert recent[0]["metadata"]["task"] == "write tests"
        assert recent[0]["metadata"]["score"] == 9

    def test_metadata_always_contains_agent_id(self, temp_memory):
        temp_memory.remember("agent-f", "content", {"custom_key": "value"})
        recent = temp_memory.get_recent("agent-f", limit=1)
        assert recent[0]["metadata"]["agent_id"] == "agent-f"
        assert recent[0]["metadata"]["custom_key"] == "value"

    def test_metadata_agent_id_preserved_if_caller_supplies_it(self, temp_memory):
        # setdefault: caller-supplied agent_id is kept, not overwritten
        temp_memory.remember("agent-g", "content", {"agent_id": "caller-set"})
        recent = temp_memory.get_recent("agent-g", limit=1)
        assert recent[0]["metadata"]["agent_id"] == "caller-set"

    def test_multiple_agents_isolated(self, temp_memory):
        temp_memory.remember("agent-x", "x memory")
        temp_memory.remember("agent-y", "y memory")
        x_recent = temp_memory.get_recent("agent-x", limit=5)
        y_recent = temp_memory.get_recent("agent-y", limit=5)
        assert all("x memory" == r["content"] for r in x_recent)
        assert all("y memory" == r["content"] for r in y_recent)
