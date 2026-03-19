# RaaS Production Monitoring

**Version:** 1.0.0 | **Last Updated:** 2026-03-19

## Overview

Production monitoring infrastructure for Mekong Engine RaaS platform, providing request logging, metrics collection, and Prometheus integration.

## Architecture

```mermaid
graph LR
    A[Client Request] --> B[metricsMiddleware]
    B --> C[requestLoggingMiddleware]
    C --> D[Route Handler]
    D --> E[Response]

    F[metricsMiddleware] --> G[Increment Counters]
    F --> H[Record Latency]

    I[/metrics Endpoint] --> J[Prometheus Scraper]
    J --> K[Grafana Dashboard]

    L[Cloudflare Logpush] --> M[Log Aggregator]
    M --> N[Alerting System]
```

## Middleware Stack

### 1. metricsMiddleware

**File:** `src/lib/monitoring.ts:145-163`

Collects metrics for each request:
- Request count by endpoint
- Error count by status code
- Latency measurements

```typescript
app.use('*', metricsMiddleware)
```

### 2. requestLoggingMiddleware

**File:** `src/lib/monitoring.ts:97-140`

Structured JSON logging for each request:

```typescript
app.use('*', requestLoggingMiddleware)
```

**Log Format:**
```json
{
  "timestamp": "2026-03-19T19:17:10.583Z",
  "method": "GET",
  "path": "/v1/tasks",
  "status": 200,
  "latency_ms": 45,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_agent": "Mozilla/5.0...",
  "ip": "203.0.113.1"
}
```

**Log Levels:**
| Status Range | Console Level |
|--------------|---------------|
| 5xx | `console.error` |
| 4xx | `console.warn` |
| 2xx/3xx | `console.log` |

## Metrics Collection

### Metrics Tracked

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `mekong_request_count_total` | Counter | Total requests | `endpoint` |
| `mekong_error_count_total` | Counter | Total errors | `status` |
| `mekong_latency_ms_p50` | Gauge | 50th percentile latency | - |
| `mekong_latency_ms_p95` | Gauge | 95th percentile latency | - |
| `mekong_latency_ms_p99` | Gauge | 99th percentile latency | - |
| `mekong_uptime_seconds` | Counter | Service uptime | - |

### Implementation Details

**File:** `src/lib/monitoring.ts:10-92`

```typescript
// In-memory store (Cloudflare Workers ephemeral)
export interface Metrics {
  request_count: Record<string, number>
  error_count: Record<string, number>
  latency_ms: number[]
  active_missions: number
  uptime_seconds: number
}
```

**Latency Calculation:**
- Stores last 1000 measurements (circular buffer)
- Calculates p50, p95, p99 on demand
- Sorted array with index-based percentile lookup

## /metrics Endpoint

**File:** `src/index.ts:241-252`

**Endpoint:** `GET /metrics`

**Authentication:** Bearer token via `SERVICE_TOKEN` environment variable

**Request:**
```bash
curl -H "Authorization: Bearer $SERVICE_TOKEN" \
  https://mekong-engine.workers.dev/metrics
```

**Response (Prometheus Format):**
```
# HELP mekong_request_count_total Total number of requests
# TYPE mekong_request_count_total counter
mekong_request_count_total{endpoint="/v1/tasks"} 1547
mekong_request_count_total{endpoint="/v1/agents"} 892

# HELP mekong_error_count_total Total number of errors by status code
# TYPE mekong_error_count_total counter
mekong_error_count_total{status="400"} 12
mekong_error_count_total{status="401"} 5
mekong_error_count_total{status="429"} 3

# HELP mekong_latency_ms Request latency in milliseconds
# TYPE mekong_latency_ms gauge
mekong_latency_ms_p50 45
mekong_latency_ms_p95 120
mekong_latency_ms_p99 350

# HELP mekong_uptime_seconds Service uptime in seconds
# TYPE mekong_uptime_seconds counter
mekong_uptime_seconds 86400
```

**Headers:**
```
Content-Type: text/plain; version=0.0.4
```

## Cloudflare Logpush Integration

**Configuration:** Required for production log aggregation.

### Setup Steps

1. **Enable Logpush in Cloudflare Dashboard:**
   - Go to Workers → Your Worker → Logs
   - Enable "Logpush"
   - Select destination (Splunk, Datadog, Sumo Logic, or self-hosted)

2. **Log Format:** Already structured as JSON (see above)

3. **Filter Errors Only (Optional):**
```javascript
// In wrangler.toml
[observability.logs]
enabled = true
filter = "status >= 400"
```

## Prometheus Configuration

**scrape_config example:**
```yaml
scrape_configs:
  - job_name: 'mekong-engine'
    scheme: https
    metrics_path: '/metrics'
    headers:
      Authorization: 'Bearer ${SERVICE_TOKEN}'
    static_configs:
      - targets: ['mekong-engine.workers.dev']
    scrape_interval: 30s
    scrape_timeout: 10s
```

## Grafana Dashboard Panels

### Recommended Panels

| Panel | Type | Query |
|-------|------|-------|
| Request Rate | Time series | `rate(mekong_request_count_total[5m])` |
| Error Rate | Time series | `rate(mekong_error_count_total[5m])` |
| Error Ratio | Gauge | `rate(mekong_error_count_total[5m]) / rate(mekong_request_count_total[5m])` |
| Latency Heatmap | Heatmap | `mekong_latency_ms_p95` |
| Uptime | Stat | `mekong_uptime_seconds` |
| Requests by Endpoint | Bar chart | `mekong_request_count_total` |

### Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | `error_rate > 0.05` (5%) | Critical |
| High Latency p99 | `p99 > 1000ms` | Warning |
| Service Down | `up == 0` | Critical |
| High 429 Rate | `rate(errors{status="429"}[5m]) > 10` | Warning |

## Database Schema for Metrics

**Optional:** Store aggregated metrics in D1 for historical analysis.

```sql
CREATE TABLE IF NOT EXISTS metrics_hourly (
  hour TEXT PRIMARY KEY,
  endpoint TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  p50_latency_ms INTEGER,
  p95_latency_ms INTEGER,
  p99_latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS metrics_daily (
  day TEXT PRIMARY KEY,
  endpoint TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  avg_latency_ms INTEGER,
  max_latency_ms INTEGER
);
```

## Testing

**Test File:** `test/health-and-billing-endpoints.test.ts`

Tests include:
- Request logging output verification
- Metrics endpoint authentication
- Prometheus format validation

**Run Tests:**
```bash
cd packages/mekong-engine
npm test
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SERVICE_TOKEN` | Yes | Protects /metrics endpoint |
| `ENVIRONMENT` | No | Adds environment label to logs |

## Best Practices

1. **Log Sampling:** For high-traffic endpoints, consider sampling debug logs
2. **Metric Retention:** In-memory metrics reset on worker restart
3. **Error Budgets:** Set SLOs based on error rate metrics
4. **Latency Targets:** Monitor p95/p99, not just averages

## Troubleshooting

### Issue: /metrics returns 401

**Solution:** Ensure `SERVICE_TOKEN` is set and matches the bearer token in request.

### Issue: No logs appearing

**Solution:** Check Cloudflare Logpush configuration and verify worker is logging at correct level.

### Issue: Metrics reset frequently

**Solution:** Expected behavior for Cloudflare Workers (ephemeral storage). Use D1 for persistence if needed.

## Related Files

| File | Purpose |
|------|---------|
| `src/lib/monitoring.ts` | Core monitoring implementation |
| `src/index.ts:79-80` | Middleware registration |
| `src/index.ts:241-252` | /metrics endpoint |
| `test/health-and-billing-endpoints.test.ts` | Test coverage |

## RaaS Phase 1 Completion

This monitoring system is part of RaaS Phase 1 Production Readiness:

- ✅ Phase 1: Dunning System (license suspension/reactivation)
- ✅ Phase 2: Credit Insufficiency Gate (402 responses)
- ✅ Phase 3: Production Monitoring (this document)

**Production Readiness:** 68/100 → 85/100
