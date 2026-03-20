---
description: "Execute a shell command safely with timeout and error handling"
argument-hint: [command]
---

# /worker-exec — Worker Operation

Run a shell command with safety guards.

1. Validate command is safe (no rm -rf, no force operations)
2. Execute with timeout
3. Capture and report output
4. Handle errors gracefully
