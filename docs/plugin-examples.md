# Plugin Examples

Learn by example! This page catalogs real plugin implementations in the Mekong CLI codebase that you can study, run, and adapt for your own plugins.

## Quick Start Examples

### Hello World

The simplest possible plugin that defines a single command.

- **Location**: `packages/mekong-plugin-sdk/examples/hello-world/`
- **What it shows**: Basic plugin structure, command definition, and handler
- **Try it**:
  ```bash
  cd packages/mekong-plugin-sdk/examples/hello-world
  mekong plugin install .
  mekong hello --name="Mekong"
  ```

### Multi-Command Plugin

Demonstrates a plugin with multiple related commands.

- **Location**: `packages/mekong-plugin-sdk/examples/multi-command/`
- **What it shows**: How to register multiple commands in a single plugin, command grouping
- **Commands provided**: `plugin-info`, `plugin-health`, `plugin-status`

### HTTP Client Plugin

Shows how to make HTTP requests and integrate with external APIs.

- **Location**: `packages/mekong-plugin-sdk/examples/http-demo/`
- **What it shows**: Network permissions, HTTP client usage, error handling
- **Commands provided**: `http-get`, `http-post`, `http-json`

### Storage Plugin

Demonstrates persistent storage usage for plugins.

- **Location**: `packages/mekong-plugin-sdk/examples/storage-demo/`
- **What it shows**: Reading/writing files, data persistence across invocations
- **Commands provided**: `storage-write`, `storage-read`, `storage-list`, `storage-delete`

### Hook System

Shows how to register hooks for lifecycle events.

- **Location**: `packages/mekong-plugin-sdk/examples/hooks-demo/`
- **What it shows**: Hook registration, event handling, priority ordering
- **Hooks registered**: `before_command`, `after_command`, `before_plugin_init`, `after_plugin_start`

### Event Bus

Demonstrates pub/sub pattern for inter-plugin communication.

- **Location**: `packages/mekong-plugin-sdk/examples/events-demo/`
- **What it shows**: Publishing events, subscribing to events, event payloads
- **Events**: `plugin.started`, `plugin.stopped`, `command.executed`

### Configuration Demo

Shows plugin configuration management.

- **Location**: `packages/mekong-plugin-sdk/examples/config-demo/`
- **What it shows**: Accessing plugin config, environment variables, secrets management
- **Commands provided**: `config-get`, `config-set`, `config-list`

## Production Reference Plugins

The Mekong CLI itself includes several built-in plugins that serve as production-grade reference implementations.

### Founder Plugin

- **Location**: `packages/mekong-cli-core/src/plugins/builtin/founder/`
- **Commands**: `annual`, `okr`, `swot`, `fundraise`, `pitch`, `vc`, `ipo/*` (52 commands total)
- **What it shows**: Complex business logic, agent orchestration, multi-step workflows
- **Best for**: Learning how to build sophisticated plugins that orchestrate AI agents

### Business Plugin

- **Location**: `packages/mekong-cli-core/src/plugins/builtin/business/`
- **Commands**: `sales`, `marketing`, `finance`, `hr`, `pricing`, `brand` (71 commands total)
- **What it shows**: Revenue operations, CRM integration, financial calculations
- **Best for**: Building business-facing plugins with complex data handling

### Product Plugin

- **Location**: `packages/mekong-cli-core/src/plugins/builtin/product/`
- **Commands**: `plan`, `sprint`, `roadmap`, `brainstorm`, `scope` (31 commands total)
- **What it shows**: Product management workflows, planning tools, agile methodologies
- **Best for**: Project management and product development plugins

### Studio Plugin

- **Location**: `packages/mekong-cli-core/src/plugins/builtin/studio/`
- **Commands**: `studio-launch`, `dealflow`, `venture`, `expert` (23 commands)
- **What it shows**: VC studio operations, portfolio management, expert network
- **Best for**: Building plugins for professional services and investment

### Ops Plugin

- **Location**: `packages/mekong-cli-core/src/plugins/builtin/ops/`
- **Commands**: `audit`, `health`, `security`, `status`, `clean` (41 commands)
- **What it shows**: System monitoring, security scanning, health checks, maintenance
- **Best for**: DevOps and infrastructure plugins

## Study Guide

### For First-Time Plugin Developers

Start here:
1. Read the [Plugin Developer Onboarding](../docs/plugin-developer-onboarding.md)
2. Run the hello-world example
3. Modify it to add your own command
4. Study the multi-command example
5. Explore the builtin plugins to see real-world patterns

### For Advanced Plugin Development

Dive deeper:
- **Complex workflows**: Study `founder-plugin` for agent orchestration
- **Performance**: Review `ops` plugin for efficient resource usage
- **Security**: Examine permission models in all builtin plugins
- **Testing**: Look at test patterns in `packages/mekong-plugin-sdk/tests/`

### Key Patterns to Look For

When studying examples, pay attention to:

| Pattern | Where to Look | Purpose |
|---------|---------------|---------|
| Command registration | All examples | How commands are declared and registered |
| Permission declaration | Builtin plugins | Capability-based security model |
| Error handling | http-demo, storage-demo | Robust error handling and user feedback |
| Agent orchestration | founder, business plugins | Using the PEV engine |
| Configuration | config-demo | Managing plugin settings and secrets |
| Hooks | hooks-demo | Extending Mekong lifecycle |
| Events | events-demo | Inter-plugin communication |
| Testing | SDK tests | Test-driven plugin development |

## Running the Examples

### Prerequisites

- Mekong CLI installed and configured
- Python 3.11+ with mekong-plugin-sdk installed
- LLM provider configured (Ollama, Anthropic, etc.)

### Installation Steps

```bash
# Navigate to an example directory
cd packages/mekong-plugin-sdk/examples/hello-world

# Install the plugin from local directory
mekong plugin install .

# Verify installation
mekong plugin list

# Run a command from the plugin
mekong hello --name="World"

# Uninstall when done
mekong plugin uninstall com.example.hello
```

### Development Mode

For active development, use the `MEKONG_PLUGIN_PATH` environment variable:

```bash
export MEKONG_PLUGIN_PATH=./my-plugin
# Changes are picked up automatically without reinstall
```

## Contributing New Examples

We welcome new example plugins! Please follow these guidelines:

1. **Keep it simple**: Each example should demonstrate one clear concept
2. **Include README**: Explain what the example shows and how to run it
3. **Self-contained**: No external dependencies beyond the SDK
4. **Documented**: Code comments explaining key sections
5. **Tested**: Include basic tests if applicable

To contribute:
- Add your example to `packages/mekong-plugin-sdk/examples/`
- Update this page to include your example
- Submit a PR with both the example and documentation

## Next Steps

- Read the [Plugin Developer Guide](../docs/plugin-developer-guide.md) for comprehensive documentation
- Learn about [Plugin Architecture](../docs/plugin-architecture.md)
- Understand the [Plugin Migration Guide](../docs/plugin-migration-guide.md) if converting legacy commands
- Join the [Mekong Community](https://github.com/longtho638-jpg/mekong-cli/discussions) to ask questions and share plugins
