# Plugin Developer Onboarding

> **Version**: 2.0.0 | **Date**: 2026-06-20 | **Status**: Ready for Use

Welcome to Mekong CLI plugin development! This guide will take you from zero to your first working plugin in under 30 minutes.

## Table of Contents

- [Who Should Read This](#who-should-read-this)
- [What is a Mekong Plugin?](#what-is-a-mekong-plugin)
- [Prerequisites](#prerequisites)
- [Quick Start: Your First Plugin](#quick-start-your-first-plugin)
- [Understanding the Plugin Structure](#understanding-the-plugin-structure)
- [Core Concepts Deep Dive](#core-concepts-deep-dive)
- [Testing Your Plugin](#testing-your-plugin)
- [Debugging](#debugging)
- [Publishing Your Plugin](#publishing-your-plugin)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Who Should Read This

You should read this guide if you:

- Want to extend Mekong CLI with custom commands
- Are building integrations with external services (Zalo, Stripe, etc.)
- Want to create reusable business logic for your team
- Are migrating existing commands to the plugin architecture

**What this guide covers:**
- Step-by-step plugin creation
- Understanding the plugin manifest and architecture
- Testing, debugging, and publishing

**What this guide does NOT cover:**
- Detailed API reference (see [Plugin Developer Guide](./plugin-developer-guide.md))
- Migration from legacy commands (see [Plugin Migration Guide](./plugin-migration-guide.md))
- Plugin architecture deep dive (see [Plugin Architecture](./plugin-architecture.md))

---

## What is a Mekong Plugin?

A Mekong plugin is a self-contained extension that adds functionality to Mekong CLI. Think of it as a package that can:

- Add new slash commands (e.g., `mekong zalo-broadcast`)
- Integrate with external APIs (Zalo, Stripe, Polar, etc.)
- Provide reusable skills for AI agents
- Hook into Mekong's lifecycle for custom processing

### Plugin vs Command

| Aspect | Command | Plugin |
|--------|---------|--------|
| Scope | Single operation | Multiple commands + shared code |
| Reusability | Limited | High (can be shared across projects) |
| Distribution | Manual copy | Published to registry |
| Dependencies | None managed | Declared in manifest |
| Lifecycle | None | Install, enable, disable, uninstall |

### Real-World Examples

```bash
# Zalo OA plugin - adds 5 commands for Vietnamese messaging
mekong plugin install zalo-oa
mekong zalo-broadcast "Khuyến mãi hôm nay!"

# Stripe plugin - payment processing commands
mekong plugin install stripe
mekong stripe-create-customer "user@example.com" "John Doe"

# Custom internal plugin
mekong plugin install ./my-company-tools
mekong qr-generate --data "https://example.com"
```

---

## Prerequisites

Before starting, ensure you have:

### Software Requirements

| Tool | Version | Check Command |
|------|---------|---------------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| Mekong CLI | 6.0+ | `mekong --version` |
| Git | 2+ | `git --version` |

### Mekong CLI Setup

If you haven't installed Mekong CLI yet:

```bash
# Clone and setup
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
source scripts/shell-init.sh

# Verify installation
mekong --version
# Expected: Mekong CLI v6.0.0 or higher
```

### Optional: Plugin SDK

For better development experience:

```bash
# Python SDK
pip install mekong-plugin-sdk

# TypeScript SDK
npm install @mekongcli/plugin-sdk
```

---

## Quick Start: Your First Plugin

Let's build a simple "Hello World" plugin that adds a greeting command using the **Plugin SDK** (recommended approach).

### Step 1: Create Plugin Skeleton

```bash
# Create plugin directory structure
mkdir -p my-first-plugin
cd my-first-plugin

# Create the manifest
cat > plugin.json << 'EOF'
{
  "$schema": "https://mekong.dev/schema/plugin-manifest/v1.json",
  "id": "com.example.my-first-plugin",
  "name": "My First Plugin",
  "version": "1.0.0",
  "description": "A simple hello world plugin to learn plugin development",
  "author": "Your Name",
  "license": "MIT",
  "entrypoint": "./plugin.py",
  "export": "Plugin",
  "type": "module",
  "category": "utils",
  "mcuCost": 0,
  "commands": [
    {
      "name": "hello",
      "description": "Greet someone with a friendly message",
      "handler": "handlers.greet",
      "arguments": [
        {
          "name": "name",
          "type": "string",
          "description": "Name of the person to greet",
          "required": true
        }
      ],
      "options": [
        {
          "name": "formal",
          "alias": "f",
          "type": "boolean",
          "description": "Use formal greeting"
        }
      ]
    }
  ],
  "permissions": {}
}
EOF
```

Create the handlers module:

```python
"""Handlers for plugin commands."""

from typing import Any


def greet(name: str, formal: bool = False) -> dict[str, Any]:
    """Generate a greeting.

    Args:
        name: The person to greet
        formal: Whether to use formal greeting

    Returns:
        Dict with greeting message

    Raises:
        ValueError: If name is empty
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")

    if formal:
        message = f"Good day, {name}. It is a pleasure to meet you."
    else:
        message = f"Hey {name}! Welcome to Mekong!"

    return {
        "success": True,
        "message": message,
        "name": name,
        "formal": formal
    }
```

Create `plugin.py` for the Plugin class:

```python
"""My First Plugin - A simple greeting plugin."""

from __future__ import annotations

from mekong.plugins.sdk import Plugin, CommandSpec, PluginContext
from typing import List


class Plugin(Plugin):
    """Greeting plugin using the Plugin SDK."""

    def get_commands(self) -> List[CommandSpec]:
        """Return list of commands provided by this plugin."""
        return [
            CommandSpec(
                name="hello",
                description="Greet someone with a friendly message",
                module="handlers",  # handlers.py module
                function="greet",   # greet function in handlers.py
                layer="utils",
                mcu_cost=0,
            )
        ]

    def on_load(self, manager) -> None:
        """Called when plugin is loaded."""
        self.logger.info("Greeting plugin loaded!")
```

### Step 3: Install and Test

```bash
# Install the plugin from local directory
mekong plugin install ./my-first-plugin

# List installed plugins to verify
mekong plugin list
# You should see: com.example.my-first-plugin (v1.0.0) - ACTIVE

# Test your command
mekong hello Alice
# Output: Hey Alice! 👋 Welcome to Mekong!

mekong hello Bob --formal
# Output: Good day, Bob. It is a pleasure to meet you.
```

### Step 4: View Plugin Information

```bash
# Show plugin details
mekong plugin info com.example.my-first-plugin

# View command help
mekong hello --help
```

**Congratulations!** You've created and installed your first plugin.

---

## Understanding the Plugin Structure

Let's break down what we created:

### Directory Structure

```
my-first-plugin/
├── plugin.json          # Manifest - the "package.json" of your plugin
├── plugin.py            # Plugin class definition
└── handlers.py          # Command handler implementations
```

### The Manifest (`plugin.json`)

The manifest is the heart of your plugin. Key fields:

| Field | Purpose | Example |
|-------|---------|---------|
| `id` | Unique identifier (kebab-case) | `com.example.greeting` |
| `name` | Human-readable name | `"Greeting Plugin"` |
| `version` | Semver version | `"1.0.0"` |
| `description` | What the plugin does | `"Adds greeting commands"` |
| `entrypoint` | Path to Plugin class | `"./plugin.py"` |
| `export` | Class name in entrypoint | `"Plugin"` (default) |
| `commands` | Array of command definitions | See below |
| `permissions` | Required capabilities | `{"network": true}` |
| `mcuCost` | Credits per execution | `0` for free |
| `category` | Plugin category | `"utils"`, `"engineering"` |

### Command Definition in Manifest

Each command references a handler function:

```json
{
  "name": "hello",
  "description": "Greet someone",
  "handler": "handlers.greet",
  "arguments": [
    {
      "name": "name",
      "type": "string",
      "description": "Person to greet",
      "required": true
    }
  ],
  "options": [
    {
      "name": "formal",
      "alias": "f",
      "type": "boolean",
      "description": "Use formal greeting"
    }
  ]
}
```

**Handler Resolution**:
- `handler: "handlers.greet"` means: import the `handlers` module (relative to plugin directory) and call the `greet` function
- The function receives arguments as keyword arguments matching the argument/option names
- Handler returns a dict (typically with `success` and `message` keys) or raises an exception

---

## Core Concepts Deep Dive

### 1. Plugin SDK Architecture

Mekong CLI plugins use the **Plugin SDK** pattern:

1. **Plugin Class** (`plugin.py`): Extends `mekong.plugins.sdk.Plugin`
   - `get_commands()`: Returns list of `CommandSpec` objects
   - `initialize(context)`: Receives `PluginContext` with config, storage, logger
   - `on_load(manager)`: Called when plugin is activated
   - `start()` / `stop()`: Background task lifecycle
   - `health_check()`: Return plugin health status

2. **Command Handlers** (e.g., `handlers.py`): Plain functions
   - Receive arguments as keyword arguments
   - Return dict (typically with `success` key) or raise exceptions
   - No need to parse CLI args - Mekong handles that

3. **Manifest** (`plugin.json`): Declares plugin metadata and commands
   - `entrypoint`: Path to module containing `Plugin` class
   - `export`: Class name (default `"Plugin"`)
   - `commands[].handler`: `"module.function"` - dotted path to handler

**Execution Flow**:
```
User runs: mekong hello Alice
  ↓
CommandRegistry finds registered command
  ↓
Lazy-imports plugin module (plugin.py)
  ↓
Instantiates Plugin class (if not already)
  ↓
Calls initialize(context) once
  ↓
Resolves handler from manifest: module=handlers, function=greet
  ↓
Imports handlers module, gets greet function
  ↓
Calls greet(name="Alice", formal=False)
  ↓
Returns result to user
```

### 2. CommandSpec API

Use `CommandSpec` to declare commands programmatically:

```python
from mekong.plugins.sdk import CommandSpec, Argument, Option

def get_commands(self) -> List[CommandSpec]:
    return [
        CommandSpec(
            name="deploy",
            description="Deploy to production",
            module="handlers.deploy",
            function="run",
            layer="engineering",
            mcu_cost=2,
            tags=["deploy", "prod"],
            arguments=[
                Argument(
                    name="environment",
                    type="string",
                    description="Target environment",
                    choices=["staging", "production"],
                    required=True
                )
            ],
            options=[
                Option(
                    name="force",
                    alias="f",
                    type="boolean",
                    description="Force deploy without confirmation"
                )
            ]
        )
    ]
```

**CommandSpec fields**:
- `name`: Command name (kebab-case)
- `description`: Short help text
- `module`: Python module path (relative to plugin)
- `function`: Function name within module
- `layer`: Business layer (engineering, ops, business, product, founder, studio, utils)
- `mcu_cost`: Credits per execution (default 1)
- `tags`: Categorization tags
- `arguments` / `options`: CLI parameters (often defined in manifest instead)

### 3. PluginContext - Accessing Plugin Services

The `PluginContext` is provided in `initialize()`:

```python
def initialize(self, context: PluginContext) -> None:
    self.config = context.config                    # Plugin configuration dict
    self.logger = context.logger                   # Plugin-specific logger
    self.storage = context.storage_dir             # ~/.mekong/plugins/<id>/storage
    self.cache = context.cache_dir                 # ~/.mekong/plugins/<id>/cache
    self.data = context.data_dir                   # ~/.mekong/plugins/<id>/data

    # Log with plugin context
    context.log("info", "Plugin initialized", version=self.version)
```

### 4. Permissions Model

Plugins declare required permissions in manifest:

```json
{
  "permissions": {
    "network": ["https://api.example.com/*"],
    "file": ["read:./data", "write:./output"],
    "env_vars": ["API_KEY", "BASE_URL"],
    "child_processes": false
  }
}
```

**Permission Types**:
- `network`: Allowed URL patterns (wildcards supported)
- `file`: Read/write file paths with colon prefix (`read:`, `write:`)
- `env_vars`: Required environment variables
- `child_processes`: `true` to allow subprocess execution

If your plugin attempts unauthorized access, it will be blocked with a clear error.

### 5. MCU Billing

Every command consumes MCU (Mekong Credit Units):

```json
{
  "mcuCost": 1,                    // Plugin default
  "commands": [
    { "name": "expensive", "mcuCost": 5 }  // Override per command
  ]
}
```

- Balance checked before execution
- Only deducted after successful completion
- 402 Payment Required if insufficient credits

**Best practice**: Start with `mcuCost: 0` during development.

### 6. Configuration & Secrets

Never hardcode secrets. Use environment variables or Mekong's config store:

```python
import os

# Environment variables (set by user)
api_key = os.getenv("MY_PLUGIN_API_KEY")

# Mekong config store (encrypted)
from mekong.config import get_secret
api_key = get_secret("my-plugin", "api_key")
```

User configuration:
```bash
# Shell profile
export MY_PLUGIN_API_KEY="secret"

# Or Mekong's encrypted store
mekong config set my-plugin api_key "secret"
```

### 7. Output Format

Handlers return Python dicts (auto-converted to JSON):

```python
def my_handler(name: str) -> dict:
    return {
        "success": True,
        "message": f"Hello {name}",
        "data": {"processed": True}
    }
```

For rich terminal output, check `sys.stdout.isatty()`:
```python
import sys

if sys.stdout.isatty():
    print(f"✅ Success!")
else:
    print(json.dumps({"success": True}))
```

### 8. Error Handling

Raise exceptions for errors - Mekong catches and formats them:

```python
def my_handler(name: str) -> dict:
    if not name:
        raise ValueError("Name is required")
    try:
        result = external_api_call()
        return {"success": True, "result": result}
    except ExternalAPIError as e:
        raise RuntimeError(f"API call failed: {e}") from e
```

Error response format:
```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human readable error message"
}
```

---

## Testing Your Plugin

### Unit Tests

Test handler functions directly (they're pure functions):

Create `tests/test_handlers.py`:

```python
"""Tests for plugin handlers."""

import pytest
from handlers import greet


def test_greet_basic() -> None:
    """Test basic greeting."""
    result = greet(name="Alice", formal=False)
    assert result["success"] is True
    assert "Alice" in result["message"]


def test_greet_formal() -> None:
    """Test formal greeting."""
    result = greet(name="Bob", formal=True)
    assert result["success"] is True
    assert "Good day" in result["message"]
    assert "Bob" in result["message"]


def test_greet_empty_name() -> None:
    """Test empty name handling."""
    with pytest.raises(ValueError):
        greet(name="", formal=False)
```

Run tests:

```bash
# Install pytest if needed
pip install pytest

# Run tests from plugin directory
cd my-first-plugin
python3 -m pytest tests/ -v

# Or run from parent if PYTHONPATH includes plugin directory
PYTHONPATH=. python3 -m pytest tests/ -v
```

### Integration Tests

Test the full command through Mekong CLI:

```python
"""Integration tests."""

import subprocess
import json


def test_hello_command() -> None:
    """Test hello command via Mekong CLI."""
    result = subprocess.run(
        ["mekong", "hello", "Alice"],
        capture_output=True,
        text=True,
        env={"MEKONG_TEST_MODE": "1"}  # Skip billing if needed
    )
    assert result.returncode == 0
    output = result.stdout.strip()
    assert "Alice" in output


def test_hello_formal() -> None:
    """Test hello with formal flag."""
    result = subprocess.run(
        ["mekong", "hello", "Bob", "--formal"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Good day" in result.stdout
```

### Plugin Validation

Validate your plugin manifest:

```bash
# Validate from plugin directory
cd my-first-plugin
mekong plugin validate .

# Or validate specific path
mekong plugin validate ./my-first-plugin

# Expected output: "Plugin valid" or error messages
```

---

## Debugging

### View Plugin Logs

```bash
# View all plugin logs
mekong admin plugin logs

# Filter by plugin ID
mekong admin plugin logs com.example.my-first-plugin

# Follow logs (like tail -f)
mekong admin plugin logs --follow
```

### Enable Debug Mode

```bash
# Set debug logging for plugin system
export MEKONG_LOG_LEVEL=DEBUG
export MEKONG_PLUGIN_DEBUG=1

# Run command with verbose output
mekong hello Alice --verbose
```

### Common Debugging Scenarios

| Issue | Check | Fix |
|-------|-------|-----|
| Command not found | `mekong plugin list` | Plugin not installed or disabled |
| Permission denied | Logs show "permission" | Add permission to manifest |
| Import errors | Check Python path | Ensure all dependencies in `requirements.txt` |
| Syntax errors | `python3 -m py_compile plugin.py` | Fix Python syntax |

---

## Publishing Your Plugin

### Prepare for Release

1. **Update manifest** with complete metadata:

```json
{
  "$schema": "../schemas/plugin-manifest-v1.json",
  "id": "com.yourorg.your-plugin",
  "name": "Your Plugin Name",
  "version": "1.0.0",
  "description": "Detailed description of what your plugin does",
  "author": "Your Name",
  "author_email": "you@example.com",
  "homepage": "https://github.com/yourorg/your-plugin",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourorg/your-plugin"
  },
  "license": "MIT",
  "keywords": ["mekong", "plugin", "your-feature"],
  "category": "integrations",
  "type": "module",
  "export": "Plugin",
  "entrypoint": "plugin.py",
  "mcuCost": 1,
  "permissions": {...},
  "commands": [...],
  "changelog": {
    "1.0.0": ["Initial release"]
  }
}
```

2. **Add README.md** with usage instructions:

```markdown
# Your Plugin Name

> Description for users.

## Installation

```bash
mekong plugin install com.yourorg.your-plugin
```

Or install from local:

```bash
mekong plugin install ./your-plugin-dir
```

## Quick Start

```bash
mekong your-command --option value
```

## Configuration

Set these environment variables:

- `YOUR_PLUGIN_API_KEY` - Your API key

## Commands

- `your-command` - Does something useful

## License

MIT
```

3. **Add examples/** directory:

```
examples/
├── basic-usage.md
├── advanced-config.md
└── integration-with-x.md
```

### Package for Distribution

```bash
# Create distribution package
python3 -m build

# Outputs dist/your-plugin-1.0.0.tar.gz
```

### Submit to Plugin Marketplace

1. Create PR or submit via web portal at `plugins.mekongmind.com`
2. CI runs automated checks:
   - Manifest validation
   - Security scan
   - Contract verification
   - Documentation completeness
3. Approved plugins are listed in the registry

### Install from Source (Development)

```bash
# Local development
mekong plugin install ./my-plugin --dev

# Changes to plugin.py are picked up automatically (hot reload)
# But you may need to reload: mekong admin plugin reload
```

---

## Advanced Topics

### Multi-Command Plugins

Most plugins provide multiple related commands. Define all commands in `get_commands()`:

**plugin.py:**

```python
from mekong.plugins.sdk import Plugin, CommandSpec, PluginContext
from typing import List
from handlers import create_customer, create_checkout, handle_webhook


class Plugin(Plugin):
    """Stripe integration plugin."""

    def get_commands(self) -> List[CommandSpec]:
        """Return all commands provided by this plugin."""
        return [
            CommandSpec(
                name="stripe-create-customer",
                description="Create a Stripe customer",
                module="handlers",
                function="create_customer",
                layer="product",
                mcu_cost=5,
                tags=["stripe", "customer"],
            ),
            CommandSpec(
                name="stripe-create-checkout",
                description="Create Stripe checkout session",
                module="handlers",
                function="create_checkout",
                layer="product",
                mcu_cost=3,
                tags=["stripe", "checkout"],
            ),
            CommandSpec(
                name="stripe-webhook-handler",
                description="Handle Stripe webhook events",
                module="handlers",
                function="handle_webhook",
                layer="infra",
                mcu_cost=10,
                tags=["stripe", "webhook"],
            ),
        ]

    def on_load(self, manager) -> None:
        """Called when plugin is loaded."""
        self.logger.info("Stripe plugin loaded with %d commands", len(self.get_commands()))
```

**handlers.py:**

```python
"""Handler functions for Stripe plugin."""

from typing import Any


def create_customer(email: str, name: str) -> dict[str, Any]:
    """Create a Stripe customer."""
    # Implementation using stripe library
    return {"success": True, "customer_id": "cus_123"}


def create_checkout_session(customer_id: str) -> dict[str, Any]:
    """Create checkout session."""
    return {"success": True, "session_id": "sess_123"}


def handle_webhook(payload: dict[str, Any], signature: str) -> dict[str, Any]:
    """Process Stripe webhook."""
    # Verify signature, process event
    return {"success": True, "processed": True}
```

### Plugin Lifecycle Hooks

The `Plugin` base class defines lifecycle methods you can override:

```python
from mekong.plugins.sdk import Plugin, CommandSpec


class Plugin(Plugin):
    """Plugin with full lifecycle hooks."""

    def initialize(self, context: PluginContext) -> None:
        """Called before on_load. Use to set up configuration."""
        self.context = context
        self.config = context.config
        self.logger.info("Initializing with config: %s", self.config)

    def on_load(self, manager: Any) -> None:
        """Called after plugin is loaded but before activation."""
        self.manager = manager
        self.logger.info("Plugin on_load")

    def start(self) -> None:
        """Called after activation. Start background tasks here."""
        self.logger.info("Plugin started")
        # Start background worker, scheduler, etc.

    def stop(self) -> None:
        """Called before deactivation. Clean up background tasks."""
        self.logger.info("Plugin stopping")
        # Stop workers, close connections

    def on_unload(self) -> None:
        """Called after deactivation but before module unload."""
        self.logger.info("Plugin on_unload")

    def dispose(self) -> None:
        """Final cleanup. Called after on_unload."""
        self.logger.info("Plugin disposed")
```

**Lifecycle sequence:**
1. `initialize()` - Setup configuration
2. `on_load()` - Plugin loaded, register with manager
3. `start()` - Activate, start background tasks
4. `stop()` - Deactivate, stop tasks
5. `on_unload()` - Unload from manager
6. `dispose()` - Final cleanup

### Event System

Plugins can publish and subscribe to events via the context's event bus:

```python
from mekong.plugins.sdk import Plugin, PluginContext
from typing import Any


class Plugin(Plugin):
    """Plugin using event system."""

    def on_load(self, manager: Any) -> None:
        """Subscribe to events on load."""
        # Get event bus from manager or context
        event_bus = manager.get_event_bus()  # hypothetical API
        
        # Subscribe to events
        event_bus.subscribe("command.executed", self.on_command_executed)
        event_bus.subscribe("plugin.activated", self.on_plugin_activated)

    def on_command_executed(self, event) -> None:
        """Handle command executed event."""
        command = event.data["command"]
        result = event.data["result"]
        self.logger.info("Command %s completed: %s", command, result.get("success"))

    def publish_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Publish custom event."""
        event_bus = self.manager.get_event_bus()
        event_bus.publish(event_name, data)
```

**Built-in events:**
- `plugin.loaded` - Plugin module loaded
- `plugin.activated` - Plugin activated
- `plugin.deactivated` - Plugin deactivated
- `command.executed` - Command completed
- `command.failed` - Command execution failed

### Configuration and Secrets

Access plugin configuration via `PluginContext`:

**plugin.json:**
```json
{
  "id": "com.example.my-plugin",
  "config": {
    "api_key": {"type": "string", "required": true},
    "timeout": {"type": "number", "default": 30}
  }
}
```

**plugin.py:**
```python
from mekong.plugins.sdk import Plugin, PluginContext


class Plugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        # Access user-provided configuration
        self.api_key = context.config.get("api_key")
        self.timeout = context.config.get("timeout", 30)
        
        # Access secrets (stored encrypted)
        self.db_password = context.get_secret("db_password")
        
        # Access storage directories (created automatically)
        self.storage_path = context.storage_dir  # ~/.mekong/plugins/<id>/storage
        self.cache_path = context.cache_dir
        self.data_path = context.data_dir
```

### Health Checks

Implement health checks for monitoring:

```python
from mekong.plugins.sdk import Plugin, HealthStatus


class Plugin(Plugin):
    def health_check(self) -> HealthStatus:
        """Return plugin health status."""
        # Check external service connectivity
        try:
            response = requests.get("https://api.example.com/health", timeout=5)
            if response.status_code == 200:
                return HealthStatus(healthy=True, message="Service OK")
            else:
                return HealthStatus(healthy=False, message=f"API returned {response.status_code}")
        except Exception as e:
            return HealthStatus(healthy=False, message=f"Connection failed: {e}")
```

### External Dependencies

Declare Python dependencies in `requirements.txt`:

```
requests>=2.28.0
stripe>=5.0.0
```

Mekong will install them when the plugin is installed. For system dependencies, document them in README.

---

## Troubleshooting

### Plugin Not Loading

**Symptom:** `mekong plugin list` doesn't show your plugin.

**Check:**
1. Is `plugin.json` valid JSON? Run `python3 -m json.tool plugin.json`
2. Is `entrypoint` path correct relative to plugin root?
3. Does the entrypoint module exist and have execute permission?
4. Check logs: `mekong admin plugin logs`

**Common fixes:**
- Invalid JSON → Fix syntax errors
- Missing entrypoint file → Create the file
- Invalid entrypoint → Ensure module is importable

### Command Not Found

**Symptom:** `mekong mycommand` → "Command not found"

**Check:**
1. Is command name in manifest exactly matching?
2. Is the plugin ACTIVE? (not disabled)
3. Run `mekong plugin list` to see active commands

**Fix:** Ensure `commands[].name` matches what you type.

### Permission Denied

**Symptom:** "Error: Permission denied for network access"

**Fix:** Add the required permission to `plugin.json`:

```json
{
  "permissions": {
    "network": ["https://api.example.com/*"]
  }
}
```

Then reinstall: `mekong plugin install ./my-plugin --force`

### Import Errors

**Symptom:** "ModuleNotFoundError: No module named 'requests'"

**Fix:**
1. Add to `requirements.txt`: `requests>=2.28.0`
2. Reinstall plugin: `mekong plugin install ./my-plugin --force`
3. Or install globally: `pip install requests`

### High MCU Cost

**Symptom:** "Insufficient credits" when running your command

**Fix:**
1. During development, set `mcu_cost: 0` in manifest
2. For production, ensure user has enough credits
3. Test with: `MEKONG_TEST_MODE=1 mekong mycommand` to bypass billing

---

## Next Steps

### Learning Path

1. **[Your First Plugin](#quick-start-your-first-plugin)** - Done!
2. **[Plugin Developer Guide](./plugin-developer-guide.md)** - Read Architecture section
3. **[Command Fabric](./command-fabric.md)** - Understand the unified catalog
4. **[Example Plugins](../packages/mekong-plugin-sdk/examples/)** - Study real-world examples
5. Build your actual plugin!

### Recommended Reading Order

| Stage | Document | Purpose |
|-------|----------|---------|
| Beginner | This guide | Get started quickly |
| Beginner | [Plugin Examples](../packages/mekong-plugin-sdk/examples/) | See working code |
| Intermediate | [Plugin Developer Guide](./plugin-developer-guide.md) | Full reference |
| Intermediate | [Plugin Architecture](./plugin-architecture.md) | System design |
| Advanced | [Plugin Migration Guide](./plugin-migration-guide.md) | Legacy migration |
| Advanced | [Plugin Health Monitoring](./plugin-health-monitoring-design.md) | Production ops |

### Hands-On Next

Try building:

1. **Config Plugin** - Read from config file
2. **API Plugin** - Call an external REST API
3. **Multi-Command Plugin** - 3+ related commands
4. **Hook Plugin** - Use lifecycle hooks
5. **Event Plugin** - Publish/subscribe pattern

### Get Help

- CLI: `mekong plugin --help`
- Docs: `docs/` directory
- Issues: GitHub Issues
- Discord: `#plugins` channel

---

## Quick Reference

### Common Commands

```bash
# Create plugin skeleton
mkdir my-plugin && cd my-plugin

# Create manifest (plugin.json)
cat > plugin.json << 'EOF'
{
  "$schema": "../schemas/plugin-manifest-v1.json",
  "id": "com.example.my",
  "name": "My Plugin",
  "version": "1.0.0",
  "type": "module",
  "export": "Plugin",
  "entrypoint": "./plugin.py",
  "category": "utils",
  "commands": [
    {
      "name": "mycmd",
      "description": "Does something",
      "handler": "handlers.mycmd"
    }
  ],
  "permissions": {},
  "mcuCost": 0
}
EOF

# Create handlers module
cat > handlers.py << 'EOF'
"""Command handlers."""

from typing import Any


def mycmd(arg: str) -> dict[str, Any]:
    """Handle mycmd command."""
    return {"success": True, "message": f"Processed {arg}"}
EOF

# Create plugin class
cat > plugin.py << 'EOF'
"""My Plugin - Plugin SDK implementation."""

from mekong.plugins.sdk import Plugin, CommandSpec
from typing import List


class Plugin(Plugin):
    """My plugin implementation."""

    def get_commands(self) -> List[CommandSpec]:
        return [
            CommandSpec(
                name="mycmd",
                description="Does something",
                module="handlers",
                function="mycmd",
                layer="utils",
                mcu_cost=0,
            )
        ]
EOF

# Install and test
mekong plugin install ./
mekong mycmd testarg

# List plugins
mekong plugin list

# View info
mekong plugin info com.example.my

# Uninstall
mekong plugin uninstall com.example.my

# Validate manifest
mekong plugin validate ./
```

### Manifest Template

```json
{
  "$schema": "../schemas/plugin-manifest-v1.json",
  "id": "com.yourorg.your-plugin",
  "name": "Your Plugin Name",
  "version": "1.0.0",
  "description": "What it does",
  "author": "Your Name",
  "license": "MIT",
  "type": "module",
  "export": "Plugin",
  "entrypoint": "./plugin.py",
  "category": "utils",
  "commands": [
    {
      "name": "command-name",
      "description": "Command description",
      "handler": "handlers.function_name",
      "arguments": [
        {"name": "arg", "type": "string", "description": "Arg description", "required": true}
      ],
      "options": [
        {"name": "option", "alias": "o", "type": "boolean", "description": "Option description"}
      ],
      "examples": ["command-name value", "command-name value --option"]
    }
  ],
  "permissions": {},
  "mcuCost": 0
}
```

---

**You're ready to build!** Start with your plugin idea, refer to the detailed guides when needed, and join the community for support.
