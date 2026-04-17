# Expected Signals — What "Healthy" Looks Like

Reference for interpreting burn-in output. Compare your actual metrics against
these baselines to decide GO / NO-GO for production claim "24/7 autonomous."

---

## Memory (RSS)

| Signal | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Baseline RSS | 150–400 MB | 400–800 MB | > 800 MB |
| Peak RSS | < 1 GB | 1–2 GB | > 2 GB |
| Drift slope | < 10 MB/hr | 10–50 MB/hr | > 50 MB/hr |
| RSS at 24h vs baseline | < 200 MB growth | 200–500 MB growth | > 500 MB growth |

A healthy daemon holds a stable RSS plateau after warm-up (~first 30 min).
A slow upward slope (< 10 MB/hr) is acceptable for a 24h run.
A steep slope signals a memory leak — investigate `state["runs"]` list growth
in `openclaw-daemon.py` or report file accumulation.

---

## CPU

| Signal | Healthy | Warning |
|--------|---------|---------|
| Idle CPU (between missions) | < 2% | > 5% |
| Active CPU (during LLM call) | 10–80% (expected) | N/A |
| Sustained > 90% for > 5 min | Never | Investigate |

CPU spikes during Ollama inference are expected and normal.
Sustained high CPU between missions = busy-loop bug.

---

## Error Rate

| Signal | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Errors per hour | 0 | < 1 | > 1 |
| `[TIMEOUT]` per cycle | 0–1 | 2–3 | > 3 |
| `[FATAL]` total | 0 | — | Any |
| `CYCLE_ERROR` total | 0–1 | 2–5 | > 5 |

One `[TIMEOUT]` per cycle is acceptable (32b model on slow query).
`[FATAL]` = cannot get API key = daemon effectively dead.

---

## Restart Count

| Signal | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Restarts in 24h | 0 | 1–3 | > 3 |

Restarts are tracked by `harness_restart` events in the JSONL log.
0 restarts = strong demo evidence for "runs unattended."

---

## Task Completion

| Signal | Healthy |
|--------|---------|
| Missions attempted per cycle | 9 (all MISSIONS list) |
| Missions skipped (24h dedup) | Expected after cycle 1 |
| `chars` per mission output | > 500 chars = substantive |
| `[SHORT]` results | < 20% of missions |

---

## Log Continuity

A healthy run log shows events in this order per cycle:
```
harness_start → daemon_start → sampler_start
  → [daemon_stdout × N] (heartbeats + mission logs)
  → [repeat every 12h]
harness_end (on graceful stop)
```

Gaps > 15 min in `daemon_stdout` events = daemon may be blocked on LLM call (normal for 32b model).
Gaps > 60 min = potential hang, investigate.

---

## GO / NO-GO Criteria (D-Day)

For the production claim "OpenClaw runs 24/7 autonomous":

| Criteria | Threshold | Source |
|----------|-----------|--------|
| Uptime | >= 23.9h (86040s) | `harness_end.uptime_s` |
| Restarts | <= 3 | `daemon_restart` event count |
| Error rate | < 1/hr | error `daemon_stdout` lines |
| Peak RSS | < 2 GB | metrics CSV `rss_mb` max |
| RSS drift | < 50 MB/hr | linear slope over CSV |
| Clean shutdown | Yes | `harness_end` event present |

**12h intermediate GO criteria** (kill-switch test checkpoint):
- Uptime >= 12h, restarts <= 2, no `[FATAL]` events.

If all 6 criteria met → update README claim with burn-in run link.
If any fail → file bug, fix, restart 24h clock.
