# Plugin API Reference

**Last Updated**: 2026-06-22  
**Status**: Stable  
**Audience**: Plugin developers, SDK contributors  
**Version**: v1.0.0

---

## Overview

This document provides a comprehensive API reference for the Mekong CLI Plugin System. It covers all public classes, methods, and interfaces available to plugin developers.

The plugin system provides:

- **Plugin base class** for creating custom plugins
- **Plugin registry** for discovering and managing plugins
- **Plugin loader** for dynamic module loading and isolation
- **Plugin validator** for manifest and dependency validation
- **Health monitoring** for plugin observability
- **Marketplace integration** for plugin distribution

## Quick Start

```python
from mekong.plugin import Plugin, PluginContext

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__(
            id="com.example.myplugin",
            name="My Plugin",
            version="1.0.0"
        )
    
    async def initialize(self, ctx: PluginContext):
        """Initialize plugin with context"""
        self.logger.info("Plugin initialized")
    
    async def execute(self, ctx: PluginContext, **kwargs):
        """Main plugin execution"""
        return {"result": "success"}

# Register plugin
plugin = MyPlugin()
```

## Table of Contents

- [Plugin Class](#plugin-class)
- [PluginContext](#plugincontext)
- [PluginManifest](#pluginmanifest)
- [PluginRegistry](#pluginregistry)
- [PluginLoader](#pluginloader)
- [PluginValidator](#pluginvalidator)
- [PluginHealthMonitor](#pluginhealthmonitor)
- [Enums and Types](#enums-and-types)
- [Exceptions](#exceptions)

---

## Plugin Class

The base `Plugin` class that all plugins must inherit from.

### Class Definition

```python
class Plugin:
    """Base plugin class for Mekong CLI."""
    
    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        dependencies: list[str] = None
    ):
        ...
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | `str` | Yes | Unique plugin identifier (reverse DNS format, e.g., `com.example.myplugin`) |
| `name` | `str` | Yes | Human-readable plugin name |
| `version` | `str` | Yes | Plugin version (semver 2.0.0 format, e.g., `1.0.0`) |
| `description` | `str` | No | Short plugin description (max 500 chars) |
| `author` | `str` | No | Plugin author or organization |
| `dependencies` | `list[str]` | No | List of required plugin dependencies |

### Methods

#### `initialize(ctx: PluginContext) -> None`

Called when plugin is loaded and initialized.

**Parameters**:

- `ctx` (`PluginContext`): Plugin context with configuration, logger, and services

**Raises**:

- `PluginInitializationError`: If initialization fails

**Example**:

```python
async def initialize(self, ctx: PluginContext):
    # Access configuration
    api_key = ctx.config.get("api_key")
    
    # Access logger
    ctx.logger.info("Initializing with API key")
    
    # Access other plugins
    cache = await ctx.get_plugin("com.example.cache")
    
    # Set up resources
    self.db = await connect_database(ctx.config["database_url"])
```

#### `execute(ctx: PluginContext, **kwargs) -> Any`

Main plugin execution method. Called when plugin is invoked.

**Parameters**:

- `ctx` (`PluginContext`): Plugin context
- `**kwargs`: Plugin-specific arguments

**Returns**:

- Any JSON-serializable result

**Raises**:

- `PluginExecutionError`: If execution fails

**Example**:

```python
async def execute(self, ctx: PluginContext, query: str, limit: int = 10):
    # Validate inputs
    if not query:
        raise ValueError("query is required")
    
    # Execute plugin logic
    results = await self.search(query, limit)
    
    # Return results
    return {
        "query": query,
        "count": len(results),
        "results": results
    }
```

#### `shutdown(ctx: PluginContext) -> None`

Called when plugin is being unloaded. Clean up resources.

**Parameters**:

- `ctx` (`PluginContext`): Plugin context

**Example**:

```python
async def shutdown(self, ctx: PluginContext):
    # Close database connections
    if self.db:
        await self.db.close()
    
    # Cancel background tasks
    for task in self.background_tasks:
        task.cancel()
    
    ctx.logger.info("Plugin shut down cleanly")
```

#### `health_check(ctx: PluginContext) -> dict`

Optional health check endpoint. Return plugin health status.

**Parameters**:

- `ctx` (`PluginContext`): Plugin context

**Returns**:

- `dict` with health status, e.g., `{"status": "healthy", "timestamp": "..."}`

**Example**:

```python
async def health_check(self, ctx: PluginContext) -> dict:
    # Check database connectivity
    db_healthy = await self.db.ping()
    
    # Check external API
    api_healthy = await check_external_api()
    
    status = "healthy" if (db_healthy and api_healthy) else "unhealthy"
    
    return {
        "status": status,
        "checks": {
            "database": "ok" if db_healthy else "error",
            "external_api": "ok" if api_healthy else "error"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## PluginContext

Context object passed to plugin methods containing runtime services.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `dict[str, Any]` | Plugin configuration (from manifest `config` field or environment) |
| `logger` | `logging.Logger` | Plugin-specific logger instance |
| `plugin_id` | `str` | ID of the current plugin |
| `plugin_version` | `str` | Version of the current plugin |
| `metadata` | `dict[str, Any]` | Runtime metadata (deployment info, environment, etc.) |

### Methods

#### `async get_plugin(plugin_id: str) -> Plugin`

Retrieve another plugin by ID.

**Parameters**:

- `plugin_id` (`str`): ID of the plugin to retrieve

**Returns**:

- `Plugin` instance if found

**Raises**:

- `PluginNotFoundError`: If plugin not found

**Example**:

```python
cache_plugin = await ctx.get_plugin("com.example.cache")
cached = await cache_plugin.get("key")
```

#### `async invoke_plugin(plugin_id: str, method: str, **kwargs) -> Any`

Invoke a method on another plugin.

**Parameters**:

- `plugin_id` (`str`): ID of the plugin to invoke
- `method` (`str`): Method name to call
- `**kwargs`: Arguments to pass to the method

**Returns**:

- Result from the invoked plugin method

**Example**:

```python
result = await ctx.invoke_plugin(
    "com.example.formatter",
    "format",
    text="Hello World",
    format="json"
)
```

#### `async emit_event(event_type: str, data: dict) -> None`

Emit an event that other plugins can listen to.

**Parameters**:

- `event_type` (`str`): Event type (e.g., `"user.signup"`, `"plugin.installed"`)
- `data` (`dict`): Event payload

**Example**:

```python
await ctx.emit_event("user.created", {
    "user_id": user.id,
    "email": user.email,
    "created_at": user.created_at.isoformat()
})
```

---

## PluginManifest

Dataclass representing a plugin manifest (plugin.json/mekong-plugin.json).

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique plugin identifier |
| `name` | `str` | Yes | Human-readable name |
| `version` | `str` | Yes | Semantic version |
| `description` | `str` | No | Plugin description |
| `type` | `str` | No | Plugin type (`module`, `package`, `shim`) |
| `entrypoint` | `str` | Yes | Path to entry module |
| `engines` | `dict` | No | Engine version requirements |
| `author` | `str` | No | Plugin author |
| `license` | `str` | No | SPDX license identifier |
| `homepage` | `str` | No | Plugin homepage URL |
| `repository` | `str` | No | Source repository URL |
| `dependencies` | `list[str]` | No | Runtime dependencies |
| `permissions` | `list[str]` | No | Required permissions |
| `config` | `dict` | No | Default configuration schema |
| `exports` | `dict` | No | Exported commands and hooks |

### Example Manifest

```json
{
  "$schema": "https://mekong.dev/schema/plugin-manifest/v1.json",
  "id": "com.example.myplugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "A sample Mekong CLI plugin",
  "type": "package",
  "entrypoint": "./src/plugin.py",
  "export": "MyPlugin",
  "engines": {
    "mekong": "^6.0.0"
  },
  "author": "Example Corp",
  "license": "MIT",
  "homepage": "https://example.com/myplugin",
  "repository": "https://github.com/example/myplugin",
  "dependencies": [
    "com.example.database>=1.0.0",
    "com.example.cache>=2.0.0"
  ],
  "permissions": [
    "network",
    "database:read"
  ],
  "config": {
    "api_key": {
      "type": "string",
      "description": "API key for external service",
      "secret": true
    },
    "timeout": {
      "type": "integer",
      "default": 30,
      "description": "Request timeout in seconds"
    }
  }
}
```

---

## PluginRegistry

Central registry for plugin discovery, installation, and lifecycle management.

### Class Definition

```python
class PluginRegistry:
    """Global plugin registry singleton."""
    
    def __init__(
        self,
        plugin_dir: Path = None,
        cache_dir: Path = None
    ):
        ...
```

### Methods

#### `async register(manifest: PluginManifest) -> Plugin`

Register a new plugin with the registry.

**Parameters**:

- `manifest` (`PluginManifest`): Plugin manifest

**Returns**:

- `Plugin` instance

**Example**:

```python
from mekong.plugin import PluginRegistry, PluginManifest

registry = PluginRegistry()

manifest = PluginManifest(
    id="com.example.myplugin",
    name="My Plugin",
    version="1.0.0",
    entrypoint="./plugin.py"
)

plugin = await registry.register(manifest)
```

#### `async load(plugin_id: str) -> Plugin`

Load a plugin by ID.

**Parameters**:

- `plugin_id` (`str`): Plugin ID

**Returns**:

- `Plugin` instance

**Raises**:

- `PluginNotFoundError`: If plugin not found
- `PluginLoadError`: If plugin fails to load

**Example**:

```python
plugin = await registry.load("com.example.myplugin")
await plugin.initialize(ctx)
```

#### `async unload(plugin_id: str) -> None`

Unload a plugin.

**Parameters**:

- `plugin_id` (`str`): Plugin ID

**Example**:

```python
await registry.unload("com.example.myplugin")
```

#### `async list_plugins() -> list[PluginManifest]`

List all registered plugins.

**Returns**:

- `list[PluginManifest]`: List of plugin manifests

**Example**:

```python
plugins = await registry.list_plugins()
for p in plugins:
    print(f"{p.name} ({p.id}) v{p.version}")
```

#### `async get_plugin(plugin_id: str) -> Optional[Plugin]`

Get a loaded plugin instance.

**Parameters**:

- `plugin_id` (`str`): Plugin ID

**Returns**:

- `Plugin` instance or `None` if not loaded

**Example**:

```python
plugin = registry.get_plugin("com.example.myplugin")
if plugin:
    result = await plugin.execute(ctx, **kwargs)
```

#### `async install(source: str, **kwargs) -> Plugin`

Install a plugin from a source.

**Parameters**:

- `source` (`str`): Installation source (`pypi://`, `git://`, `local://`)
- `**kwargs`: Installation options (version, branch, etc.)

**Returns**:

- `Plugin` instance

**Example**:

```python
# Install from PyPI
plugin = await registry.install("pypi://mekong-myplugin==1.0.0")

# Install from git
plugin = await registry.install(
    "git://github.com/example/myplugin.git",
    branch="main"
)

# Install local plugin
plugin = await registry.install("local:///path/to/plugin")
```

#### `async uninstall(plugin_id: str) -> None`

Uninstall a plugin.

**Parameters**:

- `plugin_id` (`str`): Plugin ID

**Example**:

```python
await registry.uninstall("com.example.myplugin")
```

#### `async validate_dependencies() -> list[DependencyError]`

Validate all plugin dependencies are satisfied.

**Returns**:

- `list[DependencyError]`: Empty list if all dependencies satisfied

**Example**:

```python
errors = await registry.validate_dependencies()
if errors:
    for error in errors:
        print(f"Dependency error: {error}")
```

---

## PluginLoader

Dynamic plugin module loader with isolation support.

### Class Definition

```python
class PluginLoader:
    """Loads plugin modules with sandboxing."""
    
    def __init__(
        self,
        plugin_dir: Path,
        isolate: bool = True
    ):
        ...
```

### Methods

#### `load_module(entrypoint: Path) -> ModuleType`

Load a plugin module from entrypoint path.

**Parameters**:

- `entrypoint` (`Path`): Path to plugin entry module

**Returns**:

- Loaded Python module

**Raises**:

- `PluginLoadError`: If module cannot be loaded

**Example**:

```python
loader = PluginLoader(Path("/path/to/plugins"))
module = loader.load_module(Path("./plugin.py"))
```

#### `create_isolated_namespace() -> dict`

Create an isolated namespace for plugin execution.

**Returns**:

- `dict`: Isolated namespace with restricted builtins

**Example**:

```python
namespace = loader.create_isolated_namespace()
exec(module_code, namespace)
```

---

## PluginValidator

Validates plugin manifests and dependencies.

### Class Definition

```python
class PluginValidator:
    """Validates plugin manifests and dependencies."""
    
    def validate_manifest(manifest: dict) -> list[ValidationError]:
        """Validate plugin manifest against schema."""
        ...
    
    def validate_dependencies(
        self,
        manifest: PluginManifest,
        available: list[PluginManifest]
    ) -> list[DependencyError]:
        """Validate plugin dependencies."""
        ...
```

### Methods

#### `validate_manifest(manifest: dict) -> list[ValidationError]`

Validate manifest structure and fields.

**Parameters**:

- `manifest` (`dict`): Manifest dictionary

**Returns**:

- `list[ValidationError]`: List of validation errors (empty if valid)

**Example**:

```python
validator = PluginValidator()
errors = validator.validate_manifest(manifest_dict)
if errors:
    for error in errors:
        print(f"Validation error: {error.field}: {error.message}")
```

#### `validate_dependencies(manifest: PluginManifest, available: list[PluginManifest]) -> list[DependencyError]`

Validate that all dependencies are available and satisfy version requirements.

**Parameters**:

- `manifest` (`PluginManifest`): Plugin manifest
- `available` (`list[PluginManifest]`): Available plugins to check against

**Returns**:

- `list[DependencyError]`: List of dependency errors

---

## PluginHealthMonitor

Monitors plugin health and performance.

### Class Definition

```python
class PluginHealthMonitor:
    """Monitors plugin health and performance."""
    
    def __init__(self, plugin_id: str):
        ...
    
    async def check_health(self) -> HealthStatus:
        """Check plugin health."""
        ...
    
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: dict = None
    ) -> None:
        """Record a performance metric."""
        ...
```

### Methods

#### `async check_health() -> HealthStatus`

Check plugin health.

**Returns**:

- `HealthStatus`: Health status object

**Example**:

```python
monitor = PluginHealthMonitor("com.example.myplugin")
status = await monitor.check_health()
print(f"Status: {status.state}")
```

#### `async record_metric(name: str, value: float, tags: dict = None) -> None`

Record a custom metric.

**Parameters**:

- `name` (`str`): Metric name
- `value` (`float`): Metric value
- `tags` (`dict`): Optional tags

**Example**:

```python
await monitor.record_metric(
    "requests.duration",
    duration_seconds,
    tags={"endpoint": "/api/search", "method": "GET"}
)
```

---

## Enums and Types

### PluginType

Plugin type classification.

```python
class PluginType(str, Enum):
    AGENT = "agent"
    PROVIDER = "provider"
    HOOK = "hook"
    RECIPE = "recipe"
    COMMAND = "command"
    TOOL = "tool"
```

### PluginStatus

Plugin lifecycle status.

```python
class PluginStatus(str, Enum):
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
```

### Permission

Built-in permission constants.

```python
class Permission:
    # Resource access
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"
    NETWORK = "network"
    FILE_SYSTEM = "filesystem"
    
    # Mekong system
    COMMAND_EXECUTE = "command:execute"
    PLUGIN_INSTALL = "plugin:install"
    PLUGIN_UNINSTALL = "plugin:uninstall"
    
    # External services
    API_EXTERNAL = "api:external"
    EMAIL_SEND = "email:send"
    STORAGE_WRITE = "storage:write"
```

---

## Exceptions

All plugin system exceptions.

### PluginError

Base exception for all plugin errors.

```python
class PluginError(Exception):
    """Base plugin error."""
    pass
```

### PluginNotFoundError

Plugin not found in registry.

```python
class PluginNotFoundError(PluginError):
    """Plugin not found."""
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
```

### PluginLoadError

Plugin failed to load.

```python
class PluginLoadError(PluginError):
    """Plugin load failure."""
    def __init__(self, plugin_id: str, reason: str):
        self.plugin_id = plugin_id
        self.reason = reason
```

### PluginInitializationError

Plugin initialization failed.

```python
class PluginInitializationError(PluginError):
    """Plugin initialization failure."""
    def __init__(self, plugin_id: str, reason: str):
        self.plugin_id = plugin_id
        self.reason = reason
```

### PluginExecutionError

Plugin execution failed.

```python
class PluginExecutionError(PluginError):
    """Plugin execution failure."""
    def __init__(self, plugin_id: str, reason: str):
        self.plugin_id = plugin_id
        self.reason = reason
```

### DependencyError

Dependency resolution failed.

```python
class DependencyError(PluginError):
    """Dependency error."""
    def __init__(
        self,
        plugin_id: str,
        dependency: str,
        reason: str
    ):
        self.plugin_id = plugin_id
        self.dependency = dependency
        self.reason = reason
```

### ValidationError

Manifest validation failed.

```python
class ValidationError(PluginError):
    """Validation error."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
```

---

## Configuration Schema

Plugin configuration is defined in the manifest `config` field.

### Schema Format

```json
{
  "config": {
    "setting_name": {
      "type": "string|integer|boolean|array|object",
      "description": "Human-readable description",
      "default": "default value (optional)",
      "required": true|false,
      "secret": true|false,
      "validation": {
        "min": 0,
        "max": 100,
        "pattern": "^[a-z]+$",
        "enum": ["value1", "value2"]
      }
    }
  }
}
```

### Example Config

```json
{
  "config": {
    "api_endpoint": {
      "type": "string",
      "description": "External API endpoint URL",
      "default": "https://api.example.com"
    },
    "api_key": {
      "type": "string",
      "description": "API authentication key",
      "secret": true
    },
    "timeout": {
      "type": "integer",
      "description": "Request timeout in seconds",
      "default": 30,
      "min": 1,
      "max": 300
    },
    "retry_attempts": {
      "type": "integer",
      "default": 3,
      "enum": [0, 1, 2, 3, 5, 10]
    },
    "debug_mode": {
      "type": "boolean",
      "default": false
    }
  }
}
```

---

## Permissions Schema

Plugins declare required permissions in the manifest `permissions` field.

### Built-in Permissions

| Permission | Description | Default |
|------------|-------------|---------|
| `network` | Outbound network access | Denied |
| `database:read` | Read from databases | Denied |
| `database:write` | Write to databases | Denied |
| `filesystem` | File system access | Denied |
| `command:execute` | Execute system commands | Denied |
| `plugin:install` | Install other plugins | Denied |
| `plugin:uninstall` | Uninstall plugins | Denied |
| `api:external` | Call external APIs | Denied |

### Custom Permissions

Plugins can define custom permissions that the host system must grant:

```json
{
  "permissions": [
    "network",
    "custom:access_google_sheets",
    "custom:send_slack_notifications"
  ]
}
```

---

## TypeScript/JavaScript Plugin API

For plugins written in JavaScript/TypeScript, the API is largely similar.

### TypeScript Types

```typescript
// Plugin class
export interface MekongPlugin {
  id: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  
  initialize(ctx: PluginContext): Promise<void>;
  execute(ctx: PluginContext, args: Record<string, any>): Promise<any>;
  shutdown?(ctx: PluginContext): Promise<void>;
  healthCheck?(ctx: PluginContext): Promise<HealthStatus>;
}

// Plugin context
export interface PluginContext {
  config: Record<string, any>;
  logger: Logger;
  pluginId: string;
  
  getPlugin(pluginId: string): Promise<MekongPlugin | null>;
  invokePlugin(pluginId: string, method: string, args: any): Promise<any>;
  emitEvent(eventType: string, data: any): Promise<void>;
}

// Health status
export interface HealthStatus {
  state: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: Record<string, 'ok' | 'error' | 'warning'>;
}
```

### Example TypeScript Plugin

```typescript
import { MekongPlugin, PluginContext } from '@mekong/plugin-sdk';

export class MyPlugin implements MekongPlugin {
  id = 'com.example.myplugin';
  name = 'My Plugin';
  version = '1.0.0';
  description = 'A TypeScript plugin';
  
  async initialize(ctx: PluginContext): Promise<void> {
    ctx.logger.info('Initialized');
  }
  
  async execute(ctx: PluginContext, query: string): Promise<any> {
    return { result: `Processed: ${query}` };
  }
}
```

---

## Metrics and Observability

Plugins can expose metrics for monitoring.

### Standard Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `plugin_requests_total` | counter | `plugin`, `endpoint` | Total requests |
| `plugin_errors_total` | counter | `plugin`, `error_type` | Total errors |
| `plugin_response_duration_seconds` | histogram | `plugin`, `endpoint` | Response time |
| `plugin_concurrent_requests` | gauge | `plugin` | Active requests |
| `plugin_memory_bytes` | gauge | `plugin` | Memory usage |

### Prometheus Format

Expose metrics at `/metrics` endpoint in Prometheus text format:

```
# HELP plugin_requests_total Total number of requests
# TYPE plugin_requests_total counter
plugin_requests_total{plugin="com.example.myplugin",endpoint="/execute"} 1234

# HELP plugin_response_duration_seconds Response time histogram
# TYPE plugin_response_duration_seconds histogram
plugin_response_duration_seconds_bucket{plugin="com.example.myplugin",le="0.1"} 100
plugin_response_duration_seconds_bucket{plugin="com.example.myplugin",le="0.5"} 800
plugin_response_duration_seconds_bucket{plugin="com.example.myplugin",le="1.0"} 950
plugin_response_duration_seconds_bucket{plugin="com.example.myplugin",le="+Inf"} 1000
plugin_response_duration_seconds_sum{plugin="com.example.myplugin"} 456.7
plugin_response_duration_seconds_count{plugin="com.example.myplugin"} 1000
```

---

## Logging Standards

Plugins should use structured logging.

### Python

```python
import logging

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__(...)
        self.logger = logging.getLogger(f"mekong.plugin.{self.id}")
    
    async def execute(self, ctx, **kwargs):
        self.logger.info(
            "Executing plugin",
            extra={
                "plugin_id": self.id,
                "action": "execute",
                "kwargs": kwargs
            }
        )
```

### JavaScript

```javascript
const pino = require('pino');
const logger = pino({ level: 'info' });

class MyPlugin {
  constructor() {
    this.id = 'com.example.myplugin';
    this.logger = logger.child({ plugin: this.id });
  }
  
  async execute(ctx, args) {
    this.logger.info(
      { action: 'execute', args },
      'Executing plugin'
    );
  }
}
```

---

## Testing Plugins

Plugins should include unit tests and integration tests.

### Python Tests

```python
import pytest
from mekong.plugin import Plugin, PluginContext

class TestMyPlugin:
    @pytest.fixture
    def plugin(self):
        return MyPlugin()
    
    @pytest.fixture
    def mock_context(self):
        return Mock(spec=PluginContext)
    
    async def test_initialize(self, plugin, mock_context):
        await plugin.initialize(mock_context)
        # Assert initialization succeeded
    
    async def test_execute(self, plugin, mock_context):
        result = await plugin.execute(mock_context, query="test")
        assert result["result"] == "success"
```

### JavaScript Tests

```typescript
import { test, expect } from '@playwright/test';
import { MyPlugin } from './plugin';

test('plugin executes successfully', async () => {
  const plugin = new MyPlugin();
  const mockContext = { /* mock */ };
  
  const result = await plugin.execute(mockContext, { query: 'test' });
  expect(result.result).toBe('success');
});
```

---

## Best Practices

1. **Validate all inputs**: Never trust user-provided data
2. **Handle errors gracefully**: Catch exceptions and return meaningful error messages
3. **Implement health checks**: Provide `/health` endpoint for monitoring
4. **Use structured logging**: Include context in all log messages
5. **Respect timeouts**: Set appropriate timeouts for external calls
6. **Clean up resources**: Always implement `shutdown()` to release resources
7. **Follow semver**: Use semantic versioning for releases
8. **Document configuration**: Provide examples and defaults for all config options
9. **Request minimal permissions**: Only request permissions your plugin actually needs
10. **Write tests**: Include unit and integration tests

---

## Migration from Legacy System

For plugins written for Mekong CLI v5.x or earlier, see the [Plugin Migration Guide](../plugin-migration-guide.md).

Key changes:

- Plugin class now requires explicit `id` and `version` in constructor
- `context` parameter renamed to `ctx` for consistency
- `run()` method renamed to `execute()`
- Manifest format changed from `plugin.yaml` to `plugin.json`

---

## See Also

- [Plugin Developer Guide](../plugin-developer-guide.md) - Comprehensive tutorial
- [Plugin Manifest Format Reference](../plugin-manifest-format.md) - Manifest field details
- [Plugin Developer Onboarding](../plugin-developer-onboarding.md) - Getting started
- [Plugin Deployment Guide](../plugin-deployment.md) - Deployment best practices
- [Plugin Health Monitoring Operations Guide](../plugin-health-monitoring-operations.md)
- [API Documentation Standards](../../.claude/rules/api-documentation-standards.md)

---

**Need help?** Contact the plugin team in `#plugin-dev` on Discord or email plugins@mekong.cli.
