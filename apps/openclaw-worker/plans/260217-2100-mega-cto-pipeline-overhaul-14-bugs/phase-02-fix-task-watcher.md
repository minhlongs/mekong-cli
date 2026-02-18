# Phase 2: Fix Group A - Task Watcher

## Context
- **Parent Plan**: [plan.md](plan.md)
- **Dependencies**: Phase 1 must complete
- **Status**: Pending
- **Priority**: P0

## Overview
Fix 3 bugs trong task-watcher.js để tăng tốc độ scan và ngăn duplicate dispatch.

## Key Insights
- POLL_INTERVAL hiện tại có thể quá chậm
- Task files không được move ngay sau dispatch → detect lại
- Priority queue chưa implement

## Requirements

### Bug #1: Scan interval quá chậm
- **Current**: Unknown (từ Phase 1)
- **Expected**: <= 5000ms (5s MAX)
- **Fix**: Giảm interval xuống 5s hoặc thấp hơn

### Bug #2: DUPLICATE DISPATCH
- **Current**: Task file không move sau dispatch
- **Expected**: mv sang processed/ NGAY SAU dispatch
- **Fix**: Add `fs.renameSync()` ngay sau `executeTask()`

### Bug #3: Task priority
- **Current**: FIFO only
- **Expected**: CRITICAL > HIGH > MEDIUM > (no prefix)
- **Fix**: Sort queue by priority prefix

## Architecture

### Current Flow
```
watchDir → detect file → add to queue → dispatch → (no move!)
```

### Fixed Flow
```
watchDir → detect file → sort by priority → dispatch → move to processed/
```

## Related Code Files

**Modify**:
- `task-watcher.js`

**Reference** (no changes):
- `config.js` (POLL_INTERVAL_MS, TASK_PATTERN)

## Implementation Steps

1. **Fix Bug #1 — Scan Interval**
   ```javascript
   // Before (assumed)
   const scanInterval = 10000; // or from config

   // After
   const scanInterval = Math.min(config.POLL_INTERVAL_MS || 5000, 5000);
   ```

2. **Fix Bug #2 — Immediate Move**
   ```javascript
   // After executeTask() completes
   const result = await executeTask(content, filename);

   // ADD THIS:
   const processedPath = path.join(config.PROCESSED_DIR, filename);
   fs.renameSync(filepath, processedPath);
   log(`MOVED: ${filename} → processed/`);
   ```

3. **Fix Bug #3 — Priority Queue**
   ```javascript
   // Sort queue before dispatch
   function getPriority(filename) {
     if (filename.startsWith('CRITICAL_')) return 0;
     if (filename.startsWith('HIGH_')) return 1;
     if (filename.startsWith('MEDIUM_')) return 2;
     return 3; // LOW or no prefix
   }

   queue.sort((a, b) => getPriority(a) - getPriority(b));
   ```

4. **Verify Syntax**
   ```bash
   node -e "require('./task-watcher.js')"
   ```

## Todo List
- [ ] Fix Bug #1 — Update scan interval <= 5s
- [ ] Fix Bug #2 — Add fs.renameSync() after dispatch
- [ ] Fix Bug #3 — Implement priority sorting
- [ ] Verify `node -e require` passes
- [ ] Test with sample mission files
- [ ] Document changes in comments

## Success Criteria
- ✅ Scan interval <= 5s
- ✅ Task files moved immediately after dispatch
- ✅ CRITICAL missions execute before HIGH/MEDIUM
- ✅ No syntax errors
- ✅ Zero duplicate dispatch in test run

## Risk Assessment
**Low Risk** — Simple logic changes, well-defined fixes.

**Mitigation**:
- Keep original values in comments
- Test with 3 sample files (CRITICAL, HIGH, MEDIUM)
- Verify processedPath exists before move

## Security Considerations
- Validate filename before fs.renameSync() to prevent path traversal
- Check file exists before move

## Next Steps
- Proceed to Phase 3 after verification
- Monitor first 10 missions for duplicate detection
