---
name: billing
description: >-
  Billing operations: usage submission, reconciliation, and event tracking.
---

# /billing — Billing operations: usage submission, reconciliation, and event tracking

Billing operations: usage submission, reconciliation, and event tracking.

## Usage

```bash
// turbo
mekong billing $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `simulate` | 🧪 Simulate billing calculation for usage. |
| `submit-usage` | 📤 Submit usage events for billing (with idempotency). |
| `reconcile` | 🔍 Trigger reconciliation audit for variance detection. |
| `emit-event` | 📡 Emit billing event to event bus or webhook. |
| `status` | 📊 Get billing status for a license. |
| `sync` | 🔄 Sync usage records from local SQLite to RaaS Gateway. |
| `sync-status` | 📊 Show billing sync status. |
| `tiers` | 🏷️ Display monetization tiers and consumption rate matrices. |
