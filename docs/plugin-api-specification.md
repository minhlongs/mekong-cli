# Plugin API Specification

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Stable

Complete API reference for Mekong CLI plugin developers.

## Table of Contents

1. [Plugin Base Class](#plugin-base-class)
2. [PluginContext](#plugincontext)
3. [CommandSpec](#commandspec)
4. [Argument and Option](#argument-and-option)
5. [Factory Function](#factory-function)
6. [Type Hints](#type-hints)
7. [Error Handling](#error-handling)
8. [Lifecycle Hooks](#lifecycle-hooks)

---

## Plugin Base Class

The `Plugin` class is the base class all plugins must inherit from.

```python
from src.plugins.sdk import Plugin, PluginContext, CommandSpec

class MyPlugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        """Initialize plugin with context."""
        self.context = context
        context.logger.info("Plugin initializing")

    def get_commands(self) -> list[CommandSpec]:
        """Return commands provided by this plugin."""
        return [
            CommandSpec(
                name="my-command",
                description="Does something",
                module="myplugin.commands",
                function="run",
                layer="engineering",
                mcu_cost=1,
            )
        ]

    def start(self) -> None:
        """Start background services (optional)."""
        pass

    def stop(self) -> None:
        """Stop background services (optional)."""
        pass

    def health_check(self) -> dict[str, Any]:
        """Return health status."""
        return {"status": "healthy", "plugin": self.context.id}
```

### Plugin Lifecycle

1. `__init__()` - Plugin instantiated
2. `initialize(context)` - Context provided, store for later use
3. `on_load(manager)` - (Deprecated) Manager reference provided
4. `get_commands()` - Command specs collected
5. `start()` - Background services started (if defined)
6. Commands invoked as needed
7. `stop()` - Graceful shutdown (if defined)
8. `dispose()` - Resource cleanup (if defined)

---

## PluginContext

Provided to plugins during `initialize()`. Provides access to plugin resources.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | str | Plugin identifier |
| `manifest` | FullPluginManifest | Full manifest data |
| `config` | dict | Plugin configuration snapshot |
| `storage_dir` | Path | Writable data directory |
| `cache_dir` | Path | Writable cache directory |
| `data_dir` | Path | Writable persistent data directory |
| `logger` | logging.Logger | Plugin-specific logger |

### Methods

```python
# Get configuration value
value = context.get_config("api_key", default="")

# Log with plugin context
context.log("info", "Message here", extra_key="value")

# Report error to core
context.error(exception, context={"operation": "deploy"})
```

---

## CommandSpec

Defines a command that the plugin provides.

### Constructor Parameters

```python
CommandSpec(
    name: str,              # Command name (kebab-case)
    description: str,        # Short description
    module: str,            # Python module path (e.g., "myplugin.commands")
    function: str,          # Function name within module
    layer: str = "product", # Business layer
    mcu_cost: int = 1,      # MCU credits per execution
    tags: list[str] = [],   # Categorization tags
    hidden: bool = False,   # Hide from help
    deprecated: bool = False,
    deprecation_message: str | None = None,
    arguments: list[Argument] = [],
    options: list[Option] = [],
    permission: str | None = None,
)
```

### Example

```python
CommandSpec(
    name="deploy-app",
    description="Deploy an application",
    module="myplugin.deploy",
    function="run_deploy",
    layer="engineering",
    mcu_cost=5,
    tags=["deployment", "production"],
    arguments=[
        Argument(
            name="app_name",
            type="string",
            description="Application name",
            required=True
        )
    ],
    options=[
        Option(
            name="environment",
            alias="e",
            type="string",
            description="Target environment",
            default="production"
        )
    ]
)
```

---

## Argument and Option

### Argument

```python
Argument(
    name: str,              # Argument name (snake_case identifier)
    type: str = "string",   # Type: string, number, integer, boolean, path, choice
    description: str = "",  # Help text
    required: bool = False,
    default: Any = None,
    choices: list[str] | None = None,  # For type='choice'
    metavar: str | None = None,       # Display name in help
)
```

### Option

```python
Option(
    name: str,              # Option name (kebab-case)
    alias: str | None = None,    # Short flag (e.g., "-v")
    type: str = "string",   # Type: string, number, integer, boolean
    description: str = "",
    required: bool = False,
    default: Any = None,
    metavar: str | None = None,
)
```

---

## Factory Function

Plugins must provide a factory function that returns a `Plugin` instance:

```python
# In plugin module
from src.plugins.sdk import Plugin, PluginContext, CommandSpec

class MyPlugin(Plugin):
    # ... implementation ...

def create_plugin(context: PluginContext) -> Plugin:
    """Factory function for plugin instantiation.

    Args:
        context: Plugin context with config, storage, logger

    Returns:
        Configured plugin instance
    """
    return MyPlugin()
```

The manifest's `entrypoint` should point to the module containing `create_plugin`.

---

## Type Hints

All SDK methods support type hints. Recommended pattern:

```python
from typing import Any

class MyPlugin(Plugin):
    def get_commands(self) -> list[CommandSpec]:
        return [...]

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy"}

def my_command(name: str, verbose: bool = False) -> str:
    """Command handler function.

    Args:
        name: User name
        verbose: Enable verbose output

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"
```

---

## Error Handling

Plugin errors should be raised as exceptions. The core will:

1. Catch all exceptions from command handlers
2. Log full traceback with plugin context
3. Return error response to user
4. Mark plugin health as `degraded` or `error` based on severity

```python
def my_command(config: dict) -> None:
    if "api_key" not in config:
        raise ValueError("API key is required in plugin config")
    # ...
```

### Plugin-Level Error Handling

```python
class MyPlugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        try:
            self.setup_resources()
        except Exception as e:
            context.error(e, {"phase": "initialize"})
            raise  # Re-raise to prevent plugin loading
```

---

## Lifecycle Hooks

### initialize(context)

Called immediately after plugin instantiation. Use to:
- Store the context
- Load configuration
- Initialize resources (database connections, API clients)

### start()

Called after all plugins have been initialized and commands registered.
Use to:
- Start background workers
- Begin periodic tasks
- Connect to external services

### stop()

Called when plugin is being deactivated. Use to:
- Stop background workers gracefully
- Close connections
- Flush pending data

### dispose()

Called after `stop()` for final cleanup. Use to:
- Release resources that need explicit cleanup
- Delete temporary files

### health_check()

Return plugin health status. Called by monitoring systems.

```python
def health_check(self) -> dict[str, Any]:
    return {
        "status": "healthy",  # or "degraded", "error", "starting", "stopping"
        "plugin": self.context.id,
        "version": self.context.manifest.version,
        "uptime": time.time() - self._started_at,
        "resources": {
            "memory_mb": self._get_memory_usage(),
            "active_tasks": len(self._tasks)
        }
    }
```

---

## Constants

### Plugin Loading Modes

- `LOADING_MODE_IN_PROCESS = "in-process"`
- `LOADING_MODE_WORKER = "worker"`
- `LOADING_MODE_PROCESS = "process"`
- `LOADING_MODE_WASM = "wasm"`

### Health Statuses

- `HEALTH_HEALTHY = "healthy"`
- `HEALTH_DEGRADED = "degraded"`
- `HEALTH_ERROR = "error"`
- `HEALTH_STARTING = "starting"`
- `HEALTH_STOPPING = "stopping"`
- `HEALTH_STOPPED = "stopped"`

---

## Complete Example

```python
# plugin.py
from typing import Any
from src.plugins.sdk import Plugin, CommandSpec, PluginContext, Argument, Option

class GreetingPlugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        self.context = context
        self.greeting = context.get_config("greeting", "Hello")

    def get_commands(self) -> list[CommandSpec]:
        return [
            CommandSpec(
                name="greet",
                description="Greet a user",
                module="plugin",
                function="greet",
                layer="engineering",
                mcu_cost=1,
                arguments=[
                    Argument(
                        name="name",
                        type="string",
                        description="User name",
                        required=True
                    )
                ],
                options=[
                    Option(
                        name="formal",
                        alias="f",
                        type="boolean",
                        description="Use formal greeting"
                    )
                ]
            )
        ]

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "plugin": self.context.id,
            "greeting": self.greeting
        }

def greet(name: str, formal: bool = False) -> str:
    """Greet a user.

    Args:
        name: User name
        formal: Use formal greeting

    Returns:
        Greeting message
    """
    if formal:
        return f"Good day, {name}!"
    return f"Hello, {name}!"

def create_plugin(context: PluginContext) -> Plugin:
    return GreetingPlugin()
```

---

## See Also

- [Plugin Manifest Format](./plugin-manifest-format.md)
- [Plugin Developer Guide](./plugin-developer-guide.md)
- [Plugin Isolation Model](./plugin-isolation-model.md)
- JSON Schema: `schemas/plugin-manifest-v1.json`
