"""Plugin Debug Mode.

Provides debugging capabilities for plugin development and troubleshooting:
- Verbose logging
- Step-by-step execution tracing
- State inspection
- Performance profiling
- Error dump generation
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Debug output directory
DEFAULT_DEBUG_DIR = Path.home() / ".mekong" / "debug"


class DebugLevel(str, Enum):
    """Debug verbosity levels."""

    ERROR = "error"  # Only errors
    WARNING = "warning"  # Warnings and errors
    INFO = "info"  # Basic info
    VERBOSE = "verbose"  # Detailed operation logs
    TRACE = "trace"  # Function call tracing
    PROFILE = "profile"  # Performance profiling


@dataclass
class DebugContext:
    """Context for a debug operation."""

    context_id: str
    plugin_id: str
    command: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    level: DebugLevel = DebugLevel.INFO
    trace_calls: bool = False
    profile: bool = False

    # Collected data
    logs: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    state_snapshots: list[dict[str, Any]] = field(default_factory=list)

    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        end = self.ended_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds() * 1000

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "context_id": self.context_id,
            "plugin_id": self.plugin_id,
            "command": self.command,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "level": self.level.value,
            "duration_ms": self.duration_ms(),
            "logs": self.logs,
            "errors": self.errors,
            "performance_metrics": self.performance_metrics,
            "state_snapshots": self.state_snapshots,
        }


class DebugTracer:
    """Traces function calls and execution flow.

    Uses sys.settrace for detailed execution tracing.
    """

    def __init__(self, debug_context: DebugContext) -> None:
        self.context = debug_context
        self._original_trace = None
        self._call_stack: list[dict[str, Any]] = []
        self._indent = 0

    def start(self) -> None:
        """Start tracing."""
        self._original_trace = sys.gettrace()
        sys.settrace(self._trace_calls)

    def stop(self) -> None:
        """Stop tracing."""
        sys.settrace(self._original_trace)
        self._original_trace = None

    def _trace_calls(self, frame, event, arg) -> "DebugTracer | None":
        """Trace function calls."""
        if event == "call":
            code = frame.f_code
            filename = code.co_filename
            lineno = frame.f_lineno
            func_name = code.co_name

            # Skip internal/standard library frames based on config
            if self._should_trace(filename):
                call_info = {
                    "filename": filename,
                    "lineno": lineno,
                    "function": func_name,
                    "timestamp": time.time(),
                }
                self._call_stack.append(call_info)

                if self.context.level == DebugLevel.TRACE:
                    indent = "  " * self._indent
                    logger.debug(
                        f"{indent}→ {func_name} ({Path(filename).name}:{lineno})"
                    )
                self._indent += 1

        elif event == "return":
            if self._call_stack:
                self._call_stack.pop()
                self._indent = max(0, self._indent - 1)

        elif event == "exception":
            if self.context.level in (DebugLevel.ERROR, DebugLevel.VERBOSE):
                exc_type, exc_val, exc_tb = arg
                logger.error(
                    f"Exception in {frame.f_code.co_name}: {exc_type.__name__}: {exc_val}"
                )

        return self


class PerformanceProfiler:
    """Profiles plugin execution performance."""

    def __init__(self, debug_context: DebugContext) -> None:
        self.context = debug_context
        self._timers: dict[str, float] = {}
        self._measurements: dict[str, list[float]] = {}
        self._current_timer: str | None = None

    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self._timers[name] = time.perf_counter()
        if self._current_timer:
            self.stop_timer()

    def stop_timer(self, name: str | None = None) -> float:
        """Stop a timer and record measurement."""
        timer_name = name or self._current_timer
        if timer_name not in self._timers:
            return 0.0

        elapsed = time.perf_counter() - self._timers.pop(timer_name)
        self._measurements.setdefault(timer_name, []).append(elapsed)

        if self.context.level == DebugLevel.PROFILE:
            logger.debug(f"⏱ {timer_name}: {elapsed * 1000:.2f}ms")

        return elapsed

    def get_metrics(self) -> dict[str, dict[str, float]]:
        """Get aggregated metrics."""
        metrics: dict[str, dict[str, float]] = {}
        for name, values in self._measurements.items():
            if values:
                metrics[name] = {
                    "count": len(values),
                    "total_seconds": sum(values),
                    "avg_seconds": sum(values) / len(values),
                    "min_seconds": min(values),
                    "max_seconds": max(values),
                }
        return metrics


class DebugMode:
    """Main debug mode controller.

    Features:
    - Context capture for plugin execution
    - Structured logging
    - Performance profiling
    - Error dump generation
    - State snapshots
    """

    def __init__(
        self,
        debug_dir: Path | None = None,
        level: DebugLevel = DebugLevel.INFO,
        enable_profiling: bool = False,
        enable_tracing: bool = False,
    ) -> None:
        """Initialize debug mode.

        Args:
            debug_dir: Directory for debug outputs
            level: Debug verbosity level
            enable_profiling: Enable performance profiling
            enable_tracing: Enable function call tracing
        """
        self._debug_dir = debug_dir or DEFAULT_DEBUG_DIR
        self._level = level
        self._enable_profiling = enable_profiling or level == DebugLevel.PROFILE
        self._enable_tracing = enable_tracing or level == DebugLevel.TRACE

        self._debug_dir.mkdir(parents=True, exist_ok=True)
        self._active_context: DebugContext | None = None
        self._profiler: PerformanceProfiler | None = None
        self._tracer: DebugTracer | None = None
        self._original_log_level: int | None = None

        # Configure logging for debug
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for debug mode."""
        level_map = {
            DebugLevel.ERROR: logging.ERROR,
            DebugLevel.WARNING: logging.WARNING,
            DebugLevel.INFO: logging.INFO,
            DebugLevel.VERBOSE: logging.DEBUG,
            DebugLevel.TRACE: logging.DEBUG,
            DebugLevel.PROFILE: logging.INFO,
        }

        self._original_log_level = logger.level
        logger.setLevel(level_map.get(self._level, logging.INFO))

        # Add file handler if in verbose mode
        if self._level in (DebugLevel.VERBOSE, DebugLevel.TRACE):
            debug_log = self._debug_dir / "debug.log"
            handler = logging.FileHandler(debug_log, mode="a")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    def start_context(
        self,
        plugin_id: str,
        command: str | None = None,
    ) -> DebugContext:
        """Start a new debug context.

        Args:
            plugin_id: Plugin being debugged
            command: Command being executed

        Returns:
            DebugContext for this execution
        """
        import secrets

        context = DebugContext(
            context_id=f"ctx_{secrets.token_hex(8)}",
            plugin_id=plugin_id,
            command=command,
            started_at=datetime.now(timezone.utc),
            level=self._level,
            trace_calls=self._enable_tracing,
        )

        self._active_context = context

        if self._enable_profiling:
            self._profiler = PerformanceProfiler(context)
            self._profiler.start_timer("total")

        if self._enable_tracing:
            self._tracer = DebugTracer(context)
            self._tracer.start()

        logger.info(
            f"[DEBUG] Started context: {context.context_id} "
            f"(plugin={plugin_id}, command={command})"
        )

        return context

    def end_context(self, success: bool = True) -> DebugContext | None:
        """End current debug context."""
        if not self._active_context:
            return None

        context = self._active_context
        context.ended_at = datetime.now(timezone.utc)

        if self._profiler:
            self._profiler.stop_timer()
            context.performance_metrics = self._profiler.get_metrics()

        if self._tracer:
            self._tracer.stop()

        # Save debug output
        self._save_context(context, success)

        logger.info(
            f"[DEBUG] Ended context: {context.context_id} "
            f"(duration={context.duration_ms():.1f}ms, success={success})"
        )

        self._active_context = None
        self._profiler = None
        self._tracer = None

        return context

    def log(
        self,
        level: DebugLevel,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log a debug message."""
        if not self._active_context:
            return

        log_entry = {
            "timestamp": time.time(),
            "level": level.value,
            "message": message,
            "data": data or {},
        }
        self._active_context.logs.append(log_entry)

        log_func = getattr(logger, level.value, logger.info)
        if data:
            log_func(f"[DEBUG] {message} | data={json.dumps(data, default=str)}")
        else:
            log_func(f"[DEBUG] {message}")

    def capture_error(
        self,
        exc: BaseException,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Capture an error with traceback."""
        if not self._active_context:
            return

        error_entry = {
            "timestamp": time.time(),
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "context": context or {},
        }
        self._active_context.errors.append(error_entry)

        logger.error(f"[DEBUG] Error captured: {type(exc).__name__}: {exc}")

    def capture_state_snapshot(
        self,
        name: str,
        state: dict[str, Any],
    ) -> None:
        """Capture a state snapshot."""
        if not self._active_context:
            return

        snapshot = {
            "name": name,
            "timestamp": time.time(),
            "state": state,
        }
        self._active_context.state_snapshots.append(snapshot)

        if self._level == DebugLevel.VERBOSE:
            logger.debug(f"[DEBUG] State snapshot: {name}")

    def _save_context(self, context: DebugContext, success: bool) -> None:
        """Save debug context to disk."""
        try:
            data = context.to_dict()
            data["success"] = success

            debug_file = (
                self._debug_dir / f"{context.context_id}_{context.plugin_id}.json"
            )
            debug_file.write_text(json.dumps(data, indent=2, default=str))

            # Also save traceback if errors
            if context.errors:
                trace_file = self._debug_dir / f"{context.context_id}_traceback.txt"
                trace_content = "\n\n".join(
                    err["traceback"] for err in context.errors
                )
                trace_file.write_text(trace_content)

        except Exception as e:
            logger.error(f"Failed to save debug context: {e}")

    def get_recent_sessions(
        self,
        plugin_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent debug sessions."""
        sessions = []

        for debug_file in sorted(
            self._debug_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                data = json.loads(debug_file.read_text())
                if plugin_id and data.get("plugin_id") != plugin_id:
                    continue
                sessions.append(data)
                if len(sessions) >= limit:
                    break
            except Exception:
                continue

        return sessions

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Remove old debug session files."""
        cutoff = time.time() - (days * 24 * 3600)
        removed = 0

        for debug_file in self._debug_dir.glob("*.json"):
            if debug_file.stat().st_mtime < cutoff:
                debug_file.unlink(missing_ok=True)
                trace_file = debug_file.with_suffix("_traceback.txt")
                trace_file.unlink(missing_ok=True)
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old debug sessions")

        return removed


class PluginDebugger:
    """Integrated debugger for plugin execution.

    Wraps plugin execution with debug context and reporting.
    """

    def __init__(
        self,
        debug_mode: DebugMode | None = None,
        registry: Any | None = None,
    ) -> None:
        """Initialize plugin debugger."""
        self.debug_mode = debug_mode or DebugMode()
        self.registry = registry

    def execute_with_debug(
        self,
        plugin_id: str,
        command: str,
        execute_fn: callable,
        *args,
        **kwargs,
    ) -> tuple[Any, dict[str, Any]]:
        """Execute a plugin command with debug context.

        Args:
            plugin_id: Plugin ID
            command: Command name
            execute_fn: Function to execute
            *args, **kwargs: Arguments for execute_fn

        Returns:
            (result, debug_report) tuple
        """
        context = self.debug_mode.start_context(plugin_id, command)

        try:
            if self.debug_mode._enable_profiling and self.debug_mode._profiler:
                self.debug_mode._profiler.start_timer("execute")

            result = execute_fn(*args, **kwargs)

            if self.debug_mode._enable_profiling and self.debug_mode._profiler:
                self.debug_mode._profiler.stop_timer("execute")

            context = self.debug_mode.end_context(success=True)

            return result, self._generate_report(context)

        except Exception as e:
            self.debug_mode.capture_error(e, {"plugin_id": plugin_id, "command": command})
            context = self.debug_mode.end_context(success=False)
            raise

    def _generate_report(self, context: DebugContext) -> dict[str, Any]:
        """Generate debug report."""
        report = {
            "context_id": context.context_id,
            "plugin_id": context.plugin_id,
            "command": context.command,
            "duration_ms": context.duration_ms(),
            "success": context.ended_at is not None,
            "error_count": len(context.errors),
            "log_count": len(context.logs),
            "snapshot_count": len(context.state_snapshots),
        }

        if context.performance_metrics:
            report["performance"] = context.performance_metrics

        if context.errors:
            report["errors"] = [
                {"type": e["exception_type"], "message": e["message"]}
                for e in context.errors[:3]
            ]

        return report


def enable_debug_mode(
    level: DebugLevel = DebugLevel.VERBOSE,
    profiling: bool = True,
    tracing: bool = False,
) -> DebugMode:
    """Enable debug mode globally.

    Args:
        level: Debug level
        profiling: Enable performance profiling
        tracing: Enable call tracing

    Returns:
        DebugMode instance
    """
    mode = DebugMode(
        level=level,
        enable_profiling=profiling,
        enable_tracing=tracing,
    )
    logger.info(f"Debug mode enabled: level={level.value}, profiling={profiling}, tracing={tracing}")
    return mode


__all__ = [
    "DebugContext",
    "DebugLevel",
    "DebugMode",
    "DebugTracer",
    "PerformanceProfiler",
    "PluginDebugger",
    "enable_debug_mode",
]
