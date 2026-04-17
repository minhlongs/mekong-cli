---
description: ⚡⚡ COO Health Check — 5-pillar system health, exchange/bot/strategy/infra/data status
argument-hint: [pillar: exchange|bot|strategy|infra|data|all]
---

**Ultrathink** COO health check: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/coo-sops.md` SOP-O02

## 5-Pillar Health Check

### 1. Exchange Health
- `src/netdata/HealthManager.ts` → `getReport()`
- `src/execution/exchange-health-monitor.ts` → per-exchange status
- Check: connectivity, latency <500ms, rate usage <65%, WebSocket active

### 2. Bot Engine Health
```bash
tsc --noEmit              # 0 errors
pnpm test 2>&1 | tail -5  # all PASS
```
- `src/core/BotEngine.ts` → process status
- Check: memory <500MB, CPU <50%, no hung processes

### 3. Strategy Health
- `src/core/SignalGenerator.ts` → signal generation active?
- `src/core/autonomy-controller.ts` → current autonomy level
- Check: weights balanced, alpha not decaying, regime detection working

### 4. Infrastructure Health
- Proxy: `curl -s http://localhost:9191/health`
- Tôm Hùm: process alive check
- Disk: `df -h` → >10% free
- Network: stable connectivity

### 5. Data Health
- `src/netdata/TickStore.ts` → price feeds current?
- Order book depth: sufficient for trading?
- Reports: generating correctly?

## Output
```
╔═══════════════════════════════════════════╗
║        SYSTEM HEALTH — {date}             ║
╠═══════════════════════════════════════════╣
║ 1. Exchange       🟢/🟡/🔴  {details}   ║
║ 2. Bot Engine     🟢/🟡/🔴  {details}   ║
║ 3. Strategy       🟢/🟡/🔴  {details}   ║
║ 4. Infrastructure 🟢/🟡/🔴  {details}   ║
║ 5. Data           🟢/🟡/🔴  {details}   ║
╠═══════════════════════════════════════════╣
║ Overall: X/5 GREEN | Decision: GO/CAUTION ║
╚═══════════════════════════════════════════╝
```
