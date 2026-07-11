# ADR-002: Blueprint Is Immutable, Not Mutable

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

Should the foundational documents (philosophy, principles, lifecycle phases, schemas) change in-place as VentureOS evolves?

## Decision

`blueprint/` is append-only. Changes require a new version number (SemVer) and a new document. Old versions remain available for ventures that depend on them. The "current" version is a symlink, never an overwrite.

## Consequences

- **Easier:** Running ventures never break when blueprint updates. Reproducibility: any artifact cites its blueprint version.
- **Harder:** More files over time. Managed by periodic archival of superseded versions.
- **Longevity:** A 10-year-old venture can still reproduce its exact environment by pointing at its blueprint commit hash.
- **What breaks if wrong:** In-place mutation makes "what was true when this was built?" unanswerable. Trust erodes.
