"""Tests for CrashPatternDetector and CrashDetector (Phase C3 - crash_detector.py)."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.crash_detector import (
    CrashDetector,
    CrashEvent,
    CrashFrequency,
    CrashPatternDetector,
    CrashSignal,
    detect_crash_signals,
    get_crash_detector,
    reset_crash_detector,
    reset_crash_pattern_detector,
    _OOM_LINUX_PATTERN,
    _OOM_MACOS_PATTERN,
    _PY_FATAL_PATTERN,
    _SIGNAL_MAP,
    _classify_exit_code,
    _classify_text,
)


# ===========================================================================
# _classify_exit_code
# ===========================================================================


class TestClassifyExitCode:
    def test_zero_returns_none(self):
        assert _classify_exit_code(0) is None

    def test_positive_nonzero_returns_none(self):
        assert _classify_exit_code(1) is None
        assert _classify_exit_code(42) is None

    def test_negative_sigkill(self):
        sig = _classify_exit_code(-9)
        assert sig is not None
        assert sig.category == "system"
        assert sig.signal == "SIGKILL"
        assert "exit code -9" in sig.detail

    def test_negative_sigsegv(self):
        sig = _classify_exit_code(-11)
        assert sig is not None
        assert sig.signal == "SIGSEGV"

    def test_negative_unknown_signal(self):
        sig = _classify_exit_code(-15)
        assert sig is not None
        assert sig.signal == "signal 15"
        assert sig.category == "system"

    def test_all_mapped_signals_detected(self):
        for code, name in _SIGNAL_MAP.items():
            sig = _classify_exit_code(-code)
            assert sig is not None
            assert sig.signal == name


# ===========================================================================
# _classify_text
# ===========================================================================


class TestClassifyText:
    def test_empty_returns_empty(self):
        assert _classify_text("") == []
        assert _classify_text("   ") == []

    def test_memory_error(self):
        sigs = _classify_text("Traceback (most recent call last):\nMemoryError")
        assert any(s.category == "oom" for s in sigs)
        assert any(s.signal == "python-memory" for s in sigs)

    def test_fatal_python_error(self):
        sigs = _classify_text("Fatal Python error: Abort (core dumped)")
        assert any(s.category == "python" for s in sigs)

    def test_recursion_error(self):
        sigs = _classify_text("RecursionError: maximum recursion depth exceeded")
        assert any(s.category == "python" for s in sigs)

    def test_system_exit(self):
        sigs = _classify_text("SystemExit(1)")
        assert any(s.category == "python" for s in sigs)

    def test_linux_oom(self):
        sigs = _classify_text("Out of memory: Kill process 12345")
        assert any(s.category == "oom" for s in sigs)
        assert any(s.signal == "linux-oom" for s in sigs)

    def test_linux_oom_killer(self):
        sigs = _classify_text("oom-killer: invoked oom-killer")
        assert any(s.category == "oom" for s in sigs)

    def test_macos_jetsam(self):
        sigs = _classify_text("jetsam: kill terminated due to memory pressure")
        assert any("macos-jetsam" in s.signal for s in sigs)

    def test_macos_memory_pressure(self):
        sigs = _classify_text("terminated due to memory pressure")
        assert any(s.category == "oom" for s in sigs)

    def test_multiple_signals_in_text(self):
        text = "Fatal Python error\nOut of memory: Kill process"
        sigs = _classify_text(text)
        cats = {s.category for s in sigs}
        assert "python" in cats
        assert "oom" in cats


# ===========================================================================
# CrashPatternDetector.inspect
# ===========================================================================


class TestCrashPatternDetectorInspect:
    def setup_method(self):
        self.det = CrashPatternDetector()

    def test_clean_result(self):
        assert self.det.inspect(0, "", "hello world") == []

    def test_sigkill_exit_code(self):
        sigs = self.det.inspect(-9, "", "text")
        assert len(sigs) == 1
        assert sigs[0]["signal"] == "SIGKILL"

    def test_sigsegv_exit_code(self):
        sigs = self.det.inspect(-11, "", "text")
        assert any(s["signal"] == "SIGSEGV" for s in sigs)

    def test_pattern_in_stderr(self):
        sigs = self.det.inspect(1, "MemoryError", "")
        assert any(s["signal"] == "python-memory" for s in sigs)

    def test_pattern_in_combined(self):
        """Pattern from combined_text should be detected even if stderr is empty."""
        sigs = self.det.inspect(0, "", "Out of memory: Kill process 999")
        assert any(s["category"] == "oom" for s in sigs)

    def test_strict_mode_nonzero(self):
        det = CrashPatternDetector(strict=True)
        sigs = det.inspect(1, "", "")
        assert len(sigs) == 1
        assert sigs[0]["category"] == "failure"
        assert sigs[0]["signal"] == "non-zero"

    def test_strict_mode_zero_clean(self):
        det = CrashPatternDetector(strict=True)
        assert det.inspect(0, "", "") == []

    def test_strict_mode_no_double_count_for_mapped_signal(self):
        """Mapped signal codes should NOT also be counted as strict non-zero."""
        det = CrashPatternDetector(strict=True)
        sigs = det.inspect(-9, "", "")
        assert len(sigs) == 1
        assert sigs[0]["signal"] == "SIGKILL"


# ===========================================================================
# CrashPatternDetector.inspect_step
# ===========================================================================


class TestCrashPatternDetectorInspectStep:
    def setup_method(self):
        self.det = CrashPatternDetector()

    def test_clean_execution_result(self):
        mock = MagicMock()
        mock.exit_code = 0
        mock.stderr = ""
        mock.metadata = {}
        assert self.det.inspect_step(mock) == []

    def test_sigsegv_in_result(self):
        mock = MagicMock()
        mock.exit_code = -11
        mock.stderr = "segfault log"
        mock.metadata = {"command": "mycmd"}
        sigs = self.det.inspect_step(mock)
        assert any(s["signal"] == "SIGSEGV" for s in sigs)

    def test_uses_command_in_combined(self):
        mock = MagicMock()
        mock.exit_code = -9
        mock.stderr = ""
        mock.metadata = {"command": "`rm -rf /`"}
        sigs = self.det.inspect_step(mock)
        assert any(s["signal"] == "SIGKILL" for s in sigs)

    def test_missing_metadata_falls_back_gracefully(self):
        mock = MagicMock()
        mock.exit_code = 0
        mock.stderr = "some error"
        mock.metadata = None
        # Should not raise — None metadata is handled
        sigs = self.det.inspect_step(mock)
        assert isinstance(sigs, list)


# ===========================================================================
# detect_crash_signals wrapper
# ===========================================================================


class TestDetectCrashSignalsWrapper:
    def test_sigkill(self):
        sigs = detect_crash_signals(-9, "segfault")
        assert sigs[0]["signal"] == "SIGKILL"

    def test_strict_flag(self):
        sigs = detect_crash_signals(1, "", "", strict=True)
        assert sigs[0]["signal"] == "non-zero"

    def test_combined_with_text(self):
        """MemoryError in combined_text should be detected as python-memory."""
        # _classify_text scans combined text; "MemoryError" → python-memory
        sigs = detect_crash_signals(0, "", "MemoryError")
        assert any(s["signal"] == "python-memory" for s in sigs)

    def test_default_non_strict_nonzero_clean(self):
        sigs = detect_crash_signals(1, "some stderr", "")
        # exit_code=1 is positive, no mapped signal, non-strict -> empty
        assert sigs == []


# ===========================================================================
# CrashSignal / CrashEvent / CrashFrequency dataclasses
# ===========================================================================


class TestCrashSignal:
    def test_defaults(self):
        s = CrashSignal()
        assert s.category == "unknown"
        assert s.signal == ""
        assert s.detail == ""

    def test_values(self):
        s = CrashSignal(category="system", signal="SIGKILL", detail="exit -9")
        assert s.category == "system"

    def test_to_dict(self):
        from dataclasses import asdict

        s = CrashSignal(category="system", signal="SIGKILL", detail="exit -9")
        d = asdict(s)
        assert d["signal"] == "SIGKILL"


class TestCrashEvent:
    def test_to_dict(self):
        e = CrashEvent(
            crash_id="c1",
            timestamp="2026-01-01T00:00:00+00:00",
            exit_code=-9,
            command="python app.py",
            stderr=None,
            cwd="/tmp",
            duration_ms=100.0,
            metadata={"sig": "SIGKILL"},
        )
        d = e.to_dict()
        assert d["crash_id"] == "c1"
        assert d["exit_code"] == -9
        assert d["metadata"]["sig"] == "SIGKILL"

    def test_crash_id_format(self):
        """Crash events should have IDs starting with 'crash-'."""
        # Use the private method via the detector instance
        det = CrashDetector(crashes_dir=".mekong/crashes")
        cid = det._generate_crash_id()
        assert cid.startswith("crash-")


class TestCrashFrequency:
    def test_zero(self):
        f = CrashFrequency(crashes_per_hour=0.0, crashes_last_hour=0)
        assert f.crashes_per_hour == 0.0

    def test_with_data(self):
        f = CrashFrequency(
            crashes_per_hour=3.5,
            crashes_last_hour=3,
            first_crash_time="T1",
            last_crash_time="T3",
        )
        assert f.crashes_per_hour == 3.5


# ===========================================================================
# CrashDetector (persistent crash tracking)
# ===========================================================================


class TestCrashDetectorRecord:
    def setup_method(self):
        self.det = CrashDetector(crashes_dir=".mekong/crashes")

    def test_record_returns_crash_event(self):
        e = self.det.record_crash(-9, "python app.py", stderr="segfault")
        assert isinstance(e, CrashEvent)
        assert e.exit_code == -9
        assert e.command == "python app.py"
        assert e.crash_id.startswith("crash-")

    def test_record_persists_to_disk(self, tmp_path):
        det = CrashDetector(crashes_dir=str(tmp_path / "c"))
        e = det.record_crash(1, "failing-cmd", stderr="error", cwd=str(tmp_path))
        p = tmp_path / "c" / f"{e.crash_id}.json"
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["exit_code"] == 1
        assert data["command"] == "failing-cmd"

    def test_appended_to_recent(self):
        e1 = self.det.record_crash(-9, "cmd1")
        e2 = self.det.record_crash(-11, "cmd2")
        recent = self.det.get_recent_crashes(limit=5)
        ids = [c.crash_id for c in recent]
        assert e1.crash_id in ids
        assert e2.crash_id in ids

    def test_recent_respects_limit(self):
        for i in range(15):
            self.det.record_crash(-9, f"cmd{i}")
        recent = self.det.get_recent_crashes(limit=5)
        assert len(recent) == 5

    def test_recent_returns_newest_first(self):
        self.det.record_crash(-9, "first")
        e2 = self.det.record_crash(-9, "second")
        recent = self.det.get_recent_crashes(limit=2)
        assert recent[0].command == "second"
        assert recent[1].command == "first"

    def test_record_triggers_recovery_no_raise(self):
        """record_crash schedules recovery without raising."""
        with patch.object(self.det, "_trigger_recovery"):
            self.det.record_crash(-9, "cmd")
        # If we get here without exception, recovery scheduling worked


class TestCrashDetectorFrequency:
    def setup_method(self):
        self.det = CrashDetector(crashes_dir=".mekong/crashes")

    def test_zero_crashes(self):
        freq = self.det.get_frequency()
        assert freq.crashes_last_hour == 0
        assert freq.crashes_per_hour == 0.0

    def test_crashes_in_window(self):
        now = time.time()
        self.det._crash_times.append(now - 100)  # ~100s ago
        self.det._crash_times.append(now - 500)
        freq = self.det.get_frequency()
        assert freq.crashes_last_hour == 2
        assert freq.crashes_per_hour > 0


class TestCrashDetectorDiskOperations:
    def setup_method(self):
        self.det = CrashDetector(crashes_dir=".mekong/crashes")

    def test_load_empty(self, tmp_path):
        """A fresh detector with an empty dir should return no crashes."""
        det = CrashDetector(crashes_dir=str(tmp_path / "empty"))
        assert det.load_crashes_from_disk() == []

    def test_load_after_record(self, tmp_path):
        det = CrashDetector(crashes_dir=str(tmp_path / "d"))
        det.record_crash(-9, "test", stderr="segfault")
        crashes = det.load_crashes_from_disk(limit=10)
        assert len(crashes) == 1
        assert crashes[0]["exit_code"] == -9

    def test_clear_history(self):
        self.det.record_crash(1, "a")
        self.det.record_crash(2, "b")
        count = self.det.clear_history()
        assert count == 2
        assert len(self.det.get_recent_crashes()) == 0

    def test_cleanup_old_crashes(self, tmp_path):
        det = CrashDetector(crashes_dir=str(tmp_path / "old"))
        # Create a crash file
        e = det.record_crash(1, "old-cmd")
        assert det.cleanup_old_crashes(max_age_days=0) == 1
        assert not (tmp_path / "old" / f"{e.crash_id}.json").exists()

    def test_cleanup_keeps_recent(self, tmp_path):
        det = CrashDetector(crashes_dir=str(tmp_path / "recent"))
        e = det.record_crash(1, "recent-cmd")
        assert det.cleanup_old_crashes(max_age_days=1) == 0
        assert (tmp_path / "recent" / f"{e.crash_id}.json").exists()


class TestCrashDetectorSummary:
    def setup_method(self):
        self.det = CrashDetector(crashes_dir=".mekong/crashes")

    def test_summary_structure(self):
        self.det.record_crash(-9, "cmd1")
        summary = self.det.get_crash_summary()
        assert "total_crashes_stored" in summary
        assert "frequency" in summary
        assert "recent_crashes" in summary
        assert "exit_code_distribution" in summary

    def test_exit_code_distribution(self):
        self.det.record_crash(-9, "a")
        self.det.record_crash(-9, "b")
        self.det.record_crash(1, "c")
        dist = self.det.get_crash_summary()["exit_code_distribution"]
        assert dist[-9] == 2
        assert dist[1] == 1


# ===========================================================================
# Global singleton
# ===========================================================================


class TestGlobalInstance:
    def test_get_creates(self):
        reset_crash_detector()
        det = get_crash_detector()
        assert det is not None

    def test_get_returns_same(self):
        reset_crash_detector()
        det1 = get_crash_detector()
        det2 = get_crash_detector()
        assert det1 is det2

    def test_reset_clears(self):
        get_crash_detector()
        reset_crash_detector()
        # After reset, next call creates a new instance
        det = get_crash_detector()
        assert det is not None


# ===========================================================================
# Reset stubs
# ===========================================================================


class TestResetStubs:
    def test_reset_crash_detector(self):
        reset_crash_detector()
        get_crash_detector()  # recreate
        reset_crash_detector()  # should not raise

    def test_reset_crash_pattern_detector(self):
        reset_crash_pattern_detector()  # should not raise
