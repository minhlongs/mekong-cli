# Plugin Manifest Format Reference

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Stable

This document describes the complete `plugin.json` manifest format for Mekong CLI plugins.

## Overview

Every Mekong CLI plugin requires a `plugin.json` manifest file that declares its identity, capabilities, and requirements. The manifest is validated against the JSON Schema in `schemas/plugin-manifest-v1.json`.

## Quick Example

```json
{
  "id": "com.example.myplugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "A sample Mekong CLI plugin",
  "type": "module",
  "entrypoint": "plugin.py",
  "commands": [
    {
      "name": "my-command",
      "description": "Does something useful",
      "handler": "my_command"
    }
  ]
}
```

## Full Reference

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique plugin identifier (reverse DNS format recommended: `com.example.plugin`) |
| `name` | string | Yes | Human-readable name (max 100 chars) |
| `version` | string | Yes | Semantic version (e.g., `1.2.3`) |
| `description` | string | No | Short description (max 500 chars) |
| `type` | enum | No | Plugin type: `module`, `package`, or `shim` (default: `module`) |
| `entrypoint` | string | Yes | Path to entry module relative to manifest (e.g., `./plugin.py`) |
| `export` | string | No | Named export containing Plugin class (default: `MekongPlugin`) |

### Engine Requirements

```json
"engines": {
  "mekong": "^6.0.0",
  "python": ">=3.10",
  "node": ">=18.0.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `mekong` | string | Minimum Mekong CLI version (semver range) |
| `python` | string | Python version requirement (for Python plugins) |
| `node` | string | Node.js version requirement (for JavaScript plugins) |

### Metadata

```json
{
  "author": "Your Name",
  "license": "MIT",
  "homepage": "https://example.com/plugin",
  "repository": {
    "type": "git",
    "url": "https://github.com/example/plugin"
  },
  "keywords": ["mekong", "plugin", "example"],
  "category": "engineering"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Plugin author or organization |
| `license` | string | SPDX license identifier (e.g., `MIT`, `Apache-2.0`) |
| `homepage` | uri | Plugin homepage URL |
| `repository` | object | Git repository information |
| `keywords` | string[] | Search keywords (max 10) |
| `category` | string | Primary category: `engineering`, `business`, `ops`, `product`, `founder`, `studio` |

### Commands

```json
"commands": [
  {
    "name": "deploy-app",
    "description": "Deploy an application to production",
    "handler": "commands.deploy.run",
    "usage": "mekong deploy-app <app-name> [environment]",
    "aliases": ["deploy", "del"],
    "arguments": [
      {
        "name": "app_name",
        "type": "string",
        "description": "Name of the application to deploy",
        "required": true
      }
    ],
    "options": [
      {
        "name": "environment",
        "alias": "e",
        "type": "string",
        "description": "Target environment",
        "default": "production"
      }
    ],
    "mcuCost": 5,
    "tags": ["deployment", "production"],
    "permission": "deploy:write"
  }
]
```

### Permissions

```json
"permissions": {
  "file": ["read", "write"],
  "network": ["outbound"],
  "llm": ["anthropic:claude", "openai:gpt-4"],
  "billing": ["mcu:read", "mcu:consume"]
}
```

| Permission Type | Values |
|-----------------|--------|
| `file` | `read`, `write`, `execute` |
| `network` | `outbound`, `inbound` |
| `llm` | `*` (all) or specific `provider:model` |
| `billing` | `mcu:read`, `mcu:consume`, `mcu:bypass` |
| `cli` | `command:register`, `hook:register`, `config:read`, `config:write` |
| `system` | `env`, `process`, `socket` |

### Hooks and Events

```json
"hooks": [
  {
    "point": "before_command",
    "handler": "hooks.pre_command",
    "priority": 10
  }
],
"events": [
  {
    "event": "command.completed",
    "handler": "events.on_command_done"
  }
]
```

### Dependencies

```json
"dependencies": [
  {
    "id": "com.mekong.logging",
    "version": "^1.0.0",
    "source": "builtin",
    "autoInstall": false,
    "optional": false
  }
],
"peerDependencies": {
  "pandas": "^2.0.0",
  "requests": "^2.28.0"
}
```

### Resources and Sandbox

```json
"resources": {
  "memory": 256,
  "cpuTime": 30000,
  "storage": 100
},
"loadingMode": "worker",
"hotReload": true,
"sandbox": {
  "enabled": true,
  "v8Isolate": true,
  "allowedModules": ["os", "path", "logging"],
  "blockedModules": ["subprocess", "socket"]
}
```

| Field | Values | Description |
|-------|--------|-------------|
| `loadingMode` | `in-process`, `worker`, `process`, `wasm` | How plugin loads |
| `hotReload` | boolean | Enable hot reload in dev mode |
| `sandbox.enabled` | boolean | Enable sandboxing |
| `sandbox.allowedModules` | string[] | Python/JS modules allowed |
| `sandbox.blockedModules` | string[] | Modules explicitly blocked |

### Configuration Schema

```json
"config": {
  "schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API key for external service"
      },
      "timeout": {
        "type": "number",
        "default": 30,
        "minimum": 1,
        "maximum": 300
      }
    },
    "required": ["api_key"]
  },
  "defaults": {
    "timeout": 30
  },
  "ui": {
    "category": "Integration",
    "order": 1
  }
}
```

### Signature (for verified plugins)

```json
"signature": {
  "algorithm": "ed25519",
  "keyId": "abc123def456",
  "signature": "base64-encoded-signature..."
}
```

## Validation

Validate your manifest against the schema:

```bash
# Install ajv-cli
npm install -g ajv-cli

# Validate
ajv validate -s schemas/plugin-manifest-v1.json -d plugin.json
```

Or use Python:

```python
import json, jsonschema

with open('schemas/plugin-manifest-v1.json') as f:
    schema = json.load(f)

with open('plugin.json') as f:
    manifest = json.load(f)

jsonschema.validate(manifest, schema)
print("Valid!")
```

## Common Pitfalls

1. **Missing required fields**: `id`, `name`, `version`, `entrypoint` are required
2. **Invalid semver**: Version must follow semver 2.0 format
3. **Invalid ID format**: Use lowercase alphanumeric with hyphens only
4. **Handler path incorrect**: Handler should be `module.function` where module is importable
5. **Permission typos**: Use exact permission strings from the docs

## See Also

- [Plugin Developer Guide](./plugin-developer-guide.md) - Complete tutorial
- [Plugin API Specification](./plugin-api-specification.md) - SDK API reference
- [Plugin Security Model](./plugin-security-hardening.md) - Permissions and sandboxing
