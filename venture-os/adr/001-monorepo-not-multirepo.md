# ADR-001: Monorepo, Not Multi-Repo

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

VentureOS needs to host: foundational blueprints, workflow definitions, a growing knowledge graph, multiple venture runtimes, extensions, and tooling. Two topologies were considered.

## Decision

Single repository (`venture-os/`) for the first decade. Split by domain only when a sub-tree exceeds practical git performance (~50K files) or when a domain needs independent hosting (e.g., knowledge graph served as its own API).

## Consequences

- **Easier:** Atomic changes across blueprint + workflows + knowledge. Single clone. No cross-repo dependency hell.
- **Harder:** Repo grows over time. Git operations slow. Mitigated by `.gitignore` on generated artifacts and shallow clones for ventures/.
- **Longevity:** One artifact survives longer than many interlocked ones. Migration to multi-repo (if ever needed) is a mechanical tree-split, not a redesign.
- **What breaks if wrong:** Nothing — the internal directory layout is an implementation detail. External consumers only see the CLI API.
