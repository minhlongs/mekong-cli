# Phase 01 — Extend Intent Enum + KEYWORD_MAP

**Context:** [plan.md](plan.md) | [phase-03-nlu-enhancement.md](../260223-1922-mekong-agi-roadmap/phase-03-nlu-enhancement.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P2
- **Status:** pending
- **Effort:** 30m

## Key Insights
- Current `Intent` enum: 7 members (DEPLOY, AUDIT, CREATE, FIX, STATUS, SCHEDULE, UNKNOWN)
- `KEYWORD_MAP` uses first-match-wins order — keyword conflicts must be handled carefully
- **CONFLICT ALERT:** "check" exists in AUDIT. If TEST also has "check", AUDIT always wins (it comes first in dict)
  - Solution: Use "kiểm thử", "chạy test", "run test" for TEST — avoid "check"
- "verify" is a safe TEST keyword (not in AUDIT)
- Vietnamese diacritics are stored as-is in keywords (e.g. "tìm kiếm") and work because `.lower()` preserves unicode

## Requirements
- Add 5 intents: REFACTOR, SEARCH, LEARN, TEST, OPTIMIZE
- Add KEYWORD_MAP entries for all 5 (required by existing `test_all_intents_except_unknown_have_keywords`)
- Keywords must NOT conflict with existing higher-priority intents

## Related Code Files
- **Modify:** `src/core/nlu.py`

## Architecture

```
Intent enum (str, Enum):
  DEPLOY, AUDIT, CREATE, FIX, STATUS, SCHEDULE, UNKNOWN  ← existing
  REFACTOR, SEARCH, LEARN, TEST, OPTIMIZE                ← NEW

KEYWORD_MAP dict iteration = first-match-wins:
  Position matters! New intents appended after existing = lower priority
```

## Implementation Steps

1. In `src/core/nlu.py`, add 5 new values to `Intent` enum after `SCHEDULE`:
   ```python
   REFACTOR = "refactor"
   SEARCH = "search"
   LEARN = "learn"
   TEST = "test"
   OPTIMIZE = "optimize"
   ```

2. Add entries to `KEYWORD_MAP` (after existing entries):
   ```python
   Intent.REFACTOR: ["refactor", "restructure", "cleanup", "tái cấu trúc", "dọn dẹp", "refac"],
   Intent.SEARCH: ["search", "find", "lookup", "tìm kiếm", "tìm", "tim kiem"],
   Intent.LEARN: ["learn", "study", "train model", "học", "học hỏi", "hoc"],
   Intent.TEST: ["test", "run test", "kiểm thử", "chạy test", "kiem thu"],
   Intent.OPTIMIZE: ["optimize", "speed up", "tối ưu", "toi uu", "performance tune"],
   ```
   **Note:** "verify" intentionally excluded from TEST (already in AUDIT context). "check" excluded from TEST.

## Todo
- [ ] Add 5 intents to `Intent` enum
- [ ] Add KEYWORD_MAP entries (5 intents × ≥3 keywords each)
- [ ] Confirm no keyword conflicts with existing intents

## Success Criteria
- `len(Intent) == 12`
- All 5 new intents present in KEYWORD_MAP
- `classify("refactor auth")` → REFACTOR
- `classify("tìm kiếm lỗi")` → SEARCH
- `classify("optimize performance")` → OPTIMIZE

## Risk Assessment
- LOW: keyword conflicts if "verify" accidentally added to TEST (AUDIT has it)
- LOW: dict ordering in Python 3.7+ is insertion-order guaranteed

## Security Considerations
- N/A — pure classification logic, no I/O

## Next Steps
→ Phase 02: Recipe mapping + entity patterns
