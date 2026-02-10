# Research: Expect ANSI Detection & File IPC

## 1. ANSI Escape Sequence Detection in Expect

CC CLI prompt `❯` is wrapped in ANSI color codes. Typical pattern:
```
\x1b[32m❯\x1b[0m   (green prompt)
\x1b[?2004h        (bracketed paste mode)
```

**Best expect regex pattern:**
```tcl
# Match ❯ preceded by any ANSI escape sequences
-re {\x1b\[[0-9;]*m[^\x1b]*❯}
# Or more broadly — match the raw UTF-8 bytes for ❯ (E2 9D AF)
-re {\xe2\x9d\xaf}
```

Key insight: `expect` works on raw byte streams, so matching the UTF-8 bytes of ❯ (`\xe2\x9d\xaf`) is most reliable regardless of ANSI wrapping. Match the character itself, strip ANSI separately.

**Robust pattern strategy:** Match `❯` OR `>` at line end after stripping ANSI, with a small delay to confirm no more output follows (200ms debounce).

## 2. Why Idle Detection Fails for LLM Tools

Current code: 25s silence × 3 checks = ~75s idle → "done"
Problem: CC CLI Opus 4.6 thinking can be 60-120s silent while reasoning.

**Solution: Prompt-return detection (gold standard)**
- CC CLI prints `❯` when ready for next input
- This is deterministic — no guessing
- Combine with debounce: wait 500ms after seeing `❯` to confirm it's the real prompt (not echoed text)

## 3. Persistent Process in Expect

Best practices:
- Use `while {1}` loop with `expect` inside
- Handle `eof` to detect process death → auto-respawn
- `catch {spawn ...}` for error-safe spawning
- Set `timeout -1` during idle polling (no timeout)
- Use `exp_internal 0` to suppress debug noise

**Auto-respawn pattern:**
```tcl
proc spawn_cli {} {
    global spawn_id
    spawn claude --dangerously-skip-permissions --resume
    # wait for prompt
}
# In main loop, on eof:
expect {
    eof { spawn_cli; exp_continue }
}
```

## 4. File-Based IPC (Node.js ↔ Expect)

**Atomic write pattern:**
```javascript
// Write to temp file, then rename (atomic on same filesystem)
fs.writeFileSync('/tmp/tom_hum_next_mission.txt.tmp', content);
fs.renameSync('/tmp/tom_hum_next_mission.txt.tmp', '/tmp/tom_hum_next_mission.txt');
```

**Expect side — poll with non-blocking check:**
```tcl
if {[file exists $mission_file]} {
    set f [open $mission_file r]
    set data [read $f]
    close $f
    file delete -force $mission_file
}
```

Race condition prevention:
- Writer: write to .tmp then rename
- Reader: read then delete
- Order: writer creates → reader reads → reader deletes → writer creates next
