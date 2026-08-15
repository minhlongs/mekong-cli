# ADR-003: Append-Only Event Log as Primary Data Mechanism

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

How should VentureOS track state changes, decisions, and workflow executions? Options: database, JSON files, append-only log.

## Decision

Every runtime operation writes to an append-only JSONL event log (`wal/` and `events/`). State is *derived* from replaying the log, not stored separately. A `state.json` snapshot exists for performance but is always reconstructable from the log.

## Consequences

- **Easier:** Full audit trail by default. Crash recovery = replay from last checkpoint. Reversible decisions.
- **Harder:** Log compaction strategy needed for long-running ventures. Reads require replay (mitigated by snapshots).
- **Longevity:** JSONL is human-readable, git-diffable, and survives format changes (ignore unknown fields). No database migration ever needed.
- **What breaks if wrong:** If events can be modified or deleted, auditability is false. The log MUST be append-only enforced at the OS level.
