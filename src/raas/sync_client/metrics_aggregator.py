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

from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

from .metrics_aggregator_phase5 import build_events_list, build_phase5_summary
from .models import UsageSummary

if TYPE_CHECKING:
    from src.core.telemetry_reporter import TelemetryReporter

logger = logging.getLogger(__name__)


def build_usage_summary(telemetry: "TelemetryReporter") -> UsageSummary:
    """Aggregate raw telemetry metrics into a UsageSummary."""
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
    """Aggregate telemetry into hourly bucket dicts for RaaS Gateway."""
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


__all__ = [
    "build_usage_summary",
    "build_hourly_buckets",
    "build_phase5_summary",
    "build_events_list",
]
