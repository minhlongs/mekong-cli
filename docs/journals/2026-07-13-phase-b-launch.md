# Phase B Launch & Warptask Complete

**Date**: 2026-07-13 12:16
**Severity**: High
**Component**: mekong-cli orchestration
**Status**: Ongoing

## What Happened

Warptask (plan `260712-1849-mekong-warptask`) completed: NL routing expanded to 48 commands, shadow fix applied to `route_ask()`, workflow docs expanded. Phase B full execution then launched — B2+B3 in parallel, B4+B5 in parallel, then B6 sequential, then B7. Phase C draft plan created at `plans/260713-1200-phase-c-draft/`. Deep parallel audit is running now (security, dependency graph, performance baseline, tech debt).

## The Brutal Truth

This session is a marathon, not a sprint. We shipped warptask successfully but the real pressure is Phase B dependency-correct chaining — getting the parallel/sequential ordering right means the difference between a clean run and a cascading failure. The deep audit running in parallel is our safety net, but it also signals we have accumulated tech debt we can't ignore.

## Technical Details

- NL routing now handles 48 commands via longest-match shadow fix in `route_ask()`
- `workflow.py` consolidated into single file (rejected splitting into 3 — YAGNI)
- Phase B chain: B2+B3 (parallel) → B4+B5 (parallel) → B6 (seq) → B7 (seq)
- Bash unavailability risk flagged: subagents cannot execute shell commands
- Pre-existing test failures in `260712-1849-warptui-interactive-layer` plan: Warptui layer 2 ruff tech-debt branch has test failures merged into main

## What We Tried

Longest-match shadow fix vs table reordering for NL routing. Longest-match won because table reordering would break command precedence semantics unpredictably.

Consolidating `workflow.py` vs splitting into 3 files. Consolidated won — split was premature abstraction with no measurable benefit.

## Root Cause Analysis

We had two competing routing strategies because the original NL router used exact-match. As command count grew past ~30, collisions became unavoidable. The shadow fix resolves collisions by picking the longest matching pattern, which is the correct tiebreaker semantically.

Phase B dependency ordering was guessed initially — B2+B3 independent, B4+B5 independent but both depend on B2+B3 completion, B6 needs B4+B5, B7 needs B6. This is correct but requires strict enforcement; one agent jumping ahead breaks the chain.

## Lessons Learned

- Always verify Bash availability before launching parallel subagents that need it
- Test failures should block plan merges — don't accept "we'll fix it later"
- Dependency graph should be explicit in plan.md, not inferred at execution time
- Longest-match is the right semantic for NL routing; document this invariant in the router code

## Next Steps

- [ ] Wait for deep parallel audit results (security, dependency, performance, tech-debt)
- [ ] Verify Phase B B6 completion before B7 kickoff
- [ ] Fix pre-existing test failures in warptui-interactive-layer
- [ ] Evaluate Bash availability constraint for remaining subagent phases
- [ ] Phase C draft review once Phase B completes
