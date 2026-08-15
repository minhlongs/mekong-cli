# Mekong CLI Plugin Migration Guide

> Migrating from Monolithic Commands to Plugin Architecture

**Last Updated**: 2026-06-20  
**Target Version**: Mekong CLI v6.1+  
**Migration Type**: Gradual architectural transformation with zero downtime

---

## Overview

Mekong CLI is transitioning from a monolithic command structure to a plugin-based architecture. This migration enables:

- **Modularity**: Commands are packaged as isolated plugins
- **Hot Reload**: Update plugins without restarting the CLI
- **Security**: Sandboxed execution with fine-grained permissions
- **Extensibility**: Third-party plugin marketplace
- **Maintainability**: Clear boundaries and independent releases

### What Changes

| Aspect | Legacy (v6.0) | Plugin System (v6.1+) |
|--------|---------------|----------------------|
| Command location | `src/commands/`, `cli/` | `plugins/` or `~/.mekong/plugins/` |
| Registration | Static import at startup | Dynamic discovery & loading |
| Isolation | None (shared process) | Process/worker isolation available |
| Dependencies | Implicit global imports | Explicit manifest declaration |
| Configuration | `settings.json` | `plugin.json` + plugin-specific config |
| Hot reload | No (restart required) | Yes (watch mode) |
| Custom commands | `~/.mekong/commands/*.py` | `~/.mekong/plugins/installed/*/` |

### Migration Path

```
┌─────────────────────────────┐
│  Existing Mekong CLI Setup  │
│  (monolithic commands)      │
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Phase 1: Prepare - Read this guide          │
│  - Backup your custom commands               │
│  - Inventory your plugins/settings           │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Phase 2: Enable Compatibility Shim         │
│  - Legacy commands work as plugins           │
│  - No code changes required                  │
│  - Test plugin system loads                  │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Phase 3: Migrate Custom Commands            │
│  - Convert to plugin format                  │
│  - Update manifests                         │
│  - Test in isolation                        │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Phase 4: Full Plugin Mode                   │
│  - All commands as plugins                   │
│  - Hot reload enabled                       │
│  - Feature flags for gradual rollout        │
└───────────────────────────────────────────────┘
```

---

## Pre-Migration Checklist

### 1. Backup Everything

```bash
# Backup custom commands
cp -r ~/.mekong/commands ~/.mekong/commands.backup-$(date +%Y%m%d)

# Backup plugin configs
cp ~/.mekong/plugin_config.json ~/.mekong/plugin_config.json.backup-$(date +%Y%m%d) 2>/dev/null || true

# Backup settings
cp ~/.mekong/settings.json ~/.mekong/settings.json.backup-$(date +%Y%m%d)

# Export installed plugins list
ls ~/.mekong/plugins/installed/ > ~/Desktop/plugins-list-$(date +%Y%m%d).txt
```

### 2. Verify Prerequisites

```bash
# Check Python version (3.11+ required)
python3 --version

# Check Mekong CLI version
mekong version
# Must be v6.1.0 or higher

# Check disk space
df -h ~/.mekong

# Ensure no running gateway (clean state)
sudo launchctl list | grep mekong || echo "No gateway running"
```

### 3. Inventory Your Setup

```bash
# List all commands (count)
mekong help | wc -l

# Find custom commands
find ~/.mekong/commands -name "*.py" 2>/dev/null

# List current plugins (if any)
ls -la ~/.mekong/plugins/installed/ 2>/dev/null || echo "No installed plugins"
```

### 4. Read Release Notes

Check what's changed in v6.1:

```bash
cat ../../CHANGELOG.md | grep -A 20 "## 6.1.0"
```

---

## Phase 1: Enable Plugin System (Compatibility Mode)

The plugin system includes a **compatibility shim** that wraps existing command modules as plugins automatically. No code changes needed.

### Step 1.1: Enable Plugin System

```bash
# Option A: Environment variable (temporary)
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true

# Option B: Edit settings.json (persistent)
# Add to ~/.mekong/settings.json:
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": true,
    "hot_reload": false  // Enable after migration
  }
}
```

### Step 1.2: Start Mekong CLI

```bash
# The compatibility shim automatically wraps all legacy commands
mekong

# You should see:
# Plugin System: enabled (compatibility mode)
# Loaded plugins: legacy-core-commands, legacy-build, ...
```

### Step 1.3: Verify Compatibility Mode

```bash
# Check plugin status
mekong admin plugin list

# Expected output:
# ID                    Name                 Status    Type
# legacy-core-commands  Legacy Core Cmds    active    shim
# legacy-build          Legacy Build         active    shim
# ...

# Test a command (should work as before)
mekong version
mekong cook --help
```

### Step 1.4: Test Rollback

```bash
# Disable plugin system
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false

# Verify legacy mode
mekong admin plugin list
# Should show: "Plugin system disabled"

# Re-enable
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true
```

---

## Phase 2: Migrate Custom Commands

If you have custom commands in `~/.mekong/commands/`, convert them to plugins.

### Step 2.1: Understand Plugin Structure

A plugin is a directory with:

```
my-custom-plugin/
├── plugin.json          # Manifest (required)
├── plugin.py            # Plugin class (required)
├── commands.py          # Command definitions (optional)
├── handlers.py          # Business logic (optional)
├── schemas.py           # Pydantic models (optional)
├── config.json          # Default configuration (optional)
└── README.md            # Documentation (optional)
```

### Step 2.2: Create Plugin Manifest

Create `plugin.json`:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "id": "my-custom-plugin",
  "name": "My Custom Commands",
  "version": "1.0.0",
  "description": "Custom commands for my workflow",
  "author": "Your Name",
  "entrypoint": "./plugin.py",
  "type": "module",
  "commands": [
    {
      "name": "my-command",
      "description": "Does something useful",
      "handler": "handlers.my_command",
      "permissions": {
        "file": ["read", "write"],
        "network": ["outbound"]
      },
      "mcu_cost": 1
    }
  ],
  "dependencies": [],
  "permissions": {
    "filesystem": ["~/projects/**"],
    "network": ["https://api.example.com/**"]
  }
}
```

### Step 2.3: Create Plugin Class

Create `plugin.py`:

```python
from mekong_plugin_sdk import MekongPlugin, Command, CommandRegistry

class MyCustomPlugin(MekongPlugin):
    """My custom plugin."""

    @property
    def id(self) -> str:
        return "my-custom-plugin"

    @property
    def name(self) -> str:
        return "My Custom Commands"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, registry: CommandRegistry) -> None:
        """Initialize plugin and register commands."""
        self.registry = registry
        self._register_commands()

    def _register_commands(self) -> None:
        """Register all commands."""
        self.registry.register(Command(
            name="my-command",
            description="Does something useful",
            handler=self.handle_my_command,
            mcu_cost=1
        ))

    def handle_my_command(self, ctx, args):
        """Command handler."""
        # Your logic here
        return {"result": "success", "message": "Command executed"}

    def shutdown(self) -> None:
        """Cleanup on shutdown."""
        pass
```

### Step 2.4: Move Your Code

If your legacy command looked like:

```python
# ~/.mekong/commands/my_command.py (LEGACY)
import typer

app = typer.Typer()

@app.command()
def my_command(name: str):
    """Does something."""
    print(f"Hello {name}")

# In commands_registry.py:
# from .my_command import app as my_command_app
# main_app.add_typer(my_command_app, name="my-command")
```

Convert to plugin structure:

```python
# plugins/my-custom-plugin/handlers.py
def my_command(name: str):
    """Does something."""
    return {"message": f"Hello {name}"}

# plugins/my-custom-plugin/plugin.py (as above)
# The handler references handlers.my_command
```

### Step 2.5: Install the Plugin

```bash
# Create plugin directory
mkdir -p ~/.mekong/plugins/installed/my-custom-plugin

# Copy your plugin files
cp plugin.json plugin.py handlers.py ~/.mekong/plugins/installed/my-custom-plugin/

# Set permissions (important for security)
chmod 600 ~/.mekong/plugins/installed/my-custom-plugin/plugin.json
chmod 700 ~/.mekong/plugins/installed/my-custom-plugin

# Reload plugin system
mekong admin plugin reload

# Verify plugin loaded
mekong admin plugin list
```

### Step 2.6: Test the Plugin

```bash
# Test command works
mekong my-command --name "Test"

# Check plugin logs
mekong admin plugin logs my-custom-plugin

# Test unload/reload cycle
mekong admin plugin unload my-custom-plugin
mekong admin plugin load my-custom-plugin
```

---

## Phase 3: Migrate Core Commands (Bulk Migration)

For teams maintaining core Mekong commands, migrate command modules to plugins.

### Step 3.1: Use the Migration Helper

```bash
# Generate plugin manifests for existing command modules
python3 scripts/generate-legacy-plugins.py

# This creates:
# ~/.mekong/plugins/legacy/{module-name}/plugin.json
```

### Step 3.2: Review Generated Manifests

```bash
# Check generated manifests
ls ~/.mekong/plugins/legacy/

# Review one
cat ~/.mekong/plugins/legacy/core-commands/plugin.json
```

### Step 3.3: Enable Legacy Plugins

```bash
# In settings.json, enable legacy plugin loading:
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": true,
    "legacy_plugins_dir": "~/.mekong/plugins/legacy"
  }
}

# Restart Mekong CLI
mekong admin plugin scan
```

### Step 3.4: Gradually Convert to Native Plugins

For each important command module:

1. Create native plugin directory: `plugins/{module-name}/`
2. Copy and refactor code
3. Update manifest with proper permissions
4. Test thoroughly
5. Update feature flag to use native over shim

---

## Phase 4: Production Rollout

### Step 4.1: Canary Testing

Enable plugin system for a subset of commands first:

```bash
# Enable only specific plugins
export MEKONG_FEATURE_PLUGIN_BUILD=true
export MEKONG_FEATURE_PLUGIN_DEPLOY=true
# Others fall back to legacy
```

Monitor:

```bash
# Watch plugin metrics
mekong admin metrics --plugin

# Check error rates
mekong admin logs --level error --tail 100 | grep -i plugin
```

### Step 4.2: Gradual Enablement

Enable plugins in batches:

| Week | Commands Enabled | Risk Level |
|------|------------------|------------|
| 1 | core, version, help | Low |
| 2 | cook, code, test | Medium |
| 3 | deploy, review, fix | Medium |
| 4 | All remaining | Standard |

### Step 4.3: Full Enablement

```bash
# Enable all plugins
for flag in $(mekong admin feature-flags --list | grep plugin_ | cut -d: -f1); do
  export MEKONG_FEATURE_${flag^^}=true
done

# Or edit settings.json
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": false,
    "hot_reload": true
  },
  "feature_flags": {
    "plugin_build": true,
    "plugin_deploy": true,
    "plugin_cook": true,
    // ... all plugins enabled
  }
}
```

---

## Post-Migration Verification

### Run Test Suite

```bash
# Plugin-specific tests
python3 -m pytest tests/plugin/ -v

# Integration tests
python3 -m pytest tests/integration/test_plugin_system.py -v

# Full test suite
python3 -m pytest -q

# Performance benchmarks
python3 -m pytest tests/benchmarks/plugin_startup.py -v
```

### Verify All Commands Work

```bash
# Generate command coverage report
python3 scripts/verify-command-coverage.py

# Should show: 100% of commands available in plugin mode
```

### Check Migration Metrics

```bash
# Plugin vs legacy usage
mekong admin metrics --plugin-invocations

# Load times
mekong admin metrics --plugin-startup

# Error rates
mekong admin metrics --plugin-errors
```

---

## Troubleshooting

### Plugin Fails to Load

```bash
# Check plugin logs
mekong admin plugin logs <plugin-id>

# Validate manifest
mekong admin plugin validate <plugin-path>

# Common issues:
# - Invalid JSON in plugin.json
# - Missing MekongPlugin base class
# - Syntax errors in plugin.py
```

### Command Not Found After Migration

```bash
# Check if plugin is loaded
mekong admin plugin list

# If not loaded, check:
# 1. Manifest has correct command name
# 2. Handler path is correct (module.function)
# 3. Plugin is enabled (not disabled)

# Scan for new plugins
mekong admin plugin scan
```

### Performance Regression

```bash
# Measure cold start
time mekong --cold-start version

# If > 5 seconds:
# 1. Check for slow plugin initialization
# 2. Enable plugin caching:
export MEKONG_PLUGIN_CACHE_ENABLED=true
# 3. Profile with:
mekong admin plugin profile
```

### Hot Reload Not Working

```bash
# Verify hot reload is enabled
mekong admin config get plugin.hot_reload

# If false, enable in settings.json:
{
  "plugin_system": {
    "hot_reload": true
  }
}

# Ensure plugin has watcher support
# Some plugins may not support hot reload (type: "static")
```

### Rollback to Legacy Mode

```bash
# Immediate rollback
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false
# or
jq '.plugin_system.enabled = false' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# Restart services
mekong platform restart gateway

# Verify
mekong admin plugin list
# Should show: "Plugin system disabled"
```

---

## Advanced Migration Topics

### Converting Complex Commands

For commands with complex dependencies:

1. **Extract shared code** to a common library module
2. **Declare dependencies** in plugin manifest
3. **Use dependency injection** via PluginContext

Example:

```python
# Before: direct imports
from src.utils.db import get_connection
from src.services.billing import BillingService

# After: via context
class ComplexPlugin(MekongPlugin):
    def initialize(self, context: PluginContext):
        self.db = context.get_service("database")
        self.billing = context.get_service("billing")
```

### Migrating Multi-Command Modules

If your module has multiple Typer sub-apps:

```python
# Before: one module, multiple apps
# src/commands/project.py
@app.command()
def project_create(): ...

@app.command()
def project_delete(): ...

# After: one plugin, multiple commands
class ProjectPlugin(MekongPlugin):
    def _register_commands(self):
        self.registry.register(Command(
            name="project-create",
            handler=self.handle_create
        ))
        self.registry.register(Command(
            name="project-delete",
            handler=self.handle_delete
        ))
```

### Handling Configuration Migration

If your command uses `settings.json`:

```python
# Before
config = settings.get("my_command", {})

# After: plugin-specific config
class MyPlugin(MekongPlugin):
    def initialize(self, context: PluginContext):
        self.config = context.get_plugin_config(
            default={
                "option1": "value1",
                "option2": "value2"
            }
        )
```

User config migrates automatically to:
```
~/.mekong/plugins/installed/my-plugin/config.json
```

---

## Plugin Developer Guide

### Plugin Manifest Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique plugin ID (kebab-case) |
| `name` | string | Yes | Human-readable name |
| `version` | string | Yes | Semantic version |
| `description` | string | No | Short description |
| `entrypoint` | string | Yes | Path to plugin class (./plugin.py) |
| `type` | string | Yes | `"module"` or `"package"` |
| `commands` | array | No | Command definitions |
| `dependencies` | array | No | Other plugins this depends on |
| `permissions` | object | No | Required permissions |
| `mcu_cost` | number | No | Default MCU cost |

### Command Definition Schema

```json
{
  "name": "command-name",
  "description": "What this command does",
  "handler": "module.function_name",
  "arguments": [
    {
      "name": "arg_name",
      "type": "string|number|boolean",
      "description": "Argument help text",
      "required": true
    }
  ],
  "options": [
    {
      "name": "--flag",
      "type": "string",
      "description": "Option help text",
      "default": "default_value"
    }
  ],
  "permissions": {
    "file": ["read", "write"],
    "network": ["outbound"],
    "shell": ["limited"]
  },
  "mcu_cost": 1
}
```

### Plugin Lifecycle Hooks

```python
class MyPlugin(MekongPlugin):
    def initialize(self, registry: CommandRegistry):
        """Called when plugin loads."""
        pass

    def shutdown(self):
        """Called when plugin unloads."""
        pass

    def on_config_change(self, old_config, new_config):
        """Called when plugin configuration changes."""
        pass
```

### Accessing Services

```python
from mekong_plugin_sdk import PluginContext

class MyPlugin(MekongPlugin):
    def initialize(self, context: PluginContext):
        # Available services:
        self.logger = context.logger
        self.config = context.get_plugin_config()
        self.database = context.get_service("database")
        self.billing = context.get_service("billing")
        self.cache = context.get_service("cache")
```

---

## Rollback Procedures

### Immediate Rollback (Minutes)

If a plugin causes issues:

```bash
# 1. Disable plugin system
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false

# 2. Or disable specific plugin
mekong admin plugin disable <plugin-id>

# 3. Restart gateway
mekong platform restart gateway
```

### Full Rollback (Revert Migration)

If you need to revert all plugin changes:

```bash
# 1. Stop all services
mekong platform stop

# 2. Disable plugin system in settings
jq '.plugin_system.enabled = false' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# 3. Revert migration commits
cd ~/mekong-cli
git revert --no-commit \
  "feat: migrate core commands to plugins" \
  "feat: implement plugin system" \
  ...

# 4. Redeploy
bash PUBLISH.sh

# 5. Start services
mekong platform start
```

### Plugin-Specific Rollback

```bash
# Disable one problematic plugin
mekong admin plugin disable buggy-plugin

# Or remove it
rm -rf ~/.mekong/plugins/installed/buggy-plugin

# Reload registry
mekong admin plugin scan

# Restore from backup if needed
cp -r ~/.mekong/plugins.backup/buggy-plugin ~/.mekong/plugins/installed/
```

---

## FAQ

**Q: Do I need to migrate immediately?**

A: No. The legacy system continues to work. Migration is opt-in via feature flag. We recommend migrating custom commands before v7.0 when legacy support ends.

**Q: Will my existing commands break?**

A: No. Compatibility shim ensures all legacy commands work unchanged when plugin system is enabled.

**Q: Can I mix legacy and plugin commands?**

A: Yes. During migration, both systems can coexist. Feature flags control which version is used.

**Q: What about performance?**

A: Plugin cold start adds ~100-500ms overhead. Warm/cached loads are < 50ms. Performance benchmarks show < 5% impact.

**Q: Can third parties publish plugins?**

A: Yes, in v6.2+. A plugin marketplace will launch allowing community plugins.

**Q: How do I update a plugin?**

A: Replace plugin files and run `mekong admin plugin reload <id>`. With hot reload enabled, changes auto-reload.

**Q: Are plugins isolated?**

A: Optional. By default, plugins run in same process for performance. Enable `plugin_isolation: true` for worker isolation.

---

## Next Steps

1. **For Plugin Authors**: Read [Plugin Developer Guide](./plugin-developer-guide.md)
2. **For Operators**: See [Operator Runbook](./operator-runbook.md)
3. **For Migrating Teams**: See the migration examples in `packages/mekong-plugin-sdk/examples/` (or read [Plugin Developer Guide](./plugin-developer-guide.md) for full patterns)
4. **API Reference**: See [Plugin API Specification](./plugin-api-specification.md)

---

## Support

- **Migration Issues**: Check `~/.mekong/logs/plugin-migration.log`
- **Plugin Diagnostics**: `mekong admin plugin diagnose`
- **Full Documentation**: [`docs/`](./) directory
- **Community**: [mekongmind.com/guides](https://mekongmind.com/guides)

---

## Appendix: Migration Checklist

### Individual Command Migration

- [ ] Backup original command files
- [ ] Create plugin directory structure
- [ ] Write `plugin.json` manifest
- [ ] Create `plugin.py` with MekongPlugin class
- [ ] Move business logic to handlers
- [ ] Declare permissions in manifest
- [ ] Test plugin loads: `mekong admin plugin load ./path`
- [ ] Test command execution: `mekong command-name`
- [ ] Run tests: `python3 -m pytest tests/`
- [ ] Update documentation
- [ ] Enable feature flag for migrated command
- [ ] Monitor in production

### Full System Migration

- [ ] All custom commands converted to plugins
- [ ] Feature flags enable all native plugins
- [ ] Compatibility shim disabled
- [ ] Performance benchmarks pass
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
- [ ] Rollback plan tested
- [ ] Team trained on plugin development
- [ ] Deployment scripts updated
- [ ] Monitoring/alerting configured

---

**Migration Complete?** → Continue to [Plugin Developer Guide](./plugin-developer-guide.md) for advanced plugin development patterns.
