"""Tests for src/core/signals/posthog_sink.py — async PostHog event sink."""

from __future__ import annotations

import asyncio
import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.core.signals.posthog_sink as sink
from src.core.signals.events import MissionEvent


class TestPosthogSinkTypeChecking:
    def test_type_checking_import_branch(self):
        """Simulate TYPE_CHECKING=True to cover type-checking imports."""
        with patch("typing.TYPE_CHECKING", True):
            importlib.reload(sink)
        # Restore normal runtime state
        with patch("typing.TYPE_CHECKING", False):
            importlib.reload(sink)


class TestIsEnabled:
    def test_disabled_by_default(self):
        with patch.object(sink, "_ENABLED", False), patch.object(sink, "_POSTHOG_API_KEY", ""):
            assert sink._is_enabled() is False

    def test_enabled_flag_only_without_key_is_disabled(self):
        with patch.object(sink, "_ENABLED", True), patch.object(sink, "_POSTHOG_API_KEY", ""):
            assert sink._is_enabled() is False

    def test_key_only_without_flag_is_disabled(self):
        with patch.object(sink, "_ENABLED", False), patch.object(sink, "_POSTHOG_API_KEY", "phc_123"):
            assert sink._is_enabled() is False

    def test_enabled_when_both_present(self):
        with patch.object(sink, "_ENABLED", True), patch.object(sink, "_POSTHOG_API_KEY", "phc_123"):
            assert sink._is_enabled() is True


class TestEmit:
    def setup_method(self):
        sink._batch.clear()

    def teardown_method(self):
        sink._batch.clear()

    def test_emit_disabled_does_not_queue(self):
        event = MissionEvent(
            mission_id="m-1",
            agent_id="test",
            credits_used=1,
            success=True,
            duration_ms=100,
        )
        with patch.object(sink, "_is_enabled", return_value=False):
            sink.emit(event)
        assert len(sink._batch) == 0

    def test_emit_enabled_queues_event(self):
        event = MissionEvent(
            mission_id="m-1",
            agent_id="test",
            credits_used=1,
            success=True,
            duration_ms=100,
            user_id_hash="user_abc",
        )
        with patch.object(sink, "_is_enabled", return_value=True):
            sink.emit(event)
        assert len(sink._batch) == 1
        item = sink._batch[0]
        assert item["event"] == "mission_completed"
        assert item["distinct_id"] == "user_abc"
        assert item["properties"]["mission_id"] == "m-1"

    def test_emit_enabled_without_user_id_uses_mission_id(self):
        event = MissionEvent(
            mission_id="m-2",
            agent_id="test",
            credits_used=1,
            success=True,
            duration_ms=100,
            user_id_hash="",
        )
        with patch.object(sink, "_is_enabled", return_value=True):
            sink.emit(event)
        assert len(sink._batch) == 1
        assert sink._batch[0]["distinct_id"] == "m-2"

    def test_emit_large_batch_triggers_flush(self):
        event = MissionEvent(
            mission_id="m-3",
            agent_id="test",
            credits_used=1,
            success=True,
            duration_ms=100,
        )
        with patch.object(sink, "_is_enabled", return_value=True):
            # Pre-fill batch to 19 items
            sink._batch.extend([{"test": i} for i in range(19)])
            mock_loop = MagicMock()
            with patch("asyncio.get_event_loop", return_value=mock_loop):
                sink.emit(event)
            assert len(sink._batch) == 20
            mock_loop.create_task.assert_called_once()

    def test_emit_large_batch_no_running_loop_ignored(self):
        event = MissionEvent(
            mission_id="m-4",
            agent_id="test",
            credits_used=1,
            success=True,
            duration_ms=100,
        )
        with patch.object(sink, "_is_enabled", return_value=True), \
             patch.object(sink, "_flush_batch", return_value=None):
            sink._batch.extend([{"test": i} for i in range(19)])
            with patch("asyncio.get_event_loop", side_effect=RuntimeError("no loop")):
                sink.emit(event)
            assert len(sink._batch) == 20


class TestFlushBatch:
    def setup_method(self):
        sink._batch.clear()

    def teardown_method(self):
        sink._batch.clear()

    @pytest.mark.asyncio
    async def test_flush_empty_batch_noop(self):
        await sink._flush_batch()
        assert len(sink._batch) == 0

    @pytest.mark.asyncio
    async def test_flush_successful_post(self):
        sink._batch = [{"event": "test"}]
        mock_resp = MagicMock()
        mock_resp.status = 200

        mock_post_context = MagicMock()
        mock_post_context.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post_context.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_post_context

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        mock_aiohttp = MagicMock()
        mock_aiohttp.ClientSession.return_value = mock_session_context
        mock_aiohttp.ClientTimeout = MagicMock()

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            await sink._flush_batch()

        assert len(sink._batch) == 0
        mock_session_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_rejected_post_logs_warning(self):
        sink._batch = [{"event": "test"}]
        mock_resp = MagicMock()
        mock_resp.status = 400

        mock_post_context = MagicMock()
        mock_post_context.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post_context.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_post_context

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        mock_aiohttp = MagicMock()
        mock_aiohttp.ClientSession.return_value = mock_session_context
        mock_aiohttp.ClientTimeout = MagicMock()

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            await sink._flush_batch()

        assert len(sink._batch) == 0

    @pytest.mark.asyncio
    async def test_flush_exception_swallowed(self):
        sink._batch = [{"event": "test"}]
        with patch.dict("sys.modules", {"aiohttp": None}):
            # Importing aiohttp raises ImportError, caught and swallowed
            await sink._flush_batch()
        assert len(sink._batch) == 0


class TestStartBackgroundFlush:
    def test_start_flush_disabled_noop(self):
        with patch.object(sink, "_is_enabled", return_value=False):
            sink.start_background_flush()
        assert sink._flush_task is None

    def test_start_flush_enabled_creates_task(self):
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_task = MagicMock()
        mock_loop.create_task.return_value = mock_task

        with patch.object(sink, "_is_enabled", return_value=True), \
             patch("asyncio.get_event_loop", return_value=mock_loop):
            sink.start_background_flush()

        assert sink._flush_task is mock_task

    def test_start_flush_no_loop_ignored(self):
        with patch.object(sink, "_is_enabled", return_value=True), \
             patch("asyncio.get_event_loop", side_effect=RuntimeError("no loop")):
            sink.start_background_flush()


class TestPeriodicFlush:
    @pytest.mark.asyncio
    async def test_periodic_flush_calls_flush(self):
        with patch.object(sink, "_flush_batch", new_callable=AsyncMock) as mock_flush:
            task = asyncio.create_task(sink._periodic_flush(interval=0.001))
            await asyncio.sleep(0.005)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert mock_flush.called

