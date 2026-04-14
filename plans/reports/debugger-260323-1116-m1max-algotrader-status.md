# M1 Max Remote Machine + Algo-Trader Status Report
**Date:** 2026-03-23 | **Host:** macbook@192.168.11.111

---

## Executive Summary

Machine is healthy. MLX + Ollama serving correctly. Algo-trader repo is built and contains a full paper-trading module. CTO daemon is running but cycling EMPTY (no tasks queued). Funding-rate monitor LaunchAgent is installed but NOT auto-starting (`RunAtLoad: false`, fires every 8h only when triggered). No funding-rate.log exists — monitor has never run since install.

---

## 1. Services Status

| Service | Status | Notes |
|---------|--------|-------|
| MLX server `:11435` | GREEN | `mlx-community/Qwen2.5-Coder-32B-Instruct-4bit` |
| Ollama `:11434` | GREEN | `qwen2.5-coder:32b` Q4_K_M, 32.8B, ~19.8GB |
| caffeinate | RUNNING | PID 3116 — machine won't sleep |
| CTO daemon | RUNNING | C2059+ cycles, all EMPTY (no pending tasks) |
| Funding-rate monitor | IDLE | LaunchAgent present, `RunAtLoad: false`, 8h interval |
| Daemon guardian | DISABLED | `.plist.disabled` — not loaded |

### Ollama config (via plist)
- `OLLAMA_HOST=0.0.0.0:11434` — externally accessible (NOT exposed — port blocked from host)
- `OLLAMA_NUM_CTX=32768`, `OLLAMA_NUM_PARALLEL=2`, `OLLAMA_FLASH_ATTENTION=1`
- `OLLAMA_KEEP_ALIVE=0` — model unloads immediately after request (saves RAM)
- `OLLAMA_MAX_LOADED_MODELS=0` — unlimited (contradicts keep_alive=0, effectively no cache)

---

## 2. System Resources

| Metric | Value |
|--------|-------|
| RAM total | 64GB (M1 Max) |
| RAM used | 62GB (includes compressor) |
| RAM free | ~983MB physical + 25GB in compressor |
| Swap | 88 pages swapped out (minimal — healthy) |
| CPU idle | ~78% |
| Load avg | 1.96 / 2.84 / 3.19 (slightly elevated, normal for MLX daemon) |
| Processes | 651 total, 4 running |

Memory note: 62GB "used" is normal macOS behavior — compressor holds ~25GB compressed pages. Actual memory pressure is LOW (only 88 swapouts total).

---

## 3. Algo-Trader Repo

**Path:** `~/algo-trader/` | **Version:** 0.1.0

### Build Status
- `dist/` exists and populated — built successfully
- `node_modules/` present

### Module Inventory (key dirs)
```
src/
  paper-trading/     # paper-exchange.ts, paper-portfolio.ts, paper-session.ts, index.ts
  strategies/
    cex-dex/         # funding-rate-arb.ts, grid-trading.ts, dca-bot.ts
    polymarket/
  engine/            # engine.ts, strategy-runner.ts, trade-executor.ts
  cex/               # exchange-client, order-executor, market-data
  polymarket/        # market-scanner
  ml/
```

### Paper Trading Capability
- `PaperExchange` — simulates exchange fills with 0.1–0.5% random slippage
- `PaperPortfolio` — tracks balances, P&L, equity in memory
- `PaperSession` — lifecycle wrapper with summary reports
- `paper-trade-v3.ts` — LLM-enhanced Polymarket paper trader (uses LlmRouter → MLX/Ollama)

### Strategy Inventory
| Strategy | Type | Status |
|----------|------|--------|
| `FundingRateArbStrategy` | CEX delta-neutral (spot long + perp short) | Implemented, not running |
| `GridDcaStrategy` | Grid + DCA hybrid | Implemented |
| `PolymarketArbStrategy` | Prediction market arb | Implemented |
| `paper-trade-v3.ts` | LLM-evaluated Polymarket paper trades | Script, runnable |

### Scripts Available
```
scripts/funding-rate-monitor.ts   # 8h cron, logs to ~/funding-rate.log
scripts/paper-trade-test.ts
scripts/paper-trade-v2.ts
scripts/paper-trade-v3.ts         # most advanced — LLM + Polymarket
scripts/scan-arb.py
scripts/scan-new-markets.py
scripts/settlement-arb-scanner.py
```

---

## 4. Funding-Rate Monitor Status

- **LaunchAgent:** `com.algotrader.funding-rate-monitor.plist` installed
- **RunAtLoad:** `false` — does NOT start on boot
- **Interval:** every 28800s (8 hours) — only fires if `launchctl start` was called manually
- **Log target:** `~/funding-rate.log` — DOES NOT EXIST (never ran)
- **Error log:** `~/funding-rate-monitor-error.log` — not checked (likely absent too)
- **Conclusion:** Monitor was installed but never activated. Run `launchctl start com.algotrader.funding-rate-monitor` to trigger first run.

---

## 5. CTO Daemon Status

- Running at `/Users/macbook/mekong-cli/openclaw-cto.py --no-bootstrap`
- Cycling every 20s, on cycle C2059+ as of check
- All 5 projects reporting EMPTY: `mekong-cli, algo-trader, well, sophia-factory, apex-os`
- No errors in `brain-errors.log` (0 bytes)
- `cto-daemon-stderr.log` = 449KB — daemon was active and producing output

---

## 6. Paper Trading Readiness Assessment

| Requirement | Status |
|------------|--------|
| Paper trading module | BUILT |
| LLM router (MLX/Ollama) | RUNNING |
| Polymarket scanner | PRESENT |
| Funding-rate arb strategy | PRESENT, needs CEX API keys |
| Paper-trade-v3 script | RUNNABLE (Polymarket only, no API keys needed) |
| `~/funding-rate.log` | MISSING — monitor never ran |
| Exchange API keys configured | UNKNOWN — not checked |

### To start paper trading NOW (Polymarket, no keys needed)
```bash
ssh macbook@192.168.11.111
cd ~/algo-trader
node dist/scripts/paper-trade-v3.js
# or via ts-node:
npx ts-node scripts/paper-trade-v3.ts
```

### To activate funding-rate monitor
```bash
launchctl start com.algotrader.funding-rate-monitor
# verify:
tail -f ~/funding-rate.log
```

### To run funding-rate arb (requires CEX API keys)
- Needs `EXCHANGE_API_KEY` / `EXCHANGE_SECRET` in `.env`
- Configure `FundingArbConfig` (exchange, symbols, capital, thresholds)
- Entry threshold: 0.05%/8h default; exit: 0.01%/8h

---

## Unresolved Questions

1. Are CEX exchange API keys configured in `~/algo-trader/.env`? (not read — privacy boundary)
2. Why is `OLLAMA_KEEP_ALIVE=0` set? Model unloads after each request — cold start latency per call. Intentional for RAM savings?
3. CTO daemon all-EMPTY: is this expected? No tasks queued across 5 projects — is the task source (`.mekong/tasks/`) being populated?
4. `daemon-guardian.plist.disabled` — was this intentionally disabled? Guardian would restart crashed daemon.
5. Ollama port 11434 is bound to `0.0.0.0` but unreachable externally — is a firewall blocking it, or is this intentional?
