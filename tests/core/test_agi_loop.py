# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for AGI Infinite Loop (src/core/agi_loop.py).

All tests are hermetic and deterministic: LLM client, Memory client, CC spawner,
Telegram requests, file persistence, and event loops are mocked to ensure 100%
statement and branch coverage without network, subprocess, or external side effects.
"""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.agi_loop import (
    AGILoop,
    IMPROVEMENT_AREAS,
    get_agi_loop,
    main,
)


@pytest.fixture
def sample_improvement():
    """Sample improvement dict for testing."""
    return {
        "improvement_id": "test-improvement-1",
        "title": "Add error handling",
        "description": "Improve error handling in executor.py",
        "cc_cli_prompt": "/cook Add try-catch blocks to executor.py",
        "target_files": ["src/core/executor.py"],
        "estimated_minutes": 3,
        "priority": "high",
        "category": "error handling and resilience",
    }


# ===========================================================================
# AGILoop Initialization & Property Tests
# ===========================================================================


class TestAGILoopInit:
    def test_default_initialization(self):
        loop = AGILoop()
        assert loop.cooldown == AGILoop.DEFAULT_COOLDOWN
        assert loop.telegram_notify is True
        assert loop.max_iterations is None
        assert loop.iteration == 0
        assert loop.consecutive_failures == 0
        assert loop._running is False
        assert loop.approval_mode == "manual"
        assert len(loop._pending_approvals) == 0

    def test_custom_initialization(self):
        loop = AGILoop(cooldown=30, telegram_notify=False, max_iterations=5)
        assert loop.cooldown == 30
        assert loop.telegram_notify is False
        assert loop.max_iterations == 5

    def test_shutdown_event_lazy_creation(self):
        loop = AGILoop()
        assert loop._shutdown_event is None
        evt1 = loop.shutdown_event
        assert isinstance(evt1, asyncio.Event)
        assert loop._shutdown_event is evt1
        # Second access returns the same event
        evt2 = loop.shutdown_event
        assert evt2 is evt1


# ===========================================================================
# History Management Tests
# ===========================================================================


class TestHistoryManagement:
    def test_load_history_new_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.agi_loop.HISTORY_PATH", tmp_path / "nonexistent.json")
        loop = AGILoop()
        assert loop._history == {"completed": [], "blacklist": {}, "details": []}

    def test_load_history_corrupt_json_or_oserror(self, tmp_path, monkeypatch):
        corrupt_file = tmp_path / "corrupt_history.json"
        corrupt_file.write_text("{invalid json ...")
        monkeypatch.setattr("src.core.agi_loop.HISTORY_PATH", corrupt_file)
        loop = AGILoop()
        assert loop._history == {"completed": [], "blacklist": {}, "details": []}

    def test_load_history_existing_valid_file(self, tmp_path, monkeypatch):
        history_file = tmp_path / "agi_history.json"
        test_data = {"completed": ["imp-1"], "blacklist": {"imp-bad": {"count": 2, "last": 123.0}}, "details": []}
        history_file.write_text(json.dumps(test_data))
        monkeypatch.setattr("src.core.agi_loop.HISTORY_PATH", history_file)
        loop = AGILoop()
        assert "imp-1" in loop.completed_improvements
        assert "imp-bad" in loop._history["blacklist"]

    def test_save_history_truncation(self, tmp_path, monkeypatch):
        history_file = tmp_path / "test_save_history.json"
        monkeypatch.setattr("src.core.agi_loop.HISTORY_PATH", history_file)
        loop = AGILoop()
        loop._history = {
            "completed": [f"imp-{i}" for i in range(150)],
            "blacklist": {},
            "details": [{"id": f"imp-{i}", "success": True} for i in range(150)],
        }
        loop._save_history()
        assert history_file.exists()
        saved = json.loads(history_file.read_text())
        assert len(saved["completed"]) == 100
        assert len(saved["details"]) == 100
        assert saved["completed"][-1] == "imp-149"


class TestBlacklistLogic:
    def test_is_blacklisted_not_in_dict(self):
        loop = AGILoop()
        assert loop._is_blacklisted("unknown-imp") is False

    def test_is_blacklisted_count_less_than_two(self):
        loop = AGILoop()
        loop._history["blacklist"]["imp-1"] = {"count": 1, "last": time.time()}
        assert loop._is_blacklisted("imp-1") is False

    def test_is_blacklisted_count_two_recent(self):
        loop = AGILoop()
        loop._history["blacklist"]["imp-2"] = {"count": 2, "last": time.time() - 3600}
        assert loop._is_blacklisted("imp-2") is True

    def test_is_blacklisted_count_two_expired(self):
        loop = AGILoop()
        # 86401 seconds ago (over 24h)
        loop._history["blacklist"]["imp-old"] = {"count": 2, "last": time.time() - 90000}
        assert loop._is_blacklisted("imp-old") is False

    def test_is_blacklisted_missing_or_zero_count(self):
        loop = AGILoop()
        loop._history["blacklist"]["imp-zero"] = {"count": 0, "last": time.time()}
        assert loop._is_blacklisted("imp-zero") is False


# ===========================================================================
# Adaptive Cooldown & Status Tests
# ===========================================================================


class TestCooldownCalculation:
    def test_cooldown_no_failures_low_streak(self):
        loop = AGILoop(cooldown=90)
        loop.consecutive_failures = 0
        loop._history["details"] = [{"success": True}, {"success": False}]
        assert loop._calculate_cooldown() == 90

    def test_cooldown_no_failures_high_streak(self):
        loop = AGILoop(cooldown=90)
        loop.consecutive_failures = 0
        # 3 successes in last 5
        loop._history["details"] = [
            {"success": True},
            {"success": True},
            {"success": True},
        ]
        # max(30, 90 // 2) = 45
        assert loop._calculate_cooldown() == 45

        # Lower cooldown floor at 30
        loop2 = AGILoop(cooldown=40)
        loop2.consecutive_failures = 0
        loop2._history["details"] = [{"success": True}] * 4
        # max(30, 40 // 2) = 30
        assert loop2._calculate_cooldown() == 30

    def test_cooldown_with_failures(self):
        loop = AGILoop(cooldown=90)
        loop.consecutive_failures = 1
        assert loop._calculate_cooldown() == 180
        loop.consecutive_failures = 2
        assert loop._calculate_cooldown() == 360

    def test_cooldown_max_cap(self):
        loop = AGILoop(cooldown=90)
        loop.consecutive_failures = 10
        assert loop._calculate_cooldown() == 600


class TestStatusMetrics:
    def test_get_status_running_with_details(self):
        loop = AGILoop()
        loop._running = True
        loop.iteration = 10
        loop.completed_improvements = ["imp-1", "imp-2"]
        loop.consecutive_failures = 0
        loop.start_time = time.time() - 100
        loop._history["details"] = [
            {"id": "imp-1", "success": True},
            {"id": "imp-2", "success": True},
            {"id": "imp-3", "success": False},
        ]
        loop._pending_approvals.add("imp-pending")

        status = loop.get_status()
        assert status["running"] is True
        assert status["iteration"] == 10
        assert status["improvements"] == 2
        assert status["consecutive_failures"] == 0
        assert status["success_rate"] == round(2 / 3 * 100, 1)
        assert status["uptime_seconds"] >= 99
        assert status["last_improvement"] == {"id": "imp-3", "success": False}
        assert status["approval_mode"] == "manual"
        assert status["pending_approvals"] == 1

    def test_get_status_not_running_empty(self):
        loop = AGILoop()
        loop._running = False
        loop.start_time = None
        loop._history["details"] = []
        status = loop.get_status()
        assert status["running"] is False
        assert status["success_rate"] == 0
        assert status["uptime_seconds"] == 0
        assert status["last_improvement"] is None


# ===========================================================================
# Step 1: Assess Tests
# ===========================================================================


class TestAssessStep:
    @pytest.mark.asyncio
    async def test_assess_success_with_memory_and_markdown_cleaning(self):
        loop = AGILoop()
        loop.completed_improvements = ["imp-prior-1"]

        mock_mem = MagicMock()
        mock_mem.is_available = True
        mock_mem.query_memory.return_value = "Important context for improvement"

        mock_client = MagicMock()
        mock_client.is_available = True
        json_body = {
            "improvement_id": "test-imp-1",
            "title": "Improve resilience",
            "description": "Add try-catch in worker.py",
            "cc_cli_prompt": "/cook add try-catch in worker.py",
            "target_files": ["src/core/worker.py"],
            "estimated_minutes": 3,
            "priority": "high",
            "category": "error handling and resilience",
        }
        # Wrapped in markdown json block
        raw_markdown = f"```json\n{json.dumps(json_body)}\n```"
        mock_response = MagicMock()
        mock_response.content = raw_markdown
        mock_client.chat.return_value = mock_response

        with patch("src.core.memory_client.get_memory_client", return_value=mock_mem):
            with patch("src.core.adapters.llm.client.get_client", return_value=mock_client):
                result = await loop._assess()

        assert result is not None
        assert result["improvement_id"] == "test-imp-1"
        assert result["title"] == "Improve resilience"
        mock_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_assess_memory_exception_and_empty_completed(self):
        loop = AGILoop()
        loop.completed_improvements = []

        mock_client = MagicMock()
        mock_client.is_available = True
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "improvement_id": "imp-raw",
            "title": "Raw title",
        })
        mock_client.chat.return_value = mock_response

        with patch("src.core.memory_client.get_memory_client", side_effect=RuntimeError("Mem down")):
            with patch("src.core.adapters.llm.client.get_client", return_value=mock_client):
                result = await loop._assess()

        assert result is not None
        assert result["improvement_id"] == "imp-raw"

    @pytest.mark.asyncio
    async def test_assess_llm_unavailable(self):
        loop = AGILoop()
        mock_client = MagicMock()
        mock_client.is_available = False

        with patch("src.core.memory_client.get_memory_client", side_effect=Exception("No mem")):
            with patch("src.core.adapters.llm.client.get_client", return_value=mock_client):
                result = await loop._assess()

        assert result is None

    @pytest.mark.asyncio
    async def test_assess_llm_empty_response(self):
        loop = AGILoop()
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_response = MagicMock()
        mock_response.content = ""
        mock_client.chat.return_value = mock_response

        with patch("src.core.memory_client.get_memory_client", side_effect=Exception("No mem")):
            with patch("src.core.adapters.llm.client.get_client", return_value=mock_client):
                result = await loop._assess()

        assert result is None

    @pytest.mark.asyncio
    async def test_assess_llm_exception(self):
        loop = AGILoop()
        mock_client = MagicMock()
        mock_client.is_available = True
        mock_client.chat.side_effect = RuntimeError("API rate limit")

        with patch("src.core.memory_client.get_memory_client", side_effect=Exception("No mem")):
            with patch("src.core.adapters.llm.client.get_client", return_value=mock_client):
                result = await loop._assess()

        assert result is None


# ===========================================================================
# Step 2: Execute Tests
# ===========================================================================


class TestExecuteStep:
    @pytest.mark.asyncio
    async def test_execute_no_prompt_returns_none(self, sample_improvement):
        loop = AGILoop()
        sample_improvement["cc_cli_prompt"] = ""
        res = await loop._execute(sample_improvement)
        assert res is None

    @pytest.mark.asyncio
    async def test_execute_unapproved_manual_mode_returns_none(self, sample_improvement):
        loop = AGILoop()
        loop.approval_mode = "manual"
        # Not approved
        res = await loop._execute(sample_improvement)
        assert res is None

    @pytest.mark.asyncio
    async def test_execute_success_with_status_polling(self, sample_improvement):
        loop = AGILoop()
        loop.approval_mode = "auto"

        mock_session = MagicMock()
        # First poll: running, second poll: completed
        status_mock = MagicMock()
        status_mock.value = "running"
        mock_session.status = status_mock
        mock_session.exit_code = 0
        mock_session.output_buffer = ["line1", "line2", "line3"]

        async def fake_spawn(*args, **kwargs):
            return mock_session

        mock_spawner = MagicMock()
        mock_spawner.spawn = fake_spawn

        async def switch_status():
            await asyncio.sleep(0.01)
            status_mock.value = "completed"

        with patch("src.core.cc_spawner.get_spawner", return_value=mock_spawner):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # Let sleep flip the status to completed
                def sleep_side_effect(dur):
                    status_mock.value = "completed"
                mock_sleep.side_effect = sleep_side_effect
                res = await loop._execute(sample_improvement)

        assert res is True

    @pytest.mark.asyncio
    async def test_execute_failed_status_returns_false(self, sample_improvement):
        loop = AGILoop()
        loop.approve_improvement(sample_improvement["improvement_id"])

        mock_session = MagicMock()
        mock_session.status.value = "failed"
        mock_session.error = "Command exited with error code 1"

        mock_spawner = MagicMock()
        mock_spawner.spawn = AsyncMock(return_value=mock_session)

        with patch("src.core.cc_spawner.get_spawner", return_value=mock_spawner):
            res = await loop._execute(sample_improvement)

        assert res is False

    @pytest.mark.asyncio
    async def test_execute_exception_returns_false(self, sample_improvement):
        loop = AGILoop()
        loop.approve_improvement(sample_improvement["improvement_id"])

        mock_spawner = MagicMock()
        mock_spawner.spawn = AsyncMock(side_effect=RuntimeError("Spawner crashed"))

        with patch("src.core.cc_spawner.get_spawner", return_value=mock_spawner):
            res = await loop._execute(sample_improvement)

        assert res is False


# ===========================================================================
# Step 3: Memorize Tests
# ===========================================================================


class TestMemorizeStep:
    @pytest.mark.asyncio
    async def test_memorize_client_unavailable(self, sample_improvement):
        loop = AGILoop()
        mock_mem = MagicMock()
        mock_mem.is_available = False

        with patch("src.core.memory_client.get_memory_client", return_value=mock_mem):
            await loop._memorize(sample_improvement, success=True)

        mock_mem.add_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_memorize_success_and_failure(self, sample_improvement):
        loop = AGILoop()
        loop.iteration = 4
        mock_mem = MagicMock()
        mock_mem.is_available = True

        with patch("src.core.memory_client.get_memory_client", return_value=mock_mem):
            await loop._memorize(sample_improvement, success=True)
            mock_mem.add_memory.assert_called_once()
            assert "SUCCESS" in mock_mem.add_memory.call_args[0][0]

            mock_mem.reset_mock()
            await loop._memorize(sample_improvement, success=False)
            mock_mem.add_memory.assert_called_once()
            assert "FAILED" in mock_mem.add_memory.call_args[0][0]

    @pytest.mark.asyncio
    async def test_memorize_exception_caught(self, sample_improvement):
        loop = AGILoop()
        with patch("src.core.memory_client.get_memory_client", side_effect=RuntimeError("DB locked")):
            # Should not raise
            await loop._memorize(sample_improvement, success=True)


# ===========================================================================
# Step 4: Report & Telegram Tests
# ===========================================================================


class TestReportStep:
    @pytest.mark.asyncio
    async def test_report_disabled(self, sample_improvement):
        loop = AGILoop(telegram_notify=False)
        with patch.object(loop, "_send_telegram") as mock_send:
            await loop._report(sample_improvement, success=True)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_report_enabled_success_and_failure(self, sample_improvement):
        loop = AGILoop(telegram_notify=True)
        with patch.object(loop, "_send_telegram", new_callable=AsyncMock) as mock_send:
            await loop._report(sample_improvement, success=True)
            assert "✅" in mock_send.call_args[0][0]

            await loop._report(sample_improvement, success=False)
            assert "❌" in mock_send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_report_error_disabled(self):
        loop = AGILoop(telegram_notify=False)
        with patch.object(loop, "_send_telegram") as mock_send:
            await loop._report_error("some error")
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_report_error_enabled(self):
        loop = AGILoop(telegram_notify=True)
        with patch.object(loop, "_send_telegram", new_callable=AsyncMock) as mock_send:
            await loop._report_error("critical failure")
            assert "⚠️" in mock_send.call_args[0][0]
            assert "critical failure" in mock_send.call_args[0][0]


class TestSendTelegram:
    @pytest.mark.asyncio
    async def test_send_telegram_no_token(self, monkeypatch):
        monkeypatch.delenv("MEKONG_TELEGRAM_TOKEN", raising=False)
        loop = AGILoop()
        with patch("requests.post") as mock_post:
            await loop._send_telegram("hello")
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_telegram_with_config_yaml(self, monkeypatch):
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tg-token-123")
        loop = AGILoop()

        yaml_content = "telegram:\n  chat_ids:\n    - 1111\n    - 2222\n"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", patch_mock_open(yaml_content)):
                with patch("requests.post") as mock_post:
                    await loop._send_telegram("hello telegram")
                    assert mock_post.call_count == 2
                    assert mock_post.call_args_list[0][1]["json"]["chat_id"] == 1111
                    assert mock_post.call_args_list[1][1]["json"]["chat_id"] == 2222

    @pytest.mark.asyncio
    async def test_send_telegram_with_env_fallback(self, monkeypatch):
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tg-token-123")
        monkeypatch.setenv("MEKONG_CHAT_ID", "9999")
        loop = AGILoop()

        with patch("os.path.exists", return_value=False):
            with patch("requests.post") as mock_post:
                await loop._send_telegram("hello fallback")
                assert mock_post.call_count == 1
                assert mock_post.call_args[1]["json"]["chat_id"] == 9999

    @pytest.mark.asyncio
    async def test_send_telegram_no_chat_ids(self, monkeypatch):
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tg-token-123")
        monkeypatch.delenv("MEKONG_CHAT_ID", raising=False)
        loop = AGILoop()

        with patch("os.path.exists", return_value=False):
            with patch("requests.post") as mock_post:
                await loop._send_telegram("hello nobody")
                mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_telegram_request_exception(self, monkeypatch):
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tg-token-123")
        monkeypatch.setenv("MEKONG_CHAT_ID", "9999")
        loop = AGILoop()

        with patch("os.path.exists", return_value=False):
            with patch("requests.post", side_effect=RuntimeError("Network down")):
                # Should not raise
                await loop._send_telegram("hello fail")


def patch_mock_open(content: str):
    from unittest.mock import mock_open
    return mock_open(read_data=content)


# ===========================================================================
# Sleep, Shutdown & Approval Gate Tests
# ===========================================================================


class TestSafeSleepAndShutdown:
    @pytest.mark.asyncio
    async def test_safe_sleep_normal_timeout(self):
        loop = AGILoop()
        # Small sleep completes via TimeoutError (normal)
        await loop._safe_sleep(0.01)

    @pytest.mark.asyncio
    async def test_safe_sleep_interrupted_by_shutdown(self):
        loop = AGILoop()

        async def trigger_shutdown():
            await asyncio.sleep(0.01)
            loop.stop()

        task = asyncio.create_task(trigger_shutdown())
        # Would wait 10 seconds, but shutdown event sets and it wakes up immediately
        await loop._safe_sleep(10)
        await task
        assert loop._running is False

    def test_handle_shutdown_and_stop(self):
        loop = AGILoop()
        loop._running = True
        # Access shutdown_event so it is instantiated
        _ = loop.shutdown_event
        assert loop._shutdown_event is not None
        assert not loop._shutdown_event.is_set()

        loop.stop()
        assert loop._running is False
        assert loop._shutdown_event.is_set()


class TestApprovalGate:
    def test_approve_improvement_empty_and_valid(self):
        loop = AGILoop()
        assert loop.approve_improvement("") is False
        assert loop.approve_improvement("imp-1") is True
        # Already pending -> returns False
        assert loop.approve_improvement("imp-1") is False

    def test_deny_improvement_pending_and_not_pending(self):
        loop = AGILoop()
        loop.approve_improvement("imp-1")
        assert loop.deny_improvement("imp-1") is True
        assert loop.deny_improvement("imp-1") is False
        assert loop.deny_improvement("nonexistent") is False

    def test_approval_allowed_modes(self):
        loop = AGILoop()
        loop.approval_mode = "auto"
        assert loop._approval_allowed("any-id") is True

        loop.approval_mode = "manual"
        assert loop._approval_allowed("unapproved") is False
        loop.approve_improvement("approved")
        assert loop._approval_allowed("approved") is True


# ===========================================================================
# Main Loop (run_forever) Full Orchestration Tests
# ===========================================================================


class TestRunForeverOrchestration:
    @pytest.mark.asyncio
    async def test_run_forever_max_iterations_and_no_improvement_sleep(self):
        loop = AGILoop(max_iterations=2)
        # Mock signal registration
        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", new_callable=AsyncMock) as mock_assess:
                # Iteration 1: returns None (triggers sleep & continue)
                # Iteration 2: returns None (reaches max_iterations=2)
                mock_assess.return_value = None
                with patch.object(loop, "_safe_sleep", new_callable=AsyncMock) as mock_sleep:
                    await loop.run_forever()

        assert loop.iteration == 3  # Iter 1 (None), Iter 2 (None), Iter 3 (breaks on max_iterations)
        assert mock_sleep.call_count >= 2

    @pytest.mark.asyncio
    async def test_run_forever_consecutive_failures_cooldown(self):
        loop = AGILoop(max_iterations=1)
        loop.consecutive_failures = 3

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_safe_sleep", new_callable=AsyncMock) as mock_sleep:
                with patch.object(loop, "_assess", return_value=None):
                    await loop.run_forever()

        # The 5min cooldown was triggered and reset failures
        mock_sleep.assert_any_call(300)
        assert loop.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_run_forever_blacklisted_improvement_skipped(self):
        loop = AGILoop(max_iterations=1)
        imp = {"improvement_id": "bad-imp"}

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", new_callable=AsyncMock, return_value=imp):
                with patch.object(loop, "_is_blacklisted", return_value=True):
                    with patch.object(loop, "_execute") as mock_exec:
                        with patch.object(loop, "_safe_sleep", new_callable=AsyncMock):
                            await loop.run_forever()
                            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_forever_success_cycle(self, sample_improvement):
        loop = AGILoop(max_iterations=1)
        loop.consecutive_failures = 1

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", new_callable=AsyncMock, return_value=sample_improvement):
                with patch.object(loop, "_execute", new_callable=AsyncMock, return_value=True):
                    with patch.object(loop, "_memorize", new_callable=AsyncMock) as mock_mem:
                        with patch.object(loop, "_report", new_callable=AsyncMock) as mock_rep:
                            with patch.object(loop, "_save_history") as mock_save:
                                with patch.object(loop, "_safe_sleep", new_callable=AsyncMock):
                                    await loop.run_forever()

        assert loop.consecutive_failures == 0
        assert sample_improvement["improvement_id"] in loop.completed_improvements
        assert loop.last_success_time is not None
        mock_mem.assert_called_once_with(sample_improvement, True)
        mock_rep.assert_called_once_with(sample_improvement, True)
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_forever_skipped_cycle_none(self, sample_improvement):
        loop = AGILoop(max_iterations=1)
        loop.consecutive_failures = 1

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", new_callable=AsyncMock, return_value=sample_improvement):
                with patch.object(loop, "_execute", new_callable=AsyncMock, return_value=None):
                    with patch.object(loop, "_memorize", new_callable=AsyncMock):
                        with patch.object(loop, "_report", new_callable=AsyncMock):
                            with patch.object(loop, "_save_history") as mock_save:
                                with patch.object(loop, "_safe_sleep", new_callable=AsyncMock):
                                    await loop.run_forever()

        # Consecutive failures untouched on skip
        assert loop.consecutive_failures == 1
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_forever_failure_cycle(self, sample_improvement):
        loop = AGILoop(max_iterations=1)
        loop.consecutive_failures = 0

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", new_callable=AsyncMock, return_value=sample_improvement):
                with patch.object(loop, "_execute", new_callable=AsyncMock, return_value=False):
                    with patch.object(loop, "_memorize", new_callable=AsyncMock):
                        with patch.object(loop, "_report", new_callable=AsyncMock):
                            with patch.object(loop, "_save_history") as mock_save:
                                with patch.object(loop, "_safe_sleep", new_callable=AsyncMock):
                                    await loop.run_forever()

        assert loop.consecutive_failures == 1
        imp_id = sample_improvement["improvement_id"]
        assert loop._history["blacklist"][imp_id]["count"] == 1
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_forever_exception_handling(self):
        loop = AGILoop(max_iterations=1)
        loop.consecutive_failures = 0

        fake_event_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=fake_event_loop):
            with patch.object(loop, "_assess", side_effect=RuntimeError("Unexpected crash")):
                with patch.object(loop, "_report_error", new_callable=AsyncMock) as mock_err:
                    with patch.object(loop, "_safe_sleep", new_callable=AsyncMock):
                        await loop.run_forever()

        assert loop.consecutive_failures == 1
        mock_err.assert_called_once_with("Unexpected crash")


# ===========================================================================
# Singleton, Module Constants & Main Entrypoint Tests
# ===========================================================================


class TestSingletonAndMain:
    def test_singleton_get_agi_loop(self):
        import src.core.agi_loop as agi_mod
        agi_mod._agi_loop = None
        l1 = get_agi_loop()
        l2 = get_agi_loop()
        assert l1 is l2
        assert isinstance(l1, AGILoop)

    def test_improvement_areas_list(self):
        assert len(IMPROVEMENT_AREAS) == 15
        assert "error handling and resilience" in IMPROVEMENT_AREAS

    @pytest.mark.asyncio
    async def test_main_entrypoint(self):
        with patch.object(AGILoop, "run_forever", new_callable=AsyncMock) as mock_run:
            await main()
            mock_run.assert_called_once()
