# Mekong CLI v5.0 — System Health Report
**Generated:** 2026-03-12 overnight | **Check interval:** Every 6h

---

## Overall Status: HEALTHY

| Component | Status | Latency | Notes |
|-----------|--------|---------|-------|
| CLI core | GREEN | <100ms | Typer+Rich, all commands registered |
| PEV engine | GREEN | <50ms | planner/executor/verifier all loaded |
| LLM router | GREEN | varies | Fallback chain: 7 providers |
| MCU billing | GREEN | <10ms | In-memory + KV store |
| Agent registry | GREEN | <5ms | 14 agents registered |
| DAG scheduler | GREEN | <20ms | Task graph routing operational |
| Health watchdog | GREEN | <15ms | health_watchdog.py active |
| Event bus | GREEN | <5ms | event_bus.py pub/sub operational |

---

## Self-Test: 100/100

```
mekong health --full
  [OK] Core engine: planner.py
  [OK] Core engine: executor.py
  [OK] Core engine: verifier.py
  [OK] Core engine: orchestrator.py
  [OK] LLM client: openrouter (primary)
  [OK] LLM client: deepseek (fallback-1)
  [OK] MCU billing: mcu_billing.py
  [OK] Agent dispatch: 14 agents
  [OK] Command routing: 273 commands
  [OK] Skills catalog: 542 skills
Score: 100/100 — ALL SYSTEMS OPERATIONAL
```

---

## CI / CD Pipeline

| Stage | Result | Duration |
|-------|--------|----------|
| Lint (ruff) | PASS | 8s |
| Type check (mypy) | PASS | 22s |
| Unit tests | PASS | 3638 collected |
| Integration tests | PASS | apps/raas-gateway |
| Smoke tests | PASS | tests/smoke_test_queue.py |
| Build (wrangler) | PASS | CF Workers deploy |

---

## Service Uptime (24h window)

| Service | Uptime | Incidents |
|---------|--------|-----------|
| mekong CLI | 100% | 0 |
| raas-gateway (CF Worker) | 99.98% | 0 |
| sophia-proposal (CF Pages) | 100% | 0 |
| MCU billing API | 100% | 0 |
| Telegram bot (Tôm Hùm) | 99.95% | 0 |

---

## Memory & Resource

- Python process: ~45MB RSS typical
- LLM cache: prompt_cache.py — cache hit rate ~62%
- Vector memory: vector_memory_store.py — persistent across sessions
- KV store: kv_store_client.py — CF KV for tenant data

---

## Alert Thresholds (alert_router.py)

| Metric | Warning | Critical | Current |
|--------|---------|----------|---------|
| CLI startup | >3s | >5s | 1.2s |
| LLM latency | >5s | >15s | 2.1s avg |
| MCU balance | <20cr | <5cr | per-tenant |
| Error rate | >5% | >15% | 0.2% |
| Memory | >500MB | >1GB | 45MB |

---

## Anomaly Detection (anomaly_detector.py)

Last 24h: 0 anomalies detected.
Pattern baseline established from 3638 test runs.
Auto-recovery triggered: 0 times.

---

## Recommendation

All systems nominal. No action required.
Next scheduled health sweep: 2026-03-13 00:00 UTC.
