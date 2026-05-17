---
description: ⚡⚡⚡⚡ Founder Emergency Protocols — Red/Orange/Yellow alerts, halt trading, capital preservation, recovery plan
argument-hint: [alert: red|orange|yellow] [description: "what happened"]
---

**Ultrathink** Founder emergency protocol: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/founder-sops.md` SOP-F08

---

## ALERT LEVELS

### RED ALERT — Drawdown >15%

```
1. HALT tất cả trading NGAY LẬP TỨC
   # Kill all running bot processes

2. FREEZE 24-48h — KHÔNG trade
   # Emotional cool-down + analysis

3. ROOT CAUSE ANALYSIS
   ├── Strategy nào gây loss chính?
   ├── Market regime đổi? (trending → ranging?)
   ├── Exchange issue? (slippage, latency spike?)
   ├── Circuit breaker vì sao không chặn sớm hơn?
   └── Config sai? (position size quá lớn?)

4. RECOVERY PLAN
   ├── Downgrade TẤT CẢ strategies → paper mode
   ├── Review + adjust risk limits
   ├── Paper trade minimum 3 ngày profitable
   ├── Re-enter live CHỈ KHI paper confirms
   └── Start lại với 50% budget trước đó

5. ESCALATE → CEO
   /trading:ceo quarterly    # Trigger full strategic review
```

### ORANGE ALERT — 3 Ngày Loss Liên Tiếp

```
1. REDUCE — Giảm budget 50%

2. VERIFY — Chuyển strategies mạnh nhất sang paper
   /trading:auto:agi BTC/USDT paper $100 2h

3. DIAGNOSE
   ├── Market regime change?
   ├── Strategy alpha decay?
   ├── Execution quality decline?
   └── /trading:debug "3 consecutive daily losses"

4. ADJUST — Strategy weight rebalancing
   /trading:founder:strategy review

5. RESUME — Sau 1 ngày paper profitable
   ├── Restore budget gradually (25% → 50% → 100%)
   └── Monitor closely for 48h
```

### YELLOW ALERT — Exchange Issue

```
1. IDENTIFY — Which exchange?
   /trading:health

2. FAILOVER — ExchangeRouter auto-switches
   # Verify failover working
   # src/execution/exchange-router-with-fallback.ts

3. IF 1 exchange down:
   ├── Bot auto-failover (should be automatic)
   ├── Verify trades continuing on backup exchange
   └── Monitor until recovery

4. IF 2+ exchanges down:
   ├── HALT all trading
   ├── Wait for recovery
   ├── /trading:coo:incident P1 "multiple exchanges down"
   └── Resume only when ≥2 exchanges stable

5. LOG — Document incident
   /trading:coo:incident P1 "exchange issue: {description}"
```

---

## EMERGENCY DECISION MATRIX

```
Situation                          Alert    Action
──────────────────────────────────────────────────────
DD >15%                            RED      HALT ALL. CEO review.
DD 10-15%                          ORANGE   Cut 50%. Paper verify.
3 daily losses                     ORANGE   Cut 50%. Diagnose.
5 consecutive trade losses         YELLOW   Downgrade autonomy.
1 exchange down                    YELLOW   Auto-failover. Monitor.
2+ exchanges down                  RED      HALT. Wait recovery.
Circuit breaker 3x in 1 day       ORANGE   Reduce budget. Review.
Flash crash detected               RED      HALT. Wait 24h.
API key compromised               RED      Revoke ALL keys. Halt.
Unusual activity on account        RED      Freeze. Check exchange.
```

---

## POST-EMERGENCY RECOVERY

```
1. Cool-down period (24-48h for RED, 24h for ORANGE)
2. Root cause documented in incident report
3. Risk limits adjusted if needed
4. Paper trade verification (3 days minimum)
5. Gradual budget restoration (25% → 50% → 75% → 100%)
6. Close monitoring first 48h after resuming live
7. Weekly review for 4 weeks after incident
```

## USAGE
```bash
/trading:founder:emergency red "drawdown hit 18%"
/trading:founder:emergency orange "3 days loss in a row"
/trading:founder:emergency yellow "binance API timeout"
```
