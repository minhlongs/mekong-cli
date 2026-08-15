# ADR-008: Runtime = Directory on Disk

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

How does VentureOS represent an active venture? Options: database rows, cloud container, directory on disk.

## Decision

A venture runtime IS a directory on disk. Period. It can be committed to git, rsynced, tar'd, opened in an editor. No database unlocks it. No server must be running. No network required.

## Consequences

- **Easier:** Maximum portability. Zero lock-in. Works on a plane. Survives platform changes. Human-readable without tools.
- **Harder:** Concurrent access needs file locking. Large binary artifacts (video, datasets) need a separate storage layer (R2/S3 with local symlink).
- **Longevity:** A directory tree works the same in 2026 and 2056. A cloud-native runtime depends on APIs, SDKs, and cloud providers that may not exist.
- **What breaks if wrong:** If someone abstracts "venture" into a database table or cloud service, you've built a SaaS, not an OS. Guard by making the CLI work on any directory — not just managed ventures.
