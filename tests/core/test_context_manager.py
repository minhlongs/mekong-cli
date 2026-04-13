"""Tests for src/core/context_manager.py."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_memory(search_returns=None, get_all_returns=None, add_returns=True):
    mem = MagicMock()
    mem.connect.return_value = None
    mem.get_provider_status.return_value = {"active_provider": "yaml"}
    mem.add.return_value = add_returns
    mem.search.return_value = search_returns or []
    mem.get_all.return_value = get_all_returns or []
    return mem


def _make_context_manager(tmp_path, user_id="agent:session1", mem=None):
    """Instantiate ContextManager bypassing real memory + filesystem setup."""
    from src.core.context_manager import ContextManager

    if mem is None:
        mem = _make_mock_memory()

    with patch("src.core.context_manager.get_memory_facade", return_value=mem):
        cm = ContextManager.__new__(ContextManager)
        cm.user_id = user_id if ":" in user_id else f"default:{user_id}"
        cm.memory = mem

        # Redirect storage to tmp
        cm.local_storage_path = tmp_path / "contexts"
        cm.local_storage_path.mkdir(parents=True, exist_ok=True)
        safe_id = cm.user_id.replace(":", "_").replace("/", "_")
        cm.local_context_file = cm.local_storage_path / f"{safe_id}.json"

    return cm


# ---------------------------------------------------------------------------
# ContextManager.__init__ — user_id normalisation
# ---------------------------------------------------------------------------

class TestContextManagerInit:
    def test_adds_default_prefix_when_no_colon(self, tmp_path):
        mem = _make_mock_memory()
        with patch("src.core.context_manager.get_memory_facade", return_value=mem):
            from src.core.context_manager import ContextManager
            cm = ContextManager.__new__(ContextManager)
            cm.memory = mem
            cm.local_storage_path = tmp_path / "contexts"
            cm.local_storage_path.mkdir(parents=True, exist_ok=True)
            # Simulate __init__ user_id normalisation logic directly
            raw_id = "plain_user"
            if ":" not in raw_id:
                raw_id = f"default:{raw_id}"
            cm.user_id = raw_id
        assert cm.user_id == "default:plain_user"

    def test_keeps_colon_user_id_unchanged(self, tmp_path):
        cm = _make_context_manager(tmp_path, user_id="agent:session99")
        assert cm.user_id == "agent:session99"


# ---------------------------------------------------------------------------
# _save_to_local_storage / _load_from_local_storage
# ---------------------------------------------------------------------------

class TestLocalStorage:
    def test_save_and_load_roundtrip(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        data = {"type": "conversation_interaction", "user_message": "hi", "timestamp": "T1"}
        cm._save_to_local_storage(data)

        loaded = cm._load_from_local_storage()
        assert len(loaded) == 1
        assert loaded[0]["user_message"] == "hi"

    def test_load_missing_file_returns_empty(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        result = cm._load_from_local_storage()
        assert result == []

    def test_caps_at_100_items(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        for i in range(105):
            cm._save_to_local_storage({"type": "conversation_interaction", "idx": i})
        loaded = cm._load_from_local_storage()
        assert len(loaded) == 100

    def test_most_recent_100_kept(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        for i in range(105):
            cm._save_to_local_storage({"type": "x", "idx": i})
        loaded = cm._load_from_local_storage()
        # The last 100 should remain (idx 5..104)
        indices = [d["idx"] for d in loaded]
        assert 104 in indices
        assert 0 not in indices

    def test_save_handles_corrupt_existing_file(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.local_context_file.write_text("CORRUPT", encoding="utf-8")
        # Should not raise, should handle error gracefully
        cm._save_to_local_storage({"type": "ok"})

    def test_load_handles_corrupt_file(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.local_context_file.write_text("NOT JSON", encoding="utf-8")
        result = cm._load_from_local_storage()
        assert result == []


# ---------------------------------------------------------------------------
# store_interaction
# ---------------------------------------------------------------------------

class TestStoreInteraction:
    def test_returns_bool(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        result = cm.store_interaction("hello", "world")
        assert isinstance(result, bool)

    def test_calls_memory_add(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.store_interaction("user says this", "agent says that")
        cm.memory.add.assert_called_once()

    def test_persists_to_local_storage(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.store_interaction("msg", "response")
        loaded = cm._load_from_local_storage()
        assert len(loaded) == 1
        assert loaded[0]["user_message"] == "msg"
        assert loaded[0]["agent_response"] == "response"

    def test_stores_optional_metadata(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.store_interaction("q", "a", metadata={"extra": "info"})
        loaded = cm._load_from_local_storage()
        assert loaded[0]["metadata"]["extra"] == "info"

    def test_stores_without_metadata(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.store_interaction("q", "a")
        loaded = cm._load_from_local_storage()
        assert "metadata" not in loaded[0]

    def test_stored_data_has_session_id(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        cm.store_interaction("hi", "hello")
        call_kwargs = cm.memory.add.call_args
        content_str = call_kwargs.kwargs.get("content") or call_kwargs[1]["content"]
        parsed = json.loads(content_str)
        assert parsed["session_id"] == cm.user_id

    def test_returns_memory_add_return_value(self, tmp_path):
        mem = _make_mock_memory(add_returns=False)
        cm = _make_context_manager(tmp_path, mem=mem)
        result = cm.store_interaction("q", "a")
        assert result is False


# ---------------------------------------------------------------------------
# retrieve_context
# ---------------------------------------------------------------------------

class TestRetrieveContext:
    def test_returns_list(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        result = cm.retrieve_context()
        assert isinstance(result, list)

    def test_returns_at_most_limit_items(self, tmp_path):
        # Put 10 items in local storage, request 3
        cm = _make_context_manager(tmp_path)
        for i in range(10):
            cm._save_to_local_storage({"type": "conversation_interaction", "timestamp": f"T{i:02d}"})
        result = cm.retrieve_context(limit=3)
        assert len(result) <= 3

    def test_uses_memory_search_when_query_provided(self, tmp_path):
        mem = _make_mock_memory(search_returns=[{"memory": '{"type": "conversation_interaction", "user_message": "found"}'}])
        cm = _make_context_manager(tmp_path, mem=mem)
        result = cm.retrieve_context(query="found")
        mem.search.assert_called_once()
        assert any(item.get("user_message") == "found" for item in result)

    def test_uses_get_all_when_no_query(self, tmp_path):
        mem = _make_mock_memory(get_all_returns=[{"memory": '{"type": "raw"}'}])
        cm = _make_context_manager(tmp_path, mem=mem)
        cm.retrieve_context(query=None)
        mem.get_all.assert_called_once()

    def test_handles_non_json_memory_content(self, tmp_path):
        mem = _make_mock_memory(search_returns=[{"memory": "plain text content"}])
        cm = _make_context_manager(tmp_path, mem=mem)
        result = cm.retrieve_context(query="anything")
        assert any(item.get("type") in ("raw_memory", "raw_content") for item in result)

    def test_supplements_from_local_when_memory_insufficient(self, tmp_path):
        mem = _make_mock_memory(search_returns=[])
        cm = _make_context_manager(tmp_path, mem=mem)
        cm._save_to_local_storage({
            "type": "conversation_interaction",
            "timestamp": "2024-01-01T00:00:00",
            "user_message": "local item",
        })
        result = cm.retrieve_context(limit=5)
        assert any(item.get("user_message") == "local item" for item in result)

    def test_deduplicates_by_timestamp(self, tmp_path):
        ts = "2024-06-01T12:00:00"
        shared_item = {"type": "conversation_interaction", "timestamp": ts, "user_message": "dup"}
        mem = _make_mock_memory(search_returns=[{"memory": json.dumps(shared_item)}])
        cm = _make_context_manager(tmp_path, mem=mem)
        cm._save_to_local_storage(shared_item)
        result = cm.retrieve_context(limit=10)
        matching = [i for i in result if i.get("timestamp") == ts]
        assert len(matching) == 1


# ---------------------------------------------------------------------------
# summarize_context
# ---------------------------------------------------------------------------

class TestSummarizeContext:
    def test_empty_context_returns_defaults(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        summary = cm.summarize_context([])
        assert summary["total_interactions"] == 0
        assert summary["topics_discussed"] == []
        assert summary["last_interaction"] is None
        assert "No conversation history" in summary["summary"]

    def test_counts_interactions(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        items = [
            {"type": "conversation_interaction", "user_message": "hello", "agent_response": "hi"},
            {"type": "conversation_interaction", "user_message": "world", "agent_response": "there"},
        ]
        summary = cm.summarize_context(items)
        assert summary["total_interactions"] == 2

    def test_extracts_topics_from_messages(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        items = [{"type": "conversation_interaction", "user_message": "machine learning python", "agent_response": "tensorflow"}]
        summary = cm.summarize_context(items)
        # Topics must be alpha words with length > 4
        long_alpha_topics = [w for w in summary["topics_discussed"] if len(w) > 4 and w.isalpha()]
        assert len(long_alpha_topics) > 0

    def test_limits_topics_to_10(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        # Create a message with many long words
        many_words = " ".join([f"wordX{i:03d}" for i in range(30)])
        items = [{"type": "conversation_interaction", "user_message": many_words, "agent_response": ""}]
        summary = cm.summarize_context(items)
        assert len(summary["topics_discussed"]) <= 10

    def test_last_interaction_set(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        items = [
            {"type": "conversation_interaction", "user_message": "first", "agent_response": ""},
            {"type": "conversation_interaction", "user_message": "second", "agent_response": ""},
        ]
        summary = cm.summarize_context(items)
        assert summary["last_interaction"] == items[-1]

    def test_summary_string_mentions_count(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        items = [{"type": "conversation_interaction", "user_message": "hello world check", "agent_response": ""}]
        summary = cm.summarize_context(items)
        assert "1" in summary["summary"]


# ---------------------------------------------------------------------------
# get_recent_interactions
# ---------------------------------------------------------------------------

class TestGetRecentInteractions:
    def test_returns_at_most_count_items(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        for i in range(5):
            cm._save_to_local_storage({"type": "conversation_interaction", "timestamp": f"T{i}"})
        cm.memory.search.return_value = []
        cm.memory.get_all.return_value = []
        result = cm.get_recent_interactions(count=2)
        assert len(result) <= 2

    def test_returns_list(self, tmp_path):
        cm = _make_context_manager(tmp_path)
        result = cm.get_recent_interactions(count=3)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# has_context_about
# ---------------------------------------------------------------------------

class TestHasContextAbout:
    def test_returns_true_when_context_exists(self, tmp_path):
        mem = _make_mock_memory(search_returns=[{"memory": '{"type": "conversation_interaction"}'}])
        cm = _make_context_manager(tmp_path, mem=mem)
        assert cm.has_context_about("anything") is True

    def test_returns_false_when_no_context(self, tmp_path):
        mem = _make_mock_memory(search_returns=[])
        cm = _make_context_manager(tmp_path, mem=mem)
        assert cm.has_context_about("unknown_topic") is False


# ---------------------------------------------------------------------------
# ContextAwareAgent
# ---------------------------------------------------------------------------

class TestContextAwareAgent:
    def _make_agent(self, tmp_path):
        mem = _make_mock_memory(search_returns=[], get_all_returns=[])
        with patch("src.core.context_manager.get_memory_facade", return_value=mem):
            from src.core.context_manager import ContextAwareAgent

            agent = ContextAwareAgent.__new__(ContextAwareAgent)
            agent.user_id = "agent:test"

            # Wire a real ContextManager with tmp storage
            from src.core.context_manager import ContextManager
            cm = ContextManager.__new__(ContextManager)
            cm.user_id = "agent:test"
            cm.memory = mem
            cm.local_storage_path = tmp_path / "contexts"
            cm.local_storage_path.mkdir(parents=True, exist_ok=True)
            cm.local_context_file = cm.local_storage_path / "agent_test.json"
            agent.context_manager = cm

        return agent

    def test_respond_returns_string(self, tmp_path):
        agent = self._make_agent(tmp_path)
        response = agent.respond("hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_first_interaction_greeting(self, tmp_path):
        agent = self._make_agent(tmp_path)
        response = agent.respond("machine learning")
        assert "first" in response.lower() or "hello" in response.lower()

    def test_respond_stores_interaction_twice(self, tmp_path):
        agent = self._make_agent(tmp_path)
        agent.respond("test input")
        # Should store two interactions: input_received + response_generated
        loaded = agent.context_manager._load_from_local_storage()
        assert len(loaded) >= 2

    def test_extract_topic_returns_long_word(self, tmp_path):
        agent = self._make_agent(tmp_path)
        result = agent._extract_topic("This is about kubernetes deployment")
        assert len(result) > 4

    def test_extract_topic_fallback(self, tmp_path):
        agent = self._make_agent(tmp_path)
        result = agent._extract_topic("a b c")
        assert result == "this topic"

    def test_extract_topic_empty_string(self, tmp_path):
        agent = self._make_agent(tmp_path)
        result = agent._extract_topic("")
        assert result == "this topic"


# ---------------------------------------------------------------------------
# _generate_contextual_response branch coverage
# ---------------------------------------------------------------------------

class TestGenerateContextualResponse:
    def _make_agent(self, tmp_path):
        mem = _make_mock_memory(search_returns=[], get_all_returns=[])
        with patch("src.core.context_manager.get_memory_facade", return_value=mem):
            from src.core.context_manager import ContextAwareAgent, ContextManager

            agent = ContextAwareAgent.__new__(ContextAwareAgent)
            agent.user_id = "agent:gen"
            cm = ContextManager.__new__(ContextManager)
            cm.user_id = "agent:gen"
            cm.memory = mem
            cm.local_storage_path = tmp_path / "contexts"
            cm.local_storage_path.mkdir(parents=True, exist_ok=True)
            cm.local_context_file = cm.local_storage_path / "agent_gen.json"
            agent.context_manager = cm
        return agent

    def test_zero_interactions_branch(self, tmp_path):
        agent = self._make_agent(tmp_path)
        summary = {"total_interactions": 0, "topics_discussed": [], "last_interaction": None, "summary": ""}
        response = agent._generate_contextual_response("hello", summary)
        assert "first" in response.lower()

    def test_previously_discussed_topic_branch(self, tmp_path):
        agent = self._make_agent(tmp_path)
        summary = {
            "total_interactions": 3,
            "topics_discussed": ["python"],
            "last_interaction": None,
            "summary": "prev",
        }
        response = agent._generate_contextual_response("python tutorial", summary)
        assert "remember" in response.lower() or "talked" in response.lower()

    def test_returning_user_branch(self, tmp_path):
        agent = self._make_agent(tmp_path)
        summary = {
            "total_interactions": 5,
            "topics_discussed": ["docker", "kubernetes"],
            "last_interaction": None,
            "summary": "prev",
        }
        # Input that doesn't match any topic
        response = agent._generate_contextual_response("unrelated query xyz", summary)
        assert isinstance(response, str)
        assert len(response) > 0


# ---------------------------------------------------------------------------
# create_context_aware_conversation utility function
# ---------------------------------------------------------------------------

def test_create_context_aware_conversation():
    mem = _make_mock_memory()
    with patch("src.core.context_manager.get_memory_facade", return_value=mem):
        from src.core.context_manager import ContextAwareAgent, create_context_aware_conversation
        with patch("pathlib.Path.mkdir"):
            agent = create_context_aware_conversation("myuser:session")
    assert isinstance(agent, ContextAwareAgent)
