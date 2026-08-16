"""Tests for C4 Learning Loop.

Covers:
  - D1: ExecutionOutcome + OutcomeRecorder (record, stats, clear)
  - D2: find_similar_failures (filtering by error_type, provider, command)
  - D3: get_failure_patterns (grouping, threshold)
  - D4: suggest_retry_threshold (auto-tuning)
  - D5: CLI `mekong learn` sub-commands
  - Hooks: attach_learning_hooks + record_outcome integration
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# OutcomeRecorder & ExecutionOutcome (D1)
# ---------------------------------------------------------------------------


class TestExecutionOutcome:
    """Unit tests for the ExecutionOutcome dataclass."""

    def test_round_trip_serialization(self) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        now = time.time()
        outcome = ExecutionOutcome(
            execution_id="wf-123",
            status=OutcomeStatus.FAILURE,
            retry_count=2,
            started_at=now - 5,
            finished_at=now,
            duration_ms=5123.0,
            error_type="timeout",
            error_message="Connection timed out after 30s",
            provider="openai",
            command="openai_api call",
            recipe="chat-generator",
        )

        data = outcome.to_dict()
        assert data["execution_id"] == "wf-123"
        assert data["status"] == "failure"
        assert data["retry_count"] == 2
        assert data["error_type"] == "timeout"
        assert data["provider"] == "openai"

        restored = ExecutionOutcome.from_dict(data)
        assert restored.execution_id == "wf-123"
        assert restored.status == OutcomeStatus.FAILURE
        assert restored.retry_count == 2
        assert restored.duration_ms == 5123.0

    def test_defaults(self) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        outcome = ExecutionOutcome(
            execution_id="wf-1",
            status=OutcomeStatus.SUCCESS,
        )
        assert outcome.retry_count == 0
        assert outcome.error_type is None
        assert outcome.provider is None
        assert outcome.duration_ms == 0.0


class TestOutcomeRecorderUnit:
    """Unit tests with an in-memory bridge stub (no disk)."""

    @pytest.fixture()
    def recorder(self) -> Any:
        from src.learning.outcome_recorder import (
            OutcomeRecorder,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()

        # Patch _get_bridge to return a stub
        stub_bridge = MagicMock()
        stub_bridge.record.return_value = "mem-abc123"
        rec._bridge = stub_bridge
        yield rec
        rec.clear()
        # Reset singleton so next test gets a fresh instance
        from src.learning.outcome_recorder import _reset_singleton

        _reset_singleton()

    def test_record_persists(self, recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        outcome = ExecutionOutcome(
            execution_id="wf-001",
            status=OutcomeStatus.SUCCESS,
            retry_count=0,
            provider="openai",
        )
        record_id = recorder.record(outcome)
        assert record_id == "mem-abc123"
        assert recorder._outcome_index[-1] == outcome

    def test_stats_empty(self, recorder: Any) -> None:
        stats = recorder.stats()
        assert stats["total"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_after_recordings(self, recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        for i in range(5):
            recorder.record(
                ExecutionOutcome(
                    execution_id=f"wf-{i}",
                    status=OutcomeStatus.SUCCESS if i < 3 else OutcomeStatus.FAILURE,
                    retry_count=i if i >= 3 else 0,
                    provider="openai",
                )
            )
        stats = recorder.stats()
        assert stats["total"] == 5
        assert stats["success_rate"] == 60.0
        assert stats["failure_count"] == 2
        assert stats["avg_retries"] == pytest.approx(1.4, abs=0.1)

    def test_clear(self, recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        recorder.record(
            ExecutionOutcome(
                execution_id="wf-x", status=OutcomeStatus.SUCCESS
            )
        )
        assert recorder.stats()["total"] == 1
        recorder.clear()
        assert recorder.stats()["total"] == 0


class TestFindSimilarFailures:
    """D2 — similarity query before retry."""

    @pytest.fixture()
    def populated_recorder(self) -> Any:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()

        stub_bridge = MagicMock()
        stub_bridge.record.return_value = "mem-x"
        rec._bridge = stub_bridge

        # Pre-populate with diverse outcomes
        outcomes = [
            ExecutionOutcome(
                execution_id="e1",
                status=OutcomeStatus.FAILURE,
                retry_count=1,
                error_type="timeout",
                provider="openai",
                command="gpt-4 call",
                finished_at=1000.0,
            ),
            ExecutionOutcome(
                execution_id="e2",
                status=OutcomeStatus.FAILURE,
                retry_count=3,
                error_type="timeout",
                provider="openai",
                command="gpt-4 call",
                finished_at=2000.0,
            ),
            ExecutionOutcome(
                execution_id="e3",
                status=OutcomeStatus.FAILURE,
                retry_count=1,
                error_type="auth",
                provider="anthropic",
                command="claude call",
                finished_at=3000.0,
            ),
            ExecutionOutcome(
                execution_id="e4",
                status=OutcomeStatus.SUCCESS,
                retry_count=0,
                error_type="timeout",
                provider="openai",
                command="gpt-4 call",
                finished_at=4000.0,
            ),
            ExecutionOutcome(
                execution_id="e5",
                status=OutcomeStatus.FAILURE,
                retry_count=2,
                error_type="timeout",
                provider="google",
                command="gemini call",
                finished_at=5000.0,
            ),
        ]
        for o in outcomes:
            rec._outcome_index.append(o)

        yield rec
        _reset_singleton()

    def test_filter_by_error_type(self, populated_recorder: Any) -> None:
        results = populated_recorder.find_similar_failures(error_type="timeout")
        assert len(results) >= 3  # e1, e2, e5 (e4 is success, filtered out)
        # e4 (success) should not appear
        ids = {o.execution_id for o in results}
        assert "e4" not in ids

    def test_filter_by_error_type_and_provider(self, populated_recorder: Any) -> None:
        results = populated_recorder.find_similar_failures(
            error_type="timeout", provider="openai"
        )
        ids = {o.execution_id for o in results}
        assert "e1" in ids
        assert "e2" in ids
        assert "e5" not in ids  # google provider

    def test_filter_by_command(self, populated_recorder: Any) -> None:
        results = populated_recorder.find_similar_failures(command="claude call")
        ids = {o.execution_id for o in results}
        assert "e3" in ids

    def test_newest_first(self, populated_recorder: Any) -> None:
        results = populated_recorder.find_similar_failures(error_type="timeout")
        finished_times = [o.finished_at for o in results]
        assert finished_times == sorted(finished_times, reverse=True)

    def test_empty_result(self) -> None:
        from src.learning.outcome_recorder import (
            OutcomeRecorder,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        results = rec.find_similar_failures(error_type="nonexistent")
        assert results == []
        _reset_singleton()


class TestFailurePatterns:
    """D3 — pattern detection."""

    @pytest.fixture()
    def pattern_recorder(self) -> Any:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        stub_bridge = MagicMock()
        rec._bridge = stub_bridge

        # 5 timeouts from openai
        for i in range(5):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"t-{i}",
                    status=OutcomeStatus.FAILURE,
                    error_type="timeout",
                    provider="openai",
                    command="gpt-4 call",
                    finished_at=float(1000 + i),
                )
            )
        # 3 auth failures from anthropic
        for i in range(3):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"a-{i}",
                    status=OutcomeStatus.FAILURE,
                    error_type="auth",
                    provider="anthropic",
                    command="claude call",
                    finished_at=float(2000 + i),
                )
            )
        # 2 rate_limit from openai (below threshold of 3)
        for i in range(2):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"r-{i}",
                    status=OutcomeStatus.FAILURE,
                    error_type="rate_limit",
                    provider="openai",
                    command="gpt-4 call",
                    finished_at=float(3000 + i),
                )
            )

        yield rec
        _reset_singleton()

    def test_detects_recurrent_patterns(self, pattern_recorder: Any) -> None:
        patterns = pattern_recorder.get_failure_patterns(min_occurrences=3)
        # Should detect timeout+openai (5) and auth+anthropic (3)
        error_providers = {(p["error_type"], p["provider"]) for p in patterns}
        assert ("timeout", "openai") in error_providers
        assert ("auth", "anthropic") in error_providers
        # rate_limit+openai (2) should be filtered out
        assert ("rate_limit", "openai") not in error_providers

    def test_pattern_occurrence_count(self, pattern_recorder: Any) -> None:
        patterns = pattern_recorder.get_failure_patterns(min_occurrences=3)
        timeout_pat = next(p for p in patterns if p["error_type"] == "timeout")
        assert timeout_pat["occurrences"] == 5
        auth_pat = next(p for p in patterns if p["error_type"] == "auth")
        assert auth_pat["occurrences"] == 3

    def test_suggested_action_present(self, pattern_recorder: Any) -> None:
        patterns = pattern_recorder.get_failure_patterns()
        for p in patterns:
            assert "suggested_action" in p
            assert len(p["suggested_action"]) > 0

    def test_no_patterns_when_none_exceed_threshold(self) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        rec._outcome_index.append(
            ExecutionOutcome(
                execution_id="x", status=OutcomeStatus.FAILURE, error_type="timeout"
            )
        )
        patterns = rec.get_failure_patterns(min_occurrences=5)
        assert patterns == []
        _reset_singleton()

    def test_successes_ignored(self) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        for i in range(5):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"s-{i}",
                    status=OutcomeStatus.SUCCESS,
                    error_type="timeout",
                )
            )
        patterns = rec.get_failure_patterns()
        assert patterns == []
        _reset_singleton()


class TestSuggestRetryThreshold:
    """D4 — threshold auto-tuning."""

    @pytest.fixture()
    def threshold_recorder(self) -> Any:
        from src.learning.outcome_recorder import (
            OutcomeRecorder,
            _reset_singleton,
        )

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        yield rec
        _reset_singleton()

    def test_no_history_returns_current(self, threshold_recorder: Any) -> None:
        # No outcomes recorded — should return current threshold unchanged
        suggested = threshold_recorder.suggest_retry_threshold(
            error_type="timeout", provider="openai", current_threshold=3
        )
        assert suggested == 3

    def test_high_retries_suggests_raise(self, threshold_recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        # Many failures all with retry_count >= 3 → suggest raising
        for _ in range(10):
            threshold_recorder._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"h-{_}",
                    status=OutcomeStatus.FAILURE,
                    retry_count=4,  # always hit ceiling
                    error_type="timeout",
                    provider="openai",
                )
            )
        suggested = threshold_recorder.suggest_retry_threshold(
            error_type="timeout",
            provider="openai",
            current_threshold=3,
            max_threshold=5,
        )
        assert suggested == 4  # raised by 1

    def test_low_retries_suggests_lower(self, threshold_recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        # Many failures with retry_count=0 → can lower threshold
        for _ in range(10):
            threshold_recorder._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"l-{_}",
                    status=OutcomeStatus.FAILURE,
                    retry_count=0,
                    error_type="timeout",
                    provider="openai",
                )
            )
        suggested = threshold_recorder.suggest_retry_threshold(
            error_type="timeout",
            provider="openai",
            current_threshold=3,
            max_threshold=5,
        )
        assert suggested == 2  # lowered by 1

    def test_respects_max_threshold(self, threshold_recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        for _ in range(10):
            threshold_recorder._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"mx-{_}",
                    status=OutcomeStatus.FAILURE,
                    retry_count=5,
                    error_type="timeout",
                    provider="openai",
                )
            )
        suggested = threshold_recorder.suggest_retry_threshold(
            error_type="timeout",
            provider="openai",
            current_threshold=5,
            max_threshold=5,
        )
        assert suggested == 5  # never exceeds max

    def test_middle_retries_unchanged(self, threshold_recorder: Any) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeStatus,
        )

        # Average retry = 1.2 with current=3 → avg (1.6) < 3*0.4=1.2 is False,
        # so threshold is unchanged at 3.
        for i in range(10):
            threshold_recorder._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"m-{i}",
                    status=OutcomeStatus.FAILURE,
                    retry_count=1 if i < 4 else 2,
                    error_type="timeout",
                    provider="openai",
                )
            )
        suggested = threshold_recorder.suggest_retry_threshold(
            error_type="timeout",
            provider="openai",
            current_threshold=3,
        )
        # avg = (4*1 + 6*2) / 10 = 1.6; >= 0.4*3=1.2 but < 3 → unchanged
        assert suggested == 3


# ---------------------------------------------------------------------------
# Retry hooks (D2 + D3 + D4 integration)
# ---------------------------------------------------------------------------


class TestRetryHooks:
    """Integration tests for retry_hooks module."""

    @pytest.fixture()
    def fresh_env(self) -> None:
        from src.learning.outcome_recorder import _reset_singleton

        _reset_singleton()
        yield
        _reset_singleton()  # type: ignore[possibly-undefined]

    def test_classify_error(self) -> None:
        from src.learning.retry_hooks import _classify_error

        assert _classify_error("Connection timed out") == "timeout"
        assert _classify_error("Invalid API key provided") == "auth"
        assert _classify_error("Rate limit exceeded (429)") == "rate_limit"
        assert _classify_error("Connection refused") == "connection"
        assert _classify_error("Permission denied") == "forbidden"
        assert _classify_error("Context length exceeded") == "context_length"
        assert _classify_error("Some random error") == "unknown"

    def test_record_outcome_convenience(self, fresh_env: None) -> None:
        from src.learning.retry_hooks import record_outcome

        from src.learning.outcome_recorder import (
            OutcomeRecorder,
            _reset_singleton,
        )

        record_id = record_outcome(
            execution_id="wf-hook-1",
            status="failure",
            retry_count=2,
            error_message="Connection timed out",
            provider="openai",
            command="gpt-4 call",
            duration_ms=5000.0,
        )
        assert len(record_id) > 0
        stats = OutcomeRecorder.get_instance().stats()
        assert stats["total"] == 1
        _reset_singleton()

    def test_check_before_retry_empty_when_no_history(self, fresh_env: None) -> None:
        from src.learning.retry_hooks import check_before_retry

        results = check_before_retry(error_type="timeout", provider="openai")
        assert results == []

    def test_check_before_retry_returns_matches(self, fresh_env: None) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
        )
        from src.learning.retry_hooks import check_before_retry

        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        rec._outcome_index.append(
            ExecutionOutcome(
                execution_id="past-fail",
                status=OutcomeStatus.FAILURE,
                retry_count=2,
                error_type="timeout",
                provider="openai",
                command="gpt-4 call",
                error_message="Connection timed out",
            )
        )
        results = check_before_retry(error_type="timeout", provider="openai")
        assert len(results) >= 1
        assert results[0]["execution_id"] == "past-fail"
        assert results[0]["error_type"] == "timeout"

    def test_get_pattern_warnings(self, fresh_env: None) -> None:
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
        )
        from src.learning.retry_hooks import get_pattern_warnings

        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        for i in range(4):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"p-{i}",
                    status=OutcomeStatus.FAILURE,
                    error_type="timeout",
                    provider="openai",
                )
            )
        patterns = get_pattern_warnings(min_occurrences=3)
        assert len(patterns) == 1
        assert patterns[0]["error_type"] == "timeout"
        assert patterns[0]["occurrences"] == 4


# ---------------------------------------------------------------------------
# CLI `mekong learn` (D5)
# ---------------------------------------------------------------------------


class TestLearnCLI:
    """CLI tests for `mekong learn` sub-commands."""

    @pytest.fixture(autouse=True)
    def fresh_env(self) -> None:
        from src.learning.outcome_recorder import _reset_singleton

        _reset_singleton()
        yield
        _reset_singleton()

    def _runner(self) -> Any:
        from typer.testing import CliRunner
        from src.cli.commands.memory import memory_app

        return CliRunner(), memory_app

    def test_learn_record(self) -> None:
        """`mekong learn record <id> --status failure` records outcome."""
        runner, app = self._runner()
        result = runner.invoke(
            app,
            [
                "learn",
                "record",
                "cli-test-1",
                "--status=success",
                "--retries=0",
                "--provider=openai",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Recorded" in result.output
        assert "cli-test-1" in result.output

    def test_learn_record_invalid_status(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(
            app, ["learn", "record", "bad-id", "--status=invalid"]
        )
        assert result.exit_code == 1

    def test_learn_patterns_empty(self) -> None:
        """No patterns when no outcomes recorded."""
        runner, app = self._runner()
        result = runner.invoke(app, ["learn", "patterns"])
        assert result.exit_code == 0
        assert "No failure patterns" in result.output

    def test_learn_patterns_detects(self) -> None:
        """Patterns detected when enough similar failures exist."""
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
        )

        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        for i in range(4):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id=f"pat-{i}",
                    status=OutcomeStatus.FAILURE,
                    error_type="timeout",
                    provider="openai",
                    finished_at=time.time() + i,
                )
            )

        runner, app = self._runner()
        result = runner.invoke(app, ["learn", "patterns"])
        assert result.exit_code == 0
        assert "timeout" in result.output
        assert "openai" in result.output

    def test_learn_stats(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, ["learn", "stats"])
        assert result.exit_code == 0
        assert "Total Outcomes" in result.output

    def test_learn_threshold_no_history(self) -> None:
        """Threshold suggestion returns current when no history."""
        runner, app = self._runner()
        result = runner.invoke(
            app,
            ["learn", "threshold", "--error-type=timeout", "--provider=openai", "--current=3"],
        )
        assert result.exit_code == 0
        assert "3" in result.output  # should keep current

    def test_learn_clear(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, ["learn", "clear", "--force"])
        assert result.exit_code == 0
        assert "cleared" in result.output.lower()

    def test_learn_clear_requires_force(self) -> None:
        runner, app = self._runner()
        # Without --force it should prompt/exit — CliRunner auto-denies
        result = runner.invoke(app, ["learn", "clear"])
        assert result.exit_code != 0 or "Cancelled" in result.output


# ---------------------------------------------------------------------------
# Retry hooks attaching to executor
# ---------------------------------------------------------------------------


class TestAttachLearningHooks:
    """Test the attach_learning_hooks integration with StageRetryExecutor."""

    def test_attach_does_not_raise(self) -> None:
        """Attaching hooks to a plain executor should succeed."""
        from src.core.retry_policy import RetryPolicy
        from src.core.stage_retry import StageRetryExecutor
        from src.learning.retry_hooks import attach_learning_hooks

        executor = StageRetryExecutor(policy=RetryPolicy(max_attempts=2))
        # Should not raise
        attach_learning_hooks(executor, provider="test-provider")
        assert executor.on_retry is not None

    def test_attach_auto_tune(self) -> None:
        """Auto-tune adjusts max_attempts before execution."""
        from src.core.retry_policy import RetryPolicy
        from src.core.stage_retry import StageRetryExecutor
        from src.learning.outcome_recorder import (
            ExecutionOutcome,
            OutcomeRecorder,
            OutcomeStatus,
            _reset_singleton,
        )
        from src.learning.retry_hooks import attach_learning_hooks

        _reset_singleton()
        rec = OutcomeRecorder.get_instance()
        rec._bridge = MagicMock()
        # Simulate many failures with retry_count=4 → suggest raising
        for _ in range(10):
            rec._outcome_index.append(
                ExecutionOutcome(
                    execution_id="at-1",
                    status=OutcomeStatus.FAILURE,
                    retry_count=4,
                    error_type="timeout",
                    provider="test-provider",
                )
            )

        policy = RetryPolicy(max_attempts=3)
        executor = StageRetryExecutor(policy=policy)
        attach_learning_hooks(executor, provider="test-provider", auto_tune=True, max_threshold=5)
        # Should have raised from 3 to 4
        assert executor.policy.max_attempts == 4
        _reset_singleton()
