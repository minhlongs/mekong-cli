# Observability — Mekong-IDE

Bridges Pillar 2 (Observability) `/metrics` endpoints to operator consumption.
References: PR #93 (mekongd), PR #94 (agent-forest gateway).

## Endpoints

| Service | Endpoint | Default bind | Metric family |
|---------|----------|--------------|---------------|
| mekongd | `GET /metrics` | `127.0.0.1:8765` | `mekongd_*` |
| agent-forest gateway | `GET /metrics` | per `ForestSettings.host` | `agent_forest_*` |

Format: Prometheus text exposition (hand-formatted, no `prometheus_client` dep).

## Exposed metrics

### mekongd

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `mekongd_requests_total` | counter | `destination={local,cloud}` | `stats.aggregate_stats` |
| `mekongd_tokens_in_total` | counter | — | SQLite sum |
| `mekongd_tokens_out_total` | counter | — | SQLite sum |
| `mekongd_cost_saved_usd_total` | counter | — | SQLite sum |
| `mekongd_local_ratio` | gauge | — | derived (0..1) |
| `mekongd_signals_total` | counter | `kind={good,bad}` | `aggregate_signals` |
| `mekongd_signals_ratio` | gauge | — | derived `good/(good+bad)`, 0 if none |

### agent-forest

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `agent_forest_queue_depth` | gauge | — | `LLEN TASK_QUEUE` (Redis) |
| `agent_forest_up` | gauge | — | liveness (constant `1`) |

## Prometheus scrape config

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: mekongd
    scrape_interval: 15s
    static_configs:
      - targets: ['127.0.0.1:8765']

  - job_name: agent-forest
    scrape_interval: 15s
    static_configs:
      - targets: ['127.0.0.1:8000']   # adjust to your gateway bind
```

mekongd binds loopback by default — safe to scrape without auth. agent-forest gateway exposes JWT-protected task endpoints; `/metrics` currently has no auth, so bind the gateway behind loopback or a private network.

## PromQL recipes

### Cost savings

```promql
# USD saved in the last hour
increase(mekongd_cost_saved_usd_total[1h])

# Saved $ per local request (proxy for Qwen efficacy)
increase(mekongd_cost_saved_usd_total[1h])
  / increase(mekongd_requests_total{destination="local"}[1h])
```

### Routing health

```promql
# Local routing share — target > 0.6
mekongd_local_ratio

# Escape rate to cloud (requests/sec)
rate(mekongd_requests_total{destination="cloud"}[5m])
```

### Token throughput

```promql
# Input tokens/sec (all destinations)
rate(mekongd_tokens_in_total[1m])

# Output tokens/sec
rate(mekongd_tokens_out_total[1m])
```

### Queue backpressure

```promql
# Current depth — alert > 50
agent_forest_queue_depth

# Growth rate (jobs/sec) — positive = producer out-running workers
deriv(agent_forest_queue_depth[5m])
```

### Liveness

```promql
up{job=~"mekongd|agent-forest"}         # scraper-inferred
agent_forest_up                          # self-reported
```

### Operator feedback (Pillar 3)

```promql
# Good-response ratio — single SLO number (0..1)
mekongd_signals_ratio

# Negative feedback rate (signals/min) — alert if climbing
rate(mekongd_signals_total{kind="bad"}[5m])

# Engagement: total signals captured per day
increase(mekongd_signals_total[1d])
```

## Suggested Grafana panels

Panel per row, left→right:

1. **Single stat — Local routing ratio** (`mekongd_local_ratio`, threshold green≥0.6, amber≥0.4)
2. **Time series — USD saved / day** (`increase(mekongd_cost_saved_usd_total[1d])`)
3. **Time series — Queue depth** (`agent_forest_queue_depth`, alert ≥ 50)
4. **Bar gauge — Requests/min by destination** (`sum by (destination)(rate(mekongd_requests_total[1m]))`)
5. **Stat — Tokens/sec in** and **Tokens/sec out** (`rate(mekongd_tokens_in_total[1m])` / `..._out_total`)

Full JSON dashboard export deferred until local Grafana instance stood up (YAGNI — panel list above is portable). Unified dashboard slated for next session.

## Alerting rules (starter set)

```yaml
groups:
  - name: mekong-ide
    rules:
      - alert: MekongdLocalRatioLow
        expr: mekongd_local_ratio < 0.4
        for: 15m
        annotations:
          summary: "Qwen local path underutilized (<40%) — investigate cloud_patterns"

      - alert: AgentForestQueueBackpressure
        expr: agent_forest_queue_depth > 50
        for: 5m
        annotations:
          summary: "Worker queue depth >50 — scale workers or check for stuck jobs"

      - alert: MekongdSignalsRatioDegraded
        expr: mekongd_signals_ratio < 0.6 and increase(mekongd_signals_total[1h]) > 10
        for: 30m
        annotations:
          summary: "Operator satisfaction <60% with ≥10 signals/h — routing quality regression"
```

The `MekongdSignalsRatioDegraded` alert guards against the ratio firing on a handful of bad signals: `increase > 10` requires meaningful volume before alerting.

## Not yet covered

- Request latency (histogram) — requires middleware + `prometheus_client` dep. Re-evaluate when SLO work begins.
- Per-user `agent_forest_queue_depth` — Redis `SCAN` expense deferred.
- Worker heartbeat (`agent_forest_worker_last_seen_timestamp`) — needs a worker metrics surface.
- Agent-core `/metrics` — no HTTP surface (library); expose via CLI-side stats file if needed.

## Unresolved

- Should `/metrics` require auth in prod (even behind loopback)? Low priority until public exposure planned.
- Dashboard JSON location convention: `docs/observability/` vs `packages/*/ops/` once unified dashboard lands.
