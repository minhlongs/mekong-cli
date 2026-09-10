# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for BuzzAdapter — v0.1 Buzz+Mekong autonomous runtime integration."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.core.buzz_adapter import BuzzAdapter, BuzzPayload, _urllib_transport


class TestBuzzPayloadDataclass:
    def test_default_values(self):
        bp = BuzzPayload(goal_text="hello")
        assert bp.goal_text == "hello"
        assert bp.context == {}
        assert bp.callback_url is None
        assert bp.mission_id is None

    def test_full_construction(self):
        bp = BuzzPayload(
            goal_text="deploy",
            context={"env": "staging"},
            callback_url="https://buzz.test/cb",
            mission_id="m-123",
        )
        assert bp.goal_text == "deploy"
        assert bp.context == {"env": "staging"}
        assert bp.callback_url == "https://buzz.test/cb"
        assert bp.mission_id == "m-123"


class TestReceiveGoal:
    def test_parses_goal_field(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({"goal": "analyze sales"})
        assert result["text"] == "analyze sales"
        assert result["context"] == {}
        assert result["mission_id"] is None
        assert result["callback_url"] is None

    def test_parses_text_field_as_fallback(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({"text": "fallback goal"})
        assert result["text"] == "fallback goal"

    def test_goal_field_takes_priority(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({"goal": "primary", "text": "secondary"})
        assert result["text"] == "primary"

    def test_raises_on_missing_goal(self):
        adapter = BuzzAdapter()
        with pytest.raises(ValueError, match="missing 'goal' field"):
            adapter.receive_goal({})

    def test_raises_on_empty_goal(self):
        adapter = BuzzAdapter()
        with pytest.raises(ValueError, match="missing 'goal' field"):
            adapter.receive_goal({"goal": ""})

    def test_with_callback_url(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({
            "goal": "task",
            "callback_url": "https://buzz.test/update",
        })
        assert result["callback_url"] == "https://buzz.test/update"

    def test_with_mission_id(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({
            "goal": "task",
            "mission_id": "mission-42",
        })
        assert result["mission_id"] == "mission-42"

    def test_with_context(self):
        adapter = BuzzAdapter()
        result = adapter.receive_goal({
            "goal": "task",
            "context": {"priority": "high", "source": "buzz"},
        })
        assert result["context"] == {"priority": "high", "source": "buzz"}


class TestSendUpdate:
    def test_returns_status_dict(self):
        adapter = BuzzAdapter()
        result = adapter.send_update("running", {"progress": 50})
        assert result == {"status": "running", "data": {"progress": 50}}

    def test_completed_status(self):
        adapter = BuzzAdapter()
        result = adapter.send_update("completed", {"output": "done"})
        assert result["status"] == "completed"
        assert result["data"]["output"] == "done"

    def test_send_update_with_callback_url_calls_transport(self):
        def mock_transport(url, payload):
            return 200
        adapter = BuzzAdapter(transport=mock_transport)
        result = adapter.send_update("running", {"step": 1}, callback_url="https://cb.test")
        assert result == {"status": "running", "data": {"step": 1}}

    def test_send_update_no_callback_noop(self):
        adapter = BuzzAdapter()
        result = adapter.send_update("running", {"step": 1})
        assert result == {"status": "running", "data": {"step": 1}}

    def test_send_update_transport_failure_swallows_exception(self):
        def failing_transport(url, payload):
            raise RuntimeError("network down")
        adapter = BuzzAdapter(transport=failing_transport)
        result = adapter.send_update("running", {"step": 1}, callback_url="https://cb.test")
        assert result == {"status": "running", "data": {"step": 1}}

    def test_send_update_non_2xx_logs_warning(self, caplog):
        caplog.set_level(logging.INFO)
        def bad_transport(url, payload):
            return 500
        adapter = BuzzAdapter(transport=bad_transport)
        adapter.send_update("failed", {"error": "oops"}, callback_url="https://cb.test")
        assert any("Buzz callback non-2xx (500) for https://cb.test" in rec.message for rec in caplog.records)

    def test_send_update_2xx_logs_delivered(self, caplog):
        caplog.set_level(logging.INFO)
        adapter = BuzzAdapter(transport=lambda u, p: 200)
        adapter.send_update("completed", {"result": "ok"}, callback_url="https://cb.test")
        assert any("Buzz callback delivered (200) to https://cb.test" in rec.message for rec in caplog.records)


class TestReceiveFeedback:
    def test_returns_feedback_dict(self):
        adapter = BuzzAdapter()
        fb = {"rating": 5, "comment": "great"}
        result = adapter.receive_feedback(fb)
        assert result == fb
        assert result["rating"] == 5

    def test_empty_feedback(self):
        adapter = BuzzAdapter()
        result = adapter.receive_feedback({})
        assert result == {}


class TestRuntimeProperty:
    def test_default_runtime_is_none(self):
        adapter = BuzzAdapter()
        assert adapter.runtime is None

    def test_runtime_assignment_via_property(self):
        adapter = BuzzAdapter()
        sentinel = object()
        adapter.runtime = sentinel
        assert adapter.runtime is sentinel

    def test_runtime_set_via_init(self):
        sentinel = object()
        adapter = BuzzAdapter(runtime=sentinel)
        assert adapter.runtime is sentinel


class TestTransportProperty:
    def test_default_transport_is_urllib(self):
        adapter = BuzzAdapter()
        assert adapter.transport is _urllib_transport

    def test_transport_setter(self):
        adapter = BuzzAdapter()
        def custom(u, p):
            return 204
        adapter.transport = custom
        assert adapter.transport is custom


class TestDefaultTransport:
    def test_urllib_transport_success(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_resp):
            code = _urllib_transport("https://example.com/cb", {"test": "data"})
            assert code == 200

    def test_urllib_transport_returns_zero_on_failure(self):
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            code = _urllib_transport("https://example.com/cb", {"test": "data"})
            assert code == 0