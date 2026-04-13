"""Tests for src/core/prompt_cache.py — PromptCache and IntelligentPromptManager."""

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
    m = MagicMock()
    m.connect.return_value = True
    m.add.return_value = False        # YAML fallback
    m.search.return_value = []
    m.get_all.return_value = []
    m.get_provider_status.return_value = {"active_provider": "yaml"}
    return m


@pytest.fixture
def prompt_cache(mock_memory, tmp_path):
    with patch("src.core.prompt_cache.get_memory_facade", return_value=mock_memory):
        with patch.object(Path, "home", return_value=tmp_path):
            from src.core.prompt_cache import PromptCache
            return PromptCache(user_id="test:cache")


@pytest.fixture
def manager(mock_memory, tmp_path):
    with patch("src.core.prompt_cache.get_memory_facade", return_value=mock_memory):
        with patch.object(Path, "home", return_value=tmp_path):
            from src.core.prompt_cache import IntelligentPromptManager
            return IntelligentPromptManager(user_id="test:manager")


# ---------------------------------------------------------------------------
# PromptCache._generate_prompt_hash
# ---------------------------------------------------------------------------

class TestGeneratePromptHash:
    def test_returns_sha256_hex(self, prompt_cache):
        result = prompt_cache._generate_prompt_hash("hello world")
        expected = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        assert result == expected

    def test_deterministic(self, prompt_cache):
        h1 = prompt_cache._generate_prompt_hash("same")
        h2 = prompt_cache._generate_prompt_hash("same")
        assert h1 == h2

    def test_different_inputs_differ(self, prompt_cache):
        h1 = prompt_cache._generate_prompt_hash("a")
        h2 = prompt_cache._generate_prompt_hash("b")
        assert h1 != h2

    def test_empty_string_returns_64_chars(self, prompt_cache):
        result = prompt_cache._generate_prompt_hash("")
        assert len(result) == 64


# ---------------------------------------------------------------------------
# PromptCache._calculate_similarity
# ---------------------------------------------------------------------------

class TestCalculateSimilarity:
    def test_identical(self, prompt_cache):
        assert prompt_cache._calculate_similarity("hello world", "hello world") == 1.0

    def test_no_overlap(self, prompt_cache):
        assert prompt_cache._calculate_similarity("foo bar", "baz qux") == 0.0

    def test_partial_overlap(self, prompt_cache):
        score = prompt_cache._calculate_similarity("hello world", "hello earth")
        assert abs(score - 1 / 3) < 1e-9

    def test_both_empty(self, prompt_cache):
        assert prompt_cache._calculate_similarity("", "") == 1.0

    def test_one_empty(self, prompt_cache):
        assert prompt_cache._calculate_similarity("", "word") == 0.0
        assert prompt_cache._calculate_similarity("word", "") == 0.0


# ---------------------------------------------------------------------------
# PromptCache._save_to_local_storage / _load_from_local_storage
# ---------------------------------------------------------------------------

class TestLocalStorage:
    def test_save_and_load_roundtrip(self, prompt_cache):
        data = {"prompt_text": "hello", "response_text": "world"}
        prompt_cache._save_to_local_storage(data)
        loaded = prompt_cache._load_from_local_storage()
        assert len(loaded) == 1
        assert loaded[0] == data

    def test_multiple_saves_appended(self, prompt_cache):
        for i in range(5):
            prompt_cache._save_to_local_storage({"i": i})
        assert len(prompt_cache._load_from_local_storage()) == 5

    def test_limit_200_entries(self, prompt_cache):
        for i in range(210):
            prompt_cache._save_to_local_storage({"i": i})
        loaded = prompt_cache._load_from_local_storage()
        assert len(loaded) == 200
        assert loaded[-1]["i"] == 209

    def test_load_returns_empty_when_no_file(self, prompt_cache):
        assert prompt_cache._load_from_local_storage() == []

    def test_save_handles_corrupt_file(self, prompt_cache):
        prompt_cache.local_cache_file.write_text("bad json")
        # Should not raise
        prompt_cache._save_to_local_storage({"ok": True})

    def test_load_handles_corrupt_file(self, prompt_cache):
        prompt_cache.local_cache_file.write_text("bad json")
        assert prompt_cache._load_from_local_storage() == []


# ---------------------------------------------------------------------------
# PromptCache.store_prompt
# ---------------------------------------------------------------------------

class TestStorePrompt:
    def test_returns_memory_backend_result(self, prompt_cache, mock_memory):
        mock_memory.add.return_value = True
        result = prompt_cache.store_prompt("my prompt", "my response", outcome_score=0.9)
        assert result is True

    def test_saves_to_local_storage(self, prompt_cache):
        prompt_cache.store_prompt("prompt text", "response text")
        local = prompt_cache._load_from_local_storage()
        assert len(local) == 1
        assert local[0]["prompt_text"] == "prompt text"
        assert local[0]["response_text"] == "response text"
        assert local[0]["type"] == "cached_prompt"

    def test_outcome_score_stored(self, prompt_cache):
        prompt_cache.store_prompt("p", "r", outcome_score=0.75)
        local = prompt_cache._load_from_local_storage()
        assert local[0]["outcome_score"] == 0.75

    def test_default_outcome_score_is_1(self, prompt_cache):
        prompt_cache.store_prompt("p", "r")
        local = prompt_cache._load_from_local_storage()
        assert local[0]["outcome_score"] == 1.0

    def test_metadata_included_when_provided(self, prompt_cache):
        prompt_cache.store_prompt("p", "r", metadata={"tag": "test"})
        local = prompt_cache._load_from_local_storage()
        assert local[0]["metadata"] == {"tag": "test"}

    def test_metadata_absent_when_not_provided(self, prompt_cache):
        prompt_cache.store_prompt("p", "r")
        local = prompt_cache._load_from_local_storage()
        assert "metadata" not in local[0]

    def test_prompt_hash_generated_correctly(self, prompt_cache):
        prompt = "my unique prompt"
        prompt_cache.store_prompt(prompt, "response")
        local = prompt_cache._load_from_local_storage()
        expected = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        assert local[0]["prompt_hash"] == expected

    def test_fallback_returns_false(self, prompt_cache, mock_memory):
        mock_memory.add.return_value = False
        result = prompt_cache.store_prompt("p", "r")
        assert result is False


# ---------------------------------------------------------------------------
# PromptCache.find_similar_prompts
# ---------------------------------------------------------------------------

class TestFindSimilarPrompts:
    def _make_cached(self, prompt_text, score=0.9):
        return json.dumps({
            "type": "cached_prompt",
            "prompt_text": prompt_text,
            "response_text": "response",
            "outcome_score": score,
            "prompt_hash": hashlib.sha256(prompt_text.encode()).hexdigest(),
        })

    def test_returns_empty_when_no_data(self, prompt_cache):
        assert prompt_cache.find_similar_prompts("anything") == []

    def test_finds_from_memory(self, prompt_cache, mock_memory):
        raw = self._make_cached("translate this text")
        mock_memory.search.return_value = [{"memory": raw}]
        results = prompt_cache.find_similar_prompts("translate this text", threshold=0.9)
        assert len(results) == 1

    def test_finds_from_local_when_memory_empty(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = []
        prompt_cache.store_prompt("translate this text", "bonjour")
        results = prompt_cache.find_similar_prompts("translate this text", threshold=0.9)
        assert len(results) == 1

    def test_filters_below_threshold(self, prompt_cache, mock_memory):
        raw = self._make_cached("completely unrelated topic")
        mock_memory.search.return_value = [{"memory": raw}]
        results = prompt_cache.find_similar_prompts("deploy service", threshold=0.7)
        assert results == []

    def test_skips_wrong_type(self, prompt_cache, mock_memory):
        raw = json.dumps({"type": "other", "data": "x"})
        mock_memory.search.return_value = [{"memory": raw}]
        results = prompt_cache.find_similar_prompts("anything", threshold=0.0)
        assert results == []

    def test_skips_invalid_json(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = [{"memory": "{bad"}]
        results = prompt_cache.find_similar_prompts("anything", threshold=0.0)
        assert results == []

    def test_deduplicates_memory_vs_local(self, prompt_cache, mock_memory):
        prompt_text = "deduplicate this prompt"
        raw = self._make_cached(prompt_text)
        mock_memory.search.return_value = [{"memory": raw}]
        # Also in local storage
        prompt_cache._save_to_local_storage({
            "type": "cached_prompt",
            "prompt_text": prompt_text,
            "response_text": "r",
            "outcome_score": 0.9,
            "prompt_hash": hashlib.sha256(prompt_text.encode()).hexdigest(),
        })
        results = prompt_cache.find_similar_prompts(prompt_text, threshold=0.9)
        assert len(results) == 1

    def test_limit_respected(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = []
        for i in range(10):
            prompt_cache._save_to_local_storage({
                "type": "cached_prompt",
                "prompt_text": "translate this text now",
                "response_text": f"r{i}",
                "outcome_score": 0.9,
                "prompt_hash": f"h{i}",
            })
        results = prompt_cache.find_similar_prompts("translate this text now", threshold=0.0, limit=3)
        assert len(results) <= 3

    def test_sorted_by_similarity_descending(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = []
        prompt_cache._save_to_local_storage({
            "type": "cached_prompt",
            "prompt_text": "hello world",
            "response_text": "r",
            "outcome_score": 0.9,
            "prompt_hash": "h1",
        })
        prompt_cache._save_to_local_storage({
            "type": "cached_prompt",
            "prompt_text": "hello world test run",
            "response_text": "r",
            "outcome_score": 0.9,
            "prompt_hash": "h2",
        })
        results = prompt_cache.find_similar_prompts("hello world test", threshold=0.0)
        if len(results) >= 2:
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]


# ---------------------------------------------------------------------------
# PromptCache.get_cached_response
# ---------------------------------------------------------------------------

class TestGetCachedResponse:
    def test_returns_none_when_nothing_cached(self, prompt_cache):
        result = prompt_cache.get_cached_response("some prompt")
        assert result is None

    def test_returns_cached_when_score_above_threshold(self, prompt_cache, mock_memory):
        raw = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "translate hello",
            "response_text": "bonjour",
            "outcome_score": 0.9,
            "prompt_hash": hashlib.sha256("translate hello".encode()).hexdigest(),
        })
        mock_memory.search.return_value = [{"memory": raw}]
        result = prompt_cache.get_cached_response("translate hello")
        assert result is not None
        response, meta = result
        assert response == "bonjour"

    def test_returns_none_when_score_below_threshold(self, prompt_cache, mock_memory):
        raw = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "translate hello",
            "response_text": "bonjour",
            "outcome_score": 0.2,  # below min_outcome_score=0.5
            "prompt_hash": "h1",
        })
        mock_memory.search.return_value = [{"memory": raw}]
        result = prompt_cache.get_cached_response("translate hello", min_outcome_score=0.5)
        assert result is None


# ---------------------------------------------------------------------------
# PromptCache.get_top_prompts
# ---------------------------------------------------------------------------

class TestGetTopPrompts:
    def test_returns_empty_when_no_data(self, prompt_cache):
        assert prompt_cache.get_top_prompts() == []

    def test_returns_from_local_storage(self, prompt_cache, mock_memory):
        mock_memory.get_all.return_value = []
        for i in range(3):
            prompt_cache.store_prompt(f"prompt-{i}", f"response-{i}", outcome_score=float(i) / 2)
        results = prompt_cache.get_top_prompts()
        assert len(results) == 3

    def test_sorted_by_outcome_score_descending(self, prompt_cache, mock_memory):
        mock_memory.get_all.return_value = []
        prompt_cache.store_prompt("low score prompt", "r1", outcome_score=0.3)
        prompt_cache.store_prompt("high score prompt", "r2", outcome_score=0.9)
        results = prompt_cache.get_top_prompts()
        assert results[0]["outcome_score"] >= results[-1]["outcome_score"]

    def test_limit_respected(self, prompt_cache, mock_memory):
        mock_memory.get_all.return_value = []
        for i in range(15):
            prompt_cache.store_prompt(f"prompt-{i}", f"r{i}", outcome_score=float(i) / 15)
        results = prompt_cache.get_top_prompts(limit=5)
        assert len(results) == 5

    def test_deduplicates_memory_and_local(self, prompt_cache, mock_memory):
        raw = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "unique prompt",
            "response_text": "r",
            "outcome_score": 0.9,
            "prompt_hash": "unique-hash-abc",
        })
        mock_memory.get_all.return_value = [{"memory": raw}]
        # Same hash in local
        prompt_cache._save_to_local_storage({
            "type": "cached_prompt",
            "prompt_text": "unique prompt",
            "response_text": "r",
            "outcome_score": 0.9,
            "prompt_hash": "unique-hash-abc",
        })
        results = prompt_cache.get_top_prompts()
        assert len(results) == 1

    def test_skips_non_cached_prompt_types(self, prompt_cache, mock_memory):
        mock_memory.get_all.return_value = [{"memory": json.dumps({"type": "other"})}]
        prompt_cache._save_to_local_storage({"type": "other"})
        results = prompt_cache.get_top_prompts()
        assert results == []


# ---------------------------------------------------------------------------
# PromptCache.update_prompt_outcome
# ---------------------------------------------------------------------------

class TestUpdatePromptOutcome:
    def test_updates_existing_prompt(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = []
        prompt_cache.store_prompt("my prompt text", "my response", outcome_score=0.5)
        # Now update it — uses find_similar_prompts (threshold=0.9) then store again
        prompt_cache.update_prompt_outcome("my prompt text", 0.95)
        local = prompt_cache._load_from_local_storage()
        # Should now have 2 records (original + updated)
        scores = [r["outcome_score"] for r in local if r.get("type") == "cached_prompt"]
        assert 0.95 in scores

    def test_noop_when_no_similar_found(self, prompt_cache, mock_memory):
        mock_memory.search.return_value = []
        # No stored prompts — should not raise
        prompt_cache.update_prompt_outcome("nonexistent prompt", 0.5)


# ---------------------------------------------------------------------------
# IntelligentPromptManager
# ---------------------------------------------------------------------------

class TestIntelligentPromptManager:
    def test_get_response_or_generate_uses_cache(self, manager, mock_memory):
        """When cache has a match, generator_func NOT called."""
        raw = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "what is the capital of france",
            "response_text": "Paris",
            "outcome_score": 0.9,
            "prompt_hash": hashlib.sha256("what is the capital of france".encode()).hexdigest(),
            "similarity_score": 0.95,
        })
        mock_memory.search.return_value = [{"memory": raw}]

        generator = MagicMock(return_value="NOT CALLED")
        result = manager.get_response_or_generate("what is the capital of france", generator)
        assert result == "Paris"
        generator.assert_not_called()

    def test_get_response_or_generate_calls_generator_when_no_cache(self, manager, mock_memory):
        mock_memory.search.return_value = []
        generator = MagicMock(return_value="Generated answer")
        result = manager.get_response_or_generate("brand new question nobody asked", generator)
        assert result == "Generated answer"
        generator.assert_called_once()

    def test_get_response_or_generate_caches_generated_response(self, manager, mock_memory):
        mock_memory.search.return_value = []
        generator = MagicMock(return_value="my new response")
        manager.get_response_or_generate("fresh unique prompt xyz", generator)
        # Check local storage contains the new prompt
        local = manager.cache._load_from_local_storage()
        assert any(r.get("prompt_text") == "fresh unique prompt xyz" for r in local)

    def test_evaluate_and_update_cache_calls_update(self, manager):
        """Smoke test: evaluate_and_update_cache delegates to cache.update_prompt_outcome."""
        with patch.object(manager.cache, "update_prompt_outcome") as mock_update:
            manager.evaluate_and_update_cache("some prompt", "some response", 0.8)
            mock_update.assert_called_once_with("some prompt", 0.8)

    def test_get_suggestions_for_topic_filters_low_scores(self, manager, mock_memory):
        """Only prompts with outcome_score >= 0.7 returned."""
        raw_good = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "python async tutorial",
            "response_text": "response",
            "outcome_score": 0.9,
            "prompt_hash": "h1",
        })
        raw_bad = json.dumps({
            "type": "cached_prompt",
            "prompt_text": "python async guide",
            "response_text": "response",
            "outcome_score": 0.3,
            "prompt_hash": "h2",
        })
        mock_memory.search.return_value = [{"memory": raw_good}, {"memory": raw_bad}]
        results = manager.get_suggestions_for_topic("python async")
        assert all(r["outcome_score"] >= 0.7 for r in results)

    def test_get_suggestions_returns_empty_when_no_prompts(self, manager):
        results = manager.get_suggestions_for_topic("obscure topic no match")
        assert results == []


# ---------------------------------------------------------------------------
# create_intelligent_prompt_manager convenience function
# ---------------------------------------------------------------------------

class TestCreateIntelligentPromptManager:
    def test_returns_instance(self, mock_memory, tmp_path):
        with patch("src.core.prompt_cache.get_memory_facade", return_value=mock_memory):
            with patch.object(Path, "home", return_value=tmp_path):
                from src.core.prompt_cache import create_intelligent_prompt_manager, IntelligentPromptManager
                mgr = create_intelligent_prompt_manager()
                assert isinstance(mgr, IntelligentPromptManager)

    def test_accepts_custom_user_id(self, mock_memory, tmp_path):
        with patch("src.core.prompt_cache.get_memory_facade", return_value=mock_memory):
            with patch.object(Path, "home", return_value=tmp_path):
                from src.core.prompt_cache import create_intelligent_prompt_manager
                mgr = create_intelligent_prompt_manager("custom:pm")
                assert mgr.user_id == "custom:pm"
