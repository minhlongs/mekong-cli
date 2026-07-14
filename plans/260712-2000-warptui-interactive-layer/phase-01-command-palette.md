# Plan 260712-2000-warptui-interactive-layer

**Status:** pending
**Source:** brainstorm-260712-warptui-report.md
**Mode:** --tdd (tests-first per phase)
**Approach:** B — rich + questionary palette + tmux (0 new deps)

## Phases

### Phase 1: Command Palette
Build `questionary`-based command picker that uses the existing NL routing keyword table.

### Phase 2: Block-based Output
Wrap command execution in `rich.Live` + `rich.Panel` blocks (Warp-style output).

### Phase 3: TUI Mode
Tmux session launcher with 3-pane layout (palette | output | raw).

## Dependencies
- Phases are sequential (1 → 2 → 3)
- Phase 1 depends on keyword table from ask.md (already exists)

## Acceptance Criteria
- [ ] `mekong palette "<query>"` fuzzy-searches commands and executes match
- [ ] Command output wrapped in styled blocks with timestamps
- [ ] `mekong tui` launches tmux with 3-pane layout
- [ ] All existing `mekong <command>` flows unchanged
- [ ] Tests pass for each phase
