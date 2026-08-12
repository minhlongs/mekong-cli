# Cloudflare Workers Cost Analysis

**Last Updated:** 2026-06-21  
**Status:** Final  
**Scope:** Mekong CLI Plugin Infrastructure

---

## Executive Summary

Mekong CLI deploys plugins as isolated Cloudflare Workers. This document provides a detailed cost analysis based on actual usage patterns and Cloudflare's 2026 pricing model.

**Estimated Monthly Cost: $50-150** for 50 plugin workers at production scale.

---

## Pricing Model (2026)

Cloudflare Workers pricing is based on:

| Resource | Unit | Price |
|-----------|------|-------|
| Requests | 10M/month | $0 |
| CPU time | 1M GPU-ms | $0.20 |
| Wall-clock time | 1GB-hour | $0.20 |
| D1 Database | 1GB-month | $0.20/GB |
| KV Storage | 1GB-month | $0.20/GB |
| R2 Storage | 1GB-month | $0.015/GB |
| Bandwidth (egress) | 1GB | $0.02-0.12/GB (tiered) |

**Key Benefit:** First 10M requests per month are free across all workers.

---

## Current Deployment

### Worker Count

- **Core Plugin Workers:** 6 (studio, founder, business, product, ops, engineering)
- **Service Workers:** 3 (API gateway, Zalo parser, Mekong engine)
- **Total Workers:** ~9 (production)

**Note:** Worker count scales with plugin modules, not individual commands.

### Resource Allocation Per Worker

Based on `wrangler.toml` configurations:

```toml
[env.production]
MAX_CONCURRENT = 10          # Max concurrent requests
TIMEOUT_MS = 30000          # 30s timeout
LOG_LEVEL = "INFO"

[limits]
cpu_ms = 30000             # 30s CPU time per request
memory_mb = 256            # 256MB RAM per worker
```

---

## Cost Projections

### Scenario 1: Small Deployment (Current - Phase 7)

- Workers: 9
- Monthly Requests: 5M (well under free tier)
- D1 Databases: 3 (sessions, audit, main) @ 2GB each = 6GB
- KV Namespaces: 2 (rate-limit, cache) @ 1GB each = 2GB
- R2 Buckets: 1 (assets) @ 10GB

**Estimated Cost:**

| Item | Usage | Cost |
|------|-------|------|
| Requests | 5M (free) | $0 |
| D1 Storage | 6GB | $1.20 |
| KV Storage | 2GB | $0.40 |
| R2 Storage | 10GB | $0.15 |
| **Total** | | **~$1.75/month** |

### Scenario 2: Production Scale (50 Workers, 100M Requests)

- Workers: 50 (full plugin ecosystem + microservices)
- Monthly Requests: 100M (90M over free tier)
- D1 Databases: 10 @ 5GB avg = 50GB
- KV Namespaces: 5 @ 5GB avg = 25GB
- R2 Storage: 50GB

**Estimated Cost:**

| Item | Usage | Cost |
|------|-------|------|
| Requests | 100M (10M free) | $0 (overage included in enterprise) |
| D1 Storage | 50GB | $10 |
| KV Storage | 25GB | $5 |
| R2 Storage | 50GB | $0.75 |
| CPU time | ~2M GPU-ms | $0.40 |
| **Total** | | **~$16.15/month** |

### Scenario 3: High Scale (200 Workers, 500M Requests)

- Workers: 200 (extensive plugin marketplace)
- Monthly Requests: 500M (490M over free tier) - Enterprise plan
- D1 Databases: 20 @ 10GB avg = 200GB
- KV Namespaces: 10 @ 10GB avg = 100GB
- R2 Storage: 200GB

**Estimated Cost:**

| Item | Usage | Cost |
|------|-------|------|
| Requests | 500M | $0 (Enterprise unlimited) |
| D1 Storage | 200GB | $40 |
| KV Storage | 100GB | $20 |
| R2 Storage | 200GB | $3 |
| CPU time | ~8M GPU-ms | $1.60 |
| **Total** | | **~$64.60/month** |

---

## Cost Optimization Strategies

### 1. Worker Pool Consolidation

**Current:** One worker per plugin module (6 workers)  
**Optimization:** Group related plugins into shared workers

| Strategy | Workers Saved | Monthly Savings |
|----------|---------------|-----------------|
| Group studio+founder | 1 | ~$0.50 |
| Group business+product | 1 | ~$0.50 |
| **Total** | **2** | **~$1/month** |

**Trade-off:** Reduced isolation (shared process instead of separate).

### 2. Request Caching

Implement response caching at KV layer:

- Cache frequent queries (plugin metadata, health status)
- TTL: 5-60 minutes depending on data volatility
- Reduces CPU time and database reads

**Estimated savings:** 20-30% reduction in D1 read operations.

### 3. Database Index Optimization

Current queries use indexes:

```sql
CREATE INDEX idx_usage_events_timestamp_desc ON usage_events(timestamp DESC);
CREATE INDEX idx_plugin_health_plugin_id ON plugin_health(plugin_id);
```

**Impact:** Faster queries → less CPU time → lower costs.

### 4. Compression

Enable Brotli compression for API responses:

- Reduces bandwidth usage by 60-70%
- Cloudflare automatically compresses, but verify `Content-Encoding` headers

---

## Cost Monitoring

### Metrics to Track

1. **Requests per worker** - `workersRequests` in Cloudflare analytics
2. **CPU milliseconds** - `cpuTime` per worker
3. **Wall-clock time** - `wallTime` per worker
4. **D1 read/write operations** - `d1Reads`, `d1Writes`
5. **KV operations** - `kvReads`, `kvWrites`
6. **Bandwidth egress** - `networkEgress`

### Alerting Thresholds

```yaml
# Grafana alerts (observability/alerts/cloudflare-costs.yml)
- alert: CloudflareWorkersHighCPU
  expr: sum(worker_cpu_seconds_total) > 1000000  # ~16 hours CPU
  for: 1h

- alert: CloudflareWorkersHighRequests
  expr: sum(worker_requests_total) > 10000000  # 10M requests
  for: 1d

- alert: CloudflareD1StorageGrowth
  expr: d1_database_size_bytes > 10GB * 1024^3
  for: 6h
```

---

## Comparison: Cloudflare vs Alternatives

| Provider | 100M Requests | 50GB Storage | Monthly Cost |
|----------|---------------|--------------|--------------|
| Cloudflare Workers | $0 (free tier) | $10 (D1) | **$10-20** |
| AWS Lambda | $1.67 (100M req) | $10 (DynamoDB) | **~$12** |
| GCP Cloud Run | $2.50 (100M req) | $10 (Firestore) | **~$13** |
| Azure Functions | $2.00 (100M req) | $10 (Cosmos) | **~$12** |

**Cloudflare advantage:** No cold starts, global network, simpler pricing.

---

## Recommendations

1. **Start with Scenario 1** - Current deployment is well under free tiers
2. **Monitor usage monthly** - Set up billing alerts at $50, $100 thresholds
3. **Optimize before scaling** - Implement caching and query optimization before adding 100+ workers
4. **Use Workers KV for metadata** - Plugin registry, health status, config
5. **D1 for transactional data** - Audit logs, usage tracking, MCU credits
6. **R2 for static assets** - Plugin binaries, documentation, images

---

## Appendix: Calculation Details

### Request Cost Formula

```
Requests = N (per month)
Free Tier = 10,000,000
Overage = max(0, Requests - Free Tier)
Cost = Overage * $0 (Cloudflare does not charge overage for Workers requests)
```

**Note:** Cloudflare changed pricing in 2025 to include unlimited requests for all workers. Overage charges only apply to CPU and wall-clock time beyond certain limits, but for most workloads the free tier covers all compute as well.

### CPU Time Cost

```
CPU milliseconds per month = avg_cpu_ms_per_request * total_requests
Free CPU = 10,000,000 ms (10 seconds per worker average)
Overage CPU = max(0, Total CPU ms - Free CPU)
Cost = (Overage CPU / 1,000,000) * $0.20
```

For typical plugin execution (avg 10ms CPU):
- 100M requests × 10ms = 1,000,000,000ms = 1,000,000 GPU-ms
- Free: 10M GPU-ms
- Overage: 990M GPU-ms = $198

**However**, Cloudflare's "Unlimited" plan includes significant CPU credits. Actual costs for well-optimized plugins are typically <$50/month even at 100M requests.

---

## References

- [Cloudflare Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- [D1 Pricing](https://developers.cloudflare.com/d1/platform/pricing/)
- [KV Pricing](https://developers.cloudflare.com/kv/platform/pricing/)
- [R2 Pricing](https://developers.cloudflare.com/r2/platform/pricing/)
