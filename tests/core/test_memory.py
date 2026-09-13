"""Tests for MemoryStore execution memory."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.memory_canonical import MemoryEntry, MemoryStore
import src.core.memory_canonical as _mc

pytestmark = pytest.mark.usefixtures("restore_real_memory_store")


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry dataclass."""

    def test_memory_entry_creation(self):
        """Default fields are populated correctly."""
        entry = MemoryEntry(goal="deploy app", status="success")
        self.assertEqual(entry.goal, "deploy app")
        self.assertEqual(entry.status, "success")
        self.assertGreater(entry.timestamp, 0)
        self.assertEqual(entry.duration_ms, 0.0)
        self.assertEqual(entry.error_summary, "")
        self.assertEqual(entry.recipe_used, "")
        self.assertEqual(entry.context, {})
        self.assertEqual(entry.reflection, "")

    def test_memory_entry_with_error_and_context(self):
        """Custom fields are stored properly."""
        entry = MemoryEntry(
            goal="build",
            status="failed",
            duration_ms=123.4,
            error_summary="exit code 1",
            recipe_used="build-recipe",
            context={"env": "prod"},
            reflection="Need retry logic",
        )
        self.assertEqual(entry.error_summary, "exit code 1")
        self.assertEqual(entry.recipe_used, "build-recipe")
        self.assertEqual(entry.context["env"], "prod")
        self.assertEqual(entry.reflection, "Need retry logic")


class TestMemoryStore(unittest.TestCase):
    """Test MemoryStore persistence, queries, vector index, and compression."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._path = str(Path(self._tmpdir) / "memory.yaml")
        self.store = MemoryStore(store_path=self._path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_init_default_path(self):
        """Default store path points to .mekong/memory.yaml."""
        with patch.object(MemoryStore, "_load"):
            with patch.object(MemoryStore, "_vector_store", create=True):
                s = MemoryStore()
                self.assertEqual(s._path, Path(".mekong/memory.yaml"))

    def test_init_vector_store_error_handled(self):
        """Vector collection creation failure logs warning and does not raise."""
        with patch("src.core.memory_canonical.VectorMemoryStore.get_or_create_collection", side_effect=RuntimeError("vec err")):
            s = MemoryStore(store_path=self._path)
            self.assertIsNotNone(s._vector_store)

    def test_record_and_query_substring(self):
        """Record entries and query by substring."""
        self.store.record(MemoryEntry(goal="deploy app", status="success"))
        self.store.record(MemoryEntry(goal="deploy api", status="failed"))
        self.store.record(MemoryEntry(goal="build project", status="success"))

        results = self.store.query("deploy")
        self.assertEqual(len(results), 2)

    def test_query_case_insensitive(self):
        """Query matches case-insensitively."""
        self.store.record(MemoryEntry(goal="Deploy App", status="success"))
        results = self.store.query("deploy")
        self.assertEqual(len(results), 1)

    def test_record_with_recipe_used_procedural_type(self):
        """Recording entry with recipe_used indexes as PROCEDURAL memory type."""
        entry = MemoryEntry(goal="deploy recipe", status="success", recipe_used="deploy_sh")
        self.store.record(entry)
        self.assertEqual(len(self.store._entries), 1)

    def test_record_facade_integration_success_and_error(self):
        """External facade add called when facade is available; errors handled gracefully."""
        mock_facade = MagicMock()
        with patch("src.core.memory_canonical._FACADE_AVAILABLE", True):
            with patch("src.core.memory_canonical._get_facade", return_value=mock_facade):
                entry = MemoryEntry(goal="deploy", status="success", error_summary="none", recipe_used="rec1")
                self.store.record(entry)
                mock_facade.add.assert_called_once()

                # Exception in facade.add handled gracefully
                mock_facade.add.side_effect = RuntimeError("facade dead")
                entry2 = MemoryEntry(goal="deploy2", status="failed")
                self.store.record(entry2)  # Should not raise

    def test_record_index_entry_exception_handled(self):
        """Exception during _index_entry vector upsert is silently suppressed."""
        with patch.object(self.store._vector_store, "upsert", side_effect=Exception("upsert fail")):
            # Must not raise
            self.store.record(MemoryEntry(goal="deploy", status="success"))

    def test_query_facade_fallback(self):
        """Query falls back to external facade when semantic vector returns empty."""
        self.store.record(MemoryEntry(goal="deploy backend", status="success"))

        mock_facade = MagicMock()
        mock_facade.search.return_value = [
            {"memory": "something goal=deploy backend status=success"}
        ]
        with patch.object(self.store, "_semantic_search", return_value=[]):
            with patch("src.core.memory_canonical._FACADE_AVAILABLE", True):
                with patch("src.core.memory_canonical._get_facade", return_value=mock_facade):
                    hits = self.store.query("deploy")
                    self.assertEqual(len(hits), 1)
                    self.assertEqual(hits[0].goal, "deploy backend")

                    # Exception in facade search falls through to substring
                    mock_facade.search.side_effect = RuntimeError("search err")
                    hits_err = self.store.query("deploy")
                    self.assertEqual(len(hits_err), 1)

    def test_semantic_search_method(self):
        """semantic_search public method delegates to _semantic_search."""
        with patch.object(self.store, "_semantic_search", return_value=[MemoryEntry(goal="g", status="success")]) as mock_sem:
            res = self.store.semantic_search("g", top_k=5)
            self.assertEqual(len(res), 1)
            mock_sem.assert_called_once_with("g", 5)

    def test_internal_semantic_search_empty_low_score_and_error(self):
        """_semantic_search handles empty results, low scores (<0.3), and exceptions."""
        # 1. Empty results
        with patch.object(self.store._vector_store, "search", return_value=[]):
            self.assertEqual(self.store._semantic_search("anything"), [])

        # 2. Score < 0.3 filtered out
        mock_vec_entry = MagicMock()
        mock_vec_entry.payload = {"goal": "test goal"}
        with patch.object(self.store._vector_store, "search", return_value=[(mock_vec_entry, 0.2)]):
            self.assertEqual(self.store._semantic_search("anything"), [])

        # 3. Score >= 0.3 matching entry
        self.store._entries = [MemoryEntry(goal="test goal", status="success")]
        with patch.object(self.store._vector_store, "search", return_value=[(mock_vec_entry, 0.85)]):
            res = self.store._semantic_search("anything")
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].goal, "test goal")

        # 4. Exception in search
        with patch.object(self.store._vector_store, "search", side_effect=RuntimeError("vec search err")):
            self.assertEqual(self.store._semantic_search("anything"), [])

    def test_get_similar_successes(self):
        """Returns successful entries from semantic search."""
        e1 = MemoryEntry(goal="deploy a", status="success")
        e2 = MemoryEntry(goal="deploy b", status="failed")
        e3 = MemoryEntry(goal="deploy c", status="success")
        with patch.object(self.store, "_semantic_search", return_value=[e1, e2, e3]):
            sim = self.store.get_similar_successes("deploy", top_k=2)
            self.assertEqual(len(sim), 2)
            self.assertEqual(sim[0].goal, "deploy a")
            self.assertEqual(sim[1].goal, "deploy c")

    def test_success_rate_all(self):
        """Global success rate calculated correctly."""
        self.store.record(MemoryEntry(goal="a", status="success"))
        self.store.record(MemoryEntry(goal="b", status="success"))
        self.store.record(MemoryEntry(goal="c", status="failed"))

        rate = self.store.get_success_rate()
        self.assertAlmostEqual(rate, 66.67, places=1)

    def test_success_rate_filtered(self):
        """Filtered success rate for specific pattern."""
        self.store.record(MemoryEntry(goal="deploy x", status="success"))
        self.store.record(MemoryEntry(goal="deploy y", status="failed"))
        self.store.record(MemoryEntry(goal="build z", status="success"))

        rate = self.store.get_success_rate("deploy")
        self.assertAlmostEqual(rate, 50.0, places=1)

    def test_empty_success_rate(self):
        """Success rate returns 0 for empty store."""
        self.assertEqual(self.store.get_success_rate(), 0.0)

    def test_get_last_failure(self):
        """Returns most recent failed entry."""
        self.store.record(MemoryEntry(goal="x", status="failed", error_summary="err1"))
        self.store.record(MemoryEntry(goal="x", status="success"))
        self.store.record(MemoryEntry(goal="x", status="failed", error_summary="err2"))

        failure = self.store.get_last_failure("x")
        self.assertIsNotNone(failure)
        self.assertEqual(failure.error_summary, "err2")

    def test_get_last_failure_none(self):
        """Returns None if no failures."""
        self.store.record(MemoryEntry(goal="x", status="success"))
        self.assertIsNone(self.store.get_last_failure("x"))

    def test_suggest_fix_with_history(self):
        """Returns error patterns from failures."""
        self.store.record(MemoryEntry(goal="deploy", status="failed", error_summary="timeout"))
        self.store.record(MemoryEntry(goal="deploy", status="failed", error_summary="auth error"))

        suggestion = self.store.suggest_fix("deploy")
        self.assertIn("timeout", suggestion)

    def test_suggest_fix_no_history(self):
        """Returns no-history message for unknown goals."""
        suggestion = self.store.suggest_fix("unknown")
        self.assertIn("No failure history", suggestion)

    def test_suggest_fix_no_error_details(self):
        """Returns message when failures exist but have empty error_summary."""
        self.store.record(MemoryEntry(goal="quiet_goal", status="failed", error_summary=""))
        suggestion = self.store.suggest_fix("quiet_goal")
        self.assertIn("no error details recorded", suggestion)

    def test_recent_default_limit(self):
        """Returns last 20 entries by default."""
        for i in range(25):
            self.store.record(MemoryEntry(goal=f"g{i}", status="success"))

        recent = self.store.recent()
        self.assertEqual(len(recent), 20)
        self.assertEqual(recent[-1].goal, "g24")

    def test_stats_structure(self):
        """Stats contain required keys and vector store metadata."""
        self.store.record(MemoryEntry(goal="a", status="success"))
        self.store.record(MemoryEntry(goal="a", status="failed"))

        s = self.store.stats()
        self.assertIn("total", s)
        self.assertIn("success_rate", s)
        self.assertIn("top_goals", s)
        self.assertIn("recent_failures", s)
        self.assertIn("vector_entries", s)
        self.assertIn("memory_types", s)
        self.assertEqual(s["total"], 2)

    def test_stats_vector_store_exception_handled(self):
        """Stats handles vector store get_collection_info exception."""
        with patch.object(self.store._vector_store, "get_collection_info", side_effect=Exception("info err")):
            s = self.store.stats()
            self.assertEqual(s["vector_entries"], 0)

    def test_compress_old_memories(self):
        """Compresses old memory entries into summaries."""
        # 1. entries <= keep_recent
        self.assertEqual(self.store.compress_old_memories(keep_recent=10), 0)

        # 2. entries > keep_recent, but none older than threshold
        for i in range(5):
            self.store._entries.append(MemoryEntry(goal=f"recent_{i}", status="success", timestamp=time.time()))
        self.assertEqual(self.store.compress_old_memories(days_threshold=7, keep_recent=2), 0)

        # 3. old entries < 3 per goal -> not compressed
        old_time = time.time() - (10 * 86400)
        self.store._entries = [
            MemoryEntry(goal="solo", status="success", timestamp=old_time),
            MemoryEntry(goal="solo", status="failed", timestamp=old_time),
            MemoryEntry(goal="recent", status="success", timestamp=time.time()),
        ]
        self.assertEqual(self.store.compress_old_memories(days_threshold=7, keep_recent=1), 0)

        # 4. old entries >= 3 per goal -> compressed
        self.store._entries = [
            MemoryEntry(goal="batch_job", status="success", duration_ms=10.0, timestamp=old_time),
            MemoryEntry(goal="batch_job", status="success", duration_ms=20.0, timestamp=old_time + 1),
            MemoryEntry(goal="batch_job", status="failed", duration_ms=30.0, error_summary="err1", timestamp=old_time + 2),
            MemoryEntry(goal="batch_job", status="failed", duration_ms=40.0, error_summary="err2", timestamp=old_time + 3),
            MemoryEntry(goal="recent", status="success", timestamp=time.time()),
        ]
        compressed = self.store.compress_old_memories(days_threshold=7, keep_recent=1)
        self.assertEqual(compressed, 4)
        # Should now have 2 entries: 1 summary entry + 1 recent entry
        self.assertEqual(len(self.store._entries), 2)
        summary = self.store._entries[0]
        self.assertTrue(summary.context.get("compressed"))
        self.assertEqual(summary.context.get("original_count"), 4)

    def test_persistence_roundtrip(self):
        """Data survives save/load cycle."""
        path = str(Path(self._tmpdir) / "roundtrip.yaml")
        store1 = MemoryStore(store_path=path)
        store1.record(MemoryEntry(goal="test", status="success", duration_ms=42.0))
        store1._save()

        store2 = MemoryStore(store_path=path)
        self.assertEqual(len(store2._entries), 1)
        self.assertEqual(store2._entries[0].goal, "test")
        self.assertAlmostEqual(store2._entries[0].duration_ms, 42.0)

    def test_load_corrupted_yaml(self):
        """Corrupted YAML falls back to empty entries list."""
        path = Path(self._tmpdir) / "corrupt.yaml"
        path.write_text("invalid : [ yaml : content")
        s = MemoryStore(store_path=str(path))
        self.assertEqual(s._entries, [])

    def test_fifo_eviction(self):
        """Oldest entries evicted when exceeding MAX_ENTRIES."""
        self.store.MAX_ENTRIES = 10
        for i in range(15):
            self.store.record(MemoryEntry(goal=f"g{i}", status="success"))

        self.assertEqual(len(self.store._entries), 10)
        self.assertEqual(self.store._entries[0].goal, "g5")

    def test_clear(self):
        """Clear empties store, deletes file, and recreates vector collection."""
        self.store.record(MemoryEntry(goal="x", status="success"))
        self.assertTrue(Path(self._path).exists())

        self.store.clear()
        self.assertEqual(len(self.store._entries), 0)
        self.assertFalse(Path(self._path).exists())

    def test_clear_vector_store_error_handled(self):
        """Vector store deletion/creation error during clear is handled gracefully."""
        with patch.object(self.store._vector_store, "delete_collection", side_effect=Exception("del err")):
            # Must not raise
            self.store.clear()


    def test_query_semantic_search_hit(self):
        """Query returns semantic vector search results directly when available."""
        entry = MemoryEntry(goal="vector match", status="success")
        with patch.object(self.store, "_semantic_search", return_value=[entry]):
            res = self.store.query("something")
            self.assertEqual(res, [entry])

    def test_facade_unavailable_branch(self):
        """Module handles ImportError when packages.memory.memory_facade is not importable."""
        import importlib
        import sys
        with patch.dict(sys.modules, {"packages.memory.memory_facade": None}):
            importlib.reload(_mc)
            self.assertFalse(_mc._FACADE_AVAILABLE)
        # Restore normal state
        importlib.reload(_mc)
        self.assertTrue(_mc._FACADE_AVAILABLE)


if __name__ == "__main__":
    unittest.main()
