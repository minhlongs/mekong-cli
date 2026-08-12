# Plugin Documentation System Design

**Last Updated**: 2026-06-22  
**Status**: Design Document  
**Architect**: Documentation Manager  

---

## 1. Overview

This document defines the comprehensive documentation system for Mekong CLI plugins. It establishes standards, templates, and processes for creating, maintaining, and distributing plugin documentation.

### Goals

- Consistent documentation structure across all plugins
- Clear migration path from commands to plugins
- Comprehensive API reference with examples
- Troubleshooting guides for common issues
- Developer onboarding optimized for speed

---

## 2. Documentation Structure

```
docs/
├── plugins/
│   ├── index.md                    # Plugin documentation hub
│   ├── developer-guide.md          # Getting started guide
│   ├── api-reference.md            # Complete API reference
│   ├── migration-guide.md          # Command to plugin migration
│   ├── testing-framework.md        # Plugin test framework (Task #203)
│   ├── examples/
│   │   ├── minimal-plugin/         # Minimal working plugin
│   │   ├── medium-plugin/          # Plugin with permissions, config
│   │   └── advanced-plugin/        # Plugin with marketplace integration
│   ├── troubleshooting.md          # Common issues and solutions
│   ├── security-hardening.md       # Security best practices
│   ├── performance-tuning.md       # Optimization techniques
│   └── marketplace-guide.md        # Publishing and monetization
├── plugin-developer-guide.md        # Existing developer guide (to integrate)
├── plugin-architecture.md          # Existing architecture doc (to integrate)
└── plugin-test-framework-design.md # Test framework design (Task #203)
```

---

## 3. Document Standards

### 3.1 Format Requirements

All plugin documentation MUST:

- Use Markdown with 80-character line width where practical
- Include a metadata header with:
  ```markdown
  ---
  title: <Document Title>
  lastUpdated: YYYY-MM-DD
  status: Draft | Review | Stable
  audience: Developer | Operator | User
  ---
  ```
- Follow semantic heading hierarchy (H2 → H3 → H4, no skipped levels)
- Include code examples with syntax highlighting and explanations
- Provide realistic examples, not pseudocode
- Link to related documents using relative paths

### 3.2 Code Example Standards

```python
# GOOD: Complete, runnable example with context
from mekong.plugin import Plugin, PluginManifest

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="my-plugin",
            version="1.0.0"
        )
        self.register_command("hello", self.cmd_hello)
    
    def cmd_hello(self, name: str = "World") -> str:
        """Greet a user by name."""
        return f"Hello, {name}!"
```

```python
# BAD: Incomplete, unclear example
def handler():
    # do something
    pass
```

---

## 4. Plugin Developer Guide (developer-guide.md)

### Sections

1. **Introduction**
   - What are Mekong plugins?
   - When to build a plugin vs. command
   - Plugin system capabilities

2. **Quick Start** (15 minutes)
   - Prerequisites (Python 3.11+, Mekong CLI installed)
   - Create plugin skeleton
   - Implement one command
   - Test locally
   - Package for distribution

3. **Plugin Structure**
   - Directory layout
   - `mekong-plugin.json` manifest format (all fields explained)
   - Entrypoint module structure
   - Resources and assets

4. **Manifest Reference**
   Complete reference of all manifest fields:

   | Field | Type | Required | Description |
   |-------|------|----------|-------------|
   | `name` | string | yes | Plugin identifier (kebab-case) |
   | `version` | string | yes | Semantic version |
   | `entrypoint` | string | yes | Python module path |
   | `commands` | array | yes | Command definitions |
   | `permissions` | object | no | Capability requirements |
   | `dependencies` | array | no | Plugin dependencies |
   | `config` | object | no | Configuration schema |

5. **Command Implementation**
   - Command registration patterns
   - Argument handling with types
   - Output formatting (text, JSON, table)
   - Error handling best practices

6. **Permissions & Security**
   - Capability-based access control
   - Filesystem sandbox modes (`none` / `sandboxed` / `isolated`)
   - Network access controls
   - Subprocess execution limits
   - Requesting elevated permissions

7. **Configuration**
   - Plugin configuration storage
   - Secrets management
   - Environment variable overrides
   - User configuration wizard

8. **Lifecycle Hooks**
   - `initialize()`: startup tasks
   - `cleanup()`: shutdown tasks
   - `on_config_change()`: react to config updates
   - `on_plugin_enabled/disabled()`: state transitions

9. **Testing Your Plugin**
   - Unit testing patterns
   - Integration testing with test harness
   - Mocking plugin dependencies
   - Running plugin-specific test suite

10. **Packaging & Distribution**
    - Building distributable package
    - Publishing to marketplace
    - Version management
    - Signing and verification

11. **Debugging & Troubleshooting**
    - Verbose logging (`mekong plugin:log-level debug`)
    - Inspecting plugin state
    - Common pitfalls and solutions

12. **Best Practices**
    - Error handling and user feedback
    - Performance optimization
    - Memory management
    - Security hardening checklist

---

## 5. API Reference (api-reference.md)

### Structure

This document auto-generates from plugin source code and manifest schemas. Maintain as reference.

### Sections

1. **Plugin Base Class** (`mekong.plugin.Plugin`)
   ```python
   class Plugin:
       def __init__(self, name: str, version: str): ...
       def register_command(self, name: str, handler: Callable): ...
       def initialize(self) -> None: ...
       def cleanup(self) -> None: ...
   ```

2. **Plugin Manifest Schema** (JSON Schema)
   ```json
   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "type": "object",
     "required": ["name", "version", "entrypoint", "commands"],
     "properties": {
       "name": {
         "type": "string",
         "pattern": "^[a-z0-9-]+$",
         "description": "Plugin identifier"
       },
       ...
     }
   }
   ```

3. **Plugin Manager API**
   - `PluginManager.load_plugin(path: Path) -> Plugin`
   - `PluginManager.unload_plugin(name: str) -> bool`
   - `PluginManager.get_command(name: str) -> Callable`
   - `PluginManager.list_plugins() -> List[PluginInfo]`

4. **Plugin Registry API**
   - `PluginRegistry.register(manifest: dict) -> PluginRecord`
   - `PluginRegistry.uninstall(name: str) -> bool`
   - `PluginRegistry.get(name: str) -> PluginRecord`
   - `PluginRegistry.list_installed() -> List[PluginRecord]`

5. **Permissions System**
   - Capability enums: `Network`, `Filesystem`, `Subprocess`
   - Permission checking API
   - Sandbox isolation levels

6. **Hooks & Events**
   - Event types: `plugin.loaded`, `plugin.unloaded`, `command.executed`
   - Hook registration: `plugin.hooks.on('event', callback)`
   - Event payload structures

---

## 6. Migration Guide (migration-guide.md)

Target audience: Developers with existing commands to migrate to plugins.

### Sections

1. **Why Migrate?**
   - Isolation and security
   - Discoverability in marketplace
   - Independent versioning
   - Community distribution

2. **Migration Checklist**
   - [ ] Identify command to migrate
   - [ ] Create plugin manifest
   - [ ] Move command logic to plugin class
   - [ ] Update command registration
   - [ ] Add permissions requirements
   - [ ] Write tests for plugin
   - [ ] Update documentation
   - [ ] Submit to marketplace (optional)

3. **Step-by-Step Example**
   Before (command in `src/commands/my_command.py`):
   ```python
   @app.command("my-command")
   def my_command(name: str):
       return f"Hello {name}"
   ```

   After (plugin in `plugins/my-plugin/`):
   ```
   plugins/my-plugin/
   ├── mekong-plugin.json
   └── my_plugin.py
   ```

4. **Breaking Changes & Compatibility**
   - Backward compatibility layer for CLI invocation
   - Migration timeline and deprecation warnings
   - Dual registration during transition

5. **Testing Migrated Plugins**
   - Ensuring functional parity
   - Performance comparison
   - User acceptance testing

---

## 7. Example Plugins (examples/*/)

### 7.1 Minimal Plugin

**Files**:
- `mekong-plugin.json`: Single command plugin
- `plugin.py`: 20 lines of code
- `README.md`: Usage instructions

**Purpose**: Show absolute minimum viable plugin.

**Command**: `mekong plugin:install ./examples/minimal-plugin`

### 7.2 Medium Plugin

**Features**:
- Multiple commands
- Configuration with validation
- File system sandbox with read-only data directory
- Custom output formatting

**Purpose**: Typical real-world plugin patterns.

### 7.3 Advanced Plugin

**Features**:
- Marketplace integration (license validation)
- Background worker task
- Plugin-to-plugin HTTP communication
- Health check endpoint
- Metrics reporting

**Purpose**: Enterprise-grade plugin patterns.

---

## 8. Troubleshooting Guide (troubleshooting.md)

### Issues by Category

#### Installation Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `Plugin manifest invalid` | JSON syntax error | Validate with `mekong plugin:validate` |
| `Permission denied` | Insufficient filesystem rights | Check sandbox mode config |
| `Dependency not found` | Missing required plugin | Install dependency first |

#### Runtime Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Command not found after install | Plugin not loaded | Run `mekong plugin:list` to verify |
| Plugin crashes on startup | Exception in `initialize()` | Check logs: `mekong plugin:log <name>` |
| High memory usage | Memory leak in plugin | Use profiler, report to maintainer |

#### Marketplace Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Upload rejected | Manifest validation failure | Fix issues reported by validator |
| License validation fails | Network or API issue | Check connectivity, API key |

---

## 9. Security Hardening (security-hardening.md)

### Security Checklist (for plugin developers)

- [ ] Input validation on all command arguments
- [ ] Output encoding to prevent injection
- [ ] No hardcoded secrets (use config with encryption)
- [ ] Minimal permissions principle (request only what's needed)
- [ ] Secure subprocess execution (avoid `shell=True`)
- [ ] Network request validation (TLS, certificate pinning)
- [ ] File path canonicalization to prevent traversal
- [ ] Resource limits (memory, CPU, network)
- [ ] Audit logging for sensitive operations
- [ ] Regular dependency updates (vulnerability scanning)

### Reporting Security Issues

Email: security@mekongmind.com  
PGP Key: [link to key]

Include:
- Plugin name and version
- Steps to reproduce
- Expected vs actual behavior
- Potential impact

---

## 10. Performance Tuning (performance-tuning.md)

### Optimization Patterns

1. **Lazy Initialization**
   ```python
   # BAD: Expensive setup in __init__
   def __init__(self):
       self.db = connect_expensive()  # Blocks plugin load
   
   # GOOD: Defer until first use
   def initialize(self):
       self.db = None  # Connect on-demand
   
   def get_db(self):
       if self.db is None:
           self.db = connect_expensive()
       return self.db
   ```

2. **Command Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_computation(self, arg: str) -> dict:
       return compute(arg)
   ```

3. **Batch Operations**
   ```python
   # Process multiple items in one API call
   def cmd_batch(self, items: List[str]):
       results = self.api.bulk_process(items)  # vs. loop
       return results
   ```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Plugin load time | <500ms | `time mekong plugin:load` |
| Command execution P95 | <100ms | `mekong plugin:benchmark` |
| Memory overhead | <50MB | `mekong plugin:memory` |
| Startup overhead | <5% of total CLI startup | Baseline comparison |

---

## 11. Marketplace Guide (marketplace-guide.md)

### Publishing a Plugin

1. **Prepare Plugin**
   - Ensure manifest is valid: `mekong plugin:validate`
   - Add comprehensive README with usage examples
   - Include screenshots or GIFs in README
   - Set appropriate category and tags

2. **Create Publisher Account**
   - Sign up at marketplace.mekongmind.com
   - Verify email
   - Add payment info for revenue share

3. **Submit Plugin**
   - Upload plugin package (`.tar.gz`) or git repository URL
   - Fill metadata: description, category, tags, pricing tier
   - Agree to marketplace terms
   - Submit for review (typically 1-2 business days)

4. **Post-Publication**
   - Monitor user feedback and ratings
   - Respond to bug reports
   - Release updates with semantic versioning
   - Track revenue and payouts

### Revenue Sharing Model

- **Plugin sales**: Developer 70%, Marketplace 30%
- **Subscription**: Developer 65%, Marketplace 35% (covers hosting)
- **Payout schedule**: Monthly, minimum $50 threshold
- **Tax handling**: Developer responsible for own taxes

---

## 12. Documentation Build System

### GitHub Actions Workflow

`.github/workflows/plugin-docs.yml`:

```yaml
name: Plugin Documentation
on:
  push:
    paths:
      - 'docs/plugins/**'
      - 'plugins/**/mekong-plugin.json'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate API reference
        run: python scripts/generate-plugin-api-docs.py
      - name: Validate links
        run: npx markdown-link-check docs/plugins/**/*.md
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/plugins
```

---

## 13. Documentation Review Process

All plugin documentation must pass:

1. **Technical Accuracy**: Code examples tested and verified
2. **Completeness**: All required sections present
3. **Consistency**: Terminology matches codebase
4. **Links**: All internal/external links valid
5. **Accessibility**: Alt text for images, proper heading structure

Reviewers: Assigned documentation manager + technical SME

---

## 14. Templates

### Template: New Plugin README

```markdown
# {Plugin Name}

> {One-line description}

**Version**: {version}  
**License**: {license}  
**Author**: {author}  

## Installation

```bash
mekong plugin:install {plugin-name}
```

## Usage

### Basic Example

```bash
mekong {command} {args}
```

### Advanced Usage

```bash
mekong {command} --option value
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config_key` | string | `default` | Description |

Set via:
```bash
mekong config set {plugin}.{key} value
```

## Commands

| Command | Description |
|---------|-------------|
| `{cmd1}` | Description |
| `{cmd2}` | Description |

## Troubleshooting

### {Symptom}

**Problem**: Description  
**Solution**: Steps to resolve

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

## Support

- GitHub Issues: {repo}/issues
- Documentation: {docs-url}
- Community: {discord/slack}
```

---

This design provides a complete, scalable documentation system for Mekong CLI plugins with clear standards, templates, and processes.
