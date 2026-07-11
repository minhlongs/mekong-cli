# ADR-006: 9-Phase Lifecycle as Universal Contract

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

Every venture follows a lifecycle. The question: is it a fixed sequence (waterfall), a state machine (flexible transitions), or a free-form workflow (user-defined)?

## Decision

9-phase lifecycle as a state machine with typed transitions. Not all ventures go through all phases. Transitions can loop (e.g., back to research from validation). But the phases themselves are canonical and unchanging.

**Phases:** IDENTIFY (01) → IDEA (02) → VALIDATE (03) → ARCHITECT (04) → INCORPORATE (05) → SEED (06) → BUILD (07) → SCALE (08) → EXIT (09)

## Consequences

- **Easier:** Standardized venture portfolios. Comparable metrics across ventures. Playbooks map to phases.
- **Harder:** Some ventures don't fit (e.g., lifestyle businesses that never scale). Solution: phases are optional — skip to EXIT without SCALE.
- **Longevity:** The 9 phases are derived from universal patterns (idea → validation → build → scale → exit). They don't depend on technology or market trends.
- **What breaks if wrong:** If phases are wrong, every workflow, gate, and template built on them is wrong. Mitigated by basing them on cross-industry research (a16z, YC, Antler, Startup Genome).
