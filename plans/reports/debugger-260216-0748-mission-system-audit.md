# Mission System Audit Report - 260216

## Executive Summary
Audit of `mission-complexity-classifier.js`, `mission-journal.js`, and `token-tracker.js` revealed several critical edge cases, primarily around token tracking across UTC midnight boundaries and potential self-reinforcing failure loops in the autonomous audit system.

## Technical Analysis

### 1. Token Tracker: Midnight Boundary Bug
**File:** `apps/openclaw-worker/lib/token-tracker.js`
**Issue:** The `countTokensBetween` function uses simple string comparison of HH:mm:ss timestamps.
**Impact:** If a mission starts before UTC midnight and ends after (e.g., 23:55 to 00:05), the comparison `timeStr >= startHMS && timeStr <= endHMS` will fail for all log entries, reporting 0 tokens used. This directly affects the efficiency score and project priority logic.

### 2. Mission Journal: Self-Reinforcing Failure Loops
**File:** `apps/openclaw-worker/lib/mission-journal.js`
**Issue:** `analyzePatterns` triggers a "Deep Audit" mission if a project fails 3 times in the last 20 missions.
**Risk:** If the environment or a core dependency is broken, audit missions will also fail. This can lead to a loop where failures trigger audits, which fail and contribute to the "3 failures" threshold, triggering more audits. While there is a check for *pending* audits, there is no cooling period for *completed* failed audits.

### 3. Efficiency Calculation: Type Safety & NaN
**File:** `apps/openclaw-worker/lib/mission-journal.js`
**Issue:** `efficiency` is calculated as `(data.tokensUsed / 1000) * (data.durationMs / 60000)`.
**Risk:** If `tokensUsed` or `durationMs` are missing or non-numeric (e.g., from a crashed mission where tokens couldn't be counted), `efficiency` becomes `NaN`. This `NaN` then propagates into `getProjectPriority`, potentially breaking the priority scoring for that project.

### 4. Resource Management: Sync Log Scraping
**File:** `apps/openclaw-worker/lib/token-tracker.js`
**Issue:** `readLinesSync` performs a synchronous full scan of `/tmp/proxy_11436.log` for every mission completion.
**Risk:** As the proxy log grows over days of continuous operation, these synchronous reads will block the main event loop of the Tôm Hùm daemon, potentially causing heartbeats or file watchers to lag.

### 5. Data Integrity: Silent History Reset
**File:** `apps/openclaw-worker/lib/mission-complexity-classifier.js` & `mission-journal.js`
**Issue:** `safeLoadHistory` resets the history to `[]` if JSON parsing fails.
**Impact:** While it creates a backup, the active system loses all "self-learning" context (adaptive timeouts, project priorities, efficiency trends). A single corrupted write (e.g., during a crash or power loss) wipes the AGI's "memory" of project performance.

## Actionable Recommendations

1.  **Fix Token Comparison:** Update `token-tracker.js` to parse dates or handle the wraparound case where `startHMS > endHMS`.
2.  **Audit Cooling Period:** Implement a cooldown in `mission-journal.js` to prevent creating a new audit mission if one was completed (regardless of success) within the last X hours for that project.
3.  **Efficiency Sanitization:** Ensure `tokensUsed` and `durationMs` are defaulted to 0 and check for `NaN` before recording to history.
4.  **Log Rotation/Streaming:** Implement rotation for `/tmp/proxy_11436.log` or maintain an index/offset to avoid scanning the whole file repeatedly.
5.  **Atomic Writes:** Use a temporary file and `fs.renameSync` for updating `mission-history.json` to prevent corruption during partial writes.

## Unresolved Questions
- Should the efficiency score weight tokens or time more heavily? Currently, they are weighted equally in the product.
- Is there a maximum size for the proxy log before it is manually cleared?
