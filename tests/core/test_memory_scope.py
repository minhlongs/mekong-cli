"""Tests for multi-scope memory tagging (src/core/memory_scope.py)."""

import time
import unittest

from src.core.memory_scope import (
    MemoryScope,
    ScopedMemoryEntry,
    ScopedMemoryStore,
    validate_access,
)


def _scope(**kwargs) -> MemoryScope:
    return MemoryScope(app_id="mekong", **kwargs)


def _entry(key: str, value: object, scope: MemoryScope, ttl: int | None = None) -> ScopedMemoryEntry:
    return ScopedMemoryEntry(key=key, value=value, scope=scope, ttl=ttl)


class TestValidateAccess(unittest.TestCase):
    def test_same_scope_allowed(self):
        s = _scope(agent_id="a1")
        self.assertTrue(validate_access(s, s))

    def test_different_app_denied(self):
        r = MemoryScope(app_id="other")
        t = MemoryScope(app_id="mekong")
        self.assertFalse(validate_access(r, t))

    def test_shared_entry_readable_by_any_agent(self):
        shared_scope = _scope(agent_id=None)
        requestor = _scope(agent_id="agent-x")
        self.assertTrue(validate_access(requestor, shared_scope))

    def test_agent_private_entry_denied_to_other_agent(self):
        owner = _scope(agent_id="agent-a")
        other = _scope(agent_id="agent-b")
        self.assertFalse(validate_access(other, owner))

    def test_org_mismatch_denied(self):
        r = _scope(org_id="org1")
        t = _scope(org_id="org2")
        self.assertFalse(validate_access(r, t))

    def test_user_mismatch_denied(self):
        r = _scope(org_id="org1", user_id="alice")
        t = _scope(org_id="org1", user_id="bob")
        self.assertFalse(validate_access(r, t))


class TestScopedMemoryStoreBasic(unittest.TestCase):
    def setUp(self):
        self.store = ScopedMemoryStore()
        self.scope = _scope(agent_id="agent-1", session_id="s1")

    def test_store_and_retrieve(self):
        entry = _entry("k", "hello", self.scope)
        self.store.store(entry)
        result = self.store.retrieve("k", self.scope)
        self.assertIsNotNone(result)
        self.assertEqual(result.value, "hello")

    def test_retrieve_missing_key_returns_none(self):
        self.assertIsNone(self.store.retrieve("nonexistent", self.scope))

    def test_overwrite_preserves_created_at(self):
        entry = _entry("k", "v1", self.scope)
        self.store.store(entry)
        original_created = self.store.retrieve("k", self.scope).created_at
        self.store.store(_entry("k", "v2", self.scope))
        updated = self.store.retrieve("k", self.scope)
        self.assertEqual(updated.created_at, original_created)
        self.assertEqual(updated.value, "v2")

    def test_delete_returns_true_when_found(self):
        self.store.store(_entry("k", "v", self.scope))
        self.assertTrue(self.store.delete("k", self.scope))
        self.assertIsNone(self.store.retrieve("k", self.scope))

    def test_delete_returns_false_when_missing(self):
        self.assertFalse(self.store.delete("ghost", self.scope))


class TestScopeIsolation(unittest.TestCase):
    def setUp(self):
        self.store = ScopedMemoryStore()

    def test_agent_a_cannot_read_agent_b_entry(self):
        scope_a = _scope(agent_id="agent-a")
        scope_b = _scope(agent_id="agent-b")
        self.store.store(_entry("secret", "private", scope_a))
        self.assertIsNone(self.store.retrieve("secret", scope_b))

    def test_shared_entry_readable_by_both_agents(self):
        shared = _scope(agent_id=None)
        self.store.store(_entry("common", "data", shared))
        self.assertEqual(self.store.retrieve("common", _scope(agent_id="a1")).value, "data")
        self.assertEqual(self.store.retrieve("common", _scope(agent_id="a2")).value, "data")

    def test_query_returns_only_accessible_entries(self):
        scope_a = _scope(agent_id="agent-a")
        scope_b = _scope(agent_id="agent-b")
        shared = _scope(agent_id=None)
        self.store.store(_entry("priv-a", "va", scope_a))
        self.store.store(_entry("priv-b", "vb", scope_b))
        self.store.store(_entry("pub", "vp", shared))

        results_a = self.store.query(scope_a)
        keys_a = {e.key for e in results_a}
        self.assertIn("priv-a", keys_a)
        self.assertIn("pub", keys_a)
        self.assertNotIn("priv-b", keys_a)

    def test_org_isolation(self):
        s1 = _scope(org_id="org1", agent_id="a")
        s2 = _scope(org_id="org2", agent_id="a")
        self.store.store(_entry("k", "org1-data", s1))
        self.assertIsNone(self.store.retrieve("k", s2))


class TestTTLAndPrune(unittest.TestCase):
    def setUp(self):
        self.store = ScopedMemoryStore()
        self.scope = _scope(agent_id="agent-ttl")

    def test_entry_with_no_ttl_is_permanent(self):
        self.store.store(_entry("k", "v", self.scope, ttl=None))
        self.assertIsNotNone(self.store.retrieve("k", self.scope))

    def test_expired_entry_returns_none_on_retrieve(self):
        e = ScopedMemoryEntry(key="x", value="gone", scope=self.scope, ttl=1)
        e.created_at = time.time() - 2  # already expired
        self.store.store(e)
        self.assertIsNone(self.store.retrieve("x", self.scope))

    def test_prune_removes_expired_entries(self):
        e1 = ScopedMemoryEntry(key="old", value="x", scope=self.scope, ttl=1)
        e1.created_at = time.time() - 5
        e2 = _entry("fresh", "y", self.scope, ttl=None)
        self.store.store(e1)
        self.store.store(e2)
        removed = self.store.prune_expired()
        self.assertEqual(removed, 1)
        self.assertIsNone(self.store.retrieve("old", self.scope))
        self.assertIsNotNone(self.store.retrieve("fresh", self.scope))

    def test_prune_returns_zero_when_nothing_expired(self):
        self.store.store(_entry("k", "v", self.scope))
        self.assertEqual(self.store.prune_expired(), 0)


class TestScopeKey(unittest.TestCase):
    def test_scope_key_is_deterministic(self):
        s = _scope(org_id="o", user_id="u", agent_id="a", session_id="s")
        k1 = ScopedMemoryStore._scope_key(s)
        k2 = ScopedMemoryStore._scope_key(s)
        self.assertEqual(k1, k2)

    def test_different_scopes_produce_different_keys(self):
        s1 = _scope(agent_id="a1")
        s2 = _scope(agent_id="a2")
        self.assertNotEqual(
            ScopedMemoryStore._scope_key(s1),
            ScopedMemoryStore._scope_key(s2),
        )


if __name__ == "__main__":
    unittest.main()
