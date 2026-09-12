# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Coverage tests for vector_memory_store and agent_registry.

Completes 100% statement and branch coverage for Iteration 22.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.agent_base import AgentBase
from src.core.agent_registry import (
    AgentMeta,
    AgentRegistry,
    _description_from_frontmatter,
    _discover_markdown_agents,
    _make_markdown_agent_class,
    _register_known_agents,
    get_registry,
)
from src.core.vector_memory_store import (
    MemoryType,
    VectorCollection,
    VectorEntry,
    VectorMemoryStore,
)


# =========================================================================
# vector_memory_store.py
# =========================================================================
class TestVectorMemoryStore:
    def test_enums_and_dataclasses(self) -> None:
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.PROCEDURAL.value == "procedural"

        entry = VectorEntry(
            id="e1",
            vector=[0.1, 0.2],
            payload={"tag": "test"},
            memory_type=MemoryType.SEMANTIC,
        )
        assert entry.id == "e1"
        assert entry.payload == {"tag": "test"}
        assert entry.created_at > 0

        col = VectorCollection(name="col1", dimension=2)
        assert col.name == "col1"
        assert col.dimension == 2
        assert col.entries == {}

    def test_create_and_get_collection(self) -> None:
        store = VectorMemoryStore()
        col = store.create_collection("users", 3)
        assert col.name == "users"
        assert col.dimension == 3

        # Duplicate create raises ValueError
        with pytest.raises(ValueError, match="already exists"):
            store.create_collection("users", 3)

        # get_or_create_collection existing
        col2 = store.get_or_create_collection("users", 3)
        assert col2 is col

        # get_or_create_collection new
        col3 = store.get_or_create_collection("items", 4)
        assert col3.dimension == 4
        assert "items" in store.list_collections()

    def test_delete_collection(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("to_delete", 2)
        assert "to_delete" in store.list_collections()

        store.delete_collection("to_delete")
        assert "to_delete" not in store.list_collections()

        with pytest.raises(KeyError, match="not found"):
            store.delete_collection("nonexistent")

    def test_upsert_and_dimension_validation(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("docs", 3)

        # Successful upsert
        entry = store.upsert(
            collection="docs",
            id="d1",
            vector=[1.0, 0.0, 0.0],
            payload={"category": "tech"},
            memory_type=MemoryType.PROCEDURAL,
        )
        assert entry.id == "d1"
        assert store.count("docs") == 1

        # Dimension mismatch raises ValueError
        with pytest.raises(ValueError, match="Vector dimension 2 != collection dimension 3"):
            store.upsert("docs", "bad", [1.0, 2.0])

        # Nonexistent collection raises KeyError
        with pytest.raises(KeyError, match="not found"):
            store.upsert("missing", "id", [1.0])

    def test_search_and_cosine_similarity(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("vectors", 2)

        # Empty collection returns []
        assert store.search("vectors", [1.0, 0.0]) == []

        # Query dimension mismatch raises ValueError
        with pytest.raises(ValueError, match="Query dimension 3 != collection dimension 2"):
            store.search("vectors", [1.0, 0.0, 0.0])

        # Add entries
        store.upsert("vectors", "v1", [1.0, 0.0], memory_type=MemoryType.EPISODIC)
        store.upsert("vectors", "v2", [0.0, 1.0], memory_type=MemoryType.SEMANTIC)
        store.upsert("vectors", "v3", [0.7071, 0.7071], memory_type=MemoryType.EPISODIC)
        # Zero vector for edge case
        store.upsert("vectors", "zero", [0.0, 0.0], memory_type=MemoryType.EPISODIC)

        # Search all
        results = store.search("vectors", [1.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0][0].id == "v1"
        assert results[0][1] == pytest.approx(1.0)

        # Search with memory_type filter
        semantic_results = store.search("vectors", [1.0, 0.0], memory_type=MemoryType.SEMANTIC)
        assert len(semantic_results) == 1
        assert semantic_results[0][0].id == "v2"

        # Search with zero query vector returns 0.0 similarity
        zero_results = store.search("vectors", [0.0, 0.0])
        assert all(score == 0.0 for _, score in zero_results)

    def test_search_by_payload(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("data", 2)
        store.upsert("data", "1", [1.0, 0.0], payload={"env": "prod", "tier": "free"})
        store.upsert("data", "2", [0.0, 1.0], payload={"env": "prod", "tier": "pro"})
        store.upsert("data", "3", [0.5, 0.5], payload={"env": "dev", "tier": "pro"})

        hits = store.search_by_payload("data", {"env": "prod"})
        assert len(hits) == 2
        assert {h.id for h in hits} == {"1", "2"}

        hits_multi = store.search_by_payload("data", {"env": "prod", "tier": "pro"})
        assert len(hits_multi) == 1
        assert hits_multi[0].id == "2"

        hits_limit = store.search_by_payload("data", {"env": "prod"}, limit=1)
        assert len(hits_limit) == 1

    def test_delete_point(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("pts", 2)
        store.upsert("pts", "p1", [1.0, 0.0])
        assert store.count("pts") == 1

        store.delete_point("pts", "p1")
        assert store.count("pts") == 0

        with pytest.raises(KeyError, match="Entry 'p1' not found"):
            store.delete_point("pts", "p1")

    def test_get_collection_info(self) -> None:
        store = VectorMemoryStore()
        store.create_collection("info_col", 2)
        store.upsert("info_col", "1", [1.0, 0.0], memory_type=MemoryType.EPISODIC)
        store.upsert("info_col", "2", [0.0, 1.0], memory_type=MemoryType.SEMANTIC)

        info = store.get_collection_info("info_col")
        assert info["name"] == "info_col"
        assert info["dimension"] == 2
        assert info["count"] == 2
        assert info["memory_types"]["episodic"] == 1
        assert info["memory_types"]["semantic"] == 1

    def test_persistence_save_and_load(self, tmp_path: Path) -> None:
        persist_file = tmp_path / "vectors.json"
        store = VectorMemoryStore(persist_path=str(persist_file))
        store.create_collection("persisted", 2)
        store.upsert(
            "persisted",
            "p1",
            [0.6, 0.8],
            payload={"key": "val"},
            memory_type=MemoryType.PROCEDURAL,
        )

        assert persist_file.exists()

        # Load into new store instance
        store2 = VectorMemoryStore(persist_path=str(persist_file))
        assert "persisted" in store2.list_collections()
        assert store2.count("persisted") == 1
        entry = store2.search_by_payload("persisted", {"key": "val"})[0]
        assert entry.id == "p1"
        assert entry.memory_type == MemoryType.PROCEDURAL

    def test_save_snapshot_default_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        target_file = tmp_path / "mock_store.json"
        monkeypatch.setattr(
            "src.core.vector_memory_store.Path",
            lambda p: target_file if p == ".mekong/vector_store.json" else Path(p),
        )
        store = VectorMemoryStore()
        store.create_collection("test", 1)
        path = store.save_snapshot()
        assert Path(path).exists()

    def test_load_snapshot_corrupted_or_invalid_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "corrupted.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        store = VectorMemoryStore(persist_path=str(bad_file))
        assert store.list_collections() == []

        # Valid json with invalid memory_type fallback
        invalid_type_data = {
            "col": {
                "dimension": 2,
                "entries": [
                    {
                        "id": "e1",
                        "vector": [1.0, 0.0],
                        "payload": {},
                        "memory_type": "unknown_future_type",
                        "created_at": 100.0,
                    }
                ],
            }
        }
        valid_file = tmp_path / "fallback.json"
        valid_file.write_text(json.dumps(invalid_type_data), encoding="utf-8")
        store2 = VectorMemoryStore(persist_path=str(valid_file))
        assert store2.count("col") == 1
        entry = store2.search("col", [1.0, 0.0])[0][0]
        assert entry.memory_type == MemoryType.EPISODIC

    def test_text_to_hash_vector_dimensions(self) -> None:
        # Dimension <= 32 (e.g. 16)
        v16 = VectorMemoryStore.text_to_hash_vector("hello world", dimension=16)
        assert len(v16) == 16
        # Check normalized (length ~ 1)
        mag16 = sum(x * x for x in v16)
        assert mag16 == pytest.approx(1.0, rel=1e-3)

        # Dimension > 32 (e.g. 64)
        v64 = VectorMemoryStore.text_to_hash_vector("hello world", dimension=64)
        assert len(v64) == 64
        mag64 = sum(x * x for x in v64)
        assert mag64 == pytest.approx(1.0, rel=1e-3)

        # Deterministic
        v64_again = VectorMemoryStore.text_to_hash_vector("hello world", dimension=64)
        assert v64 == v64_again


# =========================================================================
# agent_registry.py remaining coverage
# =========================================================================
class TestAgentRegistryCoverageExtended:
    def test_allowed_tools_validation(self) -> None:
        class DummyAgent(AgentBase):
            def plan(self, x): return []
            def execute(self, t): pass

        reg = AgentRegistry()
        # Valid tools and wildcard '*'
        reg.register("agent1", DummyAgent, allowed_tools=["bash", "*"])
        meta = reg.get_meta("agent1")
        assert meta["allowed_tools"] == ["bash", "*"]

        # Unknown tool logs warning
        with patch("src.core.agent_registry.logger.warning") as mock_warn:
            reg.register("agent2", DummyAgent, allowed_tools=["completely_unknown_tool_xyz"])
            mock_warn.assert_called_once()
            assert "Unknown tool(s)" in mock_warn.call_args[0][0]

    def test_get_meta_missing(self) -> None:
        reg = AgentRegistry()
        meta = reg.get_meta("nonexistent")
        assert meta == {"allowed_tools": [], "spawnable_agents": []}

    def test_get_meta_obj_and_discover(self) -> None:
        class DummyAgent(AgentBase):
            """Dummy description"""
            def plan(self, x): return []
            def execute(self, t): pass

        reg = AgentRegistry()
        reg.register("agent_a", DummyAgent)
        obj = reg.get_meta_obj("agent_a")
        assert isinstance(obj, AgentMeta)
        assert obj.name == "agent_a"
        assert obj.description == "Dummy description"

        assert reg.get_meta_obj("missing") is None

        discovery = reg.discover()
        assert len(discovery) == 1
        assert discovery[0].name == "agent_a"

    def test_repr(self) -> None:
        reg = AgentRegistry()
        assert repr(reg) == "<AgentRegistry agents=[]>"

    def test_description_from_frontmatter(self) -> None:
        # No frontmatter start
        assert _description_from_frontmatter("Just text", "default") == "default"

        # Malformed frontmatter (less than 3 parts)
        assert _description_from_frontmatter("---\nonly one line", "default") == "default"

        # Valid with quoted description
        yaml_quoted = '---\ndescription: "Quoted agent description"\n---\nbody'
        assert _description_from_frontmatter(yaml_quoted, "default") == "Quoted agent description"

        # Valid with unquoted description
        yaml_unquoted = "---\ndescription: Plain unquoted description\n---\nbody"
        assert _description_from_frontmatter(yaml_unquoted, "default") == "Plain unquoted description"

        # Frontmatter without description field
        yaml_no_desc = "---\ntitle: Agent Title\n---\nbody"
        assert _description_from_frontmatter(yaml_no_desc, "default") == "default"

    def test_make_markdown_agent_class_plan_and_execute(self) -> None:
        agent_cls = _make_markdown_agent_class("writer", "Short prompt")
        agent = agent_cls(name="writer")

        # plan
        tasks = agent.plan("write an article")
        assert len(tasks) == 1
        assert tasks[0].id == "writer-1"

        # execute
        result = agent.execute(tasks[0])
        assert result.success is True
        assert "[WRITER] Short prompt" in result.output

        # Long prompt truncation in execute
        long_prompt = "x" * 300
        agent_cls2 = _make_markdown_agent_class("editor", long_prompt)
        agent2 = agent_cls2(name="editor")
        res2 = agent2.execute(tasks[0])
        assert res2.output.endswith("...")

    def test_register_known_agents(self) -> None:
        reg = AgentRegistry()
        _register_known_agents(reg)
        names = reg.list_agents()
        for expected in ["cto", "cmo", "coo", "cfo", "cso", "planner"]:
            assert expected in names

        # Calling again skips already registered
        _register_known_agents(reg)
        assert len(reg.list_agents()) == len(names)

    def test_discover_markdown_agents(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Nonexistent dir skips
        reg = AgentRegistry()
        monkeypatch.setattr("src.core.agent_registry.AGENTS_DIR", tmp_path / "no_such_dir")
        _discover_markdown_agents(reg)
        assert len(reg) == 0

        # Existing dir with .md files
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "scout.md").write_text(
            '---\ndescription: "Scout agent"\n---\nScout instructions',
            encoding="utf-8",
        )
        monkeypatch.setattr("src.core.agent_registry.AGENTS_DIR", agents_dir)
        _discover_markdown_agents(reg)
        assert "scout" in reg
        meta = reg.get_meta_obj("scout")
        assert meta.description == "Scout agent"

    def test_discover_markdown_agents_oserror(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        bad_md = agents_dir / "unreadable.md"
        bad_md.write_text("content", encoding="utf-8")

        orig_read = Path.read_text

        def mock_read(self, *args, **kwargs):
            if self.name == "unreadable.md":
                raise OSError("Cannot read file")
            return orig_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read)
        monkeypatch.setattr("src.core.agent_registry.AGENTS_DIR", agents_dir)

        reg = AgentRegistry()
        _discover_markdown_agents(reg)
        assert len(reg) == 0

    def test_get_registry_singleton(self) -> None:
        import src.core.agent_registry as reg_mod
        reg_mod._SINGLETON = None
        r1 = get_registry()
        assert r1 is not None
        r2 = get_registry()
        assert r1 is r2
