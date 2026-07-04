"""Observability layer — traces, metrics, health checks."""

from .collector import TelemetryEvent, TelemetryCollector, get_collector, track_command, track_error
from .tracing import (
    TraceContext, SpanContext, generate_trace_id,
    start_trace, end_trace, get_current_trace_id, bind_trace_context, trace_middleware,
)
from .metrics import record, increment, get_summary, timed, print_report
from .health import (
    HealthMetrics, HealthReport, HealthReporter,
    get_health_reporter, record_command, report_health,
)

__all__ = [
    "TelemetryEvent", "TelemetryCollector", "get_collector", "track_command", "track_error",
    "TraceContext", "SpanContext", "generate_trace_id",
    "start_trace", "end_trace", "get_current_trace_id", "bind_trace_context", "trace_middleware",
    "record", "increment", "get_summary", "timed", "print_report",
    "HealthMetrics", "HealthReport", "HealthReporter",
    "get_health_reporter", "record_command", "report_health",
]
