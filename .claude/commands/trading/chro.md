---
description: ⚡⚡⚡ CHRO Command — team building, contributor onboarding, hiring triggers, culture management
argument-hint: [action: review|onboard|hire|culture]
---

**Ultrathink** CHRO review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/chro-sops.md`

## Pipeline (4 steps)

### 1. TEAM STATUS
```
Current: Solo CEO + AI System
Contributors: N active on GitHub
Discord: N members, N active/week
```

### 2. HIRING TRIGGER CHECK
| Role | Trigger | Met? | Action |
|------|---------|------|--------|
| Quant Analyst | Revenue >$5K/mo | ✅/❌ | Post job |
| DevOps | 3+ exchanges live | ✅/❌ | Post job |
| Risk Manager | Portfolio >$50K | ✅/❌ | Post job |
| Trader Ops | 24/7 trading | ✅/❌ | Post job |

### 3. CONTRIBUTOR HEALTH
- Open PRs waiting review?
- "Good first issue" labels available?
- Onboarding docs current?
- CONTRIBUTING.md exists?

### 4. CULTURE PULSE
- Safety-first culture maintained?
- Test discipline (no skipping)?
- CLI-native philosophy?
- Binh Pháp discipline?

## USAGE
```bash
/trading:chro review     # Full team review
/trading:chro onboard    # Onboarding checklist
/trading:chro hire       # Hiring trigger check
```
