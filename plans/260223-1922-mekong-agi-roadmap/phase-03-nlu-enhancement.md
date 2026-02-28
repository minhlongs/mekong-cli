# Phase 03 — NLU Enhancement + More Intents

**Context:** [plan.md](plan.md) | [audit-results.md](research/audit-results.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P2
- **Status:** pending
- **Effort:** 1.5h

## Key Insights
- `nlu.py` hiện có 6 intents: DEPLOY/AUDIT/CREATE/FIX/STATUS/SCHEDULE
- Thiếu intents quan trọng: REFACTOR, SEARCH, LEARN, ANALYZE, TEST, OPTIMIZE
- Keyword map chỉ có EN + VN cơ bản — thiếu nhiều từ đồng nghĩa
- Entity extraction dùng regex đơn giản — thiếu: version numbers, file paths, branch names
- LLM fallback có nhưng chưa có confidence calibration tốt
- `suggest_recipe` field trong `IntentResult` — chưa được populate từ keyword classification

## Requirements
- Thêm tối thiểu 4 intents mới: REFACTOR, SEARCH, LEARN, TEST
- Mở rộng keyword map: thêm Vietnamese synonyms, code terms
- `suggest_recipe` phải được populate khi confidence ≥ 0.7
- Entity extraction: thêm file_path, branch_name, version patterns

## Related Files
- `src/core/nlu.py` — IntentClassifier, KEYWORD_MAP (main file)
- `src/core/smart_router.py` — consumes IntentResult
- `tests/test_nlu.py` — existing tests

## Implementation Steps

1. **nlu.py** — Thêm intents mới vào `Intent` enum:
   ```python
   REFACTOR = "refactor"
   SEARCH = "search"
   LEARN = "learn"
   TEST = "test"
   OPTIMIZE = "optimize"
   ```

2. **nlu.py** — Mở rộng `KEYWORD_MAP`:
   ```python
   Intent.REFACTOR: ["refactor", "clean", "restructure", "tái cấu trúc", "dọn dẹp"],
   Intent.SEARCH: ["search", "find", "look", "tìm kiếm", "tìm"],
   Intent.LEARN: ["learn", "train", "improve", "học", "học hỏi"],
   Intent.TEST: ["test", "check", "verify", "kiểm thử", "chạy test"],
   Intent.OPTIMIZE: ["optimize", "speed", "performance", "tối ưu"],
   ```

3. **nlu.py** — Thêm intent → recipe mapping:
   ```python
   INTENT_RECIPE_MAP = {
       Intent.DEPLOY: "recipes/deploy.md",
       Intent.FIX: "recipes/fix.md",
       Intent.TEST: "recipes/test.md",
       # ...
   }
   # Populate IntentResult.suggested_recipe từ map này
   ```

4. **nlu.py** — Thêm entity patterns:
   ```python
   _FILE_PATH_RE = re.compile(r"[\w./]+\.(py|ts|js|md|yaml|json)", re.IGNORECASE)
   _BRANCH_RE = re.compile(r"(?:branch|nhánh)\s+([\w/-]+)", re.IGNORECASE)
   ```

5. Verify `tests/test_nlu.py` pass

## Todo
- [ ] Thêm 4 intents mới vào `Intent` enum
- [ ] Mở rộng `KEYWORD_MAP` với từ mới
- [ ] Thêm `INTENT_RECIPE_MAP` để populate `suggested_recipe`
- [ ] Thêm file_path + branch entity patterns
- [ ] Chạy `test_nlu.py` — xác nhận pass

## Success Criteria
- `classify("refactor the auth module")` → `Intent.REFACTOR, confidence ≥ 0.7`
- `classify("tìm kiếm lỗi trong planner")` → `Intent.SEARCH, confidence ≥ 0.7`
- `IntentResult.suggested_recipe` populated cho 5/10 intents
- `test_nlu.py` 100% pass

## Files Sẽ Sửa (max 2)
1. `src/core/nlu.py`
2. `tests/test_nlu.py` (thêm test cases mới)

## Next Steps
→ Phase 04: Multi-Agent Swarm
