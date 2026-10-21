# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PayloadBuilder for constructing and aggregating RaaS usage event payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class PayloadBuilder:
    """
    Builder for constructing usage event payloads.

    Aggregates events and builds hourly buckets for sync.
    """

    def __init__(self, tenant_id: str, license_key: str) -> None:
        self.tenant_id = tenant_id
        self.license_key = license_key
        self.events: list[Dict[str, Any]] = []

    def add_event(self, event: Dict[str, Any]) -> "PayloadBuilder":
        """Add usage event to payload."""
        event["tenant_id"] = self.tenant_id
        event["license_key"] = self.license_key
        self.events.append(event)
        return self

    def add_events(self, events: list[Dict[str, Any]]) -> "PayloadBuilder":
        """Add multiple events."""
        for event in events:
            self.add_event(event)
        return self

    def build(self) -> list[Dict[str, Any]]:
        """Build final payload."""
        return self.events

    def build_hourly_buckets(self) -> list[Dict[str, Any]]:
        """Aggregate events into hourly buckets."""
        buckets: dict[str, list[Dict[str, Any]]] = {}

        for event in self.events:
            timestamp = event.get("timestamp", "")
            if not timestamp:
                continue
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                else:
                    dt = timestamp
                hour_bucket = dt.strftime("%Y-%m-%d-%H")
                buckets.setdefault(hour_bucket, []).append(event)
            except (ValueError, AttributeError):
                continue

        result = []
        for hour_bucket, events in sorted(buckets.items()):
            total_tokens = sum(
                e.get("input_tokens", 0) + e.get("output_tokens", 0) for e in events
            )
            events_by_type: dict[str, int] = {}
            for event in events:
                event_type = event.get("event_type", "unknown")
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

            result.append(
                {
                    "hour_bucket": hour_bucket,
                    "tenant_id": self.tenant_id,
                    "event_count": len(events),
                    "total_tokens": total_tokens,
                    "events_by_type": events_by_type,
                }
            )

        return result


__all__ = ["PayloadBuilder"]
