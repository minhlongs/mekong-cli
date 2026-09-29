---
name: telemetry
description: >-
  📊 Autonomous Telemetry Mesh, Prometheus Exporter & Distributed Tracing.
---

# /telemetry — Autonomous Telemetry Mesh & Prometheus Exporter

Provides W3C traceparent propagation, span hierarchy tracking, standard Prometheus
exposition formatting (`# HELP`, `# TYPE`, counters, gauges, histogram buckets),
and SQLite persistence in `.mekong/telemetry.db` without external dependencies.

## Usage

```bash
# Export or inspect standard Prometheus exposition metrics
mekong telemetry metrics

# Output metrics in machine-readable JSON format
mekong telemetry metrics --format json

# View distributed tracing spans and W3C traceparent headers
mekong telemetry traces

# Filter spans by W3C 32-hex trace ID
mekong telemetry traces --trace-id <32-hex-trace-id>

# Output machine-readable JSON trace spans
mekong telemetry traces --json

# Export metrics and traces into static artifacts (metrics.prom, traces.json)
mekong telemetry export --output-dir dist/telemetry
```

## Features

1. **W3C Distributed Tracing**:
   - Generates and parses standard W3C `traceparent` headers (`00-{trace_id}-{span_id}-01`).
   - Tracks nested parent/child span hierarchy with duration timing and status tagging.
2. **Prometheus Exposition Formatting**:
   - Zero-dependency `# HELP`, `# TYPE`, counter, gauge, and histogram exposition text generation.
   - Ready for native Prometheus scrapers or OpenTelemetry collectors.
3. **Dual Persistence Buffer**:
   - In-memory ring buffer (up to 5,000 spans) for ultra-low latency real-time queries.
   - Durable SQLite fallback storage in `.mekong/telemetry.db`.

## Commands

- `mekong telemetry metrics`: Inspect Prometheus exposition text or JSON metrics.
- `mekong telemetry traces`: Query execution spans, status, latency, and W3C traceparents.
- `mekong telemetry export`: Export static `metrics.prom` and `traces.json` bundles.
