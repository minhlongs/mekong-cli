# Phase 1: Rewrite Expect Dispatch Script

## Context Links
- [Parent Plan](plan.md)
- [Research: ANSI Detection](research/researcher-01-expect-ansi-ipc.md)
- Current file: `scripts/tom-hum-dispatch.exp` (167 lines → rewrite)

## Overview
- **Priority:** P1 (critical path)
- **Status:** pending
- **Description:** Complete rewrite of the expect script with prompt-return detection, persistent CC CLI, and auto-respawn on crash

## Key Insights
- CC CLI `❯` prompt is UTF-8 `\xe2\x9d\xaf`, wrapped in ANSI color codes
- Idle detection (25s silence) fails because Opus thinking is 60-120s silent
- Must spawn CC CLI ONCE and keep it alive across all missions
- On crash/eof, respawn with `--continue` to resume conversation context

## Requirements

### Functional
- Spawn CC CLI once at startup, keep alive forever
- Read missions from `/tmp/tom_hum_next_mission.txt`
- Detect mission completion by `❯` prompt return (ANSI-aware regex)
- Write "done" to `/tmp/tom_hum_mission_done` on completion
- Auto-respawn CC CLI with `--continue` on crash (eof detection)
- 45-minute timeout per mission (safety net)
- Log all significant events to log file

### Non-Functional
- Must handle 60-120s silent thinking without false completion
- Debounce prompt detection: wait 500ms after `❯` to confirm
- Minimal CPU usage during idle polling (3s sleep between mission checks)

## Architecture

```
┌─────────────────────────────────────────────┐
│  tom-hum-persistent-dispatch.exp            │
│                                             │
│  1. spawn claude --dangerously-skip-perms   │
│  2. wait for initial ❯ prompt               │
│  3. LOOP:                                   │
│     a. poll /tmp/tom_hum_next_mission.txt   │
│     b. if exists → read, delete, send       │
│     c. expect {                             │
│        ❯ prompt → write done signal         │
│        eof → respawn with --continue        │
│        timeout 2700 → write timeout signal  │
│     }                                       │
│     d. back to polling                      │
└─────────────────────────────────────────────┘
```

## Related Code Files
- **Modify:** `scripts/tom-hum-dispatch.exp` → rewrite entirely
- **New file:** `scripts/tom-hum-persistent-dispatch.exp` (if keeping old as backup)

## Implementation Steps

1. **Define constants and args parsing**
   ```tcl
   set default_dir [lindex $argv 0]
   set log_file [lindex $argv 1]
   set mission_file "/tmp/tom_hum_next_mission.txt"
   set done_file "/tmp/tom_hum_mission_done"
   set cli_model "claude-opus-4-6-thinking"
   ```

2. **Create `spawn_cli` proc with crash recovery**
   ```tcl
   proc spawn_cli {is_resume} {
       global spawn_id default_dir cli_model
       cd $default_dir
       if {$is_resume} {
           spawn claude --model $cli_model --dangerously-skip-permissions --continue
       } else {
           spawn claude --model $cli_model --dangerously-skip-permissions
       }
   }
   ```

3. **Create `wait_for_prompt` proc — ANSI-aware ❯ detection**
   ```tcl
   proc wait_for_prompt {timeout_secs} {
       # Match ❯ (UTF-8 \xe2\x9d\xaf) anywhere in output
       # This works regardless of ANSI color wrapping
       set result 0
       expect {
           -re {\xe2\x9d\xaf} {
               # Debounce: wait 500ms to confirm no more output
               after 500
               set result 1
           }
           -re {>\s*$} {
               after 500
               set result 1
           }
           eof {
               set result -1
           }
           -timeout $timeout_secs {
               set result 0
           }
       }
       return $result
   }
   ```

4. **Main mission loop**
   - Poll for mission file every 3s
   - On mission found: read, delete file, send to CC CLI
   - Enter completion detection loop:
     - Use `expect` with ANSI ❯ pattern
     - On match → debounce 500ms → write done file → break
     - On eof → respawn with --continue, write "crash" to done file
     - On timeout (2700s) → write "timeout" to done file → break
   - Continue polling

5. **Output logging**
   - Log interesting patterns (Bash, Read, Error, etc.) during execution
   - Strip ANSI for log readability
   - Status log every 60s with elapsed time

6. **Crash recovery loop**
   - Wrap entire main flow in outer while{1}
   - On eof/crash → log, respawn with --continue
   - Track respawn count, max 5 respawns per hour

## Todo List
- [ ] Write new expect script with prompt detection
- [ ] Test ❯ detection with CC CLI manually
- [ ] Test crash recovery (kill claude process, verify respawn)
- [ ] Test 60s+ silent thinking doesn't trigger false completion
- [ ] Verify file IPC works correctly with task-watcher

## Success Criteria
- CC CLI spawns once and stays alive across multiple missions
- `❯` prompt return correctly detected after each mission
- 120s silent thinking does NOT trigger false completion
- CC CLI auto-respawns with `--continue` after crash
- Done signal reliably written to `/tmp/tom_hum_mission_done`

## Risk Assessment
- **Risk:** `❯` character might not appear in some CC CLI versions
  - **Mitigation:** Also match `>` at end of line as fallback
- **Risk:** ANSI sequences may vary between terminal contexts
  - **Mitigation:** Match raw UTF-8 bytes of `❯`, not ANSI wrappers
- **Risk:** Respawn loop if CC CLI keeps crashing
  - **Mitigation:** Max 5 respawns/hour, exponential backoff

## Security Considerations
- API key passed via environment variable, not command line
- No secrets in expect script itself
- Log file should not contain API keys

## Next Steps
- Phase 2: Rewrite task-watcher.js to use atomic file IPC
