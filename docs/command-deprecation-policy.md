# Command Deprecation Policy and Timeline

**Last Updated**: 2026-06-20  
**Owner**: Mekong CLI Team  
**Scope**: All legacy commands in `src/commands/` and `.claude/commands/*.md`

---

## 1. Policy Overview

Mekong CLI is migrating from a monolithic command structure to a plugin-based architecture. This policy establishes the timeline and procedures for deprecating legacy commands.

### Goals

- **Zero Downtime**: No breaking changes during migration period
- **Clear Communication**: Users receive advance notice of deprecations
- **Safe Rollback**: Ability to revert instantly if issues arise
- **Gradual Transition**: Incremental migration by business layer

### Definitions

- **Legacy Command**: A command defined in `src/commands/*.py` (Typer-based) or `.claude/commands/*.md` (markdown-based)
- **Plugin Command**: A command provided by a plugin with `plugin.json` manifest
- **Compatibility Mode**: Running both legacy and plugin commands simultaneously
- **Feature Flag**: Environment variable controlling which version is active

---

## 2. Deprecation Timeline

### Phase 1: Compatibility Mode (v6.1 - v6.2) [CURRENT]

**Duration**: v6.1 release → v6.2 release (~6 months)

**Status**:
- ✅ Plugin system enabled by default (opt-out possible)
- ✅ Legacy commands fully functional
- ✅ Both systems run in parallel
- ⚠️ No deprecation warnings

**User Action Required**: None

**Migration Target**: 0% (preparation phase)

---

### Phase 2: Deprecation Warnings (v6.2 - v6.4)

**Duration**: v6.2 → v6.4 (~6 months)

**Changes**:
- ⚠️ Legacy commands log deprecation warnings on first use per session
- ⚠️ `mekong admin deprecation log` shows all deprecated command invocations
- ⚠️ Documentation marks legacy commands with ⚠️ icon
- ⚠️ `mekong help` shows "(legacy)" suffix on deprecated commands

**User Action Required**: Migrate custom commands to plugin format

**Migration Target**: 25% of high-use commands migrated

**Feature Flags**:
```bash
# Disable warnings (temporary)
export MEKONG_DEPRECATION_WARNINGS=false

# Opt-in to plugin versions
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true
```

---

### Phase 3: Legacy Disabled by Default (v6.5 - v6.7)

**Duration**: v6.5 → v6.7 (~6 months)

**Changes**:
- ❌ Legacy commands disabled by default
- ✅ Plugin commands enabled by default
- 🔄 Opt-in to legacy mode: `export MEKONG_LEGACY_MODE=true`
- 🔄 Per-command override: `MEKONG_USE_LEGACY=true mekong <command>`
- ⚠️ Monthly email reminders for users with legacy command usage

**User Action Required**: All custom commands must be migrated

**Migration Target**: 100% of core commands migrated

**Rollback**: Available via `MEKONG_LEGACY_MODE=true`

---

### Phase 4: Legacy Removal (v7.0+)

**Duration**: v7.0 release onward

**Changes**:
- ❌ Legacy command system completely removed
- ❌ Compatibility shim deleted
- ❌ `src/commands/` directory may be removed or repurposed
- ✅ Only plugin commands supported

**User Action Required**: All commands must already be migrated

**Migration Target**: 100% complete

**Rollback**: Not possible - users must migrate before v7.0

---

## 3. Command-Specific Deprecation Schedule

Commands are prioritized for migration based on:

1. **Usage Frequency** (high → low)
2. **Business Impact** (critical → nice-to-have)
3. **Migration Complexity** (simple → complex)

### High-Priority (Migrate First)

| Command | Layer | Complexity | Target Version |
|---------|-------|------------|----------------|
| `cook` | engineering | medium | v6.2 |
| `code` | engineering | medium | v6.2 |
| `test` | engineering | simple | v6.2 |
| `deploy` | engineering | complex | v6.3 |
| `fix` | engineering | medium | v6.3 |
| `review` | engineering | medium | v6.3 |

### Medium-Priority (Migrate v6.3 - v6.5)

| Command | Layer | Complexity | Target Version |
|---------|-------|------------|----------------|
| `annual` | founder | simple | v6.3 |
| `okr` | founder | simple | v6.3 |
| `sales` | business | medium | v6.4 |
| `marketing` | business | complex | v6.4 |
| `plan` | product | medium | v6.4 |
| `sprint` | product | simple | v6.4 |
| `audit` | ops | complex | v6.5 |
| `health` | ops | simple | v6.5 |

### Low-Priority (Migrate v6.5 - v6.7)

| Command | Layer | Complexity | Target Version |
|---------|-------|------------|----------------|
| `swot` | founder | simple | v6.5 |
| `fundraise` | founder | complex | v6.5 |
| `pricing` | business | medium | v6.6 |
| `finance` | business | complex | v6.6 |
| `roadmap` | product | medium | v6.6 |
| `brainstorm` | product | simple | v6.6 |
| `security` | ops | complex | v6.7 |
| `status` | ops | simple | v6.7 |
| `venture` | studio | complex | v6.7 |
| `dealflow` | studio | medium | v6.7 |

---

## 4. Deprecation Notices

### Runtime Warning Format

When a deprecated legacy command is executed:

```
⚠️  DEPRECATION WARNING
Command 'annual' is deprecated and will be removed in v7.0.

Migration path:
  1. Enable plugin system: MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true
  2. Enable founder plugins: MEKONG_FEATURE_PLUGIN_FOUNDER=true
  3. Use plugin command: mekong annual (plugin version)

For migration help: mekong admin migration status
Suppress warnings: MEKONG_DEPRECATION_WARNINGS=false (temporary)

See: https://docs.mekongmind.com/command-deprecation
```

Logged to:
- Console (stderr)
- `~/.mekong/logs/deprecation.log`
- Metrics: `deprecation.warning.count{command="<name>"}`

### Help Text Format

```
annual (legacy)        Generate annual report
  ⚠️ Deprecated - use plugin version when available
```

---

## 5. Migration Tools

### Status Check

```bash
# Show migration status for all commands
mekong admin migration status

# Output:
# Layer: Founder
#   ✅ annual (plugin)
#   ⚠️ okr (legacy) - migrate by v6.3
#   ❌ swot (deprecated) - remove by v6.5
```

### Auto-Migration Helper

```bash
# Migrate custom command to plugin format
mekong admin migrate-command --name my-command --output ~/.mekong/plugins/

# Or use the script
python3 scripts/migrate-commands-to-plugins.py --layer founder
```

### Validation

```bash
# Check which commands are still legacy
mekong admin plugin list --show-legacy

# Verify plugin version available
mekong admin plugin check <command-name>
```

### Rollback

```bash
# Immediate: use legacy version for a command
MEKONG_USE_LEGACY=true mekong <command>

# Full rollback to legacy-only mode
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false
export MEKONG_LEGACY_MODE=true

# Re-enable plugins
unset MEKONG_LEGACY_MODE
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true
```

---

## 6. Communication Plan

### Before Deprecation (3 months notice)

- 📢 Release notes: "Command X will be deprecated in v6.2"
- 📢 Blog post: "Plugin Migration Guide"
- 📢 Email to subscribed users
- 📢 In-app notifications (if dashboard available)

### During Deprecation (active phase)

- 📊 Dashboard: `mekong admin migration dashboard` (real-time stats)
- 📊 Weekly deprecation report emailed
- 📊 Metrics in Prometheus/Grafana

### Before Removal (1 month notice)

- 🚨 Critical: ERROR level log when legacy command executed
- 🚨 Exit code 91 for legacy-only commands (requires --legacy flag)
- 🚨 Final warning in CLI output
- 📢 Countdown banner in `mekong --version`

---

## 7. Exceptions

### Emergency Rollback

If a plugin version has critical issues, the team can:

1. **Immediate**: Set `feature_flags.plugin_<command> = "shim"` in settings.json
2. **Hotfix**: Deploy fixed plugin version
3. **Communication**: Notify users within 24 hours

### Extended Support

Rarely-used commands (< 10 invocations/month) may receive extended support:

- Request via GitHub issue
- Reviewed quarterly
- Approval required from maintainers

---

## 8. Monitoring

### Key Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Legacy command usage | < 5% | > 10% |
| Plugin error rate | < 0.1% | > 0.5% |
| Migration completion | 100% by v6.7 | < 50% by v6.5 |

### Logs

- `~/.mekong/logs/deprecation.log` - all deprecation events
- `~/.mekong/logs/plugin-errors.log` - plugin failures

### Dashboard

```bash
# Quick status
mekong admin migration status --detailed

# Export usage report
mekong admin migration export --format csv > migration-report.csv
```

---

## 9. FAQ

**Q: Will my existing scripts break?**

A: No. During Phase 1-3, both legacy and plugin versions work. Phase 4 requires migration.

**Q: How do I migrate my custom commands?**

A: See `docs/plugin-migration-guide.md`. Use `scripts/migrate-commands-to-plugins.py` for automation.

**Q: Can I disable deprecation warnings?**

A: Temporarily with `MEKONG_DEPRECATION_WARNINGS=false`, but you must migrate before Phase 4.

**Q: What if a plugin is missing a command I need?**

A: File a GitHub issue or use legacy mode (Phase 1-3 only). Plugin coverage will reach 100% by v6.7.

**Q: Are there performance differences?**

A: Plugin cold start adds ~100-200ms. Warm starts are faster. No impact during normal operation.

---

## 10. Support

- **Documentation**: https://docs.mekongmind.com/command-deprecation
- **Migration Guide**: `docs/plugin-migration-guide.md`
- **Issues**: GitHub Issues (label: `migration`)
- **Community**: [mekongmind.com/guides](https://mekongmind.com/guides)

---

**Next Review Date**: 2026-09-20 (quarterly review)
