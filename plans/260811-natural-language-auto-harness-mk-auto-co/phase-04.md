# Phase 04 — 01.04

**Date:** 260811 · **Status:** pending

## Task
Wire router → graph → gate protocol. Implement mk auto command with --resume (load ~/.mekong/state) and --decision (provide gate decision). Exit 42 on gate block, 0 on success, 1 on error. Handle CLI args and stdin input.

## Files

- commands/auto.py

## Acceptance criteria

mk auto 'deploy service' runs full pipeline; mk auto --resume continues from checkpoint; mk auto --decision approve bypasses gate; exit codes 0/1/42 verified in integration test
