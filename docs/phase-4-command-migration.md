# Phase 4: Command Migration to Plugins

> Migrating Core Commands from Monolithic to Plugin Architecture

**Last Updated**: 2026-06-21  
**Status**: Completed  
**Target**: Mekong CLI v6.1+  
**Related**: [Plugin Migration Guide](plugin-migration-guide.md), [Plugin Architecture](architecture/plugin-architecture.md)

---

## Overview

Phase 4 represents the core migration effort: converting all built-in commands from the monolithic `src/commands/` structure to standalone plugins. This phase enables modularity, hot-reload, and third-party extensibility.

### Objectives

- Migrate all 107+ core commands to plugin format
- Maintain 100% backward compatibility during transition
- Establish plugin isolation boundaries
- Validate performance targets (< 5% startup overhead)
- Enable gradual feature flag rollout

### Scope

| Component | Before | After |
|-----------|--------|-------|
| Command location | `src/commands/{layer}/` | `plugins/mekong-core-{layer}/` |
| Registration | Static import | Dynamic discovery |
| Dependencies | Global imports | Manifest-declared |
| Configuration | `settings.json` | `plugins/mekong-core-*/config.json` |
| Isolation | None | Optional process sandbox |

---

## Migration Strategy

### Hybrid Approach (Zero Downtime)

The migration uses a **compatibility shim** that allows both legacy and plugin modes to coexist:

```json
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": true,
    "native_plugins": ["mekong-core-founder", "mekong-core-business"],
    "legacy_plugins": ["legacy-core-commands"]
  },
  "feature_flags": {
    "plugin_founder": true,
    "plugin_business": false,
    "plugin_product": "shim"
  }
}
```

### Layer-by-Layer Rollout

Commands are organized into 6 business layers. Migration proceeded layer by layer:

| Layer | Commands | Status | Target |
|-------|----------|--------|--------|
| Founder | 52 | Completed | v6.1.0 |
| Business | 71 | Completed | v6.1.0 |
| Product | 31 | Completed | v6.1.0 |
| Engineering | 66 | Completed | v6.1.0 |
| Ops | 41 | Completed | v6.1.0 |
| Studio | 23 | Completed | v6.1.0 |

---

## Migration Process

### Step 1: Plugin Skeleton Generation

For each command module, generate plugin scaffolding:

```bash
# Generate plugin structure
python3 scripts/generate-plugin-skeleton.py \
  --module src/commands/founder/annual_commands.py \
  --output plugins/mekong-core-founder/
```

### Step 2: Handler Extraction

Move business logic from Typer apps to pure functions:

**Before** (`src/commands/founder/annual_commands.py`):
```python
import typer
from src.services.billing import BillingService

@app.command()
def annual_report(year: int = typer.Option(...)):
    billing = BillingService()
    data = billing.get_annual(year)
    typer.echo(format_report(data))
```

**After** (`plugins/mekong-core-founder/handlers/annual.py`):
```python
def annual_report_handler(ctx: PluginContext, year: int):
    billing = ctx.get_service("billing")
    data = billing.get_annual(year)
    return {"report": format_report(data), "year": year}
```

### Step 3: Manifest Creation

Define commands, permissions, and dependencies in `plugin.json`:

```json
{
  "id": "mekong-core-founder",
  "name": "Mekong Core - Founder Commands",
  "version": "6.1.0",
  "layer": "founder",
  "entrypoint": "./plugin.py",
  "commands": [
    {
      "name": "annual",
      "handler": "handlers.annual.annual_report_handler",
      "permissions": {"database": ["read"]},
      "mcu_cost": 2
    }
  ]
}
```

### Step 4: Dependency Injection

Replace global imports with context-provided services:

```python
# Before
self.billing = BillingService()  # Tight coupling

# After
self.billing = context.get_service("billing")  # Loose coupling
```

### Step 5: Testing

Each plugin includes comprehensive tests:

```bash
python3 -m pytest plugins/mekong-core-founder/tests/ -v
```

---

## Verification Checklist

### Per-Plugin

- [ ] Plugin loads: `mekong admin plugin load plugins/mekong-core-{layer}/`
- [ ] All commands registered: `mekong admin plugin commands {plugin-id}`
- [ ] Command executes: `mekong {command-name} --help`
- [ ] Tests pass: `pytest plugins/mekong-core-{layer}/tests/ -v`
- [ ] Startup time < 100ms (cached)
- [ ] Permissions correctly declared

### System-Wide

- [ ] All 107+ core commands available in plugin mode
- [ ] Feature flags allow per-layer control
- [ ] Compatibility shim works for legacy commands
- [ ] Rollback to pure legacy mode verified
- [ ] E2E integration tests pass
- [ ] Load testing shows < 5% performance impact
- [ ] Memory footprint increase < 10%
- [ ] Hot reload works for native plugins

---

## Rollback Plan

```bash
# Immediate rollback
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false

# Or disable per-layer
jq '.feature_flags.plugin_founder = false' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

mekong platform restart gateway
```

Compatibility shim ensures zero-downtime rollback.

---

## Performance Targets

| Metric | Legacy | Plugin (Native) | Target |
|--------|--------|-----------------|--------|
| Cold Start | baseline | +200ms | < +500ms |
| Warm Start | baseline | +10ms | < +50ms |
| Memory | baseline | +5% | < +10% |
| Command Exec | baseline | +2ms | < +5% |

---

## Next Steps

After Phase 4 completion:

1. **Phase 5**: Frontend modernization — dashboard plugin status
2. **Phase 6**: Infrastructure hardening — separate worker deployment
3. **Phase 7**: ZenOS Bridge — particle-aware execution

See also:
- [Plugin Migration Guide](plugin-migration-guide.md)
- [Plugin Architecture](architecture/plugin-architecture.md)
- [Command Execution Flow](architecture/command-execution-flow.md)
