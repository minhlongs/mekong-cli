# ADR-004: File System as Primary API (Not Database)

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

Should VentureOS store venture state, knowledge, and decisions in a database (SQLite, PostgreSQL) or in the file system?

## Decision

The file system IS the database. Every venture is a directory tree. Every knowledge node is a file. Every decision is a file. The "API" is: open, read, write, grep. No ORM, no migrations, no schema deployments.

## Consequences

- **Easier:** Human-readable without tools. Git-native. Portable across machines. No database server to run.
- **Harder:** Concurrent writes need file-locking. Large knowledge graphs need efficient search (mitigated by ripgrep + optional SQLite FTS index for scale).
- **Longevity:** A directory tree is readable in 30 years. A SQLite database with a custom schema requires the schema doc AND the software. Plain text survives format obsolescence.
- **What breaks if wrong:** Trade performance for portability. If VentureOS needs to handle 10K+ ventures with 100K+ decisions each, a hybrid (files + SQLite FTS) is the escape hatch — but not needed for years.
