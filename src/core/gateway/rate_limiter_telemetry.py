# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway telemetry hub and metric aggregation."""

from __future__ import annotations

import collections
import math
import threading
import time
from typing import Any, Optional


class GatewayTelemetryHub:
    """Thread-safe telemetry tracker and health metrics collector for Mekong Gateway."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._total_requests = 0
        self._rate_limit_rejections = 0
        self._total_streams_opened = 0
        self._active_streams = 0
        self._active_subscribers = 0
        self._latencies_ms: collections.deque[float] = collections.deque(maxlen=10000)
        self._path_counts: collections.defaultdict[str, int] = collections.defaultdict(int)
        self._status_counts: collections.defaultdict[int, int] = collections.defaultdict(int)
        self._tenant_counts: collections.defaultdict[str, int] = collections.defaultdict(int)
        self._tenant_rejections: collections.defaultdict[str, int] = collections.defaultdict(int)

    def record_request(
        self,
        path: str | float = "/",
        duration_ms: float = 0.0,
        status_code: int = 200,
        tenant_id: str = "default",
        **kwargs: Any,
    ) -> None:
        """Record request duration, status code, and path."""
        with self._lock:
            if isinstance(path, (int, float)):
                actual_duration = float(path)
                actual_path = str(kwargs.get("path", "/"))
                actual_status = int(duration_ms) if duration_ms else 200
                actual_tenant = str(status_code) if isinstance(status_code, str) else str(tenant_id)
            else:
                actual_path = str(path) if path else "/"
                actual_duration = float(duration_ms)
                actual_status = int(status_code)
                actual_tenant = str(tenant_id)

            self._total_requests += 1
            self._latencies_ms.append(actual_duration)
            self._path_counts[actual_path] += 1
            self._status_counts[actual_status] += 1
            self._tenant_counts[actual_tenant] += 1
            if actual_status == 429:
                self._rate_limit_rejections += 1
                self._tenant_rejections[actual_tenant] += 1

    def record_rate_limit_rejection(self, tenant_id: str = "default") -> None:
        with self._lock:
            self._rate_limit_rejections += 1
            self._tenant_rejections[tenant_id] += 1

    def record_stream_opened(self) -> None:
        with self._lock:
            self._total_streams_opened += 1
            self._active_streams += 1

    def record_stream_closed(self) -> None:
        with self._lock:
            self._active_streams = max(0, self._active_streams - 1)

    record_stream_open = record_stream_opened
    record_stream_close = record_stream_closed

    def record_subscriber_joined(self) -> None:
        with self._lock:
            self._active_subscribers += 1

    def record_subscriber_left(self) -> None:
        with self._lock:
            self._active_subscribers = max(0, self._active_subscribers - 1)

    def set_active_subscribers(self, count: int) -> None:
        with self._lock:
            self._active_subscribers = max(0, count)

    def get_latency_percentiles(self) -> dict[str, float]:
        with self._lock:
            arr = sorted(self._latencies_ms)
        if not arr:
            return {
                "p50_ms": 0.0, "p90_ms": 0.0, "p99_ms": 0.0,
                "p50": 0.0, "p90": 0.0, "p99": 0.0,
            }
        n = len(arr)

        def _pct(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return round(arr[int(k)], 2)
            d0 = arr[int(f)] * (c - k)
            d1 = arr[int(c)] * (k - f)
            return round(d0 + d1, 2)

        p50 = _pct(0.50)
        p90 = _pct(0.90)
        p99 = _pct(0.99)
        return {
            "p50_ms": p50, "p90_ms": p90, "p99_ms": p99,
            "p50": p50, "p90": p90, "p99": p99,
        }

    def get_health(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            return {
                "status": "healthy", "uptime_seconds": round(now - self._start_time, 2),
                "version": "0.1.0", "timestamp": int(now), "active_streams": self._active_streams,
            }

    get_health_status = get_health

    def get_metrics(self) -> dict[str, Any]:
        now = time.time()
        pcts = self.get_latency_percentiles()
        with self._lock:
            return {
                "status": "healthy", "uptime_seconds": round(now - self._start_time, 2),
                "version": "0.1.0", "timestamp": int(now),
                "stream_count": self._total_streams_opened,
                "total_streams_opened": self._total_streams_opened,
                "active_streams": self._active_streams,
                "active_subscribers": self._active_subscribers,
                "total_requests": self._total_requests,
                "rate_limit_rejections": self._rate_limit_rejections,
                "latency_percentiles": pcts,
                "p50_ms": pcts["p50_ms"], "p90_ms": pcts["p90_ms"], "p99_ms": pcts["p99_ms"],
                "tier_quotas": {"free": 60, "pro": 600, "enterprise": 3000},
                "active_tenants_count": len(self._tenant_counts),
            }

    def reset(self) -> None:
        with self._lock:
            self._start_time = time.time()
            self._total_requests = self._rate_limit_rejections = self._total_streams_opened = 0
            self._active_streams = self._active_subscribers = 0
            for col in (self._latencies_ms, self._path_counts, self._status_counts, self._tenant_counts, self._tenant_rejections):
                col.clear()


_global_telemetry_hub: Optional[GatewayTelemetryHub] = None
_telemetry_hub_lock = threading.Lock()


def get_telemetry_hub() -> GatewayTelemetryHub:
    global _global_telemetry_hub
    if _global_telemetry_hub is None:
        with _telemetry_hub_lock:
            if _global_telemetry_hub is None:
                _global_telemetry_hub = GatewayTelemetryHub()
    return _global_telemetry_hub


def set_telemetry_hub(hub: GatewayTelemetryHub) -> None:
    global _global_telemetry_hub
    with _telemetry_hub_lock:
        _global_telemetry_hub = hub


__all__ = ["GatewayTelemetryHub", "get_telemetry_hub", "set_telemetry_hub"]
