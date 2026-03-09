# Plan: Kiến Trúc Lại Qwen API + CTO Panes Routing

**Date:** 2026-03-09 | **Branch:** master | **Priority:** CRITICAL

## Tóm Tắt Vấn Đề

6 vấn đề nghiêm trọng phát hiện sau deep scan:

1. **config.js DUPLICATE** — Lines 28-90 lặp lại, property sau override trước
2. **Pane routing MÂU THUẪN** — 4 file define pane→project khác nhau
3. **Qwen model family UNKNOWN** — `getModelFamily()` chỉ biết claude/gemini
4. **Subagent model env THIẾU** — `CLAUDE_CODE_SUBAGENT_MODEL` không set
5. **auto-cto-pilot.js SAI comment** — P1=well nhưng code=algo-trader
6. **factory-loop.sh HARDCODE** — Đường dẫn project hardcode thay vì dùng config

## Phases

| # | Phase | Status | Files |
|---|-------|--------|-------|
| 1 | Fix config.js duplicate + single source pane map | TODO | 1 file |
| 2 | Thống nhất pane routing across 4 files | TODO | 4 files |
| 3 | Proxy model mapping cho Qwen | TODO | 2 files |
| 4 | Subagent model env + generateClaudeCommand | TODO | 2 files |
| 5 | Test + verify | TODO | manual |

## Dependencies

- Phase 1 → Phase 2 (config phải fix trước)
- Phase 3 độc lập
- Phase 4 phụ thuộc Phase 1
