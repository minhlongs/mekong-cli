---
name: sandbox
description: >-
  🛡️ Secure Sandboxed Agent Execution — run untrusted commands in isolated container or restricted subprocess sandbox.
---

# /sandbox — Secure Sandboxed Agent Execution

Provides containerized isolation and restricted process sandboxing for executing
untrusted commands, external tools, and agent file modifications safely.

## Usage

```bash
# Check container sandbox daemon availability and status
mekong sandbox status
mekong sandbox status --json

# Run a command inside an isolated container sandbox
mekong sandbox run "python -c 'print(1+1)'"

# Run command with customized image and resource limits
mekong sandbox run "pytest tests/" --image python:3.11-slim --timeout 60 --memory 1024

# Output machine-readable JSON telemetry
mekong sandbox run "ls -la" --json
```

## Features

1. **Dual Container & Process Fallback**:
   - Uses local Docker or Podman engine when available for OS-level kernel isolation.
   - Falls back gracefully to sanitized subprocesses with scrubbed environment variables and CPU timeouts when Docker is absent.
2. **Resource & Filesystem Quotas**:
   - Memory limits (default: 512MB) and CPU quotas.
   - Execution timeouts with automated process termination on breach.
   - Read-only root filesystem with dedicated workspace volume mounts.
3. **Gateway Real-Time Streaming**:
   - Emits `sandbox_started`, `sandbox_completed`, and `sandbox_failed` events over the Gateway SSE/WS streaming hub.

## Options

- `command`: The shell command string to execute in the isolated sandbox.
- `-i, --image`: Container image to run (default: `python:3.11-slim`).
- `-t, --timeout`: Execution timeout in seconds (default: `30s`).
- `-m, --memory`: Memory quota in megabytes (default: `512MB`).
- `--json`: Output machine-readable JSON telemetry.
