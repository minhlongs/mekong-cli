# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Telemetry collector for PEV orchestrator.

Backward-compat shim. The canonical implementation lives in
``src.core.telemetry_collector`` (which also exposes the trace-based API
``start_trace`` / ``finish_trace`` / ``record_step`` / ``record_llm_call``
/ ``record_error`` used by ``src/core/orchestrator/runner.py``).
"""

from __future__ import annotations

from src.core.telemetry_collector import (
    TelemetryCollector,
    TelemetryEvent,
    get_collector,
    track_command,
    track_error,
)

__all__ = [
    "TelemetryCollector",
    "TelemetryEvent",
    "get_collector",
    "track_command",
    "track_error",
]