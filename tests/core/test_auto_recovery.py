"""Comprehensive unit tests for src/core/auto_recovery.py.

Covers 100% of:
- RecoveryType & RecoveryStatus enums
- RecoveryAttempt dataclass (to_dict, from_dict)
- RecoveryConfig dataclass & exponential backoff calculation
- RecoveryAction execution (sync & async callables, exception handling)
- AutoRecovery lifecycle, action registry, history persistence & loading
- attempt_recovery workflow with exponential backoff, success, retry, and exhaustion
- Event bus event emission across all status transitions
- Built-in recovery actions:
  - proxy recovery (script execution, returncodes, timeouts, exceptions, fallback)
  - restart proxy service (success & exception)
  - restart health endpoint (success & exception)
  - crash recovery (launchctl, systemctl, exceptions, and fallback)
  - license recovery
- Recovery analytics (get_recovery_statistics with empty and non-empty data)
- Recovery history querying & filtering (get_recent_recoveries)
- History clearing (with & without existing file, error resilience)
- Singleton helpers (get_auto_recovery, reset_auto_recovery, attempt_recovery)
- Export completeness
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.auto_recovery import (
    AutoRecovery,
    RecoveryAction,
    RecoveryAttempt,
    RecoveryConfig,
    RecoveryStatus,
    RecoveryType,
    attempt_recovery,
    get_auto_recovery,
    reset_auto_recovery,
)
from src.core.event_bus import EventType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestRecoveryEnums:
    def test_recovery_type_values(self) -> None:
        assert RecoveryType.LICENSE_RECOVERY.value == "license:recovery"
        assert RecoveryType.CRASH_RECOVERY.value == "crash:recovery"
        assert RecoveryType.HEALTH_ENDPOINT_RECOVERY.value == "health:endpoint_recovery"
        assert RecoveryType.PROXY_RECOVERY.value == "proxy:recovery"

    def test_recovery_status_values(self) -> None:
        assert RecoveryStatus.PENDING.value == "pending"
        assert RecoveryStatus.IN_PROGRESS.value == "in_progress"
        assert RecoveryStatus.SUCCESS.value == "success"
        assert RecoveryStatus.FAILED.value == "failed"
        assert RecoveryStatus.EXHAUSTED.value == "exhausted"


# ---------------------------------------------------------------------------
# RecoveryAttempt dataclass
# ---------------------------------------------------------------------------


class TestRecoveryAttempt:
    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        now = time.time()
        attempt = RecoveryAttempt(
            recovery_id="rec-123",
            recovery_type=RecoveryType.PROXY_RECOVERY,
            timestamp=now,
            attempt_number=2,
            status=RecoveryStatus.IN_PROGRESS,
            delay_seconds=2.0,
            error_message="failed once",
            duration_ms=150.5,
            metadata={"source": "test"},
        )

        data = attempt.to_dict()
        assert data["recovery_id"] == "rec-123"
        assert data["recovery_type"] == "proxy:recovery"
        assert data["timestamp"] == now
        assert data["attempt_number"] == 2
        assert data["status"] == "in_progress"
        assert data["delay_seconds"] == 2.0
        assert data["error_message"] == "failed once"
        assert data["duration_ms"] == 150.5
        assert data["metadata"] == {"source": "test"}

        loaded = RecoveryAttempt.from_dict(data)
        assert loaded.recovery_id == attempt.recovery_id
        assert loaded.recovery_type == attempt.recovery_type
        assert loaded.timestamp == attempt.timestamp
        assert loaded.attempt_number == attempt.attempt_number
        assert loaded.status == attempt.status
        assert loaded.delay_seconds == attempt.delay_seconds
        assert loaded.error_message == attempt.error_message
        assert loaded.duration_ms == attempt.duration_ms
        assert loaded.metadata == attempt.metadata

    def test_from_dict_defaults(self) -> None:
        data = {
            "recovery_id": "rec-minimal",
            "recovery_type": "crash:recovery",
            "timestamp": 1234567.0,
        }
        loaded = RecoveryAttempt.from_dict(data)
        assert loaded.attempt_number == 1
        assert loaded.status == RecoveryStatus.PENDING
        assert loaded.delay_seconds == 0.0
        assert loaded.error_message is None
        assert loaded.duration_ms is None
        assert loaded.metadata == {}


# ---------------------------------------------------------------------------
# RecoveryConfig
# ---------------------------------------------------------------------------


class TestRecoveryConfig:
    def test_default_config(self) -> None:
        cfg = RecoveryConfig()
        assert cfg.max_attempts == 3
        assert cfg.base_delay_seconds == 1.0
        assert cfg.max_delay_seconds == 10.0
        assert cfg.backoff_multiplier == 2.0

    def test_get_delay_exponential(self) -> None:
        cfg = RecoveryConfig(
            max_attempts=5,
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            backoff_multiplier=2.0,
        )
        assert cfg.get_delay(1) == 1.0
        assert cfg.get_delay(2) == 2.0
        assert cfg.get_delay(3) == 4.0
        assert cfg.get_delay(4) == 8.0
        assert cfg.get_delay(5) == 10.0  # min(16, 10)


# ---------------------------------------------------------------------------
# RecoveryAction
# ---------------------------------------------------------------------------


class TestRecoveryAction:
    @pytest.mark.asyncio
    async def test_execute_sync_callable(self) -> None:
        called = False

        def sync_fn() -> str:
            nonlocal called
            called = True
            return "ok"

        action = RecoveryAction(RecoveryType.PROXY_RECOVERY, sync_fn)
        success = await action.execute()
        assert success is True
        assert called is True

    @pytest.mark.asyncio
    async def test_execute_async_callable(self) -> None:
        called = False

        async def async_fn() -> str:
            nonlocal called
            called = True
            return "async_ok"

        action = RecoveryAction(RecoveryType.PROXY_RECOVERY, async_fn)
        success = await action.execute()
        assert success is True
        assert called is True

    @pytest.mark.asyncio
    async def test_execute_callable_raises_exception(self) -> None:
        def failing_fn() -> None:
            raise RuntimeError("Fatal action failure")

        action = RecoveryAction(RecoveryType.PROXY_RECOVERY, failing_fn)
        success = await action.execute()
        assert success is False


# ---------------------------------------------------------------------------
# AutoRecovery history & file persistence
# ---------------------------------------------------------------------------


class TestAutoRecoveryPersistence:
    def test_load_history_when_file_not_exists(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "not_found.json"
        ar = AutoRecovery(storage_path=str(hist_file))
        assert ar._recoveries == {}

    def test_load_history_valid_json(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "recovery.json"
        data = {
            "recoveries": {
                "rec-1": [
                    {
                        "recovery_id": "rec-1",
                        "recovery_type": "proxy:recovery",
                        "timestamp": 100.0,
                        "attempt_number": 1,
                        "status": "success",
                        "delay_seconds": 0.0,
                        "metadata": {},
                    }
                ]
            }
        }
        hist_file.write_text(json.dumps(data))

        ar = AutoRecovery(storage_path=str(hist_file))
        assert "rec-1" in ar._recoveries
        assert len(ar._recoveries["rec-1"]) == 1
        assert ar._recoveries["rec-1"][0].status == RecoveryStatus.SUCCESS

    def test_load_history_invalid_json(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "corrupt.json"
        hist_file.write_text("{ corrupt json")

        ar = AutoRecovery(storage_path=str(hist_file))
        assert ar._recoveries == {}

    def test_load_history_corrupt_entries(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "bad_keys.json"
        # Missing required fields will raise KeyError in from_dict
        hist_file.write_text(json.dumps({"recoveries": {"rec-1": [{}]}}))

        ar = AutoRecovery(storage_path=str(hist_file))
        assert ar._recoveries == {}

    def test_save_history_catches_exception(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "sub" / "recovery.json"
        ar = AutoRecovery(storage_path=str(hist_file))
        attempt = ar._create_attempt(
            recovery_id="rec-save",
            recovery_type=RecoveryType.PROXY_RECOVERY,
            status=RecoveryStatus.SUCCESS,
        )

        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            # Should catch exception without crashing
            ar._record_attempt(attempt)


# ---------------------------------------------------------------------------
# AutoRecovery workflow & exponential backoff
# ---------------------------------------------------------------------------


class TestAutoRecoveryWorkflow:
    @pytest.mark.asyncio
    async def test_attempt_recovery_unregistered_action(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        # Unregister a type
        ar._actions.pop(RecoveryType.PROXY_RECOVERY, None)

        attempt = await ar.attempt_recovery(RecoveryType.PROXY_RECOVERY)
        assert attempt.status == RecoveryStatus.FAILED
        assert "No action registered" in (attempt.error_message or "")

    @pytest.mark.asyncio
    async def test_attempt_recovery_success_first_try(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        mock_fn = AsyncMock(return_value=True)
        ar.register_action(RecoveryType.PROXY_RECOVERY, mock_fn)

        with patch.object(ar._event_bus, "emit") as mock_emit:
            attempt = await ar.attempt_recovery(
                RecoveryType.PROXY_RECOVERY, metadata={"reason": "test"}
            )

        assert attempt.status == RecoveryStatus.SUCCESS
        assert attempt.attempt_number == 1
        assert attempt.metadata == {"reason": "test"}
        assert attempt.duration_ms is not None
        mock_fn.assert_awaited_once()

        # Check emitted events
        event_types = [call[0][0] for call in mock_emit.call_args_list]
        assert EventType.HEALTH_WARNING in event_types
        assert EventType.RECOVERY_SUCCESS in event_types

    @pytest.mark.asyncio
    async def test_attempt_recovery_success_on_second_attempt(self, tmp_path: Path) -> None:
        config = RecoveryConfig(max_attempts=3, base_delay_seconds=0.1)
        ar = AutoRecovery(config=config, storage_path=str(tmp_path / "rec.json"))

        # Fails first, succeeds second
        mock_fn = AsyncMock(side_effect=[False, True])
        ar.register_action(RecoveryType.PROXY_RECOVERY, mock_fn)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            attempt = await ar.attempt_recovery(RecoveryType.PROXY_RECOVERY)

        assert attempt.status == RecoveryStatus.SUCCESS
        assert attempt.attempt_number == 2
        assert mock_fn.await_count == 2
        mock_sleep.assert_awaited_once_with(config.get_delay(2))

    @pytest.mark.asyncio
    async def test_attempt_recovery_all_attempts_exhausted(self, tmp_path: Path) -> None:
        config = RecoveryConfig(max_attempts=2, base_delay_seconds=0.01)
        ar = AutoRecovery(config=config, storage_path=str(tmp_path / "rec.json"))

        mock_fn = AsyncMock(return_value=False)
        ar.register_action(RecoveryType.PROXY_RECOVERY, mock_fn)

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch.object(ar._event_bus, "emit") as mock_emit:
            attempt = await ar.attempt_recovery(RecoveryType.PROXY_RECOVERY)

        assert attempt.status == RecoveryStatus.EXHAUSTED
        assert attempt.attempt_number == 2
        assert mock_fn.await_count == 2

        event_types = [call[0][0] for call in mock_emit.call_args_list]
        assert EventType.RECOVERY_FAILED in event_types

    @pytest.mark.asyncio
    async def test_attempt_recovery_zero_attempts_configured(self, tmp_path: Path) -> None:
        config = RecoveryConfig(max_attempts=0)
        ar = AutoRecovery(config=config, storage_path=str(tmp_path / "rec.json"))

        attempt = await ar.attempt_recovery(RecoveryType.PROXY_RECOVERY)
        assert attempt.status == RecoveryStatus.EXHAUSTED

    def test_emit_recovery_event_mappings(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        attempt = ar._create_attempt(
            recovery_id="rec-events",
            recovery_type=RecoveryType.PROXY_RECOVERY,
            status=RecoveryStatus.SUCCESS,
        )

        with patch.object(ar._event_bus, "emit") as mock_emit:
            ar._emit_recovery_event("recovery:started", attempt)
            assert mock_emit.call_args[0][0] == EventType.RECOVERY_STARTED

            ar._emit_recovery_event("recovery:attempted", attempt)
            assert mock_emit.call_args[0][0] == EventType.RECOVERY_ATTEMPTED

            ar._emit_recovery_event("recovery:success", attempt)
            assert mock_emit.call_args[0][0] == EventType.RECOVERY_SUCCESS

            ar._emit_recovery_event("recovery:failed", attempt)
            assert mock_emit.call_args[0][0] == EventType.RECOVERY_FAILED

            ar._emit_recovery_event("unknown:custom", attempt)
            assert mock_emit.call_args[0][0] == EventType.RECOVERY_STARTED


# ---------------------------------------------------------------------------
# Built-in recovery actions
# ---------------------------------------------------------------------------


class TestBuiltinRecoveryActions:
    @pytest.mark.asyncio
    async def test_execute_proxy_recovery_script_success(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        script_file = tmp_path / "proxy-recovery.sh"
        script_file.write_text("#!/bin/bash\nexit 0")

        mock_proc = MagicMock()
        mock_proc.returncode = 0

        with patch.object(Path, "exists", side_effect=lambda: True), \
             patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_proc):
            res = await ar._execute_proxy_recovery()
            assert res is True

    @pytest.mark.asyncio
    async def test_execute_proxy_recovery_script_nonzero_exit_falls_back(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = "script error"

        with patch.object(Path, "exists", side_effect=[True, False, False, False]), \
             patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_proc), \
             patch.object(ar, "_restart_proxy_service", new_callable=AsyncMock, return_value=True) as mock_restart:
            res = await ar._execute_proxy_recovery()
            assert res is True
            mock_restart.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_proxy_recovery_script_timeout_falls_back(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch.object(Path, "exists", side_effect=[True, False, False, False]), \
             patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=subprocess.TimeoutExpired(cmd="bash", timeout=30)), \
             patch.object(ar, "_restart_proxy_service", new_callable=AsyncMock, return_value=True) as mock_restart:
            res = await ar._execute_proxy_recovery()
            assert res is True
            mock_restart.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_proxy_recovery_script_generic_exception_falls_back(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch.object(Path, "exists", side_effect=[True, False, False, False]), \
             patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=RuntimeError("Subprocess failed")), \
             patch.object(ar, "_restart_proxy_service", new_callable=AsyncMock, return_value=True) as mock_restart:
            res = await ar._execute_proxy_recovery()
            assert res is True
            mock_restart.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_restart_proxy_service_success(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            res = await ar._restart_proxy_service()
            assert res is True
            mock_thread.assert_awaited_once()
            mock_sleep.assert_awaited_once_with(2)

    @pytest.mark.asyncio
    async def test_restart_proxy_service_exception(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("pkill failed")):
            res = await ar._restart_proxy_service()
            assert res is False

    @pytest.mark.asyncio
    async def test_restart_health_endpoint_success(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            res = await ar._restart_health_endpoint()
            assert res is True
            mock_thread.assert_awaited_once()
            mock_sleep.assert_awaited_once_with(2)

    @pytest.mark.asyncio
    async def test_restart_health_endpoint_exception(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("pkill health failed")):
            res = await ar._restart_health_endpoint()
            assert res is False

    def test_handle_crash_recovery_launchctl_success(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("shutil.which", side_effect=lambda cmd: "/bin/launchctl" if cmd == "launchctl" else None), \
             patch.object(Path, "exists", return_value=True), \
             patch("subprocess.run") as mock_run:
            res = ar._handle_crash_recovery()
            assert res is True
            mock_run.assert_called_once()
            assert "launchctl" in mock_run.call_args[0][0]

    def test_handle_crash_recovery_launchctl_fails_proceeds_to_systemd(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("shutil.which", side_effect=lambda cmd: "/bin/" + cmd), \
             patch.object(Path, "exists", return_value=True), \
             patch("subprocess.run", side_effect=[Exception("launchctl kickstart err"), MagicMock()]) as mock_run:
            res = ar._handle_crash_recovery()
            assert res is True
            assert mock_run.call_count == 2
            assert "systemctl" in mock_run.call_args_list[1][0][0]

    def test_handle_crash_recovery_systemctl_success(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("shutil.which", side_effect=lambda cmd: "/bin/systemctl" if cmd == "systemctl" else None), \
             patch("subprocess.run") as mock_run:
            res = ar._handle_crash_recovery()
            assert res is True
            mock_run.assert_called_once()
            assert "systemctl" in mock_run.call_args[0][0]

    def test_handle_crash_recovery_systemctl_fails_falls_back(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("shutil.which", side_effect=lambda cmd: "/bin/systemctl" if cmd == "systemctl" else None), \
             patch("subprocess.run", side_effect=Exception("systemd offline")):
            res = ar._handle_crash_recovery()
            assert res is True

    def test_handle_crash_recovery_no_service_manager_fallback(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch("shutil.which", return_value=None):
            res = ar._handle_crash_recovery()
            assert res is True

    @pytest.mark.asyncio
    async def test_handle_license_recovery(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))

        with patch.object(ar, "_execute_proxy_recovery", new_callable=AsyncMock, return_value=True) as mock_proxy:
            res = await ar._handle_license_recovery()
            assert res is True
            mock_proxy.assert_awaited_once()


# ---------------------------------------------------------------------------
# Analytics & history queries
# ---------------------------------------------------------------------------


class TestRecoveryAnalytics:
    def test_get_recovery_statistics_empty(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        stats = ar.get_recovery_statistics()
        assert stats["total_incidents"] == 0
        assert stats["total_attempts"] == 0
        assert stats["successful_recoveries"] == 0
        assert stats["failed_recoveries"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_attempts_per_incident"] == 0.0
        assert stats["average_duration_ms"] == 0.0
        assert stats["by_type"] == {}

    def test_get_recovery_statistics_with_data(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        # Incident 1: 1 attempt, success
        att1 = ar._create_attempt("inc-1", RecoveryType.PROXY_RECOVERY, RecoveryStatus.SUCCESS, duration_ms=100.0)
        # Incident 2: 2 attempts, failed then exhausted
        att2_1 = ar._create_attempt("inc-2", RecoveryType.CRASH_RECOVERY, RecoveryStatus.FAILED, attempt_number=1, duration_ms=200.0)
        att2_2 = ar._create_attempt("inc-2", RecoveryType.CRASH_RECOVERY, RecoveryStatus.EXHAUSTED, attempt_number=2, duration_ms=None)

        ar._record_attempt(att1)
        ar._record_attempt(att2_1)
        ar._record_attempt(att2_2)

        stats = ar.get_recovery_statistics()
        assert stats["total_incidents"] == 2
        assert stats["total_attempts"] == 3
        assert stats["successful_recoveries"] == 1
        assert stats["failed_recoveries"] == 2
        assert stats["success_rate"] == round(1 / 3 * 100, 2)
        assert stats["average_attempts_per_incident"] == round(3 / 2, 2)
        assert stats["average_duration_ms"] == round((100.0 + 200.0) / 2, 2)
        assert "proxy:recovery" in stats["by_type"]
        assert stats["by_type"]["proxy:recovery"]["successful"] == 1
        assert stats["by_type"]["crash:recovery"]["failed"] == 2

    def test_get_recent_recoveries(self, tmp_path: Path) -> None:
        ar = AutoRecovery(storage_path=str(tmp_path / "rec.json"))
        now = time.time()
        att1 = ar._create_attempt("inc-1", RecoveryType.PROXY_RECOVERY, RecoveryStatus.SUCCESS)
        att1.timestamp = now - 100
        att2 = ar._create_attempt("inc-2", RecoveryType.CRASH_RECOVERY, RecoveryStatus.FAILED)
        att2.timestamp = now - 50
        att3 = ar._create_attempt("inc-3", RecoveryType.LICENSE_RECOVERY, RecoveryStatus.SUCCESS)
        att3.timestamp = now

        ar._record_attempt(att1)
        ar._record_attempt(att2)
        ar._record_attempt(att3)

        recent = ar.get_recent_recoveries(limit=2)
        assert len(recent) == 2
        assert recent[0].recovery_id == "inc-3"
        assert recent[1].recovery_id == "inc-2"

        # With status filter
        failed_only = ar.get_recent_recoveries(status_filter=RecoveryStatus.FAILED)
        assert len(failed_only) == 1
        assert failed_only[0].recovery_id == "inc-2"

    def test_clear_history(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "rec.json"
        ar = AutoRecovery(storage_path=str(hist_file))
        att = ar._create_attempt("inc-1", RecoveryType.PROXY_RECOVERY, RecoveryStatus.SUCCESS)
        ar._record_attempt(att)
        assert hist_file.exists()

        cleared = ar.clear_history()
        assert cleared == 1
        assert len(ar._recoveries) == 0
        assert not hist_file.exists()

    def test_clear_history_unlink_exception(self, tmp_path: Path) -> None:
        hist_file = tmp_path / "rec.json"
        ar = AutoRecovery(storage_path=str(hist_file))
        att = ar._create_attempt("inc-1", RecoveryType.PROXY_RECOVERY, RecoveryStatus.SUCCESS)
        ar._record_attempt(att)

        with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
            cleared = ar.clear_history()
            assert cleared == 1


# ---------------------------------------------------------------------------
# Global singletons and convenience functions
# ---------------------------------------------------------------------------


class TestGlobalHelpers:
    def test_get_auto_recovery_singleton(self, tmp_path: Path) -> None:
        reset_auto_recovery()
        inst1 = get_auto_recovery(storage_path=str(tmp_path / "rec1.json"))
        inst2 = get_auto_recovery()
        assert inst1 is inst2
        reset_auto_recovery()

    @pytest.mark.asyncio
    async def test_attempt_recovery_convenience_function(self, tmp_path: Path) -> None:
        reset_auto_recovery()
        with patch.object(AutoRecovery, "attempt_recovery", new_callable=AsyncMock) as mock_attempt:
            mock_attempt.return_value = RecoveryAttempt(
                recovery_id="test",
                recovery_type=RecoveryType.PROXY_RECOVERY,
                timestamp=time.time(),
                status=RecoveryStatus.SUCCESS,
            )
            res = await attempt_recovery(RecoveryType.PROXY_RECOVERY, metadata={"m": 1})
            assert res.status == RecoveryStatus.SUCCESS
            mock_attempt.assert_awaited_once_with(
                recovery_type=RecoveryType.PROXY_RECOVERY,
                metadata={"m": 1},
            )
        reset_auto_recovery()

    def test_all_exports(self) -> None:
        import src.core.auto_recovery as mod

        for symbol in mod.__all__:
            assert hasattr(mod, symbol)
