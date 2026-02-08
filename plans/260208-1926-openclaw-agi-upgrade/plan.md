---
title: "OpenClaw AGI Upgrade"
description: "Upgrade Tom Hum to Autonomous Gateway Intelligence with self-healing, retry, and memory decay"
status: pending
priority: P1
effort: 6h
branch: master
tags: [agi, resilience, telegram, memory, llm]
created: 2026-02-08
---

# OpenClaw AGI Upgrade Plan

## Objective

Harden the Tom Hum autonomous loop into production-grade AGI: resilient LLM calls, persistent improvement history, self-testing with git rollback, memory decay, and rich Telegram status.

## Research

- [Gemini Retry Patterns](research/researcher-01-gemini-retry-patterns.md) -- SDK built-in retry, circuit breaker, jitter, runtime failover
- [AGI Loop + Memory Decay](research/researcher-02-agi-loop-memory-decay.md) -- persistent history, self-testing, adaptive cooldown, memory decay models

## Phases

| # | Phase | File | Effort | Status |
|---|-------|------|--------|--------|
| 1 | LLM Client Resilience | [phase-01](phase-01-llm-client-resilience.md) | 1.5h | pending |
| 2 | NLP Commander Robustness | [phase-02](phase-02-nlp-commander-robustness.md) | 1h | pending |
| 3 | AGI Loop Intelligence | [phase-03](phase-03-agi-loop-intelligence.md) | 1.5h | pending |
| 4 | NeuralMemory Upgrade | [phase-04](phase-04-neuralmemory-upgrade.md) | 1h | pending |
| 5 | Telegram Bot AGI Commands | [phase-05](phase-05-telegram-agi-commands.md) | 1h | pending |

## Dependencies

```
Phase 1 (LLM Client) --> Phase 2 (NLP Commander) --> Phase 3 (AGI Loop)
Phase 4 (NeuralMemory) can run parallel with Phase 3
Phase 5 (Telegram) depends on Phase 3 (needs get_status())
```

## Key Decisions

1. **Keep SDK retry + manual retry**: SDK handles HTTP errors; manual retry handles empty content
2. **Persistent history via JSON file** (~/.mekong/agi_history.json): simplest, ~40 LOC
3. **Self-testing**: `pytest tests/ -x -q` after each CC CLI execution; `git checkout -- .` on failure
4. **Memory decay**: client-side filtering (no server `/decay` endpoint assumed)
5. **Circuit breaker**: 3 consecutive failures = 60s provider cooldown

## Success Criteria

- All 62 existing tests pass after each phase
- LLM client falls through providers at runtime (not just init)
- AGI loop persists history across restarts
- AGI loop rolls back failed improvements via git
- `/agi status` shows success rate, uptime, last improvement

## Unresolved Questions

1. Does NeuralMemory server support `/decay` endpoint? (Phase 4 assumes NO)
2. `git checkout -- .` safety when user has uncommitted changes -- Phase 3 uses `git stash` guard
3. Test suite takes ~2.5min; consider `pytest --last-failed` for AGI self-test (Phase 3)
4. Double retry risk: SDK 5 attempts + manual 3 = up to 15 on 429 (accepted, documented)
