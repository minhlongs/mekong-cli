---
name: vendor
description: >-
  Autonomous vendor marketplace and third-party provider governance engine with SQLite persistence, automated security audits, trust scoring, and MCP tools.
---

# /vendor — Autonomous Vendor Marketplace & Provider Governance Engine

The `mekong vendor` engine provides an enterprise-grade vendor marketplace and third-party provider governance system. It maintains a persistent registry of ecosystem plugins, model providers, custom agent runtimes, and external tools with automated security and compliance audits.

## Usage

```bash
// turbo
mekong vendor [COMMAND] [OPTIONS]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| *(none / overview)* | Display marketplace summary, vendor counts, and system status. |
| `onboard` | Register a new vendor, plugin, model, or tool provider. |
| `list` | List registered vendors with filtering by vendor type and operational status. |
| `delist` | Remove or revoke a vendor from active marketplace listing. |
| `audit` | Run an automated security, compliance, or performance audit on a vendor provider. |

## Options & Flags

- `--vendor-type`: Filter or specify vendor type (`agent`, `plugin`, `model`, `tool`, `service`, `all`).
- `--status`: Filter or specify operational status (`active`, `pending`, `delisted`, `flagged`, `all`).
- `--trust-score`: Initial trust rating (0.0 to 100.0, default 85.0).
- `--audit-type`: Type of automated audit to run (`security`, `compliance`, `performance`).
- `--limit`: Maximum number of records to return (default 50).
- `--json`: Emit structured machine-readable JSON for CI/CD and automation.

## MCP Tools

The vendor marketplace exposes 3 dual-engine MCP tools:

1. `mekong_vendor_onboard(name, vendor_type, version, description, author, trust_score)`: Register a vendor provider.
2. `mekong_vendor_list(vendor_type, status, limit)`: Query and filter vendor registry.
3. `mekong_vendor_assess(name, audit_type)`: Perform automated compliance or security audit.
