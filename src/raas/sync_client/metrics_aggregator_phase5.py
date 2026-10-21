# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 5/6 telemetry summary and event list builders for RaaS Sync."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.telemetry_reporter import TelemetryReporter
    from src.raas.usage_event_schema import UsageSummary as SchemaUsageSummary


def build_phase5_summary(telemetry: "TelemetryReporter") -> "SchemaUsageSummary":
    """Build Phase 5 schema-compatible UsageSummary."""
    from src.raas.usage_event_schema import UsageSummary as SchemaUsageSummary

    metrics = telemetry.get_metrics()
    if not metrics:
        return SchemaUsageSummary()

    total_payload = sum(m.get("payload_size", 0) for m in metrics)
    timestamps = [m.get("timestamp", "") for m in metrics if m.get("timestamp")]

    first_request = None
    last_request = None
    if timestamps:
        try:
            first_request = datetime.fromisoformat(min(timestamps).replace("Z", "+00:00"))
            last_request = datetime.fromisoformat(max(timestamps).replace("Z", "+00:00"))
        except ValueError:
            pass

    hour_buckets: dict[str, int] = {}
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hour = dt.strftime("%Y-%m-%d-%H")
            hour_buckets[hour] = hour_buckets.get(hour, 0) + 1
        except ValueError:
            pass

    peak_hour = max(hour_buckets.keys(), key=lambda h: hour_buckets[h]) if hour_buckets else None

    return SchemaUsageSummary(
        total_requests=len(metrics),
        total_payload_size=total_payload,
        hours_active=len(hour_buckets),
        peak_hour=peak_hour,
        peak_requests=hour_buckets.get(peak_hour, 0) if peak_hour else 0,
        first_request=first_request,
        last_request=last_request,
    )


def build_events_list(telemetry: "TelemetryReporter") -> list[dict[str, Any]]:
    """Build usage events list from telemetry for batch sync."""
    metrics = telemetry.get_metrics()
    events = []

    for metric in metrics:
        event = {
            "event_type": "cli:command",
            "endpoint": metric.get("endpoint", "unknown"),
            "timestamp": metric.get("timestamp", ""),
            "input_tokens": metric.get("input_tokens", 0),
            "output_tokens": metric.get("output_tokens", 0),
            "duration_ms": metric.get("duration_ms", 0),
            "metadata": {
                "method": metric.get("method", "unknown"),
                "status_code": metric.get("status_code", 200),
            },
        }
        events.append(event)

    return events
