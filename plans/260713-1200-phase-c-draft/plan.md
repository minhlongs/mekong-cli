---
title: "Phase C — Agentic Core: Orchestration, Self-Healing, TUI UX, Learning"
description: "4 components that turn Phase B's agentic core into an autonomous system"
status: draft
priority: P1
effort: 4 weeks
branch: main
tags: [phase-c, agentic-core, orchestration, self-healing, tui]
created: 2026-07-13
---

# Phase C Plan: Agentic Core — Autonomy Layer

## Overview

Phase B delivers the agentic core (AgentFactory, MemoryBridge, PEV parser, NLU, usage tracker). Phase C turns it **autonomous**: components that survive failure, coordinate in swarm patterns, present real-time output in the terminal, and learn from every run.

4 components, sequential dependency chain: C2 → C3 → C1 → C4.

## Components

| ID | Name | One-liner | Depends on | Risk | Effort |
|------|------|-----------|-----------|------|--------|
| **C2** | TUI Streaming UX | Real-time streaming of agent output in the terminal, with progress panels and cancel support | `cli/tui/` (exists) | LOW | M |
| **C3** | Self-Healing Pipeline | Auto-retry with backoff, fallback providers, crash detection, and circuit breakers wired into PEV executor | B5 PEV Parser, `core/circuit_breaker.py` (scaffold) | MEDIUM | L |
| **C1** | Agent Orchestration | Swarm coordination: task delegation, result aggregation, supervisor loop — integrates AgentFactory into multi-agent workflows | B6 Agent Factory, C3 Self-Healing | HIGH | L |
| **C4** | Learning Loop | Agents persist execution outcomes, auto-tune retry thresholds, and surface failure patterns from usage history | B4 MemoryBridge, B7 Validation, C3 Self-Healing | MEDIUM | M |

## Dependency Graph

```
Phase B
 ├─ B4 MemoryBridge ─┐
 ├─ B5 PEV Parser ───┤
 ├─ B6 AgentFactory ─┤
 └─ B7 Integration ──┘
        │
        ▼
   Phase C
        │
        ▼
   C2 TUI Streaming UX ──────┐ (uses MemoryBridge for scrollback)
        │
        C3 Self-Healing Pipeline ───┐ (builds on PEV executor retry)
        │                          │
        C1 Agent Orchestration ─────┘ (builds on Factory + C3)
        │
        C4 Learning Loop ───────────┘ (builds on MemoryBridge + C1)

Note: C2 is independent of C1/C3/C4 — can run in parallel.
C3 must complete before C1. C4 runs last in parallel with C1.
```

## Acceptance Criteria

1. Terminal agent output streams in real-time — no more batch-dump on completion (`cli/tui/`).
2. PEV executor auto-retries on transient failures with exponential backoff; circuit breaker opens after N consecutive failures in a provider.
3. Multi-agent mode: a goal spawns a supervisor that delegates sub-tasks to specialized agents via AgentFactory and aggregates results.
4. Learning loop: after each execution, success/failure/retry-count is stored in MemoryBridge; patterns surface as warnings before retry storms.
5. All 4 components pass `pytest` in isolation AND in the Phase B end-to-end test: `goal → plan → execute → verify → remember`.

## Out of Scope

1. Voice input via Whisper (post-Phase C; requires audio pipeline in TUI that doesn't exist yet).
2. Cross-platform messaging (Telegram/Zalo webhook triggers — existing handlers in `core/telegram_*.py` are already wired, Phase C only adds agent-initiated dispatch).
3. Constitutional AI governance layer (ZenOS particle model — shipped separately as product-layer, not engine concern).
4. Distributed swarm across machines (single-process multi-agent only in Phase C; `core/swarm.py` multi-node remains future).
5. Fine-tuning or RAG over historical agent outcomes (Learning Loop stores + queries; no embedding re-training).
