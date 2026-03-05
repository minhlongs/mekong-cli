---
title: Refactor Large Files (10 files >200 lines)
description: Parallel refactoring of large Python modules into focused components
status: pending
priority: P2
effort: 12h
branch: master
tags: [refactor, quality, architecture]
created: 2026-03-05
---

# Plan: Large File Refactoring

## Files to Refactor

| P | File | Lines | Target Modules |
|---|------|-------|----------------|
| P0 | src/main.py | 1242 | cli/, commands/, core/ |
| P1 | src/core/gateway.py | 780 | gateway/, api/, dashboard/ |
| P1 | src/core/telegram_bot.py | 743 | telegram/, handlers/, inbox/ |
| P2 | src/core/orchestrator.py | 686 | orchestration/, flow/, steps/ |
| P2 | src/core/cross_session_intelligence.py | 627 | users/, sessions/, storage/ |
| P3 | src/commands/docs.py | 561 | docs/generate/, docs/serve/, docs/check/ |
| P3 | src/commands/security.py | 507 | security/scan/, security/tools/, security/report/ |
| P3 | src/core/agi_loop.py | 506 | agi/, self-improvement/, history/ |
| P3 | src/core/learning_tracker.py | 505 | learning/, memory/, analytics/ |
| P3 | src/core/verifier.py | 468 | verification/, checks/, reports/ |

## Refactoring Strategy

**Principles:**
- Extract modules by responsibility (SRP)
- Split files >200 lines into 3-5 focused modules
- Keep tests intact, update imports
- Preserve all functionality

**Pattern:**
```
src/core/old_file.py
    ↓
src/core/module_a/
    ├── __init__.py
    ├── core.py
    └── utils.py
```

## Test Plan

```
pytest tests/ -v --tb=short
coverage report -m
```

## Success Criteria

- 0 files >200 lines
- 100% test pass
- 0 `any` types
- Build < 10s
