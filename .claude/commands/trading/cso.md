---
description: ⚡⚡⚡⚡ CSO Security Command — API key audit, exchange security, stealth risk, vulnerability scan, secrets detection
argument-hint: [action: audit|scan|stealth|keys]
---

**Ultrathink** CSO security review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/caio-cso-cco-sops.md` PART 2

## Pipeline (5 steps)

### 1. SECRETS SCAN
```bash
grep -r "API_KEY\|SECRET\|PASSWORD\|PRIVATE_KEY" src/ --include="*.ts" | wc -l  # must = 0
grep -r "console\." src/ --include="*.ts" | wc -l  # target = 0
```

### 2. DEPENDENCY AUDIT
```bash
pnpm audit --audit-level=high
```

### 3. EXCHANGE SECURITY
| Exchange | 2FA | Whitelist | Read-only API | Status |
|----------|-----|-----------|---------------|--------|
| Binance | ✅/❌ | ✅/❌ | ✅/❌ | 🟢/🔴 |
| OKX | ✅/❌ | ✅/❌ | ✅/❌ | 🟢/🔴 |
| Bybit | ✅/❌ | ✅/❌ | ✅/❌ | 🟢/🔴 |

### 4. STEALTH RISK
| Risk | Module | OTR% | Status |
|------|--------|------|--------|
| Bot detection | phantom-stealth-math.ts | <15% | 🟢/🔴 |
| Fingerprint | stealth-cli-fingerprint-masking.ts | — | 🟢/🔴 |
| Pattern detect | stealth-execution-algorithms.ts | — | 🟢/🔴 |
| Rate limit | phantom-order-cloaking-engine.ts | <65% | 🟢/🔴 |
| Account ban | exchange-router-with-fallback.ts | — | 🟢/🔴 |

### 5. REPORT
Save: `plans/reports/cso-security-{date}.md`

## USAGE
```bash
/trading:cso audit      # Full security audit
/trading:cso scan       # Secrets + dependency scan
/trading:cso stealth    # Stealth risk assessment
/trading:cso keys       # API key inventory
```
