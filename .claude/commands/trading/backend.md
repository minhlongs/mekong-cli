---
description: ⚡⚡⚡ Backend Engineer — core engine audit, architecture review, code quality, module ownership
argument-hint: [action: audit|architecture|quality|modules]
---

**Ultrathink** Backend engineering review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 7
**Reports to:** CTO (`/trading:cto`)

## Pipeline (4 steps)

### 1. CORE MODULE STATUS
| Module | Key Files | LOC | Tests | Status |
|--------|----------|-----|-------|--------|
| Bot Engine | `BotEngine.ts`, plugins | X | X | 🟢/🔴 |
| Signal Pipeline | `SignalGenerator.ts`, `SignalFilter.ts` | X | X | 🟢/🔴 |
| Strategy System | `StrategyEnsemble.ts`, `StrategyLoader.ts` | X | X | 🟢/🔴 |
| Order Mgmt | `OrderManager.ts`, position mgr | X | X | 🟢/🔴 |
| Risk Engine | `RiskManager.ts`, `PortfolioRiskManager.ts` | X | X | 🟢/🔴 |
| Autonomy | `autonomy-controller.ts` | X | X | 🟢/🔴 |
| Paper Trading | `paper-trading-engine.ts` | X | X | 🟢/🔴 |
| Tenant System | `tenant-*.ts`, `raas-api-router.ts` | X | X | 🟢/🔴 |
| PnL Service | `pnl-realtime-snapshot-service.ts` | X | X | 🟢/🔴 |

### 2. CODE QUALITY SCAN
```bash
tsc --noEmit 2>&1 | tail -3                    # TS errors
grep -r ": any" src --include="*.ts" | wc -l   # any types
grep -r "@ts-ignore" src --include="*.ts" | wc -l  # ts-ignore
grep -r "console\." src --include="*.ts" | wc -l   # console
```
| Check | Count | Target | Status |
|-------|-------|--------|--------|
| TS errors | X | 0 | 🟢/🔴 |
| `any` types | X | 0 | 🟢/🔴 |
| `@ts-ignore` | X | 0 | 🟢/🔴 |
| `console.*` | X | 0 | 🟢/🔴 |
| Files >200 LOC | X | 0 | 🟢/🔴 |

### 3. TEST HEALTH
| Suite | Total | Pass | Fail | Coverage |
|-------|-------|------|------|----------|
| Unit | X | X | X | XX% |
| Integration | X | X | X | XX% |
| **Total** | **1216+** | X | X | XX% |

### 4. ARCHITECTURE REVIEW
Check plugin system, config cascade, strategy registry, tenant isolation.

## USAGE
```bash
/trading:backend audit         # Full backend audit
/trading:backend architecture  # Architecture review
/trading:backend quality       # Code quality scan
/trading:backend modules       # Module ownership map
```
