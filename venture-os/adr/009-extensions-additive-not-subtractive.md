# ADR-009: Extensions Are Additive, Never Subtractive

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

How should VentureOS evolve? Monolithic releases where everything changes at once, or an extension system where new capabilities are added without touching the core?

## Decision

The core VentureOS (blueprint + CLI + runtime engine) is minimal and stable. All new capabilities come via extensions: new workflows, new knowledge node types, new compiler modules, new output formats. Extensions declare what they provide and what they consume. The OS composes them at runtime. An extension ceasing to exist never breaks an existing venture.

## Consequences

- **Easier:** Community contributions without core team review. Custom workflows per-venture without forking. Extensions can be private (your secret sauce) or public (shared with the community).
- **Harder:** Version compatibility matrix. An extension written for blueprint v1.2 may not work with v2.0. Solved by declared compatibility ranges.
- **Longevity:** A 10-year-old venture continues to run even if the extension ecosystem has completely changed. Its pinned versions still work.
- **What breaks if wrong:** If extensions can modify or remove core behavior, we've rebuilt the monolith under a different name. Additive only — extensions can ADD behaviors, never CHANGE or REMOVE existing ones.
