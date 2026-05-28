---
name: "source-command-worker-exec"
description: "Execute a shell command safely with timeout and error handling"
---

# source-command-worker-exec

Use this skill when the user asks to run the migrated source command `worker-exec`.

## Command Template

# /worker-exec — Worker Operation

Run a shell command with safety guards.

1. Validate command is safe (no rm -rf, no force operations)
2. Execute with timeout
3. Capture and report output
4. Handle errors gracefully
