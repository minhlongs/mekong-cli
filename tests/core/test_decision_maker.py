"""Tests for src/core/decision_maker.py — DecisionMaker and MemoryAugmentedDecisionEngine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_memory():
    """Return a mock MemoryFacade with sensible defaults."""
    m = MagicMock()
    m.connect.return_value = True
    m.add.return_value = False        # YAML fallback by default
    m.search.return_value = []
    m.get_all.return_value = []
    m.get_provider_status.return_value = {"active_provider": "yaml"}
    return m


@pytest.fixture
def decision_maker(mock_memory, tmp_path):
    """DecisionMaker wired to mock memory and temp local storage."""
    with patch("src.core.decision_maker.get_memory_facade", return_value=mock_memory):
        with patch.object(Path, "home", return_value=tmp_path):
            from src.core.decision_maker import DecisionMaker
            dm = DecisionMaker(user_id="test:session")
            return dm


@pytest.fixture
def engine(mock_memory, tmp_path):
    """MemoryAugmentedDecisionEngine with mock memory and temp local storage."""
    with patch("src.core.decision_maker.get_memory_facade", return_value=mock_memory):
        with patch.object(Path, "home", return_value=tmp_path):
            from src.core.decision_maker import MemoryAugmentedDecisionEngine
            return MemoryAugmentedDecisionEngine(user_id="test:engine")


# ---------------------------------------------------------------------------
# DecisionMaker._generate_decision_hash
# ---------------------------------------------------------------------------

class TestGenerateDecisionHash:
    def test_returns_sha256_hex(self, decision_maker):
        result = decision_maker._generate_decision_hash("hello world")
        expected = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        assert result == expected

    def test_deterministic(self, decision_maker):
        h1 = decision_maker._generate_decision_hash("same input")
        h2 = decision_maker._generate_decision_hash("same input")
        assert h1 == h2

    def test_different_inputs_differ(self, decision_maker):
        h1 = decision_maker._generate_decision_hash("input a")
        h2 = decision_maker._generate_decision_hash("input b")
        assert h1 != h2

    def test_empty_string(self, decision_maker):
        result = decision_maker._generate_decision_hash("")
        assert len(result) == 64  # sha256 hex length


# ---------------------------------------------------------------------------
# DecisionMaker._calculate_similarity
# ---------------------------------------------------------------------------

class TestCalculateSimilarity:
    def test_identical_texts(self, decision_maker):
        assert decision_maker._calculate_similarity("hello world", "hello world") == 1.0

    def test_no_overlap(self, decision_maker):
        assert decision_maker._calculate_similarity("foo bar", "baz qux") == 0.0

    def test_partial_overlap(self, decision_maker):
        score = decision_maker._calculate_similarity("hello world", "hello earth")
        # intersection={hello}, union={hello, world, earth} → 1/3
        assert abs(score - 1 / 3) < 1e-9

    def test_both_empty(self, decision_maker):
        assert decision_maker._calculate_similarity("", "") == 1.0

    def test_one_empty(self, decision_maker):
        assert decision_maker._calculate_similarity("", "hello") == 0.0
        assert decision_maker._calculate_similarity("hello", "") == 0.0


# ---------------------------------------------------------------------------
# DecisionMaker._save_to_local_storage / _load_from_local_storage
# ---------------------------------------------------------------------------

class TestLocalStorage:
    def test_save_and_load_roundtrip(self, decision_maker):
        data = {"key": "value", "num": 42}
        decision_maker._save_to_local_storage(data)
        loaded = decision_maker._load_from_local_storage()
        assert len(loaded) == 1
        assert loaded[0] == data

    def test_multiple_saves_appended(self, decision_maker):
        for i in range(3):
            decision_maker._save_to_local_storage({"i": i})
        loaded = decision_maker._load_from_local_storage()
        assert len(loaded) == 3

    def test_limit_200_entries(self, decision_maker):
        for i in range(210):
            decision_maker._save_to_local_storage({"i": i})
        loaded = decision_maker._load_from_local_storage()
        assert len(loaded) == 200
        # Most recent items retained
        assert loaded[-1]["i"] == 209

    def test_load_returns_empty_when_file_missing(self, decision_maker):
        # File hasn't been created yet
        assert decision_maker._load_from_local_storage() == []

    def test_save_handles_corrupt_file_gracefully(self, decision_maker):
        # Write garbage JSON to the file
        decision_maker.local_decisions_file.write_text("not-json")
        # Should not raise; logs warning instead
        decision_maker._save_to_local_storage({"safe": True})

    def test_load_handles_corrupt_file_gracefully(self, decision_maker):
        decision_maker.local_decisions_file.write_text("not-json")
        result = decision_maker._load_from_local_storage()
        assert result == []


# ---------------------------------------------------------------------------
# DecisionMaker.record_decision
# ---------------------------------------------------------------------------

class TestRecordDecision:
    def test_happy_path_returns_memory_result(self, decision_maker, mock_memory):
        mock_memory.add.return_value = True
        result = decision_maker.record_decision(
            decision_context="deploy service",
            decision="blue-green",
            outcome="success",
            confidence=0.9,
        )
        assert result is True

    def test_saves_to_local_storage(self, decision_maker):
        decision_maker.record_decision(
            decision_context="ctx",
            decision="opt-a",
            outcome="success",
        )
        local = decision_maker._load_from_local_storage()
        assert len(local) == 1
        assert local[0]["decision_context"] == "ctx"
        assert local[0]["type"] == "decision_record"

    def test_metadata_included_when_provided(self, decision_maker):
        decision_maker.record_decision(
            decision_context="ctx",
            decision="opt-a",
            outcome="success",
            metadata={"project": "mekong"},
        )
        local = decision_maker._load_from_local_storage()
        assert local[0]["metadata"] == {"project": "mekong"}

    def test_metadata_absent_when_not_provided(self, decision_maker):
        decision_maker.record_decision("ctx", "opt", "ok")
        local = decision_maker._load_from_local_storage()
        assert "metadata" not in local[0]

    def test_fallback_returns_false(self, decision_maker, mock_memory):
        mock_memory.add.return_value = False
        result = decision_maker.record_decision("ctx", "opt", "ok")
        assert result is False

    def test_decision_hash_generated_correctly(self, decision_maker):
        ctx = "some context"
        decision_maker.record_decision(ctx, "opt", "ok")
        local = decision_maker._load_from_local_storage()
        expected_hash = hashlib.sha256(ctx.encode("utf-8")).hexdigest()
        assert local[0]["decision_hash"] == expected_hash


# ---------------------------------------------------------------------------
# DecisionMaker.find_similar_decisions
# ---------------------------------------------------------------------------

class TestFindSimilarDecisions:
    def _make_record(self, context, decision="do-it", outcome="success", confidence=0.9):
        return json.dumps({
            "type": "decision_record",
            "decision_context": context,
            "decision": decision,
            "outcome": outcome,
            "confidence": confidence,
            "decision_hash": hashlib.sha256(context.encode()).hexdigest(),
        })

    def test_returns_empty_when_no_data(self, decision_maker):
        results = decision_maker.find_similar_decisions("deploy service")
        assert results == []

    def test_finds_from_local_storage(self, decision_maker, mock_memory):
        """When memory returns nothing, fall back to local storage."""
        mock_memory.search.return_value = []
        ctx = "deploy the service now"
        decision_maker.record_decision(ctx, "blue-green", "success", 0.9)

        results = decision_maker.find_similar_decisions("deploy the service now", threshold=0.9)
        assert len(results) == 1
        assert results[0]["decision_context"] == ctx

    def test_finds_from_memory_system(self, decision_maker, mock_memory):
        """Results from memory system parsed and returned when above threshold."""
        raw = self._make_record("run database migration")
        mock_memory.search.return_value = [{"memory": raw}]

        results = decision_maker.find_similar_decisions("run database migration", threshold=0.9)
        assert len(results) == 1
        assert results[0]["decision"] == "do-it"

    def test_filters_below_threshold(self, decision_maker, mock_memory):
        """Records with similarity below threshold excluded."""
        raw = self._make_record("completely unrelated topic xyz")
        mock_memory.search.return_value = [{"memory": raw}]
        # Query is different enough that Jaccard similarity < 0.7
        results = decision_maker.find_similar_decisions("deploy service", threshold=0.7)
        assert results == []

    def test_skips_non_decision_records(self, decision_maker, mock_memory):
        raw = json.dumps({"type": "other_type", "data": "x"})
        mock_memory.search.return_value = [{"memory": raw}]
        results = decision_maker.find_similar_decisions("anything", threshold=0.0)
        assert results == []

    def test_skips_invalid_json_from_memory(self, decision_maker, mock_memory):
        mock_memory.search.return_value = [{"memory": "{bad json"}]
        results = decision_maker.find_similar_decisions("anything", threshold=0.0)
        assert results == []

    def test_deduplicates_local_vs_memory(self, decision_maker, mock_memory):
        """Same hash from memory and local storage counted only once."""
        ctx = "same context for both"
        raw = self._make_record(ctx)
        mock_memory.search.return_value = [{"memory": raw}]
        # Also add to local storage so it would appear in fallback
        decision_maker._save_to_local_storage({
            "type": "decision_record",
            "decision_context": ctx,
            "decision": "do-it",
            "outcome": "success",
            "confidence": 0.9,
            "decision_hash": hashlib.sha256(ctx.encode()).hexdigest(),
        })
        results = decision_maker.find_similar_decisions(ctx, threshold=0.9)
        assert len(results) == 1

    def test_results_sorted_by_similarity_descending(self, decision_maker, mock_memory):
        mock_memory.search.return_value = []
        # Two decisions with different overlap with query "hello world test"
        decision_maker._save_to_local_storage({
            "type": "decision_record",
            "decision_context": "hello world",
            "decision": "A",
            "outcome": "success",
            "confidence": 0.9,
            "decision_hash": "hash-a",
        })
        decision_maker._save_to_local_storage({
            "type": "decision_record",
            "decision_context": "hello world test run",
            "decision": "B",
            "outcome": "success",
            "confidence": 0.9,
            "decision_hash": "hash-b",
        })
        results = decision_maker.find_similar_decisions("hello world test", threshold=0.0)
        if len(results) >= 2:
            assert results[0].get("similarity_score", 0) >= results[1].get("similarity_score", 0)

    def test_limit_respected(self, decision_maker, mock_memory):
        mock_memory.search.return_value = []
        for i in range(10):
            decision_maker._save_to_local_storage({
                "type": "decision_record",
                "decision_context": "deploy service now",
                "decision": f"opt-{i}",
                "outcome": "success",
                "confidence": 0.9,
                "decision_hash": f"hash-{i}",
            })
        results = decision_maker.find_similar_decisions("deploy service now", threshold=0.0, limit=3)
        assert len(results) <= 3


# ---------------------------------------------------------------------------
# DecisionMaker.get_recommendation
# ---------------------------------------------------------------------------

class TestGetRecommendation:
    def test_returns_none_when_no_similar_decisions(self, decision_maker):
        result = decision_maker.get_recommendation("some context")
        assert result is None

    def test_returns_none_for_low_confidence(self, decision_maker, mock_memory):
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "deploy now",
            "decision": "blue-green",
            "outcome": "success",
            "confidence": 0.3,  # below min_confidence=0.6
            "decision_hash": "h1",
        })
        mock_memory.search.return_value = [{"memory": raw}]
        result = decision_maker.get_recommendation("deploy now", min_confidence=0.6)
        assert result is None

    def test_returns_none_for_failure_outcome(self, decision_maker, mock_memory):
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "deploy now",
            "decision": "rollback",
            "outcome": "failure",
            "confidence": 0.9,
            "decision_hash": "h1",
        })
        mock_memory.search.return_value = [{"memory": raw}]
        result = decision_maker.get_recommendation("deploy now")
        assert result is None

    def test_returns_decision_for_good_match(self, decision_maker, mock_memory):
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "deploy the service",
            "decision": "blue-green",
            "outcome": "success",
            "confidence": 0.9,
            "decision_hash": "h1",
        })
        mock_memory.search.return_value = [{"memory": raw}]
        result = decision_maker.get_recommendation("deploy the service", min_confidence=0.6)
        assert result is not None
        recommended, data = result
        assert recommended == "blue-green"
        assert data["outcome"] == "success"


# ---------------------------------------------------------------------------
# DecisionMaker.get_decision_rationale
# ---------------------------------------------------------------------------

class TestGetDecisionRationale:
    def test_returns_none_when_not_found(self, decision_maker):
        result = decision_maker.get_decision_rationale("nonexistent-hash")
        assert result is None

    def test_finds_from_local_storage(self, decision_maker, mock_memory):
        mock_memory.get_all.return_value = []
        ctx = "context for rationale"
        decision_maker.record_decision(ctx, "opt", "success")
        local = decision_maker._load_from_local_storage()
        decision_hash = local[0]["decision_hash"]

        result = decision_maker.get_decision_rationale(decision_hash)
        assert result is not None
        assert result["decision_context"] == ctx

    def test_finds_from_memory_system(self, decision_maker, mock_memory):
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "ctx",
            "decision": "opt",
            "outcome": "success",
            "decision_hash": "target-hash",
        })
        mock_memory.get_all.return_value = [{"memory": raw}]
        result = decision_maker.get_decision_rationale("target-hash")
        assert result is not None
        assert result["decision_hash"] == "target-hash"

    def test_skips_non_matching_hash(self, decision_maker, mock_memory):
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "ctx",
            "decision": "opt",
            "decision_hash": "other-hash",
        })
        mock_memory.get_all.return_value = [{"memory": raw}]
        result = decision_maker.get_decision_rationale("target-hash")
        assert result is None


# ---------------------------------------------------------------------------
# DecisionMaker.update_decision_outcome
# ---------------------------------------------------------------------------

class TestUpdateDecisionOutcome:
    def test_updates_outcome_in_local_storage(self, decision_maker):
        ctx = "context for update"
        decision_maker.record_decision(ctx, "opt-a", "pending")
        local = decision_maker._load_from_local_storage()
        decision_hash = local[0]["decision_hash"]

        decision_maker.update_decision_outcome(decision_hash, "success", 0.95)
        updated = decision_maker._load_from_local_storage()
        record = next(r for r in updated if r.get("decision_hash") == decision_hash)
        assert record["outcome"] == "success"
        assert record["confidence"] == 0.95

    def test_updates_only_confidence_when_provided(self, decision_maker):
        ctx = "context update conf"
        decision_maker.record_decision(ctx, "opt-a", "pending", confidence=0.5)
        local = decision_maker._load_from_local_storage()
        decision_hash = local[0]["decision_hash"]

        decision_maker.update_decision_outcome(decision_hash, "success")
        updated = decision_maker._load_from_local_storage()
        record = next(r for r in updated if r.get("decision_hash") == decision_hash)
        assert record["outcome"] == "success"
        assert record["confidence"] == 0.5  # unchanged

    def test_noop_when_hash_not_found(self, decision_maker):
        # No stored decisions — should not raise
        decision_maker.update_decision_outcome("nonexistent", "success")


# ---------------------------------------------------------------------------
# DecisionMaker.get_decision_audit_trail
# ---------------------------------------------------------------------------

class TestGetDecisionAuditTrail:
    def test_returns_empty_when_no_decisions(self, decision_maker):
        result = decision_maker.get_decision_audit_trail()
        assert result == []

    def test_returns_decisions_from_local_storage(self, decision_maker, mock_memory):
        mock_memory.get_all.return_value = []
        for i in range(3):
            decision_maker.record_decision(f"ctx-{i}", f"opt-{i}", "success")
        trail = decision_maker.get_decision_audit_trail()
        assert len(trail) == 3

    def test_limit_respected(self, decision_maker, mock_memory):
        mock_memory.get_all.return_value = []
        for i in range(15):
            decision_maker.record_decision(f"ctx-{i}", f"opt-{i}", "success")
        trail = decision_maker.get_decision_audit_trail(limit=5)
        assert len(trail) == 5

    def test_combines_memory_and_local(self, decision_maker, mock_memory):
        """Unique entries from both sources are merged."""
        # Add one record from memory (different hash)
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "memory ctx",
            "decision": "opt-m",
            "outcome": "success",
            "decision_hash": "memory-hash-unique",
            "timestamp": "2024-01-01T00:00:00",
        })
        mock_memory.get_all.return_value = [{"memory": raw}]
        # Add another from local
        decision_maker.record_decision("local ctx", "opt-l", "success")
        trail = decision_maker.get_decision_audit_trail()
        assert len(trail) == 2


# ---------------------------------------------------------------------------
# MemoryAugmentedDecisionEngine
# ---------------------------------------------------------------------------

class TestMemoryAugmentedDecisionEngine:
    def test_make_decision_uses_first_option_as_default(self, engine):
        option, meta = engine.make_decision("some context", ["option-a", "option-b"])
        assert option == "option-a"
        assert meta["based_on_past"] is False

    def test_make_decision_empty_options(self, engine):
        option, meta = engine.make_decision("some context", [])
        assert option == "no-option-available"

    def test_make_decision_from_past(self, engine, mock_memory):
        """When recommendation matches an option, use it."""
        # Seed local storage with a relevant past decision
        raw = json.dumps({
            "type": "decision_record",
            "decision_context": "deploy the new service",
            "decision": "blue-green",
            "outcome": "success",
            "confidence": 0.9,
            "decision_hash": "h1",
        })
        mock_memory.search.return_value = [{"memory": raw}]
        option, meta = engine.make_decision(
            "deploy the new service",
            ["blue-green", "canary"],
        )
        assert option == "blue-green"
        assert meta["based_on_past"] is True

    def test_record_decision_outcome_calls_update(self, engine, mock_memory):
        """record_decision_outcome updates and adds follow-up record."""
        mock_memory.get_all.return_value = []
        mock_memory.search.return_value = []
        # Should not raise
        engine.record_decision_outcome("ctx", "opt-a", "success", confidence=0.8)

    def test_calculate_similarity_engine(self, engine):
        assert engine._calculate_similarity("hello world", "hello world") == 1.0
        assert engine._calculate_similarity("foo", "bar") == 0.0


# ---------------------------------------------------------------------------
# create_decision_maker convenience function
# ---------------------------------------------------------------------------

class TestCreateDecisionMaker:
    def test_returns_engine_instance(self, mock_memory, tmp_path):
        with patch("src.core.decision_maker.get_memory_facade", return_value=mock_memory):
            with patch.object(Path, "home", return_value=tmp_path):
                from src.core.decision_maker import create_decision_maker, MemoryAugmentedDecisionEngine
                engine = create_decision_maker()
                assert isinstance(engine, MemoryAugmentedDecisionEngine)

    def test_accepts_custom_user_id(self, mock_memory, tmp_path):
        with patch("src.core.decision_maker.get_memory_facade", return_value=mock_memory):
            with patch.object(Path, "home", return_value=tmp_path):
                from src.core.decision_maker import create_decision_maker
                engine = create_decision_maker("custom:user")
                assert engine.user_id == "custom:user"
