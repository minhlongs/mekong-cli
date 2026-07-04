"""Agent observability — tracks think time, tool calls, memory hits.

Integrates with existing Prometheus/OTel stack in observability/.
"""

from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

# In-memory metrics store (replace with Prometheus client in prod)
_metrics: dict[str, list[float]] = defaultdict(list)
_counters: dict[str, int] = defaultdict(int)


def record(metric: str, value: float) -> None:
    _metrics[metric].append(value)


def increment(counter: str) -> None:
    _counters[counter] += 1


def get_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {"counters": dict(_counters)}
    for name, values in _metrics.items():
        if values:
            summary[name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "max": max(values),
                "min": min(values),
            }
    return summary


def timed(metric_name: str) -> Callable:
    """Decorator: records execution time of a function call."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                record(metric_name, time.perf_counter() - start)
                increment(f"{metric_name}.success")
                return result
            except Exception as e:
                increment(f"{metric_name}.error")
                record(f"{metric_name}.error_time", time.perf_counter() - start)
                raise
        return wrapper
    return decorator


def print_report() -> None:
    summary = get_summary()
    print("\n📊 Agent Metrics Report")
    print("=" * 40)
    for key, val in summary.get("counters", {}).items():
        print(f"  {key}: {val}")
    for key, val in summary.items():
        if key == "counters":
            continue
        avg = val.get("avg", 0)
        mx = val.get("max", 0)
        print(f"  {key}: avg={avg:.2f}s max={mx:.2f}s n={val.get('count', 0)}")
