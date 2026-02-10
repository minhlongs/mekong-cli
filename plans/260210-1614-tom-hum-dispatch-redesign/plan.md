---
title: "Tôm Hùm Dispatch Redesign — Persistent CC CLI + ANSI Prompt Detection"
description: "Rewrite task-watcher.js and dispatch.exp with prompt-return detection, persistent CLI, and launchd auto-restart"
status: complete
priority: P1
effort: 3h
branch: master
tags: [openclaw, tom-hum, dispatch, expect, launchd]
created: 2026-02-10
---

# Tôm Hùm Dispatch Redesign

## Problem Statement

Current system has 3 critical flaws:
1. **Idle detection triggers early** — 25s silence × 3 = done, but Opus 4.6 thinks 60-120s silently
2. **CC CLI killed/respawned per mission** — wastes context, slow restarts
3. **No ANSI prompt detection** — guessing completion instead of detecting `❯` prompt return

## Solution

Rewrite both files from scratch:
- **Expect script**: Spawn CC CLI once, detect `❯` prompt return via ANSI-aware regex
- **Task watcher**: Clean Node.js orchestrator with atomic file IPC, graceful lifecycle
- **launchd plist**: Auto-restart task-watcher on crash/login

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Rewrite expect dispatch script | code-complete | [phase-01](phase-01-rewrite-expect-dispatch.md) |
| 2 | Rewrite task-watcher.js | code-complete | [phase-02](phase-02-rewrite-task-watcher.md) |
| 3 | Add launchd plist + install script | code-complete | [phase-03](phase-03-launchd-auto-restart.md) |

## Code Review

- **Report:** [code-reviewer-260210-1630-tom-hum-dispatch-redesign.md](../reports/code-reviewer-260210-1630-tom-hum-dispatch-redesign.md)
- **Verdict:** SOLID implementation. 2 high-priority items FIXED:
  1. ~~API key not available when running via launchd~~ → reads `~/.mekong/api-key` fallback
  2. ~~`pkill -x claude` kills ALL claude processes~~ → documented as intentional (personal tool)

## Key Architecture Decisions

1. **Prompt detection over idle detection**: Match `❯` (UTF-8 `\xe2\x9d\xaf`) in expect output
2. **File IPC protocol**: Atomic write (tmp+rename) for mission delivery, touch-file for done signal
3. **Single CC CLI process**: Spawn once with `--dangerously-skip-permissions`, respawn with `--continue` on crash
4. **launchd for task-watcher**: Native macOS, KeepAlive, zero dependencies

## Dependencies

- `expect` (pre-installed macOS)
- `node` (pre-installed)
- `claude` CLI (installed)
- Antigravity Proxy running on port 8080

## Research

- [Expect ANSI & IPC](research/researcher-01-expect-ansi-ipc.md)
- [launchd & Process Mgmt](research/researcher-02-launchd-process-mgmt.md)
