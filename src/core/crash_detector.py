"""
Mekong CLI - Crash Detector.

Real-time crash detection monitoring CLI execution exit codes.
Emits crash:detected events with metadata and tracks crash frequency.
Triggers auto-recovery on crash detection (Phase 5).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.event_bus import EventType, get_event_bus
from src.core.auto_recovery import RecoveryType, attempt_recovery

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns (module-level, reused across all instances)
# ---------------------------------------------------------------------------

# Fatal Python exception class names at traceback top-level.
_PY_FATAL_PATTERN: re.Pattern[str] = re.compile(
    r"(?:^|\n)(MemoryError|SystemExit|RecursionError|"
    r"Fatal Python error|Py_Initialize)",
    re.IGNORECASE,
)

# Linux OOM killer lines.
_OOM_LINUX_PATTERN: re.Pattern[str] = re.compile(
    r"Out of memory:|oom-killer:|Kill process",
    re.IGNORECASE,
)

# macOS jetsam / pressure termination log strings.
_OOM_MACOS_PATTERN: re.Pattern[str] = re.compile(
    r"jetsam.*kill|memory pressure|terminated due to memory",
    re.IGNORECASE,
)

# Signal-derived exit codes (negative values from shell).
_SIGNAL_MAP: dict[int, str] = {
    9: "SIGKILL",
    11: "SIGSEGV",
}


# ---------------------------------------------------------------------------
# CrashSignal — lightweight detection result (PEV hook output)
# ---------------------------------------------------------------------------


@dataclass
class CrashSignal:
    """A single detected crash signal from step execution."""

    category: str = "unknown"
    signal: str = ""
    detail: str = ""


def _classify_exit_code(exit_code: int) -> CrashSignal | None:
    sig = _SIGNAL_MAP.get(-exit_code)
    if sig:
        return CrashSignal(category="system", signal=sig, detail=f"exit code {exit_code} → {sig}")
    if exit_code < 0:
        return CrashSignal(category="system", signal=f"signal {-exit_code}", detail=f"exit code {exit_code}")
    return None


def _classify_text(text: str) -> list[CrashSignal]:
    signals: list[CrashSignal] = []
    if not text:
        return signals
    if _PY_FATAL_PATTERN.search(text):
        match = _PY_FATAL_PATTERN.search(text)
        signals.append(
            CrashSignal(
                category="python",
                signal=match.group(1),
                detail=f"Fatal Python exception in output",
            )
        )
    if _OOM_LINUX_PATTERN.search(text):
        signals.append(CrashSignal(category="oom", signal="linux-oom", detail="Linux OOM kill string found"))
    if _OOM_MACOS_PATTERN.search(text):
        signals.append(CrashSignal(category="oom", signal="macos-jetsam", detail="macOS memory pressure termination"))
    if "MemoryError" in text:
        signals.append(CrashSignal(category="oom", signal="python-memory", detail="Python MemoryError in output"))
    return signals


# ---------------------------------------------------------------------------
# Lightweight inspect API (PEV hook)
# ---------------------------------------------------------------------------


class CrashPatternDetector:
    """Lightweight crash signal detection without event-bus / disk dependencies.

    Designed to be called inside PEV step execution to annotate
    ``ExecutionResult.metadata["crash_signals"]``.

    Args:
        strict:    When True, classify any non-zero exit code as crash.
                   When False (default), only classify signal-derived codes
                   and fatal pattern matches.
    """

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict

    def inspect(
        self,
        exit_code: int,
        stderr: str = "",
        combined_text: str = "",
    ) -> list[dict[str, str]]:
        """Classify a single step result for crash signals.

        Args:
            exit_code:    Process exit code (negative = OS signal on POSIX).
            stderr:       Standard error text from the step.
            combined_text: Optional combined text (stdout + stderr) for
                           pattern matching and signal detection.

        Returns:
            List of signal dicts with keys: category / signal / detail.
            Empty list when no crash signals detected.
        """
        text = combined_text or stderr or ""
        combined = text if (combined_text and stderr) else (text + "\n" + stderr if text and stderr else text)
        signals: list[CrashSignal] = []

        # Exit code signals
        sig = _classify_exit_code(exit_code)
        if sig:
            signals.append(sig)
        elif self.strict and exit_code != 0:
            signals.append(
                CrashSignal(
                    category="failure",
                    signal="non-zero",
                    detail=f"exit_code={exit_code}",
                )
            )

        # Pattern-based signals from output text
        signals.extend(_classify_text(combined))
        return [{"category": s.category, "signal": s.signal, "detail": s.detail} for s in signals]

    def inspect_step(self, result: Any) -> list[dict[str, str]]:
        """Inspect an ExecutionResult-like object for crash signals.

        Reads ``exit_code``, ``stderr`` and ``metadata.get("command", "")``
        from the result object.  Falls back gracefully when attributes are
        missing.

        Args:
            result: Object with ``exit_code`` (int), ``stderr`` (str),
                    and optional ``metadata`` (dict) attributes.
        """
        exit_code = getattr(result, "exit_code", 0)
        stderr = getattr(result, "stderr", "") or ""
        metadata = getattr(result, "metadata", {}) or {}
        combined = f"{metadata.get('command', '')}\n{stderr}"
        return self.inspect(exit_code, stderr=stderr, combined_text=combined)


def detect_crash_signals(
    exit_code: int,
    stderr: str = "",
    text: str = "",
    strict: bool = False,
) -> list[dict[str, str]]:
    """Convenience wrapper around ``CrashPatternDetector.inspect()``."""
    return CrashPatternDetector(strict=strict).inspect(exit_code, stderr, text)


def reset_crash_pattern_detector() -> None:
    """No global state; stub for symmetry during testing."""
    pass


@dataclass
class CrashEvent:
    """A detected crash event with metadata."""

    crash_id: str
    timestamp: str
    exit_code: int
    command: str
    stderr: str | None = None
    cwd: str | None = None
    duration_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CrashFrequency:
    """Crash frequency metrics."""

    crashes_per_hour: float
    crashes_last_hour: int
    first_crash_time: str | None = None
    last_crash_time: str | None = None


class CrashDetector:
    """Real-time crash detection and tracking.

    Monitors exit codes from CLI executions, emits crash events,
    tracks crash frequency, and persists crash history to disk.
    """

    def __init__(
        self,
        crashes_dir: str = ".mekong/crashes",
        frequency_window_seconds: int = 3600,
    ) -> None:
        """Initialize crash detector.

        Args:
            crashes_dir: Directory to store crash history
            frequency_window_seconds: Time window for frequency calculation
        """
        self.crashes_dir = Path(crashes_dir)
        self.frequency_window = frequency_window_seconds
        self._event_bus = get_event_bus()

        # In-memory crash history (last 100 crashes)
        self._recent_crashes: deque[CrashEvent] = deque(maxlen=100)

        # Crash times for frequency calculation
        self._crash_times: deque[float] = deque(maxlen=1000)

        # Ensure crashes directory exists
        self._init_storage()

    def _init_storage(self) -> None:
        """Initialize crash storage directory."""
        try:
            self.crashes_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Crash storage initialized at {self.crashes_dir}")
        except Exception as e:
            logger.warning(f"Failed to create crash directory: {e}")

    def record_crash(
        self,
        exit_code: int,
        command: str,
        stderr: str | None = None,
        cwd: str | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CrashEvent:
        """Record a crash event.

        Args:
            exit_code: Exit code from the crashed process
            command: Command that was executing
            stderr: Standard error output (optional)
            cwd: Working directory when crash occurred
            duration_ms: Execution duration in milliseconds
            metadata: Additional crash metadata

        Returns:
            CrashEvent that was recorded
        """
        crash = CrashEvent(
            crash_id=self._generate_crash_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            exit_code=exit_code,
            command=command,
            stderr=stderr,
            cwd=cwd,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        # Store in memory
        self._recent_crashes.append(crash)
        self._crash_times.append(time.time())

        # Emit event
        self._event_bus.emit(
            EventType.HEALTH_CRITICAL,
            {
                "type": "crash:detected",
                "crash_id": crash.crash_id,
                "exit_code": exit_code,
                "command": command,
                "timestamp": crash.timestamp,
            },
        )

        # Trigger auto-recovery (Phase 5)
        # Fire-and-forget: schedule coroutine without awaiting to avoid blocking
        self._schedule_recovery(exit_code, command)

        # Persist to disk
        self._persist_crash(crash)

        logger.warning(
            f"Crash detected: exit_code={exit_code}, command='{command[:50]}...'",
        )

        return crash

    def _schedule_recovery(
        self,
        exit_code: int,
        command: str,
    ) -> None:
        """Schedule recovery task, handling both sync and async contexts.

        Args:
            exit_code: Exit code from crashed process
            command: Command that crashed
        """
        try:
            # Check if event loop is running
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop is running - create task normally
                loop.create_task(self._trigger_recovery(exit_code, command))
            else:
                # Event loop exists but not running - run synchronously
                loop.run_until_complete(self._trigger_recovery(exit_code, command))
        except RuntimeError:
            # No event loop - run synchronously with new loop
            asyncio.run(self._trigger_recovery(exit_code, command))

    async def _trigger_recovery(
        self,
        exit_code: int,
        command: str,
    ) -> None:
        """
        Trigger auto-recovery for crash.

        Args:
            exit_code: Exit code from crashed process
            command: Command that crashed
        """
        logger.info(f"Triggering auto-recovery for crash (exit_code={exit_code})")
        try:
            result = await attempt_recovery(
                recovery_type=RecoveryType.CRASH_RECOVERY,
                metadata={
                    "exit_code": exit_code,
                    "command": command,
                },
            )
            if result.status.value == "success":
                logger.info(f"Crash recovery succeeded after {result.attempt_number} attempt(s)")
            else:
                logger.error(
                    f"Crash recovery failed after {result.attempt_number} attempt(s): "
                    f"{result.error_message}"
                )
        except Exception as e:
            logger.error(f"Error triggering crash recovery: {e}")

    def _generate_crash_id(self) -> str:
        """Generate unique crash ID."""
        return f"crash-{int(time.time() * 1000)}-{os.getpid()}"

    def _persist_crash(self, crash: CrashEvent) -> None:
        """Persist crash event to JSON file.

        Args:
            crash: CrashEvent to persist
        """
        try:
            crash_file = self.crashes_dir / f"{crash.crash_id}.json"
            crash_data = crash.to_dict()
            crash_data["crashes_dir"] = str(self.crashes_dir)

            crash_file.write_text(
                json.dumps(crash_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.debug(f"Crash persisted to {crash_file}")
        except Exception as e:
            logger.error(f"Failed to persist crash: {e}")

    def get_frequency(self) -> CrashFrequency:
        """Calculate crash frequency over the configured window.

        Returns:
            CrashFrequency with metrics
        """
        now = time.time()
        window_start = now - self.frequency_window

        # Count crashes in window
        crashes_in_window = [t for t in self._crash_times if t >= window_start]
        crash_count = len(crashes_in_window)

        # Calculate frequency (crashes per hour)
        hours = self.frequency_window / 3600
        crashes_per_hour = crash_count / hours if hours > 0 else 0.0

        # Get first and last crash times
        first_crash = None
        last_crash = None
        if crashes_in_window:
            first_crash = datetime.fromtimestamp(
                min(crashes_in_window), tz=timezone.utc,
            ).isoformat()
            last_crash = datetime.fromtimestamp(
                max(crashes_in_window), tz=timezone.utc,
            ).isoformat()

        return CrashFrequency(
            crashes_per_hour=crashes_per_hour,
            crashes_last_hour=crash_count,
            first_crash_time=first_crash,
            last_crash_time=last_crash,
        )

    def get_recent_crashes(
        self,
        limit: int = 10,
    ) -> list[CrashEvent]:
        """Get recent crash events from memory.

        Args:
            limit: Maximum number of crashes to return

        Returns:
            List of recent CrashEvents (newest first)
        """
        return list(self._recent_crashes)[-limit:][::-1]

    def load_crashes_from_disk(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Load crash history from disk.

        Args:
            limit: Maximum number of crashes to load

        Returns:
            List of crash data dictionaries (newest first)
        """
        if not self.crashes_dir.exists():
            return []

        try:
            crash_files = sorted(
                self.crashes_dir.glob("crash-*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            crashes = []
            for crash_file in crash_files[:limit]:
                try:
                    data = json.loads(crash_file.read_text(encoding="utf-8"))
                    crashes.append(data)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Failed to load crash file {crash_file}: {e}")

            return crashes
        except Exception as e:
            logger.error(f"Failed to load crash history: {e}")
            return []

    def get_crash_summary(self) -> dict[str, Any]:
        """Get summary of crash statistics.

        Returns:
            Dictionary with crash statistics
        """
        frequency = self.get_frequency()
        recent = self.get_recent_crashes(limit=5)

        # Count by exit code
        exit_code_counts: dict[int, int] = {}
        for crash in self._recent_crashes:
            exit_code_counts[crash.exit_code] = (
                exit_code_counts.get(crash.exit_code, 0) + 1
            )

        return {
            "total_crashes_stored": len(self._recent_crashes),
            "frequency": asdict(frequency),
            "recent_crashes": [c.to_dict() for c in recent],
            "exit_code_distribution": exit_code_counts,
        }

    def clear_history(self) -> int:
        """Clear in-memory crash history.

        Returns:
            Number of crashes cleared
        """
        count = len(self._recent_crashes)
        self._recent_crashes.clear()
        self._crash_times.clear()
        logger.info(f"Cleared {count} crashes from memory")
        return count

    def cleanup_old_crashes(
        self,
        max_age_days: int = 30,
    ) -> int:
        """Remove old crash files from disk.

        Args:
            max_age_days: Maximum age of crashes to keep

        Returns:
            Number of files deleted
        """
        if not self.crashes_dir.exists():
            return 0

        cutoff = time.time() - (max_age_days * 24 * 60 * 60)
        deleted = 0

        try:
            for crash_file in self.crashes_dir.glob("crash-*.json"):
                if crash_file.stat().st_mtime < cutoff:
                    crash_file.unlink()
                    deleted += 1
        except Exception as e:
            logger.error(f"Failed to cleanup old crashes: {e}")

        logger.info(f"Cleaned up {deleted} crash files older than {max_age_days} days")
        return deleted


# Global crash detector instance
_crash_detector: CrashDetector | None = None


def get_crash_detector(
    crashes_dir: str = ".mekong/crashes",
) -> CrashDetector:
    """Get or create the global crash detector instance.

    Args:
        crashes_dir: Directory for crash storage

    Returns:
        CrashDetector instance
    """
    global _crash_detector
    if _crash_detector is None:
        _crash_detector = CrashDetector(crashes_dir=crashes_dir)
    return _crash_detector


def reset_crash_detector() -> None:
    """Reset the global crash detector (for testing)."""
    global _crash_detector
    _crash_detector = None


__all__ = [
    "CrashEvent",
    "CrashFrequency",
    "CrashDetector",
    "CrashSignal",
    "CrashPatternDetector",
    "detect_crash_signals",
    "reset_crash_detector",
    "reset_crash_pattern_detector",
    "get_crash_detector",
]
