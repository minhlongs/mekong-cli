# Analytics + Monitoring Dashboard - Plan

**Phase:** 3 Week 10 | **Priority:** High | **Status:** Completed

## Overview

Build analytics and monitoring dashboard cho RaaS Gateway với error tracking, performance monitoring, custom metrics, và alerting system.

## Requirements

1. **Error Tracking** - Structured logging with context, error counting by type/tenant
2. **Performance Monitoring** - API latency (p50, p95, p99), DB query timing
3. **Custom Metrics** - Commands executed, MCU consumed, active users, error rates
4. **Alerting** - Slack webhooks, threshold-based alerts

## Implementation Steps

- [x] Create `src/observability/metrics.ts` - Metrics collection + Prometheus export
- [x] Create `src/observability/alerts.ts` - Alert rules + Slack notifications
- [x] Update `src/lib/monitoring.ts` - Integrate new metrics (re-exports)
- [x] Update `src/index.ts` - Add observability routes (/metrics, /v1/observability/alerts)
- [x] Create tests - observability-metrics.test.ts, observability-alerts.test.ts

## Files Created/Modified

### Created:
- `src/observability/metrics.ts` - 280 lines
- `src/observability/alerts.ts` - 250 lines
- `test/observability-metrics.test.ts` - 180 lines
- `test/observability-alerts.test.ts` - 200 lines

### Modified:
- `src/lib/monitoring.ts` - Added re-exports from observability
- `src/index.ts` - Added observability routes, SLACK_WEBHOOK_URL binding

## Success Criteria

- [x] All errors tracked with context (trackError with tenant, type, context)
- [x] Real-time metrics dashboard via /metrics (Prometheus format)
- [x] Alerts fire correctly on thresholds (error_rate>1%, latency_p99>500ms)
- [x] Tests pass (108 tests total, including 29 new observability tests)

## API Endpoints

- `GET /metrics` - Prometheus metrics (SERVICE_TOKEN protected)
- `GET /v1/observability/alerts` - Alert status overview
- `POST /v1/observability/alerts/check` - Manual alert trigger (SERVICE_TOKEN protected)

## Alert Thresholds

| Alert | Threshold | Comparator | Cooldown |
|-------|-----------|------------|----------|
| error_rate_high | 1% | gt | 5 min |
| latency_p99_high | 500ms | gt | 5 min |
| mcu_balance_low | 10% | lt | 60 min |
| uptime_low | N/A | lt | 1 min |

## Metrics Tracked

- commands_executed (per command type)
- commands_by_tenant (per tenant)
- mcu_consumed_total, mcu_by_tenant
- active_sessions, active_users_24h
- error_count_by_type, error_rate
- latency_p50, latency_p95, latency_p99
- db_query_count, db_query_latency_avg
- uptime_seconds

## Dependencies

- Existing monitoring.ts middleware
- Cloudflare Workers environment
- Slack webhook integration (SLACK_WEBHOOK_URL env var)
