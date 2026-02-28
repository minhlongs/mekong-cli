# Phase 05 — Learning Loop: Auto-Generate Improved Recipes

**Context:** [plan.md](plan.md) | [audit-results.md](research/audit-results.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P2
- **Status:** pending
- **Effort:** 2h
- **Blocked by:** Phase 02 (self-healing), Phase 03 (NLU)

## Key Insights
- `self_improve.py` có `analyze_and_improve()` — nhưng chỉ SUGGEST, không AUTO-APPLY
- `recipe_gen.py` có `RecipeGenerator` — tạo recipe mới từ LLM
- `memory.py` lưu execution history với `success_rate`, `suggest_fix()` — data source ready
- Thiếu: auto-trigger `recipe_gen` khi detect pattern failure
- Thiếu: feedback loop → memory → planner improvement

## Requirements
- Sau N failures của cùng 1 goal pattern:
  - `SelfImprover` detect pattern
  - Auto-call `RecipeGenerator` tạo improved recipe
  - Lưu vào `recipes/` directory với suffix `_v2.md`
  - Next time cùng goal → NLU route sang recipe mới
- `learner.py` (EXISTS) — tích hợp với learning loop

## Related Files
- `src/core/self_improve.py` — `SelfImprover` class
- `src/core/recipe_gen.py` — `RecipeGenerator`
- `src/core/learner.py` — EXISTS, chưa kiểm tra
- `src/core/memory.py` — failure patterns data
- `tests/test_self_improve.py` — existing tests
- `tests/test_learner.py` — existing tests

## Architecture
```
MemoryStore.get_success_rate(goal) < 30%
    ↓ (after 10+ runs)
SelfImprover.analyze_and_improve() detects bad recipe
    ↓
SelfImprover._auto_generate_improved(recipe_name, failures)
    ↓
RecipeGenerator.generate_from_failures(failures) → new_recipe.md
    ↓
Save to recipes/{goal_slug}_improved.md
    ↓
EventBus.emit(RECIPE_IMPROVED, {old: ..., new: ...})
    ↓
Next orchestration: SmartRouter routes to improved recipe
```

## Implementation Steps

1. **self_improve.py** — Thêm `_auto_generate_improved()` method:
   ```python
   def _auto_generate_improved(self, recipe_name: str, failures: list) -> Optional[str]:
       """Auto-generate improved recipe based on failure analysis."""
       if not self.generator.llm_client:
           return None
       improved = self.generator.generate_from_failures(recipe_name, failures)
       if improved:
           path = f"recipes/{recipe_name}_improved.md"
           Path(path).write_text(improved)
           return path
   ```

2. **self_improve.py** — Trigger auto-generate trong `analyze_and_improve()`:
   ```python
   if rate < self.DEPRECATION_THRESHOLD and runs >= self.MIN_RUNS_FOR_DEPRECATION:
       improved_path = self._auto_generate_improved(goal, failures)
       if improved_path:
           entry = JournalEntry(action="auto_improved", target=goal, data={"new": improved_path})
           new_entries.append(entry)
   ```

3. **learner.py** — Đọc file và integrate nếu phù hợp

4. **memory.py** — Thêm `get_failure_patterns()` method để group failures by error_summary

5. Verify với `tests/test_self_improve.py` và `tests/test_learner.py`

## Todo
- [ ] Đọc `learner.py` đầy đủ để hiểu current state
- [ ] Thêm `_auto_generate_improved()` vào `self_improve.py`
- [ ] Trigger từ `analyze_and_improve()` khi rate < threshold
- [ ] Thêm `get_failure_patterns()` vào `memory.py`
- [ ] Chạy `test_self_improve.py` + `test_learner.py`

## Files Sẽ Sửa (max 4)
1. `src/core/self_improve.py`
2. `src/core/learner.py` (extend nếu cần)
3. `src/core/memory.py` (thêm `get_failure_patterns`)

## Success Criteria
- Recipe với success_rate < 30% → auto-generate improved version
- `test_self_improve.py` pass với new test cases
- `recipes/` directory có file mới sau learning cycle

## Risk
- Medium: phụ thuộc LLM online để test
- Cần mock `RecipeGenerator` trong tests

## Unresolved Questions
- `learner.py` implement gì? Cần đọc trước khi implement Phase 05
