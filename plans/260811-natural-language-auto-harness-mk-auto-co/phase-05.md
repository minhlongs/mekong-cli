# Phase 05 — 01.05

**Date:** 260811 · **Status:** pending

## Task
Implement agent dispatch: node-level LLM calls using 1M context model. Tool whitelist enforcement (read, write, cat, bash-test only). Tool executor with timeout and output capture.

## Files

- core/dispatch.py
- core/tools.py

## Acceptance criteria

Dispatch calls LLM with node context + tool results; bash-test tool executes and returns stdout/stderr; disallowed tool (e.g., rm -rf) raises ToolNotAllowed; 1M token context handled without truncation
