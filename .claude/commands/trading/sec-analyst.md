---
description: ⚡⚡⚡ Security Analyst — vulnerability scan, secrets detection, stealth module integrity, API key audit
argument-hint: [action: scan|stealth|keys|vuln]
---

**Ultrathink** Security analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 9
**Reports to:** CSO (`/trading:cso`)

## Pipeline (4 steps)

### 1. VULNERABILITY SCAN
```bash
grep -r "API_KEY\|SECRET\|PASSWORD\|PRIVATE_KEY" src/ --include="*.ts" | wc -l
pnpm audit --audit-level=high
grep -r "@ts-ignore\|@ts-nocheck\|: any" src/ --include="*.ts" | wc -l
```
| Check | Count | Target | Severity |
|-------|-------|--------|----------|
| Hardcoded secrets | X | 0 | 🔴 Critical |
| npm high vulns | X | 0 | 🔴 Critical |
| `any` types | X | 0 | 🟡 Medium |
| `@ts-ignore` | X | 0 | 🟡 Medium |
| `console.*` prod | X | 0 | 🟢 Low |

### 2. STEALTH MODULE INTEGRITY
| Module | Check | Expected | Status |
|--------|-------|----------|--------|
| `phantom-stealth-math.ts` | OTR ratio | <15% | 🟢/🔴 |
| `stealth-execution-algorithms.ts` | Randomization | Active | 🟢/🔴 |
| `phantom-order-cloaking-engine.ts` | Rate limit | <65% | 🟢/🔴 |
| `anti-detection-order-randomizer-safety-layer.ts` | Size jitter | Active | 🟢/🔴 |
| `stealth-cli-fingerprint-masking-middleware.ts` | Fingerprint | Masked | 🟢/🔴 |
| `binh-phap-stealth-trading-strategy.ts` | Pattern | Varied | 🟢/🔴 |

### 3. API KEY AUDIT
| Check | Status |
|-------|--------|
| Keys in .env only (not in code) | ✅/❌ |
| .env in .gitignore | ✅/❌ |
| Key rotation <90 days | ✅/❌ |
| Read-only keys where possible | ✅/❌ |
| IP whitelist configured | ✅/❌ |
| 2FA on all exchanges | ✅/❌ |

### 4. REPORT
Save: `plans/reports/security-scan-{date}.md`

## USAGE
```bash
/trading:sec-analyst scan      # Full vulnerability scan
/trading:sec-analyst stealth   # Stealth module integrity
/trading:sec-analyst keys      # API key security audit
/trading:sec-analyst vuln      # Dependency vulnerabilities
```
