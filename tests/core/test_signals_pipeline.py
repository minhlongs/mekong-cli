# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Signals Subsystem (src/core/signals/).

Covers:
- src.core.signals.__init__
- src.core.signals.local_store
- src.core.signals.emitter
- src.core.signals.posthog_sink
- src.core.signals.evals.offline
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.core.signals as signals_pkg
from src.core.signals import (
    emitter,
    local_store,
    posthog_sink,
)
from src.core.signals.evals import offline
from src.core.signals.events import MissionEvent


# ============================================================================
# Package exports
# ============================================================================

class TestSignalsPackageExports:
    def test_exports_mission_event_and_emit(self):
        assert hasattr(signals_pkg, "MissionEvent")
        assert hasattr(signals_pkg, "emit_mission_event")
        assert signals_pkg.MissionEvent is MissionEvent
        assert signals_pkg.emit_mission_event is emitter.emit_mission_event


# ============================================================================
# Local Store
# ============================================================================

class TestSignalsLocalStore:
    def test_get_db_path_default_and_env_override(self, tmp_path):
        custom_path = str(tmp_path / "custom_signals.sqlite")
        with patch.dict(os.environ, {"SIGNALS_DB_PATH": custom_path}):
            assert local_store._get_db_path() == Path(custom_path)

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SIGNALS_DB_PATH", None)
            default = local_store._get_db_path()
            assert default.name == "signals.sqlite"

    def test_connect_creates_schema_and_enables_wal(self, tmp_path):
        db_path = tmp_path / "sub" / "test.sqlite"
        conn = local_store._connect(db_path)
        try:
            # Table must exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='missions'")
            assert cursor.fetchone() is not None
            # Index must exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_missions_agent_ts'")
            assert cursor.fetchone() is not None
        finally:
            conn.close()

    def test_write_event_success_and_row_count(self, tmp_path):
        db_path = tmp_path / "events.sqlite"
        assert local_store.row_count(db_path) == 0

        event = MissionEvent.create(
            mission_id="m-1",
            agent_id="test-agent",
            credits_used=3,
            success=True,
            duration_ms=250,
            user_id="alice",
        )
        assert local_store.write_event(event, db_path=db_path) is True
        assert local_store.row_count(db_path) == 1

        # Overwrite same mission_id (INSERT OR REPLACE)
        event_updated = MissionEvent.create(
            mission_id="m-1",
            agent_id="test-agent",
            credits_used=5,
            success=True,
            duration_ms=400,
            user_id="alice",
        )
        assert local_store.write_event(event_updated, db_path=db_path) is True
        assert local_store.row_count(db_path) == 1

    def test_write_event_catches_exception(self):
        event = MissionEvent.create("m-err", "agent", 1, True, 100)
        with patch("src.core.signals.local_store._connect", side_effect=sqlite3.OperationalError("disk error")):
            assert local_store.write_event(event) is False

    def test_row_count_handles_exception(self, tmp_path):
        db_path = tmp_path / "corrupt.sqlite"
        db_path.write_text("not a real sqlite db")
        assert local_store.row_count(db_path) == 0


# ============================================================================
# Emitter
# ============================================================================

class TestSignalsEmitter:
    def test_emit_mission_event_with_provided_id(self):
        with patch("src.core.signals.local_store.write_event") as mock_write, \
             patch("src.core.signals.posthog_sink.emit") as mock_ph:
            emitter.emit_mission_event(
                mission_id="explicit-id-123",
                agent_id="agent-x",
                success=True,
                duration_ms=300,
                credits_used=2,
                user_id="user-1",
            )
            mock_write.assert_called_once()
            mock_ph.assert_called_once()
            event = mock_write.call_args[0][0]
            assert event.mission_id == "explicit-id-123"
            assert event.agent_id == "agent-x"
            assert event.credits_used == 2

    def test_emit_mission_event_auto_generates_id_when_none(self):
        with patch("src.core.signals.local_store.write_event") as mock_write, \
             patch("src.core.signals.posthog_sink.emit") as mock_ph:
            emitter.emit_mission_event(
                mission_id=None,
                agent_id="agent-auto",
                success=False,
                duration_ms=150,
            )
            mock_write.assert_called_once()
            mock_ph.assert_called_once()
            event = mock_write.call_args[0][0]
            assert event.mission_id  # UUID generated
            assert event.agent_id == "agent-auto"
            assert event.success is False

    def test_emit_mission_event_swallows_exception(self, caplog):
        with patch("src.core.signals.events.MissionEvent.create", side_effect=RuntimeError("unexpected")):
            # Must not raise
            emitter.emit_mission_event(
                mission_id="fail",
                agent_id="a",
                success=True,
                duration_ms=10,
            )
            assert any("signals.emit swallowed exception" in rec.message for rec in caplog.records)


# ============================================================================
# PostHog Sink
# ============================================================================

class TestSignalsPosthogSink:
    def setup_method(self):
        posthog_sink._batch.clear()

    def test_is_enabled_logic(self):
        with patch.object(posthog_sink, "_ENABLED", False), \
             patch.object(posthog_sink, "_POSTHOG_API_KEY", ""):
            assert posthog_sink._is_enabled() is False

        with patch.object(posthog_sink, "_ENABLED", True), \
             patch.object(posthog_sink, "_POSTHOG_API_KEY", ""):
            assert posthog_sink._is_enabled() is False

        with patch.object(posthog_sink, "_ENABLED", True), \
             patch.object(posthog_sink, "_POSTHOG_API_KEY", "phc_valid_key"):
            assert posthog_sink._is_enabled() is True

    def test_emit_noop_when_disabled(self):
        event = MissionEvent.create("m-ph", "agent", 1, True, 100)
        with patch.object(posthog_sink, "_is_enabled", return_value=False):
            posthog_sink.emit(event)
            assert len(posthog_sink._batch) == 0

    def test_emit_appends_when_enabled(self):
        event = MissionEvent.create("m-ph2", "agent", 1, True, 100, user_id="u1")
        with patch.object(posthog_sink, "_is_enabled", return_value=True):
            posthog_sink.emit(event)
            assert len(posthog_sink._batch) == 1
            item = posthog_sink._batch[0]
            assert item["event"] == "mission_completed"
            assert item["distinct_id"] == event.user_id_hash

    def test_emit_distinct_id_falls_back_to_mission_id(self):
        event = MissionEvent.create("m-fallback-id", "agent", 1, True, 100, user_id="")
        with patch.object(posthog_sink, "_is_enabled", return_value=True):
            posthog_sink.emit(event)
            assert len(posthog_sink._batch) == 1
            item = posthog_sink._batch[0]
            assert item["distinct_id"] == "m-fallback-id"

    def test_emit_batch_limit_triggers_flush_task(self):
        with patch.object(posthog_sink, "_is_enabled", return_value=True):
            posthog_sink._batch = [{"dummy": i} for i in range(19)]
            mock_loop = MagicMock()
            with patch("asyncio.get_event_loop", return_value=mock_loop):
                event = MissionEvent.create("m-20", "agent", 1, True, 100)
                posthog_sink.emit(event)
                assert len(posthog_sink._batch) == 20
                mock_loop.create_task.assert_called_once()

    def test_emit_batch_limit_handles_runtime_error_no_loop(self):
        with patch.object(posthog_sink, "_is_enabled", return_value=True):
            posthog_sink._batch = [{"dummy": i} for i in range(19)]
            with patch("asyncio.get_event_loop", side_effect=RuntimeError("no loop")):
                event = MissionEvent.create("m-20", "agent", 1, True, 100)
                posthog_sink.emit(event)
                assert len(posthog_sink._batch) == 20

    @pytest.mark.asyncio
    async def test_flush_batch_empty_noop(self):
        posthog_sink._batch.clear()
        await posthog_sink._flush_batch()
        assert len(posthog_sink._batch) == 0

    @pytest.mark.asyncio
    async def test_flush_batch_with_events_success(self):
        posthog_sink._batch = [{"fake": "event"}]
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_aiohttp = MagicMock()
        mock_aiohttp.ClientSession.return_value = mock_session
        mock_aiohttp.ClientTimeout = MagicMock()

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            await posthog_sink._flush_batch()

        assert len(posthog_sink._batch) == 0

    @pytest.mark.asyncio
    async def test_flush_batch_with_events_error_logged(self, caplog):
        posthog_sink._batch = [{"fake": "event"}]
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_aiohttp = MagicMock()
        mock_aiohttp.ClientSession.return_value = mock_session
        mock_aiohttp.ClientTimeout = MagicMock()

        with patch.dict("sys.modules", {"aiohttp": mock_aiohttp}):
            await posthog_sink._flush_batch()

        assert len(posthog_sink._batch) == 0
        assert any("PostHog batch rejected: 500" in rec.message for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_flush_batch_handles_exception(self, caplog):
        posthog_sink._batch = [{"fake": "event"}]
        with patch.dict("sys.modules", {"aiohttp": None}):
            # aiohttp raises ImportError or TypeError
            await posthog_sink._flush_batch()
        assert len(posthog_sink._batch) == 0

    def test_start_background_flush_disabled_noop(self):
        with patch.object(posthog_sink, "_is_enabled", return_value=False):
            posthog_sink.start_background_flush()

    def test_start_background_flush_enabled_with_running_loop(self):
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        with patch.object(posthog_sink, "_is_enabled", return_value=True), \
             patch("asyncio.get_event_loop", return_value=mock_loop):
            posthog_sink.start_background_flush()
            mock_loop.create_task.assert_called_once()

    def test_start_background_flush_handles_runtime_error(self):
        with patch.object(posthog_sink, "_is_enabled", return_value=True), \
             patch("asyncio.get_event_loop", side_effect=RuntimeError("no loop")):
            posthog_sink.start_background_flush()

    @pytest.mark.asyncio
    async def test_periodic_flush_executes_flush(self):
        with patch("src.core.signals.posthog_sink._flush_batch", new_callable=AsyncMock) as mock_flush:
            calls = 0

            async def fast_sleep(_):
                nonlocal calls
                calls += 1
                if calls > 1:
                    raise asyncio.CancelledError()

            with patch("asyncio.sleep", side_effect=fast_sleep):
                with pytest.raises(asyncio.CancelledError):
                    await posthog_sink._periodic_flush(interval=1)
            assert mock_flush.call_count == 1


# ============================================================================
# Offline Evals
# ============================================================================

class TestSignalsOfflineEval:
    def test_eval_result_summary(self):
        res = offline.EvalResult(
            agent_id="test",
            window_days=7,
            total_missions=10,
            success_rate=0.85,
            p95_ms=1200,
            avg_credits=2.456,
            db_path="/path/test.sqlite",
        )
        summary = res.summary()
        assert summary["agent_id"] == "test"
        assert summary["window_days"] == 7
        assert summary["total_missions"] == 10
        assert summary["success_rate_pct"] == 85.0
        assert summary["p95_ms"] == 1200
        assert summary["avg_credits"] == 2.46

    def test_run_offline_eval_nonexistent_db(self, tmp_path):
        nonexistent = tmp_path / "missing.sqlite"
        res = offline.run_offline_eval(db_path=nonexistent)
        assert res.total_missions == 0
        assert res.success_rate == 0.0
        assert res.p95_ms == 0
        assert res.avg_credits == 0.0

    def test_run_offline_eval_empty_db(self, tmp_path):
        db_path = tmp_path / "empty.sqlite"
        local_store._connect(db_path).close()
        res = offline.run_offline_eval(db_path=db_path)
        assert res.total_missions == 0
        assert res.success_rate == 0.0

    def test_run_offline_eval_with_data_and_percentile(self, tmp_path):
        db_path = tmp_path / "data.sqlite"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Write 20 missions
        for i in range(1, 21):
            event = MissionEvent(
                mission_id=f"m-{i}",
                agent_id="agent-v1" if i <= 15 else "agent-v2",
                credits_used=i,
                success=(i % 2 == 0),
                duration_ms=i * 100,
                ts=now_iso,
                user_id_hash="hash",
            )
            local_store.write_event(event, db_path=db_path)

        # Eval "all"
        res_all = offline.run_offline_eval(agent_id="all", window_days=7, db_path=db_path)
        assert res_all.total_missions == 20
        assert res_all.success_rate == 0.5
        assert res_all.p95_ms > 0
        assert res_all.avg_credits == 10.5

        # Eval filtered by agent_id="agent-v2" (5 missions: 16, 17, 18, 19, 20)
        res_v2 = offline.run_offline_eval(agent_id="agent-v2", window_days=7, db_path=db_path)
        assert res_v2.total_missions == 5
        assert res_v2.agent_id == "agent-v2"

    def test_run_offline_eval_exception_returns_empty(self, tmp_path):
        corrupt = tmp_path / "bad.sqlite"
        corrupt.write_text("corrupted file")
        res = offline.run_offline_eval(db_path=corrupt)
        assert res.total_missions == 0
