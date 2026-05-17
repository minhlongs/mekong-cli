---
description: ⚡⚡⚡⚡ COO Incident Response — structured P0-P3 incident workflow, root cause, resolution, prevention
argument-hint: [severity: P0|P1|P2|P3] [description: "what happened"]
---

**Ultrathink** COO incident response: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/coo-sops.md` SOP-O03

---

## SEVERITY MATRIX

| Level | Trigger | Response | Escalate |
|-------|---------|----------|----------|
| **P0** | Trading halted, capital at risk | Immediate | CEO |
| **P1** | Exchange down, strategy failing | <15 min | Founder |
| **P2** | Performance degraded, warnings | <1 hour | Self |
| **P3** | Minor issues, optimization | <24 hours | Self |

---

## PIPELINE — 5 Steps (IDENTIFY → CONTAIN → DIAGNOSE → RESOLVE → REPORT)

### 1. IDENTIFY
```bash
# System status
/trading:health
/trading:coo:health

# Recent events
ls -t plans/reports/trading-*.md | head -5
```

Determine:
- What broke? (exchange/bot/strategy/infra/data)
- When did it start?
- What changed before the incident?
- Impact: trades affected? capital at risk?

### 2. CONTAIN
| Severity | Containment |
|----------|-------------|
| P0 | Halt all trading. Verify open positions. |
| P1 | Isolate affected exchange/strategy. Bot continues on healthy components. |
| P2 | Reduce exposure. Monitor closely. |
| P3 | Log issue. Continue normal operations. |

**Modules involved:**
- `src/core/autonomy-controller.ts` → `escalate()` to downgrade autonomy
- `src/execution/adaptive-circuit-breaker-per-exchange.ts` → per-exchange isolation
- `src/execution/exchange-router-with-fallback.ts` → failover routing

### 3. DIAGNOSE
```bash
/trading:debug "{incident description}"
```

**Root cause categories:**
| Category | Symptoms | Module to Check |
|----------|----------|----------------|
| Exchange | 429, timeout, WS disconnect | `exchange-health-monitor.ts` |
| Strategy | Signal accuracy drop, alpha decay | `SignalGenerator.ts` |
| Execution | High slippage, fill rate drop | `stealth-execution-algorithms.ts` |
| Infrastructure | Process crash, memory spike | `BotEngine.ts`, system metrics |
| Market | Flash crash, extreme volatility | Circuit breaker logs |
| Config | Wrong parameters, missing keys | `config-schema.ts`, `CredentialVault.ts` |

### 4. RESOLVE
- Fix root cause
- Verify fix:
```bash
tsc --noEmit                    # Build clean
pnpm test 2>&1 | tail -5       # Tests pass
/trading:auto BTC/USDT paper   # Paper trade verify
```
- If P0/P1: paper trade minimum 2h before resuming live

### 5. REPORT
Save: `plans/reports/coo-incident-P{N}-{date}.md`

```markdown
## Incident Report — P{N} — {date}

### Summary
- **Severity:** P{N}
- **Duration:** {start} → {resolved} ({Xh Xm})
- **Impact:** {trades affected, capital impact}

### Timeline
| Time | Event |
|------|-------|
| HH:MM | Issue detected |
| HH:MM | Containment action |
| HH:MM | Root cause identified |
| HH:MM | Fix applied |
| HH:MM | Verified resolved |

### Root Cause
{Description + module + evidence}

### Resolution
{What was done to fix}

### Prevention
- [ ] {Action to prevent recurrence}
- [ ] {Config/code change needed}
- [ ] {Monitoring improvement}

### Escalation
- Escalated to: {CEO/Founder/Self}
- Decision: {action taken}
```

## USAGE
```bash
/trading:coo:incident P0 "trading halted — daily loss limit hit"
/trading:coo:incident P1 "binance exchange 429 rate limit"
/trading:coo:incident P2 "strategy alpha declining last 3 days"
/trading:coo:incident P3 "report generation slow"
```
