# Phase 3: Fix Group B - Brain Tmux

## Context
- **Parent Plan**: [plan.md](plan.md)
- **Dependencies**: Phase 2 complete
- **Status**: Pending
- **Priority**: P0

## Overview
Fix 6 bugs trong brain-tmux.js để tăng tốc độ response và improve question handling.

## Key Insights
- Sleep values hiện tại quá cao → slow response
- APPROVE_PATTERNS không đủ coverage cho USER DECISION questions
- hasApproveQuestion scan chỉ 3 lines → miss questions ở scrollback
- Model override có thể conflict với proxy routing

## Requirements

### Bug #4: Poll sleep(5000) → 2000ms
- **Current**: 5000ms (line 840)
- **Expected**: 2000ms
- **Impact**: 2.5x faster polling

### Bug #5: Initial sleep(5000) → 2000ms
- **Current**: 5000ms (line 689)
- **Expected**: 2000ms
- **Impact**: 3s faster mission start

### Bug #6: Question sleep(3000) → 1000ms
- **Current**: 3000ms (line 790)
- **Expected**: 1000ms (already done per code!)
- **Action**: VERIFY only

### Bug #7: QUESTION NOT ANSWERED
- **Current**: APPROVE_PATTERNS có 15 patterns, hasApproveQuestion scan 15 lines
- **Expected**: Add more patterns, extend scan to 15 lines
- **Fix**: Add patterns cho "muốn.*làm gì", "USER DECISION", "Options:", etc.

### Bug #8: Verify Escape+C-u trước pasteText
- **Current**: Lines 660-664 có Escape+C-u
- **Expected**: VERIFIED ✅
- **Action**: No change needed

### Bug #9: Verify model override disabled
- **Current**: Line 603 có comment "// REMOVED"
- **Expected**: VERIFIED ✅
- **Action**: No change needed

## Architecture

### Polling Loop Enhancement
```
BEFORE: poll every 5s → detect busy → wait 5s → repeat
AFTER:  poll every 2s → detect busy → wait 2s → repeat
Result: 2.5x faster detection
```

### Question Detection Enhancement
```
BEFORE: Scan last 3 lines → limited patterns
AFTER:  Scan last 15 lines → comprehensive patterns
Result: Catch questions in scrollback
```

## Related Code Files

**Modify**:
- `lib/brain-tmux.js`

## Implementation Steps

1. **Fix Bug #4 — Poll Sleep**
   ```javascript
   // Line ~840 (in while loop)
   // BEFORE:
   await sleep(5000);

   // AFTER:
   await sleep(2000); // 🧬 FIX #4: Reduce poll interval for faster response
   ```

2. **Fix Bug #5 — Initial Sleep**
   ```javascript
   // Line ~689
   // BEFORE:
   await sleep(5000); // Give CC CLI time to parse

   // AFTER:
   await sleep(2000); // 🧬 FIX #5: Faster initial detection
   ```

3. **Verify Bug #6 — Question Sleep (Already Fixed)**
   ```javascript
   // Line 790 — ALREADY shows 1000ms:
   await sleep(1000); // ✅ VERIFIED
   ```

4. **Fix Bug #7 — Extend APPROVE_PATTERNS**
   ```javascript
   // Lines 82-89 — ADD these patterns:
   const APPROVE_PATTERNS = [
     // ... existing patterns ...
     // 🧬 FIX Bug #7: ADD decision-request patterns
     /muốn.*làm gì/i,                     // "Bạn muốn tôi làm gì tiếp theo?"
     /USER DECISION/i,                    // "USER DECISION REQUIRED"
     /Khuyến nghị.*chọn/i,                // "Khuyến nghị: Chọn Option A"
     /Options?:/i,                        // "Options: A) ... B) ...-"
     /What would you like/i,              // "What would you like me to do?"
     /Which option/i,                     // "Which option do you prefer?"
   ];
   ```

   **VERIFY**: hasApproveQuestion already scans 15 lines (line 191) ✅

5. **Verify Bug #8 — Escape+C-u (Already Present)**
   ```javascript
   // Lines 660-664 — ALREADY has Escape+C-u:
   tmuxExec(`tmux send-keys -t ${targetPane} Escape`);
   await sleep(200);
   tmuxExec(`tmux send-keys -t ${targetPane} C-u`);
   await sleep(300);
   // ✅ VERIFIED
   ```

6. **Verify Bug #9 — Model Override Disabled**
   ```javascript
   // Line 603 — ALREADY commented out:
   // 🔒 Chairman Fix: MODEL OVERRIDE DISABLED
   // Bug #3: /model claude-opus → proxy returns "invalid model"
   // if (modelOverride) { ... } — REMOVED
   // ✅ VERIFIED
   ```

7. **Syntax Check**
   ```bash
   node -e "require('./lib/brain-tmux.js')"
   ```

## Todo List
- [ ] Fix Bug #4 — Reduce poll sleep 5000→2000
- [ ] Fix Bug #5 — Reduce initial sleep 5000→2000
- [ ] Verify Bug #6 — Question sleep already 1000 ✅
- [ ] Fix Bug #7 — Add 6 new APPROVE_PATTERNS
- [ ] Verify Bug #8 — Escape+C-u already present ✅
- [ ] Verify Bug #9 — Model override already disabled ✅
- [ ] Syntax check passes
- [ ] Test with sample mission

## Success Criteria
- ✅ Poll interval = 2000ms
- ✅ Initial sleep = 2000ms
- ✅ Question sleep = 1000ms (verified)
- ✅ APPROVE_PATTERNS includes 6 new decision patterns
- ✅ Escape+C-u verified present
- ✅ Model override verified disabled
- ✅ No syntax errors
- ✅ Mission response time < 5s in test

## Risk Assessment
**Low Risk** — Sleep reductions are safe. Pattern additions only expand coverage.

**Mitigation**:
- Keep old values in comments
- Test with mission that triggers questions
- Verify patterns with regex tester

## Security Considerations
N/A — No security impact.

## Next Steps
- Proceed to Phase 4
- Monitor first 10 missions for question handling
