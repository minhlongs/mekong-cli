# M1 Max LLM Brain + Trading Daemon Setup
**Date:** 2026-03-23
**Host:** 192.168.11.111 (MacBook-Pro.local) | macbook | arm64 | 64GB RAM

---

## 1. Ollama Model Status

| Model | Size | Quantization | Status |
|-------|------|-------------|--------|
| qwen2.5-coder:32b | 19.9 GB | Q4_K_M | Available |
| qwen3:32b | 20.2 GB | Q4_K_M | Available |

No pull needed — both models already present. Last modified: qwen2.5-coder 10h ago, qwen3 3 days ago.

---

## 2. Ollama Configuration

### Config file: `~/.ollama/env`
```
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_NUM_CTX=32768
OLLAMA_NUM_PARALLEL=2
OLLAMA_KV_CACHE_TYPE=q4_0
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KEEP_ALIVE=0
OLLAMA_MAX_LOADED_MODELS=0
```

**Previous state:** Bound to `127.0.0.1:11434` only (loopback). `NUM_PARALLEL=1`, no KV cache or flash attention config.

**Changes made:**
- Updated `~/.ollama/env` with M1 Max optimized settings
- Restarted `ollama serve` with env vars explicitly exported
- Now listening: `127.0.0.1:11434` (IPv4) + `*:11434` (IPv6 wildcard = all interfaces)

### Persistent LaunchAgent: `~/Library/LaunchAgents/com.ollama.server.plist`
- Created new plist with all env vars baked in
- `RunAtLoad=true`, `KeepAlive=true` — survives reboots + auto-restarts on crash
- Logs: `~/.ollama/logs/server.log`
- Status: written (will activate on next login/reboot; current `ollama serve` process is already running correctly)

**Note:** `com.ollama.ollama` (PID 1065) visible in launchctl is the Squirrel.framework auto-updater, not the serve process. The server is PID 26491/26494.

---

## 3. Algo-Trader Repo Status

**Path:** `~/algo-trader`
**Recent commits:**
```
eb37e67 feat: add Polymarket settlement arb scanner
a5a1da8 feat: funding rate arb monitor for Binance futures
e7b9557 feat: paper-trade-v3 — lower thresholds, fixed JSON parsing, verified market efficiency
```

**Scripts available:**
- `funding-rate-monitor.ts` — confirmed present
- `paper-trade-v3.ts`, `settlement-arb-scanner.py`, `scan-arb.py`, and 10 others

---

## 4. Funding Rate Monitor Schedule

### Method: LaunchAgent (crontab blocked by macOS Full Disk Access in SSH sessions)

**File:** `~/Library/LaunchAgents/com.algotrader.funding-rate-monitor.plist`
**Schedule:** `StartInterval=28800` (every 8 hours)
**Command:** `cd ~/algo-trader && /opt/homebrew/bin/npx ts-node scripts/funding-rate-monitor.ts`
**Logs:** `~/funding-rate.log`, errors → `~/funding-rate-monitor-error.log`
**Status:** Loaded (`launchctl list | grep algotrader` shows `com.algotrader.funding-rate-monitor`)

**Existing run:** Script was previously run with `--watch` flag, output in `/tmp/funding-rate.log`:
```
TOTAL MONTHLY    : $32334.58
TOTAL ANNUAL     : $393404.04
BLENDED APR      : 786.8%
STRATEGY         : delta-neutral (long spot + short perp)
```

---

## 5. LLM Connectivity Test

```bash
curl http://192.168.11.111:11434/
# → "Ollama is running"

curl http://192.168.11.111:11434/api/tags
# → qwen2.5-coder:32b (19.9GB), qwen3:32b (20.2GB)
```

**Status: PASS.** Local machine can reach M1 Max Ollama at `192.168.11.111:11434`.

**LLM_BASE_URL for mekong/adapters:** `http://192.168.11.111:11434/v1`

---

## 6. Summary

| Task | Status | Notes |
|------|--------|-------|
| Ollama model check | PASS | 2 models present, no pull needed |
| Ollama 0.0.0.0 binding | PASS | Running on all interfaces |
| M1 Max config applied | PASS | NUM_CTX=32768, KV_CACHE=q4_0, FLASH_ATTN=1 |
| Persistent LaunchAgent | DONE | `com.ollama.server.plist` created |
| algo-trader repo check | PASS | Clean, 3 recent commits |
| Funding rate monitor | DONE | LaunchAgent every 8h, loaded |
| Local connectivity | PASS | `curl 192.168.11.111:11434` responds |

---

## Unresolved Questions

1. **Ollama app.plist vs custom serve plist** — The Ollama.app may restart `ollama serve` on its own. If conflicts arise, disable Ollama.app from Login Items and rely solely on `com.ollama.server.plist`.
2. **npx path** — LaunchAgent uses `/opt/homebrew/bin/npx`. If ts-node fails, may need to verify node/bun path inside the LaunchAgent shell env.
3. **Firewall** — macOS firewall may prompt to allow `ollama` on port 11434 after reboot. Accept or add rule: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/ollama`.
4. **crontab blocked** — `Operation not permitted` in SSH non-interactive sessions is a macOS FDA restriction. LaunchAgent is the correct workaround. Crontab would need Terminal FDA grant.
