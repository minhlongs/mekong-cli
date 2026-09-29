---
name: queue
description: >-
  📬 Autonomous Distributed Task Queue & Dead-Letter Recovery Mesh.
---

# /queue — Autonomous Distributed Task Queue & Dead-Letter Mesh

Provides prioritized task scheduling (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`), atomic worker
leasing with heartbeat extensions and stale reclamation, exponential retry backoff,
and dead-letter queue (DLQ) inspection and replay without external dependencies.

## Usage

```bash
# Schedule a task for prioritized execution
mekong queue enqueue "nightly_data_sync" --priority high --payload '{"source": "orders"}'

# Enqueue with delayed execution (e.g. 60 seconds)
mekong queue enqueue "reconcile_invoice" --delay-sec 60

# Inspect queue depth, active leases, and dead-letter count
mekong queue status

# Output status in machine-readable JSON format
mekong queue status --json

# Lease pending tasks for worker execution
mekong queue process --limit 5

# Inspect tasks residing in the dead-letter queue
mekong queue dlq

# Replay all failed tasks from DLQ
mekong queue dlq --action retry-all

# Purge DLQ tasks
mekong queue dlq --action clear
```

## Features

1. **Priority Scheduling**:
   - `CRITICAL` (0), `HIGH` (1), `NORMAL` (2), `LOW` (3).
   - Atomic fetch-and-lease ensures tasks are never double-processed.
2. **Heartbeats & Stale Reclamation**:
   - Workers extend active leases via heartbeat tokens.
   - Expired or orphaned leases are automatically reclaimed back to `PENDING`.
3. **Exponential Backoff & Dead-Letter Queue (DLQ)**:
   - Configurable retry ceiling (`max_retries`).
   - Exponential delay growth prevents cascading infrastructure failures.
   - Tasks that exhaust retries are routed to DLQ for auditing and manual replay.
4. **Pure Standard Library Persistence**:
   - SQLite ledger stored in `.mekong/task_queue.db`.
   - Multi-process safe with `PRAGMA journal_mode=WAL`.

## Commands

- `mekong queue enqueue <name>`: Enqueue a new task with optional priority and payload.
- `mekong queue status`: View current queue metrics and depth.
- `mekong queue process`: Lease pending tasks for worker execution.
- `mekong queue dlq`: Inspect, replay, or clear dead-letter queue entries.
