"""Unit tests for src/daemon/jidoka.py.

Covers:
- ErrorSeverity enum
- ErrorPattern / JidokaEvent dataclasses
- JidokaMonitor.detect_error (all patterns + no match)
- JidokaMonitor.handle_error (all action branches)
- JidokaMonitor._log_alert (file write + event recording + rotation)
- JidokaMonitor._rotate_alerts
- JidokaMonitor._run_auto_fix (success, failure, timeout)
- JidokaMonitor._run_rollback (success, failure, exception)
- JidokaMonitor._escalate (with/without telegram tokens)
- JidokaMonitor.get_recent_events / get_stats / read_alerts
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


from src.daemon.jidoka import (
    ALERT_LOG_MAX_LINES,
    ErrorPattern,
    ErrorSeverity,
    JidokaMonitor,
)
from src.daemon.circuit_breaker import CircuitBreakerRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_monitor(tmp_path: Path) -> JidokaMonitor:
    """Create a JidokaMonitor with Jidoka file redirected to tmp_path."""
    with patch("src.daemon.jidoka.MEKONG_DIR", tmp_path), \
         patch("src.daemon.jidoka.JIDOKA_FILE", tmp_path / "jidoka-alerts.log"):
        registry = CircuitBreakerRegistry()
        monitor = JidokaMonitor(circuit_breaker_registry=registry)
    return monitor


# ---------------------------------------------------------------------------
# ErrorSeverity
# ---------------------------------------------------------------------------

class TestErrorSeverity:
    def test_values(self):
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


# ---------------------------------------------------------------------------
# JidokaMonitor.detect_error
# ---------------------------------------------------------------------------

class TestDetectError:
    def setup_method(self):
        self.monitor = JidokaMonitor()

    def test_breaking_test_detected(self):
        p = self.monitor.detect_error("test failed: assertion error on line 42")
        assert p is not None
        assert p.name == "breaking_test"
        assert p.severity == ErrorSeverity.HIGH

    def test_schema_change_detected(self):
        p = self.monitor.detect_error("database migration: ALTER TABLE users")
        assert p is not None
        assert p.name == "schema_change"
        assert p.severity == ErrorSeverity.CRITICAL

    def test_security_vulnerability_detected(self):
        p = self.monitor.detect_error("npm audit: high severity CVE-2024-1234")
        assert p is not None
        assert p.name == "security_vulnerability"

    def test_build_failure_detected(self):
        p = self.monitor.detect_error("build failed with SyntaxError in main.py")
        assert p is not None
        assert p.name == "build_failure"

    def test_import_error_detected(self):
        p = self.monitor.detect_error("ModuleNotFoundError: No module named 'foo'")
        assert p is not None
        assert p.name == "import_error"
        assert p.severity == ErrorSeverity.MEDIUM

    def test_type_error_detected(self):
        p = self.monitor.detect_error("TS2345: Argument of type string")
        assert p is not None
        assert p.name == "type_error"

    def test_no_match_returns_none(self):
        p = self.monitor.detect_error("Everything looks fine, no issues here.")
        assert p is None

    def test_case_insensitive(self):
        p = self.monitor.detect_error("BREAKING CHANGE detected in API")
        assert p is not None
        assert p.name == "breaking_test"


# ---------------------------------------------------------------------------
# JidokaMonitor.handle_error
# ---------------------------------------------------------------------------

class TestHandleError:
    def test_ignored_when_no_pattern_matches(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        result = monitor.handle_error("w1", "everything is fine")
        assert result == "ignored"

    def test_auto_fix_attempted_on_high_severity(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        pattern = ErrorPattern(
            name="build_failure",
            pattern=r"build failed",
            severity=ErrorSeverity.HIGH,
            auto_fix="echo fix",
        )
        with patch.object(monitor, "_run_auto_fix", return_value=True) as mock_fix:
            result = monitor.handle_error("w1", "build failed", pattern=pattern)
        assert result == "auto_fix_attempted"
        mock_fix.assert_called_once_with("echo fix")

    def test_rolled_back_when_auto_fix_fails_and_rollback_available(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        pattern = ErrorPattern(
            name="schema_change",
            pattern=r"ALTER TABLE",
            severity=ErrorSeverity.HIGH,
            auto_fix="echo fix",
            rollback="git revert HEAD",
        )
        with patch.object(monitor, "_run_auto_fix", return_value=False), \
             patch.object(monitor, "_run_rollback", return_value=True) as mock_rb:
            result = monitor.handle_error("w1", "ALTER TABLE users", pattern=pattern)
        assert result == "rolled_back"
        mock_rb.assert_called_once_with("git revert HEAD")

    def test_escalated_for_critical_no_auto_fix(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        pattern = ErrorPattern(
            name="schema_change",
            pattern=r"DROP COLUMN",
            severity=ErrorSeverity.CRITICAL,
        )
        with patch.object(monitor, "_escalate") as mock_esc:
            result = monitor.handle_error("w1", "DROP COLUMN id", pattern=pattern)
        assert result == "escalated"
        mock_esc.assert_called_once()

    def test_logged_for_medium_no_auto_fix(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        pattern = ErrorPattern(
            name="type_error",
            pattern=r"TS\d+:",
            severity=ErrorSeverity.MEDIUM,
        )
        result = monitor.handle_error("w1", "TS2345: error", pattern=pattern)
        assert result == "logged"

    def test_circuit_open_skips_auto_fix(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        pattern = ErrorPattern(
            name="build_failure",
            pattern=r"build failed",
            severity=ErrorSeverity.HIGH,
            auto_fix="echo fix",
        )
        breaker = monitor.circuit_breakers.get("worker-w1")
        # Trip the breaker by failing many times
        for _ in range(6):
            breaker.on_failure("err")

        with patch.object(monitor, "_run_auto_fix") as mock_fix:
            result = monitor.handle_error("w1", "build failed", pattern=pattern)
        assert result == "circuit_open"
        mock_fix.assert_not_called()

    def test_pattern_auto_detected_when_not_provided(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch.object(monitor, "_run_auto_fix", return_value=True):
            result = monitor.handle_error("w1", "test failed: assertion error")
        assert result == "auto_fix_attempted"


# ---------------------------------------------------------------------------
# JidokaMonitor._run_auto_fix
# ---------------------------------------------------------------------------

class TestRunAutoFix:
    def test_returns_true_on_success(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = monitor._run_auto_fix("echo ok")
        assert result is True

    def test_returns_false_on_nonzero_exit(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="failed")
            result = monitor._run_auto_fix("false")
        assert result is False

    def test_returns_false_on_timeout(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 120)):
            result = monitor._run_auto_fix("sleep 999")
        assert result is False

    def test_returns_false_on_exception(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run", side_effect=OSError("no such file")):
            result = monitor._run_auto_fix("nonexistent_cmd")
        assert result is False


# ---------------------------------------------------------------------------
# JidokaMonitor._run_rollback
# ---------------------------------------------------------------------------

class TestRunRollback:
    def test_returns_true_on_success(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = monitor._run_rollback("git revert HEAD")
        assert result is True

    def test_returns_false_on_failure(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="conflict")
            result = monitor._run_rollback("git revert HEAD")
        assert result is False

    def test_returns_false_on_exception(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        with patch("subprocess.run", side_effect=Exception("explosion")):
            result = monitor._run_rollback("boom")
        assert result is False


# ---------------------------------------------------------------------------
# JidokaMonitor._escalate
# ---------------------------------------------------------------------------

class TestEscalate:
    def test_skips_when_no_telegram_config(self, tmp_path, monkeypatch):
        monitor = _make_monitor(tmp_path)
        monkeypatch.delenv("MEKONG_TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("MEKONG_TELEGRAM_CHAT_ID", raising=False)
        pattern = ErrorPattern(name="test", pattern="x", severity=ErrorSeverity.CRITICAL)
        # Should not raise
        monitor._escalate("w1", "critical error", pattern)

    def test_sends_telegram_when_configured(self, tmp_path, monkeypatch):
        monitor = _make_monitor(tmp_path)
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tok123")
        monkeypatch.setenv("MEKONG_TELEGRAM_CHAT_ID", "chat456")
        pattern = ErrorPattern(name="test", pattern="x", severity=ErrorSeverity.CRITICAL)
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            monitor._escalate("w1", "critical error", pattern)
        mock_open.assert_called_once()

    def test_escalate_handles_urllib_exception(self, tmp_path, monkeypatch):
        monitor = _make_monitor(tmp_path)
        monkeypatch.setenv("MEKONG_TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("MEKONG_TELEGRAM_CHAT_ID", "chat")
        pattern = ErrorPattern(name="test", pattern="x", severity=ErrorSeverity.CRITICAL)
        with patch("urllib.request.urlopen", side_effect=Exception("network error")):
            # Should not raise
            monitor._escalate("w1", "err", pattern)


# ---------------------------------------------------------------------------
# JidokaMonitor._log_alert + _rotate_alerts
# ---------------------------------------------------------------------------

class TestLogAlertAndRotation:
    def test_log_alert_writes_to_file(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        pattern = ErrorPattern(name="build_failure", pattern="x", severity=ErrorSeverity.HIGH)
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            monitor._log_alert("w1", "build failed", pattern)
        content = log_file.read_text()
        assert "w1" in content
        assert "build_failure" in content

    def test_log_alert_records_event(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        pattern = ErrorPattern(name="import_error", pattern="x", severity=ErrorSeverity.MEDIUM)
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            monitor._log_alert("w2", "ImportError foo", pattern)
        assert len(monitor._events) == 1
        assert monitor._events[0].worker_id == "w2"

    def test_events_capped_at_100(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        pattern = ErrorPattern(name="build_failure", pattern="x", severity=ErrorSeverity.HIGH)
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            for i in range(110):
                monitor._log_alert(f"w{i}", "err", pattern)
        assert len(monitor._events) <= 100

    def test_rotate_alerts_trims_file(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        # Write more than ALERT_LOG_MAX_LINES lines
        lines = [f"line {i}" for i in range(ALERT_LOG_MAX_LINES + 20)]
        log_file.write_text("\n".join(lines))
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            monitor._rotate_alerts()
        result_lines = log_file.read_text().strip().split("\n")
        assert len(result_lines) == ALERT_LOG_MAX_LINES

    def test_rotate_no_op_when_small(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        log_file.write_text("line1\nline2\n")
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            monitor._rotate_alerts()
        assert "line1" in log_file.read_text()


# ---------------------------------------------------------------------------
# JidokaMonitor.get_recent_events / get_stats / read_alerts
# ---------------------------------------------------------------------------

class TestQueryMethods:
    def test_get_recent_events_empty(self):
        monitor = JidokaMonitor()
        assert monitor.get_recent_events() == []

    def test_get_recent_events_limit(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        pattern = ErrorPattern(name="build_failure", pattern="x", severity=ErrorSeverity.HIGH)
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            for i in range(15):
                monitor._log_alert(f"w{i}", "err", pattern)
        events = monitor.get_recent_events(limit=5)
        assert len(events) == 5

    def test_get_stats_counts(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        pattern_high = ErrorPattern(name="build_failure", pattern="x", severity=ErrorSeverity.HIGH)
        pattern_critical = ErrorPattern(name="schema_change", pattern="x", severity=ErrorSeverity.CRITICAL)
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            monitor._log_alert("w1", "err", pattern_high)
            monitor._log_alert("w1", "err", pattern_critical)
        stats = monitor.get_stats()
        assert stats["total_events"] == 2
        assert stats["critical_count"] == 1
        assert stats["high_count"] == 1

    def test_read_alerts_returns_lines(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        log_file = tmp_path / "jidoka-alerts.log"
        log_file.write_text("alert1\nalert2\nalert3\n")
        with patch("src.daemon.jidoka.JIDOKA_FILE", log_file):
            lines = monitor.read_alerts(limit=2)
        assert len(lines) == 2

    def test_read_alerts_missing_file_returns_empty(self, tmp_path):
        monitor = _make_monitor(tmp_path)
        missing = tmp_path / "nonexistent.log"
        with patch("src.daemon.jidoka.JIDOKA_FILE", missing):
            result = monitor.read_alerts()
        assert result == []
