# Command Migration - Admin Quick Reference

**Quick commands for managing the migration**

---

## Check Migration Status

```bash
# Comprehensive status (layers, plugins, progress)
python3 scripts/migration-status-reporter.py

# JSON output for automation
python3 scripts/migration-status-reporter.py --json

# Detailed with issues
python3 scripts/migration-status-reporter.py --detailed
```

## Enable/Disable Plugins

```bash
# Enable plugin system globally
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true

# Enable specific layer as plugin (use native plugin version)
export MEKONG_FEATURE_PLUGIN_FOUNDER=plugin
export MEKONG_FEATURE_PLUGIN_BUSINESS=plugin

# Use shim mode (auto: plugin if available, else legacy)
export MEKONG_FEATURE_PLUGIN_FOUNDER=shim

# Disable and use legacy
export MEKONG_FEATURE_PLUGIN_FOUNDER=legacy

# Full rollback to legacy-only mode
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false
export MEKONG_LEGACY_MODE=true
```

## Plugin Management

```bash
# List all discovered plugins
mekong admin plugin list

# Check plugin health
mekong admin plugin status mekong-core-founder

# Enable specific plugin
mekong admin plugin enable mekong-core-founder

# Disable specific plugin
mekong admin plugin disable mekong-core-founder

# Validate plugin
mekong admin plugin validate plugins/mekong-core-founder/

# View plugin logs
mekong admin plugin logs mekong-core-founder

# Reload plugins (after code changes)
mekong admin plugin reload
```

## Canary Testing

```bash
# Test plugin performance before rollout
python3 scripts/migration-canary-tester.py \
  --plugin mekong-core-founder \
  --commands annual,okr,swot \
  --iterations 50

# With custom thresholds
python3 scripts/migration-canary-tester.py \
  --plugin mekong-core-founder \
  --commands annual \
  --latency-threshold 300 \
  --error-threshold 0.005
```

## Emergency Rollback

```bash
# Full system rollback (instant)
scripts/migration-rollback.sh full

# Rollback specific layer only
scripts/migration-rollback.sh layer founder

# Disable problematic plugin
scripts/migration-rollback.sh plugin mekong-core-founder
```

## Analysis & Monitoring

```bash
# Run codebase analysis (if not already done)
python3 scripts/analyze-command-dependencies.py \
  --output build/command-analysis/

# View generated reports
cat build/command-analysis/command-analysis.md

# Check deprecation warnings (log tail)
tail -f ~/.mekong/logs/deprecation.log

# View plugin error logs
tail -f ~/.mekong/logs/plugin-errors.log
```

## Migration Phases Reference

| Phase | Version | Status | Action |
|-------|---------|--------|--------|
| 1 | v6.1-v6.2 | ✅ Active | Compatibility mode, no warnings |
| 2 | v6.2-v6.4 | Upcoming | Deprecation warnings enabled |
| 3 | v6.5-v6.7 | Future | Legacy disabled by default |
| 4 | v7.0+ | Future | Legacy removed |

---

## Feature Flag Reference

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED` | true/false | true | Master switch |
| `MEKONG_FEATURE_PLUGIN_FOUNDER` | plugin/legacy/shim | shim | Founder layer |
| `MEKONG_FEATURE_PLUGIN_BUSINESS` | plugin/legacy/shim | shim | Business layer |
| `MEKONG_FEATURE_PLUGIN_PRODUCT` | plugin/legacy/shim | shim | Product layer |
| `MEKONG_FEATURE_PLUGIN_ENGINEERING` | plugin/legacy/shim | shim | Engineering layer |
| `MEKONG_FEATURE_PLUGIN_OPS` | plugin/legacy/shim | shim | Ops layer |
| `MEKONG_FEATURE_PLUGIN_STUDIO` | plugin/legacy/shim | shim | Studio layer |
| `MEKONG_DEPRECATION_WARNINGS` | true/false | true | Show deprecation notices |

Settings are also in `~/.mekong/settings.json`:

```json
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": true
  },
  "feature_flags": {
    "plugin_founder": "shim",
    "plugin_business": "shim"
  }
}
```

---

## Troubleshooting

### Plugin not loading?
```bash
# Check manifest validity
mekong admin plugin validate plugins/mekong-core-founder/

# Common issues:
# - Missing handler in plugin.json
# - Syntax error in plugin.py
# - Handler import path wrong
```

### Command not found after enabling plugin?
```bash
# Ensure plugin is active
mekong admin plugin list

# If not active, enable it
mekong admin plugin enable mekong-core-founder

# Check if command is in plugin manifest
cat plugins/mekong-core-founder/plugin.json | jq '.commands'
```

### Performance regression?
```bash
# Run canary test to measure impact
python3 scripts/migration-canary-tester.py \
  --plugin mekong-core-founder \
  --commands annual \
  --iterations 100

# Compare against baseline (legacy mode)
MEKONG_FEATURE_PLUGIN_FOUNDER=legacy time mekong annual
```

### Need to see what's happening?
```bash
# Enable debug logging
export MEKONG_LOG_LEVEL=DEBUG

# Check plugin-specific logs
tail -f ~/.mekong/logs/plugin-migration.log
```

---

## Support Resources

- **Full Strategy**: `docs/incremental-migration-strategy.md`
- **Deprecation Policy**: `docs/command-deprecation-policy.md`
- **Codebase Analysis**: `docs/codebase-structure-analysis.md`
- **Final Report**: `plans/command-migration-workstream/FINAL_REPORT.md`
- **Migration Guide**: `docs/plugin-migration-guide.md`
- **Status**: `python3 scripts/migration-status-reporter.py`

---

**Last Updated**: 2026-06-20  
**Maintainer**: Mekong CLI Team  
**Emergency**: See `scripts/migration-rollback.sh`
