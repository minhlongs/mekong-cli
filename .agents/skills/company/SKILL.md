---
name: company
description: >-
  Company workspace configuration, initialization, and status monitoring.
---

# /company — Company workspace configuration, initialization, and status monitoring

Company workspace configuration, initialization, and status monitoring.

## Usage

```bash
// turbo
mekong company $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `init` | Set up the current workspace (.mekong/ + 12 config files). |
| `status` | Show current ``.mekong/company.json`` contents. |
| `reset` | Re-initialize the company config (idempotent). |
