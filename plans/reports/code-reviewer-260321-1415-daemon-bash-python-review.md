# Code Review: Daemon System (doanh-trai-daemon.sh + brain_think.py)

## Scope
- Files: `scripts/doanh-trai-daemon.sh` (342 lines), `scripts/brain_think.py` (163 lines)
- Focus: Bash compatibility, error handling, race conditions, retry logic, edge cases

## Overall Assessment: 6/10
Functional but has a **critical Bash compatibility bug**, several medium-severity logic errors, and missing edge case handling.

---

## CRITICAL Issues

### 1. `declare -A` requires Bash 4+ -- but `local` used inside main loop body (line 224)
**Lines 51, 190:** `declare -A RESPAWN_COUNT` and `declare -A DEPT_SESSION DEPT_PANES DEPT_TASKS DEPT_TASK_IDX` use associative arrays (Bash 4+).

**Mitigation:** Shebang is `#!/opt/homebrew/bin/bash` which is Bash 5.x on Homebrew. This is correct for macOS -- system `/bin/bash` is 3.2 but Homebrew bash is 5.x. **No bug here if users always invoke via the shebang.** However, if anyone runs `bash scripts/doanh-trai-daemon.sh` and their PATH resolves to `/bin/bash` (3.2), it will fail silently -- associative arrays degrade to regular arrays with no error in Bash 3.2.

**Recommendation:** Add a version guard at top:
```bash
if ((BASH_VERSINFO[0] < 4)); then
  echo "[FATAL] Requires bash 4+. Got: $BASH_VERSION" >&2; exit 1
fi
```

### 2. `local` keyword used outside function (line 224, 305, 307)
**Line 224:** `local rc="${RESPAWN_COUNT[${session}-${pane_idx}]:-0}"` -- this is inside the `while true` + `for` loop body, NOT inside a function. `local` outside a function is a **bash error** in strict mode and undefined behavior in POSIX.

**Line 305:** `local cooldown_file=...` -- same issue.
**Line 307:** `local cd_age=...` -- same issue.

**Impact:** In bash 5.x, `local` outside a function emits a warning but still creates the variable. With `set -u` (which IS set on line 8), this may not crash but produces undefined scoping. The variable leaks to global scope anyway, making `local` misleading.

**Fix:** Remove `local` from lines 224, 305, 307 or extract these blocks into functions.

---

## HIGH Priority

### 3. `IFS='|||'` does NOT split on `|||` as a delimiter (lines 278, 317)
`IFS='|||'` sets IFS to the **characters** `|`, not the string `|||`. This means `read -ra task_arr` splits on ANY single `|` character, not the 3-pipe delimiter. Since the YAML parser on line 83 joins with `|||`, a task containing a single `|` would be incorrectly split.

**Fix options:**
- Change Python separator to something unlikely in task text (e.g., `\x1f` unit separator)
- Or parse differently: `readarray -t task_arr < <(echo "${DEPT_TASKS[$dept_name]}" | sed 's/|||/\n/g')`

### 4. Race condition in pane lock (lines 118-124)
`acquire_pane_lock` is not atomic -- TOCTOU race between checking `[[ -f "$lock_file" ]]` and `touch "$lock_file"`. Two daemon instances (or rapid cycles) could both pass the check and both acquire.

**Impact:** Low in practice (single daemon process, sequential loop), but if the script is accidentally double-started, two daemons dispatch to the same pane.

**Mitigation:** Use `mkdir` as an atomic lock primitive or `flock`.

### 5. Python retry with exponential backoff -- timeout not adjusted (line 36)
`call_ollama()` uses `timeout=30` for the thinking-mode call (line 145) and retries 3 times with backoff (1s, 2s, 4s waits). Worst case: 3 x 30s timeout + 1+2+4s = **97 seconds** blocking the main loop for a single pane dispatch.

**Impact:** With multiple departments and panes, a down Ollama server stalls the entire daemon for minutes per cycle.

**Recommendation:** Reduce retries for the daemon use case or add a total-timeout cap. Consider `retries=2, timeout=15` for think=False call.

### 6. Respawn counter reset happens even when panes are still dead (line 335-337)
Every `RESPAWN_RESET_CYCLES` (10 cycles = ~20 min), ALL respawn counters reset to 0. If a pane is genuinely dead (e.g., session crashed permanently), the daemon will attempt 5 more respawns every 20 minutes indefinitely -- generating noise.

**Better approach:** Only reset counters for panes that have had at least one successful health check since last reset.

---

## MEDIUM Priority

### 7. `set -uo pipefail` but no `-e` (line 8)
`-e` (errexit) is intentionally omitted, which is fine for a daemon. But `-u` (nounset) combined with `${RESPAWN_COUNT[${session}-${pane_idx}]:-0}` may behave unexpectedly -- in Bash 4+, accessing an unset associative array key with `:-` default DOES work, but in some edge cases with `-u`, accessing the array itself before any key is set can trigger nounset errors.

**Tested:** Works correctly in Bash 5.x. Low risk but worth noting.

### 8. Log rotation race (lines 62-64)
`wc -l < "$LOG_FILE"` followed by `tail ... > .tmp && mv .tmp` is not atomic. If the daemon writes a log line between `tail` and `mv`, that line is lost.

**Impact:** Minimal -- one log line lost per rotation. Acceptable for this use case.

### 9. `brain_think.py` swallows Strategy 1 errors silently (line 141)
```python
except Exception:
    pass  # Timeout expected -- fall through to thinking mode
```
All exceptions (not just timeout) are silently swallowed, including JSON decode errors, connection refused, DNS failures. These should at least log to stderr for debugging.

### 10. File size: daemon.sh at 342 lines exceeds 200-line limit
Per project rules, files should be under 200 lines. Consider extracting:
- Startup validation into `daemon-validate.sh`
- Brain dispatch + task routing into `daemon-dispatch.sh`

---

## LOW Priority

### 11. `stat -f %m` is macOS-specific (lines 119, 307)
Linux `stat` uses `stat -c %Y`. This daemon is macOS-only (Homebrew bash shebang) so not a portability issue, but worth a comment.

### 12. `grep -c` returns exit code 1 when count is 0 (line 270)
`daily_usage=$(grep -c "^${today}" "$API_USAGE_FILE" 2>/dev/null || echo 0)` -- correctly handled with `|| echo 0`. Good.

### 13. Python `CMD_NAMES` regex is a single alternation string (line 14-32)
Works but is fragile -- adding a new command requires updating a long regex. Consider loading from a config file or the command catalog JSON.

---

## Edge Cases Found

1. **Empty YAML config:** `parse_departments()` returns nothing, `while read` loop processes zero lines, `DEPT_SESSION` is empty -- daemon runs but does nothing. No error logged for "0 departments loaded."
2. **Ollama not running at startup:** No pre-check. First `brain_dispatch_dept` call will retry 3x with backoff, blocking loop for ~97s. `warmup-ollama.sh` failure is logged as WARN but daemon continues.
3. **Task array with empty elements:** `|||` split produces empty strings between delimiters. Lines 282 and 322 check for empty task but only after assignment -- the task index still advances, potentially skipping real tasks in the rotation.
4. **Pane output contains ANSI escape codes:** `is_pane_idle()` grep patterns may fail to match prompts obscured by color/cursor codes. Consider stripping ANSI before matching.
5. **API usage file grows unbounded:** `$API_USAGE_FILE` has no rotation -- every dispatch appends a line forever.

---

## Positive Observations
- `startup_validate()` checks all dependencies upfront -- good fail-fast pattern
- YAML parsing properly uses `yaml.safe_load` (not `yaml.load`)
- Two-strategy approach in brain_think.py (think:false first, then thinking mode) is clever
- Lock timeout prevents permanent lock starvation
- Context percentage detection and auto-compact is a useful daemon feature
- API budget tracking with daily limits prevents runaway costs

---

## Recommended Actions (Priority Order)
1. **Remove `local` from non-function scope** (lines 224, 305, 307) -- syntax error risk
2. **Add Bash version guard** -- prevents silent failures on system bash
3. **Fix `IFS='|||'` splitting** -- use unit separator or readarray+sed
4. **Cap total retry time** in brain_think.py for daemon use case
5. **Log Strategy 1 exceptions** in brain_think.py instead of silent pass
6. **Add "0 departments" warning** after parse loop
7. **Add API usage file rotation** alongside log rotation
8. **Consider file size split** to meet 200-line rule

---

## Metrics
- Bash compatibility: Bash 5+ required (shebang correct, but no version guard)
- File sizes: daemon.sh 342 lines (over limit), brain_think.py 163 lines (OK)
- Error handling: 7/10 -- good in Python, gaps in bash
- Security: No injection risks found (no eval, no user-controlled shell expansion)

---

## Unresolved Questions
1. Is the daemon ever invoked via `bash scripts/doanh-trai-daemon.sh` (PATH bash) vs `./scripts/doanh-trai-daemon.sh` (shebang bash)? This determines severity of the version guard issue.
2. Are `dept-task-runner.sh`, `warmup-ollama.sh`, `reset-full-panes.sh` expected to exist at review time? They exist on disk but were not part of the changed files -- unclear if they are new or pre-existing.
3. Should the daemon have a PID file / single-instance guard to prevent double-start (which would cause the lock race in issue #4)?
