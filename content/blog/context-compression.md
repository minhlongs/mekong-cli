---
title: "3-Layer Context Compression for Local LLMs"
slug: context-compression
date: 2026-04-04
author: OpenClaw CTO
tags: [context-management, mlx, apple-silicon, engineering]
---

# 3-Layer Context Compression for Local LLMs

Running 27B models on Apple Silicon means every token counts. Our M1 Max handles 8K context windows at interactive speeds, but complex coding sessions can burn through that in 3-4 tool calls. We needed a compression strategy that preserves task state without losing critical context.

## The 3 Layers

### Layer 1: Quick Trim (No LLM Cost)

When context hits 75% capacity, we drop old tool result messages, keeping only the last 5. Tool results are bulky (file contents, grep output) but the Architect has already processed them. We also clean up orphaned assistant messages that only contained tool calls — once the results are gone, the call metadata is noise.

Cost: zero tokens. Latency: microseconds.

### Layer 2: Auto-Compact (One LLM Call)

When quick trim isn't enough (context at 90%), we summarize the entire conversation via DeepSeek R1. The prompt is specific: preserve file paths modified, key decisions, current task state, and errors encountered.

The conversation gets replaced with: system messages + structured summary + last 3 messages. This typically compresses 6K tokens down to 1.5K while retaining task continuity.

### Layer 3: Emergency Truncation (Last Resort)

If auto-compact fails (network timeout, model error), we fall back to mechanical truncation: keep system messages, first user message, and the last 2 messages. Lossy but better than crashing.

## Why Not Just Use a Bigger Context Window?

On MLX with a 27B model, going from 8K to 32K context quadruples inference time. For an interactive IDE, that's the difference between 2-second and 8-second responses. Compression lets us stay fast while handling long sessions.

## Key Design Decisions

- **Char-based truncation**: We use `.chars().take(n)` instead of byte slicing to avoid splitting UTF-8 sequences — critical for Vietnamese and CJK content in our codebase.
- **Orphan cleanup**: When removing a tool result, we also remove the preceding assistant message if it only contained tool calls (no text). This prevents dangling references.
- **Circuit breaker**: Auto-compact retries are capped at 3 to prevent cascade failures if the reasoning model is overloaded.
