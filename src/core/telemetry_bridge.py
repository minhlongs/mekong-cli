# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Telemetry Mesh, Prometheus Exporter & Distributed Tracing.

Provides W3C traceparent propagation, span hierarchy tracking, standard Prometheus
exposition formatting (# HELP, # TYPE, counters, gauges, histogram buckets),
and SQLite persistence in .mekong/telemetry.db without external dependencies.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy telemetry libraries (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default database location in .mekong/telemetry.db
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / ".mekong" / "telemetry.db"

# Standard Prometheus histogram buckets in seconds
DEFAULT_HISTOGRAM_BUCKETS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS telemetry_spans (
    span_id         TEXT    NOT NULL PRIMARY KEY,
    trace_id        TEXT    NOT NULL,
    parent_id       TEXT,
    name            TEXT    NOT NULL,
    start_time      REAL    NOT NULL,
    end_time        REAL,
    duration_ms     REAL    NOT NULL DEFAULT 0.0,
    status          TEXT    NOT NULL DEFAULT 'unset',
    attributes_json TEXT    NOT NULL DEFAULT '{}',
    events_json     TEXT    NOT NULL DEFAULT '[]',
    created_at      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry_metric_snapshots (
    snapshot_id     TEXT    NOT NULL PRIMARY KEY,
    payload_json    TEXT    NOT NULL,
    prometheus_text TEXT    NOT NULL,
    created_at      REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_spans_trace ON telemetry_spans (trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_created ON telemetry_spans (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_created ON telemetry_metric_snapshots (created_at DESC);
"""


def _generate_hex(byte_length: int) -> str:
    """Generate cryptographically secure random hexadecimal identifier."""
    return os.urandom(byte_length).hex()


@dataclass
class Span:
    """Represents an OpenTelemetry-compatible span with W3C traceparent support."""

    span_id: str
    trace_id: str
    name: str
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "unset"  # "ok", "error", "unset"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def traceparent(self) -> str:
        """Format as W3C standard traceparent header: 00-{trace_id}-{span_id}-01."""
        return f"00-{self.trace_id}-{self.span_id}-01"

    def end(self, status: str = "ok", error: Optional[str] = None) -> None:
        """Mark span as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        self.status = status
        if error:
            self.attributes["error"] = error
            self.status = "error"
            self.add_event("exception", {"message": error})

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Record an annotated timestamped event within this span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
            "traceparent": self.traceparent,
        }


def parse_traceparent(header_val: str) -> Optional[Tuple[str, str]]:
    """Parse W3C traceparent header and return (trace_id, parent_id)."""
    match = re.match(r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-[0-9a-fA-F]{2}$", header_val.strip())
    if match:
        return match.group(1).lower(), match.group(2).lower()
    return None


class TelemetryRegistry:
    """In-memory Prometheus metrics store with standard exposition generator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._gauges: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._histograms: Dict[str, Dict[Tuple[Tuple[str, str], ...], Dict[str, Any]]] = {}
        self._descriptions: Dict[str, str] = {}
        self._init_default_metrics()

    def _init_default_metrics(self) -> None:
        """Initialize built-in core operational metrics."""
        self.register_counter("mekong_missions_total", "Total autonomous agent missions executed")
        self.register_histogram("mekong_mission_duration_seconds", "Duration of agent mission executions in seconds")
        self.register_counter("mekong_consensus_votes_total", "Total multi-agent consensus ballots evaluated")
        self.register_gauge("mekong_gateway_active_streams", "Number of currently active SSE and WebSocket streaming clients")
        self.register_counter("mekong_sandbox_executions_total", "Total sandboxed shell and tool executions")
        self.register_gauge("mekong_memory_items_total", "Total items indexed across federated memory domains")

    def register_counter(self, name: str, description: str) -> None:
        with self._lock:
            self._descriptions[name] = description
            if name not in self._counters:
                self._counters[name] = {}

    def register_gauge(self, name: str, description: str) -> None:
        with self._lock:
            self._descriptions[name] = description
            if name not in self._gauges:
                self._gauges[name] = {}

    def register_histogram(self, name: str, description: str) -> None:
        with self._lock:
            self._descriptions[name] = description
            if name not in self._histograms:
                self._histograms[name] = {}

    def _hash_labels(self, labels: Optional[Dict[str, str]]) -> Tuple[Tuple[str, str], ...]:
        if not labels:
            return ()
        return tuple(sorted((k, str(v)) for k, v in labels.items()))

    def inc_counter(
        self,
        name: str,
        value_or_labels: Any = 1.0,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        actual_val = 1.0
        actual_labels = None

        if isinstance(value_or_labels, (int, float)):
            actual_val = float(value_or_labels)
            actual_labels = labels
        elif isinstance(value_or_labels, dict):
            actual_labels = value_or_labels
            if isinstance(labels, (int, float)):
                actual_val = float(labels)
        elif labels is not None and isinstance(labels, dict):
            actual_labels = labels

        if description:
            with self._lock:
                self._descriptions[name] = description

        key = self._hash_labels(actual_labels)
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
            current = self._counters[name].get(key, 0.0)
            self._counters[name][key] = current + actual_val

    def set_gauge(
        self,
        name: str,
        value_or_labels: Any = 0.0,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        help_text: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        actual_val = 0.0
        actual_labels = None

        if isinstance(value_or_labels, (int, float)):
            actual_val = float(value_or_labels)
            actual_labels = labels
        elif isinstance(value_or_labels, dict):
            actual_labels = value_or_labels
            if isinstance(labels, (int, float)):
                actual_val = float(labels)
        elif labels is not None and isinstance(labels, dict):
            actual_labels = labels

        desc = description or help_text
        if desc:
            with self._lock:
                self._descriptions[name] = desc

        key = self._hash_labels(actual_labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            self._gauges[name][key] = actual_val

    def inc_gauge(
        self,
        name: str,
        value_or_labels: Any = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        actual_val = 1.0
        actual_labels = None
        if isinstance(value_or_labels, (int, float)):
            actual_val = float(value_or_labels)
            actual_labels = labels
        elif isinstance(value_or_labels, dict):
            actual_labels = value_or_labels
            if isinstance(labels, (int, float)):
                actual_val = float(labels)

        key = self._hash_labels(actual_labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            current = self._gauges[name].get(key, 0.0)
            self._gauges[name][key] = current + actual_val

    def dec_gauge(
        self,
        name: str,
        value_or_labels: Any = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        actual_val = 1.0
        actual_labels = None
        if isinstance(value_or_labels, (int, float)):
            actual_val = float(value_or_labels)
            actual_labels = labels
        elif isinstance(value_or_labels, dict):
            actual_labels = value_or_labels
            if isinstance(labels, (int, float)):
                actual_val = float(labels)

        key = self._hash_labels(actual_labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            current = self._gauges[name].get(key, 0.0)
            self._gauges[name][key] = current - actual_val

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        buckets: Any = DEFAULT_HISTOGRAM_BUCKETS,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        actual_buckets = DEFAULT_HISTOGRAM_BUCKETS
        if isinstance(buckets, (tuple, list)) and all(isinstance(x, (int, float)) for x in buckets):
            actual_buckets = tuple(sorted(float(x) for x in buckets))
        elif isinstance(buckets, str) and not description:
            description = buckets

        if description:
            with self._lock:
                self._descriptions[name] = description

        key = self._hash_labels(labels)
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = {}
            hist = self._histograms[name].get(key)
            if not hist:
                hist = {
                    "count": 0,
                    "sum": 0.0,
                    "buckets": {b: 0 for b in actual_buckets},
                }
                self._histograms[name][key] = hist

            hist["count"] += 1
            hist["sum"] += float(value)
            for b in actual_buckets:
                if float(value) <= b:
                    hist["buckets"][b] = hist["buckets"].get(b, 0) + 1

    def to_prometheus_text(self) -> str:
        """Format metrics in standard Prometheus exposition text."""
        lines: List[str] = []

        with self._lock:
            # 1. Counters
            for name, entries in self._counters.items():
                desc = self._descriptions.get(name, "Counter metric")
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} counter")
                if not entries:
                    lines.append(f"{name} 0.0")
                for label_tuples, val in sorted(entries.items()):
                    if label_tuples:
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in label_tuples)
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")
                lines.append("")

            # 2. Gauges
            for name, entries in self._gauges.items():
                desc = self._descriptions.get(name, "Gauge metric")
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} gauge")
                if not entries:
                    lines.append(f"{name} 0.0")
                for label_tuples, val in sorted(entries.items()):
                    if label_tuples:
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in label_tuples)
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")
                lines.append("")

            # 3. Histograms
            for name, entries in self._histograms.items():
                desc = self._descriptions.get(name, "Histogram metric")
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} histogram")
                for label_tuples, hist in sorted(entries.items()):
                    lbl_base = dict(label_tuples)
                    # Bucket lines
                    for le_bound, count in sorted(hist["buckets"].items(), key=lambda x: x[0]):
                        lbl_with_le = dict(lbl_base)
                        lbl_with_le["le"] = str(le_bound)
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_with_le.items()))
                        lines.append(f"{name}_bucket{{{lbl_str}}} {count}")

                    # +Inf bucket
                    lbl_inf = dict(lbl_base)
                    lbl_inf["le"] = "+Inf"
                    lbl_inf_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_inf.items()))
                    lines.append(f"{name}_bucket{{{lbl_inf_str}}} {hist['count']}")

                    # Sum and Count
                    lbl_sum_str = ",".join(f'{k}="{v}"' for k, v in sorted(lbl_base.items()))
                    if lbl_sum_str:
                        lines.append(f"{name}_sum{{{lbl_sum_str}}} {hist['sum']:.4f}")
                        lines.append(f"{name}_count{{{lbl_sum_str}}} {hist['count']}")
                    else:
                        lines.append(f"{name}_sum {hist['sum']:.4f}")
                        lines.append(f"{name}_count {hist['count']}")
                lines.append("")

        return "\n".join(lines).strip() + "\n"

    def to_dict(self) -> Dict[str, Any]:
        """Convert all metrics to structured dictionary."""
        with self._lock:
            return {
                "counters": {
                    name: [{
                        "labels": dict(lbls),
                        "value": val,
                    } for lbls, val in entries.items()]
                    for name, entries in self._counters.items()
                },
                "gauges": {
                    name: [{
                        "labels": dict(lbls),
                        "value": val,
                    } for lbls, val in entries.items()]
                    for name, entries in self._gauges.items()
                },
                "histograms": {
                    name: [{
                        "labels": dict(lbls),
                        "count": hist["count"],
                        "sum": hist["sum"],
                    } for lbls, hist in entries.items()]
                    for name, entries in self._histograms.items()
                },
            }


class TelemetryBridge:
    """Coordinates distributed tracing, span ring-buffering, and Prometheus metrics."""

    def __init__(self, db_path: Optional[Path] = None, max_spans: int = 5000) -> None:
        raw_env = os.environ.get("MEKONG_TELEMETRY_DB_PATH")
        if db_path:
            self.db_path = Path(db_path).resolve()
        elif raw_env:
            self.db_path = Path(raw_env).resolve()
        else:
            self.db_path = _DEFAULT_DB.resolve()

        self.max_spans = max_spans
        self.metrics = TelemetryRegistry()
        self._spans_buffer: List[Span] = []
        self._active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database parent directories and initialize tables."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.executescript(_SCHEMA_SQL)
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error initializing telemetry database: {exc}")

    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        traceparent: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new execution span, inheriting or generating trace identifiers."""
        t_id = trace_id
        p_id = parent_id

        if traceparent:
            parsed = parse_traceparent(traceparent)
            if parsed:
                t_id, p_id = parsed

        if not t_id:
            t_id = _generate_hex(16)  # 32 hex chars
        s_id = _generate_hex(8)  # 16 hex chars

        span = Span(
            span_id=s_id,
            trace_id=t_id,
            parent_id=p_id,
            name=name,
            attributes=attributes or {},
        )

        with self._lock:
            self._active_spans[s_id] = span

        return span

    def end_span(
        self,
        span: Span,
        status: str = "ok",
        error: Optional[str] = None,
    ) -> Span:
        """Finalize a span, append to ring buffer, and record in SQLite."""
        span.end(status=status, error=error)

        with self._lock:
            self._active_spans.pop(span.span_id, None)
            self._spans_buffer.append(span)
            if len(self._spans_buffer) > self.max_spans:
                self._spans_buffer = self._spans_buffer[-self.max_spans:]

        self._save_span(span)
        return span

    def _save_span(self, span: Span) -> None:
        """Persist finalized span into SQLite."""
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO telemetry_spans
                    (span_id, trace_id, parent_id, name, start_time, end_time, duration_ms, status, attributes_json, events_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        span.span_id,
                        span.trace_id,
                        span.parent_id,
                        span.name,
                        span.start_time,
                        span.end_time,
                        span.duration_ms,
                        span.status,
                        json.dumps(span.attributes),
                        json.dumps(span.events),
                        time.time(),
                    ),
                )
                conn.commit()
        except Exception as exc:
            logger.debug(f"Error persisting span {span.span_id}: {exc}")

    def query_spans(
        self,
        trace_id: Optional[str] = None,
        limit: int = 50,
        from_db: bool = False,
    ) -> List[Span]:
        """Fetch spans from in-memory buffer or SQLite ledger."""
        with self._lock:
            if not from_db:
                if trace_id:
                    matched = [s for s in self._spans_buffer if s.trace_id.lower() == trace_id.lower()]
                    if len(matched) >= limit:
                        return matched[:limit]
                elif len(self._spans_buffer) >= limit:
                    return list(reversed(self._spans_buffer))[:limit]

        # Query SQLite if not enough in memory or explicitly requested
        results: List[Span] = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                if trace_id:
                    cur = conn.execute(
                        "SELECT span_id, trace_id, parent_id, name, start_time, end_time, duration_ms, status, attributes_json, events_json FROM telemetry_spans WHERE trace_id = ? ORDER BY start_time ASC LIMIT ?",
                        (trace_id.lower(), limit),
                    )
                else:
                    cur = conn.execute(
                        "SELECT span_id, trace_id, parent_id, name, start_time, end_time, duration_ms, status, attributes_json, events_json FROM telemetry_spans ORDER BY created_at DESC LIMIT ?",
                        (limit,),
                    )
                for row in cur.fetchall():
                    s_id, t_id, p_id, name, st, et, dur, status, attr_raw, ev_raw = row
                    results.append(Span(
                        span_id=s_id,
                        trace_id=t_id,
                        parent_id=p_id,
                        name=name,
                        start_time=st,
                        end_time=et,
                        duration_ms=dur,
                        status=status,
                        attributes=json.loads(attr_raw) if attr_raw else {},
                        events=json.loads(ev_raw) if ev_raw else [],
                    ))
        except Exception as exc:
            logger.warning(f"Error querying spans from database: {exc}")

        if results:
            return results

        with self._lock:
            if trace_id:
                return [s for s in self._spans_buffer if s.trace_id.lower() == trace_id.lower()][:limit]
            return list(reversed(self._spans_buffer))[:limit]


# Global singleton instance
_GLOBAL_TELEMETRY_BRIDGE: Optional[TelemetryBridge] = None
_GLOBAL_TELEMETRY_LOCK = threading.Lock()


def get_telemetry_bridge() -> TelemetryBridge:
    """Get or initialize singleton TelemetryBridge."""
    global _GLOBAL_TELEMETRY_BRIDGE
    with _GLOBAL_TELEMETRY_LOCK:
        if _GLOBAL_TELEMETRY_BRIDGE is None:
            _GLOBAL_TELEMETRY_BRIDGE = TelemetryBridge()
        return _GLOBAL_TELEMETRY_BRIDGE
