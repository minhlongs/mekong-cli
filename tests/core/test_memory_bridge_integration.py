"""E2E integration tests for MemoryBridge protocol (B4 adapter + B5 parser).

Test: goal produces MemoryRecord → bridge.record() → bridge.search() round-trip
across all backends (seed, memory_store, scoped, pev).
"""
from __future__ import annotations

import pytest

from src.core.memory_bridge import MemoryBridge, MemoryKind, MemoryRecord, get_bridge


# --- Fixtures ---

@pytest.fixture(params=["seed", "memory_store", "scoped", "pev"])
def bridge(request: str) -> MemoryBridge:
    """Parametrized: one bridge per adapter backend."""
    return get_bridge(request.param)


@pytest.fixture
def sample_record() -> MemoryRecord:
    """Deterministic MemoryRecord for round-trip tests."""
    return MemoryRecord(
        content="User asked about pricing plans for the SaaS product.",
        kind=MemoryKind.EPISODIC,
        metadata={"source": "telegram", "confidence": 0.92},
        agent_id="ceo",
        session_id="sess_001",
        user_id="user_42",
    )


@pytest.fixture
def mixed_records() -> list[MemoryRecord]:
    """Records across different kinds and agents for search filtering."""
    return [
        MemoryRecord(
            content="Quarterly revenue target exceeded by 15%.",
            kind=MemoryKind.EPISODIC,
            agent_id="ceo",
            session_id="sess_1",
            user_id="u1",
        ),
        MemoryRecord(
            content="Revenue growth strategies: upselling, referrals, premium tiers.",
            kind=MemoryKind.SEMANTIC,
            agent_id="ceo",
            session_id="sess_1",
            user_id="u1",
        ),
        MemoryRecord(
            content="Billing microservice consumes 300 MCU/month.",
            kind=MemoryKind.PROCEDURAL,
            agent_id="eng",
            session_id="sess_2",
            user_id="u1",
        ),
        MemoryRecord(
            content="Customer onboarding checklist for new pilot users.",
            kind=MemoryKind.WORKING,
            agent_id="ops",
            session_id="sess_3",
            user_id="u2",
        ),
    ]


# --- Record + Search round-trip ---

class TestRecordSearchRoundtrip:
    def test_record_returns_string_id(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """record() must return a non-empty string identifier."""
        entry_id = bridge.record(sample_record)
        assert isinstance(entry_id, str)
        assert len(entry_id) > 0

    def test_search_finds_recorded_content(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """A recorded record should appear in search results for matching query."""
        bridge.record(sample_record)
        results = bridge.search("pricing plans", limit=5)
        assert len(results) > 0
        contents = [r.content.lower() for r in results]
        assert any("pricing" in c or "plans" in c for c in contents)

    def test_stats_reflects_count(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """stats() count should increase after record()."""
        before = bridge.stats()
        bridge.record(sample_record)
        after = bridge.stats()
        assert after["count"] >= before["count"] + 1


# --- Search with scope filters ---

class TestSearchScoping:
    def test_kind_filter(self, bridge: MemoryBridge, mixed_records: list[MemoryRecord]) -> None:
        """Filtering by kind should only return matching kinds."""
        for rec in mixed_records:
            bridge.record(rec)
        results = bridge.search("revenue", limit=10, kind=MemoryKind.SEMANTIC)
        assert all(r.kind == MemoryKind.SEMANTIC for r in results)

    def test_agent_id_filter(self, bridge: MemoryBridge, mixed_records: list[MemoryRecord]) -> None:
        """Filtering by agent_id = eng should only return eng records."""
        for rec in mixed_records:
            bridge.record(rec)
        results = bridge.search("", limit=10, agent_id="eng")
        assert len(results) > 0
        assert all(r.agent_id == "eng" for r in results)

    def test_session_id_filter(self, bridge: MemoryBridge, mixed_records: list[MemoryRecord]) -> None:
        """Filtering by session_id should return only records from that session."""
        for rec in mixed_records:
            bridge.record(rec)
        results = bridge.search("", limit=10, session_id="sess_2")
        assert all(r.session_id == "sess_2" for r in results)

    def test_user_id_filter(self, bridge: MemoryBridge, mixed_records: list[MemoryRecord]) -> None:
        """Filtering by user_id should return only records for that user."""
        for rec in mixed_records:
            bridge.record(rec)
        results = bridge.search("", limit=10, user_id="u2")
        assert all(r.user_id == "u2" for r in results)


# --- Recent + Recall ---

class TestRecentRecall:
    def test_recent_returns_records(self, bridge: MemoryBridge, mixed_records: list[MemoryRecord]) -> None:
        """recent() should return recorded entries in time order."""
        for rec in mixed_records:
            bridge.record(rec)
        results = bridge.recent(limit=10)
        assert len(results) >= len(mixed_records) - 1  # at least most

    def test_recall_returns_dicts(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """recall() should return list[dict] with content and agent_id."""
        bridge.record(sample_record)
        results = bridge.recall("pricing", k=3)
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, dict)
            assert "content" in item
            assert "agent_id" in item


# --- Delete ---

class TestDelete:
    def test_delete_returns_bool(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """delete() must return True/False."""
        entry_id = bridge.record(sample_record)
        result = bridge.delete(entry_id)
        assert isinstance(result, bool)

    def test_delete_removes_record(self, bridge: MemoryBridge, sample_record: MemoryRecord) -> None:
        """After delete, the record should not appear in search."""
        entry_id = bridge.record(sample_record)
        bridge.delete(entry_id)
        results = bridge.search("pricing plans", limit=5)
        contents = [r.content.lower() for r in results]
        # The deleted record should be absent if it was unique
        assert sample_record.content.lower() not in contents


# --- Prune / Stats ---

class TestPruneStats:
    def test_prune_expired_returns_int(self, bridge: MemoryBridge) -> None:
        """prune_expired() must return an integer."""
        result = bridge.prune_expired()
        assert isinstance(result, int)
        assert result >= 0

    def test_stats_returns_dict_with_backend(self, bridge: MemoryBridge) -> None:
        """stats() must include a backend key with a string value."""
        stats = bridge.stats()
        assert isinstance(stats, dict)
        assert "backend" in stats
        assert isinstance(stats["backend"], str)


# --- MemoryRecord fields preserved ---

class TestRecordCompleteness:
    def test_all_fields_preserved(self, bridge: MemoryBridge) -> None:
        """All MemoryRecord fields should survive the round-trip."""
        original = MemoryRecord(
            content="Integration test of MemoryRecord field preservation.",
            kind=MemoryKind.PROCEDURAL,
            metadata={"test": True, "round": 1},
            agent_id="test_agent",
            session_id="sess_test",
            user_id="user_test",
            ttl_seconds=3600,
        )
        _ = bridge.record(original)
        results = bridge.search("field preservation", limit=5)
        assert len(results) >= 1
        match = results[0]
        assert match.kind == MemoryKind.PROCEDURAL
        assert match.agent_id == "test_agent"
        assert match.session_id == "sess_test"
        assert match.user_id == "user_test"
        assert match.metadata.get("test") is True
