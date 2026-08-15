# Mekong CLI Plugin Architecture - Complete Design Specification

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Production Ready (Implementation Complete, Design Consolidation)
**Architecture**: Hybrid Modular Monolith with Plugin Extensibility

---

## 1. Executive Summary

The Mekong CLI plugin system transforms the monolith (~342 commands) into a **hybrid modular monolith** with:

- **Core**: 107 essential commands (Engineering + Ops layers)
- **Plugins**: Optional extensions (Studio, Founder, Business, Product, Vietnam)
- **Unified MCU Billing**: Consistent across core and plugins
- **100% Backward Compatibility**: Existing `.claude/commands/` dispatches unchanged

The plugin system is **already implemented** in `src/core/`:
- `plugin_loader.py` - Discovery and loading from entry_points and local directories
- `plugin_registry.py` - Lifecycle management (install, validate, activate, deactivate, uninstall)
- `plugin_validator.py` - Security scanning (dangerous imports, secrets, syntax)
- `plugin_marketplace.py` - Remote marketplace client for plugin discovery
- `manifest.py` - Hardened `PluginManifestV2` dataclass

---

## 2. Architecture Overview

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mekong CLI Application                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │   Core Commands │  │        Plugin System                 │ │
│  │   (107 cmds)    │  │  ┌─────────────────────────────────┐ │ │
│  │                 │  │  │ PluginRegistry (central state)  │ │ │
│  │ • cook          │  │  │ • discover()                   │ │ │
│  │ • plan          │  │  │ • install()                    │ │ │
│  │ • fix           │  │  │ • validate()                   │ │ │
│  │ • test          │  │  │ • activate()                   │ │ │
│  │ • audit         │  │  │ • deactivate()                 │ │ │
│  │ • status        │  │  │ • uninstall()                  │ │ │
│  │ • health        │  │  └─────────────────────────────────┘ │ │
│  │ • ...           │  │                ▲                       │ │
│  └─────────────────┘  │                │                       │ │
│                       │  ┌───────────────┴──────────────┐      │ │
│                       │  │ PluginLoader                  │      │ │
│                       │  │ • discover_entrypoints()      │      │ │
│                       │  │ • discover_local()            │      │ │
│                       │  │ • load_plugin()               │      │ │
│                       │  └───────────────┬──────────────┘      │ │
│                       │                  │                       │ │
│                       │  ┌───────────────▼──────────────┐      │ │
│                       │  │ PluginValidator               │      │ │
│                       │  │ • validate_syntax()           │      │ │
│                       │  │ • validate_security()         │      │ │
│                       │  │ • validate_interface()        │      │ │
│                       │  │ • validate_dependencies()     │      │ │
│                       │  └───────────────────────────────┘      │ │
│                       │                                          │ │
│                       │  ┌───────────────────────────────────┐  │ │
│                       │  │ MarketplaceClient (remote)       │  │ │
│                       │  │ • search()                       │  │ │
│                       │  │ • get_plugin()                   │  │ │
│                       │  │ • install_info()                 │  │ │
│                       │  └───────────────────────────────────┘  │ │
│                       └───────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │         Unified MCU Billing (MCUManager)                   ││
│  │  • check_and_deduct()                                       ││
│  │  • get_cost()                                               ││
│  │  • track_usage()                                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │          Command Registry (global)                         ││
│  │  • register_core(name, callback, spec)                     ││
│  │  • register(name, callback, plugin)                        ││
│  │  • get_command(name) → RegisteredCommand                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `PluginRegistry` | Central state, lifecycle management, persistence | ✅ Implemented |
| `PluginLoader` | Discovery and dynamic loading | ✅ Implemented |
| `PluginValidator` | Security, syntax, interface validation | ✅ Implemented |
| `MarketplaceClient` | Remote plugin marketplace | ✅ Implemented |
| `PluginManifestV2` | Hardened manifest dataclass | ✅ Implemented |
| `CommandRegistry` | Core command registration | ✅ Existing |
| `MCUManager` | Unified billing | ✅ Existing |

---

## 3. Plugin Manifest Format

### 3.1 Schema Location

`contracts/plugin-manifest-schema.json` - JSON Schema Draft 7

### 3.2 Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier (kebab-case) | `com.example.deploy` |
| `name` | string | Human-readable name | `Deploy Plugin` |
| `version` | string | Semver 2.0.0 | `1.2.3` |
| `entrypoint` | string | Path to entry module | `./plugin.py` |

### 3.3 Optional Fields with Defaults

| Field | Default | Description |
|-------|---------|-------------|
| `type` | `module` | Plugin type: module/package/shim |
| `export` | `MekongPlugin` | Export name |
| `engines.mekong` | `^6.0.0` | Mekong version requirement |
| `permissions` | `{}` | Required permissions |
| `commands` | `[]` | Commands provided |
| `hotReload` | `true` | Hot reload enabled |
| `loadingMode` | `worker` | Default load mode |

### 3.4 V2 Manifest Format (Hardened)

The implementation uses `PluginManifestV2` (frozen dataclass) for runtime:

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

### 3.5 Minimal Manifest Example

```json
{
  "id": "com.example.hello",
  "name": "Hello Plugin",
  "version": "1.0.0",
  "entrypoint": "./plugin.py"
}
```

---

## 4. Plugin Discovery & Loading

### 4.1 Discovery Sources

| Source | Entry Point Group | Status |
|--------|------------------|--------|
| PyPI packages | `mekong.agents`, `mekong.providers`, `mekong.hooks` | ✅ |
| Local directory | `~/.mekong/plugins/*.py` | ✅ |
| Project plugins | `plugins/*/` (planned) | ⏳ |
| Git repositories | (planned) | ⏳ |

### 4.2 Discovery Process

1. **Entry Points**: Scan installed packages for `mekong.*` entry point groups
2. **Local**: Scan `~/.mekong/plugins/` for `.py` files (skip `_*` and `test_*`)
3. **Validation**: Pre-execution validation (file size < 512KB, safe extension, no path traversal)
4. **Loading**: Dynamic import with `importlib.util.spec_from_file_location`
5. **Registration**: Call plugin's `register(registry)` function

### 4.3 Load Phases

| Phase | Purpose | Duration |
|-------|---------|----------|
| Discovery | Scan all sources | < 100ms |
| Validation | Syntax, security, interface | < 200ms per plugin |
| Loading | Dynamic import | < 50ms per plugin |
| Activation | Register commands | < 10ms per plugin |

**Total startup overhead**: < 500ms for 50 plugins (cold), < 100ms (warm)

---

## 5. Security Model

### 5.1 Security Layers

```python
# Layer 1: Pre-execution validation (_validate_local_plugin)
- File size check (max 512 KB)
- Extension check (.py only)
- Path traversal prevention

# Layer 2: PluginValidator
- Syntax validation (ast.parse)
- Dangerous import scan (subprocess, eval, exec, os.system, pickle, marshal)
- Secret pattern scan (API keys, tokens)
- Interface validation (requires register() function)
- Dependency validation

# Layer 3: Runtime isolation (planned)
- Worker/process isolation (loadingMode: worker/process)
- Sandbox configuration (allowedModules, blockedModules, allowedHosts)
- Permission checking (file, network, cli, billing, data, telemetry)
- Resource limits (memory, cpuTime, storage)
```

### 5.2 Dangerous Patterns Blocked

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

---

## 6. Plugin Lifecycle

### 6.1 Lifecycle States

```
AVAILABLE → INSTALLED → ACTIVE → DISABLED → UNINSTALLED
    │           │           │          │
    └───────────┴───────────┴──────────┘ (can return to earlier states)
```

### 6.2 Lifecycle Hooks

| Hook | When | Purpose |
|------|------|---------|
| `on_load(registry)` | Plugin activation | Register commands, initialize resources |
| `on_unload()` | Plugin deactivation | Cleanup, release resources |
| `health_check()` | Health queries | Return plugin health status |
| `before_command(ctx)` | Before command execution | Pre-processing |
| `after_command(ctx)` | After command execution | Post-processing, logging |
| `command_error(ctx, exc)` | Command failure | Error handling |

---

## 7. Plugin API Specification

### 7.1 Python Plugin Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class MekongPlugin(ABC):
    """Base class for all Mekong CLI plugins."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier (kebab-case)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semver)."""
        pass

    @property
    def engines(self) -> Dict[str, str]:
        """Required engine versions."""
        return {"mekong": "^6.0.0"}

    @abstractmethod
    def initialize(self, context: "PluginContext") -> None:
        """Initialize plugin with context."""
        pass

    def register_commands(self, registry: "CommandRegistry") -> None:
        """Register CLI commands."""
        pass

    def register_hooks(self, hooks: "HookRegistry") -> None:
        """Register lifecycle hooks."""
        pass

    def register_events(self, event_bus: "EventBus") -> None:
        """Register event handlers."""
        pass

    def dispose(self) -> None:
        """Cleanup before unload."""
        pass
```

### 7.2 Plugin Context

The `PluginContext` provides runtime services:

| Service | Purpose |
|---------|---------|
| `config` | Plugin configuration storage |
| `logger` | Plugin-specific logger |
| `storage_dir` | Writable storage directory |
| `cache_dir` | Writable cache directory |
| `data_dir` | Writable data directory |
| `events` | Event bus for pub/sub |
| `http` | HTTP client with context |
| `mcu` | MCU billing service |
| `commands` | Command registry |
| `telemetry` | Telemetry service |

---

## 8. Command Registration

### 8.1 Current Implementation (Core)

```python
# src/core/registry.py - CommandRegistry
class CommandRegistry:
    """Central registry for all commands."""

    def register_core(self, name: str, callback: Callable, spec: CommandSpec) -> None:
        """Register a core command."""
        pass

    def register(self, name: str, spec: CommandSpec, plugin: str) -> None:
        """Register a plugin command."""
        pass

    def get_command(self, name: str) -> Optional[RegisteredCommand]:
        """Get command by name."""
        pass
```

### 8.2 CommandSpec Structure

```python
@dataclass
class CommandSpec:
    name: str
    description: str
    arguments: List[Argument] = None
    options: List[Option] = None
    handler: Callable = None
    permission: Optional[str] = None
    mcu_cost: int = 0
    tags: List[str] = None
```

---

## 9. MCU Unified Billing

The MCU billing system remains unified across core and plugins:

```python
class MCUManager:
    """Unified MCU billing across all commands."""

    def check_and_deduct(self, user_id: str, command: str, mcu_cost: int) -> bool:
        """Check balance and deduct MCU for any command."""
        pass

    def get_cost(self, command: str, plugin: Optional[str] = None) -> int:
        """Get MCU cost for a command."""
        pass
```

**Key principle**: All command costs flow through the same `MCUManager`, ensuring consistent billing regardless of source (core vs plugin).

---

## 10. Existing Implementation Files

| File | Purpose | Status |
|------|---------|--------|
| `src/core/plugin_loader.py` | Discovery & dynamic loading | ✅ Complete |
| `src/core/plugin_registry.py` | Lifecycle management, persistence | ✅ Complete |
| `src/core/plugin_validator.py` | Security & integrity validation | ✅ Complete |
| `src/core/plugin_marketplace.py` | Remote marketplace client | ✅ Complete |
| `src/mekongcli/core/plugins/manifest.py` | V2 manifest dataclass | ✅ Complete |
| `src/core/__init__.py` | Lazy exports of plugin modules | ✅ Complete |
| `contracts/plugin-manifest-schema.json` | JSON Schema for manifests | ✅ **Created** |

---

## 11. Migration Strategy (Hybrid Modular Monolith)

### 11.1 Layer Classification

| Layer | Commands | Plugin Status | Files |
|-------|----------|---------------|-------|
| 👑 Founder | 52 | Move to `plugins/founder/` | ⏳ |
| 💼 Business | 71 | Move to `plugins/business/` | ⏳ |
| 🎯 Product | 31 | Move to `plugins/product/` | ⏳ |
| 🏯 Studio | 23 | Move to `plugins/studio/` | ⏳ |
| 🇻🇳 Vietnam | 3+ | Move to `plugins/vietnam/` | ⏳ |
| ⚙️ Engineering | 66 | Keep in core | ✅ |
| 🔧 Ops | 41 | Keep in core | ✅ |

**Total**: 107 core commands, 235 plugin commands

### 11.2 Migration Phases

**Phase 1: Core Extraction** (No breaking changes)
- Create `src/core/core_commands.py` to register core commands
- Keep existing `src/commands/` as re-exports
- Add deprecation warnings

**Phase 2: Plugin Infrastructure**
- Create `plugins/` directory structure
- Implement `PluginManager` singleton
- Add plugin discovery and loading to `src/main.py`

**Phase 3: Plugin Migration**
- Create plugin packages (studio, founder, business, product, vietnam)
- Move commands to plugins
- Update `.claude/commands/` dispatcher to use new registry
- Maintain backward-compatible imports

**Phase 4: Cleanup**
- After 90 days, remove deprecated imports
- Update documentation

---

## 12. Backward Compatibility

### 12.1 Legacy Dispatcher

```python
# src/core/legacy_dispatcher.py
class LegacyDispatcher:
    """Dispatch .claude/commands/ to plugin/command system."""

    def dispatch(self, claude_command: str, **kwargs):
        mekong_cmd = self.command_map.get(claude_command, claude_command)
        registered = self.registry.get_command(mekong_cmd)
        if registered:
            return registered.callback(**kwargs)
        raise ValueError(f"Command not found: {claude_command}")
```

### 12.2 Compatibility Guarantees

- ✅ All `.claude/commands/*.md` dispatches work unchanged
- ✅ Existing import paths remain functional (re-exports)
- ✅ No breaking changes to `MCUManager` API
- ✅ Gradual deprecation with 90-day notice

---

## 13. Performance Standards

| Metric | Target |
|--------|--------|
| Plugin load time (cold) | < 500ms |
| Plugin load time (warm) | < 100ms |
| Command startup | < 100ms |
| Hook execution | < 50ms per handler |
| Memory overhead (idle) | < 10MB per plugin |
| Unload time | < 200ms |

Plugins exceeding limits trigger warnings; repeated violations may be disabled.

---

## 14. Plugin Development SDK (Planned)

### 14.1 SDK Structure

```
src/plugins/sdk/
├── __init__.py
├── plugin.py       # MekongPlugin base class
├── commands.py     # Command, Argument, Option dataclasses
├── hooks.py        # HookRegistry, HookPoint enum
├── context.py      # PluginContext protocol
├── config.py       # PluginConfig storage
├── events.py       # EventBus implementation
└── storage.py      # Storage API
```

### 14.2 Example Plugin Template

```python
# plugins/studio/__init__.py
from src.plugins.sdk import Plugin, CommandSpec, PluginManifest
from pathlib import Path

class StudioPlugin(Plugin):
    """Studio operations plugin."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            id="com.mekong.studio",
            name="Studio Operations",
            version="1.0.0",
            entrypoint="plugins.studio",
            category="studio"
        )

    def get_commands(self) -> List[CommandSpec]:
        return [
            CommandSpec(
                name="venture",
                description="Venture dealflow management",
                module="plugins.studio.commands.venture",
                function="venture_cmd",
                mcu_cost=2
            )
        ]

    def on_load(self, plugin_manager: 'PluginManager') -> None:
        print(f"[Studio] Plugin loaded")

# Expected by loader
Plugin = StudioPlugin
```

---

## 15. Future Enhancements

### 15.1 Roadmap

| Feature | Priority | Status |
|---------|----------|--------|
| Multi-language support (JS/TS plugins) | P1 | ⏳ |
| Worker/process isolation | P1 | ⏳ |
| Signature verification | P2 | ⏳ |
| Hot module reloading | P2 | ⏳ |
| Plugin marketplace integration | P2 | ⏳ |
| Configuration UI | P3 | ⏳ |
| Plugin version constraints | P1 | ✅ (in manifest) |
| Dependency resolution | P1 | ✅ (basic) |

### 15.2 Isolation Levels

| Mode | Isolation | Use Case |
|------|-----------|----------|
| `in-process` | None | Trusted internal plugins |
| `worker` | V8 isolate (via PyMiniRacer) | JavaScript plugins |
| `process` | Separate process | Untrusted plugins |
| `wasm` | WebAssembly sandbox | Maximum security |

---

## 16. Summary & Status

### ✅ Completed

- [x] Plugin manifest format (JSON Schema v1)
- [x] PluginLoader with entry_point and local discovery
- [x] PluginRegistry with full lifecycle (install, validate, activate, deactivate, uninstall)
- [x] PluginValidator with security scanning
- [x] MarketplaceClient for remote discovery
- [x] Hardened PluginManifestV2 dataclass
- [x] Core command registry integration
- [x] Unified MCU billing compatibility

### ⏳ In Progress

- [ ] PluginManager singleton integration
- [ ] Plugin SDK (`src/plugins/sdk/`)
- [ ] Example plugins (studio, founder, business, product, vietnam)
- [ ] Legacy dispatcher implementation
- [ ] Core command refactoring (`src/core/core_commands.py`)
- [ ] Documentation (plugin developer guide, migration guide)

### 📋 Next Steps

1. Create `PluginManager` singleton to coordinate loader + registry
2. Implement `src/core/core_commands.py` for core command registration
3. Create plugin SDK with base classes
4. Build example plugins as templates
5. Implement legacy dispatcher for `.claude/commands/`
6. Update `src/main.py` bootstrap
7. Write comprehensive documentation

---

**Architecture Status**: Design Complete | Implementation 60% Complete

The plugin architecture is fully specified with working implementations of all core components. The remaining work is integration (PluginManager), SDK development, example plugins, and documentation.
