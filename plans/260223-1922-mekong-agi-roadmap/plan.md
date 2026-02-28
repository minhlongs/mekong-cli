---
title: "mekong-cli AGI Readiness Roadmap"
description: "Audit kết quả + roadmap hoàn thiện 5 AGI capabilities để đạt AGI Level"
status: pending
priority: P1
effort: 8h
branch: master
tags: [agi, audit, roadmap, python, mekong-cli]
created: 2026-02-23
---

# mekong-cli AGI Readiness Roadmap

## Kết quả Audit (2026-02-23)

| Hạng mục | Kết quả |
|----------|---------|
| pytest (388 tests) | ✅ 100% PASS |
| src/core/ modules | ✅ 8/10 modules hoạt động |
| mekong cook CLI | ❌ Binary không accessible |
| AGI capabilities | ⚠️ 3/5 complete, 2/5 partial |

## Phases

| Phase | Tên | Status | Effort |
|-------|-----|--------|--------|
| 01 | [Fix CLI Install + Environment](phase-01-fix-cli-install.md) | pending | 30m |
| 02 | [Self-Healing Auto-Correct Integration](phase-02-self-healing.md) | pending | 2h |
| 03 | [NLU Enhancement + More Intents](phase-03-nlu-enhancement.md) | pending | 1.5h |
| 04 | [Multi-Agent Swarm Task Distribution](phase-04-swarm-dispatch.md) | pending | 3h |
| 05 | [Learning Loop: Auto-Generate Improved Recipes](phase-05-learning-loop.md) | pending | 2h |

## AGI Capability Map

```
Plan-Execute-Verify Pipeline ──── ✅ COMPLETE (orchestrator.py)
Self-Healing Auto-Correct   ──── ⚠️ PARTIAL → Phase 02
Memory Cross-Session        ──── ✅ COMPLETE (memory.py YAML)
NLU Intent Classification   ──── ⚠️ PARTIAL → Phase 03
Multi-Agent Coordination    ──── ❌ MISSING → Phase 04
Learning Loop               ──── ❌ MISSING → Phase 05
```

## Context
- Working dir: `/Users/macbookprom1/mekong-cli`
- Audit report: `plans/260223-1922-mekong-agi-roadmap/research/audit-results.md`
- pyproject: `poetry scripts` định nghĩa `mekong = "src.main:app"`
- Tests: `uv run python -m pytest tests/` — phải install deps trước

## Unresolved Questions
- `agi_loop.py` chưa được kiểm tra chi tiết — có thể đã implement learning loop?
- `self_improve.py` đầy đủ code chưa hay còn stub?
