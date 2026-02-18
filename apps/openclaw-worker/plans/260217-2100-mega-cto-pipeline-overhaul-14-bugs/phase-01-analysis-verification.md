# Phase 1: Analysis & Verification

## Context
- **Parent Plan**: [plan.md](plan.md)
- **Status**: Pending
- **Priority**: P0 - Must complete before fixes

## Overview
Phân tích code hiện tại, verify tất cả 14 bugs tồn tại, document baseline values.

## Key Insights
- Cần đọc tất cả 5 files để xác nhận exact line numbers
- Một số bugs có thể đã được fix (cần verify)
- Baseline values cần được document để so sánh sau khi fix

## Requirements

### Functional
- Read all 5 target files
- Identify exact locations of all 14 bugs
- Document current values vs expected values
- Create verification checklist

### Non-Functional
- Must complete trong < 5 phút
- Output: markdown report với line numbers

## Related Code Files

**Files to analyze**:
- `task-watcher.js` (bugs 1-3)
- `lib/brain-tmux.js` (bugs 4-9)
- `lib/mission-dispatcher.js` (bugs 10-12)
- `lib/m1-cooling-daemon.js` (bug 13)
- `config.js` (bug 14)

## Implementation Steps

1. **Read task-watcher.js**
   - Line ~? — POLL_INTERVAL check
   - Line ~? — File move logic after dispatch
   - Line ~? — Priority queue implementation

2. **Read lib/brain-tmux.js**
   - Line 840 — Poll sleep (5000)
   - Line 689 — Initial sleep (5000)
   - Line 790 — Question sleep (3000)
   - Line 82-89 — APPROVE_PATTERNS
   - Line 191 — hasApproveQuestion scan range
   - Line 660-664 — Escape+C-u verification
   - Line 603 — Model override logic

3. **Read lib/mission-dispatcher.js**
   - Line 62 — Bypass check
   - Line 102 — mandatePrefix usage
   - Line 91-95 — HÀN BĂNG threshold

4. **Read lib/m1-cooling-daemon.js**
   - Line 30-32 — OVERHEAT_LOAD, SAFE_LOAD
   - Line 46 — VELOCITY_THRESHOLD

5. **Read config.js**
   - Line 28 — POLL_INTERVAL_MS

6. **Create Bug Report**
   ```markdown
   ## Bug Analysis Report

   | Bug# | File | Line | Current | Expected | Status |
   |------|------|------|---------|----------|--------|
   | 1    | task-watcher.js | ? | ? | <= 5000 | ✅/❌ |
   | ...  | ... | ... | ... | ... | ... |
   ```

## Todo List
- [ ] Read task-watcher.js — identify bugs 1-3
- [ ] Read brain-tmux.js — identify bugs 4-9
- [ ] Read mission-dispatcher.js — identify bugs 10-12
- [ ] Read m1-cooling-daemon.js — identify bug 13
- [ ] Read config.js — identify bug 14
- [ ] Create bug analysis report
- [ ] Document baseline values
- [ ] Create fix checklist

## Success Criteria
- All 14 bugs located với exact line numbers
- Baseline values documented
- Report saved to `reports/bug-analysis-260217.md`
- Ready to proceed to Phase 2

## Risk Assessment
**Zero Risk** — Pure analysis, no code changes.

## Security Considerations
N/A — Read-only analysis.

## Next Steps
- Proceed to Phase 2 after report complete
- Use report as guide for fixes
