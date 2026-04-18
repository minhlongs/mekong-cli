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
| `mekongd_user_signals_total` | counter | `kind={good,bad}` | `aggregate_user_signals` (note LIKE `%#user%`) |
| `mekongd_user_feedback_ratio` | gauge | — | derived `user_good/(user_good+user_bad)`, 0 if none |

### agent-forest

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `agent_forest_queue_depth` | gauge | — | `LLEN TASK_QUEUE` (Redis) |
| `agent_forest_tasks_completed_total` | counter | — | `INCR agent_forest:tasks:completed` (worker) |
| `agent_forest_tasks_failed_total` | counter | — | `INCR agent_forest:tasks:failed` (worker) |
| `agent_forest_up` | gauge | — | liveness (constant `1`) |
| `agent_forest_workers_alive` | gauge | — | `SCAN workers:heartbeat:*` count |
| `agent_forest_worker_last_seen_timestamp` | gauge | — | max unix-ts across live heartbeats |
| `agent_forest_prompt_guard_rejections_total` | counter | `reason={injection,dangerous}` | `INCR agent_forest:prompt_guard:rejections_*` on /task reject |

Workers write `SETEX workers:heartbeat:<id> 60 <unix_ts>` each loop iteration;
stale entries auto-expire. `agent_forest_workers_alive` thus reflects workers
with a heartbeat no older than 60s.

Task counters are incremented via best-effort `INCR` in `worker/main.py::process_one`
immediately after `emit_signal`. Counter bumps are wrapped in try/except so a Redis
error never crashes the worker. No labels are used — cardinality stays bounded.

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

# Via CLI (combines signal + cost report):
agent-core report --cost --hours 168
# Cloud cost by model (last 168h):
#   claude-opus-4-7                  $    7.2000
#   claude-sonnet-4-6                $    1.8400
#   TOTAL                            $    9.0400
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

### Throughput (Giai đoạn 3.3.B)

```promql
# Jobs completed per second (5m window)
rate(agent_forest_tasks_completed_total[5m])

# Task failure rate (fraction 0..1) — alert > 0.3
rate(agent_forest_tasks_failed_total[5m])
  / (rate(agent_forest_tasks_completed_total[5m]) + rate(agent_forest_tasks_failed_total[5m]))
```

### Queue backpressure

```promql
# Current depth — alert > 50
agent_forest_queue_depth

# Growth rate (jobs/sec) — positive = producer out-running workers
deriv(agent_forest_queue_depth[5m])
```

### prompt_guard surge (Pillar 4)

```promql
# Total rejects per second — alert > 0.1 (6/min)
sum(rate(agent_forest_prompt_guard_rejections_total[5m]))

# Split by reason — injection vs dangerous-code pattern
sum by (reason) (rate(agent_forest_prompt_guard_rejections_total[5m]))
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
# Good-response ratio — single SLO number (0..1) — everything, auto + user
mekongd_signals_ratio

# Negative feedback rate (signals/min) — alert if climbing
rate(mekongd_signals_total{kind="bad"}[5m])

# Engagement: total signals captured per day
increase(mekongd_signals_total[1d])

# USER feedback only (notes carrying `#user`, forwarded by agent-forest's
# POST /task/{id}/feedback). Distinguishes "my users are unhappy" from
# "my auto pipeline is breaking" — they move independently.
mekongd_user_feedback_ratio

# Alert thresholds for user-only stream (no floor if no traffic)
mekongd_user_feedback_ratio < 0.7
  and on() (mekongd_user_signals_total{kind="good"}
          + mekongd_user_signals_total{kind="bad"}) > 20
```

## Grafana dashboard (drop-in)

A portable Grafana dashboard JSON lives at [`docs/alerting/mekong-ide-dashboard.json`](alerting/mekong-ide-dashboard.json). Panels (3 rows × ~4 panels):

| # | Panel | Expression |
|---|-------|-----------|
| 1 | Local routing ratio (gauge) | `mekongd_local_ratio` |
| 2 | Cloud spend today vs budget (stat) | `mekongd_cloud_spent_usd_today`, `mekongd_cloud_daily_budget_usd` |
| 3 | Signals ratio — all (stat) | `mekongd_signals_ratio` |
| 4 | User feedback ratio (stat) | `mekongd_user_feedback_ratio` |
| 5 | Requests/min by destination (bar gauge) | `sum by (destination)(rate(mekongd_requests_total[1m]))` |
| 6 | USD saved over time (time series) | `increase(mekongd_cost_saved_usd_total[5m])` |
| 7 | Token throughput in/out (time series) | `rate(mekongd_tokens_{in,out}_total[1m])` |
| 8 | Queue depth (time series, alert line @ 50) | `agent_forest_queue_depth` |
| 9 | Workers alive (stat) | `agent_forest_workers_alive` |
| 10 | Heartbeat staleness (stat) | `time() - agent_forest_worker_last_seen_timestamp` |
| 11 | Liveness (stat) | `agent_forest_up` |

**Import:** Grafana → Dashboards → Import → Upload JSON → select your Prometheus datasource for the `DS_PROMETHEUS` prompt. The dashboard uses `${DS_PROMETHEUS}` so it's portable across deployments.

**CLI import (Grafana API):**

```bash
jq --arg ds "$DS_UID" '
    (.panels[].datasource.uid) = $ds
    | {dashboard: (del(.__inputs, .__requires)), overwrite: true}
  ' docs/alerting/mekong-ide-dashboard.json \
| curl -sS -X POST "http://$GRAFANA_HOST/api/dashboards/db" \
    -H "Authorization: Bearer $GRAFANA_TOKEN" \
    -H "Content-Type: application/json" \
    -d @-
# DS_UID = your Prometheus datasource UID (Grafana → Datasources → Prometheus → copy UID)
```

The JSON is hand-authored (no Grafana-provisioned `id` or `version` drift), so it round-trips cleanly through git.

## Alerting rules (starter set)

Maintained as a drop-in Prometheus rules file at [`docs/alerting/mekong-ide-rules.yml`](alerting/mekong-ide-rules.yml). Add to your Prometheus config:

```yaml
rule_files:
  - /etc/prometheus/rules/mekong-ide-rules.yml
```

The starter set covers:

| Alert | Trigger | For |
|-------|---------|-----|
| `MekongdLocalRatioLow` | `mekongd_local_ratio < 0.4` | 15m |
| `MekongdSignalsRatioDegraded` | `ratio < 0.6 and increase(signals[1h]) > 10` | 30m |
| `MekongdUserFeedbackRatioDegraded` | `user_feedback_ratio < 0.7 and user_signals_total > 20` | 30m |
| `MekongdCloudSpendHigh` | `mekongd_cloud_spent_usd_today > 10` | 5m |
| `AgentForestQueueBackpressure` | `agent_forest_queue_depth > 50` | 5m |
| `AgentForestNoWorkers` | `queue > 0 and workers_alive == 0` | 2m |
| `AgentForestTaskFailureRateHigh` | `failure_rate > 0.3` (5m window) | 10m |

`MekongdSignalsRatioDegraded` guards against firing on a handful of bad signals: `increase > 10` requires meaningful volume before alerting.

Every alert carries two labels — `severity` (`critical` | `warning`) and `component` (`mekongd` | `agent-forest`) — so downstream Alertmanager routes can page by urgency without matching on alertname strings.

## Alert delivery (Alertmanager)

Routing template at [`docs/alerting/mekong-ide-alertmanager.yml`](alerting/mekong-ide-alertmanager.yml). Pairs with `mekong-ide-rules.yml` — the severity labels on each rule drive the route tree:

- `severity=critical` → Slack `#mekong-ide-oncall` (10s group_wait, 1h repeat) + optional PagerDuty
- `severity=warning` → Slack `#mekong-ide-alerts` digest (1m group_wait, 12h repeat)
- inhibit rule silences warnings for a component while a critical alert is firing on the same component (incident-mode noise reduction)

Placeholder webhook URLs in the template (`REPLACE_WITH_SLACK_WEBHOOK_URL`, `REPLACE_ME` SMTP creds) are sentinels — replace before deploy. Unrouted alerts fall through to `default-drop` so newly added rules don't accidentally page anyone until you wire a route.

## Not yet covered

- Request latency (histogram) — requires middleware + `prometheus_client` dep. Re-evaluate when SLO work begins.
- Per-user `agent_forest_queue_depth` — Redis `SCAN` expense deferred.
- Agent-core `/metrics` — no HTTP surface (library); expose via CLI-side stats file if needed.

## Unresolved

- Should `/metrics` require auth in prod (even behind loopback)? Low priority until public exposure planned.
- Dashboard JSON co-lives with the alerting rules under `docs/alerting/`; revisit if ops assets grow beyond a handful of files (candidate relocation: `docs/observability/`).
