---
description: "Binh Phap patrol — check military camp compliance, detect violations"
argument-hint: "[--fix]"
---

# /patrol — Military Camp Patrol

## Usage
```
/patrol              # Check violations
/patrol --fix        # Auto-archive orphans, clean up
```

## Checks
1. **HÀNH LANG** — orphan dirs (.agent, .agents, .antigravity, ...)
2. **Stale reports** — GO_LIVE, PHASE*, security, etc.
3. **Package manager** — npm vs pnpm conflict
4. **QUÂN DOANH integrity** — mekong/ + hooks/ modified without approval

## Auto-Fix
With `--fix`: archive orphans to `.archive/orphan-dirs/`, archive stale reports to `.archive/reports/`.
