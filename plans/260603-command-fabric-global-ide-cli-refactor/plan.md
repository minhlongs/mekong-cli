# Mekong Command Fabric Global IDE/CLI Refactor

## Status

- [x] Read README and CLAUDE project context.
- [x] Inspect current Typer, slash-command, contract, and SDK command surfaces.
- [x] Build a neutral command fabric shared by CLI, IDE, MCP, SDK, and future adapters.
- [x] Replace generated recursive slash dispatch with data-driven routing.
- [x] Export IDE/CLI manifests for Claude Code, Codex, Gemini CLI, OpenCode, Cursor, VS Code, JetBrains, shell completion, and MCP.
- [x] Split legacy command families into stable layers and plugin packs.
- [ ] Add migration tests and compatibility gates.

## Objective

Refactor Mekong CLI from a fragmented command tree into a globally portable
agentic command fabric. It must support most current IDEs and CLIs through one
source of truth, not copied command definitions.

## Requirements

- Preserve open-source Core DNA governance and PR review gates.
- Make command definitions machine-readable and exportable.
- Keep backwards compatibility for existing `mekong <command>` and slash command names.
- Support deep command metadata: layer, namespace, source file, execution target,
  argument hint, allowed tools, contract path, portability targets.
- Make adapters generated from catalog, not hand-maintained command copies.
- Verify every command surface against the catalog.

## Phase 1: Command Fabric Foundation

Related files:

- Created `src/command_fabric/catalog.py`
- Created `src/cli/commands/command_fabric.py`
- Updated `src/cli/app_setup.py`
- Added `tests/test_command_fabric_catalog.py`
- Added command surface docs in `docs/command-fabric.md`

Implementation steps:

1. Parse `.claude/commands/*.md` frontmatter and execution block.
2. Join optional `factory/contracts/commands/<name>.json`.
3. Produce normalized command records with portability targets.
4. Add CLI command `mekong command-fabric export --format json`.
5. Add tests for parsing, export shape, and known command coverage.

## Phase 1 Verification

- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_command_surface.py tests/test_core_dna.py tests/test_harness_eval.py -q`: pass, 19 tests.
- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_core_dna.py tests/test_binh_phap_operating_system.py tests/test_hermes_learning_loop.py tests/test_command_surface.py tests/test_harness_eval.py tests/core/test_command_authorizer.py -q`: pass, 66 tests.
- `python3 -m src.main command-fabric export --format json`: pass, emits `mekong.command_fabric.v1` with 91 commands.
- `python3 -m src.main command-fabric export --format table`: pass.

## Phase 2: Adapter Manifests

Related files:

- Created `src/command_fabric/adapters.py`
- Updated `src/cli/commands/command_fabric.py`
- Updated `docs/command-fabric.md`
- Extended `tests/test_command_fabric_catalog.py`

Implemented adapters:

- Agent CLIs: `claude-code`, `codex`, `gemini-cli`, `opencode`
- IDE command palettes: `vscode`, `cursor`, `jetbrains`
- Gateways/completions: `mcp`, `shell`
- Canonical fallback: `canonical`

Verification:

- `python3 -m pytest tests/test_command_fabric_catalog.py -q`: pass, 9 tests.
- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_core_dna.py tests/test_binh_phap_operating_system.py tests/test_hermes_learning_loop.py tests/test_command_surface.py tests/test_harness_eval.py tests/core/test_command_authorizer.py -q`: pass, 71 tests.
- `python3 -m src.main command-fabric adapters`: pass, lists 10 adapters.
- `python3 -m src.main command-fabric export --adapter vscode --format json`: pass.
- `python3 -m src.main command-fabric export --adapter mcp --format json`: pass.
- Smoke-exported `claude-code`, `codex`, `gemini-cli`, `opencode`, `cursor`,
  `jetbrains`, and `shell`: pass, 91 commands each.

## Phase 3: Data-Driven Slash Routing

Related files:

- Replaced `src/cli/slash_commands.py`
- Updated `docs/command-fabric.md`
- Extended `tests/test_command_fabric_catalog.py`

Behavior:

- Native Typer commands are preserved and not overwritten by command markdown.
- Markdown-only commands register from `build_command_catalog()`.
- Self-referential execution declarations such as `mekong 4-project` are shown
  as catalog-only command cards instead of recursively invoking themselves.
- Non-self-referential execution declarations still run through subprocess with
  `shell=False`.

Verification:

- `python3 -m pytest tests/test_command_fabric_catalog.py -q`: pass, 11 tests.
- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_core_dna.py tests/test_binh_phap_operating_system.py tests/test_hermes_learning_loop.py tests/test_command_surface.py tests/test_harness_eval.py tests/core/test_command_authorizer.py -q`: pass, 73 tests.
- `python3 -m src.main plan --help`: pass, native plan help restored.
- `python3 -m src.main 4-project`: pass, shows non-recursive command card.
- `python3 -m src.main harness-eval --json`: pass, 5/5.
- `python3 -m src.main command-fabric export --adapter mcp --format json`: pass, 91 tools.

## Phase 4: Native Command Packs

Related files:

- Added `dna/command-packs.json`
- Added `src/command_fabric/packs.py`
- Updated `src/cli/commands/command_fabric.py`
- Updated `src/harness/evals/solo_ceo.py`
- Updated `docs/command-fabric.md`
- Extended `tests/test_command_fabric_catalog.py`

Behavior:

- Root command surface is now covered by two sources:
  `.claude/commands/*.md` command fabric catalog and reviewed native packs.
- Native-only commands are grouped into packs: `core-runtime`,
  `workflow-native`, `agentic-systems`, `sdlc`, and `studio`.
- `command-fabric packs --json` validates pack coverage.
- `harness-eval` includes `EVAL-12` for command pack coverage.

Verification:

- `python3 -m src.main command-fabric packs --json`: pass, 5 packs, 37 native commands, 128 root commands covered.
- `python3 -m src.main harness-eval --json`: pass, 6/6 evals including `EVAL-12`.
- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_harness_eval.py -q`: pass, 15 tests.
- `python3 -m pytest tests/test_command_fabric_catalog.py tests/test_core_dna.py tests/test_binh_phap_operating_system.py tests/test_hermes_learning_loop.py tests/test_command_surface.py tests/test_harness_eval.py tests/core/test_command_authorizer.py -q`: pass, 75 tests.

## Success Criteria

- `python3 -m src.main command-fabric export --format json` emits a stable catalog.
- Catalog includes `cook`, `plan`, `binh-phap`, and `harness-eval` where applicable.
- Tests prove command metadata comes from source files, not hard-coded copies.
- Targeted harness/Core DNA tests still pass.

## Risk

- Current worktree is dirty with large prior harness changes.
- Full `python3 -m pytest tests/` already fails collection on legacy missing modules
  outside this refactor: `seed.*`, `src.a2ui`, `scripts.contract_gen`, `integrations.zalo`.
- Do not mark overall objective complete until command registration, adapters,
  docs, tests, and migration gates cover the full global IDE/CLI scope.

## Unresolved Questions

- Which IDE adapter should be promoted first after catalog foundation: MCP,
  VS Code, JetBrains, Cursor, Gemini CLI, or OpenCode?
