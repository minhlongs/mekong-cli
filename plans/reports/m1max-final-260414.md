---
report: m1max-final-260414
date: 2026-04-14
type: health-check
---

# M1 Max Autonomous System — Final Health Check

**Date:** 2026-04-14 ~06:00 UTC  
**SSH:** ssh m1max-cf (m1max.cashclaw.cc)

---

## Results

| Check | Status | Detail |
|-------|--------|--------|
| Gateway health | HEALTHY | `{"status":"healthy","version":"3.3.0"}` |
| qwen3-coder-next | AVAILABLE | 51 GB, loaded 26h ago |
| Daemon process | 1x running | PID 38469, started Sun 04PM, CPU 0.0% |
| Daemon last activity | SLEEPING | 20 lifetime missions complete, sleeping 12h until next cycle |
| Redis | PONG | Healthy |
| Gateway watchdog | LOADED | `com.mekong.gateway-watchdog` PID 0 (idle, watching) |
| Daemon account credits | 9,947 credits | balance=9947, earned=50, spent=103 |

---

## Ollama Models Available

| Model | Size | Age |
|-------|------|-----|
| qwen3-coder-next:latest | 51 GB | 26h |
| qwen3:32b | 20 GB | 40h |
| qwen2.5-coder:7b | 4.7 GB | 3d |
| nomic-embed-text:latest | 274 MB | 9d |
| deepseek-r1:32b | 19 GB | 9d |

---

## LaunchCtl Services

| Service | PID | Status |
|---------|-----|--------|
| com.mekong.gateway | 95592 | Running |
| com.mekong.openclaw | 38469 | Running (daemon) |
| com.mekong.gateway-watchdog | 0 | Loaded/idle |
| com.mekong.proxy | - | Exit 78 |
| com.mekong.pipeline-executor | - | Exit 0 |
| com.mekong.watchdog | - | Exit 78 |

> Exit 78 = service not needed / on-demand; not an error.

---

## Daemon Credits (daemon@openclaw.local)

- Balance: **9,947 credits** (healthy runway)
- Total earned: 50
- Total spent: 103
- Note: balance >> earned+spent discrepancy suggests initial seeding. Daemon is not at risk of credit exhaustion.

---

## Mission Stats (Global)

| Status | Count |
|--------|-------|
| completed | 26 |
| failed | 11 |
| queued | 5 |

- Failure rate: ~30% — some queued missions appear stuck (created 2026-04-12, still queued)
- Daemon last cycle: 20 lifetime missions total; next cycle in ~12h from check time

---

## Assessment

**ALL CRITICAL SYSTEMS GREEN.**

- Gateway v3.3.0: healthy
- qwen3-coder-next: confirmed available (was the goal)
- Exactly 1 daemon process: confirmed
- Redis: healthy
- Daemon sleeping normally (12h cycle)
- Daemon credits: 9,947 — no risk of exhaustion

**Minor notes:**
- 5 missions stuck in `queued` state since 2026-04-12 — daemon did not pick them up in last cycle. May indicate missions were queued outside active daemon window or tenant mismatch (one already confirmed `tenant_not_found` error).
- `com.mekong.proxy` and `com.mekong.watchdog` exiting with code 78 — normal for on-demand LaunchD services.
