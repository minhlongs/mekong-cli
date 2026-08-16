# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps TelemetryCollector to satisfy ObservabilitySink Protocol."""

from __future__ import annotations

from typing import Any, Dict


class TelemetrySinkAdapter:
    """Thin adapter mapping ObservabilitySink Protocol to TelemetryCollector.

    Protocol → Implementation:
    - emit(event)  → collect_event(event_type, data, metadata)
    - flush()      → no-op (collector flushes on shutdown/atexit)
    """

    def __init__(self) -> None:
        from src.core.telemetry_collector import get_collector
        self._collector = get_collector()

    def emit(self, event: Dict[str, Any]) -> None:
        """Emit a telemetry event."""
        event_type = event.get("event_type", "unknown")
        payload = event.get("payload", {})
        metadata = {k: v for k, v in event.items()
                    if k not in ("event_type", "timestamp", "payload", "consent")}
        self._collector.collect_event(
            event_type=event_type,
            data=payload,
            metadata=metadata,
        )

    def flush(self) -> None:
        """Flush buffered events. No-op: collector flushes on shutdown/atexit."""
        pass