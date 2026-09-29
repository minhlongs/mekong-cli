---
name: billing
description: >-
  Billing operations: usage submission, reconciliation, and event tracking.
---

# /billing — Autonomous Billing & Usage Reconciliation Engine

Meter API consumption, simulate multi-tier invoices, reconcile usage variances, and monitor license quota health.

## Usage

```bash
// turbo
mekong billing $ARGUMENTS
```

## CLI Commands

| Subcommand | Description | Flags |
|---|---|---|
| `mekong billing` | Display billing status, pricing tiers, and active quota summary | `--json, -j` |
| `mekong billing simulate` | 🧪 Simulate billing calculation and itemized invoice for accrued usage | `--license, -l`, `--tier, -t`, `--days, -d`, `--json, -j` |
| `mekong billing submit-usage` | 📤 Submit usage events for metering with idempotency | `--license, -l`, `--event-type, -t`, `--value, -v`, `--json, -j` |
| `mekong billing reconcile` | 🔍 Trigger reconciliation audit for variance detection | `--license, -l`, `--date, -d`, `--all`, `--json, -j` |
| `mekong billing status` | 📊 Get billing status and MCU quota consumption for a license | `--license, -l`, `--json, -j` |
| `mekong billing sync` | 🔄 Sync usage records from local SQLite to RaaS Gateway | `--dry-run, -n`, `--verbose, -v`, `--json, -j` |
| `mekong billing sync-status` | 📊 Show billing sync status and recent push history | |
| `mekong billing tiers` | 🏷️ Display monetization tiers and consumption rate matrices | `--json, -j` |

## Model Context Protocol (MCP) Tools

The billing engine exposes native MCP tools across FastMCP and JSON-RPC 2.0 stdio:

- **`mekong_billing_simulate(license_key="mekong_lic_default", tier="pro", period_days=30)`**: Generate simulated invoice breakdown with USD and VND conversion.
- **`mekong_billing_record_usage(license_key, event_type, quantity, idempotency_key="", tier="pro")`**: Meter billable consumption (`llm_tokens`, `agent_minutes`, `api_calls`, `storage_mb`, `mcu_credits`).
- **`mekong_billing_status(license_key="mekong_lic_default")`**: Inspect active quotas, consumed units, and unbilled charges.

## Pricing Tiers (USD & VND @ 25,400 rate)

- **FREE**: \$0/mo | 50 MCU | \$0.0020/k tokens | \$0.050/agent min
- **DEVELOPER**: \$49/mo | 500 MCU | \$0.0015/k tokens | \$0.030/agent min
- **PRO**: \$199/mo | 3,000 MCU | \$0.0010/k tokens | \$0.020/agent min
- **ENTERPRISE**: \$999/mo | 20,000 MCU | \$0.0006/k tokens | \$0.010/agent min
