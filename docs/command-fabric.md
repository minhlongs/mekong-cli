# Mekong Command Fabric

Mekong command fabric is the new command architecture direction: one neutral
catalog feeds every CLI, IDE, SDK, MCP, and agent runtime adapter.

## Why

The old command surface is split across Typer registrations, generated slash
commands, markdown command files, factory contracts, shell wrappers, and npm
packages. That makes global IDE/CLI support expensive because every adapter can
drift.

The command fabric makes `.claude/commands/*.md` the first source layer, merges
readable user-level `~/.claude/commands/*.md` entries for global wrappers, and
joins optional `factory/contracts/commands/*.json` metadata. Adapters consume
the exported catalog instead of copying command definitions.

## Export

```bash
python3 -m src.main command-fabric export --format json
python3 -m src.main command-fabric export --scope project --format json
python3 -m src.main command-fabric export --format table
python3 -m src.main command-fabric export --adapter mcp --format json
python3 -m src.main command-fabric export --adapter vscode --format json
python3 -m src.main command-fabric adapters
python3 -m src.main command-fabric packs --json
python3 -m src.main command-fabric target-matrix
python3 -m src.main command-fabric materialize --scope global --out build/command-fabric
python3 -m src.main command-fabric shell-completion --scope project --out build/shell-completion
python3 -m src.main command-fabric agent-cli-package --scope project --out build/agent-cli
python3 -m src.main command-fabric contracts --scope project --out build/command-contracts
python3 -m src.main command-fabric package-managers --scope project --out build/package-managers
python3 -m src.main command-fabric emacs-package --scope project --out build/command-fabric-emacs
python3 -m src.main command-fabric sublime-package --scope project --out build/command-fabric-sublime
python3 -m src.main command-fabric readiness-audit --scope global --out build/readiness
```

Payload schema:

- `schema`: `mekong.command_fabric.v1`
- `count`: command count
- `source`: source roots. Default export is global:
  `.claude/commands + ~/.claude/commands`
- `commands[].name`: stable command name
- `commands[].source`: source markdown file
- `commands[].description`: command description from frontmatter
- `commands[].argument_hint`: human/agent argument shape
- `commands[].allowed_tools`: allowed tool hints
- `commands[].execution`: execution block
- `commands[].contract`: optional factory contract path
- `commands[].layer`: optional business layer from contract
- `commands[].portability_targets`: adapters that can consume this record

## Adapter Roadmap

- Claude Code and slash commands: export command cards from catalog.
- Codex, Gemini CLI, OpenCode, Kiro CLI: export command cards and execution wrappers.
- VS Code, Cursor, JetBrains: export command palette manifests.
- MCP: export tool metadata for command invocation gateways.
- Shell: export completions and help text metadata.
- SDK packages: consume the same JSON catalog at build time.

Supported adapters:

- `canonical`
- `claude-code`
- `codex`
- `gemini-cli`
- `opencode`
- `aider`
- `continue-dev`
- `copilot-cli`
- `cursor-agent`
- `amp`
- `goose`
- `crush`
- `kiro-cli`
- `mcp`
- `vscode`
- `cursor`
- `windsurf`
- `theia`
- `jetbrains`
- `visual-studio`
- `eclipse`
- `fleet`
- `nova`
- `lapce`
- `kakoune`
- `micro`
- `vim`
- `neovim`
- `helix`
- `zed`
- `emacs`
- `sublime`
- `shell`

## Gate

Adding a new root command must update:

- `.claude/commands/<name>.md`
- `dna/command-surface.json`
- `dna/core-dna.json` when it is an official free/advanced feature
- Tests covering catalog export or adapter generation

## Runtime Routing

Catalog modules are intentionally split by responsibility:

- `src/command_fabric/records.py`: command record model, markdown parsing,
  contract lookup, and portability target inference.
- `src/command_fabric/catalog.py`: project/global catalog assembly and stable
  JSON export.
- `src/command_fabric/adapters.py`: adapter-specific manifest projection.
- `src/command_fabric/runtime.py`: command lookup and invocation gateway.

`src/cli/slash_commands.py` now registers command specs from the fabric catalog
instead of generated one-wrapper-per-command code. The runtime invocation logic
lives in `src/command_fabric/runtime.py` so Typer, MCP, SDKs, and future IDE
bridges share the same command lookup and self-recursion protection.

- Native Typer commands are preserved and never overwritten by markdown specs.
- Runtime slash registration uses the project-only catalog so user/global
  ClaudeKit commands do not unexpectedly change the root Typer surface.
- Catalog-only commands are registered as non-recursive command cards in the
  Python runtime.
- Adapter runtimes can still execute or transform those command cards through
  `command-fabric export`, whose default global scope includes readable
  ClaudeKit commands such as `marketing-local` and `claude-mem`.
- Self-referential declarations like `mekong 4-project` are detected and do
  not call back into `python3 -m src.main 4-project`.
- MCP exposes `cc_command_fabric_list` and `cc_command_fabric_run`, both backed
  by the same runtime gateway.

## Native Packs

`dna/command-packs.json` declares native Typer commands that are not sourced
from `.claude/commands/*.md`. The invariant is:

```
root Typer commands = command fabric catalog + reviewed native command packs
```

`python3 -m src.main command-fabric packs --json` validates this coverage.
`harness-eval` runs the same check as `EVAL-12`, so new root commands cannot
float outside the catalog or a reviewed native pack.

## Materialized Artifacts

`command-fabric materialize` writes JSON files for build systems that should
not import Python internals directly:

- `canonical.json`
- one file per adapter, such as `mcp.json`, `vscode.json`, `shell.json`
- `command-packs.json`

These files are intended for npm packages, MCP gateways, IDE extensions, and
release pipelines.

Package build hooks:

```bash
npm run command-fabric:materialize
npm run command-fabric:materialize --workspace=packages/mekong-engine
```

The root script writes global artifacts to `build/command-fabric`. The
`mekong-engine` workspace script writes project-scoped artifacts to
`packages/mekong-engine/generated/command-fabric` for Workers/package builds.

## Release Bundle

Generate every portable command-fabric surface in one release tree:

```bash
python3 -m src.main command-fabric bundle --scope project --out build/command-fabric-bundle
python3 -m src.main command-fabric bundle --scope project --ide-host vscode --agent-host codex --out build/command-fabric-bundle
```

Generated sections:

- `manifests/`: canonical catalog, adapter manifests, and command packs
- `ide-extensions/`: VS Code, Cursor, Windsurf, Theia, and JetBrains extension scaffolds
- `shell-completion/`: Bash, Zsh, Fish, PowerShell, Nushell, and Elvish
  completions and installer
- `agent-cli/`: Claude Code, Gemini CLI, OpenCode, Codex, Aider,
  Continue.dev, Copilot CLI, Cursor Agent, Amp, Goose, and Crush packages
- `contracts/`: one machine-readable command contract per command
- `marketplace/`: publish/package metadata for IDE, agent CLI, shell, and
  package-manager distribution
- `package-managers/`: Homebrew, Scoop, Winget, Chocolatey, npm global,
  Bun, Deno, asdf, mise, aqua, pkgx/tea, PyPI/pipx, Nix, AUR, Debian, RPM,
  Snap, Flatpak, AppImage, FreeBSD, OpenBSD, NetBSD/pkgsrc, and Docker
  metadata for global CLI installation
- `workspace-templates/`: Dev Container, GitHub Codespaces, and Gitpod
  bootstrap templates for cloud IDE environments
- `npm-package/`: standalone `@mekongcli/command-fabric` consumer package
- `mcp-package/`: standalone `@mekongcli/command-fabric-mcp` stdio server
- `visual-studio-package/`: Visual Studio VSIX scaffold
- `eclipse-package/`: Eclipse plugin scaffold
- `fleet-package/`: JetBrains Fleet plugin metadata and runner
- `nova-package/`: Nova extension scaffold
- `lapce-package/`: Lapce plugin scaffold
- `kakoune-package/`: Kakoune command definitions and runner
- `micro-package/`: micro editor Lua plugin and runner
- `vim-package/`: Vimscript plugin package for classic Vim users
- `neovim-package/`: Lua plugin package for terminal-native Neovim users
- `helix-package/`: Helix runner and config snippets for terminal-native users
- `zed-package/`: Zed extension scaffold exposing the command-fabric MCP server
- `emacs-package/`: Emacs Lisp package exposing interactive command execution
- `sublime-package/`: Sublime Text command-palette package

The bundle command is the release pipeline entrypoint. It proves that all
portable surfaces are generated from one catalog without hand-maintained
command copies.

## Target Matrix

`src/command_fabric/target_matrix.py` is the shared portability matrix for
adapter, marketplace, release bundle, native install, package-manager, and
package-build coverage. Readiness and release-gate tests use this matrix so
new global IDE/CLI targets fail loudly when one surface is updated without the
others.

Inspect the current matrix:

```bash
python3 -m src.main command-fabric target-matrix
```

## Universal Readiness Audit

Run the top-level readiness audit before claiming global IDE/CLI coverage:

```bash
python3 -m src.main command-fabric readiness-audit --scope global --out build/readiness
python3 -m src.main command-fabric readiness-audit --scope project --out build/readiness-project
```

The audit materializes the release bundle, verifies IDE/npm/MCP/Visual Studio/
Eclipse/Fleet/Nova/Lapce/Kakoune/micro/Vim/Neovim/Helix/Zed/Emacs/Sublime package
build contracts, runs native install dry-run for Claude Code, Gemini CLI,
OpenCode, Codex, Aider, Continue.dev, Copilot CLI, Cursor Agent, Amp, Goose,
Crush, Kiro CLI, shell, Visual Studio, Eclipse, Fleet, Nova, Lapce, Kakoune, micro, Vim,
Neovim, Helix, Zed, Emacs, and Sublime, and checks
package-manager targets plus required sections/counts. It exits `2` when any
readiness check fails.

## Marketplace Metadata

Generate distribution metadata without publishing anything:

```bash
python3 -m src.main command-fabric marketplace-metadata --scope project --out build/marketplace
```

Generated `marketplace.json` describes package paths, package commands, and
publish commands for:

- VS Code via `vsce`
- Cursor/Open VSX via `ovsx`
- Windsurf-compatible VSIX packages
- Theia-compatible VSIX packages
- JetBrains plugin repository via Gradle plugin tasks
- Visual Studio, Eclipse, Nova, Lapce, Kakoune, micro, Vim, Neovim,
  Helix, Zed, Emacs, and Sublime Text editor packages
- Claude Code, Gemini CLI, OpenCode, Codex, Aider, Continue.dev, Copilot CLI,
  Cursor Agent, Amp, Goose, and Crush native package installs
- Shell completions
- Dev Containers, GitHub Codespaces, and Gitpod workspace bootstrap templates
- Homebrew, Scoop, Winget, Chocolatey, npm global, Bun, Deno, asdf, mise,
  aqua, pkgx/tea, PyPI/pipx, Nix, AUR, Debian, RPM, and Docker package metadata
  plus Snap, Flatpak, AppImage, and BSD package metadata

## Package Manager Metadata

Generate CLI package-manager metadata without publishing anything:

```bash
python3 -m src.main command-fabric package-managers --scope project --out build/package-managers
```

Generated files:

- `homebrew/mekong-cli.rb`: Homebrew formula scaffold
- `scoop/mekong-cli.json`: Scoop bucket manifest
- `winget/Mekong.MekongCLI.yaml`: Winget singleton manifest
- `chocolatey/mekong-cli.nuspec`: Chocolatey package metadata
- `npm/package.json` and `npm/bin/mekong.js`: npm global install shim
- `bun/package.json` and `bun/bin/mekong.js`: Bun global install shim
- `deno/deno.json` and `deno/mekong.ts`: Deno global install shim
- `asdf/`: asdf plugin scaffold with `bin/list-all`, `bin/download`, and
  `bin/install`
- `mise/mise.toml`: mise GitHub backend metadata
- `aqua/registry.yaml`: aqua registry package metadata
- `pkgx/package.yml`: pkgx/tea pantry package metadata
- `snap/snapcraft.yaml`: Snapcraft package metadata
- `flatpak/io.mekongmind.MekongCLI.yaml`: Flatpak manifest
- `appimage/`: AppImage AppDir scaffold with `AppRun`, desktop entry, and README
- `freebsd/Makefile`: FreeBSD port scaffold
- `openbsd/Makefile`: OpenBSD port scaffold
- `netbsd/Makefile`: NetBSD pkgsrc scaffold
- `pypi/pyproject.toml`: PyPI/pipx project metadata
- `nix/flake.nix`: Nix flake package scaffold
- `aur/PKGBUILD`: Arch User Repository package scaffold
- `debian/control`: Debian package control metadata
- `rpm/mekong-cli.spec`: RPM spec metadata
- `docker/Dockerfile`: Docker/OCI image scaffold
- `package-managers.json`: deterministic index of all package-manager targets

The npm, Bun, Deno, asdf, mise, aqua, pkgx, Snap, Flatpak, AppImage, FreeBSD,
OpenBSD, and NetBSD global shims are package-manager metadata for publishing
from a Mekong CLI source release. They are separate from the TypeScript
consumer package generated under `npm-package/`.

## Package Build Check

Verify generated IDE package build contracts without publishing or downloading
marketplace tooling:

```bash
python3 -m src.main command-fabric package-build-check --bundle build/command-fabric-bundle
```

The check validates:

- VS Code/Cursor/Windsurf/Theia `package.json` compile/package scripts and command
  contributions
- VS Code/Cursor/Windsurf/Theia generated `build-package.sh` with
  compile/package steps
- VS Code/Cursor/Windsurf/Theia strict `tsconfig.json`
- VS Code/Cursor/Windsurf/Theia extension entrypoint command registration
- JetBrains Gradle plugin declarations
- JetBrains generated `build-package.sh` with `gradle buildPlugin`
- JetBrains `plugin.xml` parseability and generated actions
- JetBrains Kotlin action run-console integration
- npm consumer package metadata, strict TypeScript config, helper API, and
  canonical command data
- MCP stdio package metadata, strict TypeScript config, tool handlers, and
  MCP adapter data
- Visual Studio VSIX manifest, C# package entrypoint, and adapter data
- Eclipse plugin descriptor, Java handler, and adapter data
- Nova extension command registration and adapter data
- Lapce plugin metadata, local runner, and adapter data
- Kakoune command definitions, local runner, and adapter data
- micro Lua plugin, local runner, and adapter data
- Vimscript command registration and adapter data
- Neovim Lua plugin command registration and adapter data
- Helix runner/config snippets and adapter data
- Zed extension manifest, Rust context server entrypoint, and adapter data
- Emacs Lisp interactive command bridge and adapter data
- Sublime Text command-palette plugin and adapter data
- Package-manager target index plus Homebrew, npm global, Bun, Deno, asdf,
  mise, aqua, pkgx, Snap, Flatpak, AppImage, BSD ports, PyPI/pipx, and Docker
  sentinels

## Visual Studio Package

Generate a Visual Studio VSIX scaffold:

```bash
python3 -m src.main command-fabric visual-studio-package --scope project --out build/command-fabric-visual-studio
```

Generated files:

- `source.extension.vsixmanifest`: VSIX extension manifest
- `Mekong.CommandFabric.VisualStudio.csproj`: Visual Studio SDK project
- `MekongCommandFabricPackage.cs`: command runner package entrypoint
- `data/canonical.json`: neutral command catalog
- `data/visual-studio.json`: Visual Studio adapter manifest
- `README.md` and `BUILD.md`

The Visual Studio package builds an argv list and starts `ProcessStartInfo`
directly. It does not route command invocations through `/bin/sh -lc`.

## Eclipse Package

Generate an Eclipse plugin scaffold:

```bash
python3 -m src.main command-fabric eclipse-package --scope project --out build/command-fabric-eclipse
```

Generated files:

- `plugin.xml`: Eclipse commands and handlers
- `pom.xml`: Tycho/Eclipse plugin build scaffold
- `src/com/mekong/commandfabric/MekongCommandHandler.java`: command runner handler
- `data/canonical.json`: neutral command catalog
- `data/eclipse.json`: Eclipse adapter manifest
- `README.md` and `BUILD.md`

The Eclipse handler builds an argv list for `ProcessBuilder` directly. It does
not route command invocations through `/bin/sh -lc`.

## Vim Package

Generate a Vim plugin package for classic terminal editor workflows:

```bash
python3 -m src.main command-fabric vim-package --scope project --out build/command-fabric-vim
```

Generated files:

- `plugin/mekong_command_fabric.vim`: dependency-free Vimscript plugin with `:Mekong <command> [args]`
- `data/canonical.json`: neutral command catalog
- `data/vim.json`: Vim adapter manifest
- `README.md` and `BUILD.md`

The Vim plugin shell-escapes command template tokens and each user argument
before opening the terminal job.

## Lightweight Editor Packages

Generate Fleet, Nova, Lapce, Kakoune, or micro packages from the same catalog:

```bash
python3 -m src.main command-fabric lightweight-editor-package --host fleet --scope project --out build/command-fabric-fleet
python3 -m src.main command-fabric lightweight-editor-package --host nova --scope project --out build/command-fabric-nova
python3 -m src.main command-fabric lightweight-editor-package --host lapce --scope project --out build/command-fabric-lapce
python3 -m src.main command-fabric lightweight-editor-package --host kakoune --scope project --out build/command-fabric-kakoune
python3 -m src.main command-fabric lightweight-editor-package --host micro --scope project --out build/command-fabric-micro
```

Generated package-specific files:

- Fleet: `plugin.json` and `bin/mekong-fleet`
- Nova: `extension.js`
- Lapce: `lapce-plugin.toml` and `bin/mekong-lapce`
- Kakoune: `kakrc` and `bin/mekong-kakoune`
- micro: `mekong.lua`, `repo.json`, and `bin/mekong-micro`
- all: `data/canonical.json`, `data/<host>.json`, `README.md`, `BUILD.md`

Fleet, Lapce, Kakoune, and micro Python runners split command templates with `shlex`
and invoke subprocesses with argv lists. They do not use `shell=True`, so user
arguments are passed as command arguments instead of re-parsed by a shell.

## Neovim Package

Generate a Neovim plugin package for terminal-native editor workflows:

```bash
python3 -m src.main command-fabric neovim-package --scope project --out build/command-fabric-neovim
```

Generated files:

- `lua/mekong.lua`: dependency-free Lua plugin with `:Mekong <command> [args]`
- `data/canonical.json`: neutral command catalog
- `data/neovim.json`: Neovim adapter manifest
- `README.md` and `BUILD.md`

The Neovim plugin shell-escapes command template tokens and each user argument
before opening the terminal job.

## Helix Package

Generate a Helix package for shell-command binding workflows:

```bash
python3 -m src.main command-fabric helix-package --scope project --out build/command-fabric-helix
```

Generated files:

- `bin/mekong-helix`: local runner for `:sh mekong-helix <command> [args]`
- `config.toml`: sample keybinding snippets
- `data/canonical.json`: neutral command catalog
- `data/helix.json`: Helix adapter manifest
- `README.md` and `BUILD.md`

The Helix runner uses argv-based subprocess invocation and does not use
`shell=True`.

## Zed Package

Generate a Zed extension scaffold for MCP-capable editor workflows:

```bash
python3 -m src.main command-fabric zed-package --scope project --out build/command-fabric-zed
```

Generated files:

- `extension.toml`: Zed extension manifest and context server declaration
- `Cargo.toml`: Rust extension package metadata
- `src/lib.rs`: Zed extension entrypoint returning `mekong-command-fabric-mcp`
- `data/canonical.json`: neutral command catalog
- `data/zed.json`: Zed adapter manifest
- `README.md`

## Emacs Package

Generate an Emacs package for editor-native command execution:

```bash
python3 -m src.main command-fabric emacs-package --scope project --out build/command-fabric-emacs
```

Generated files:

- `mekong-command-fabric.el`: interactive `mekong-command-fabric-run`
- `data/canonical.json`: neutral command catalog
- `data/emacs.json`: Emacs adapter manifest
- `README.md`

## Sublime Text Package

Generate a Sublime Text package for command palette workflows:

```bash
python3 -m src.main command-fabric sublime-package --scope project --out build/command-fabric-sublime
```

Generated files:

- `mekong_command_fabric.py`: Sublime `WindowCommand` plugin
- `Default.sublime-commands`: command palette entry
- `data/canonical.json`: neutral command catalog
- `data/sublime.json`: Sublime adapter manifest
- `README.md`

The Sublime plugin parses user input with `shlex.split()` and starts the Mekong
process with an argv list instead of `shell=True`.

## Npm Consumer Package

Generate a standalone npm package scaffold for SDKs, IDEs, workers, and other
JavaScript/TypeScript consumers:

```bash
python3 -m src.main command-fabric npm-package --scope project --out build/command-fabric-npm
```

Generated files:

- `package.json`: `@mekongcli/command-fabric` package metadata
- `src/index.ts`: typed helper API and command-name list
- `data/canonical.json`: neutral command catalog
- `data/<adapter>.json`: adapter manifests
- `data/command-packs.json`: reviewed native command pack coverage
- `README.md` and `tsconfig.json`

The release bundle includes this package under `npm-package/`, and the release
gate verifies its package build contract.

The selected `--scope` applies to both the helper API command list and all
`data/` artifacts. A global npm package cannot mix global command names with a
project-only `data/canonical.json`.

## MCP Server Package

Generate a standalone MCP stdio server package for MCP-capable IDEs and agent
clients:

```bash
python3 -m src.main command-fabric mcp-package --scope project --out build/command-fabric-mcp
```

Generated files:

- `package.json`: `@mekongcli/command-fabric-mcp` package metadata and bin
- `src/server.ts`: dependency-free JSON-RPC stdio server
- `data/canonical.json`: neutral command catalog
- `data/mcp.json`: MCP tool manifest
- `README.md` and `tsconfig.json`

The server handles `initialize`, `tools/list`, and `tools/call`. Tool calls
return local-only execution plans, so MCP clients can run Mekong commands in the
developer workspace rather than inside a remote package runtime.

## Native Install

Install generated packages into native local runtime locations:

```bash
python3 -m src.main command-fabric install --scope project --host claude-code --host shell
python3 -m src.main command-fabric install --scope project --host opencode --host codex --write
```

`install` defaults to `--dry-run`. Use `--write` to copy generated packages.
Use `--target-root` in tests, CI, or custom home directories.

Default targets:

- `claude-code`: `~/.claude/commands/mekong`
- `gemini-cli`: `~/.gemini/commands/mekong`
- `opencode`: `~/.config/opencode/commands/mekong`
- `codex`: `~/.codex/command-fabric/mekong`
- `aider`: `~/.mekong/command-fabric/aider`
- `continue-dev`: `~/.mekong/command-fabric/continue-dev`
- `copilot-cli`: `~/.mekong/command-fabric/copilot-cli`
- `cursor-agent`: `~/.mekong/command-fabric/cursor-agent`
- `amp`: `~/.mekong/command-fabric/amp`
- `goose`: `~/.mekong/command-fabric/goose`
- `crush`: `~/.mekong/command-fabric/crush`
- `kiro-cli`: `~/.mekong/command-fabric/kiro-cli`
- `shell`: `~/.mekong/completions`
- `visual-studio`: `~/.mekong/command-fabric/visual-studio`
- `eclipse`: `~/eclipse/dropins/mekong-command-fabric`
- `fleet`: `~/.local/share/JetBrains/Fleet/plugins/mekong-command-fabric`
- `nova`: `~/Library/Application Support/Nova/Extensions/mekong-command-fabric.novaextension`
- `lapce`: `~/.local/share/lapce/plugins/mekong-command-fabric`
- `kakoune`: `~/.config/kak/autoload/mekong-command-fabric`
- `micro`: `~/.config/micro/plug/mekong-command-fabric`
- `vim`: `~/.vim/pack/mekong/start/command-fabric`
- `neovim`: `~/.local/share/nvim/site/pack/mekong/start/command-fabric`
- `helix`: `~/.config/helix/mekong-command-fabric`
- `zed`: `~/.local/share/zed/extensions/installed/mekong-command-fabric`
- `emacs`: `~/.emacs.d/site-lisp/mekong-command-fabric`
- `sublime`: `~/.config/sublime-text/Packages/Mekong Command Fabric`

The install command regenerates packages into a staging directory first, then
copies the selected host package into its native target. This keeps install
behavior reproducible and avoids relying on stale build artifacts.

## Release Gate

Run the same release checks locally and in CI:

```bash
npm run command-fabric:release-gate
python3 scripts/command_fabric_release_gate.py --out build/command-fabric-release-gate --target-root build/command-fabric-install-home
```

The gate rebuilds the project-scoped release bundle, verifies sentinel files for
manifests, VS Code, Cursor, Windsurf, Theia, JetBrains, shell, agent CLI
packages, contracts, marketplace metadata, package-manager metadata, npm package,
MCP package, Visual Studio, Eclipse, Fleet, Nova, Lapce, Kakoune, micro, Vim, Neovim,
Helix, Zed, Emacs, and Sublime Text, verifies package build contracts, then runs
native install in dry-run mode for all supported install hosts. GitHub Actions runs the same gate in
`.github/workflows/command-fabric-release-gate.yml`.

## Shell Completion Package

Generate terminal completion packages from the same catalog:

```bash
python3 -m src.main command-fabric shell-completion --scope project --out build/shell-completion
```

Generated files:

- `shell/bash/mekong.bash`: Bash root-command completion
- `shell/zsh/_mekong`: Zsh root-command completion
- `shell/fish/mekong.fish`: Fish root-command completion
- `shell/powershell/mekong.ps1`: PowerShell native argument completer
- `shell/nushell/mekong.nu`: Nushell extern and completion source
- `shell/elvish/mekong.elv`: Elvish argument completer
- `shell/install.sh`: local installer that copies completions into a target
  directory and prints shell-specific activation instructions

## Agent CLI Packages

Generate package scaffolds for agent CLI runtimes from the same catalog:

```bash
python3 -m src.main command-fabric agent-cli-package --scope project --out build/agent-cli
python3 -m src.main command-fabric agent-cli-package --host opencode --scope project --out build/agent-cli
```

Generated package hosts:

- `claude-code`: command markdown files under `claude-code/commands/`
- `gemini-cli`: command markdown files under `gemini-cli/commands/`
- `opencode`: command markdown files under `opencode/commands/`
- `codex`: portable command-card `manifest.json` plus README for local
  invocation adapters
- `aider`: portable command-card `manifest.json` plus README
- `continue-dev`: portable command-card `manifest.json` plus README
- `copilot-cli`: portable command-card `manifest.json` plus README
- `cursor-agent`: portable command-card `manifest.json` plus README
- `amp`: portable command-card `manifest.json` plus README
- `goose`: portable command-card `manifest.json` plus README
- `crush`: portable command-card `manifest.json` plus README

Each package also includes `manifest.json` with adapter-specific command cards.

## Command Contracts

Generate machine-readable contracts for every command fabric record:

```bash
python3 -m src.main command-fabric contracts --scope project --out build/command-contracts
```

Generated files:

- `contracts/commands/<command>.json`: one contract per command record

Each generated contract includes:

- command identity and source file
- existing source contract reference when present
- execution command and argument hint
- allowed tools and portability targets
- generic input/output JSON schema
- validation metadata such as self-recursion protection

Contracts are materialized from the catalog so the repo does not need to track
copied JSON for every command. Existing hand-authored contracts remain source
metadata and are referenced by generated contracts.

## IDE Extension Scaffolds

Generate VS Code-compatible command palette extensions from the same catalog:

```bash
python3 -m src.main command-fabric ide-extension --host vscode --scope project --out build/ide-extensions
python3 -m src.main command-fabric ide-extension --host cursor --scope project --out build/ide-extensions
python3 -m src.main command-fabric ide-extension --host theia --scope project --out build/ide-extensions
python3 -m src.main command-fabric ide-extension --host jetbrains --scope project --out build/ide-extensions
```

VS Code/Cursor/Windsurf/Theia generated files:

- `<host>/package.json`: command contributions and activation events
- `<host>/src/extension.ts`: registers commands and sends Mekong invocations to
  an IDE terminal
- `<host>/tsconfig.json`: minimal TypeScript compile config
- `<host>/build-package.sh`: deterministic compile/package entrypoint
- `<host>/BUILD.md`: package build notes

Cursor, Windsurf, and Theia consume the same VS Code-compatible extension
shape.

JetBrains generated files:

- `jetbrains/build.gradle.kts`: minimal IntelliJ Platform plugin build
- `jetbrains/src/main/resources/META-INF/plugin.xml`: generated action
  registrations for command-fabric records
- `jetbrains/src/main/kotlin/com/mekong/commandfabric/MekongCommandAction.kt`:
  shared action implementation that prompts for arguments and runs the Mekong
  invocation in the IDE run console
- `jetbrains/build-package.sh`: Gradle IntelliJ package build entrypoint
- `jetbrains/BUILD.md`: JetBrains package build notes

The JetBrains action builds a `GeneralCommandLine` from an argv list and does
not route command invocations through `/bin/sh -lc`.

## Worker Package API

`packages/mekong-engine` exposes command fabric artifacts to remote IDE/CLI
clients through Worker bindings:

- `COMMAND_FABRIC_CANONICAL`: JSON from `canonical.json`
- `COMMAND_FABRIC_ADAPTERS`: JSON from `adapters.json`; contains every
  materialized adapter manifest keyed by adapter name
- `COMMAND_FABRIC_MCP`: legacy fallback JSON from `mcp.json` when a deployment
  has not switched to `COMMAND_FABRIC_ADAPTERS`

Routes:

- `GET /v1/command-fabric`: returns the canonical catalog.
- `GET /v1/command-fabric/commands/:name`: returns one command record.
- `GET /v1/command-fabric/adapters`: returns configured adapter names.
- `GET /v1/command-fabric/adapters/:adapter`: returns adapter metadata for MCP,
  VS Code, Cursor, Windsurf, Theia, JetBrains, Visual Studio, Eclipse, Nova,
  Lapce, Kakoune, micro, Vim, Neovim, Helix, Zed, Emacs, Sublime, shell, and
  agent CLI bridges.
- `POST /v1/command-fabric/invoke`: returns a local execution plan.

Workers cannot execute a local developer CLI. The invoke route returns
`local_only: true` with the exact execution string so VS Code, Cursor,
JetBrains, Theia, Codex, Gemini CLI, OpenCode, Aider, Continue.dev,
Copilot CLI, shell wrappers, or MCP clients can run the command in the user's
workspace.
