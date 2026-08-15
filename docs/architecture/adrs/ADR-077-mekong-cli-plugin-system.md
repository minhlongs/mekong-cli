# ADR-077: Mekong CLI Plugin System — Hybrid Modular Monolith Architecture

**Status:** Implemented
**Date:** 2026-06-20
**Task:** Multiple (T4–T23, T240, T387, T1015, etc.)
**Supersedes:** n/a

---

## Context

Mekong CLI started as a monolithic application with all commands (~342) built directly into the binary. This created several problems:

1. **Tight coupling** — All commands, regardless of domain (Studio, Founder, Business, Product, Engineering, Ops), lived in the same codebase with no isolation.
2. **Long startup time** — Importing all command modules on every CLI invocation, even when only one command was needed.
3. **No optionality** — Users who only needed Engineering commands still paid memory and startup cost for all Studio/Founder commands.
4. **No marketplace** — Third-party developers could not easily extend the CLI with their own commands.
5. **No lifecycle management** — No way to install, update, activate, deactivate, or uninstall command sets independently.
6. **Security surface** — All code ran with full privileges; no sandboxing or permission model for less-trusted extensions.

The need for a plugin system emerged as the product expanded to cover multiple business domains and as the marketplace vision (Clipmart) required extensibility.

---

## Decision

Adopt a **hybrid modular monolith with plugin extensibility** architecture:

### 1. Core vs Plugin Separation

- **Core**: 107 essential commands covering Engineering (`cook`, `fix`, `test`, `deploy`, `review`) and Ops (`audit`, `health`, `security`, `status`) layers. Core is always present, compiled into the application.
- **Plugins**: Optional extensions for other domains:
  - `studio` — VC studio operations (23 commands)
  - `founder` — Founder/strategy commands (52 commands)
  - `business` — Revenue operations: sales, marketing, finance, HR (71 commands)
  - `product` — Product management: plan, sprint, roadmap (31 commands)
  - `vietnam` — Vietnam-specific: accounting, tax, Zalo OA

Plugins are **not** separate packages initially; they live in the same repository but are loaded dynamically and can be deactivated/uninstalled without rebuilding the binary.

### 2. Plugin System Components

The implementation lives in `src/core/`:

| Component | File | Responsibility |
|-----------|------|----------------|
| `PluginRegistry` | `plugin_registry.py` | Central state, lifecycle management, persistence to `.cleo/plugins/` |
| `PluginLoader` | `plugin_loader.py` | Discovery from entry_points (`mekong.*`) and local dirs (`~/.mekong/plugins/`) |
| `PluginValidator` | `plugin_validator.py` | Security scanning: dangerous imports, secrets, syntax, interface compliance |
| `MarketplaceClient` | `plugin_marketplace.py` | Remote plugin marketplace for discovery and install info |
| `PluginManifestV2` | `manifest.py` | Hardened, frozen dataclass manifest format with checksum validation |

### 3. Plugin Manifest Format (V2)

**Schema**: `contracts/plugin-manifest-schema.json` (JSON Schema Draft 7)

**Required fields**:
- `id` — unique identifier in kebab-case (e.g., `com.mekong.studio`)
- `name` — human-readable name
- `version` — Semver 2.0.0
- `entrypoint` — path to entry module (e.g., `./plugin.py`)

**Optional fields with defaults**:
- `type` → `module`
- `export` → `MekongPlugin`
- `engines.mekong` → `^6.0.0`
- `permissions` → `{}`
- `commands` → `[]`
- `hotReload` → `true`
- `loadingMode` → `worker`

**Runtime representation** — `PluginManifestV2` (frozen dataclass):
```python
@dataclass(frozen=True)
class PluginManifestV2:
    name: str
    version: str
    capabilities: tuple[PluginCapability, ...]
    entry_point: str
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    checksum: str = ""
    isolated: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
```

**PluginCapability enum**:
```python
class PluginCapability(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    DEPLOYMENT_TARGET = "deployment_target"
    MEMORY_BACKEND = "memory_backend"
```

### 4. Plugin Discovery & Loading

**Discovery sources**:

| Source | Entry Point Group | Status |
|--------|------------------|--------|
| PyPI packages | `mekong.agents`, `mekong.providers`, `mekong.hooks` | ✅ |
| Local directory | `~/.mekong/plugins/*.py` | ✅ |
| Project plugins | `plugins/*/` | ⏳ (planned) |
| Git repositories | (planned) | ⏳ |

**Discovery process**:

1. **Entry Points**: Use `importlib.metadata.entry_points()` to find `mekong.*` groups in installed packages
2. **Local**: Scan `~/.mekong/plugins/` for `.py` files (skip `_*` and `test_*`)
3. **Validation**: Pre-execution checks (file size < 512KB, `.py` extension only, no path traversal)
4. **Loading**: Dynamic import with `importlib.util.spec_from_file_location`
5. **Registration**: Call plugin's `register(registry)` function to allow it to register commands

**Load phases** and performance:

| Phase | Purpose | Duration |
|-------|---------|----------|
| Discovery | Scan all sources | < 100ms |
| Validation | Syntax, security, interface | < 200ms per plugin |
| Loading | Dynamic import | < 50ms per plugin |
| Activation | Register commands | < 10ms per plugin |

**Total startup overhead**: < 500ms for 50 plugins (cold), < 100ms (warm)

### 5. Security Model — Defense in Depth

**Layer 1 — Pre-execution validation** (`_validate_local_plugin`):
- File size check (max 512 KB)
- Extension check (`.py` only)
- Path traversal prevention (no `..` in path)

**Layer 2 — PluginValidator**:
- **Syntax validation**: `ast.parse()` to ensure valid Python without executing
- **Dangerous import scan**: Block `subprocess`, `os.system`, `eval`, `exec`, `compile`, `__import__`, `pickle`, `marshal`
- **Secret pattern scan**: Regex for API keys, tokens, credentials (AWS/GCP/Azure/STRIPE/Polar keys)
- **Interface validation**: Ensure plugin provides `register(registry)` function
- **Dependency validation**: Check required dependencies are installed

**Layer 3 — Runtime isolation** (planned, not yet implemented):
- **Worker/process isolation** (`loadingMode`: `worker` or `process`)
- **Sandbox configuration**: `allowedModules`, `blockedModules`, `allowedHosts`
- **Permission checking**: `file`, `network`, `cli`, `billing`, `data`, `telemetry`
- **Resource limits**: `memory`, `cpuTime`, `storage`

**Blocked patterns**:
```python
DANGEROUS_IMPORTS = {
    "subprocess", "os.system", "eval", "exec", "compile",
    "__import__", "pickle", "marshal"
}

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|token|credential)\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)(AWS|GCP|AZURE|STRIPE|POLAR)_.*_KEY\s*=",
    r"sk-[a-zA-Z0-9]{32,}",
]
```

### 6. Plugin Lifecycle

**States**:
```
AVAILABLE → INSTALLED → ACTIVE → DISABLED → UNINSTALLED
    │           │           │          │
    └───────────┴───────────┴──────────┘ (can return to earlier states)
```

**Hooks**:

| Hook | When | Purpose |
|------|------|---------|
| `on_load(registry)` | Plugin activation | Register commands, initialize resources |
| `on_unload()` | Plugin deactivation | Cleanup, release resources |
| `health_check()` | Health queries | Return plugin health status |
| `before_command(ctx)` | Before command execution | Pre-processing |
| `after_command(ctx)` | After command execution | Post-processing, logging |
| `command_error(ctx, exc)` | Command failure | Error handling |

**Registry persistence**: Plugin state (installed, active, disabled) persisted in `.cleo/plugins/registry.json` for survival across restarts.

### 7. Command Registration Integration

Plugins register commands via the global `CommandRegistry`:

```python
def register(registry):
    registry.register(
        name="my-command",
        callback=my_command_function,
        plugin=my_plugin_metadata,
        spec={"description": "...", "allowed_tools": [...]}
    )
```

Core commands use `register_core()` to bypass plugin checks. The unified registry ensures all commands (core + plugin) are discovered by the command fabric (`command-fabric export`) and dispatched consistently.

### 8. Unified MCU Billing

The existing `MCUManager` (`.cleo/core/billing/mcu_manager.py`) handles billing for both core and plugin commands:

- Each plugin command declares its MCU cost in the command spec
- `check_and_deduct()` is called before command execution
- `track_usage()` logs consumption for analytics
- Plugins cannot bypass billing; the gate is in the dispatch layer

### 9. Backward Compatibility

- Existing `.claude/commands/` files continue to work unchanged
- Core commands are still registered via Typer as before; plugin system does not alter core behavior
- CLI startup automatically loads installed plugins but does not require any to be active
- Disabling a plugin makes its commands disappear from the catalog but does not affect core

---

## Rationale

### Why a Hybrid Modular Monolith (Not Microservices)?

- **Deployment simplicity**: Single binary, no network overhead, no service discovery
- **Developer ergonomics**: Plugin developers can debug with `mekong` directly, no separate server
- **Performance**: In-process calls are faster than RPC; no serialization overhead
- **Monorepo alignment**: All plugins (Studio, Founder, Business, Product, Vietnam) are developed in the same repository and released together

### Why Dynamic Loading (Not Static Imports)?

- **Optionality**: Plugins can be deactivated/uninstalled without rebuilding
- **Marketplace**: Third-party plugins from PyPI can be installed at runtime
- **Startup cost**: Import only when needed; cold startup < 500ms even with 50 plugins
- **Isolation**: Each plugin gets its own module namespace; conflicts are contained

### Why Worker/Process Isolation (Planned) Instead of In-Process Only?

- **Security**: Less-trusted third-party plugins (from marketplace) should not run in the same process as billing logic
- **Stability**: A segfault in a native extension in one plugin should not crash the entire CLI
- **Resource limits**: Per-process limits are easier to enforce than in-process quotas
- **Future-proof**: Enables sandboxing via containers or VMs if needed

### Why Hardened Manifest (`PluginManifestV2`) Instead of Loose JSON?

- **Validation**: Frozen dataclass enforces type safety at load time
- **Checksum**: Allows integrity verification of plugin files after install
- **Immutability**: Frozen prevents accidental mutation during lifecycle
- **Performance**: Dataclass is faster to instantiate than dict parsing

---

## Consequences

### What Changes

- **New modules** in `src/core/`:
  - `plugin_loader.py` (≈180 lines)
  - `plugin_registry.py` (≈220 lines)
  - `plugin_validator.py` (≈250 lines)
  - `plugin_marketplace.py` (≈150 lines)
  - `manifest.py` (≈120 lines)
- **New directory**: `.cleo/plugins/` for plugin registry persistence
- **New CLI commands** (in `plugin` command group):
  - `mekong plugin list` — show installed plugins
  - `mekong plugin install <id>` — install from PyPI or marketplace
  - `mekong plugin uninstall <id>` — remove plugin
  - `mekong plugin activate <id>` / `deactivate <id>`
  - `mekong plugin validate <path>` — pre-install validation
  - `mekong plugin search <query>` — marketplace search
- **Extended command registry** to accept `plugin` parameter and distinguish core vs plugin commands
- **Gate in dispatch layer**: Before executing any command, check if plugin is ACTIVE; if not, return `E_PLUGIN_DISABLED`
- **Health monitoring**: Plugin health status reported in `cleo health` output
- **Audit logging**: Plugin lifecycle events (install, activate, deactivate, uninstall) written to audit log

### What Stays the Same

- **Core command implementation** — No changes needed to existing commands; they register via existing Typer mechanisms
- **MCU billing** — Existing billing integration points remain; plugin commands just declare their cost in the spec
- **Command fabric** — Plugin commands are automatically included in `command-fabric export` because they register in the same CommandRegistry
- **Harness evaluation** — Core DNA tests still pass; plugin-specific checks are additive

### Migration Impact

- **No migration needed for existing users** — Plugin system is fully backward compatible; core commands work identically
- **Plugin developers** must:
  1. Create `pyproject.toml` with `[tool.mekong.agents]` or `[tool.mekong.providers]` entry points
  2. Implement `MekongPlugin` base class or `register(registry)` function
  3. Provide `PluginManifestV2` compatible manifest (can be auto-generated from `pyproject.toml`)
  4. Publish to PyPI or distribute as local plugin

### Performance Characteristics

- **Cold startup with 50 plugins**: < 500ms overhead (discovery + validation + load)
- **Warm startup** (plugins already loaded in memory): < 100ms
- **Per-command overhead**: < 1ms (registry lookup) — negligible
- **Memory overhead**: ~5MB per loaded plugin (module code + data structures)

### Operational Considerations

- **Plugin registry corruption** → Rebuild by rescanning entry points and local plugins: `mekong plugin repair`
- **Plugin breaking change** → Pin version in `engines.mekong`; Mekong checks compatibility on load
- **Malicious plugin** → Security scanner blocks dangerous imports before execution; marketplace runs additional static analysis
- **Plugin dependency conflicts** → Dependency validation catches missing requirements before activation

---

## Supersedes

n/a (new subsystem)

---

## Cross-References

- **ADR-004**: TypeScript-First Architecture — Plugin system is Python-based but respects the shared-core principle; plugin loader integrates with dispatch layer
- **ADR-008**: CLEO Canonical Architecture — Plugin registry is part of the canonical shared-core; plugins delegate to core for billing, logging, audit
- **ADR-016**: Installation Channels — Plugin discovery respects the same installation channel semantics (npm global, local, dev symlink)
- **docs/plugin-architecture.md**: Complete plugin architecture specification (v1.0.0, 2026-06-20)
- **docs/plugin-developer-guide.md**: Guide for plugin developers
- **docs/plugin-security-hardening.md**: Security model deep dive
- **docs/plugin-isolation-model.md**: Isolation and sandboxing design
- **docs/plugin-api-specification.md**: API reference for `PluginRegistry`, `PluginLoader`, etc.
- **docs/plugin-migration-guide.md**: Migration from legacy monolith to plugin-based organization

---

## Related Tasks

| Epic | Task | Title |
|------|------|-------|
| T4 | T4–T23 | Plugin System Design Epic (architecture, SDK, loader, manifest, isolation, security) |
| T240 | T240 | Complete Plugin SDK Design and Package Setup |
| T387 | T387 | Implement Plugin Infrastructure Integration and Migrate Business Plugin |
| T1015 | T1015 | Plugin Loader Architecture Design |
| T1410 | T1410 | Plugin Validation CI Workflow |
| T1820 | T1820 | Plugin Health Monitoring System |
| T2205 | T2205 | Plugin Isolation Unit Tests |
| T2610 | T2610 | Plugin Documentation System |
| T3015 | T3015 | Plugin Marketplace Implementation |
| T3420 | T3420 | Plugin Runtime Isolation (worker/process mode) |

---

## Implementation Notes

### File Placement Rationale

All plugin system components live in `src/core/` (not `src/plugins/`) because:
- The plugin system is part of the **core runtime**, not a plugin itself
- Core modules must be available before any plugin is loaded
- Shared dependencies (`registry.py`, `billing/`, `logging/`) are in `src/core/`

### Plugin Manifest Discovery

Plugins can provide manifests via:

1. **Entry points** (PyPI packages):
   ```toml
   [tool.mekong.agents]
   my-plugin = "my_package.plugin:register"
   ```

2. **Local files** (`~/.mekong/plugins/`):
   - Each `.py` file is validated and loaded
   - Plugin must define `register(registry)` at module level

3. **Project plugins** (planned):
   - `plugins/<name>/plugin.py`
   - Auto-discovered on project initialization

### Compatibility Checking

When a plugin loads:

1. Read `engines.mekong` from manifest (e.g., `^6.0.0`)
2. Compare against `__version__` from `mekong/__init__.py`
3. If incompatible, log warning but still load (soft failure)
4. Registry marks plugin as `compatible=False`; health check reports issue

### Hot Reload

`hotReload: true` (default) enables:
- File modification time check on every `mekong <command>` invocation
- If plugin file changed, reload the plugin (validate → load → activate)
- Useful for plugin development; disable in production for stability

Set `loadingMode: process` (future) to run plugin in separate process; hot reload becomes process restart.

### Marketplace Integration

`MarketplaceClient` provides:
- `search(query)` — search available plugins
- `get_plugin(id)` — fetch plugin metadata, download URL, checksum
- `install_info(id)` — get install instructions (used by `mekong plugin install`)

Marketplace is **read-only**; plugin binaries are still fetched from PyPI or direct URL. Marketplace provides trust metadata (verified publisher, security scan results, ratings).

---

## Verification

### Unit Tests

```bash
python3 -m pytest tests/test_plugin_*.py -q
# Expected: tests/test_plugin_loader.py, test_plugin_registry.py,
# test_plugin_validator.py, test_plugin_marketplace.py — all pass
```

### Integration Tests

```bash
# Install a test plugin from local file
mekong plugin validate tests/fixtures/plugins/example_plugin.py
mekong plugin install --local tests/fixtures/plugins/example_plugin.py
mekong plugin list  # should show example plugin as ACTIVE
mekong example-hello  # run a command from the plugin
mekong plugin deactivate example
mekong plugin uninstall example
```

### Security Scan Validation

```bash
# Plugin with dangerous import should be rejected
echo "import subprocess" > /tmp/bad_plugin.py
mekong plugin validate /tmp/bad_plugin.py
# Exit code non-zero, error message mentions "subprocess"
```

### Compatibility Check

```bash
# Plugin with incompatible engines.mekong should warn but load
mekong plugin install --local tests/fixtures/plugins/incompatible_plugin.py
# Log: "WARNING: plugin 'test-incompatible' requires mekong ^99.0.0, current is 6.0.0"
# Plugin appears in list with compatible=False
```

### Performance Benchmark

```bash
# Cold startup with 50 dummy plugins
python3 -m timeit -s "import subprocess; cmd='mekong status'" \
  "subprocess.run(cmd.split(), capture_output=True)"
# Should be < 2s total (including 500ms plugin overhead)
```

---

## Open Questions

1. **Process isolation**: When will `loadingMode: process` be implemented? This is critical for third-party marketplace plugins but requires IPC for command registration and execution.
2. **Plugin dependency resolution**: Currently `dependencies` is informational only. Should Mekong automatically `pip install` missing dependencies?
3. **Plugin upgrade**: `mekong plugin upgrade <id>` not yet implemented. Should it check PyPI for newer version or only accept explicit install URL?
4. **Plugin signing**: How to enforce signed manifests for marketplace plugins? GPG orSigstore?
5. **Resource accounting**: Per-plugin MCU tracking exists but not enforced quotas. Should plugins be able to declare `maxMcuPerDay`?
6. **Project-scoped plugins**: `plugins/*/` auto-discovery needs project-specific activation logic (some plugins enabled in project A but not project B).

---

## Future Roadmap (Out of Scope for This ADR)

- **Phase 2 — Process Isolation**: `loadingMode: process` spawns subprocess; communication via stdin/stdout JSON-RPC
- **Phase 3 — Sandboxing**: `allowedModules`, `blockedModules`, `allowedHosts` enforcement via `RestrictedPython` or custom AST transformer
- **Phase 4 — Marketplace V2**: Plugin ratings, reviews, verified publisher badges, automated security scan pipeline
- **Phase 5 — Plugin Dependencies**: Automatic dependency resolution and installation from PyPI
- **Phase 6 — Per-Project Plugin Configuration**: `.cleo/plugins.toml` enabling/disabling plugins per project
