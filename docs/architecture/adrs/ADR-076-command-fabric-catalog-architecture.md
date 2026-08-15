# ADR-076: Command Fabric — Unified Command Catalog Architecture

**Status:** Implemented
**Date:** 2026-06-20
**Task:** T260603 (Command Fabric Global IDE/CLI Refactor)
**Supersedes:** n/a

---

## Context

Prior to Command Fabric, Mekong CLI's command surface was fragmented across multiple independent sources:

- **Typer registrations** in Python code (`src/cli/`)
- **Generated slash commands** from markdown files
- **Markdown command files** in `.claude/commands/`
- **Factory contracts** in `factory/contracts/commands/`
- **Shell wrapper scripts** scattered across projects
- **NPM package definitions** for Worker API

This fragmentation created several critical problems:

1. **Adapter drift** — Every IDE/CLI adapter (VS Code, JetBrains, Claude Code, etc.) required manual updates. When a command changed, adapters would silently diverge.
2. **No machine-readable source** — No single canonical export of all commands with full metadata.
3. **Duplication** — Command definitions were copied into multiple adapter-specific manifests.
4. **Verification impossibility** — No way to prove that all adapters covered the same command set.
5. **Governance erosion** — PR review gates existed for the core Python code, but adapter manifests in separate repositories could not be automatically checked against the source of truth.

The existing harness evaluation (`harness-eval`) checked Core DNA properties but did not validate universal IDE/CLI coverage or adapter manifest consistency.

---

## Decision

Adopt a **unified command fabric architecture** with the following characteristics:

### 1. Single Source of Truth

`.claude/commands/*.md` becomes the first source layer for all command definitions. Each markdown file contains:

- Frontmatter: `description`, `argument-hint`, `allowed-tools`
- Execution block: the actual command to run

Optional `factory/contracts/commands/<name>.json` provides additional metadata: `layer`, `namespace`, `contractPath`, `portabilityTargets`.

### 2. Neutral Catalog Abstraction

Create `src/command_fabric/catalog.py` to parse all command sources and produce normalized `CommandRecord` objects:

```python
@dataclass
class CommandRecord:
    name: str                    # Stable command name (e.g., "cook", "plan")
    source: str                  # Source markdown file path
    description: str             # From frontmatter
    argument_hint: str           # Human/agent argument shape
    allowed_tools: List[str]     # Allowed tool hints
    execution: str               # Execution block
    contract: Optional[str]      # Optional factory contract path
    layer: Optional[str]         # Business layer from contract
    portability_targets: List[str]  # Adapters that can consume this
```

The catalog is **scope-aware**:
- `--scope project`: only `.claude/commands/` in current project
- `--scope global`: project + readable `~/.claude/commands/`

### 3. Adapter Manifest Generation (Not Hand-Maintenance)

All adapter manifests are **generated** from the catalog. No adapter-specific command lists are hand-maintained.

Supported adapters (as of 260611):

| Category | Adapters |
|----------|----------|
| Agent CLIs | `claude-code`, `codex`, `gemini-cli`, `opencode`, `aider`, `continue-dev`, `copilot-cli`, `cursor-agent`, `amp`, `goose`, `crush`, `kiro-cli` |
| IDE Palettes | `vscode`, `cursor`, `windsurf`, `theia`, `jetbrains`, `visual-studio`, `eclipse`, `fleet`, `nova`, `lapce`, `kakoune`, `micro`, `vim`, `neovim`, `helix`, `zed`, `emacs`, `sublime` |
| Gateways | `mcp`, `shell` |
| Package Managers | `npm`, `bun`, `deno`, `pypi`, `homebrew`, `scoop`, `winget`, `chocolatey`, `asdf`, `mise`, `aqua`, `pkgx`, `snap`, `flatpak`, `appimage`, `aur`, `debian`, `rpm`, `freebsd`, `openbsd`, `netbsd`, `docker` |

Each adapter receives a tailored artifact:
- **JSON-RPC adapters** (MCP): tool definitions with schema
- **IDE extensions**: `package.json` contributions, `extension.ts` entrypoints
- **Agent CLIs**: markdown command files + wrapper scripts
- **Shell**: completion scripts + help text
- **Package managers**: distro-specific packaging metadata

### 4. Runtime Gateway

Create `src/command_fabric/runtime.py` — a shared runtime gateway that:

- Lists available commands from the catalog
- Invokes commands either from the catalog (data-driven) or native Typer registrations
- Exposes endpoints to MCP server and Worker package

The gateway replaces the previous recursive Typer slash dispatch with a single, testable, mockable module.

### 5. Release Bundle Orchestration

`command-fabric bundle` materializes the complete release tree in one operation:

```
bundle/
├── manifests/           (canonical.json, adapter manifests)
├── ide-vscode/          (VS Code extension scaffold)
├── ide-jetbrains/       (JetBrains plugin scaffold)
├── ide-neovim/          (Neovim package)
├── ide-zed/             (Zed extension)
├── ide-emacs/           (Emacs package)
├── ide-sublime/         (Sublime package)
├── shell/               (bash/zsh/fish completions)
├── agent-cli/           (claude-code, codex, gemini-cli, opencode)
├── agent-cli-aider/     (Aider package)
├── agent-cli-continue/  (Continue.dev package)
├── agent-cli-copilot/   (Copilot CLI package)
├── agent-cli-cursor/    (Cursor Agent package)
├── agent-cli-amp/       (Amp package)
├── agent-cli-goose/     (Goose package)
├── agent-cli-crush/     (Crush package)
├── agent-cli-kiro/      (Kiro CLI package)
├── contracts/           (deep command contracts, one per command)
├── marketplace/         (marketplace metadata for all targets)
├── npm-package/         (@mekongcli/command-fabric)
├── mcp-package/         (@mekongcli/command-fabric-mcp)
├── package-managers/    (homebrew, scoop, pypi, docker, etc.)
└── native-install/      (install scripts for local runtime)
```

### 6. CI Release Gate

`scripts/command_fabric_release_gate.py` runs deterministically on every PR:

1. Materializes project-scoped bundle
2. Verifies sentinel files exist in each section
3. Runs package build verifiers (can build VS Code extension, JetBrains plugin, etc.)
4. Runs native install dry-run for all supported hosts
5. Runs `readiness-audit` to ensure `ready=true`
6. Fails if any section, build check, or adapter is missing

The release gate prevents adapter drift by making the full universal surface a PR gate.

### 7. Universal Readiness Audit

`command-fabric readiness-audit` is the single source of truth for "is the command fabric ready for release?" It returns:

```json
{
  "ready": true,
  "project_commands": 91,
  "global_commands": 206,
  "marketplace_targets": 56,
  "package_manager_targets": 23,
  "native_install_hosts": 24,
  "bundle_sections": 27,
  "package_build_checks": 22,
  "checks": { ... per-check details ... }
}
```

The CI release gate fails if `ready` is not `true`.

---

## Rationale

### Why a Neutral Catalog Instead of Extending Typer?

- **Adapter independence** — Typer is Python-specific. IDE extensions (TypeScript), MCP (JSON-RPC), and package managers (shell scripts) cannot consume Typer directly.
- **Separation of concerns** — Command *definition* should be separate from command *invocation*. The catalog describes what commands exist; the runtime gateway handles how to run them.
- **Cross-language portability** — The Worker API (`packages/mekong-engine`) is TypeScript. A neutral JSON catalog can be consumed by any language.

### Why Generated, Not Hand-Written, Adapters?

- **Drift elimination** — If adapters are hand-maintained, they inevitably diverge when commands change. Generation ensures consistency.
- **Coverage verification** — The release gate can verify that generated artifacts exist. Hand-maintained files cannot be auto-verified.
- **New adapter cost** — Adding a new adapter requires only a generator function, not manual updates to 90+ command definitions.

### Why Preserve Native Typer Commands?

- **Backwards compatibility** — Existing `mekong <command>` invocations must keep working without materialization overhead.
- **Core DNA governance** — The existing Core DNA evaluators (`test_core_dna.py`) understand Typer registrations. The runtime gateway bridges catalog-driven commands to Typer when needed.
- **Incremental migration** — New commands can be markdown-only; legacy commands stay in Typer. Over time, everything moves to markdown as teams refactor.

### Why Materialize Artifacts Instead of On-Demand Export?

- **Release reproducibility** — The exact bundle that passed CI can be shipped to production.
- **Offline consumption** — NPM packages, IDE extensions, and package manager feeds consume files from the bundle, not live Python imports.
- **Deterministic gate** — The release gate verifies files that will actually be published, not ephemeral in-memory exports.

---

## Consequences

### What Changes

- **New modules**:
  - `src/command_fabric/catalog.py` — command record model + parser
  - `src/command_fabric/adapters.py` — adapter registry + target enumeration
  - `src/command_fabric/artifacts.py` — artifact materialization orchestrator
  - `src/command_fabric/packs.py` — native command pack definitions
  - `src/command_fabric/runtime.py` — shared gateway for Typer + catalog
  - `src/command_fabric/ide_extensions.py` — VS Code, Cursor, JetBrains scaffolds
  - `src/command_fabric/shell_package.py` — shell completion generation
  - `src/command_fabric/agent_cli_package.py` — agent CLI packages
  - `src/command_fabric/contracts.py` — deep command contract generation
  - `src/command_fabric/release_bundle.py` — bundle orchestration
  - `src/command_fabric/native_install.py` — local runtime installation
  - `src/command_fabric/distribution.py` — marketplace metadata
  - `src/command_fabric/npm_package.py` — `@mekongcli/command-fabric`
  - `src/command_fabric/mcp_package.py` — `@mekongcli/command-fabric-mcp`
  - `src/command_fabric/package_build.py` — package build contract verification
  - `src/command_fabric/readiness.py` — universal readiness audit
  - `src/command_fabric/jetbrains_extension.py` — JetBrains-specific
  - `src/command_fabric/neovim_package.py` — Neovim package
  - `src/command_fabric/zed_package.py` — Zed extension
  - `src/command_fabric/emacs_package.py` — Emacs package
  - `src/command_fabric/sublime_package.py` — Sublime package
  - `src/command_fabric/lightweight_editor_templates.py` — Fleet, Nova, Lapce, Kakoune, micro
  - `src/command_fabric/package_managers.py` — 23 package manager targets
  - `src/command_fabric/ide_build_plan.py` — build script generation
  - `src/command_fabric/command_fabric_target_matrix.py` — coverage matrix

- **CLI commands**: `mekong command-fabric <subcommand>` with 15+ subcommands
- **CI/CD**: New GitHub Actions workflow `command-fabric-release-gate.yml`
- **Tests**: 120+ tests across 18 test modules in `tests/test_command_fabric_*.py`
- **Documentation**: `docs/command-fabric.md` (comprehensive reference)

### What Stays the Same

- **Core runtime behavior** — `mekong <command>` still invokes Typer registrations directly.
- **Slash command semantics** — Existing slash commands continue to work; the catalog describes them to adapters.
- **Governance model** — PR review gates, Core DNA checks, and harness evaluation remain the source of truth for code quality.
- **Contract layer** — Existing factory contracts remain authoritative; generated contracts reference them.

### Performance Impact

- **CLI startup**: catalog parsing adds ~50ms on first load (cached thereafter)
- **Release pipeline**: gate adds ~30s for full bundle materialization + verification (acceptable for CI)
- **Runtime gateway**: one extra indirection layer when catalog commands are invoked (negligible)

---

## Supersedes

n/a (new architecture)

---

## Cross-References

- **ADR-073** (Above-Epic Naming): Command Fabric is tracked as Epic `T260603`
- **AGENTS.md**: Command Pack definitions (`dna/command-packs.json`) follow the native command pack pattern
- **CLEO-INJECTION.md**: Spawn prompts now include command-fabric context for orchestration agents
- **docs/command-fabric.md**: Comprehensive command-fabric reference

---

## Related Tasks

| Phase | Task | Title |
|-------|------|-------|
| All | T260603 | Command Fabric Global IDE/CLI Refactor (30-phase epic) |
| 1 | T260603-P1 | Command Fabric Foundation (catalog, CLI, docs) |
| 2 | T260603-P2 | Adapter Manifests (10 adapters) |
| 3 | T260603-P3 | Data-Driven Slash Routing |
| 4 | T260603-P4 | Native Command Packs |
| 5 | T260603-P5 | Global Command Ingestion |
| 6 | T260603-P6 | Materialized Adapter Artifacts |
| 7 | T260603-P7 | Runtime Gateway + Package Hooks |
| 8 | T260603-P8 | Worker Package Command Fabric API |
| 9 | T260603-P9 | VS Code/Cursor Extension Scaffold |
| 10 | T260603-P10 | Catalog Decomposition |
| 11 | T260603-P11 | JetBrains Plugin Scaffold |
| 12 | T260603-P12 | Shell Completion Package |
| 13 | T260603-P13 | Agent CLI Packages |
| 14 | T260603-P14 | Deep Command Contracts |
| 15 | T260603-P15 | Release Bundle Orchestrator |
| 16 | T260603-P16 | Native Runtime Install |
| 17 | T260603-P17 | Release CI Gate |
| 18 | T260603-P18 | Marketplace Distribution Metadata |
| 19 | T260603-P19 | IDE Package Build Contract Verification |
| 20 | T260603-P20 | Npm Consumer Package Export |
| 21 | T260603-P21 | MCP Server Package Export |
| 22 | T260603-P22 | Npm Scope Consistency Gate |
| 23 | T260603-P23 | Universal IDE/CLI Readiness Audit |
| 24 | T260603-P24 | CI Release Gate Coverage |
| 25 | T260603-P25 | IDE Package Build Plans |
| 26 | T260603-P26 | Neovim Editor Package |
| 27 | T260603-P27 | Zed Editor Package |
| 28 | T260603-P28 | Windsurf, Emacs, and Sublime Coverage |
| 29 | T260603-P29 | Theia and Manifest Agent CLI Expansion |
| 30 | T260603-P30 | Package-Manager Expansion (homebrew, pypi, docker, etc.) |

---

## Implementation Notes

### File Count & Size Management

The Command Fabric implementation spans 30+ modules. To maintain the local architecture threshold (≤200 lines/module):

- Template generators extracted to focused modules (`jetbrains_templates.py`, `visual_studio_templates.py`, `lightweight_editor_templates.py`, `package_manager_templates.py`)
- Adapter target groups extracted to `adapter_targets.py`
- Native install paths extracted to `native_install_targets.py`
- Package build verifiers split by domain (`package_build.py`, `package_build_editor_verifiers.py`, `package_manager_build.py`)

All modules remain under 200 lines as verified by line-count checks in each phase.

### Test Coverage

As of 260611:
- **Total command-fabric tests**: 120
- **Targets**: catalog, adapters, runtime, IDE extensions, shell package, agent CLI packages, contracts, distribution, npm package, MCP package, package managers, Neovim, Zed, Emacs, Sublime, lightweight editors, release bundle, native install, release gate, readiness audit, package build verification
- **CI gate**: `npm run command-fabric:release-gate` runs all 120 tests plus Core DNA tests

### Universal Surface Metrics (260611)

After Phase 30 (package-manager expansion):

- Project commands: **91**
- Global commands: **206**
- Marketplace targets: **56**
- Package manager targets: **23**
- Native install hosts: **24**
- Bundle sections: **27**
- Package-build checks: **22**

These metrics are tracked centrally in `src/command_fabric/target_matrix.py` to avoid magic numbers in tests.

---

## Verification

All 30 phases passed with full test suites:

```bash
# Full command-fabric test suite
TESTING=true python3 -m pytest -q tests/test_command_fabric*.py
# → 120 passed, 1 Starlette deprecation warning (non-blocking)

# Release gate
npm run command-fabric:release-gate -- --out /tmp/mekong-release-gate
# → ready=true, 91 commands, 27 sections, 22 build checks, 24 install hosts

# Readiness audit
python3 -m src.main command-fabric readiness-audit --scope global --out /tmp/readiness
# → ready=true, 206 commands, 56 marketplace targets, 23 package-manager targets
```

Full repo test suite also passes:
```bash
TESTING=true python3 -m pytest -q tests/
# → 6495 passed, 46 skipped
```

---
