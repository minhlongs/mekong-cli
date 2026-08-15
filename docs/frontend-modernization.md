# Frontend Modernization Migration Guide

> Migrating Legacy CLI/IDE Surfaces to Command Fabric Adapters

**Last Updated**: 2026-06-21  
**Target Version**: Mekong CLI v6.1+  
**Migration Type**: Progressive modernization with zero downtime

---

## Overview

Mekong CLI's frontend surfaces (shell completions, IDE command palettes, agent CLIs) have historically been manually maintained, leading to drift and inconsistency. The **Command Fabric** introduces a unified catalog that automatically generates all frontend adapter manifests from a single source of truth.

### What Changes

| Aspect | Legacy | Command Fabric |
|--------|--------|----------------|
| Command discovery | Manual per-adapter maintenance | Single catalog export |
| Shell completions | Hand-written scripts | Generated from catalog |
| VS Code extension | Manual manifest updates | Auto-generated command palette |
| JetBrains plugin | Manual action definitions | Generated from catalog |
| Claude Code tools | Static MCP tools list | Dynamic catalog export |
| Release process | Multiple manual steps | Single `command-fabric bundle` |

### Migration Path

```
┌─────────────────────────────────────┐
│  Existing Frontend Surfaces         │
│  (hand-maintained adapters)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 1: Readiness                 │
│  - Install Mekong CLI v6.1+         │
│  - Run `mekong command-fabric export` │
│  - Review generated manifests       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 2: Materialize Adapters      │
│  - Generate all adapter manifests   │
│  - Compare with current surfaces    │
│  - Identify differences             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 3: Gradual Rollout           │
│  - Deploy one adapter at a time     │
│  - Verify compatibility             │
│  - Monitor for issues               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 4: Full Automation           │
│  - All surfaces from catalog        │
│  - CI gate prevents drift           │
│  - Release gate validates bundle    │
└─────────────────────────────────────┘
```

---

## Pre-Migration Checklist

### 1. Inventory Current Surfaces

```bash
# List all current adapter implementations
find .claude/commands -name "*.md" | wc -l  # Command count
find packages -name "*extension*" -o -name "*plugin*"  # IDE extensions
ls -la .claude/skills/ | grep -i "mcp\|tool"  # MCP tools

# Check current shell completions
ls -la ~/.mekong/completions/ 2>/dev/null || echo "No completions dir"

# List IDE extensions
# VS Code: Check .vscode/extensions/ for Mekong extensions
# JetBrains: Check ~/.local/share/JetBrains/IntelliJPlatform/
```

### 2. Verify Command Fabric Availability

```bash
# Check Mekong CLI version
mekong version
# Must be v6.1.0 or higher

# Test command fabric export
mekong command-fabric export --format json --scope project > /tmp/catalog.json
cat /tmp/catalog.json | jq '.schema'
# Should output: "mekong.command_fabric.v1"
```

### 3. Backup Current Configurations

```bash
# Backup current command definitions
cp -r .claude/commands ~/backup/claude-commands-$(date +%Y%m%d)

# Backup IDE extension scaffolds
cp -r packages/mekong-ide ~/backup/mekong-ide-$(date +%Y%m%d) 2>/dev/null || true

# Backup shell completions
cp -r ~/.mekong/completions ~/backup/mekong-completions-$(date +%Y%m%d) 2>/dev/null || true
```

---

## Phase 1: Explore Generated Adapters

The command fabric can generate all frontend adapter manifests. Start by exploring what's available.

### List Available Adapters

```bash
mekong command-fabric adapters
```

Expected output:
```
Available adapters:
  - shell        (Bash/Zsh/Fish completions)
  - mcp          (Model Context Protocol)
  - vscode       (VS Code extension)
  - cursor       (Cursor IDE)
  - jetbrains    (JetBrains plugin)
  - claude-code  (Claude Code tools)
  - gemini-cli   (Gemini CLI)
  - opencode     (OpenCode commands)
  - codex        (Codex manifest)
  - neovim       (Neovim package)
  - zed          (Zed extension)
  - emacs        (Emacs package)
  - sublime      (Sublime Text package)
  - theia        (Theia extension)
  - fleet        (Fleet editor)
```

### Generate All Adapters (Dry Run)

```bash
# Create a temporary output directory
mkdir -p /tmp/mekong-frontend-migration

# Generate all adapters without writing
mekong command-fabric materialize \
  --scope project \
  --out /tmp/mekong-frontend-migration \
  --dry-run
```

This will show:
- Which adapters would be generated
- Number of commands per adapter
- Output file structure

---

## Phase 2: Generate and Compare Adapters

### Generate Specific Adapters

Start with one adapter to validate the process:

```bash
# Generate shell completions
mekong command-fabric shell-completion \
  --scope project \
  --out /tmp/mekong-frontend-migration/shell

# Generated files:
# - /tmp/mekong-frontend-migration/shell/_mekong
# - /tmp/mekong-frontend-migration/shell/mekong.fish
# - /tmp/mekong-frontend-migration/shell/install.sh
```

### Compare with Existing Completions

```bash
# Diff generated vs installed
diff -r /tmp/mekong-frontend-migration/shell ~/.mekong/completions/ || true
```

### Generate VS Code Extension

```bash
mekong command-fabric ide-extension \
  --host vscode \
  --scope project \
  --out /tmp/mekong-frontend-migration/vscode
```

Generated files:
```
vscode/
├── package.json          # VS Code extension manifest
├── src/
│   └── extension.ts      # Command registration
├── tsconfig.json
└── README.md
```

### Generate MCP Tools Manifest

```bash
mekong command-fabric mcp-package \
  --scope project \
  --out /tmp/mekong-frontend-migration/mcp
```

---

## Phase 3: Gradual Rollout

### Start with Shell Completions (Lowest Risk)

1. **Install generated completions**:

```bash
# Backup current completions
cp -r ~/.mekong/completions ~/.mekong/completions.backup-$(date +%Y%m%d)

# Install new completions
mekong command-fabric shell-completion \
  --scope project \
  --out ~/.mekong/completions

# Activate
source ~/.mekong/completions/install.sh
# Or for fish:
# ~/.mekong/completions/install.fish
```

2. **Test completion behavior**:

```bash
# Reload shell completions
# For zsh:
autoload -U +X compinit && compinit

# Test a few commands
mekong <tab><tab>  # Should show all commands
mekong cook <tab>  # Should show cook's arguments
```

3. **Rollback if needed**:

```bash
# Restore previous completions
rm -rf ~/.mekong/completions
cp -r ~/.mekong/completions.backup-$(date +%Y%m%d) ~/.mekong/completions
```

### Deploy VS Code Extension

1. **Build the generated extension**:

```bash
cd /tmp/mekong-frontend-migration/vscode
npm install
npm run compile
npm run package  # Produces .vsix file
```

2. **Install in VS Code**:

```bash
code --install-extension mekong-cli-*.vsix
```

3. **Test command palette**:

- Open VS Code Command Palette (Ctrl+Shift+P)
- Type "Mekong" - all commands should appear
- Try running a simple command like "Mekong: Version"

4. **Monitor for issues**:

```bash
# Check VS Code extension logs
# View → Output → "Mekong CLI" channel
```

### Deploy MCP Tools (Claude Code)

1. **Install MCP package**:

```bash
# Copy MCP package to Claude Code's MCP directory
# Typically: ~/.config/Claude/mcp/
mkdir -p ~/.config/Claude/mcp
cp -r /tmp/mekong-frontend-migration/mcp/* ~/.config/Claude/mcp/

# Restart Claude Code for changes to take effect
```

2. **Verify tools are available**:

In Claude Code, ask:
```
What Mekong commands can you run?
```

Should list all commands from the catalog.

---

## Phase 4: Full Automation

### Enable CI/CD for Frontend Surfaces

The command fabric includes a **release gate** that validates all surfaces:

```bash
# Run release gate locally
npm run command-fabric:release-gate -- \
  --out /tmp/release-gate-output \
  --target-root /tmp/install-targets
```

This verifies:
- All adapters materialize correctly
- Package build scripts exist
- Shell completions are valid
- IDE extensions compile
- MCP manifest is valid
- Coverage is complete

### Configure GitHub Actions

The `.github/workflows/command-fabric-release-gate.yml` workflow runs automatically on PRs and pushes to `main`. Ensure it's enabled in your repository settings.

### Deprecate Legacy Surfaces

Once all adapters are deployed and validated:

1. Remove manually maintained adapter files
2. Update documentation to reference generated surfaces only
3. Add deprecation warnings if legacy paths are detected

---

## Rollback Procedures

If a frontend update causes issues:

### Quick Rollback (Shell)

```bash
# Restore previous completions
rm -rf ~/.mekong/completions
cp -r ~/.mekong/completions.backup-<timestamp> ~/.mekong/completions
source ~/.zshrc  # or restart shell
```

### IDE Extension Rollback

- VS Code: `code --uninstall-extension mekong-cli`
- Install previous version from `.vsix` backup
- JetBrains: Remove plugin from Settings → Plugins, reinstall previous build

### MCP Rollback

```bash
# Restore previous MCP config
rm -rf ~/.config/Claude/mcp
cp -r ~/backup/claude-mcp-<timestamp> ~/.config/Claude/mcp
# Restart Claude Code
```

---

## Troubleshooting

### "Adapter generation fails: command count mismatch"

The catalog may be out of sync with actual command definitions:

```bash
# Regenerate catalog
mekong command-fabric export --scope project --format json > /tmp/catalog.json
# Verify count
cat /tmp/catalog.json | jq '.command_count'
# Should match expected count from docs
```

### "Shell completions not loading"

```bash
# Reinstall completions
mekong command-fabric shell-completion --scope project --out ~/.mekong/completions
# For zsh:
rm -f ~/.zcompcache/*
autoload -U +X compinit && compinit
# For bash:
source ~/.mekong/completions/install.sh
```

### "VS Code extension shows fewer commands"

The extension may be using cached command data:

1. Reload VS Code window (Ctrl+Shift+P → "Developer: Reload Window")
2. Check that the extension's `data/canonical.json` is up to date
3. Rebuild the extension if needed

### "MCP tools not appearing in Claude Code"

```bash
# Verify MCP package structure
ls -la ~/.config/Claude/mcp/
# Should contain:
# - mekong-cli-mcp.json (manifest)
# - bin/ (executable)
# Check Claude Code logs for MCP errors
```

---

## Verification

### Run Readiness Audit

```bash
mekong command-fabric readiness-audit \
  --scope project \
  --out /tmp/readiness-audit.json
```

Expected: `"ready": true` with all surfaces validated.

### Run Release Gate

```bash
npm run command-fabric:release-gate -- \
  --out /tmp/release-gate \
  --target-root /tmp/install-targets
```

All checks must pass before considering migration complete.

---

## Next Steps

After frontend modernization is complete:

1. **Monitor adoption**: Track which adapters are actually used
2. **Gather feedback**: Collect issues from users of different frontends
3. **Plan enhancements**: Use command-fabric extensibility for new adapter targets
4. **Document custom adapters**: If you've built custom adapters, update them to use the command fabric runtime

---

## Related Documentation

- [Command Fabric](./command-fabric.md) - Core architecture and commands
- [Command Fabric ADR](architecture/adrs/ADR-076-command-fabric-catalog-architecture.md) - Design decisions and alternatives
- [Plugin Migration Guide](./plugin-migration-guide.md) - Backend command migration
- [Zenos Migration Guide](./zenos-migration-guide.md) - Economic particle migration
- [Release Gate Script](../scripts/command_fabric_release_gate.py) - CI/CD validation

---

**Migration Complete?** → Your frontend surfaces are now generated from the unified command fabric catalog, ensuring consistency across all adapters and eliminating manual maintenance.
