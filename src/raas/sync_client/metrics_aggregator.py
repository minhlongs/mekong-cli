# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Metrics Aggregator — Telemetry data aggregation helpers for RaaS Sync

Handles:
- Hourly bucket aggregation from raw telemetry
- Phase 5 schema-compatible summary generation
- Events list construction for batch sync
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TYPE_CHECKING

from .models import UsageSummary

if TYPE_CHECKING:
    from src.core.telemetry_reporter import TelemetryReporter
    from src.raas.usage_event_schema import UsageSummary as SchemaUsageSummary

logger = logging.getLogger(__name__)


def build_usage_summary(telemetry: "TelemetryReporter") -> UsageSummary:
    """
    Aggregate raw telemetry metrics into a UsageSummary.

    Args:
        telemetry: TelemetryReporter instance

    Returns:
        UsageSummary with aggregated metrics
    """
    summary = UsageSummary()

    try:
        metrics = telemetry.get_metrics()
        if not metrics:
            return summary

        endpoint_counts: dict[str, int] = {}
        method_counts: dict[str, int] = {}
        hour_buckets: dict[str, int] = {}

        for metric in metrics:
            endpoint = metric.get("endpoint", "unknown")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

            method = metric.get("method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1

            payload = metric.get("payload_size", 0)
            summary.total_payload_size += payload

            timestamp = metric.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hour_bucket = dt.strftime("%Y-%m-%d-%H")
                    hour_buckets[hour_bucket] = hour_buckets.get(hour_bucket, 0) + 1
                except (ValueError, AttributeError):
                    pass

            summary.total_requests += 1

        if hour_buckets:
            peak_hour = max(hour_buckets.keys(), key=lambda h: hour_buckets[h])
            summary.peak_hour = peak_hour
            summary.peak_requests = hour_buckets[peak_hour]
            summary.hours_active = len(hour_buckets)

        summary.endpoints = endpoint_counts
        summary.methods = method_counts

    except Exception as e:
        logger.debug("Usage summary error: %s", e)

    return summary


def build_hourly_buckets(telemetry: "TelemetryReporter") -> list[dict[str, Any]]:
    """
    Aggregate telemetry into hourly bucket dicts for RaaS Gateway.

    Args:
        telemetry: TelemetryReporter instance

    Returns:
        List of hourly bucket metrics sorted by hour
    """
    metrics = telemetry.get_metrics()
    if not metrics:
        return []

    buckets: dict[str, dict[str, Any]] = {}

    for metric in metrics:
        timestamp = metric.get("timestamp", "")
        if not timestamp:
            continue

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hour_bucket = dt.strftime("%Y-%m-%d-%H")

            if hour_bucket not in buckets:
                buckets[hour_bucket] = {
                    "hour_bucket": hour_bucket,
                    "request_count": 0,
                    "payload_size": 0,
                    "endpoints": {},
                    "methods": {},
                }

            bucket = buckets[hour_bucket]
            bucket["request_count"] += 1
            bucket["payload_size"] += metric.get("payload_size", 0)

            endpoint = metric.get("endpoint", "unknown")
            bucket["endpoints"][endpoint] = bucket["endpoints"].get(endpoint, 0) + 1

            method = metric.get("method", "unknown")
            bucket["methods"][method] = bucket["methods"].get(method, 0) + 1

        except (ValueError, AttributeError):
            continue

    return sorted(buckets.values(), key=lambda b: b["hour_bucket"])


def build_phase5_summary(telemetry: "TelemetryReporter") -> "SchemaUsageSummary":
    """
    Build Phase 5 schema-compatible UsageSummary.

    Args:
        telemetry: TelemetryReporter instance

    Returns:
        SchemaUsageSummary with Phase 5 fields
    """
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
    """
    Build usage events list from telemetry for batch sync.

    Args:
        telemetry: TelemetryReporter instance

    Returns:
        List of event dicts ready for sync
    """
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
