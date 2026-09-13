"""Tests for 100% statement and branch coverage of src/core/adapters/ memory adapters.

Covers:
- src/core/adapters/memory_store_adapter.py
- src/core/adapters/scoped_adapter.py
- src/core/adapters/seed_adapter.py
- src/core/adapters/pev_adapter.py
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from src.core.adapters.memory_store_adapter import MemoryStoreBridge
from src.core.adapters.pev_adapter import PevBridge
from src.core.adapters.scoped_adapter import ScopedBridge
from src.core.adapters.seed_adapter import SeedBridge
from src.core.memory_bridge import MemoryKind, MemoryRecord
from src.core.memory_scope import MemoryScope, ScopedMemoryEntry


# ============================================================================
# MemoryStoreBridge
# ============================================================================


class TestMemoryStoreBridgeCoverage:
    def test_search_semantic_with_matching_bridge_id_and_dedupe(self):
        bridge = MemoryStoreBridge()
        item = MemoryRecord(
            content="Task alpha execution",
            kind=MemoryKind.EPISODIC,
            agent_id="agent_1",
            metadata={"source": "unit_test"},
        )
        bid = bridge.record(item)

        # Mock semantic_search to return candidate with bridge_id
        mock_entry = MagicMock()
        mock_entry.context = {"bridge_id": bid, "agent_id": "agent_1", "kind": "episodic"}
        mock_entry.goal = "Task alpha execution"
        mock_entry.timestamp = 1234567.0

        with patch.object(bridge._store, "semantic_search", return_value=[mock_entry]):
            results = bridge.search("Task", limit=5)
            assert len(results) >= 1
            assert results[0].agent_id == "agent_1"

    def test_search_semantic_exception_suppressed(self):
        bridge = MemoryStoreBridge()
        with patch.object(bridge._store, "semantic_search", side_effect=RuntimeError("Vector DB down")):
            # Should not raise, falls back to text search
            results = bridge.search("anything")
            assert isinstance(results, list)

    def test_search_semantic_dict_entry_and_foreign_bridge_id(self):
        bridge = MemoryStoreBridge()
        item = MemoryRecord(content="Task test", kind=MemoryKind.EPISODIC)
        bid = bridge.record(item)

        dict_entry_valid = {
            "context": {"bridge_id": bid, "kind": "episodic"},
            "goal": "Task test",
            "timestamp": 12345.0,
        }
        dict_entry_foreign = {
            "context": {"bridge_id": "foreign_unknown_id"},
            "goal": "Foreign task",
        }
        raw_non_dict = 42

        with patch.object(
            bridge._store,
            "semantic_search",
            return_value=[dict_entry_valid, dict_entry_foreign, raw_non_dict],
        ):
            results = bridge.search("Task", limit=5)
            assert len(results) >= 1
            assert results[0].content == "Task test"

    def test_search_entry_object_branch_and_limit_break(self):
        bridge = MemoryStoreBridge()
        item1 = MemoryRecord(content="Task one", kind=MemoryKind.EPISODIC, agent_id="a1")
        item2 = MemoryRecord(content="Task two", kind=MemoryKind.EPISODIC, agent_id="a1")
        bid1 = bridge.record(item1)
        bid2 = bridge.record(item2)

        # Mock semantic search returning 2 valid entry objects
        mock_entry1 = MagicMock()
        mock_entry1.context = {"bridge_id": bid1, "agent_id": "a1", "kind": "episodic"}
        mock_entry1.goal = "Task one"
        mock_entry1.timestamp = 100.0

        mock_entry2 = MagicMock()
        mock_entry2.context = {"bridge_id": bid2, "agent_id": "a1", "kind": "episodic"}
        mock_entry2.goal = "Task two"
        mock_entry2.timestamp = 200.0

        with patch.object(bridge._store, "semantic_search", return_value=[mock_entry1, mock_entry2]):
            # limit=1 forces the `if len(records) >= limit: break`
            results = bridge.search("Task", limit=1)
            assert len(results) == 1

    def test_search_filtering_branches_and_fallback_text_continue(self):
        bridge = MemoryStoreBridge()
        rec = MemoryRecord(
            content="Alpha beta gamma",
            kind=MemoryKind.SEMANTIC,
            agent_id="bot1",
            session_id="s1",
            user_id="u1",
        )
        bid = bridge.record(rec)

        # Mismatched agent_id
        assert bridge.search("Alpha", agent_id="bot2") == []
        # Mismatched session_id
        assert bridge.search("Alpha", session_id="s2") == []
        # Mismatched user_id
        assert bridge.search("Alpha", user_id="u2") == []
        # Mismatched kind
        assert bridge.search("Alpha", kind=MemoryKind.WORKING) == []
        # Matched
        assert len(bridge.search("Alpha", agent_id="bot1", session_id="s1", user_id="u1", kind=MemoryKind.SEMANTIC)) == 1

        # Fallback text search mismatch triggers `if q and q not in goal.lower(): continue` (line 116)
        assert bridge.search("NonExistentTermXYZ") == []

        # Recall triggers line 129
        recall_res = bridge.recall("Alpha", k=2, agent_id="bot1")
        assert len(recall_res) == 1
        assert recall_res[0]["content"] == "Alpha beta gamma"

        # Delete existing and non-existing triggers lines 156-159
        assert bridge.delete(bid) is True
        assert bridge.delete("non_existent_bid") is False

        # Prune expired triggers line 170
        with patch.object(bridge._store, "compress_old_memories", return_value=5):
            assert bridge.prune_expired() == 5

    def test_fallback_text_search_without_context_or_goal(self):
        bridge = MemoryStoreBridge()
        dummy_entry = object()
        bridge._id_map["dummy_bid"] = dummy_entry
        # Should handle object without context or goal safely
        results = bridge.search("anything")
        assert isinstance(results, list)

    def test_recent_scoping_branches(self):
        bridge = MemoryStoreBridge()
        rec1 = MemoryRecord(content="R1", kind=MemoryKind.EPISODIC, agent_id="a1")
        rec2 = MemoryRecord(content="R2", kind=MemoryKind.SEMANTIC, agent_id="a2")
        bridge.record(rec1)
        bridge.record(rec2)

        # Filter by agent_id mismatch
        results_agent = bridge.recent(agent_id="a2")
        assert all(r.agent_id == "a2" for r in results_agent)

        # Filter by kind mismatch
        results_kind = bridge.recent(kind=MemoryKind.SEMANTIC)
        assert all(r.kind == MemoryKind.SEMANTIC for r in results_kind)

        # Limit break
        results_limit = bridge.recent(limit=1)
        assert len(results_limit) <= 1

    def test_stats_exception_handled(self):
        bridge = MemoryStoreBridge()
        with patch.object(bridge._store, "stats", side_effect=Exception("stats error")):
            st = bridge.stats()
            assert st["backend"] == "memory_store"
            assert "count" in st

    def test_dict_to_record_invalid_kind_fallback(self):
        d = {"context": {"kind": "invalid_kind_value", "goal": "Sample goal"}}
        record = MemoryStoreBridge._dict_to_record(d)
        assert record.kind == MemoryKind.EPISODIC
        assert record.content == "Sample goal"

    def test_entry_to_record_invalid_kind_fallback(self):
        mock_entry = MagicMock()
        mock_entry.context = {"kind": "corrupted_kind", "agent_id": "test"}
        mock_entry.goal = "Corrupted goal"
        mock_entry.timestamp = None
        record = MemoryStoreBridge._entry_to_record(mock_entry)
        assert record.kind == MemoryKind.EPISODIC
        assert record.content == "Corrupted goal"
        assert record.created_at == 0.0


# ============================================================================
# ScopedBridge
# ============================================================================


class TestScopedBridgeCoverage:
    def test_search_filters_and_limit_break(self):
        bridge = ScopedBridge()
        r1 = MemoryRecord(
            content="Scoped content target 1",
            kind=MemoryKind.SEMANTIC,
            agent_id="sc_agent",
            session_id="sc_sess",
            user_id="sc_user",
        )
        r2 = MemoryRecord(
            content="Scoped content target 2",
            kind=MemoryKind.EPISODIC,
            agent_id="sc_agent",
            session_id="sc_sess",
            user_id="other_user",
        )
        r3 = MemoryRecord(
            content="Scoped content target 3",
            kind=MemoryKind.EPISODIC,
            agent_id="sc_agent",
            session_id="sc_sess",
            user_id=None,
        )
        key1 = bridge.record(r1)
        key2 = bridge.record(r2)
        key3 = bridge.record(r3)

        # Query mismatch (line 73)
        assert bridge.search("nomatch_xyz") == []

        # Kind mismatch (line 75)
        assert bridge.search("Scoped", kind=MemoryKind.WORKING) == []

        # Session mismatch (line 77)
        assert bridge.search("Scoped", session_id="wrong_sess") == []

        # User mismatch (line 79) - r3 has user_id=None so it passes validate_access, then hits line 79
        assert bridge.search("Scoped", user_id="nonexistent_user") == []

        # Limit break (lines 86-87)
        res_limit = bridge.search("Scoped", limit=1)
        assert len(res_limit) == 1

        # Recall (line 96)
        recall_res = bridge.recall("Scoped", k=2)
        assert len(recall_res) >= 1

        # Delete existing (lines 130-140)
        assert bridge.delete(key1) is True
        assert bridge.delete(key2) is True
        assert bridge.delete(key3) is True

        # Stats (line 143)
        st = bridge.stats()
        assert st["backend"] == "scoped"

        # Prune expired (line 146)
        with patch.object(bridge._store, "prune_expired", return_value=0):
            assert bridge.prune_expired() == 0

    def test_search_and_recent_with_non_dict_entry_value(self):
        bridge = ScopedBridge()
        entry = ScopedMemoryEntry(
            key="raw_val_key",
            value="plain non dict string",
            scope=MemoryScope(),
        )
        bridge._store.store(entry)
        bridge._key_scope["raw_val_key"] = bridge._store._scope_key(MemoryScope())

        # search reaches non-dict value in loop
        results = bridge.search("plain")
        assert len(results) >= 1
        assert results[0].content == "plain non dict string"

        # recent reaches non-dict value in loop
        recents = bridge.recent()
        assert len(recents) >= 1

    def test_recent_kind_mismatch_and_limit_break(self):
        bridge = ScopedBridge()
        r1 = MemoryRecord(content="Recent 1", kind=MemoryKind.EPISODIC)
        r2 = MemoryRecord(content="Recent 2", kind=MemoryKind.SEMANTIC)
        r3 = MemoryRecord(content="Recent 3", kind=MemoryKind.SEMANTIC)
        bridge.record(r1)
        bridge.record(r2)
        bridge.record(r3)

        # Filter by SEMANTIC kind skips EPISODIC
        results = bridge.recent(kind=MemoryKind.SEMANTIC, limit=1)
        assert len(results) == 1
        assert results[0].kind == MemoryKind.SEMANTIC

    def test_delete_missing_key_returns_false(self):
        bridge = ScopedBridge()
        assert bridge.delete("non_existent_key") is False

    def test_delete_short_scope_key_and_delete_failure(self):
        bridge = ScopedBridge()
        # 1. key in _key_scope with fewer than 5 parts
        bridge._key_scope["short_key"] = "only|three|parts"
        # store does not have short_key, so delete returns False
        assert bridge.delete("short_key") is False

    def test_dict_to_record_non_dict_value_branch(self):
        raw_dict = {"value": "plain text value", "created_at": 100.0}
        rec = ScopedBridge._dict_to_record(raw_dict)
        assert rec.content == "plain text value"
        assert rec.kind == MemoryKind.EPISODIC
        assert rec.created_at == 100.0

    def test_dict_to_record_invalid_kind_fallback(self):
        raw_dict = {"value": {"content": "text", "kind": "unrecognized_kind"}}
        rec = ScopedBridge._dict_to_record(raw_dict)
        assert rec.kind == MemoryKind.EPISODIC


# ============================================================================
# SeedBridge
# ============================================================================


class TestSeedBridgeCoverage:
    def test_record_with_ttl_and_search_all_filters(self, tmp_path):
        db_path = str(tmp_path / "seed_mem_search.db")
        bridge = SeedBridge(path=db_path)

        # Record with ttl_seconds (line 34)
        rec = MemoryRecord(
            content="Searchable seed item",
            kind=MemoryKind.SEMANTIC,
            agent_id="seed_ag",
            session_id="seed_sess",
            user_id="seed_usr",
            ttl_seconds=3600,
        )
        doc_id = bridge.record(rec)

        # Search matching (lines 53-66)
        res = bridge.search(
            "Searchable",
            kind=MemoryKind.SEMANTIC,
            agent_id="seed_ag",
            session_id="seed_sess",
            user_id="seed_usr",
        )
        assert len(res) >= 1
        assert res[0].content == "Searchable seed item"

        # Search agent mismatch
        assert bridge.search("Searchable", agent_id="other_ag") == []
        # Search kind mismatch
        assert bridge.search("Searchable", kind=MemoryKind.EPISODIC) == []
        # Search session mismatch
        assert bridge.search("Searchable", session_id="other_sess") == []
        # Search user mismatch
        assert bridge.search("Searchable", user_id="other_usr") == []

        # Successful delete (lines 120-121)
        assert bridge.delete(doc_id) is True

        # Stats without exception (lines 130-134)
        st = bridge.stats()
        assert st["backend"] == "seed"
        assert isinstance(st["count"], int)

        # Prune expired (line 141)
        assert bridge.prune_expired() == 0

    def test_search_and_recent_and_recall_optional_filters_none(self, tmp_path):
        db_path = str(tmp_path / "seed_opt.db")
        bridge = SeedBridge(path=db_path)
        rec = MemoryRecord(content="Optional test entry")
        bridge.record(rec)

        # search with no filters (all None)
        res = bridge.search("Optional")
        assert len(res) >= 1

        # recall with agent_id=None
        recalls = bridge.recall("Optional", agent_id=None)
        assert len(recalls) >= 1

        # recent with kind=None, agent_id=None
        recents = bridge.recent(kind=None, agent_id=None, limit=10)
        assert len(recents) >= 1

    def test_recall_with_agent_id_filtering(self, tmp_path):
        db_path = str(tmp_path / "seed_mem.db")
        bridge = SeedBridge(path=db_path)
        rec1 = MemoryRecord(content="Seed entry 1", agent_id="agent_x")
        rec2 = MemoryRecord(content="Seed entry 2", agent_id="agent_y")
        bridge.record(rec1)
        bridge.record(rec2)

        results_x = bridge.recall("Seed", agent_id="agent_x")
        assert len(results_x) >= 1
        assert all(r.get("agent_id") == "agent_x" for r in results_x)

    def test_recent_kind_and_agent_id_filtering_and_limit_break(self, tmp_path):
        db_path = str(tmp_path / "seed_mem.db")
        bridge = SeedBridge(path=db_path)
        r1 = MemoryRecord(content="Rec 1", kind=MemoryKind.SEMANTIC, agent_id="ag1")
        r2 = MemoryRecord(content="Rec 2", kind=MemoryKind.EPISODIC, agent_id="ag1")
        r3 = MemoryRecord(content="Rec 3", kind=MemoryKind.SEMANTIC, agent_id="ag2")
        bridge.record(r1)
        bridge.record(r2)
        bridge.record(r3)

        # Filter by kind=SEMANTIC and agent_id=ag1
        res = bridge.recent(kind=MemoryKind.SEMANTIC, agent_id="ag1", limit=1)
        assert len(res) == 1
        assert res[0].kind == MemoryKind.SEMANTIC
        assert res[0].agent_id == "ag1"

    def test_delete_exceptions_and_not_found(self, tmp_path):
        db_path = str(tmp_path / "seed_mem.db")
        bridge = SeedBridge(path=db_path)

        # 1. Connection retrieval exception
        with patch.object(bridge._db, "_conn_ref", side_effect=Exception("conn error")):
            assert bridge.delete("any_id") is False

        # 2. Key not found in DB
        assert bridge.delete("definitely_nonexistent_key_12345") is False

        # 3. DELETE execution failure
        rec = MemoryRecord(content="Delete test failure entry")
        doc_id = bridge.record(rec)
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = [MagicMock(fetchone=lambda: (doc_id,)), RuntimeError("delete fail")]
        with patch.object(bridge._db, "_conn_ref", return_value=mock_conn):
            assert bridge.delete(doc_id) is False

    def test_stats_exception_handled(self, tmp_path):
        db_path = str(tmp_path / "seed_mem.db")
        bridge = SeedBridge(path=db_path)
        with patch.object(bridge._db, "_conn_ref", side_effect=Exception("db closed")):
            st = bridge.stats()
            assert st["count"] == 0
            assert st["backend"] == "seed"

    def test_dict_to_record_none_metadata(self):
        r = {"content": "no meta", "metadata": None}
        rec = SeedBridge._dict_to_record(r)
        assert rec.content == "no meta"
        assert rec.kind == MemoryKind.EPISODIC

    def test_dict_to_record_invalid_kind_fallback(self):
        r = {"content": "seed text", "metadata": {"kind": "corrupted_kind"}}
        rec = SeedBridge._dict_to_record(r)
        assert rec.kind == MemoryKind.EPISODIC


# ============================================================================
# PevBridge
# ============================================================================


class TestPevBridgeCoverage:
    def test_init_without_pev_fallback(self):
        with patch.dict(sys.modules, {"src.harness.pev.memory": None}):
            bridge = PevBridge()
            assert bridge._has_pev is False
            assert bridge._store is None

    def test_fallback_store_record_and_search_all_filters(self):
        bridge = PevBridge()
        # Force fallback mode
        bridge._has_pev = False
        bridge._store = None

        item1 = MemoryRecord(
            content="Fallback content 1",
            kind=MemoryKind.SEMANTIC,
            agent_id="bot1",
            session_id="sess1",
            user_id="user1",
            metadata={"m": 1},
        )
        item2 = MemoryRecord(
            content="Fallback content 2",
            kind=MemoryKind.EPISODIC,
            agent_id="bot2",
            session_id="sess2",
            user_id="user2",
        )
        k1 = bridge.record(item1)
        k2 = bridge.record(item2)
        assert k1 in bridge._fallback_store
        assert k2 in bridge._fallback_store

        # Search query mismatch
        assert bridge.search("nomatch") == []

        # Search kind mismatch
        assert bridge.search("Fallback", kind=MemoryKind.WORKING) == []

        # Search agent_id mismatch
        assert bridge.search("Fallback", agent_id="bot3") == []

        # Search session_id mismatch
        assert bridge.search("Fallback", session_id="sess3") == []

        # Search user_id mismatch
        assert bridge.search("Fallback", user_id="user3") == []

        # Limit break
        res_limit = bridge.search("Fallback", limit=1)
        assert len(res_limit) == 1

        # Non-dict entry in fallback store
        bridge._fallback_store["raw_str"] = "just a string"
        res_str = bridge.search("just a string")
        assert len(res_str) >= 1
        assert res_str[0].content == "just a string"

        # Delete in fallback mode
        assert bridge.delete(k1) is True
        assert bridge.delete("non_existent_key") is False

    def test_search_with_pev_entry_validation_and_limit_break(self):
        bridge = PevBridge()
        if not bridge._has_pev or bridge._store is None:
            return

        # Record multiple items
        item = MemoryRecord(
            content="Pev test unique item",
            kind=MemoryKind.SEMANTIC,
            agent_id="pev_bot",
            session_id="pev_sess",
            user_id="pev_usr",
        )
        eid = bridge.record(item)

        # Filters under PEV mode (lines 72, 74, 76, 78, 80)
        assert bridge.search("nomatch_pev") == []
        assert bridge.search("Pev test", kind=MemoryKind.WORKING) == []
        assert bridge.search("Pev test", agent_id="other_bot") == []
        assert bridge.search("Pev test", session_id="other_sess") == []
        assert bridge.search("Pev test", user_id="other_usr") == []

        # Recall and recent (lines 121, 134)
        assert len(bridge.recall("Pev test")) >= 1
        assert len(bridge.recent()) >= 1

        # Delete successful under PEV mode (line 142)
        assert bridge.delete(eid) is True

        # Prune expired (line 158)
        assert bridge.prune_expired() == 0

        # Limit break in search
        for i in range(5):
            bridge.record(MemoryRecord(content=f"Pev test item {i}"))
        res = bridge.search("Pev test", limit=2)
        assert len(res) == 2

        # Non-dict entry.value or None entry skipped
        mock_store = MagicMock()
        mock_entry_none = None
        mock_entry_non_dict = MagicMock(value="not a dict")
        mock_valid_entry = MagicMock(
            value={"content": "valid match", "kind": "episodic", "metadata": {}},
            created_at=MagicMock(timestamp=lambda: 100.0),
        )
        mock_store._store = {"k1": 1, "k2": 2, "k3": 3}
        mock_store.recall.side_effect = [mock_entry_none, mock_entry_non_dict, mock_valid_entry]

        with patch.object(bridge, "_store", mock_store):
            results = bridge.search("valid", limit=5)
            assert len(results) == 1
            assert results[0].content == "valid match"

    def test_delete_exception_handled(self):
        bridge = PevBridge()
        if bridge._has_pev and bridge._store is not None:
            with patch.object(bridge._store, "forget", side_effect=Exception("forget error")):
                assert bridge.delete("k") is False

    def test_stats_fallback_and_attribute_error(self):
        bridge = PevBridge()
        # Fallback stats (has_pev is False)
        bridge._has_pev = False
        bridge._store = None
        st = bridge.stats()
        assert st["backend"] == "pev"
        assert st["has_pev"] is False

        # has_pev True but store raises AttributeError on _store access
        bridge._has_pev = True
        mock_store = MagicMock(spec=[])  # No attributes, raises AttributeError on ._store
        bridge._store = mock_store
        st2 = bridge.stats()
        assert st2["backend"] == "pev"

    def test_stats_store_exception_handled(self):
        bridge = PevBridge()
        if bridge._has_pev and bridge._store is not None:
            mock_store = MagicMock()
            type(mock_store)._store = property(lambda self: (_ for _ in ()).throw(TypeError("len error")))
            with patch.object(bridge, "_store", mock_store):
                st = bridge.stats()
                assert st["backend"] == "pev"

    def test_entry_to_record_invalid_kind_fallback(self):
        mock_entry = MagicMock()
        mock_entry.value = {"content": "text", "kind": "unknown_pev_kind"}
        mock_entry.created_at = None
        rec = PevBridge._entry_to_record(mock_entry, "k")
        assert rec.kind == MemoryKind.EPISODIC
        assert rec.created_at == 0.0
