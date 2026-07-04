---
description: "Manage mekong-cli plugins — scaffold, install, list, remove"
argument-hint: "[init|install|list|remove|info] [args]"
---

# /plugin — Plugin Manager

## Usage
```
/plugin init <name>              # Scaffold new plugin skeleton
/plugin install <path>           # Install plugin from path
/plugin list                     # List installed plugins
/plugin remove <name>            # Remove plugin
/plugin info <name>              # Show plugin details
```

## Ecosystem
Plugins extend mekong-cli with custom skills and commands.

Registry: `.claude/plugins/registry.json`
Installed: `.claude/plugins/<name>/`

## Implementation
- init: `node scripts/plugin-init.cjs <name>`
- install: `node scripts/plugin-registry.cjs install <path>`
- list: `node scripts/plugin-registry.cjs list`
- remove: `node scripts/plugin-registry.cjs remove <name>`
