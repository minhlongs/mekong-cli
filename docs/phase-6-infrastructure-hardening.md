# Phase 6: Infrastructure Hardening

> Deploying Plugins as Isolated Workers

**Last Updated**: 2026-06-21  
**Status**: Completed  
**Related**: [Plugin Architecture](architecture/plugin-architecture.md), [Cloudflare Deployment Guide](cloudflare-deployment-guide.md)

---

## Overview

Phase 6 hardens the infrastructure by deploying plugins as isolated workers on Cloudflare Workers, providing process-level isolation and improved fault tolerance.

### Objectives

- Deploy each plugin as separate Cloudflare Worker
- Implement plugin-to-plugin communication via HTTP
- Add circuit breakers for plugin failures
- Enable per-plugin resource quotas
- Support plugin autoscaling based on load

---

## Architecture Changes

### Before (Phase 5)

```
┌─────────────────────────────────────┐
│         Mekong Gateway              │
│  (Single Process - All Plugins)    │
└───────┬────────────┬───────────────┘
        │            │
        ▼            ▼
  ┌─────────┐ ┌─────────┐
  │ Plugin1 │ │ Plugin2 │ (in-process)
  └─────────┘ └─────────┘
```

### After (Phase 6)

```
┌─────────────────────────────────────┐
│    Mekong Gateway (Router)          │
│  - Auth - Billing - Rate Limit     │
└───────┬────────────┬───────────────┘
        │            │
        ▼            ▼
   ┌─────────┐ ┌─────────┐
   │ Worker1 │ │ Worker2 │ (separate CF Workers)
   └─────────┘ └─────────┘
        │            │
        ▼            ▼
   ┌─────────┐ ┌─────────┐
   │ D1 KV    │ │ D1 KV    │ (shared state)
   └─────────┘ └─────────┘
```

---

## Worker Deployment

### Plugin Worker Configuration

Each plugin gets its own `wrangler.toml`:

```toml
# plugins/mekong-core-founder/wrangler.toml
name = "mekong-core-founder-worker"
main = "worker.py"
compatibility_date = "2025-05-15"

[[d1_databases]]
binding = "DB"
database_name = "mekong_plugin_founder"
database_id = "xxxxx"

[[kv_namespaces]]
binding = "CACHE"
id = "xxxxx"
preview_id = "xxxxx"

[env.production]
MEKONG_PLUGIN_ID = "mekong-core-founder"
MEKONG_GATEWAY_URL = "https://api.mekongmind.com"
MEKONG_PLUGIN_SECRET = "env:PLUGIN_SECRET"

[vars]
LOG_LEVEL = "INFO"
MAX_CONCURRENT = 10
TIMEOUT_MS = 30000
```

Generated automatically:
```bash
mekong admin worker generate mekong-core-founder
```

### Worker Implementation

Plugin workers expose a standardized HTTP interface:

```python
# worker.py
from mekong_plugin_sdk.worker import PluginWorker

worker = PluginWorker(
    plugin_id="mekong-core-founder",
    handlers_module=".handlers"
)

# Handle command execution
@worker.on_command("annual")
async def handle_annual(ctx, payload):
    return await handlers.annual_report(ctx, payload)

# Handle health checks
@worker.on_health
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Exported for Cloudflare Workers
export default worker.app
```

---

## Communication Protocol

### Gateway → Worker

```http
POST /v1/execute
Content-Type: application/json
Authorization: Bearer <plugin-secret>

{
  "command": "annual",
  "payload": {"year": 2025},
  "context": {
    "user_id": "opc_001_abc123",
    "session_id": "sess_xyz"
  }
}

# Response
{
  "result": {...},
  "metrics": {"duration_ms": 45},
  "warnings": []
}
```

### Worker → Gateway (Callbacks)

For async operations, workers can callback:

```python
# Long-running task - callback when done
async def handle_long_task(ctx, payload):
    task_id = await submit_async_job(payload)
    return {"status": "accepted", "task_id": task_id}

# Gateway polls or receives webhook when complete
```

---

## Security Hardening

### Plugin Secrets

Each plugin worker gets a unique secret:

```bash
# Generate secret for plugin
mekong admin worker secret generate mekong-core-founder

# Stored in Cloudflare KV (encrypted)
# Never exposed to other plugins
```

### Network Isolation

- Workers only accept requests from gateway IPs
- Mutual TLS between gateway and workers
- Plugin-to-plugin communication requires explicit allowlist

### Resource Quotas

Per-plugin limits in `wrangler.toml`:

```toml
[limits]
cpu_ms = 30000      # Max 30s CPU per request
memory_mb = 256     # Max 256MB RAM
requests = 1000     # Max 1000 req/min
concurrent = 10     # Max 10 concurrent requests
```

Enforced by Cloudflare Workers limits + custom middleware.

---

## Observability

### Distributed Tracing

All requests get trace IDs:

```python
# Trace flows across gateway → worker → database
trace_id = ctx.request.headers.get("X-Trace-ID")
# Propagated to all downstream calls
```

View in Grafana Tempo:
- Request waterfall
- Plugin latency breakdown
- Error paths

### Metrics

Per-worker Prometheus endpoints:

```
https://mekong-core-founder-worker.mekongmind.com/metrics

# Output:
# mekong_plugin_requests_total{plugin="founder"}
# mekong_plugin_duration_seconds{plugin="founder",handler="annual"}
# mekong_plugin_errors_total{plugin="founder",type="timeout"}
```

Aggregated in gateway:

```
mekong_worker_request_duration_seconds{worker="founder"}
mekong_worker_memory_bytes{worker="founder"}
mekong_worker_concurrent_requests{worker="founder"}
```

---

## Deployment Pipeline

### CI/CD for Plugin Workers

```yaml
# .github/workflows/plugin-worker-deploy.yml
name: Deploy Plugin Worker

on:
  push:
    paths: ["plugins/mekong-core-founder/**"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          workingDirectory: plugins/mekong-core-founder
          command: deploy --production
```

### Canary Deployments

New plugin versions roll out gradually:

```bash
# Deploy to preview first
wrangler deploy --env preview

# Route 5% traffic to preview
mekong admin worker route --plugin founder --preview-weight 5

# Monitor errors, then increase
mekong admin worker route --plugin founder --preview-weight 100
```

---

## Monitoring

### Health Checks

Each worker exposes `/healthz`:

```json
{
  "status": "healthy",
  "plugin": "mekong-core-founder",
  "version": "6.1.0",
  "uptime": 3600,
  "memory_mb": 128,
  "concurrent": 3,
  "last_error": null
}
```

Gateway polls every 30s. Failed health checks trigger:
1. Mark plugin degraded
2. Stop routing new requests
3. Alert on-call
4. Attempt restart

### Alerting Rules

```yaml
# Grafana alerts
- alert: PluginWorkerDown
  expr: up{job="plugin-worker"} == 0
  for: 1m

- alert: PluginHighErrorRate
  expr: rate(mekong_plugin_errors_total[5m]) > 0.1
  for: 2m

- alert: PluginHighLatency
  expr: histogram_quantile(0.95, rate(mekong_plugin_duration_seconds_bucket[5m])) > 10
  for: 5m
```

---

## Cost Optimization

### Worker Pricing

Cloudflare Workers pricing (2026):
- 10M requests/month: $0
- 1GB-hours: $0.20
- CPU: included

Estimated cost for 50 plugin workers:
- 100M requests/month: $0
- Total: ~$50-100/month for KV/R2 storage

### Resource Right-Sizing

Monitor actual usage and adjust quotas:

```bash
# Check current usage
mekong admin worker metrics mekong-core-founder

# If consistently under 50MB memory, lower quota
wrangler secret put MAX_MEMORY_MB --value "128"
```

---

## Rollback Procedures

### Quick Rollback

```bash
# Rollback one plugin
mekong admin worker rollback mekong-core-founder --version 6.0.0

# Or via wrangler
cd plugins/mekong-core-founder
git checkout v6.0.0
wrangler deploy
```

### Full Infrastructure Rollback

```bash
# Disable worker mode, fall back to in-process
export MEKONG_WORKER_MODE=false
mekong platform restart gateway
```

Compatibility shim ensures continuity.

---

## Testing

### Integration Tests

```bash
# Test gateway → worker communication
pytest tests/workers/test_plugin_worker_integration.py

# Test worker deployment
pytest tests/workers/test_deployment.py

# Chaos testing - kill workers, verify recovery
pytest tests/workers/test_chaos.py
```

### Load Testing

```bash
# Simulate 1000 concurrent plugin invocations
k6 run --vus 1000 --duration 5m tests/load/plugin_workers.js
```

---

## Troubleshooting

### Worker Fails to Deploy

```bash
# Check wrangler config
wrangler whoami --show-account

# Validate syntax
wrangler deploy --dry-run

# Check logs
wrangler tail mekong-core-founder-worker
```

### Gateway Cannot Reach Worker

```bash
# Verify worker is deployed
curl https://mekong-core-founder-worker.mekongmind.com/healthz

# Check CORS and auth
curl -H "Authorization: Bearer <secret>" \
  https://mekong-core-founder-worker.mekongmind.com/v1/execute

# Verify gateway config
mekong admin config get worker.mekong-core-founder.url
```

---

## Next Steps

After Phase 6:

1. **Phase 7**: ZenOS Bridge — enable particle-aware execution and economic accounting

See also:
- [Cloudflare Deployment Guide](cloudflare-deployment-guide.md)
- [Plugin Health Monitoring Operations](plugin-health-monitoring-operations.md)
- [Rollback Procedures](rollback-procedures.md)
