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
| `mekongd_cloud_spent_usd_today` | gauge | — | SQLite sum (cloud, UTC today) |
| `mekongd_cloud_daily_budget_usd` | gauge | — | config `cloud_daily_budget_usd` (0 = no cap) |
| `mekongd_signals_total` | counter | `kind={good,bad}` | `aggregate_signals` |
| `mekongd_signals_ratio` | gauge | — | derived `good/(good+bad)`, 0 if none |

### agent-forest

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `agent_forest_queue_depth` | gauge | — | `LLEN TASK_QUEUE` (Redis) |
| `agent_forest_up` | gauge | — | liveness (constant `1`) |
| `agent_forest_workers_alive` | gauge | — | `SCAN workers:heartbeat:*` count |
| `agent_forest_worker_last_seen_timestamp` | gauge | — | max unix-ts across live heartbeats |

Workers write `SETEX workers:heartbeat:<id> 60 <unix_ts>` each loop iteration;
stale entries auto-expire. `agent_forest_workers_alive` thus reflects workers
with a heartbeat no older than 60s.

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

### Cloud spend guardrails

```promql
# Cloud USD spent today — alert when near budget
mekongd_cloud_spent_usd_today

# Burn rate: cloud USD/sec over last 5m
rate(mekongd_cloud_spent_usd_today[5m])

# Fraction of budget consumed (0..1) — 1.0 = cap reached; further cloud routes → HTTP 402
mekongd_cloud_spent_usd_today / mekongd_cloud_daily_budget_usd
```

**Budget enforcement:** set `MEKONGD_CLOUD_DAILY_BUDGET_USD=10` (or `cloud_daily_budget_usd` in config.toml). When today's cloud spend reaches the cap, `POST /v1/messages` with a cloud-routed decision returns HTTP 402 with a human-readable detail. Local routes are never blocked.

**Per-model cost breakdown:** for tuning decisions ("which model is eating the budget?"):

```bash
curl -s '127.0.0.1:8765/v1/cost/by-model?hours=168' | jq .
# {"by_model": {"claude-opus-4-7": 7.20, "claude-sonnet-4-6": 1.84}}
```

Only models with non-zero spend appear. Omit `hours` for all-time. Legacy rows (missing `model` column before PR #102) bucket under `""`.

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

### Worker liveness

```promql
# Workers reporting heartbeat (TTL<60s)
agent_forest_workers_alive

# Dead pool: queue has work but no worker heartbeat
agent_forest_queue_depth > 0 and agent_forest_workers_alive == 0

# Staleness in seconds (how fresh is the last heartbeat)
time() - agent_forest_worker_last_seen_timestamp
```

### Liveness

```promql
up{job=~"mekongd|agent-forest"}         # scraper-inferred
agent_forest_up                          # self-reported
```

### Per-model signal breakdown

Not a scrape target — a JSON diagnostic endpoint for operator triage when
`mekongd_signals_ratio` degrades:

```bash
curl -s 127.0.0.1:8765/v1/signals/breakdown | jq .
# {"by_model": {"qwen3-8b": {"good": 12, "bad": 3},
#               "claude-sonnet-4-6": {"good": 5, "bad": 2},
#               "": {"good": 0, "bad": 1}}}   # legacy rows (no model field)
```

Or via the bundled CLI:

```bash
agent-core report
# Model                           Good     Bad     Ratio
# ----------------------------------------------------------
# (unknown)                          0       1      0.00
# claude-sonnet-4-6                  5       2      0.71
# qwen3-8b                          12       3      0.80
# ----------------------------------------------------------
# TOTAL                             17       6      0.74

# Limit window after a policy change:
agent-core report --hours 24       # last 24h only
curl -s '127.0.0.1:8765/v1/signals/breakdown?hours=24' | jq .

# Append last N signal notes to see the "diary" of why operators marked bad/good:
agent-core report --notes 20
curl -s '127.0.0.1:8765/v1/signals/recent?limit=20' | jq .
```

Counters on `/metrics` stay unlabeled to keep Prometheus cardinality bounded.
Use the breakdown endpoint for ad-hoc slicing; export to a panel only if
the model set is small and stable.

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

      - alert: AgentForestNoWorkers
        expr: agent_forest_queue_depth > 0 and agent_forest_workers_alive == 0
        for: 2m
        annotations:
          summary: "Queue has pending jobs but zero workers heartbeating — pool is dead"

      - alert: MekongdCloudSpendHigh
        expr: mekongd_cloud_spent_usd_today > 10
        for: 5m
        annotations:
          summary: "Cloud spend today exceeds $10 — review routing policy / budget"

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
- Agent-core `/metrics` — no HTTP surface (library); expose via CLI-side stats file if needed.

## Unresolved

- Should `/metrics` require auth in prod (even behind loopback)? Low priority until public exposure planned.
- Dashboard JSON location convention: `docs/observability/` vs `packages/*/ops/` once unified dashboard lands.
