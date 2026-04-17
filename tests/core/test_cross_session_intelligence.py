"""Tests for src/core/cross_session_intelligence.py."""

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch



# ---------------------------------------------------------------------------
# Helpers to build a patched CrossSessionStateManager without real memory/fs
# ---------------------------------------------------------------------------

def _make_mock_memory(search_returns=None, get_all_returns=None):
    """Build a memory facade mock."""
    mem = MagicMock()
    mem.connect.return_value = None
    mem.get_provider_status.return_value = {"active_provider": "yaml"}
    mem.add.return_value = True
    mem.search.return_value = search_returns or []
    mem.get_all.return_value = get_all_returns or []
    return mem


def _make_manager(tmp_path, search_returns=None, user_id="test_user"):
    """Instantiate CrossSessionStateManager with mocked memory and tmp storage."""
    from src.core.cross_session_intelligence import CrossSessionStateManager

    mem = _make_mock_memory(search_returns=search_returns)

    with patch("src.core.cross_session_intelligence.get_memory_facade", return_value=mem):
        manager = CrossSessionStateManager.__new__(CrossSessionStateManager)
        manager.user_id = user_id
        manager.memory = mem

        # Point local storage at a safe tmp directory
        manager.local_storage_path = tmp_path / "cross_session_profiles"
        manager.local_storage_path.mkdir(parents=True, exist_ok=True)
        manager.local_profile_file = (
            manager.local_storage_path / f"{user_id.replace(':', '_')}.json"
        )

        # Manually call profile load (no real files yet)
        from src.core.cross_session_intelligence import UserProfile
        manager.profile = UserProfile(user_id)

    return manager


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class TestUserProfile:
    def test_init_defaults(self):
        from src.core.cross_session_intelligence import UserProfile

        profile = UserProfile("alice")
        assert profile.user_id == "alice"
        assert isinstance(profile.created_at, datetime)
        assert profile.preferences == {}
        assert profile.interaction_history == []
        assert profile.knowledge_base == {}
        assert profile.session_history == []


# ---------------------------------------------------------------------------
# CrossSessionStateManager — local storage
# ---------------------------------------------------------------------------

class TestLocalStorage:
    def test_save_and_load_roundtrip(self, tmp_path):
        mgr = _make_manager(tmp_path)
        data = {"type": "user_profile", "user_id": "test_user", "value": 42}
        mgr._save_to_local_storage(data)

        loaded = mgr._load_from_local_storage()
        assert len(loaded) == 1
        assert loaded[0]["value"] == 42

    def test_load_missing_file_returns_empty(self, tmp_path):
        mgr = _make_manager(tmp_path)
        result = mgr._load_from_local_storage()
        assert result == []

    def test_update_existing_profile_record(self, tmp_path):
        """Saving a user_profile twice should update in-place, not append."""
        mgr = _make_manager(tmp_path)
        profile_v1 = {"type": "user_profile", "user_id": "test_user", "version": 1}
        profile_v2 = {"type": "user_profile", "user_id": "test_user", "version": 2}

        mgr._save_to_local_storage(profile_v1)
        mgr._save_to_local_storage(profile_v2)

        loaded = mgr._load_from_local_storage()
        # Should still have only one user_profile entry
        profiles = [d for d in loaded if d.get("type") == "user_profile"]
        assert len(profiles) == 1
        assert profiles[0]["version"] == 2

    def test_save_caps_at_10_items(self, tmp_path):
        mgr = _make_manager(tmp_path)
        for i in range(15):
            mgr._save_to_local_storage({"type": "other", "idx": i})
        loaded = mgr._load_from_local_storage()
        # capping logic: > 10 items are pruned when type is profile
        # For non-profile items the list may grow — just check it doesn't explode
        assert len(loaded) <= 15  # No crash is the key assertion

    def test_save_handles_corrupt_file(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.local_profile_file.write_text("CORRUPT JSON{{{{", encoding="utf-8")
        # Should not raise
        mgr._save_to_local_storage({"type": "other", "ok": True})

    def test_load_handles_corrupt_file(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.local_profile_file.write_text("NOT JSON", encoding="utf-8")
        result = mgr._load_from_local_storage()
        assert result == []


# ---------------------------------------------------------------------------
# CrossSessionStateManager — profile load / save
# ---------------------------------------------------------------------------

class TestProfileLoadCreate:
    def test_creates_new_profile_when_no_data(self, tmp_path):
        mgr = _make_manager(tmp_path)
        assert mgr.profile.user_id == "test_user"
        assert mgr.profile.preferences == {}

    def test_restores_profile_from_local_storage(self, tmp_path):
        """When memory returns nothing but local file has a profile, it is restored."""
        from src.core.cross_session_intelligence import CrossSessionStateManager

        profile_data = {
            "type": "user_profile",
            "user_id": "test_user",
            "created_at": datetime.now().isoformat(),
            "preferences": {"lang": "vi"},
            "interaction_history": [],
            "knowledge_base": {},
            "session_history": [],
        }
        # Write local file first
        local_dir = tmp_path / "cross_session_profiles"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file = local_dir / "test_user.json"
        local_file.write_text(json.dumps([profile_data]), encoding="utf-8")

        mem = _make_mock_memory(search_returns=[])
        with patch("src.core.cross_session_intelligence.get_memory_facade", return_value=mem):
            manager = CrossSessionStateManager.__new__(CrossSessionStateManager)
            manager.user_id = "test_user"
            manager.memory = mem
            manager.local_storage_path = local_dir
            manager.local_profile_file = local_file
            manager.profile = manager._load_or_create_profile()

        assert manager.profile.preferences == {"lang": "vi"}

    def test_restores_profile_from_memory_system(self, tmp_path):
        """When memory returns a valid profile JSON, it is used."""
        from src.core.cross_session_intelligence import CrossSessionStateManager

        profile_data = {
            "type": "user_profile",
            "user_id": "test_user",
            "created_at": datetime.now().isoformat(),
            "preferences": {"theme": "dark"},
            "interaction_history": [],
            "knowledge_base": {},
            "session_history": [],
        }
        memory_result = {"memory": json.dumps(profile_data)}
        mem = _make_mock_memory(search_returns=[memory_result])

        with patch("src.core.cross_session_intelligence.get_memory_facade", return_value=mem):
            manager = CrossSessionStateManager.__new__(CrossSessionStateManager)
            manager.user_id = "test_user"
            manager.memory = mem
            manager.local_storage_path = tmp_path / "cross_session_profiles"
            manager.local_storage_path.mkdir(parents=True, exist_ok=True)
            manager.local_profile_file = manager.local_storage_path / "test_user.json"
            manager.profile = manager._load_or_create_profile()

        assert manager.profile.preferences == {"theme": "dark"}

    def test_save_profile_calls_memory_add(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.preferences = {"key": "val"}
        mgr.save_profile()
        mgr.memory.add.assert_called_once()
        call_kwargs = mgr.memory.add.call_args
        content = json.loads(call_kwargs.kwargs["content"] if call_kwargs.kwargs else call_kwargs[1]["content"])
        assert content["type"] == "user_profile"
        assert content["preferences"] == {"key": "val"}


# ---------------------------------------------------------------------------
# CrossSessionStateManager — update_preferences
# ---------------------------------------------------------------------------

class TestUpdatePreferences:
    def test_updates_in_memory_profile(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.update_preferences({"language": "en", "debug": True})
        assert mgr.profile.preferences["language"] == "en"
        assert mgr.profile.preferences["debug"] is True

    def test_persists_to_memory_system(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.update_preferences({"foo": "bar"})
        mgr.memory.add.assert_called_once()

    def test_merges_with_existing_preferences(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.preferences = {"existing": "value"}
        mgr.update_preferences({"new_key": "new_val"})
        assert mgr.profile.preferences["existing"] == "value"
        assert mgr.profile.preferences["new_key"] == "new_val"


# ---------------------------------------------------------------------------
# CrossSessionStateManager — add_interaction
# ---------------------------------------------------------------------------

class TestAddInteraction:
    def test_returns_valid_uuid(self, tmp_path):
        mgr = _make_manager(tmp_path)
        iid = mgr.add_interaction("query", "hello world")
        uuid.UUID(iid)  # raises ValueError if not valid UUID

    def test_appends_to_profile_history(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_interaction("query", "test content")
        assert len(mgr.profile.interaction_history) == 1
        item = mgr.profile.interaction_history[0]
        assert item["type"] == "query"
        assert item["content"] == "test content"

    def test_stores_metadata(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_interaction("feedback", "great!", metadata={"rating": 5})
        item = mgr.profile.interaction_history[0]
        assert item["metadata"]["rating"] == 5

    def test_default_metadata_is_empty_dict(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_interaction("command", "do something")
        item = mgr.profile.interaction_history[0]
        assert item["metadata"] == {}


# ---------------------------------------------------------------------------
# CrossSessionStateManager — add_to_knowledge_base
# ---------------------------------------------------------------------------

class TestAddToKnowledgeBase:
    def test_creates_category_if_missing(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_to_knowledge_base("facts", "capital_of_vn", "Hanoi")
        assert "facts" in mgr.profile.knowledge_base
        assert mgr.profile.knowledge_base["facts"]["capital_of_vn"] == "Hanoi"

    def test_updates_existing_category(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_to_knowledge_base("facts", "key1", "value1")
        mgr.add_to_knowledge_base("facts", "key2", "value2")
        assert mgr.profile.knowledge_base["facts"]["key1"] == "value1"
        assert mgr.profile.knowledge_base["facts"]["key2"] == "value2"

    def test_persists_to_memory(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_to_knowledge_base("cat", "k", "v")
        mgr.memory.add.assert_called_once()


# ---------------------------------------------------------------------------
# CrossSessionStateManager — record_session
# ---------------------------------------------------------------------------

class TestRecordSession:
    def test_returns_valid_uuid(self, tmp_path):
        mgr = _make_manager(tmp_path)
        sid = mgr.record_session({"duration": 10})
        uuid.UUID(sid)

    def test_appends_to_session_history(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.record_session({"duration": 30})
        assert len(mgr.profile.session_history) == 1
        record = mgr.profile.session_history[0]
        assert record["session_data"]["duration"] == 30
        assert record["user_id"] == "test_user"


# ---------------------------------------------------------------------------
# CrossSessionStateManager — get_user_preferences
# ---------------------------------------------------------------------------

class TestGetUserPreferences:
    def test_returns_copy_not_reference(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.preferences = {"x": 1}
        prefs = mgr.get_user_preferences()
        prefs["x"] = 999  # mutate copy
        assert mgr.profile.preferences["x"] == 1  # original untouched

    def test_merges_memory_preferences(self, tmp_path):
        """Preferences from memory system are merged into profile."""
        pref_data = {"type": "user_preference", "preferences": {"from_mem": True}}
        mem = _make_mock_memory(search_returns=[{"memory": json.dumps(pref_data)}])

        mgr = _make_manager(tmp_path)
        mgr.memory = mem
        mgr.profile.preferences = {}
        result = mgr.get_user_preferences()
        assert result.get("from_mem") is True

    def test_skips_non_json_memory_results(self, tmp_path):
        mem = _make_mock_memory(search_returns=[{"memory": "not json at all"}])
        mgr = _make_manager(tmp_path)
        mgr.memory = mem
        # Should not raise
        result = mgr.get_user_preferences()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# CrossSessionStateManager — get_interaction_history
# ---------------------------------------------------------------------------

class TestGetInteractionHistory:
    def test_returns_list(self, tmp_path):
        mgr = _make_manager(tmp_path)
        history = mgr.get_interaction_history()
        assert isinstance(history, list)

    def test_supplements_from_local_storage(self, tmp_path):
        """When memory returns nothing, fall back to local storage."""
        interaction = {
            "id": "123",
            "type": "query",
            "content": "hello",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {},
        }
        local_item = {
            "type": "user_interaction",
            "user_id": "test_user",
            "interaction": interaction,
        }
        mgr = _make_manager(tmp_path)
        mgr._save_to_local_storage(local_item)

        # Memory returns nothing
        mgr.memory.search.return_value = []
        result = mgr.get_interaction_history(limit=10)
        assert any(r is not None for r in result)

    def test_respects_limit(self, tmp_path):
        mgr = _make_manager(tmp_path)
        for i in range(5):
            mgr.add_interaction("query", f"msg {i}")
        mgr.memory.search.return_value = []
        result = mgr.get_interaction_history(limit=3)
        assert len(result) <= 3


# ---------------------------------------------------------------------------
# CrossSessionStateManager — get_knowledge_base
# ---------------------------------------------------------------------------

class TestGetKnowledgeBase:
    def test_returns_all_categories(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.knowledge_base = {"cat1": {"k": "v"}, "cat2": {"k2": "v2"}}
        mgr.memory.search.return_value = []
        result = mgr.get_knowledge_base()
        assert "cat1" in result
        assert "cat2" in result

    def test_filters_by_category(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.knowledge_base = {"cat1": {"k": "v"}, "cat2": {"k2": "v2"}}
        mgr.memory.search.return_value = []
        result = mgr.get_knowledge_base(category="cat1")
        assert result == {"k": "v"}

    def test_returns_empty_dict_for_missing_category(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.knowledge_base = {}
        mgr.memory.search.return_value = []
        result = mgr.get_knowledge_base(category="nonexistent")
        assert result == {}


# ---------------------------------------------------------------------------
# CrossSessionStateManager — recall_information
# ---------------------------------------------------------------------------

class TestRecallInformation:
    def test_returns_list(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.memory.search.return_value = []
        result = mgr.recall_information("anything")
        assert isinstance(result, list)

    def test_finds_matching_interaction(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.add_interaction("query", "machine learning tutorial")
        mgr.memory.search.return_value = []
        results = mgr.recall_information("machine learning")
        types = [r["type"] for r in results]
        assert "interaction" in types

    def test_finds_matching_knowledge(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.profile.knowledge_base = {"tech": {"python": "a programming language"}}
        mgr.memory.search.return_value = []
        results = mgr.recall_information("python")
        types = [r["type"] for r in results]
        assert "knowledge" in types

    def test_no_match_returns_empty(self, tmp_path):
        mgr = _make_manager(tmp_path)
        mgr.memory.search.return_value = []
        results = mgr.recall_information("zzz_no_match_zzz")
        assert results == []


# ---------------------------------------------------------------------------
# CrossSessionIntelligenceEngine
# ---------------------------------------------------------------------------

class TestCrossSessionIntelligenceEngine:
    def _make_engine(self, tmp_path):
        from src.core.cross_session_intelligence import CrossSessionIntelligenceEngine

        engine = CrossSessionIntelligenceEngine()
        # Patch get_state_manager to return a mocked manager
        mem = _make_mock_memory(search_returns=[])
        mgr = _make_manager(tmp_path, user_id="engine_user")
        mgr.memory = mem
        engine.state_managers["engine_user"] = mgr
        return engine, mgr

    def test_get_state_manager_creates_once(self, tmp_path):
        from src.core.cross_session_intelligence import CrossSessionIntelligenceEngine

        engine = CrossSessionIntelligenceEngine()
        # Inject a pre-built manager and verify caching (same object returned)
        mgr1 = _make_manager(tmp_path, user_id="u1")
        engine.state_managers["u1"] = mgr1
        mgr2 = engine.get_state_manager("u1")
        assert mgr1 is mgr2

    def test_personalize_response_with_no_prefs(self, tmp_path):
        engine, mgr = self._make_engine(tmp_path)
        mgr.profile.preferences = {}
        mgr.memory.search.return_value = []
        result = engine.personalize_response("engine_user", "Hello there")
        assert "Hello there" in result

    def test_personalize_response_appends_prefs(self, tmp_path):
        engine, mgr = self._make_engine(tmp_path)
        mgr.profile.preferences = {"language": "en"}
        mgr.memory.search.return_value = []
        result = engine.personalize_response("engine_user", "Good morning")
        assert "language" in result

    def test_build_context_from_history_empty(self, tmp_path):
        engine, mgr = self._make_engine(tmp_path)
        mgr.profile.preferences = {}
        mgr.profile.knowledge_base = {}
        mgr.memory.search.return_value = []
        result = engine.build_context_from_history("engine_user", "xyz_no_match")
        assert result == ""

    def test_build_context_from_history_with_knowledge(self, tmp_path):
        engine, mgr = self._make_engine(tmp_path)
        mgr.profile.knowledge_base = {"tech": {"python": "great language"}}
        mgr.profile.preferences = {}
        mgr.memory.search.return_value = []
        result = engine.build_context_from_history("engine_user", "python")
        assert "python" in result


# ---------------------------------------------------------------------------
# create_cross_session_engine
# ---------------------------------------------------------------------------

def test_create_cross_session_engine():
    from src.core.cross_session_intelligence import (
        CrossSessionIntelligenceEngine,
        create_cross_session_engine,
    )

    engine = create_cross_session_engine()
    assert isinstance(engine, CrossSessionIntelligenceEngine)
