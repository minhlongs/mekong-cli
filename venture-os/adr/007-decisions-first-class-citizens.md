# ADR-007: Decisions as First-Class Citizens

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

Most operating systems track actions but not decisions. A venture that records "we raised $2M at $10M cap" without recording "why we chose equity over debt, why this valuation, why now" cannot be audited, improved, or reused.

## Decision

Every decision is a typed artifact with a formal schema: problem statement, options considered, evidence consulted, chosen option, rationale in operator's own words, and downstream consequences. Decisions drive actions — not the other way around.

## Consequences

- **Easier:** Reverse a bad decision → replay all dependent actions with the new decision. Build institutional memory per-venture and cross-venture.
- **Harder:** Requires discipline from operators to write rationale at decision time (not reconstruct later). Tooling helps: decision templates + required fields.
- **Longevity:** "Why did we choose X?" is answerable for 10 years. Without this, each new team re-litigates every decision from scratch.
- **What breaks if wrong:** Decisions without actions are just opinions. Actions without decisions are unreliable. Both must exist — the schema enforces this coupling.
