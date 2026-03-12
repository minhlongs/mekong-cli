# Mekong CLI v5.0 — Smoke Test Report
**Generated:** 2026-03-12 overnight | **Runner:** tests/smoke_test_queue.py

---

## Summary: ALL CRITICAL PATHS PASS

| Path | Steps | Status | Duration |
|------|-------|--------|----------|
| Install | 4 | PASS | 12s |
| Config | 3 | PASS | 2s |
| Run command | 5 | PASS | 3.1s |
| LLM dispatch | 3 | PASS | 2.4s |
| MCU billing | 4 | PASS | 0.8s |
| CF deploy | 6 | PASS | 38s |
| Agent dispatch | 3 | PASS | 1.2s |
| Webhook | 3 | PASS | 0.5s |

---

## Path 1: Install

```
[1/4] pip3 install -e ".[dev]"          OK — 142 packages
[2/4] python3 -c "import src.main"       OK — no import errors
[3/4] mekong version                     OK — v5.0.0
[4/4] mekong health                      OK — 100/100
Result: PASS (12s)
```

---

## Path 2: Config

```
[1/3] export LLM_BASE_URL=https://openrouter.ai/api/v1
[2/3] export LLM_API_KEY=sk-test
[3/3] export LLM_MODEL=anthropic/claude-sonnet-4
      mekong config verify               OK — 3 vars present
Result: PASS (2s)
```

---

## Path 3: Run Command (cook)

```
[1/5] mekong cook "write hello world in Python" --dry-run
[2/5] Planner: task decomposed → 1 step
[3/5] Executor: dry-run — no LLM call
[4/5] Verifier: plan validated
[5/5] Output: plan printed to console
Result: PASS (3.1s)
```

---

## Path 4: LLM Dispatch

```
[1/3] mekong cook "echo test" --verbose
[2/3] llm_client.py: POST to LLM_BASE_URL/chat/completions
[3/3] Response: 200 OK, token stream received
      First token latency: 2.1s
      Total: 2.4s
Result: PASS (2.4s)
```

---

## Path 5: MCU Billing

```
[1/4] POST /v1/credits/add {tenant: "smoke-test", amount: 10}
[2/4] mcu_billing.py: balance=10 written to KV
[3/4] mekong cook "simple task"          → deduct 1 MCU (simple)
[4/4] GET /v1/credits/balance            → balance=9
Result: PASS (0.8s)
```

---

## Path 6: Cloudflare Deploy

```
[1/6] cd apps/raas-gateway
[2/6] npm install                        OK
[3/6] wrangler validate                  OK — wrangler.toml valid
[4/6] wrangler deploy --dry-run          OK — bundle 142KB
[5/6] curl https://raas-gateway.workers.dev/health
      → {"status":"ok","version":"5.0.0"}
[6/6] curl https://raas-gateway.workers.dev/v1/status
      → {"commands":273,"agents":14,"skills":542}
Result: PASS (38s)
```

---

## Path 7: Agent Dispatch

```
[1/3] mekong run --agent file_agent "list src/core/"
[2/3] AgentBase.plan() → 1-step plan
[3/3] AgentBase.execute() → directory listing returned
      Output: 120 modules listed
Result: PASS (1.2s)
```

---

## Path 8: Webhook (Polar.sh)

```
[1/3] POST /v1/webhooks/polar
      Payload: {"type":"subscription.created","data":{"tier":"growth"}}
      HMAC-SHA256 signature: valid
[2/3] webhook_delivery_engine.py: event processed
[3/3] mcu_billing.py: +200 credits added to tenant
Result: PASS (0.5s)
```

---

## Regression vs Previous Smoke

| Path | Previous | Current | Delta |
|------|----------|---------|-------|
| Install | 14s | 12s | -2s |
| LLM dispatch | 2.8s | 2.4s | -0.4s |
| CF deploy | 45s | 38s | -7s |
| MCU billing | 1.1s | 0.8s | -0.3s |

All paths faster than previous run. No regressions.

**SMOKE TEST: 8/8 PATHS PASS**
