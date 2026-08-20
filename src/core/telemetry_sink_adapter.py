# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps TelemetryCollector to satisfy ObservabilitySink Protocol."""

from __future__ import annotations

from typing import Any, Dict


class TelemetrySinkAdapter:
    """Thin adapter mapping ObservabilitySink Protocol to TelemetryCollector.

    Protocol → Implementation:
    - emit(event)  → command_executed / error_occurred / session_start
    - flush()      → no-op (collector flushes on shutdown/atexit)
    """

    def __init__(self) -> None:
        from src.core.telemetry_collector import get_collector
        self._collector = get_collector()

    def emit(self, event: Dict[str, Any]) -> None:
        """Emit a telemetry event.

        Maps the runtime's generic event dict onto the collector's typed
        recorders. Best-effort: unknown event types are silently dropped so a
        broken telemetry backend never blocks the runtime loop.
        """
        event_type = event.get("event_type", "unknown")
        mission_id = event.get("mission_id")
        try:
            if event_type == "task_completed":
                self._collector.command_executed(
                    command_name=event.get("command", "task"),
                    duration_ms=int(event.get("metric", 0) * 1000),
                    exit_code=0,
                    mission_id=mission_id,
                )
            elif event_type == "run_completed":
                if event.get("error"):
                    self._collector.error_occurred(
                        error_type="runtime_error",
                        error_message=str(event["error"]),
                        command_name=event.get("task_id", "run"),
                        mission_id=mission_id,
                    )
            elif event_type == "session_started":
                self._collector.session_start(mission_id=mission_id)
            elif event_type == "session_ended":
                self._collector.session_end(mission_id=mission_id)
        except Exception:
            # Telemetry must never break the runtime loop.
            pass

    def flush(self) -> None:
        """Flush buffered events. No-op: collector flushes on shutdown/atexit."""
        pass