# Phase 4: Fix Group C - Mission Dispatcher

## Context
- **Parent Plan**: [plan.md](plan.md)
- **Dependencies**: Phase 3 complete
- **Status**: Pending
- **Priority**: P0

## Overview
Fix 3 bugs trong mission-dispatcher.js để ensure đa luồng + HÀN BĂNG threshold.

## Key Insights
- Line 62 có thể có bypass logic cần xóa
- mandatePrefix phải apply cho MỌI prompt (không có exception)
- HÀN BĂNG threshold phải >= 25 để tránh over-throttle

## Requirements

### Bug #10: Verify line 62 bypass xóa
- **Location**: Line 62
- **Expected**: Bypass đã bị remove
- **Action**: Verify comment shows "REMOVED bypass"

### Bug #11: Verify đa luồng mandatePrefix mọi prompt
- **Location**: Line 102 (mandatePrefix definition)
- **Expected**: mandatePrefix được apply cho tất cả branches
- **Action**: Verify không có `if (safe.includes('/cook')) return safe;`

### Bug #12: Verify HÀN BĂNG >= 25
- **Location**: Lines 91-95 (HÀN BĂNG logic)
- **Expected**: Threshold >= 25
- **Action**: Verify `if (load > 25 || overheat)`

## Architecture

### Prompt Building Flow
```
buildPrompt()
  → Clean input
  → Load memory context
  → Build mandatePrefix (ALWAYS)
  → Detect intent
  → Return ClaudeKit command with mandatePrefix
```

**CRITICAL**: NO bypass paths. Every prompt gets mandatePrefix.

## Related Code Files

**Verify**:
- `lib/mission-dispatcher.js`

**Reference**:
- `lib/m1-cooling-daemon.js` (isOverheating)

## Implementation Steps

1. **Verify Bug #10 — Line 62 Bypass Removed**
   ```javascript
   // Line 62 should have:
   // 🔒 Chairman Fix: REMOVED bypass — ALL prompts MUST go through mandatePrefix
   // OLD BUG: if (safe.includes('/cook')) return safe; ← SKIPPED all multi-thread mandates!

   // VERIFY: No early return before mandatePrefix
   ```

   **Expected**: ✅ Comment shows bypass removed

2. **Verify Bug #11 — Đa Luồng MandatePrefix**
   ```javascript
   // Line 102 — mandatePrefix definition
   const mandatePrefix = `${memoryPrefix}${adaptiveMandate}${claudekitEnforcement}`;

   // VERIFY all return statements include mandatePrefix:
   // Line 108: return `${mandatePrefix}/cook ...`
   // Line 112: return `${mandatePrefix}/debug ...`
   // Line 114: return `${mandatePrefix}/review ...`
   // Line 116: return `${mandatePrefix}/plan:parallel ...`
   // Line 119: return `${mandatePrefix}/debug ...`
   // Line 120: return `${mandatePrefix}/review ...`
   // Line 122: return `${mandatePrefix}/cook ...`
   ```

   **Expected**: ✅ ALL returns use mandatePrefix

3. **Verify Bug #12 — HÀN BĂNG >= 25**
   ```javascript
   // Lines 91-95 should have:
   if (load > 25 || overheat) {
     adaptiveMandate = 'HÀN BĂNG MODE: Máy rất nóng — Chỉ dùng TỐI ĐA 3 subagents parallel...';
   } else {
     adaptiveMandate = 'COMMANDER RULE 13: ... 10+ agents nếu cần ...';
   }
   ```

   **Expected**: ✅ Threshold is 25 (not lower)

4. **Syntax Check**
   ```bash
   node -e "require('./lib/mission-dispatcher.js')"
   ```

## Todo List
- [ ] Verify Bug #10 — Line 62 bypass removed ✅
- [ ] Verify Bug #11 — All returns use mandatePrefix ✅
- [ ] Verify Bug #12 — HÀN BĂNG threshold = 25 ✅
- [ ] Syntax check passes
- [ ] Code review confirms no bypass paths

## Success Criteria
- ✅ Line 62 shows "REMOVED bypass" comment
- ✅ Zero early returns before mandatePrefix
- ✅ All 7 return statements include mandatePrefix
- ✅ HÀN BĂNG threshold = 25
- ✅ No syntax errors
- ✅ Code review passes

## Risk Assessment
**Zero Risk** — Pure verification phase, no code changes.

**If Issues Found**:
- Document exact problem
- Create fix in this phase
- Re-verify syntax

## Security Considerations
N/A — Verification only.

## Next Steps
- If all verified ✅ → Proceed to Phase 5
- If issues found → Fix in this phase before proceeding
