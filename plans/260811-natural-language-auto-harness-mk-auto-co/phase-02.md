# Phase 02 — 01.02

**Date:** 260811 · **Status:** pending

## Task
Build DAG state machine (~250 lines): Node/Edge classes, topological execution, checkpoint/resume to ~/.mekong/state, retry ≤3 per node, budget enforcement (max 20 nodes, 60 LLM calls), parallel execution for independent nodes. Persist state after each node.

## Files

- core/graph.py

## Acceptance criteria

Graph executes 5-node DAG with 2 parallel branches; resume from checkpoint after simulated crash replays from last completed node; budget exceeded raises BudgetExceeded; retry logic retries failed node 3x then marks failed
