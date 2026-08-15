"""Extended coverage tests for src/core/telemetry_collector.py.

Targets uncovered paths:
- TelemetryEvent.to_dict
- TelemetryCollector.start_trace / finish_trace / get_trace
- TelemetryCollector.record_step / record_llm_call / record_error
- TelemetryCollector._ensure_anonymous_id (consent/no-consent)
- TelemetryCollector._get_session_id
- TelemetryCollector._hash_error
- TelemetryCollector._get_python_version / _get_os_info
- TelemetryCollector.session_start (idempotent, no consent)
- TelemetryCollector.command_executed (with/without error_type)
- TelemetryCollector.error_occurred
- TelemetryCollector.session_end
- TelemetryCollector._check_buffer / _flush / _flush_on_exit
- TelemetryCollector.get_pending_events / clear_buffer
- get_collector / track_command / track_error module helpers
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock


from src.core.telemetry_collector import (
    TelemetryCollector,
    TelemetryEvent,
    get_collector,
    track_command,
    track_error,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_collector(tmp_path: Path, has_consent: bool = True) -> TelemetryCollector:
    """Create an isolated TelemetryCollector with mocked consent and tmp storage."""
    mock_consent = MagicMock()
    mock_consent.has_consent.return_value = has_consent
    mock_consent.get_anonymous_id.return_value = "anon-123" if has_consent else None
    collector = TelemetryCollector(consent_manager=mock_consent)
    collector._storage_file = tmp_path / "telemetry-buffer.json"
    return collector


# ---------------------------------------------------------------------------
# TelemetryEvent
# ---------------------------------------------------------------------------

class TestTelemetryEvent:
    def test_to_dict_contains_all_fields(self):
        evt = TelemetryEvent(
            event_type="session_started",
            anonymous_id="anon-1",
            timestamp="2026-01-01T00:00:00+00:00",
            session_id="sess-1",
            properties={"os": "darwin"},
        )
        d = evt.to_dict()
        assert d["event_type"] == "session_started"
        assert d["anonymous_id"] == "anon-1"
        assert d["properties"]["os"] == "darwin"
        assert d["cli_version"] == "3.0.0"


# ---------------------------------------------------------------------------
# Trace-based API
# ---------------------------------------------------------------------------

class TestTraceAPI:
    def test_start_and_finish_trace(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("deploy app")
        assert collector.get_trace() is not None
        assert collector.get_trace().goal == "deploy app"
        trace = collector.finish_trace()
        assert trace.goal == "deploy app"
        assert collector.get_trace() is None

    def test_finish_trace_without_start_returns_empty_trace(self, tmp_path):
        collector = _make_collector(tmp_path)
        trace = collector.finish_trace()
        assert trace is not None
        assert trace.goal == ""

    def test_finish_trace_sets_total_duration(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("goal")
        trace = collector.finish_trace()
        assert trace.total_duration >= 0

    def test_finish_trace_writes_to_output_dir(self, tmp_path):
        output = tmp_path / "traces"
        mock_consent = MagicMock()
        mock_consent.has_consent.return_value = True
        mock_consent.get_anonymous_id.return_value = "anon"
        collector = TelemetryCollector(consent_manager=mock_consent, output_dir=str(output))
        collector.start_trace("write test")
        collector.finish_trace()
        assert (output / "execution_trace.json").exists()

    def test_record_step_appends_to_trace(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("run steps")
        collector.record_step(step_order=1, title="Step A", duration_seconds=1.0, exit_code=0)
        trace = collector.get_trace()
        assert len(trace.steps) == 1
        assert trace.steps[0].title == "Step A"

    def test_record_step_duration_alias(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("test")
        collector.record_step(step_order=1, title="S", duration=2.5)
        assert collector.get_trace().steps[0].duration_seconds == 2.5

    def test_record_step_no_trace_is_noop(self, tmp_path):
        collector = _make_collector(tmp_path)
        # No trace started — should not raise
        collector.record_step(step_order=1, title="X")

    def test_record_llm_call_increments_counter(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("llm test")
        collector.record_llm_call()
        collector.record_llm_call()
        assert collector.get_trace().llm_calls == 2

    def test_record_llm_call_no_trace_is_noop(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.record_llm_call()  # Should not raise

    def test_record_error_appends_message(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.start_trace("err test")
        collector.record_error("Something went wrong")
        assert "Something went wrong" in collector.get_trace().errors

    def test_record_error_no_trace_is_noop(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.record_error("err")  # Should not raise


# ---------------------------------------------------------------------------
# Anonymous ID / Session ID / Hash helpers
# ---------------------------------------------------------------------------

class TestInternalHelpers:
    def test_ensure_anonymous_id_returns_none_when_no_consent(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=False)
        assert collector._ensure_anonymous_id() is None

    def test_ensure_anonymous_id_returns_id_with_consent(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=True)
        assert collector._ensure_anonymous_id() == "anon-123"

    def test_get_session_id_stable(self, tmp_path):
        collector = _make_collector(tmp_path)
        s1 = collector._get_session_id()
        s2 = collector._get_session_id()
        assert s1 == s2
        assert len(s1) > 0

    def test_hash_error_returns_16_chars(self, tmp_path):
        collector = _make_collector(tmp_path)
        h = collector._hash_error("ImportError: foo")
        assert len(h) == 16

    def test_hash_error_deterministic(self, tmp_path):
        collector = _make_collector(tmp_path)
        assert collector._hash_error("err") == collector._hash_error("err")

    def test_hash_error_different_inputs(self, tmp_path):
        collector = _make_collector(tmp_path)
        assert collector._hash_error("err1") != collector._hash_error("err2")

    def test_get_python_version_returns_string(self, tmp_path):
        collector = _make_collector(tmp_path)
        v = collector._get_python_version()
        assert isinstance(v, str)
        assert "." in v

    def test_get_os_info_returns_string(self, tmp_path):
        collector = _make_collector(tmp_path)
        os_info = collector._get_os_info()
        assert isinstance(os_info, str)
        assert len(os_info) > 0


# ---------------------------------------------------------------------------
# Event-based API: session_start
# ---------------------------------------------------------------------------

class TestSessionStart:
    def test_session_start_with_consent_adds_event(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=True)
        collector.session_start()
        assert len(collector._buffer) == 1
        assert collector._buffer[0].event_type == "session_started"

    def test_session_start_idempotent(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=True)
        collector.session_start()
        collector.session_start()
        assert len(collector._buffer) == 1  # only one event

    def test_session_start_no_consent_skips_event(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=False)
        collector.session_start()
        assert len(collector._buffer) == 0
        assert collector._initialized is True


# ---------------------------------------------------------------------------
# Event-based API: command_executed
# ---------------------------------------------------------------------------

class TestCommandExecuted:
    def test_records_command_event(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.command_executed("cook", 500, 0)
        events = [e for e in collector._buffer if e.event_type == "command_executed"]
        assert len(events) == 1
        assert events[0].properties["command"] == "cook"
        assert events[0].properties["success"] is True

    def test_records_error_type_hash(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.command_executed("fix", 200, 1, error_type="ValueError")
        evt = [e for e in collector._buffer if e.event_type == "command_executed"][0]
        assert "error_type_hash" in evt.properties

    def test_no_consent_skips_event(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=False)
        collector.command_executed("cook", 100, 0)
        cmd_events = [e for e in collector._buffer if e.event_type == "command_executed"]
        assert len(cmd_events) == 0

    def test_increments_commands_count(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.command_executed("cmd1", 10, 0)
        collector.command_executed("cmd2", 20, 0)
        assert collector._commands_count == 2


# ---------------------------------------------------------------------------
# Event-based API: error_occurred
# ---------------------------------------------------------------------------

class TestErrorOccurred:
    def test_records_error_event(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.error_occurred("ValueError", "bad value", "cook")
        evt = [e for e in collector._buffer if e.event_type == "error_occurred"][0]
        assert evt.properties["error_type"] == "ValueError"
        assert evt.properties["command"] == "cook"
        assert "error_message_hash" in evt.properties

    def test_no_consent_skips_event(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=False)
        collector.error_occurred("ValueError", "bad")
        assert len(collector._buffer) == 0


# ---------------------------------------------------------------------------
# Event-based API: session_end
# ---------------------------------------------------------------------------

class TestSessionEnd:
    def test_records_session_ended_event(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._session_start = time.time() - 1.0  # 1 second ago
        collector.session_end()
        evt = [e for e in collector._buffer if e.event_type == "session_ended"][0]
        assert evt.properties["duration_ms"] >= 1000
        assert "commands_count" in evt.properties

    def test_session_end_no_consent_skips(self, tmp_path):
        collector = _make_collector(tmp_path, has_consent=False)
        collector.session_end()
        assert len(collector._buffer) == 0


# ---------------------------------------------------------------------------
# Buffer management: _check_buffer / _flush
# ---------------------------------------------------------------------------

class TestBufferManagement:
    def test_flush_writes_to_storage(self, tmp_path):
        collector = _make_collector(tmp_path)
        evt = TelemetryEvent(
            event_type="test", anonymous_id="a", timestamp="ts", session_id="s"
        )
        collector._buffer.append(evt)
        collector._flush()
        assert collector._storage_file.exists()
        data = json.loads(collector._storage_file.read_text())
        assert len(data) == 1
        assert data[0]["event_type"] == "test"

    def test_flush_appends_to_existing(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._storage_file.write_text(json.dumps([{"event_type": "old"}]))
        evt = TelemetryEvent(
            event_type="new", anonymous_id="a", timestamp="ts", session_id="s"
        )
        collector._buffer.append(evt)
        collector._flush()
        data = json.loads(collector._storage_file.read_text())
        assert len(data) == 2

    def test_flush_clears_buffer(self, tmp_path):
        collector = _make_collector(tmp_path)
        evt = TelemetryEvent(
            event_type="test", anonymous_id="a", timestamp="ts", session_id="s"
        )
        collector._buffer.append(evt)
        collector._flush()
        assert collector._buffer == []

    def test_flush_noop_when_empty(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._flush()  # Should not raise
        assert not collector._storage_file.exists()

    def test_check_buffer_flushes_when_full(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._max_buffer_size = 3
        for i in range(3):
            evt = TelemetryEvent(
                event_type=f"e{i}", anonymous_id="a", timestamp="ts", session_id="s"
            )
            collector._buffer.append(evt)
        collector._check_buffer()
        assert collector._buffer == []

    def test_flush_handles_corrupt_json_in_storage(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._storage_file.write_text("INVALID JSON{{")
        evt = TelemetryEvent(
            event_type="test", anonymous_id="a", timestamp="ts", session_id="s"
        )
        collector._buffer.append(evt)
        collector._flush()  # Should not raise
        data = json.loads(collector._storage_file.read_text())
        assert len(data) == 1


# ---------------------------------------------------------------------------
# get_pending_events / clear_buffer
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_get_pending_events_returns_stored(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._storage_file.write_text(json.dumps([{"event_type": "x"}]))
        events = collector.get_pending_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "x"

    def test_get_pending_events_empty_when_no_file(self, tmp_path):
        collector = _make_collector(tmp_path)
        assert collector.get_pending_events() == []

    def test_get_pending_events_handles_corrupt_file(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._storage_file.write_text("bad json")
        assert collector.get_pending_events() == []

    def test_clear_buffer_deletes_file(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector._storage_file.write_text("[]")
        collector.clear_buffer()
        assert not collector._storage_file.exists()

    def test_clear_buffer_noop_when_no_file(self, tmp_path):
        collector = _make_collector(tmp_path)
        collector.clear_buffer()  # Should not raise


# ---------------------------------------------------------------------------
# Module-level helpers: get_collector, track_command, track_error
# ---------------------------------------------------------------------------

class TestModuleHelpers:
    def test_get_collector_returns_singleton(self):
        import src.core.telemetry_collector as mod
        mod._collector = None  # reset
        c1 = get_collector()
        c2 = get_collector()
        assert c1 is c2
        mod._collector = None  # cleanup

    def test_track_command_delegates(self):
        import src.core.telemetry_collector as mod
        mock_col = MagicMock()
        mod._collector = mock_col
        track_command("cook", 100, 0, "ValueError")
        mock_col.command_executed.assert_called_once_with("cook", 100, 0, "ValueError")
        mod._collector = None

    def test_track_error_delegates(self):
        import src.core.telemetry_collector as mod
        mock_col = MagicMock()
        mod._collector = mock_col
        track_error("TypeError", "bad type", "run")
        mock_col.error_occurred.assert_called_once_with("TypeError", "bad type", "run")
        mod._collector = None
