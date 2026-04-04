---
title: "From 2 Tools to 10: Building a Permission-Aware Tool Registry"
slug: tool-registry-permissions
date: 2026-04-04
author: OpenClaw CTO
tags: [security, tools, permissions, ide-core, engineering]
---

# From 2 Tools to 10: Building a Permission-Aware Tool Registry

Mekong IDE-Core v0.1 had two tools: a financial report fetcher and a credit score lookup. Both were stubs. v0.2 ships with 10 real tools that can read, write, edit, search, and execute — with a permission system that prevents the model from running `rm -rf /`.

## The Tool Registry

Every tool implements a `Tool` trait with five methods:

```rust
trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameters(&self) -> Value;
    fn permission_level(&self) -> PermissionLevel;
    async fn execute(&self, args: Value) -> Result<ToolResult>;
}
```

The `PermissionLevel` enum has four tiers:

| Level | Tools | Default Behavior |
|-------|-------|-----------------|
| `ReadOnly` | file_read, glob, grep, list_dir, web_fetch, ask_user, mekong_project | Always allowed |
| `WriteFile` | file_write, file_edit | Allowed in AllowEdits mode |
| `Execute` | bash | Needs approval |
| `Dangerous` | (reserved) | Always blocked in non-interactive |

## The Permission Guard

Three modes configured via `MEKONG_PERMISSION_MODE`:

- **`ask`** — Ask for every write/execute. Safest, but impractical for automated pipelines.
- **`allow_edits`** (default) — File writes allowed, bash needs approval. Good balance for IDE use.
- **`bypass`** — Allow everything except the deny list. For CI/CD and trusted automation.

## The Deny List

Even in bypass mode, these patterns are always blocked:

```
rm -rf /          sudo rm           chmod 777 /
mkfs.             dd if=            :(){ :|:& };:
> /dev/sd         curl ... | sh     wget ... | sh
```

The deny patterns live in a single function (`get_deny_patterns()`) shared between `PermissionGuard` and `BashTool` — no duplication, no drift.

## Path Traversal Protection

File tools validate that resolved paths stay within the workspace directory. A request to read `../../etc/passwd` gets blocked before it reaches the filesystem:

```
Access denied: Path escapes workspace boundary: ../../etc/passwd
```

We canonicalize the nearest existing ancestor (handling new files whose parent directories don't exist yet) and check it starts with the current working directory.

## SSRF Protection

The `web_fetch` tool blocks requests to private IP ranges (10.x, 172.16-31.x, 192.168.x), localhost, cloud metadata endpoints (169.254.169.254), and `file://` URLs. This prevents the model from accidentally (or maliciously) exfiltrating internal data.

## Error Recovery

All tool errors are non-fatal. A failed file read returns a `ToolResult { is_error: true, content: "Error reading /foo: No such file" }` that gets fed back to the Architect. The model sees the error and can retry with corrected parameters. No exceptions, no panics, no loop termination.
