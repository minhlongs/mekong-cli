---
name: queue
description: >-
  📬 Autonomous Distributed Task Queue & Dead-Letter Mesh
---

# /queue — 📬 Autonomous Distributed Task Queue & Dead-Letter Mesh

📬 Autonomous Distributed Task Queue & Dead-Letter Mesh.

## Usage

```bash
// turbo
mekong queue $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `enqueue` | Schedule a new task for prioritized execution. |
| `status` | Inspect current queue depth, active worker leases, and dead-letter count. |
| `process` | Lease eligible pending tasks for execution. |
| `dlq` | Inspect and recover failed tasks residing in the dead-letter queue. |
