---
title: "NLU Enhancement Phase 03 — New Intents + Recipe Mapping"
description: "Extend IntentClassifier with 5 new intents, populate suggested_recipe, add entity patterns"
status: pending
priority: P2
effort: 1.5h
branch: master
tags: [nlu, python, intents, classification, vietnamese]
created: 2026-02-23
---

# NLU Enhancement Phase 03

## Context
- Source plan: [plans/260223-1922-mekong-agi-roadmap/phase-03-nlu-enhancement.md](../260223-1922-mekong-agi-roadmap/phase-03-nlu-enhancement.md)
- Working dir: `/Users/macbookprom1/mekong-cli`

## Phases

| # | Phase | Status | Effort |
|---|-------|--------|--------|
| 01 | [Extend Intent Enum + KEYWORD_MAP](phase-01-extend-intents.md) | pending | 30m |
| 02 | [Populate suggested_recipe + Entity Patterns](phase-02-recipe-mapping-entities.md) | pending | 30m |
| 03 | [Update Tests](phase-03-update-tests.md) | pending | 30m |

## Files Changed (max 2)
1. `src/core/nlu.py`
2. `tests/test_nlu.py`

## Key Constraints
- `test_all_intents_except_unknown_have_keywords` auto-enforces all new intents must have KEYWORD_MAP entries
- `test_intent_count` must be updated: 7 → 12
- "check" is already in AUDIT — do NOT put in TEST (first-wins rule, AUDIT would steal TEST matches)
- SmartRouter already has `_INTENT_TAGS` dict that needs updating too (out of scope for this plan — note only)

## Success Criteria
- `classify("refactor the auth module")` → `Intent.REFACTOR, confidence ≥ 0.7`
- `classify("tìm kiếm lỗi trong planner")` → `Intent.SEARCH, confidence ≥ 0.7`
- `IntentResult.suggested_recipe` populated for ≥5 intents when confidence ≥ 0.7
- `python3 -m pytest tests/test_nlu.py` → 100% pass
