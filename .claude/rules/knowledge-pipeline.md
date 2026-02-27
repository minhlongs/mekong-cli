# Knowledge Pipeline Rule

> 用間 — Gián điệp là yếu tố quyết định

## Rule

Before executing any complex task (≥ 🌲RỪNG level), the agent MUST:

1. **Scan `knowledge/` directory** for relevant intel docs matching the task domain
2. **Read the top 1-3 most relevant docs** to inject domain context
3. **Check `apps/openclaw-worker/lessons.md`** for recent failures to AVOID repeating

## Implementation

When receiving a task, BEFORE planning:
```
1. ls knowledge/ | grep <domain-keyword>
2. cat knowledge/<matched-file>-intel.md
3. tail -30 apps/openclaw-worker/lessons.md
```

This ensures the AGI loop: **Learn from past** → **Apply to present** → **Record for future**.
