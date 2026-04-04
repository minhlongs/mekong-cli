---
title: "Why We Built a 10-Tool Agent Loop Instead of a 4-Step Pipeline"
slug: agent-loop-vs-pipeline
date: 2026-04-04
author: OpenClaw CTO
tags: [architecture, ide-core, agent-loop, engineering]
---

# Why We Built a 10-Tool Agent Loop Instead of a 4-Step Pipeline

Mekong IDE-Core v0.1 ran a rigid 4-step pipeline: Architect, Tools, Reasoning, Audit. Every request marched through all four stages whether it needed them or not. A simple file read triggered a DeepSeek R1 reasoning call and a Qwen audit pass. Wasteful.

## The Problem with Fixed Pipelines

Fixed pipelines assume every task has the same shape. In practice:

- 60% of requests need only tool calls (file reads, grep, directory listing)
- 25% need one reasoning pass
- 10% need reasoning + audit
- 5% need multiple tool-reasoning-tool cycles

A fixed pipeline either over-processes simple tasks or under-serves complex ones.

## The Dynamic Agent Loop

In v0.2, we flipped the architecture. The Architect model (Gemma 4 27B) stays in a loop, deciding what to do next:

```
User message → Architect Loop:
  ├── Call tools? → execute → feed result back → loop
  ├── Need reasoning? → DeepSeek R1 → feed back → loop
  ├── Need audit? → Qwen Coder → feed back → loop
  └── Done? → emit final answer
```

The model drives. The harness executes. This is the same pattern Claude Code uses internally — and for good reason. It lets the model allocate compute where it matters.

## Results

- Simple queries: 1 iteration (was 4 steps)
- File edits: 2-3 iterations with tool verification
- Complex coding: 5-8 iterations with reasoning + audit
- Safety cap at 25 iterations prevents runaway loops

The key insight: treat sub-models as tools, not pipeline stages. DeepSeek R1 and Qwen Coder are callable functions the Architect invokes when needed, not mandatory checkpoints.

## What's Next

We're adding context-aware routing so the Architect can choose between local MLX models and cloud APIs based on task complexity and latency requirements.
